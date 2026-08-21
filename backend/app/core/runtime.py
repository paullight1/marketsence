import re

from app.core.config import settings


_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}\.?$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.?$",
    re.IGNORECASE,
)


def _normalized_hostname(value: str) -> str | None:
    hostname = value.strip().rstrip(".").lower()
    if not hostname or not _HOSTNAME_RE.fullmatch(hostname):
        return None
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return None
    return hostname


def _domain_is_within(domain: str, allowed_domains: set[str]) -> bool:
    return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in allowed_domains)


def validate_runtime_configuration() -> None:
    errors: list[str] = []

    if settings.auth_enabled:
        if len(settings.auth_secret) < 32:
            errors.append("AUTH_SECRET must contain at least 32 characters")
        if not settings.auth_username:
            errors.append("AUTH_USERNAME is required when authentication is enabled")
        if not settings.auth_password_hash.startswith("scrypt$"):
            errors.append("AUTH_PASSWORD_HASH must be a generated scrypt hash")

    if settings.environment == "production":
        if not settings.auth_enabled:
            errors.append("AUTH_ENABLED must be true in production")
        if not settings.rate_limit_enabled:
            errors.append("RATE_LIMIT_ENABLED must be true in production")
        if not settings.redis_url:
            errors.append("REDIS_URL is required for distributed production rate limiting")
        if not settings.background_jobs_enabled:
            errors.append("BACKGROUND_JOBS_ENABLED must be true in production")
        if not settings.database_url.startswith("postgresql+asyncpg://"):
            errors.append("Production DATABASE_URL must use PostgreSQL via postgresql+asyncpg://")
        if settings.export_storage_backend != "s3":
            errors.append("Production cleaned exports require private S3-compatible object storage")
        if not settings.s3_bucket:
            errors.append("S3_BUCKET is required for private S3-compatible export storage")

        if not settings.scrape_allowed_domains:
            errors.append("SCRAPE_ALLOWED_DOMAINS must contain at least one approved hostname in production")
        normalized_allowed: set[str] = set()
        invalid_allowed: list[str] = []
        for entry in settings.scrape_allowed_domains:
            hostname = _normalized_hostname(entry)
            if hostname is None:
                invalid_allowed.append(entry)
            else:
                normalized_allowed.add(hostname)
        if invalid_allowed:
            errors.append(
                "SCRAPE_ALLOWED_DOMAINS entries must be bare hostnames without schemes, paths, ports, or wildcards: "
                + ", ".join(invalid_allowed)
            )

        if settings.browser_scraper_enabled:
            if not settings.browser_scrape_allowed_domains:
                errors.append("BROWSER_SCRAPE_ALLOWED_DOMAINS must be non-empty when browser scraping is enabled")
            for entry in settings.browser_scrape_allowed_domains:
                hostname = _normalized_hostname(entry)
                if hostname is None:
                    errors.append(
                        "BROWSER_SCRAPE_ALLOWED_DOMAINS entries must be bare hostnames without schemes, paths, ports, or wildcards"
                    )
                    continue
                if normalized_allowed and not _domain_is_within(hostname, normalized_allowed):
                    errors.append(
                        "BROWSER_SCRAPE_ALLOWED_DOMAINS must stay within SCRAPE_ALLOWED_DOMAINS"
                    )
                    break

    if errors:
        raise RuntimeError("Invalid MarketSense runtime configuration: " + "; ".join(errors))
