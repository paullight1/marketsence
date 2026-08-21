import asyncio
from collections import Counter

from sqlalchemy import func, select

from app.models.models import Job, RawListing, Supplier, utc_now
from conftest import TestSessionLocal


def _listing(*, external_id=None):
    item = {
        "source": "Manual",
        "original_name": "Idempotent Rice 25kg",
        "price": "37800.00",
        "seller_name": "Idempotent Supplier",
        "seller_source": "manual",
        "location": "Lagos",
        "url": "https://example.com/rice",
    }
    if external_id is not None:
        item["external_id"] = external_id
    return item


def test_supplier_identity_and_listing_ingestion_key_are_database_unique():
    supplier_unique = {
        tuple(constraint.columns.keys())
        for constraint in Supplier.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    listing_unique = {
        tuple(constraint.columns.keys())
        for constraint in RawListing.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("name", "source") in supplier_unique
    assert ("ingestion_key",) in listing_unique


def test_same_request_idempotency_key_does_not_duplicate_listings(client):
    headers = {"Idempotency-Key": "sync-import-20260821-001"}
    payload = {"listings": [_listing()]}

    first = client.post("/api/ingest/listings", json=payload, headers=headers)
    second = client.post("/api/ingest/listings", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["added"] == 1
    assert second.json()["added"] == 0

    suppliers = client.get("/api/suppliers/").json()
    assert len(suppliers) == 1
    assert suppliers[0]["total_listings"] == 1


def test_external_listing_id_dedupes_across_different_request_keys(client):
    payload = {"listings": [_listing(external_id="source-row-42")]}

    first = client.post(
        "/api/ingest/listings",
        json=payload,
        headers={"Idempotency-Key": "request-a"},
    )
    second = client.post(
        "/api/ingest/listings",
        json=payload,
        headers={"Idempotency-Key": "request-b"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["added"] == 1
    assert second.json()["added"] == 0


def test_duplicate_external_ids_inside_one_batch_insert_once(client):
    payload = {
        "listings": [
            _listing(external_id="duplicate-row"),
            _listing(external_id="duplicate-row"),
        ]
    }

    response = client.post(
        "/api/ingest/listings",
        json=payload,
        headers={"Idempotency-Key": "batch-with-duplicate"},
    )

    assert response.status_code == 200
    assert response.json()["added"] == 1
    suppliers = client.get("/api/suppliers/").json()
    assert suppliers[0]["total_listings"] == 1


def test_durable_ingest_job_retry_does_not_reinsert_committed_rows(client):
    queued = client.post(
        "/api/jobs/ingest",
        json={"listings": [_listing()]},
        headers={"Idempotency-Key": "durable-import-retry-1"},
    )
    assert queued.status_code == 202
    job_id = queued.json()["id"]

    async def run_and_force_retry():
        from app.services.jobs import run_one_job

        first = await run_one_job(TestSessionLocal, worker_id="worker-one")
        async with TestSessionLocal() as db:
            job = await db.get(Job, job_id)
            assert job is not None
            assert job.status == "completed"
            job.status = "retrying"
            job.completed_at = None
            job.result = None
            job.error = "simulated crash after data commit"
            job.available_at = utc_now()
            await db.commit()
        second = await run_one_job(TestSessionLocal, worker_id="worker-two")

        async with TestSessionLocal() as db:
            listing_count = int(
                (await db.execute(select(func.count(RawListing.id)))).scalar() or 0
            )
            suppliers = list((await db.execute(select(Supplier))).scalars().all())
            totals = Counter({supplier.id: supplier.total_listings for supplier in suppliers})
            job = await db.get(Job, job_id)
            return first, second, listing_count, suppliers, totals, job

    first, second, listing_count, suppliers, totals, job = asyncio.run(run_and_force_retry())

    assert first is True
    assert second is True
    assert listing_count == 1
    assert len(suppliers) == 1
    assert list(totals.values()) == [1]
    assert job is not None
    assert job.status == "completed"
