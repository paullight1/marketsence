import re

from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Product, RawListing


async def normalize_all_listings(db: AsyncSession) -> tuple[int, int]:
    """Link unresolved listings to canonical products and report manual-review work."""
    result = await db.execute(
        select(RawListing).where(RawListing.product_id.is_(None))
    )
    unlinked_listings = result.scalars().all()
    if not unlinked_listings:
        return 0, 0

    product_result = await db.execute(select(Product))
    products = product_result.scalars().all()
    if not products:
        return 0, len(unlinked_listings)

    product_map = {product.normalized_name: product.id for product in products}
    choices = list(product_map)

    linked_count = 0
    unresolved_count = 0

    for listing in unlinked_listings:
        cleaned_listing_name = clean_text(listing.original_name)
        match = process.extractOne(
            cleaned_listing_name,
            choices,
            scorer=fuzz.token_set_ratio,
        )

        if match and match[1] >= 85:
            best_name = match[0]
            listing.product_id = product_map[best_name]
            linked_count += 1
        else:
            unresolved_count += 1

    await db.commit()
    return linked_count, unresolved_count


def clean_text(text: str) -> str:
    """Normalize common Nigerian-market packaging noise before fuzzy matching."""
    text = text.lower()
    text = re.sub(r"\bx\d+\b", "", text)
    text = re.sub(r"\b(ctn|pcs|pack|carton|bag)\b", "", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
