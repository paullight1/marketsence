import asyncio
from datetime import timedelta

from app.core.config import settings
from app.models.models import RawListing, Supplier, utc_now
from conftest import TestSessionLocal


def test_normalization_job_is_persisted_and_retrievable(client):
    response = client.post(
        "/api/jobs/normalize",
        headers={"Idempotency-Key": "normalize-run-1"},
    )

    assert response.status_code == 202
    job = response.json()
    assert job["job_type"] == "normalize"
    assert job["status"] == "queued"

    fetched = client.get(f"/api/jobs/{job['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == job["id"]


def test_enqueue_is_idempotent_for_same_key(client):
    headers = {"Idempotency-Key": "benchmark-day-2026-08-21"}

    first = client.post("/api/jobs/benchmark", headers=headers)
    second = client.post("/api/jobs/benchmark", headers=headers)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]


def test_queued_job_can_be_cancelled(client):
    created = client.post("/api/jobs/normalize").json()

    response = client.post(f"/api/jobs/{created['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_worker_executes_normalization_job_to_completion(client):
    async def seed_listing():
        from app.models.models import Product

        async with TestSessionLocal() as db:
            product = Product(normalized_name="rice 25kg")
            supplier = Supplier(name="Worker Supplier", source="test", total_listings=1)
            db.add_all([product, supplier])
            await db.flush()
            db.add(
                RawListing(
                    source="test",
                    original_name="Rice 25kg bag",
                    price=37_800,
                    seller_id=supplier.id,
                    product_id=None,
                )
            )
            await db.commit()

    async def run_job():
        from app.services.jobs import run_one_job

        return await run_one_job(TestSessionLocal, worker_id="test-worker")

    asyncio.run(seed_listing())
    created = client.post("/api/jobs/normalize").json()

    processed = asyncio.run(run_job())

    assert processed is True
    fetched = client.get(f"/api/jobs/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "completed"
    assert fetched.json()["result"]["linked_count"] == 1


def test_worker_failure_retries_then_exhausts_attempts(client):
    async def create_and_run():
        from app.services.jobs import enqueue_job, run_one_job

        async with TestSessionLocal() as db:
            job = await enqueue_job(
                db,
                job_type="scrape",
                payload={"url": "http://127.0.0.1/private", "ingest": False},
                max_attempts=1,
            )
            job_id = job.id

        processed = await run_one_job(TestSessionLocal, worker_id="test-worker")
        return job_id, processed

    job_id, processed = asyncio.run(create_and_run())

    assert processed is True
    fetched = client.get(f"/api/jobs/{job_id}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "failed"
    assert fetched.json()["attempts"] == 1
    assert fetched.json()["error"]


def test_stale_running_lease_is_recovered(client):
    async def create_and_stale():
        from app.services.jobs import enqueue_job, recover_stale_jobs

        async with TestSessionLocal() as db:
            job = await enqueue_job(db, job_type="normalize", payload={})
            job.status = "running"
            job.attempts = 1
            job.worker_id = "dead-worker"
            job.lease_expires_at = utc_now() - timedelta(minutes=5)
            await db.commit()
            job_id = job.id

        async with TestSessionLocal() as db:
            recovered = await recover_stale_jobs(db)
            return job_id, recovered

    job_id, recovered = asyncio.run(create_and_stale())

    assert recovered == 1
    fetched = client.get(f"/api/jobs/{job_id}")
    assert fetched.json()["status"] == "retrying"
    assert fetched.json()["worker_id"] is None


def test_large_sync_import_is_redirected_to_job_api(client, monkeypatch):
    monkeypatch.setitem(settings.__dict__, "sync_ingest_max_listings", 2)
    listings = [
        {
            "source": "Manual",
            "original_name": f"Rice observation {index}",
            "price": 1000 + index,
            "seller_name": "Large Import Seller",
            "seller_source": "manual",
        }
        for index in range(3)
    ]

    response = client.post("/api/ingest/listings", json={"listings": listings})

    assert response.status_code == 413
    assert "/api/jobs/ingest" in response.json()["detail"]

    queued = client.post(
        "/api/jobs/ingest",
        json={"listings": listings},
        headers={"Idempotency-Key": "large-import-1"},
    )
    assert queued.status_code == 202
    assert queued.json()["job_type"] == "ingest"


def test_production_requires_background_jobs(monkeypatch):
    from app.core.runtime import validate_runtime_configuration

    values = {
        "environment": "production",
        "auth_enabled": True,
        "auth_secret": "x" * 64,
        "auth_username": "admin",
        "auth_password_hash": "scrypt$16384$8$1$ZmFrZQ$ZmFrZQ",
        "rate_limit_enabled": True,
        "redis_url": "redis://localhost:6379/0",
        "background_jobs_enabled": False,
    }
    for key, value in values.items():
        monkeypatch.setitem(settings.__dict__, key, value)

    try:
        validate_runtime_configuration()
    except RuntimeError as exc:
        assert "BACKGROUND_JOBS_ENABLED" in str(exc)
    else:
        raise AssertionError("production configuration must require background jobs")
