from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import ProductDetail, ProductSearchResult, ProductSummary
from app.services.catalog import get_product, list_products, search_products

router = APIRouter()


@router.get("/search", response_model=list[ProductSearchResult])
async def search_products_route(
    q: str = Query(min_length=1, max_length=120),
    db: AsyncSession = Depends(get_db),
):
    return await search_products(db, q)


@router.get("/", response_model=list[ProductSummary])
async def list_products_route(
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = Query(default=None, max_length=100),
    search: Optional[str] = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100_000),
):
    return await list_products(
        db, category=category, search=search, limit=limit, offset=offset
    )


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product_route(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
