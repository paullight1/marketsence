from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

catalog = [
    "Big Bull Rice 25kg",
    "Big Bull Rice 50kg",
    "Golden Penny Semovita 10kg",
    "Power Oil Vegetable Oil 5L",
    "Peak Milk Powder 400g Tin",
    "Dangote Refined Sugar 50kg",
    "Tecno Spark 20 128GB",
    "Samsung Galaxy A15 128GB",
    "Oraimo FreePods 4",
    "HP 15 Intel Core i5 Laptop",
]

messy_names = [
    "big bull rice 25KG promo price",
    "Power Oil Veg Oil 5 litres",
    "Samsung A15 Galaxy phone 128GB",
    "HP core i5 laptop 15 inch",
    "Rice bag local market",
    "Unknown product special offer",
]

model = SentenceTransformer("all-MiniLM-L6-v2")

catalog_embeddings = model.encode(catalog)
messy_embeddings = model.encode(messy_names)


def explain_score(score):
    if score >= 0.80:
        return "AUTO MATCH"
    elif score >= 0.60:
        return "REVIEW"
    else:
        return "NO MATCH"


print("EMBEDDINGS LESSON")
print("=" * 80)

for messy_name, messy_embedding in zip(messy_names, messy_embeddings):
    scores = cosine_similarity([messy_embedding], catalog_embeddings)[0]
    best_index = scores.argmax()
    best_match = catalog[best_index]
    best_score = float(scores[best_index])
    decision = explain_score(best_score)

    print(f"\nMessy name:   {messy_name}")
    print(f"Best match:   {best_match}")
    print(f"Similarity:   {best_score:.4f}")
    print(f"Decision:     {decision}")

