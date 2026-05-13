from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.schemas import SupplierDetail, SupplierListingItem, SupplierSummary
from app.services.catalog import get_supplier, get_supplier_listings, list_suppliers

router = APIRouter()


@router.get("/", response_model=list[SupplierSummary])
async def list_suppliers_route(
    db: AsyncSession = Depends(get_db),
    source: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
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
    limit: int = 20,
):
    return await get_supplier_listings(db, supplier_id, limit=limit)
