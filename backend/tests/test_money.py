import asyncio
from decimal import Decimal

from sqlalchemy import Numeric, select

from app.models.models import PriceHistory, Product, RawListing, Supplier
from app.schemas import ListingInput
from conftest import TestSessionLocal


def test_money_columns_are_fixed_point_numeric():
    assert isinstance(RawListing.__table__.c.price.type, Numeric)
    assert RawListing.__table__.c.price.type.scale == 2
    assert isinstance(PriceHistory.__table__.c.price.type, Numeric)
    assert PriceHistory.__table__.c.price.type.scale == 2


def test_listing_input_quantizes_binary_float_to_kobo():
    listing = ListingInput(
        source="Manual",
        original_name="Precision Rice",
        price=0.1 + 0.2,
        seller_name="Precision Seller",
        seller_source="manual",
    )

    assert isinstance(listing.price, Decimal)
    assert listing.price == Decimal("0.30")


def test_ingest_rounds_to_two_decimal_places_and_api_preserves_value(client):
    response = client.post(
        "/api/ingest/listings",
        json={
            "listings": [
                {
                    "source": "Manual",
                    "original_name": "Precision Rice",
                    "price": "100.015",
                    "seller_name": "Precision Seller",
                    "seller_source": "manual",
                }
            ]
        },
    )
    assert response.status_code == 200

    ops = client.get("/api/ops/overview")
    assert ops.status_code == 200
    assert ops.json()["recent_listings"][0]["price"] == 100.02


def test_benchmark_is_decimal_exact_and_persists_numeric_value(client):
    async def seed_and_benchmark():
        from app.services.analytics import calculate_market_benchmarks

        async with TestSessionLocal() as db:
            product = Product(normalized_name="precision rice")
            supplier = Supplier(
                name="Precision Supplier",
                source="seed",
                trust_score=50,
                total_listings=2,
            )
            db.add_all([product, supplier])
            await db.flush()
            db.add_all(
                [
                    RawListing(
                        source="seed",
                        original_name="Precision Rice A",
                        price=Decimal("0.10"),
                        seller_id=supplier.id,
                        product_id=product.id,
                    ),
                    RawListing(
                        source="seed",
                        original_name="Precision Rice B",
                        price=Decimal("0.20"),
                        seller_id=supplier.id,
                        product_id=product.id,
                    ),
                ]
            )
            await db.commit()
            updated = await calculate_market_benchmarks(db)
            result = await db.execute(
                select(PriceHistory).where(
                    PriceHistory.product_id == product.id,
                    PriceHistory.source == "System Benchmark",
                )
            )
            history = result.scalar_one()
            return updated, history.price

    updated, price = asyncio.run(seed_and_benchmark())

    assert updated == 1
    assert isinstance(price, Decimal)
    assert price == Decimal("0.15")
