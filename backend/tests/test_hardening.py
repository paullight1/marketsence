import asyncio

import pytest

from app.core.config import settings
from app.models.models import Product, RawListing, Supplier
from conftest import TestSessionLocal


@pytest.mark.parametrize(
    "target_url",
    [
        "http://127.0.0.1:8000/internal",
        "http://10.0.0.5/private",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/internal",
    ],
)
def test_scrape_rejects_non_public_targets_before_fetch(client, monkeypatch, target_url):
    from app.api import ingest as ingest_api

    called = False

    async def fake_scrape(_payload):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(ingest_api, "scrape_price_listings", fake_scrape)

    response = client.post(
        "/api/ingest/scrape",
        json={
            "url": target_url,
            "source": "Website",
            "ingest": False,
        },
    )

    assert response.status_code == 400
    assert "public" in response.json()["detail"].lower()
    assert called is False


def test_clean_csv_rejects_upload_larger_than_configured_limit(client, monkeypatch):
    monkeypatch.setitem(settings.__dict__, "max_csv_upload_bytes", 48)
    csv_content = (
        b"source,original_name,price\n"
        + b"Jumia,Big Bull Rice 25kg,37800\n" * 4
    )

    response = client.post(
        "/api/ingest/clean-csv",
        files={"file": ("oversized.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_clean_csv_download_escapes_spreadsheet_formulas(client):
    csv_content = (
        "name,price\n"
        '"=HYPERLINK(\"\"https://attacker.example\"\",\"\"click\"\")",100\n'
    )

    response = client.post(
        "/api/ingest/clean-csv",
        files={"file": ("formulas.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()

    download_response = client.get(
        f"/api/ingest/clean-csv/{payload['file_id']}/download"
    )

    assert download_response.status_code == 200
    assert "'=HYPERLINK" in download_response.text


def test_clean_csv_export_cache_is_bounded(client, monkeypatch, tmp_path):
    from app.services import csv_cleaner

    monkeypatch.setattr(csv_cleaner, "OUTPUT_DIR", tmp_path)
    monkeypatch.setitem(settings.__dict__, "max_cleaned_csv_exports", 2)
    monkeypatch.setitem(settings.__dict__, "cleaned_csv_retention_hours", 24)

    for index in range(3):
        response = client.post(
            "/api/ingest/clean-csv",
            files={
                "file": (
                    f"sample-{index}.csv",
                    f"name,price\nRice {index},100\n",
                    "text/csv",
                )
            },
        )
        assert response.status_code == 200

    assert len(list(tmp_path.glob("*.csv"))) == 2


def test_product_list_rejects_unbounded_page_size(client):
    response = client.get("/api/products/", params={"limit": 101})

    assert response.status_code == 422


def test_ops_marks_benchmarking_blocked_until_products_are_linked(client):
    ingest_payload = {
        "listings": [
            {
                "source": "Jumia",
                "original_name": "Big Bull Rice 25kg",
                "price": 37800,
                "seller_name": "Jumia Nigeria",
                "seller_source": "website",
                "location": "Lagos",
                "url": "https://example.com/rice",
            }
        ]
    }
    ingest_response = client.post("/api/ingest/listings", json=ingest_payload)
    assert ingest_response.status_code == 200

    response = client.get("/api/ops/overview")
    assert response.status_code == 200

    benchmarking = next(
        task for task in response.json()["tasks"] if task["id"] == "benchmarking"
    )
    assert benchmarking["stage"] == "Blocked"
    assert benchmarking["progress"] == 0


def test_normalization_reports_unresolved_rows_when_catalog_is_empty(client):
    ingest_response = client.post(
        "/api/ingest/listings",
        json={
            "listings": [
                {
                    "source": "Jumia",
                    "original_name": "Golden Penny Semovita 5kg",
                    "price": 8500,
                    "seller_name": "Jumia Nigeria",
                    "seller_source": "website",
                    "location": "Lagos",
                    "url": "https://example.com/semovita",
                }
            ]
        },
    )
    assert ingest_response.status_code == 200

    response = client.post("/api/ingest/normalize")

    assert response.status_code == 200
    assert response.json()["linked_count"] == 0
    assert response.json()["new_suggestions"] == 1


def test_market_compare_returns_conflict_for_ambiguous_product_query(client):
    async def seed_products():
        async with TestSessionLocal() as db:
            db.add_all(
                [
                    Product(normalized_name="rice 25kg"),
                    Product(normalized_name="rice 50kg"),
                ]
            )
            await db.commit()

    asyncio.run(seed_products())

    response = client.get("/api/market/compare", params={"product_name": "rice"})

    assert response.status_code == 409
    assert "multiple" in response.json()["detail"].lower()


def test_benchmark_persists_extreme_outlier_once_for_review(client):
    async def seed_market_data():
        async with TestSessionLocal() as db:
            product = Product(normalized_name="rice 25kg")
            supplier = Supplier(
                name="Benchmark Supplier",
                source="seed",
                location="Lagos",
                trust_score=80,
                total_listings=5,
            )
            db.add_all([product, supplier])
            await db.flush()

            for index, price in enumerate([100.0, 99.0, 101.0, 102.0, 1000.0]):
                db.add(
                    RawListing(
                        source="seed",
                        original_name=f"Rice 25kg observation {index}",
                        price=price,
                        seller_id=supplier.id,
                        location="Lagos",
                        product_id=product.id,
                    )
                )
            await db.commit()

    asyncio.run(seed_market_data())

    first = client.post("/api/ingest/benchmark")
    second = client.post("/api/ingest/benchmark")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["updated_products"] == 1

    summary = client.get("/api/analytics/summary")
    assert summary.status_code == 200
    assert summary.json()["suspicious_prices"] == 1

    ops = client.get("/api/ops/overview")
    assert ops.status_code == 200
    review_queue = next(
        metric for metric in ops.json()["queue_metrics"] if metric["label"] == "Review queue"
    )
    assert review_queue["value"] == "1"
