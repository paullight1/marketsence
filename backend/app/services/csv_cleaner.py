import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "cleaned_uploads"

NAME_COLUMNS = [
    "original_name",
    "product_name",
    "product",
    "name",
    "title",
    "item_name",
    "description",
]
PRICE_COLUMNS = ["price", "amount", "listing_price", "current_price", "cost"]
DATE_COLUMNS = ["scraped_at", "created_at", "date", "listed_at", "timestamp"]
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def clean_uploaded_csv(content: bytes, original_filename: str | None) -> dict[str, Any]:
    if not content:
        raise ValueError("Uploaded CSV is empty")

    try:
        df = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise ValueError(f"Could not read CSV: {exc}") from exc

    if df.empty:
        raise ValueError("CSV has headers but no rows")

    rows_before = len(df)
    missing_before = _missing_counts(df)

    df.columns = _unique_column_names(
        [_normalize_column_name(column) for column in df.columns]
    )
    for column in df.select_dtypes(include=["object"]).columns:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    name_column = _first_existing(df, NAME_COLUMNS)
    price_column = _first_existing(df, PRICE_COLUMNS)
    date_column = _first_existing(df, DATE_COLUMNS)

    if name_column:
        df["clean_name"] = df[name_column].fillna("").map(_clean_name)

    if price_column:
        df["clean_price"] = df[price_column].map(_clean_price)

    if date_column:
        df["clean_date"] = pd.to_datetime(df[date_column], errors="coerce", utc=True)
        df["clean_date"] = df["clean_date"].dt.date.astype("string")

    if "location" in df.columns:
        df["location"] = df["location"].fillna("Unknown")

    dedupe_subset = [
        column
        for column in ["source", "clean_name", "clean_price", "seller_name", "location", "url"]
        if column in df.columns
    ]
    if not dedupe_subset:
        dedupe_subset = list(df.columns)

    df = df.drop_duplicates(subset=dedupe_subset)
    rows_after = len(df)

    missing_after = _missing_counts(df)
    file_id = uuid.uuid4().hex
    safe_name = _safe_filename(original_filename or "uploaded.csv")
    output_name = f"{file_id}_{safe_name.replace('.csv', '')}_cleaned.csv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_name

    export_df = df.copy()
    for column in export_df.select_dtypes(include=["object", "string"]).columns:
        export_df[column] = export_df[column].map(_escape_spreadsheet_formula)
    export_df.to_csv(output_path, index=False)

    preview = df.head(12).where(pd.notnull(df), None).to_dict(orient="records")

    return {
        "file_id": file_id,
        "download_filename": output_name,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "duplicates_removed": rows_before - rows_after,
        "columns": list(df.columns),
        "detected_name_column": name_column,
        "detected_price_column": price_column,
        "detected_date_column": date_column,
        "missing_before": missing_before,
        "missing_after": missing_after,
        "preview": preview,
        "message": "CSV cleaned successfully",
    }


def get_cleaned_csv_path(file_id: str) -> Path | None:
    if not re.fullmatch(r"[a-f0-9]{32}", file_id):
        return None

    matches = list(OUTPUT_DIR.glob(f"{file_id}_*.csv"))
    if not matches:
        return None
    return matches[0]


def _normalize_column_name(column: object) -> str:
    normalized = str(column).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_") or "column"


def _unique_column_names(columns: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    unique: list[str] = []
    for column in columns:
        seen[column] = seen.get(column, 0) + 1
        count = seen[column]
        unique.append(column if count == 1 else f"{column}_{count}")
    return unique


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def _clean_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value).lower()
    text = re.sub(r"\b(promo|price|wholesale|special|offer|buy now|shop now)\b", " ", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_price(value: object) -> float | None:
    if pd.isna(value):
        return None

    text = str(value).replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0))


def _escape_spreadsheet_formula(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(FORMULA_PREFIXES):
        return f"'{value}"
    return value


def _missing_counts(df: pd.DataFrame) -> dict[str, int]:
    return {str(key): int(value) for key, value in df.isna().sum().to_dict().items()}


def _safe_filename(filename: str) -> str:
    base = Path(filename).name.lower()
    base = re.sub(r"[^a-z0-9_.-]+", "_", base)
    if not base.endswith(".csv"):
        base = f"{base}.csv"
    return base
