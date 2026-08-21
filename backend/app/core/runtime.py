from app.core.config import settings


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

    if errors:
        raise RuntimeError("Invalid MarketSense runtime configuration: " + "; ".join(errors))
