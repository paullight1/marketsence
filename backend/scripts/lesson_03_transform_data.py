import pandas as pd


df = pd.read_csv("../data/clean_learning_listings_10k.csv")

print("Loaded cleaned dataset:")
print(df.shape)

# 1. Convert scraped_at back to datetime after loading from CSV.
df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True).dt.tz_localize(None)

# 2. Create time-based columns.
df["scrape_month"] = df["scraped_at"].dt.to_period("M").astype(str)
df["scrape_day"] = df["scraped_at"].dt.day_name()

# 3. Create a simple product key for grouping similar records.
df["product_key"] = (
    df["clean_name"]
    .str.replace(" promo price", "", regex=False)
    .str.replace(" wholesale", "", regex=False)
    .str.strip()
)

# 4. Create price bands.
df["price_band"] = pd.cut(
    df["price"],
    bins=[0, 10_000, 50_000, 150_000, 500_000, float("inf")],
    labels=["very_low", "low", "medium", "high", "very_high"],
)

# 5. Calculate average price per product key.
product_avg_price = df.groupby("product_key")["price"].transform("mean")
df["product_avg_price"] = product_avg_price.round(2)

# 6. Calculate how far each listing is from its product average.
df["price_difference"] = df["price"] - df["product_avg_price"]
df["price_difference_percent"] = (
    (df["price_difference"] / df["product_avg_price"]) * 100
).round(2)

# 7. Flag suspicious prices.
df["is_suspicious_price"] = df["price_difference_percent"].abs() > 60

print("\nFirst 10 transformed rows:")
print(
    df[
        [
            "source",
            "clean_name",
            "price",
            "price_band",
            "product_avg_price",
            "price_difference_percent",
            "is_suspicious_price",
            "scrape_month",
        ]
    ].head(10)
)

print("\nListings by price band:")
print(df["price_band"].value_counts())

print("\nSuspicious price count:")
print(df["is_suspicious_price"].value_counts())

print("\nAverage price by category:")
category_summary = (
    df.groupby("raw_category_hint")
    .agg(
        listings_count=("row_id", "count"),
        average_price=("price", "mean"),
        min_price=("price", "min"),
        max_price=("price", "max"),
        suspicious_count=("is_suspicious_price", "sum"),
    )
    .round(2)
    .sort_values("average_price", ascending=False)
)
print(category_summary)

print("\nAverage price by source:")
source_summary = (
    df.groupby("source")
    .agg(
        listings_count=("row_id", "count"),
        average_price=("price", "mean"),
        min_price=("price", "min"),
        max_price=("price", "max"),
        suspicious_count=("is_suspicious_price", "sum"),
    )
    .round(2)
    .sort_values("listings_count", ascending=False)
)
print(source_summary)

print("\nTop 10 suspicious listings:")
top_suspicious = df[df["is_suspicious_price"]].sort_values(
    "price_difference_percent",
    key=lambda values: values.abs(),
    ascending=False,
)
print(
    top_suspicious[
        [
            "source",
            "clean_name",
            "price",
            "product_avg_price",
            "price_difference_percent",
            "location",
        ]
    ].head(10)
)

df.to_csv("../data/transformed_learning_listings_10k.csv", index=False)
category_summary.to_csv("../data/category_summary_10k.csv")
source_summary.to_csv("../data/source_summary_10k.csv")

print("\nSaved transformed dataset to ../data/transformed_learning_listings_10k.csv")
print("Saved category summary to ../data/category_summary_10k.csv")
print("Saved source summary to ../data/source_summary_10k.csv")
