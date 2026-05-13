import re
from rapidfuzz import fuzz, process

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
    "BigBull Rice 50 kg",
    "Golden  Penny  Semovita  10kg  wholesale",
    "Power Oil Veg Oil 5 litres",
    "Peak milk 400g",
    "Dangote sugar 50kg bag",
    "Tecno Spark20 128 gb",
    "Samsung A15 Galaxy phone 128GB",
    "Oraimo free pods 4",
    "HP core i5 laptop 15 inch",
    "Rice bag local market",
    "Unknown product special offer",
]


def clean_text(text):
    text = text.lower()

    # Fix common joined words
    text = text.replace("bigbull", "big bull")
    text = text.replace("spark20", "spark 20")
    text = text.replace("free pods", "freepods")

    # Normalize units
    text = text.replace("litres", "l")
    text = text.replace("liters", "l")
    text = text.replace("kg", "kg")
    text = text.replace("gb", "gb")

    # Remove marketplace/sales words
    words_to_remove = [
        "promo",
        "price",
        "wholesale",
        "special",
        "offer",
        "bag",
        "phone",
        "local",
        "market",
    ]

    for word in words_to_remove:
        text = re.sub(rf"\b{word}\b", " ", text)

    # Remove punctuation
    text = re.sub(r"[^a-z0-9\s]+", " ", text)

    # Fix spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def explain_score(score):
    if score >= 85:
        return "AUTO MATCH"
    elif score >= 70:
        return "REVIEW"
    else:
        return "NO MATCH"


clean_catalog = [clean_text(name) for name in catalog]

print("FUZZY MATCHING WITH CLEANING")
print("=" * 80)

for messy_name in messy_names:
    cleaned_messy_name = clean_text(messy_name)

    best_match = process.extractOne(
        cleaned_messy_name,
        clean_catalog,
        scorer=fuzz.token_set_ratio,
    )

    matched_clean_name, score, index = best_match
    matched_original_name = catalog[index]
    decision = explain_score(score)

    print(f"\nOriginal messy name: {messy_name}")
    print(f"Cleaned messy name:  {cleaned_messy_name}")
    print(f"Best match:          {matched_original_name}")
    print(f"Score:               {score}")
    print(f"Decision:            {decision}")
