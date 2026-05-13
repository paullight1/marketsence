from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, ingest, market, products, suppliers
from app.core.config import settings
from app.db.database import init_db
from app.schemas import HealthResponse, RootResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Nigerian Market Price Intelligence System",
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(products.router, prefix="/api/products", tags=["products"])
    app.include_router(suppliers.router, prefix="/api/suppliers", tags=["suppliers"])
    app.include_router(market.router, prefix="/api/market", tags=["market"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])

    @app.get("/", response_model=RootResponse)
    async def root():
        return {"message": settings.app_name, "status": "running"}

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return {"status": "healthy"}

    return app


app = create_app()
