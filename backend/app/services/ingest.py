from collections.abc import Iterable

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RawListing, Supplier
from app.schemas import BulkListingsInput, ListingInput

SUPPLIER_LOOKUP_BATCH_SIZE = 400


async def ingest_listings(db: AsyncSession, payload: BulkListingsInput) -> int:
    """Persist a listing batch while resolving suppliers in bounded set queries."""
    supplier_keys = list(
        dict.fromkeys(
            (listing.seller_name, listing.seller_source)
            for listing in payload.listings
        )
    )
    suppliers = await _load_suppliers(db, supplier_keys)

    for listing in payload.listings:
        key = (listing.seller_name, listing.seller_source)
        if key in suppliers:
            continue
        supplier = Supplier(
            name=listing.seller_name,
            source=listing.seller_source,
            location=listing.location,
            total_listings=0,
        )
        db.add(supplier)
        suppliers[key] = supplier

    # One flush assigns IDs to every new supplier instead of flushing per listing.
    await db.flush()

    for listing in payload.listings:
        seller = suppliers[(listing.seller_name, listing.seller_source)]
        db.add(_raw_listing_from_input(listing, seller.id))
        seller.total_listings = int(seller.total_listings or 0) + 1

    await db.commit()
    return len(payload.listings)


async def _load_suppliers(
    db: AsyncSession,
    supplier_keys: list[tuple[str, str]],
) -> dict[tuple[str, str], Supplier]:
    suppliers: dict[tuple[str, str], Supplier] = {}
    for chunk in _chunks(supplier_keys, SUPPLIER_LOOKUP_BATCH_SIZE):
        result = await db.execute(
            select(Supplier).where(
                tuple_(Supplier.name, Supplier.source).in_(chunk)
            )
        )
        for supplier in result.scalars().all():
            suppliers.setdefault((supplier.name, supplier.source), supplier)
    return suppliers


def _raw_listing_from_input(listing: ListingInput, seller_id: int) -> RawListing:
    return RawListing(
        source=listing.source,
        original_name=listing.original_name,
        price=listing.price,
        seller_id=seller_id,
        location=listing.location,
        url=listing.url,
    )


def _chunks[T](items: list[T], size: int) -> Iterable[list[T]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]
