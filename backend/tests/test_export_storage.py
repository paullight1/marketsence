import asyncio
from io import BytesIO

from app.core.config import settings


def _set_production(monkeypatch, **overrides):
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
        "export_storage_backend": "local",
        "s3_bucket": "",
    }
    values.update(overrides)
    for key, value in values.items():
        monkeypatch.setitem(settings.__dict__, key, value)


def test_production_rejects_local_export_storage(monkeypatch):
    from app.core.runtime import validate_runtime_configuration

    _set_production(monkeypatch)

    try:
        validate_runtime_configuration()
    except RuntimeError as exc:
        assert "S3" in str(exc)
    else:
        raise AssertionError("production must require private S3-compatible export storage")


def test_s3_export_storage_writes_private_encrypted_object():
    from app.services.export_storage import S3ExportStorage

    class FakeClient:
        def __init__(self):
            self.put_calls = []

        def put_object(self, **kwargs):
            self.put_calls.append(kwargs)

        def head_bucket(self, **kwargs):
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    client = FakeClient()
    storage = S3ExportStorage(
        bucket="private-bucket",
        prefix="market-exports",
        region="eu-west-1",
        client=client,
    )

    asyncio.run(storage.ready())
    asyncio.run(storage.put("abc123", b"name,price\nRice,100\n", "rice.csv"))

    assert len(client.put_calls) == 1
    call = client.put_calls[0]
    assert call["Bucket"] == "private-bucket"
    assert call["Key"] == "market-exports/abc123.csv"
    assert call["ContentType"] == "text/csv"
    assert call["ServerSideEncryption"] == "AES256"
    assert call.get("ACL") != "public-read"
    assert call["Metadata"]["filename"] == "rice.csv"


def test_s3_export_storage_reads_private_object_metadata():
    from app.services.export_storage import S3ExportStorage

    class FakeClient:
        def get_object(self, **kwargs):
            assert kwargs == {"Bucket": "private-bucket", "Key": "exports/file-1.csv"}
            return {
                "Body": BytesIO(b"name,price\nRice,100\n"),
                "Metadata": {"filename": "cleaned-rice.csv"},
            }

    storage = S3ExportStorage(
        bucket="private-bucket",
        prefix="exports",
        region="us-east-1",
        client=FakeClient(),
    )

    stored = asyncio.run(storage.get("file-1"))

    assert stored is not None
    assert stored.content.startswith(b"name,price")
    assert stored.filename == "cleaned-rice.csv"


def test_clean_csv_api_uses_storage_backend_without_local_export(client, monkeypatch, tmp_path):
    from app.main import app
    from app.services import csv_cleaner
    from app.services.export_storage import StoredExport, get_export_storage

    class FakeStorage:
        def __init__(self):
            self.objects = {}

        async def put(self, file_id, content, filename):
            self.objects[file_id] = StoredExport(content=content, filename=filename)

        async def get(self, file_id):
            return self.objects.get(file_id)

    fake = FakeStorage()
    monkeypatch.setattr(csv_cleaner, "OUTPUT_DIR", tmp_path)
    app.dependency_overrides[get_export_storage] = lambda: fake
    try:
        response = client.post(
            "/api/ingest/clean-csv",
            files={"file": ("market.csv", "name,price\nRice,100\n", "text/csv")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["file_id"] in fake.objects
        assert list(tmp_path.glob("*.csv")) == []

        download = client.get(f"/api/ingest/clean-csv/{payload['file_id']}/download")
        assert download.status_code == 200
        assert download.text.startswith("name,price")
    finally:
        app.dependency_overrides.pop(get_export_storage, None)
