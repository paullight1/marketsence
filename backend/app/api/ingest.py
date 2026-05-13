import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db, init_db
from app.schemas import (
    BenchmarkResult,
    BulkListingsInput,
    CleanCsvResult,
    IngestResult,
    NormalizationResult,
    ScrapeIngestResult,
    ScrapeRequest,
)
from app.services.ingest import ingest_listings as ingest_listings_service
from app.services.scraper import scrape_price_listings
from app.services.csv_cleaner import clean_uploaded_csv, get_cleaned_csv_path

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
        listings = await scrape_price_listings(data)
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

    try:
        result = clean_uploaded_csv(await file.read(), file.filename)
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


from app.services.normalizer import normalize_all_listings

@router.post("/normalize", response_model=NormalizationResult)
async def run_normalization(db: AsyncSession = Depends(get_db)):
    linked, suggested = await normalize_all_listings(db)
    return {
        "message": "Normalization pipeline completed",
        "linked_count": linked,
        "new_suggestions": suggested,
        "status": "success"
    }


from app.services.analytics import calculate_market_benchmarks

@router.post("/benchmark", response_model=BenchmarkResult)
async def recalculate_benchmarks(db: AsyncSession = Depends(get_db)):
    count = await calculate_market_benchmarks(db)
    return {
        "message": "Benchmark recalculation completed",
        "updated_products": count,
        "status": "success"
    }


@router.post("/init")
async def initialize_database(db: AsyncSession = Depends(get_db)):
    await init_db()
    return {"message": "Database initialized successfully"}
