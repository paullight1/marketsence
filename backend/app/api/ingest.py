from typing import Annotated
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.schemas import BenchmarkResult, BulkListingsInput, CleanCsvResult, IngestResult, NormalizationResult, ScrapeIngestResult, ScrapeRequest
from app.services.analytics import calculate_market_benchmarks
from app.services.csv_cleaner import build_cleaned_csv
from app.services.export_storage import ExportStorage, get_export_storage
from app.services.ingest import ingest_listings as ingest_listings_service
from app.services.normalizer import normalize_all_listings
from app.services.scraper import ScrapeSafetyError, scrape_price_listings, validate_scrape_target_syntax

router = APIRouter()


def _require_sync_pipeline(operation: str, job_path: str) -> None:
    if settings.environment == "production" and settings.background_jobs_enabled:
        raise HTTPException(status_code=409, detail=f"Synchronous {operation} is disabled in production; use {job_path}")


@router.post("/listings", response_model=IngestResult)
async def ingest_listings(data: BulkListingsInput, db: AsyncSession = Depends(get_db), idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=255)] = None):
    if len(data.listings) > settings.sync_ingest_max_listings:
        raise HTTPException(status_code=413, detail=f"Synchronous imports are limited to {settings.sync_ingest_max_listings} listings; use /api/jobs/ingest for durable imports")
    added_count = await ingest_listings_service(db, data, request_key=idempotency_key)
    return {"added": added_count, "message": "Listings ingested successfully"}


@router.post("/scrape", response_model=ScrapeIngestResult)
async def scrape_website_listings(data: ScrapeRequest, db: AsyncSession = Depends(get_db)):
    _require_sync_pipeline("scraping", "/api/jobs/scrape")
    try:
        validate_scrape_target_syntax(data.url)
        listings = await scrape_price_listings(data)
    except ScrapeSafetyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"Could not scrape website: {exc}") from exc
    ingested_count = 0
    if data.ingest and listings:
        ingested_count = await ingest_listings_service(db, BulkListingsInput(listings=listings))
    return {"scraped": len(listings), "ingested": ingested_count, "listings": listings, "message": "Website scraped and listings ingested" if ingested_count else "Website scraped; no listings were ingested"}


@router.post("/clean-csv", response_model=CleanCsvResult)
async def clean_csv_upload(
    file: UploadFile = File(...),
    storage: ExportStorage = Depends(get_export_storage),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    content = await file.read(settings.max_csv_upload_bytes + 1)
    await file.close()
    if len(content) > settings.max_csv_upload_bytes:
        max_mb = settings.max_csv_upload_bytes / (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"CSV file is too large. Maximum size is {max_mb:g} MB")
    try:
        artifact = build_cleaned_csv(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await storage.put(
        artifact.metadata["file_id"],
        artifact.content,
        artifact.metadata["download_filename"],
    )
    return artifact.metadata


@router.get("/clean-csv/{file_id}/download")
async def download_cleaned_csv(
    file_id: str,
    storage: ExportStorage = Depends(get_export_storage),
):
    stored = await storage.get(file_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Cleaned CSV not found")
    safe_filename = stored.filename.replace('"', "").replace("\r", "").replace("\n", "")
    return Response(
        content=stored.content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_filename)}",
            "Cache-Control": "private, no-store",
        },
    )


@router.post("/normalize", response_model=NormalizationResult)
async def run_normalization(db: AsyncSession = Depends(get_db)):
    _require_sync_pipeline("normalization", "/api/jobs/normalize")
    linked, suggested = await normalize_all_listings(db)
    return {"message": "Normalization pipeline completed", "linked_count": linked, "new_suggestions": suggested, "status": "success"}


@router.post("/benchmark", response_model=BenchmarkResult)
async def recalculate_benchmarks(db: AsyncSession = Depends(get_db)):
    _require_sync_pipeline("benchmarking", "/api/jobs/benchmark")
    count = await calculate_market_benchmarks(db)
    return {"message": "Benchmark recalculation completed", "updated_products": count, "status": "success"}
