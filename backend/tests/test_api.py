def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ingest_then_read_products(client):
    ingest_payload = {
        "listings": [
            {
                "source": "Jumia",
                "original_name": "Dangote Sugar 50kg bag",
                "price": 85000,
                "seller_name": "Jumia Nigeria",
                "seller_source": "online",
                "location": "Lagos",
                "url": "https://example.com/dangote-sugar",
            }
        ]
    }

    ingest_response = client.post("/api/ingest/listings", json=ingest_payload)
    suppliers_response = client.get("/api/suppliers")

    assert ingest_response.status_code == 200
    assert ingest_response.json()["added"] == 1
    assert suppliers_response.status_code == 200
    assert suppliers_response.json()[0]["name"] == "Jumia Nigeria"


def test_bulk_ingest_reuses_one_supplier_and_counts_the_batch(client):
    ingest_payload = {
        "listings": [
            {
                "source": "Market survey",
                "original_name": f"Rice observation {index}",
                "price": 40000 + index,
                "seller_name": "Balogun Market Seller",
                "seller_source": "field",
                "location": "Lagos",
                "url": f"https://example.com/rice/{index}",
            }
            for index in range(25)
        ]
    }

    ingest_response = client.post("/api/ingest/listings", json=ingest_payload)
    suppliers_response = client.get("/api/suppliers")

    assert ingest_response.status_code == 200
    assert ingest_response.json()["added"] == 25
    assert suppliers_response.status_code == 200
    assert len(suppliers_response.json()) == 1
    assert suppliers_response.json()[0]["total_listings"] == 25


def test_product_search_route_is_not_shadowed_by_id_route(client):
    payload = {
        "listings": [
            {
                "source": "Manual",
                "original_name": "Indomie Onion Flavor 70g x 40",
                "price": 12500,
                "seller_name": "Market Seller",
                "seller_source": "market",
                "location": "Ibadan",
                "url": "https://example.com/indomie",
            }
        ]
    }
    client.post("/api/ingest/listings", json=payload)

    response = client.get("/api/products/search", params={"q": "Indomie"})

    assert response.status_code == 200
    assert response.json() == []


def test_scrape_endpoint_ingests_extracted_listings(client, monkeypatch):
    from app.api import ingest as ingest_api
    from app.schemas import ListingInput

    async def fake_scrape(_payload):
        return [
            ListingInput(
                source="Website",
                original_name="Golden Penny Semovita 10kg",
                price=18500,
                seller_name="market.example",
                seller_source="website",
                location="Lagos",
                url="https://market.example/products",
            )
        ]

    monkeypatch.setattr(ingest_api, "scrape_price_listings", fake_scrape)

    response = client.post(
        "/api/ingest/scrape",
        json={
            "url": "https://market.example/products",
            "source": "Website",
            "location": "Lagos",
            "ingest": True,
        },
    )
    suppliers_response = client.get("/api/suppliers")

    assert response.status_code == 200
    assert response.json()["scraped"] == 1
    assert response.json()["ingested"] == 1
    assert suppliers_response.json()[0]["name"] == "market.example"


def test_clean_csv_upload_returns_preview_and_download(client):
    csv_content = (
        "source,original_name,price,seller_name,location,scraped_at\n"
        "Jumia,Big Bull Rice 25KG promo price,\"NGN 37,800\",Jumia Nigeria,Lagos,2026-05-13\n"
        "Jumia,Big Bull Rice 25KG promo price,\"NGN 37,800\",Jumia Nigeria,Lagos,2026-05-13\n"
        "Konga,Golden Penny Semovita 10kg wholesale,20250,Konga Store,,2026-05-12\n"
    )

    response = client.post(
        "/api/ingest/clean-csv",
        files={"file": ("messy.csv", csv_content, "text/csv")},
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["rows_before"] == 3
    assert payload["rows_after"] == 2
    assert payload["duplicates_removed"] == 1
    assert payload["detected_name_column"] == "original_name"
    assert payload["detected_price_column"] == "price"
    assert payload["preview"][0]["clean_name"] == "big bull rice 25kg"
    assert payload["preview"][1]["location"] == "Unknown"

    download_response = client.get(
        f"/api/ingest/clean-csv/{payload['file_id']}/download"
    )

    assert download_response.status_code == 200
    assert "clean_name" in download_response.text


def test_ops_overview_returns_live_workflow_state(client):
    payload = {
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
    client.post("/api/ingest/listings", json=payload)

    response = client.get("/api/ops/overview")
    body = response.json()

    assert response.status_code == 200
    assert body["queue_metrics"][0]["label"] == "Raw listings"
    assert body["recent_listings"][0]["product_name"] == "Big Bull Rice 25kg"
    assert any(task["id"] == "normalization" for task in body["tasks"])
