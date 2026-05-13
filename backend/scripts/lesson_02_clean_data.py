import pandas as pd

df = pd.read_csv("../data/raw_learning_listings_10k.csv")

print("Before cleaning:")
print(df.head())
print(df.isna().sum())

# 1. Fill missing locations
df["location"] = df["location"].fillna("Unknown")

# 2. Clean product names
df["clean_name"] = (
    df["original_name"]
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.replace("promo price", "", regex=False)
    .str.replace("wholesale", "", regex=False)
    .str.replace("-", " ", regex=False)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

# 3. Convert scraped_at from text to datetime
df["scraped_at"] = pd.to_datetime(df["scraped_at"])

# 4. Create a date-only column
df["scrape_date"] = df["scraped_at"].dt.date

# 5. Remove duplicate rows
df = df.drop_duplicates(
    subset=["source", "clean_name", "price", "seller_name", "location"]
)

print("\nAfter cleaning:")
print(df[["original_name", "clean_name", "price", "location", "scrape_date"]].head(10))

print("\nMissing values after cleaning:")
print(df.isna().sum())

print("\nRows after removing duplicates:")
print(df.shape)

df.to_csv("../data/clean_learning_listings_10k.csv", index=False)

print("\nSaved cleaned file to ../data/clean_learning_listings_10k.csv")
