import pytest

from app.core.config import settings


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
    monkeypatch.setattr(settings, "max_csv_upload_bytes", 48, raising=False)
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
