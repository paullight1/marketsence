import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.schemas import (
    BenchmarkResult,
    BulkListingsInput,
    CleanCsvResult,
    IngestResult,
    NormalizationResult,
    ScrapeIngestResult,
    ScrapeRequest,
)
from app.services.analytics import calculate_market_benchmarks
from app.services.csv_cleaner import clean_uploaded_csv, get_cleaned_csv_path
from app.services.ingest import ingest_listings as ingest_listings_service
from app.services.normalizer import normalize_all_listings
from app.services.scraper import (
    ScrapeSafetyError,
    scrape_price_listings,
    validate_scrape_target_syntax,
)

router = APIRouter()


@router.post("/listings", response_model=IngestResult)
async def ingest_listings(
    data: BulkListingsInput,
    db: AsyncSession = Depends(get_db),
):
    added_count = await ingest_listings_service(db, data)
    return {"added": added_count, "message": "Listings ingested successfully"}


@router.post("/scrape", response_model=ScrapeIngestResult)
async def scrape_website_listings(
    data: ScrapeRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        validate_scrape_target_syntax(data.url)
        listings = await scrape_price_listings(data)
    except ScrapeSafetyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not scrape website: {exc}",
        ) from exc

    ingested_count = 0

    if data.ingest and listings:
        ingested_count = await ingest_listings_service(
            db,
            BulkListingsInput(listings=listings),
        )

    return {
        "scraped": len(listings),
        "ingested": ingested_count,
        "listings": listings,
        "message": (
            "Website scraped and listings ingested"
            if ingested_count
            else "Website scraped; no listings were ingested"
        ),
    }


@router.post("/clean-csv", response_model=CleanCsvResult)
async def clean_csv_upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    content = await file.read(settings.max_csv_upload_bytes + 1)
    await file.close()
    if len(content) > settings.max_csv_upload_bytes:
        max_mb = settings.max_csv_upload_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"CSV file is too large. Maximum size is {max_mb:g} MB",
        )

    try:
        result = clean_uploaded_csv(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result


@router.get("/clean-csv/{file_id}/download")
async def download_cleaned_csv(file_id: str):
    path = get_cleaned_csv_path(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="Cleaned CSV not found")

    return FileResponse(
        path,
        media_type="text/csv",
        filename=path.name,
    )


@router.post("/normalize", response_model=NormalizationResult)
async def run_normalization(db: AsyncSession = Depends(get_db)):
    linked, suggested = await normalize_all_listings(db)
    return {
        "message": "Normalization pipeline completed",
        "linked_count": linked,
        "new_suggestions": suggested,
        "status": "success",
    }


@router.post("/benchmark", response_model=BenchmarkResult)
async def recalculate_benchmarks(db: AsyncSession = Depends(get_db)):
    count = await calculate_market_benchmarks(db)
    return {
        "message": "Benchmark recalculation completed",
        "updated_products": count,
        "status": "success",
    }
