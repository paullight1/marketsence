import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db, async_session_maker
from app.models.models import Product, RawListing, Supplier, Category

async def seed():
    print("Initializing Database...")
    await init_db()
    
    async with async_session_maker() as db:
        # 1. Create Category
        cat = Category(name="Food & Groceries")
        db.add(cat)
        await db.flush()
        
        # 2. Create Golden Records (Products)
        p1 = Product(normalized_name="Indomie Instant Noodles Onion 70g", category_id=cat.id, brand="Indomie")
        p2 = Product(normalized_name="Dangote Refined Sugar 50kg", category_id=cat.id, brand="Dangote")
        db.add_all([p1, p2])
        await db.flush()
        
        # 3. Create Suppliers
        s1 = Supplier(name="Jumia Nigeria", source="online", trust_score=90.0)
        s2 = Supplier(name="Konga", source="online", trust_score=85.0)
        s3 = Supplier(name="Alaba International", source="market", trust_score=60.0)
        db.add_all([s1, s2, s3])
        await db.flush()
        
        # 4. Create Messy Raw Listings
        messy_listings = [
            # Source 1: Jumia
            RawListing(
                source="Jumia", 
                original_name="Indomie Onion Flavor 70g x 40", 
                price=12500.0, 
                seller_id=s1.id
            ),
            # Source 2: Konga
            RawListing(
                source="Konga", 
                original_name="Noodles - Indomie (70g) Carton", 
                price=13000.0, 
                seller_id=s2.id
            ),
            # Source 3: Messy Market Source
            RawListing(
                source="Manual", 
                original_name="Indomie pack - 70g", 
                price=14000.0, 
                seller_id=s3.id
            ),
            # Sugar
            RawListing(
                source="Jumia", 
                original_name="Dangote Sugar 50kg bag", 
                price=85000.0, 
                seller_id=s1.id
            ),
            RawListing(
                source="Market", 
                original_name="Sugar - Dangote - Refined 50kg", 
                price=82000.0, 
                seller_id=s3.id
            )
        ]
        db.add_all(messy_listings)
        
        await db.commit()
        print("Seed completed. Database populated with messy data.")

if __name__ == "__main__":
    asyncio.run(seed())
