import pandas as pd


df = pd.read_csv("../data/transformed_learning_listings_10k.csv")

print("Loaded transformed dataset:")
print(df.shape)

# Human review is needed when the computer is not confident.
needs_review = df[
    (df["is_suspicious_price"] == True)
    | (df["location"] == "Unknown")
    | (df["clean_name"].str.len() < 8)
].copy()

needs_review["review_status"] = "pending"
needs_review["human_corrected_name"] = ""
needs_review["human_corrected_price"] = ""
needs_review["human_comment"] = ""

review_columns = [
    "row_id",
    "source",
    "original_name",
    "clean_name",
    "price",
    "product_avg_price",
    "price_difference_percent",
    "is_suspicious_price",
    "seller_name",
    "location",
    "url",
    "review_status",
    "human_corrected_name",
    "human_corrected_price",
    "human_comment",
]

needs_review = needs_review[review_columns].sort_values(
    "price_difference_percent",
    key=lambda values: values.abs(),
    ascending=False,
)

needs_review.to_csv("../data/human_review_queue_10k.csv", index=False)

print("\nRows needing human review:")
print(len(needs_review))

print("\nFirst 10 review rows:")
print(
    needs_review[
        [
            "row_id",
            "source",
            "original_name",
            "price",
            "product_avg_price",
            "price_difference_percent",
            "review_status",
        ]
    ].head(10)
)

print("\nSaved review queue to ../data/human_review_queue_10k.csv")
print("\nHuman review instructions:")
print("1. Open the CSV file.")
print("2. For each row, set review_status to approved, corrected, or rejected.")
print("3. If corrected, fill human_corrected_name and/or human_corrected_price.")
print("4. Add a short note in human_comment.")
