import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


PRODUCTS = [
    ("Indomie Instant Noodles Onion 70g Carton", "Indomie", "Food", 12500),
    ("Dangote Refined Sugar 50kg Bag", "Dangote", "Food", 85000),
    ("Big Bull Rice 25kg", "Big Bull", "Food", 38000),
    ("Big Bull Rice 50kg", "Big Bull", "Food", 74000),
    ("Golden Penny Semovita 10kg", "Golden Penny", "Food", 18500),
    ("Power Oil Vegetable Oil 5L", "Power Oil", "Food", 15500),
    ("Peak Milk Powder 400g Tin", "Peak", "Food", 6200),
    ("Dano Milk Powder 800g", "Dano", "Food", 9800),
    ("Samsung Galaxy A15 128GB", "Samsung", "Electronics", 225000),
    ("Tecno Spark 20 128GB", "Tecno", "Electronics", 165000),
    ("Oraimo FreePods 4", "Oraimo", "Electronics", 25500),
    ("HP 15 Intel Core i5 Laptop", "HP", "Electronics", 640000),
    ("Binatone Blender 1.5L", "Binatone", "Home Appliances", 36000),
    ("Scanfrost Gas Cooker 4 Burner", "Scanfrost", "Home Appliances", 185000),
    ("Vitafoam Orthopedic Mattress 6x6", "Vitafoam", "Home", 245000),
]

SOURCES = ["Jumia", "Konga", "Jiji", "MarketSquare", "ManualMarket", "TradeDepot"]
LOCATIONS = ["Lagos", "Abuja", "Port Harcourt", "Kano", "Ibadan", "Aba", "Onitsha", "Kaduna", None]
SELLERS = [
    "Jumia Nigeria",
    "Konga Store",
    "Mainland Wholesale",
    "Alaba International",
    "Balogun Market Seller",
    "Ariaria Distributor",
    "TradeDepot Partner",
    "Open Market Vendor",
]


def messy_name(product_name: str, brand: str) -> str:
    variants = [
        product_name,
        product_name.lower(),
        product_name.upper(),
        product_name.replace("Instant ", "").replace(" Bag", ""),
        f"{brand} {product_name.split(' ', 1)[-1]}",
        f"{product_name} - wholesale",
        f"{product_name} promo price",
        f"{product_name.replace('kg', 'KG').replace('g', 'G')}",
    ]
    value = random.choice(variants)
    if random.random() < 0.08:
        value = value.replace(" ", "  ")
    if random.random() < 0.04:
        value = value.replace("0", "O")
    return value[:255]


def noisy_price(base_price: int) -> float:
    multiplier = random.uniform(0.78, 1.28)
    if random.random() < 0.015:
        multiplier *= random.choice([0.35, 2.8, 4.5])
    return round(base_price * multiplier / 50) * 50


def generate_rows(total_rows: int):
    start = datetime.now(timezone.utc) - timedelta(days=180)
    for row_id in range(1, total_rows + 1):
        product_name, brand, category, base_price = random.choice(PRODUCTS)
        source = random.choice(SOURCES)
        seller = random.choice(SELLERS)
        location = random.choice(LOCATIONS)
        scraped_at = start + timedelta(minutes=random.randint(0, 180 * 24 * 60))

        yield {
            "row_id": row_id,
            "source": source,
            "original_name": messy_name(product_name, brand),
            "price": noisy_price(base_price),
            "seller_name": seller,
            "seller_source": "website" if source in {"Jumia", "Konga", "Jiji"} else "market",
            "location": location or "",
            "url": f"https://example.test/{source.lower()}/listing/{row_id}",
            "scraped_at": scraped_at.isoformat(),
            "raw_brand_hint": brand,
            "raw_category_hint": category,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a large raw marketplace listing dataset for processing practice."
    )
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "raw_learning_listings.csv",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "row_id",
                "source",
                "original_name",
                "price",
                "seller_name",
                "seller_source",
                "location",
                "url",
                "scraped_at",
                "raw_brand_hint",
                "raw_category_hint",
            ],
        )
        writer.writeheader()
        writer.writerows(generate_rows(args.rows))

    print(f"Generated {args.rows:,} raw listings at {args.out}")


if __name__ == "__main__":
    main()
