from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.money import to_money
from app.db.database import get_db
from app.models.models import PriceHistory, RawListing, Supplier, SuspiciousListing
from app.schemas import OpsOverview

router = APIRouter()


@router.get("/overview", response_model=OpsOverview)
async def get_ops_overview(db: AsyncSession = Depends(get_db)):
    supplier_count = await _count(db, Supplier.id)
    listing_count = await _count(db, RawListing.id)
    unlinked_count = await _count_where(db, RawListing.id, RawListing.product_id.is_(None))
    linked_product_count = await _count_distinct_where(db, RawListing.product_id, RawListing.product_id.is_not(None))
    benchmarked_product_count = await _count_distinct_where(db, PriceHistory.product_id, PriceHistory.source == "System Benchmark")
    suspicious_total = await _count(db, SuspiciousListing.id)
    suspicious_unreviewed = await _count_where(db, SuspiciousListing.id, SuspiciousListing.reviewed.is_(False))

    recent_result = await db.execute(
        select(RawListing, Supplier.name)
        .join(Supplier, RawListing.seller_id == Supplier.id)
        .order_by(RawListing.created_at.desc())
        .limit(6)
    )
    recent_listings = [
        {
            "id": listing.id,
            "product_name": listing.original_name,
            "price": to_money(listing.price),
            "seller": seller_name,
            "source": listing.source,
            "location": listing.location,
            "is_suspicious": bool(listing.is_suspicious),
        }
        for listing, seller_name in recent_result.all()
    ]

    review_alerts = await _review_alerts(db)
    if listing_count == 0:
        normalization_stage, normalization_eta = "Queued", "Waiting for listings"
    elif unlinked_count:
        normalization_stage, normalization_eta = "Review", f"{unlinked_count} unresolved"
    else:
        normalization_stage, normalization_eta = "Completed", "Done"

    if linked_product_count == 0:
        benchmark_stage, benchmark_eta, benchmark_progress = "Blocked", "Needs linked products", 0
    elif benchmarked_product_count >= linked_product_count:
        benchmark_stage, benchmark_eta, benchmark_progress = "Completed", "Current", 100
    else:
        pending = linked_product_count - benchmarked_product_count
        benchmark_stage, benchmark_eta = "Queued", f"{pending} products pending"
        benchmark_progress = _percentage(benchmarked_product_count, linked_product_count)

    reviewed_count = suspicious_total - suspicious_unreviewed
    tasks = [
        {"id": "raw-ingestion", "title": "Raw listing ingestion", "stage": "Completed" if listing_count else "Queued", "owner": "API", "source": "All sources", "eta": "Live" if listing_count else "Waiting for input", "progress": 100 if listing_count else 0, "listings": listing_count, "note": "Raw scrape and listing rows are persisted before downstream processing."},
        {"id": "normalization", "title": "Product normalization", "stage": normalization_stage, "owner": "Matching pipeline", "source": "Catalog", "eta": normalization_eta, "progress": _percentage(listing_count - unlinked_count, listing_count), "listings": unlinked_count, "note": "Unlinked rows remain visible until they are matched to canonical products."},
        {"id": "benchmarking", "title": "Benchmark refresh", "stage": benchmark_stage, "owner": "Analytics", "source": "System", "eta": benchmark_eta, "progress": benchmark_progress, "listings": linked_product_count, "note": "Benchmark status is derived from linked products and persisted benchmark history."},
        {"id": "review", "title": "Suspicious price review", "stage": "Review" if suspicious_unreviewed else "Completed", "owner": "Analyst", "source": "Quality control", "eta": f"{suspicious_unreviewed} flagged" if suspicious_unreviewed else "No open flags", "progress": _percentage(reviewed_count, suspicious_total) if suspicious_total else 100, "listings": suspicious_unreviewed, "note": "Only explicit suspicious-listing records enter this review queue."},
    ]
    return {
        "queue_metrics": [
            {"label": "Raw listings", "value": str(listing_count), "tone": "default"},
            {"label": "Unresolved matches", "value": str(unlinked_count), "tone": "warning" if unlinked_count else "success"},
            {"label": "Suppliers", "value": str(supplier_count), "tone": "default"},
            {"label": "Review queue", "value": str(suspicious_unreviewed), "tone": "warning" if suspicious_unreviewed else "success"},
        ],
        "tasks": tasks,
        "review_alerts": review_alerts,
        "recent_listings": recent_listings,
    }


async def _review_alerts(db: AsyncSession) -> list[dict]:
    flagged_rows = (
        await db.execute(
            select(SuspiciousListing, RawListing)
            .join(RawListing, SuspiciousListing.listing_id == RawListing.id)
            .where(SuspiciousListing.reviewed.is_(False))
            .order_by(SuspiciousListing.created_at.desc())
            .limit(4)
        )
    ).all()
    alerts = [
        {"id": f"suspicious-{flag.id}", "product": listing.original_name, "issue": flag.reason, "severity": str(flag.severity or "medium").title(), "delta": 0}
        for flag, listing in flagged_rows
    ]
    if len(alerts) >= 4:
        return alerts
    excluded_ids = [listing.id for _, listing in flagged_rows]
    unresolved_query = select(RawListing).where(RawListing.product_id.is_(None)).order_by(RawListing.created_at.desc())
    if excluded_ids:
        unresolved_query = unresolved_query.where(RawListing.id.notin_(excluded_ids))
    unresolved_result = await db.execute(unresolved_query.limit(4 - len(alerts)))
    alerts.extend(
        {"id": f"unresolved-{listing.id}", "product": listing.original_name, "issue": "Product match unresolved", "severity": "Medium", "delta": 0}
        for listing in unresolved_result.scalars().all()
    )
    return alerts


async def _count(db: AsyncSession, column) -> int:
    return int((await db.execute(select(func.count(column)))).scalar() or 0)


async def _count_where(db: AsyncSession, column, condition) -> int:
    return int((await db.execute(select(func.count(column)).where(condition))).scalar() or 0)


async def _count_distinct_where(db: AsyncSession, column, condition) -> int:
    return int((await db.execute(select(func.count(func.distinct(column))).where(condition))).scalar() or 0)


def _percentage(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round((done / total) * 100)))
