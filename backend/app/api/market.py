from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.models import Product, RawListing, PriceHistory
from app.schemas import MarketSnapshot, SourceComparison, TrendPoint

router = APIRouter()


@router.get("/compare", response_model=list[SourceComparison])
async def compare_prices(
    product_name: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.normalized_name.ilike(f"%{product_name}%"))
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    listings_query = select(
        RawListing.source,
        func.avg(RawListing.price).label("avg_price"),
        func.min(RawListing.price).label("min_price"),
        func.max(RawListing.price).label("max_price"),
        func.count(RawListing.id).label("count"),
    ).where(RawListing.product_id == product.id).group_by(RawListing.source)

    listings_result = await db.execute(listings_query)

    return [
        {
            "source": row.source,
            "avg_price": float(row.avg_price or 0),
            "min_price": float(row.min_price or 0),
            "max_price": float(row.max_price or 0),
            "listings_count": int(row.count or 0),
        }
        for row in listings_result
    ]


@router.get("/trends", response_model=list[TrendPoint])
async def get_price_trends(
    product_name: str,
    days: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.normalized_name.ilike(f"%{product_name}%"))
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    trends_query = select(
        func.date(PriceHistory.recorded_at).label("date"),
        func.avg(PriceHistory.price).label("avg_price"),
    ).where(
        PriceHistory.product_id == product.id,
    ).group_by(func.date(PriceHistory.recorded_at)).order_by(func.date(PriceHistory.recorded_at).desc()).limit(days)

    trends_result = await db.execute(trends_query)

    return [
        {"date": str(row.date), "avg_price": float(row.avg_price or 0)}
        for row in trends_result
    ]


@router.get("/{product_name}", response_model=MarketSnapshot)
async def get_market_price(
    product_name: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.normalized_name.ilike(f"%{product_name}%"))
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    listing_query = select(
        func.avg(RawListing.price).label("avg_price"),
        func.min(RawListing.price).label("min_price"),
        func.max(RawListing.price).label("max_price"),
        func.count(RawListing.id).label("count"),
    ).where(RawListing.product_id == product.id)

    listing_result = await db.execute(listing_query)
    stats = listing_result.one()

    sus_query = select(func.count(RawListing.id)).where(
        RawListing.product_id == product.id,
        RawListing.is_suspicious.is_(True),
    )
    sus_result = await db.execute(sus_query)
    suspicious_count = sus_result.scalar()

    return {
        "product_id": product.id,
        "product_name": product.normalized_name,
        "average_price": float(stats.avg_price or 0),
        "market_range": [float(stats.min_price or 0), float(stats.max_price or 0)],
        "total_listings": int(stats.count or 0),
        "suspicious_listings": int(suspicious_count or 0),
    }
