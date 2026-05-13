from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import RawListing, Product
from rapidfuzz import process, fuzz
import logging
import re

logger = logging.getLogger(__name__)

async def normalize_all_listings(db: AsyncSession):
    """
    Main entry point for the normalization pipeline.
    It links RawListing items to canonical Products.
    """
    # 1. Fetch unlinked listings
    result = await db.execute(select(RawListing).where(RawListing.product_id == None))
    unlinked_listings = result.scalars().all()
    
    if not unlinked_listings:
        return 0, 0
    
    # 2. Fetch all products (Golden Records)
    p_result = await db.execute(select(Product))
    products = p_result.scalars().all()
    
    # Map for fuzzy search: {product_name: product_id}
    product_map = {p.normalized_name: p.id for p in products}
    choices = list(product_map.keys())
    
    linked_count = 0
    new_products_suggested = 0
    
    for listing in unlinked_listings:
        if not choices:
            # If no products exist yet, we can't link, so we skip or create first product
            logger.info("No products in database to match against.")
            break
            
        # 3. Fuzzy match the original name against choices
        # We use token_set_ratio which is great for messy names like "Indomie 70g" vs "Noodles Indomie"
        cleaned_listing_name = clean_text(listing.original_name)
        match = process.extractOne(cleaned_listing_name, choices, scorer=fuzz.token_set_ratio)
        
        if match:
            best_name, score, index = match
            
            # 4. If score is high enough, link it
            if score >= 85:
                listing.product_id = product_map[best_name]
                linked_count += 1
            else:
                # Potential new product or manual review needed
                new_products_suggested += 1
                
    await db.commit()
    return linked_count, new_products_suggested

def clean_text(text: str) -> str:
    """
    Utility to clean strings before matching (remove special chars, lower case).
    Waz mentioned 'textbook solutions don't work' - this is where we add 
    market-specific cleaning logic (e.g., removing 'x40', 'CTN', etc).
    """
    text = text.lower()
    # Remove common packaging suffixes in Nigerian markets
    text = re.sub(r'\bx\d+\b', '', text) # remove x40, x20
    text = re.sub(r'\b(ctn|pcs|pack|carton|bag)\b', '', text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
