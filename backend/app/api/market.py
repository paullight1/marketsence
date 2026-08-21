from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import PriceHistory, Product, RawListing
from app.schemas import MarketSnapshot, SourceComparison, TrendPoint

router = APIRouter()


@router.get("/compare", response_model=list[SourceComparison])
async def compare_prices(
    product_name: str = Query(min_length=1, max_length=255),
    db: AsyncSession = Depends(get_db),
):
    product = await _resolve_product(db, product_name)

    listings_query = (
        select(
            RawListing.source,
            func.avg(RawListing.price).label("avg_price"),
            func.min(RawListing.price).label("min_price"),
            func.max(RawListing.price).label("max_price"),
            func.count(RawListing.id).label("count"),
        )
        .where(RawListing.product_id == product.id)
        .group_by(RawListing.source)
        .order_by(RawListing.source.asc())
    )
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
    product_name: str = Query(min_length=1, max_length=255),
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    product = await _resolve_product(db, product_name)

    trends_query = (
        select(
            func.date(PriceHistory.recorded_at).label("date"),
            func.avg(PriceHistory.price).label("avg_price"),
        )
        .where(PriceHistory.product_id == product.id)
        .group_by(func.date(PriceHistory.recorded_at))
        .order_by(func.date(PriceHistory.recorded_at).desc())
        .limit(days)
    )
    trends_result = await db.execute(trends_query)
    rows = list(trends_result.all())
    rows.reverse()

    return [
        {"date": str(row.date), "avg_price": float(row.avg_price or 0)}
        for row in rows
    ]


@router.get("/{product_name}", response_model=MarketSnapshot)
async def get_market_price(
    product_name: str = Path(min_length=1, max_length=255),
    db: AsyncSession = Depends(get_db),
):
    product = await _resolve_product(db, product_name)

    listing_query = select(
        func.avg(RawListing.price).label("avg_price"),
        func.min(RawListing.price).label("min_price"),
        func.max(RawListing.price).label("max_price"),
        func.count(RawListing.id).label("count"),
    ).where(RawListing.product_id == product.id)

    listing_result = await db.execute(listing_query)
    stats = listing_result.one()

    suspicious_result = await db.execute(
        select(func.count(RawListing.id)).where(
            RawListing.product_id == product.id,
            RawListing.is_suspicious.is_(True),
        )
    )
    suspicious_count = suspicious_result.scalar()

    return {
        "product_id": product.id,
        "product_name": product.normalized_name,
        "average_price": float(stats.avg_price or 0),
        "market_range": [float(stats.min_price or 0), float(stats.max_price or 0)],
        "total_listings": int(stats.count or 0),
        "suspicious_listings": int(suspicious_count or 0),
    }


async def _resolve_product(db: AsyncSession, product_name: str) -> Product:
    term = product_name.strip()
    if not term:
        raise HTTPException(status_code=422, detail="Product name is required")

    exact_result = await db.execute(
        select(Product)
        .where(func.lower(Product.normalized_name) == term.lower())
        .limit(1)
    )
    exact_match = exact_result.scalar_one_or_none()
    if exact_match:
        return exact_match

    partial_result = await db.execute(
        select(Product)
        .where(Product.normalized_name.ilike(f"%{term}%"))
        .order_by(Product.normalized_name.asc())
        .limit(2)
    )
    matches = partial_result.scalars().all()

    if not matches:
        raise HTTPException(status_code=404, detail="Product not found")
    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail="Multiple products match this query; use an exact product name",
        )
    return matches[0]
