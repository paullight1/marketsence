import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_session_maker
from app.services.analytics import calculate_market_benchmarks
from app.models.models import PriceHistory, Product
from sqlalchemy import select

async def run():
    print("Running Market Benchmark Calculation...")
    async with async_session_maker() as db:
        count = await calculate_market_benchmarks(db)
        print(f"Calculated benchmarks for {count} products.")
        
        # Display the results
        print("\n--- Current Market Benchmarks (Golden Prices) ---")
        result = await db.execute(
            select(Product.normalized_name, PriceHistory.price)
            .join(PriceHistory, Product.id == PriceHistory.product_id)
            .order_by(PriceHistory.recorded_at.desc())
        )
        
        seen = set()
        for name, price in result:
            if name not in seen:
                print(f"Product: {name:.<40} Benchmark: NGN {price:,.2f}")
                seen.add(name)

if __name__ == "__main__":
    asyncio.run(run())
