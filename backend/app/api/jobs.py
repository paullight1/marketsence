from datetime import datetime
from typing import Annotated, Any
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db.database import get_db
from app.models.models import Job
from app.schemas import BulkListingsInput, ScrapeRequest
from app.services.jobs import cancel_job, enqueue_job, get_job, list_jobs

router = APIRouter()


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_type: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    idempotency_key: str | None = None
    attempts: int
    max_attempts: int
    available_at: datetime
    lease_expires_at: datetime | None = None
    worker_id: str | None = None
    cancel_requested: bool
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


async def _enqueue(db: AsyncSession, *, job_type: str, payload: dict[str, Any], idempotency_key: str | None) -> Job:
    return await enqueue_job(db, job_type=job_type, payload=payload, idempotency_key=idempotency_key)


@router.get("/", response_model=list[JobResponse])
async def jobs_list(db: AsyncSession = Depends(get_db), limit: int = Query(default=50, ge=1, le=100)):
    return await list_jobs(db, limit=limit)


@router.get("/{job_id}", response_model=JobResponse)
async def job_detail(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/normalize", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_normalize(db: AsyncSession = Depends(get_db), idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=255)] = None, _=Depends(require_role("analyst"))):
    return await _enqueue(db, job_type="normalize", payload={}, idempotency_key=idempotency_key)


@router.post("/benchmark", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_benchmark(db: AsyncSession = Depends(get_db), idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=255)] = None, _=Depends(require_role("analyst"))):
    return await _enqueue(db, job_type="benchmark", payload={}, idempotency_key=idempotency_key)


@router.post("/scrape", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_scrape(data: ScrapeRequest, db: AsyncSession = Depends(get_db), idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=255)] = None, _=Depends(require_role("analyst"))):
    payload = data.model_dump(mode="json")
    payload["_ingestion_request_key"] = idempotency_key or f"scrape-job-{uuid.uuid4()}"
    return await _enqueue(db, job_type="scrape", payload=payload, idempotency_key=idempotency_key)


@router.post("/ingest", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_ingest(data: BulkListingsInput, db: AsyncSession = Depends(get_db), idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=255)] = None, _=Depends(require_role("analyst"))):
    payload = data.model_dump(mode="json")
    payload["_ingestion_request_key"] = idempotency_key or f"ingest-job-{uuid.uuid4()}"
    return await _enqueue(db, job_type="ingest", payload=payload, idempotency_key=idempotency_key)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel(job_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_role("analyst"))):
    job = await cancel_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
