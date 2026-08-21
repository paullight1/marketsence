from pathlib import Path

from app.core.config import settings


REPO_ROOT = Path(__file__).resolve().parents[2]


def _production_values(**overrides):
    values = {
        "environment": "production",
        "database_url": "postgresql+asyncpg://user:pass@db/marketsense",
        "auth_enabled": True,
        "auth_secret": "x" * 64,
        "auth_username": "admin",
        "auth_password_hash": "scrypt$16384$8$1$ZmFrZQ$ZmFrZQ",
        "rate_limit_enabled": True,
        "redis_url": "redis://redis:6379/0",
        "background_jobs_enabled": True,
        "export_storage_backend": "s3",
        "s3_bucket": "private-market-exports",
        "scrape_allowed_domains": [],
        "browser_scraper_enabled": False,
        "browser_scrape_allowed_domains": [],
    }
    values.update(overrides)
    return values


def _apply(monkeypatch, values):
    for key, value in values.items():
        monkeypatch.setitem(settings.__dict__, key, value)


def test_production_requires_nonempty_scrape_allowlist(monkeypatch):
    from app.core.runtime import validate_runtime_configuration

    _apply(monkeypatch, _production_values())

    try:
        validate_runtime_configuration()
    except RuntimeError as exc:
        assert "SCRAPE_ALLOWED_DOMAINS" in str(exc)
    else:
        raise AssertionError("production must require an explicit scrape-domain allowlist")


def test_production_rejects_malformed_allowlist_entries(monkeypatch):
    from app.core.runtime import validate_runtime_configuration

    _apply(
        monkeypatch,
        _production_values(scrape_allowed_domains=["https://example.com", "*.shop.example"]),
    )

    try:
        validate_runtime_configuration()
    except RuntimeError as exc:
        message = str(exc)
        assert "SCRAPE_ALLOWED_DOMAINS" in message
        assert "hostname" in message.lower()
    else:
        raise AssertionError("allowlist entries must be bare hostnames")


def test_browser_allowlist_must_be_subset_of_scrape_allowlist(monkeypatch):
    from app.core.runtime import validate_runtime_configuration

    _apply(
        monkeypatch,
        _production_values(
            scrape_allowed_domains=["example.com"],
            browser_scraper_enabled=True,
            browser_scrape_allowed_domains=["untrusted.example.net"],
        ),
    )

    try:
        validate_runtime_configuration()
    except RuntimeError as exc:
        assert "BROWSER_SCRAPE_ALLOWED_DOMAINS" in str(exc)
    else:
        raise AssertionError("browser scraping must stay inside the production scrape allowlist")


def test_valid_production_allowlists_pass_runtime_validation(monkeypatch):
    from app.core.runtime import validate_runtime_configuration

    _apply(
        monkeypatch,
        _production_values(
            scrape_allowed_domains=["example.com", "shop.example.org"],
            browser_scraper_enabled=True,
            browser_scrape_allowed_domains=["shop.example.org"],
        ),
    )

    validate_runtime_configuration()


def test_kubernetes_egress_policy_blocks_private_and_metadata_ranges():
    policy_path = REPO_ROOT / "deploy" / "kubernetes" / "network-policy.yaml"
    text = policy_path.read_text(encoding="utf-8")

    for blocked_range in [
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "198.18.0.0/15",
    ]:
        assert blocked_range in text

    assert "protocol: TCP" in text
    assert "port: 80" in text
    assert "port: 443" in text
    assert "protocol: UDP" in text
    assert "port: 53" in text
