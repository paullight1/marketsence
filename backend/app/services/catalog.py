from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Category, Product, RawListing, Supplier
from app.schemas import (
    ProductDetail,
    ProductSearchResult,
    ProductSummary,
    SupplierDetail,
    SupplierListingItem,
    SupplierSummary,
)


async def list_products(
    db: AsyncSession,
    *,
    category: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ProductSummary]:
    query = select(Product).options(selectinload(Product.category)).order_by(Product.id)
    if search:
        query = query.where(Product.normalized_name.ilike(f"%{search}%"))
    if category:
        query = query.join(Category).where(Category.name == category)

    result = await db.execute(query.offset(offset).limit(limit))
    products = result.scalars().all()

    items: list[ProductSummary] = []
    for product in products:
        stats_result = await db.execute(
            select(
                func.avg(RawListing.price),
                func.min(RawListing.price),
                func.max(RawListing.price),
                func.count(RawListing.id),
            ).where(RawListing.product_id == product.id)
        )
        avg_price, min_price, max_price, count = stats_result.one()
        items.append(
            ProductSummary(
                id=product.id,
                name=product.normalized_name,
                category=product.category.name if product.category else None,
                brand=product.brand,
                avg_price=float(avg_price or 0),
                min_price=float(min_price or 0),
                max_price=float(max_price or 0),
                listings_count=int(count or 0),
                last_updated=product.updated_at,
            )
        )

    return items


async def get_product(db: AsyncSession, product_id: int) -> ProductDetail | None:
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        return None

    return ProductDetail(
        id=product.id,
        name=product.normalized_name,
        category=product.category.name if product.category else None,
        brand=product.brand,
        specifications=product.specifications,
    )


async def search_products(db: AsyncSession, query_text: str, limit: int = 10) -> list[ProductSearchResult]:
    result = await db.execute(
        select(Product)
        .where(Product.normalized_name.ilike(f"%{query_text}%"))
        .order_by(Product.normalized_name)
        .limit(limit)
    )
    return [ProductSearchResult(id=product.id, name=product.normalized_name) for product in result.scalars()]


async def list_suppliers(
    db: AsyncSession,
    *,
    source: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SupplierSummary]:
    query = select(Supplier).order_by(Supplier.id)
    if source and source != "all":
        query = query.where(Supplier.source == source)
    if search:
        query = query.where(Supplier.name.ilike(f"%{search}%"))

    result = await db.execute(query.offset(offset).limit(limit))
    suppliers = result.scalars().all()

    items: list[SupplierSummary] = []
    for supplier in suppliers:
        avg_price_result = await db.execute(
            select(func.avg(RawListing.price)).where(RawListing.seller_id == supplier.id)
        )
        suspicious_result = await db.execute(
            select(func.count(RawListing.id)).where(
                RawListing.seller_id == supplier.id,
                RawListing.is_suspicious.is_(True),
            )
        )
        items.append(
            SupplierSummary(
                id=supplier.id,
                name=supplier.name,
                source=supplier.source,
                location=supplier.location,
                trust_score=float(supplier.trust_score),
                total_listings=supplier.total_listings,
                avg_price=float(avg_price_result.scalar() or 0),
                suspicious_count=int(suspicious_result.scalar() or 0),
            )
        )

    return items


async def get_supplier(db: AsyncSession, supplier_id: int) -> SupplierDetail | None:
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        return None

    return SupplierDetail(
        id=supplier.id,
        name=supplier.name,
        source=supplier.source,
        location=supplier.location,
        contact_info=supplier.contact_info,
        trust_score=float(supplier.trust_score),
        total_listings=supplier.total_listings,
        successful_transactions=supplier.successful_transactions,
    )


async def get_supplier_listings(
    db: AsyncSession, supplier_id: int, *, limit: int = 20
) -> list[SupplierListingItem]:
    result = await db.execute(
        select(RawListing)
        .where(RawListing.seller_id == supplier_id)
        .order_by(RawListing.created_at.desc())
        .limit(limit)
    )
    return [
        SupplierListingItem(
            id=listing.id,
            product_name=listing.original_name,
            price=float(listing.price),
            source=listing.source,
            location=listing.location,
            date=listing.created_at,
            is_suspicious=listing.is_suspicious,
        )
        for listing in result.scalars()
    ]
