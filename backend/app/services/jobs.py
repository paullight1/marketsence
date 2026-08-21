import asyncio
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Job, utc_now
from app.schemas import BulkListingsInput, ScrapeRequest
from app.services.analytics import calculate_market_benchmarks
from app.services.ingest import ingest_listings
from app.services.normalizer import normalize_all_listings
from app.services.scraper import scrape_price_listings, validate_scrape_target_syntax


RUNNABLE_STATUSES = ("queued", "retrying")
TERMINAL_STATUSES = ("completed", "failed", "cancelled")


async def enqueue_job(
    db: AsyncSession,
    *,
    job_type: str,
    payload: dict[str, Any],
    idempotency_key: str | None = None,
    max_attempts: int | None = None,
) -> Job:
    if idempotency_key:
        existing = await db.execute(
            select(Job).where(
                Job.job_type == job_type,
                Job.idempotency_key == idempotency_key,
            )
        )
        found = existing.scalar_one_or_none()
        if found:
            return found

    job = Job(
        job_type=job_type,
        payload=payload,
        idempotency_key=idempotency_key,
        max_attempts=max_attempts or settings.job_default_max_attempts,
    )
    db.add(job)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        if not idempotency_key:
            raise
        result = await db.execute(
            select(Job).where(
                Job.job_type == job_type,
                Job.idempotency_key == idempotency_key,
            )
        )
        found = result.scalar_one_or_none()
        if not found:
            raise
        return found
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: str) -> Job | None:
    return await db.get(Job, job_id)


async def list_jobs(db: AsyncSession, *, limit: int = 50) -> list[Job]:
    result = await db.execute(
        select(Job).order_by(Job.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def cancel_job(db: AsyncSession, job_id: str) -> Job | None:
    job = await db.get(Job, job_id)
    if not job:
        return None
    if job.status in TERMINAL_STATUSES:
        return job
    job.cancel_requested = True
    if job.status in RUNNABLE_STATUSES:
        job.status = "cancelled"
        job.completed_at = utc_now()
        job.worker_id = None
        job.lease_expires_at = None
    await db.commit()
    await db.refresh(job)
    return job


async def recover_stale_jobs(db: AsyncSession) -> int:
    now = utc_now()
    result = await db.execute(
        select(Job).where(
            Job.status == "running",
            Job.lease_expires_at.is_not(None),
            Job.lease_expires_at < now,
        )
    )
    jobs = list(result.scalars().all())
    for job in jobs:
        job.worker_id = None
        job.lease_expires_at = None
        if job.cancel_requested:
            job.status = "cancelled"
            job.completed_at = now
        elif job.attempts >= job.max_attempts:
            job.status = "failed"
            job.error = job.error or "Worker lease expired after final attempt"
            job.completed_at = now
        else:
            job.status = "retrying"
            job.available_at = now
            job.error = job.error or "Worker lease expired; job returned to queue"
    if jobs:
        await db.commit()
    return len(jobs)


async def claim_next_job(db: AsyncSession, *, worker_id: str) -> Job | None:
    now = utc_now()
    query = (
        select(Job)
        .where(
            Job.status.in_(RUNNABLE_STATUSES),
            Job.available_at <= now,
            Job.cancel_requested.is_(False),
        )
        .order_by(Job.available_at, Job.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    if not job:
        return None

    job.status = "running"
    job.attempts += 1
    job.worker_id = worker_id
    job.started_at = job.started_at or now
    job.lease_expires_at = now + timedelta(seconds=settings.job_lease_seconds)
    await db.commit()
    await db.refresh(job)
    return job


async def _execute_job(db: AsyncSession, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if job_type == "normalize":
        linked, suggested = await normalize_all_listings(db)
        return {"linked_count": linked, "new_suggestions": suggested}

    if job_type == "benchmark":
        updated = await calculate_market_benchmarks(db)
        return {"updated_products": updated}

    if job_type == "ingest":
        validated = BulkListingsInput.model_validate(payload)
        added = await ingest_listings(db, validated)
        return {"added": added}

    if job_type == "scrape":
        request = ScrapeRequest.model_validate(payload)
        validate_scrape_target_syntax(request.url)
        listings = await scrape_price_listings(request)
        ingested = 0
        if request.ingest and listings:
            ingested = await ingest_listings(
                db,
                BulkListingsInput(listings=listings),
            )
        return {
            "scraped": len(listings),
            "ingested": ingested,
            "listings": [listing.model_dump(mode="json") for listing in listings],
        }

    raise ValueError(f"Unknown job type: {job_type}")


async def run_one_job(session_factory, *, worker_id: str) -> bool:
    async with session_factory() as claim_db:
        await recover_stale_jobs(claim_db)
        job = await claim_next_job(claim_db, worker_id=worker_id)
        if not job:
            return False
        job_id = job.id
        job_type = job.job_type
        payload = dict(job.payload or {})

    try:
        async with session_factory() as work_db:
            result_payload = await _execute_job(work_db, job_type, payload)
    except Exception as exc:
        async with session_factory() as failure_db:
            current = await failure_db.get(Job, job_id)
            if current:
                current.worker_id = None
                current.lease_expires_at = None
                current.error = str(exc)[:4000]
                if current.cancel_requested:
                    current.status = "cancelled"
                    current.completed_at = utc_now()
                elif current.attempts >= current.max_attempts:
                    current.status = "failed"
                    current.completed_at = utc_now()
                else:
                    current.status = "retrying"
                    delay = settings.job_retry_base_seconds * (2 ** max(current.attempts - 1, 0))
                    current.available_at = utc_now() + timedelta(seconds=delay)
                await failure_db.commit()
        return True

    async with session_factory() as complete_db:
        current = await complete_db.get(Job, job_id)
        if current:
            current.worker_id = None
            current.lease_expires_at = None
            if current.cancel_requested:
                current.status = "cancelled"
            else:
                current.status = "completed"
                current.result = result_payload
                current.error = None
            current.completed_at = utc_now()
            await complete_db.commit()
    return True


async def run_worker_forever(session_factory, *, worker_id: str) -> None:
    while True:
        processed = await run_one_job(session_factory, worker_id=worker_id)
        if not processed:
            await asyncio.sleep(settings.job_poll_seconds)
