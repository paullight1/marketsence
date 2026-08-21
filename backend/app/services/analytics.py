import logging

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Category,
    PriceHistory,
    Product,
    RawListing,
    Supplier,
    SuspiciousListing,
)

logger = logging.getLogger(__name__)


async def calculate_market_benchmarks(db: AsyncSession):
    """Calculate one trust-weighted benchmark price for each linked product."""
    result = await db.execute(
        select(RawListing, Supplier.trust_score)
        .join(Supplier, RawListing.seller_id == Supplier.id)
        .where(RawListing.product_id.is_not(None))
    )
    data = []
    for row, trust in result:
        data.append(
            {
                "product_id": row.product_id,
                "price": row.price,
                "trust_score": trust if trust is not None else 50.0,
            }
        )

    if not data:
        return 0

    df = pd.DataFrame(data)

    def remove_outliers(group):
        if len(group) < 3:
            return group
        mean = group["price"].mean()
        std = group["price"].std()
        if pd.isna(std) or std == 0:
            return group
        return group[
            (group["price"] >= mean - 2 * std)
            & (group["price"] <= mean + 2 * std)
        ]

    df = (
        df.groupby("product_id", group_keys=False)
        .apply(remove_outliers, include_groups=False)
        .reset_index(drop=False)
    )

    def weighted_mean(group):
        weights = group["trust_score"].clip(lower=0)
        total_weight = weights.sum()
        if total_weight <= 0:
            return group["price"].mean()
        return (group["price"] * weights).sum() / total_weight

    benchmarks = df.groupby("product_id").apply(
        weighted_mean, include_groups=False
    )

    updated_count = 0
    for product_id, golden_price in benchmarks.items():
        db.add(
            PriceHistory(
                product_id=int(product_id),
                price=float(golden_price),
                source="System Benchmark",
            )
        )
        updated_count += 1

    await db.commit()
    return updated_count


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
            func.count(SuspiciousListing.id).filter(
                SuspiciousListing.severity == "high"
            ),
            func.count(SuspiciousListing.id).filter(
                SuspiciousListing.severity == "medium"
            ),
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
