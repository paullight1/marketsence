from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import SupplierDetail, SupplierListingItem, SupplierSummary
from app.services.catalog import get_supplier, get_supplier_listings, list_suppliers

router = APIRouter()


@router.get("/", response_model=list[SupplierSummary])
async def list_suppliers_route(
    db: AsyncSession = Depends(get_db),
    source: Optional[str] = Query(default=None, max_length=50),
    search: Optional[str] = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100_000),
):
    return await list_suppliers(
        db, source=source, search=search, limit=limit, offset=offset
    )


@router.get("/{supplier_id}", response_model=SupplierDetail)
async def get_supplier_route(supplier_id: int, db: AsyncSession = Depends(get_db)):
    supplier = await get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.get("/{supplier_id}/listings", response_model=list[SupplierListingItem])
async def get_supplier_listings_route(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
):
    return await get_supplier_listings(db, supplier_id, limit=limit)
