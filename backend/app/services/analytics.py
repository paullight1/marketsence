from collections import defaultdict
from decimal import Decimal
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.money import ZERO_MONEY, to_money, to_weight
from app.models.models import Category, PriceHistory, Product, RawListing, Supplier, SuspiciousListing


async def calculate_market_benchmarks(db: AsyncSession) -> int:
    """Persist trust-weighted product benchmarks using fixed-point money."""
    result = await db.execute(
        select(RawListing, Supplier.trust_score)
        .join(Supplier, RawListing.seller_id == Supplier.id)
        .where(RawListing.product_id.is_not(None))
    )
    rows = result.all()
    if not rows:
        return 0

    grouped: dict[int, list[tuple[RawListing, Decimal]]] = defaultdict(list)
    listing_ids: list[int] = []
    for listing, trust_score in rows:
        grouped[int(listing.product_id)].append((listing, to_weight(trust_score)))
        listing_ids.append(int(listing.id))

    existing_result = await db.execute(
        select(SuspiciousListing).where(SuspiciousListing.listing_id.in_(listing_ids))
    )
    existing_flags: dict[int, SuspiciousListing] = {}
    for flag in existing_result.scalars().all():
        existing_flags.setdefault(int(flag.listing_id), flag)

    updated_count = 0
    for product_id, observations in grouped.items():
        flagged_ids = _detect_outlier_listing_ids(observations)
        center = median(to_money(item.price) for item, _ in observations)

        for listing, _ in observations:
            if listing.id not in flagged_ids:
                continue

            listing.is_suspicious = True
            price = to_money(listing.price)
            relative_delta = abs(price - center) / center if center else Decimal("0")
            direction = "above" if price >= center else "below"
            reason = (
                "Benchmark outlier: price is "
                f"{relative_delta * Decimal('100'):.1f}% {direction} product median {center:.2f}"
            )
            severity = "high" if relative_delta >= Decimal("1") else "medium"

            existing = existing_flags.get(int(listing.id))
            if existing is None:
                flag = SuspiciousListing(
                    listing_id=listing.id,
                    reason=reason,
                    severity=severity,
                    reviewed=False,
                )
                db.add(flag)
                existing_flags[int(listing.id)] = flag
            elif not existing.reviewed and existing.reason.startswith("Benchmark outlier:"):
                existing.reason = reason
                existing.severity = severity

        benchmark_rows = [observation for observation in observations if observation[0].id not in flagged_ids] or observations

        weighted_total = Decimal("0")
        total_weight = Decimal("0")
        for listing, trust_score in benchmark_rows:
            price = to_money(listing.price)
            weighted_total += price * trust_score
            total_weight += trust_score

        if total_weight > 0:
            benchmark_price = to_money(weighted_total / total_weight)
        else:
            benchmark_price = to_money(
                sum((to_money(listing.price) for listing, _ in benchmark_rows), ZERO_MONEY)
                / Decimal(len(benchmark_rows))
            )

        db.add(PriceHistory(product_id=product_id, price=benchmark_price, source="System Benchmark"))
        updated_count += 1

    await db.commit()
    return updated_count


def _detect_outlier_listing_ids(observations: list[tuple[RawListing, Decimal]]) -> set[int]:
    if len(observations) < 4:
        return set()

    prices = [to_money(listing.price) for listing, _ in observations]
    center = median(prices)
    deviations = [abs(price - center) for price in prices]
    mad = median(deviations)

    flagged: set[int] = set()
    for (listing, _), deviation in zip(observations, deviations, strict=True):
        if mad > 0:
            modified_z = Decimal("0.6745") * deviation / mad
            is_outlier = modified_z > Decimal("3.5")
        else:
            relative_delta = deviation / center if center else Decimal("0")
            is_outlier = relative_delta >= Decimal("0.5")
        if is_outlier:
            flagged.add(int(listing.id))
    return flagged


async def get_dashboard_summary(db: AsyncSession) -> dict:
    products_count = await _count(db, Product.id)
    suppliers_count = await _count(db, Supplier.id)
    listings_count = await _count(db, RawListing.id)
    suspicious_count = await _count(db, SuspiciousListing.id)
    trust_result = await db.execute(select(func.avg(Supplier.trust_score)))
    avg_trust = float(trust_result.scalar() or 0)
    return {
        "total_products": products_count,
        "total_suppliers": suppliers_count,
        "total_listings": listings_count,
        "suspicious_prices": suspicious_count,
        "avg_trust_score": round(avg_trust, 1),
    }


async def get_category_breakdown(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Category.name, func.count(Product.id))
        .join(Product, Product.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    )
    return [{"category": name, "count": count} for name, count in result.all()]


async def get_suspicious_summary(db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            func.count(SuspiciousListing.id),
            func.count(SuspiciousListing.id).filter(SuspiciousListing.severity == "high"),
            func.count(SuspiciousListing.id).filter(SuspiciousListing.severity == "medium"),
        ).where(SuspiciousListing.reviewed.is_(False))
    )
    total_unreviewed, high, medium = result.one()
    return {
        "total_unreviewed": int(total_unreviewed or 0),
        "high_severity": int(high or 0),
        "medium_severity": int(medium or 0),
    }


async def _count(db: AsyncSession, column) -> int:
    result = await db.execute(select(func.count(column)))
    return int(result.scalar() or 0)
