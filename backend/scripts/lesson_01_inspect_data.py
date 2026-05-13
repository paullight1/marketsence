import pandas as pd

df = pd.read_csv("../data/raw_learning_listings_10k.csv")

print("Rows and columns:")
print(df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nColumn names:")
print(df.columns)

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isna().sum())

print("\nBasic price summary:")
print(df["price"].describe())

print("\nSource distribution:")
print(df["source"].value_counts())

print("\nLocation distribution:")
print(df["location"].value_counts())

print("\nSeller source distribution:")
print(df["seller_source"].value_counts())

print("\nRaw brand hint distribution:")
print(df["raw_brand_hint"].value_counts())

print("\nRaw category hint distribution:")
print(df["raw_category_hint"].value_counts())

# Print summary for expensive items
print("\nTop 5 most expensive items:")
print(df.sort_values(by="price", ascending=False).head())

# Print missing values summary
print("\nMissing values per column:")
print(df.isna().sum())

# Print price grouped by category
print("\nAverage price by raw category hint:")
print(df.groupby("raw_category_hint")["price"].mean())

# Print price grouped by location
print("\nAverage price by location:")
print(df.groupby("location")["price"].mean())