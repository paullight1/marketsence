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
