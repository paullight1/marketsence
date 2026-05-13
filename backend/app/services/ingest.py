from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RawListing, Supplier
from app.schemas import BulkListingsInput


async def ingest_listings(db: AsyncSession, payload: BulkListingsInput) -> int:
    added_count = 0

    for listing in payload.listings:
        seller_result = await db.execute(
            select(Supplier).where(
                Supplier.name == listing.seller_name,
                Supplier.source == listing.seller_source,
            )
        )
        seller = seller_result.scalar_one_or_none()

        if not seller:
            seller = Supplier(
                name=listing.seller_name,
                source=listing.seller_source,
                location=listing.location,
                total_listings=0,
            )
            db.add(seller)
            await db.flush()

        db.add(
            RawListing(
                source=listing.source,
                original_name=listing.original_name,
                price=listing.price,
                seller_id=seller.id,
                location=listing.location,
                url=listing.url,
            )
        )
        seller.total_listings += 1
        added_count += 1

    await db.commit()
    return added_count
