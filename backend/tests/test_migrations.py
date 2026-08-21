import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from app.core.config import settings


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _production_values(database_url: str):
    return {
        "environment": "production",
        "database_url": database_url,
        "auth_enabled": True,
        "auth_secret": "x" * 64,
        "auth_username": "admin",
        "auth_password_hash": "scrypt$16384$8$1$ZmFrZQ$ZmFrZQ",
        "rate_limit_enabled": True,
        "redis_url": "redis://localhost:6379/0",
        "background_jobs_enabled": True,
    }


def test_production_requires_postgresql(monkeypatch):
    from app.core.runtime import validate_runtime_configuration

    for key, value in _production_values("sqlite+aiosqlite:///./marketsense.db").items():
        monkeypatch.setitem(settings.__dict__, key, value)

    try:
        validate_runtime_configuration()
    except RuntimeError as exc:
        assert "PostgreSQL" in str(exc)
    else:
        raise AssertionError("production must reject SQLite")


def test_application_schema_autocreate_is_disabled_in_production(monkeypatch):
    from app.db.database import should_auto_create_schema

    monkeypatch.setitem(settings.__dict__, "environment", "production")
    assert should_auto_create_schema() is False

    monkeypatch.setitem(settings.__dict__, "environment", "test")
    assert should_auto_create_schema() is True


def test_alembic_upgrade_head_creates_complete_schema(tmp_path):
    database_path = tmp_path / "migration-smoke.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{database_path}"
    env["ENVIRONMENT"] = "test"

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert {
        "alembic_version",
        "categories",
        "products",
        "suppliers",
        "raw_listings",
        "price_history",
        "suspicious_listings",
        "jobs",
    }.issubset(tables)
