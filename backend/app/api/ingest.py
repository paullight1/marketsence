from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db, init_db
from app.schemas import (
    BenchmarkResult,
    BulkListingsInput,
    IngestResult,
    NormalizationResult,
)
from app.services.ingest import ingest_listings as ingest_listings_service

router = APIRouter()


@router.post("/listings", response_model=IngestResult)
async def ingest_listings(
    data: BulkListingsInput,
    db: AsyncSession = Depends(get_db),
):
    added_count = await ingest_listings_service(db, data)
    return {"added": added_count, "message": "Listings ingested successfully"}


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
