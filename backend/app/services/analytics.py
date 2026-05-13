import logging

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Category, PriceHistory, Product, RawListing, Supplier, SuspiciousListing

logger = logging.getLogger(__name__)

async def calculate_market_benchmarks(db: AsyncSession):
    """
    TEACHING POINT: 
    This service takes all raw listings and calculates a 'Golden Price' 
    for every product. We use a Weighted Average based on the Supplier's Trust Score.
    """
    
    # 1. Fetch all listings that are linked to a product
    result = await db.execute(
        select(RawListing, Supplier.trust_score)
        .join(Supplier, RawListing.seller_id == Supplier.id)
        .where(RawListing.product_id.is_not(None))
    )
    data = []
    for row, trust in result:
        data.append({
            "product_id": row.product_id,
            "price": row.price,
            "trust_score": trust or 50.0 # Default trust if none set
        })

    if not data:
        return 0

    # 2. Load into Pandas for statistical math
    df = pd.DataFrame(data)

    # 3. OUTLIER DETECTION (The 'Waz' Way)
    # We remove any price that is more than 2 standard deviations away from the mean.
    # This stops 'Ghost Prices' from ruining the benchmark.
    def remove_outliers(group):
        if len(group) < 3: return group # Need enough data to detect outliers
        mean = group['price'].mean()
        std = group['price'].std()
        return group[(group['price'] >= mean - 2*std) & (group['price'] <= mean + 2*std)]

    df = df.groupby("product_id", group_keys=False).apply(remove_outliers).reset_index(drop=True)

    # 4. WEIGHTED AVERAGE CALCULATION
    # Formula: Sum(Price * Trust) / Sum(Trust)
    def weighted_mean(group):
        weights = group['trust_score']
        return (group['price'] * weights).sum() / weights.sum()

    benchmarks = df.groupby("product_id").apply(weighted_mean)

    # 5. Save the results to PriceHistory
    updated_count = 0
    for product_id, golden_price in benchmarks.items():
        new_history = PriceHistory(
            product_id=product_id,
            price=float(golden_price),
            source="System Benchmark"
        )
        db.add(new_history)
        updated_count += 1

    await db.commit()
    return updated_count


async def get_dashboard_summary(db: AsyncSession) -> dict:
    products_count = await db.execute(select(Product))
    suppliers_count = await db.execute(select(Supplier))
    listings_count = await db.execute(select(RawListing))
    suspicious_count = await db.execute(select(SuspiciousListing))
    trust_result = await db.execute(select(Supplier.trust_score))

    trust_scores = [row for row in trust_result.scalars().all() if row is not None]
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0

    return {
        "total_products": len(products_count.scalars().all()),
        "total_suppliers": len(suppliers_count.scalars().all()),
        "total_listings": len(listings_count.scalars().all()),
        "suspicious_prices": len(suspicious_count.scalars().all()),
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
        select(SuspiciousListing).where(SuspiciousListing.reviewed.is_(False))
    )
    items = result.scalars().all()
    high = sum(1 for item in items if item.severity == "high")
    medium = sum(1 for item in items if item.severity == "medium")
    return {
        "total_unreviewed": len(items),
        "high_severity": high,
        "medium_severity": medium,
    }
