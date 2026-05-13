from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Product, RawListing, Supplier, SuspiciousListing
from app.schemas import OpsOverview

router = APIRouter()


@router.get("/overview", response_model=OpsOverview)
async def get_ops_overview(db: AsyncSession = Depends(get_db)):
    product_count = await _count(db, Product.id)
    supplier_count = await _count(db, Supplier.id)
    listing_count = await _count(db, RawListing.id)
    suspicious_count = await _count(db, SuspiciousListing.id)
    unlinked_count = await _count_where(db, RawListing.id, RawListing.product_id.is_(None))

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
            "price": float(listing.price),
            "seller": seller_name,
            "source": listing.source,
            "location": listing.location,
            "is_suspicious": bool(listing.is_suspicious),
        }
        for listing, seller_name in recent_result.all()
    ]

    review_alerts = [
        {
            "id": f"review-{index + 1}",
            "product": item["product_name"],
            "issue": "Flagged price or unresolved match",
            "severity": "High" if item["is_suspicious"] else "Medium",
            "delta": 0,
        }
        for index, item in enumerate(recent_listings[:4])
        if item["is_suspicious"] or unlinked_count
    ]

    tasks = [
        {
            "id": "raw-ingestion",
            "title": "Raw listing ingestion",
            "stage": "Completed" if listing_count else "Queued",
            "owner": "API",
            "source": "All sources",
            "eta": "Live",
            "progress": 100 if listing_count else 0,
            "listings": listing_count,
            "note": "Raw scrape and CSV rows are persisted before processing.",
        },
        {
            "id": "normalization",
            "title": "Product normalization",
            "stage": "Review" if unlinked_count else "Completed",
            "owner": "Matching pipeline",
            "source": "Catalog",
            "eta": f"{unlinked_count} unresolved" if unlinked_count else "Done",
            "progress": _percentage(listing_count - unlinked_count, listing_count),
            "listings": unlinked_count,
            "note": "Unlinked rows should be matched or sent to analyst review.",
        },
        {
            "id": "benchmarking",
            "title": "Benchmark refresh",
            "stage": "Queued" if product_count else "Queued",
            "owner": "Analytics",
            "source": "System",
            "eta": "After normalization",
            "progress": 35 if product_count else 0,
            "listings": product_count,
            "note": "Benchmarks are recalculated after listings are linked to products.",
        },
        {
            "id": "review",
            "title": "Suspicious price review",
            "stage": "Review" if suspicious_count else "Completed",
            "owner": "Analyst",
            "source": "Quality control",
            "eta": f"{suspicious_count} flagged",
            "progress": 100 if not suspicious_count else 65,
            "listings": suspicious_count,
            "note": "Outliers stay visible before benchmark publication.",
        },
    ]

    return {
        "queue_metrics": [
            {"label": "Raw listings", "value": str(listing_count), "tone": "default"},
            {"label": "Unresolved matches", "value": str(unlinked_count), "tone": "warning" if unlinked_count else "success"},
            {"label": "Suppliers", "value": str(supplier_count), "tone": "default"},
            {"label": "Review queue", "value": str(suspicious_count), "tone": "warning" if suspicious_count else "success"},
        ],
        "tasks": tasks,
        "review_alerts": review_alerts,
        "recent_listings": recent_listings,
    }


async def _count(db: AsyncSession, column) -> int:
    result = await db.execute(select(func.count(column)))
    return int(result.scalar() or 0)


async def _count_where(db: AsyncSession, column, condition) -> int:
    result = await db.execute(select(func.count(column)).where(condition))
    return int(result.scalar() or 0)


def _percentage(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round((done / total) * 100)))
