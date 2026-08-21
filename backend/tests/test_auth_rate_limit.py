import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


TEST_USERNAME = "market-admin"
TEST_PASSWORD = "test-password-123!"
TEST_PASSWORD_HASH = (
    "scrypt$16384$8$1$"
    "bWFya2V0c2Vuc2UtdGVzdC1zYWx0$"
    "q0eE3oKhZBRySI5umrgMEt4PO-J_UxqoBacaPppdKNk"
)


def _set(monkeypatch, **values):
    for key, value in values.items():
        monkeypatch.setitem(settings.__dict__, key, value)


def _enable_auth(monkeypatch, *, role="admin", rate_limit=False, login_limit=5):
    _set(
        monkeypatch,
        environment="test",
        auth_enabled=True,
        auth_secret="test-secret-" + ("x" * 64),
        auth_username=TEST_USERNAME,
        auth_password_hash=TEST_PASSWORD_HASH,
        auth_role=role,
        auth_token_ttl_minutes=30,
        rate_limit_enabled=rate_limit,
        auth_login_limit_per_minute=login_limit,
        read_limit_per_minute=120,
        write_limit_per_minute=30,
        redis_url=None,
    )


def _login(client):
    return client.post(
        "/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )


def _listing_payload():
    return {
        "listings": [
            {
                "source": "Manual",
                "original_name": "Big Bull Rice 25kg",
                "price": 37800,
                "seller_name": "Market Admin Test",
                "seller_source": "manual",
                "location": "Lagos",
                "url": "https://example.com/rice",
            }
        ]
    }


def test_write_routes_require_bearer_auth_when_enabled(client, monkeypatch):
    _enable_auth(monkeypatch)

    response = client.post("/api/ingest/listings", json=_listing_payload())

    assert response.status_code == 401
    assert "authorization" in response.json()["detail"].lower()


def test_login_issues_bearer_token_that_allows_admin_write(client, monkeypatch):
    _enable_auth(monkeypatch)

    login = _login(client)
    assert login.status_code == 200
    payload = login.json()
    assert payload["token_type"] == "bearer"
    assert payload["role"] == "admin"
    assert payload["expires_in"] > 0

    response = client.post(
        "/api/ingest/listings",
        json=_listing_payload(),
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["added"] == 1


def test_viewer_can_read_but_cannot_run_write_pipeline(client, monkeypatch):
    _enable_auth(monkeypatch, role="viewer")
    login = _login(client)
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    read_response = client.get("/api/analytics/summary", headers=headers)
    write_response = client.post("/api/ingest/normalize", headers=headers)

    assert read_response.status_code == 200
    assert write_response.status_code == 403
    assert "role" in write_response.json()["detail"].lower()


def test_access_token_cookie_is_not_accepted_as_authentication(client, monkeypatch):
    _enable_auth(monkeypatch)
    login = _login(client)
    assert login.status_code == 200
    token = login.json()["access_token"]

    client.cookies.set("access_token", token)
    response = client.post("/api/ingest/listings", json=_listing_payload())

    assert response.status_code == 401


def test_invalid_credentials_fail_closed(client, monkeypatch):
    _enable_auth(monkeypatch)

    response = client.post(
        "/api/auth/login",
        json={"username": TEST_USERNAME, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


def test_login_endpoint_is_rate_limited(client, monkeypatch):
    _enable_auth(monkeypatch, rate_limit=True, login_limit=2)

    statuses = []
    for _ in range(3):
        response = client.post(
            "/api/auth/login",
            json={"username": TEST_USERNAME, "password": "wrong-password"},
        )
        statuses.append(response.status_code)

    assert statuses[:2] == [401, 401]
    assert statuses[2] == 429


def test_production_startup_fails_without_auth_and_distributed_limiter(monkeypatch):
    _set(
        monkeypatch,
        environment="production",
        auth_enabled=False,
        auth_secret="",
        auth_username="",
        auth_password_hash="",
        redis_url=None,
        rate_limit_enabled=True,
    )

    app = create_app()
    with pytest.raises(RuntimeError):
        with TestClient(app, raise_server_exceptions=True):
            pass
