from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import CategoryBreakdownItem, DashboardSummary, SuspiciousSummary
from app.services.analytics import (
    get_category_breakdown,
    get_dashboard_summary,
    get_suspicious_summary,
)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary_route(db: AsyncSession = Depends(get_db)):
    return await get_dashboard_summary(db)


@router.get("/categories", response_model=list[CategoryBreakdownItem])
async def get_category_breakdown_route(db: AsyncSession = Depends(get_db)):
    return await get_category_breakdown(db)


@router.get("/suspicious", response_model=SuspiciousSummary)
async def get_suspicious_summary_route(db: AsyncSession = Depends(get_db)):
    return await get_suspicious_summary(db)
