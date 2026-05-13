import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_session_maker
from app.services.normalizer import normalize_all_listings
from app.models.models import RawListing, Product
from sqlalchemy import select

async def run():
    print("Starting Normalization Pipeline...")
    async with async_session_maker() as db:
        # Check initial state
        res = await db.execute(select(RawListing).where(RawListing.product_id == None))
        unlinked = len(res.scalars().all())
        print(f"Found {unlinked} unlinked listings.")
        
        # Run normalization
        linked, suggested = await normalize_all_listings(db)
        print(f"Normalization complete: Linked {linked} items, {suggested} suggested for review.")
        
        # Verify links
        result = await db.execute(select(RawListing).where(RawListing.product_id != None))
        linked_items = result.scalars().all()
        
        print("\n--- Linked Results ---")
        for item in linked_items:
            # Fetch the product name
            p_res = await db.execute(select(Product).where(Product.id == item.product_id))
            product = p_res.scalar_one()
            print(f"Source: {item.source} | Original: '{item.original_name}' -> Matched: '{product.normalized_name}'")

if __name__ == "__main__":
    asyncio.run(run())
