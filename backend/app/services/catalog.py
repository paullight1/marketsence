from sqlalchemy import case, func, select
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
    stats = (
        select(
            RawListing.product_id.label("product_id"),
            func.avg(RawListing.price).label("avg_price"),
            func.min(RawListing.price).label("min_price"),
            func.max(RawListing.price).label("max_price"),
            func.count(RawListing.id).label("listings_count"),
        )
        .where(RawListing.product_id.is_not(None))
        .group_by(RawListing.product_id)
        .subquery()
    )

    query = (
        select(
            Product,
            Category.name.label("category_name"),
            stats.c.avg_price,
            stats.c.min_price,
            stats.c.max_price,
            stats.c.listings_count,
        )
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(stats, stats.c.product_id == Product.id)
        .order_by(Product.id)
    )
    if search:
        query = query.where(Product.normalized_name.ilike(f"%{search}%"))
    if category:
        query = query.where(Category.name == category)

    result = await db.execute(query.offset(offset).limit(limit))
    return [
        ProductSummary(
            id=product.id,
            name=product.normalized_name,
            category=category_name,
            brand=product.brand,
            avg_price=float(avg_price or 0),
            min_price=float(min_price or 0),
            max_price=float(max_price or 0),
            listings_count=int(listings_count or 0),
            last_updated=product.updated_at,
        )
        for (
            product,
            category_name,
            avg_price,
            min_price,
            max_price,
            listings_count,
        ) in result.all()
    ]


async def get_product(db: AsyncSession, product_id: int) -> ProductDetail | None:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id)
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


async def search_products(
    db: AsyncSession, query_text: str, limit: int = 10
) -> list[ProductSearchResult]:
    result = await db.execute(
        select(Product)
        .where(Product.normalized_name.ilike(f"%{query_text}%"))
        .order_by(Product.normalized_name)
        .limit(limit)
    )
    return [
        ProductSearchResult(id=product.id, name=product.normalized_name)
        for product in result.scalars()
    ]


async def list_suppliers(
    db: AsyncSession,
    *,
    source: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SupplierSummary]:
    stats = (
        select(
            RawListing.seller_id.label("seller_id"),
            func.avg(RawListing.price).label("avg_price"),
            func.sum(
                case((RawListing.is_suspicious.is_(True), 1), else_=0)
            ).label("suspicious_count"),
        )
        .group_by(RawListing.seller_id)
        .subquery()
    )

    query = (
        select(
            Supplier,
            stats.c.avg_price,
            stats.c.suspicious_count,
        )
        .outerjoin(stats, stats.c.seller_id == Supplier.id)
        .order_by(Supplier.id)
    )
    if source and source != "all":
        query = query.where(Supplier.source == source)
    if search:
        query = query.where(Supplier.name.ilike(f"%{search}%"))

    result = await db.execute(query.offset(offset).limit(limit))
    return [
        SupplierSummary(
            id=supplier.id,
            name=supplier.name,
            source=supplier.source,
            location=supplier.location,
            trust_score=float(supplier.trust_score),
            total_listings=int(supplier.total_listings or 0),
            avg_price=float(avg_price or 0),
            suspicious_count=int(suspicious_count or 0),
        )
        for supplier, avg_price, suspicious_count in result.all()
    ]


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
        total_listings=int(supplier.total_listings or 0),
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
