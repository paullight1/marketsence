from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import analytics, auth, ingest, jobs, market, ops, products, suppliers
from app.core.config import settings
from app.core.observability import ObservabilityMiddleware
from app.core.rate_limit import RateLimitMiddleware, build_rate_limiter
from app.core.runtime import validate_runtime_configuration
from app.core.security import require_role
from app.db.database import async_session_maker, init_db
from app.schemas import HealthResponse, RootResponse
from app.services.export_storage import build_export_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_configuration()
    await init_db()
    rate_limiter = build_rate_limiter()
    export_storage = build_export_storage()
    await rate_limiter.ready()
    try:
        await export_storage.ready()
        app.state.rate_limiter = rate_limiter
        app.state.export_storage = export_storage
        yield
    finally:
        await export_storage.close()
        await rate_limiter.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, description="Nigerian Market Price Intelligence System", version=settings.app_version, lifespan=lifespan)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(ObservabilityMiddleware)

    viewer = [Depends(require_role("viewer"))]
    analyst = [Depends(require_role("analyst"))]
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(products.router, prefix="/api/products", tags=["products"], dependencies=viewer)
    app.include_router(suppliers.router, prefix="/api/suppliers", tags=["suppliers"], dependencies=viewer)
    app.include_router(market.router, prefix="/api/market", tags=["market"], dependencies=viewer)
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"], dependencies=viewer)
    app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"], dependencies=analyst)
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"], dependencies=viewer)
    app.include_router(ops.router, prefix="/api/ops", tags=["ops"], dependencies=viewer)

    @app.get("/", response_model=RootResponse)
    async def root():
        return {"message": settings.app_name, "status": "running"}

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return {"status": "healthy"}

    @app.get("/ready")
    async def ready():
        checks = {
            "database": "not_ready",
            "rate_limiter": "not_ready",
            "export_storage": "not_ready",
        }
        try:
            async with async_session_maker() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ready"
        except Exception:
            pass
        try:
            await app.state.rate_limiter.ready()
            checks["rate_limiter"] = "ready"
        except Exception:
            pass
        try:
            await app.state.export_storage.ready()
            checks["export_storage"] = "ready"
        except Exception:
            pass
        all_ready = all(value == "ready" for value in checks.values())
        return JSONResponse(
            status_code=200 if all_ready else 503,
            content={"status": "ready" if all_ready else "not_ready", "checks": checks},
        )

    return app


app = create_app()
