# MarketSense NG Backend

The MarketSense backend is a FastAPI service for Nigerian market-price intelligence. It keeps HTTP routes thin and separates API contracts, persistence models, scraping/cleaning, matching, benchmark logic, and catalog queries.

## Run locally

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open the API docs at `http://localhost:8000/docs`.

### Optional browser scraping

Core installs use the guarded HTTP scraper. Browser automation is intentionally optional:

```powershell
pip install -r requirements-browser.txt
crawl4ai-setup
```

Do not enable it for arbitrary URLs. Configure trusted domains explicitly with `BROWSER_SCRAPER_ENABLED=true` and `BROWSER_SCRAPE_ALLOWED_DOMAINS=["trusted.example"]`.

## Key files

- [`app/main.py`](app/main.py) - FastAPI application setup and router registration.
- [`app/core/config.py`](app/core/config.py) - runtime configuration and ingestion safety limits.
- [`app/db/database.py`](app/db/database.py) - async engine/session dependency and current local table initialization.
- [`app/models/models.py`](app/models/models.py) - SQLAlchemy persistence models.
- [`app/schemas.py`](app/schemas.py) - request/response contracts.
- [`app/services/scraper.py`](app/services/scraper.py) - guarded scraping and optional trusted-domain browser fallback.
- [`app/services/csv_cleaner.py`](app/services/csv_cleaner.py) - bounded CSV cleaning and export retention.
- [`app/services/normalizer.py`](app/services/normalizer.py) - canonical-product matching and unresolved counts.
- [`app/services/analytics.py`](app/services/analytics.py) - benchmarks, outlier review records, and analytics summaries.
- [`app/services/catalog.py`](app/services/catalog.py) - set-based product/supplier aggregate queries.
- [`app/services/ingest.py`](app/services/ingest.py) - batched supplier resolution and listing ingestion.

## HTTP-layer rule

Routes should generally:

1. accept validated input,
2. call a service,
3. translate known domain/safety failures into a deliberate HTTP response,
4. return a typed response model.

Business/data logic belongs under `app/services` so it can be tested independently of presentation code.

## Ingestion safety boundary

The current service includes application-level protections for the highest-risk input paths:

- scrape targets reject localhost/private/reserved literal addresses and resolve only to public network addresses,
- HTTP redirect hops are revalidated,
- scrape response type, size, redirect count, and timeout are bounded,
- browser scraping is disabled by default and restricted to explicitly trusted domains when enabled,
- CSV uploads have a byte limit before Pandas parsing,
- cleaned exports neutralize spreadsheet-formula prefixes,
- local cleaned exports expire and are count-bounded,
- list API page sizes are bounded.

These controls are defense in depth, not a replacement for authentication, authorization, distributed rate limits, and infrastructure egress controls.

## Data/analytics behavior

- Raw listings are persisted before explicit normalization.
- Normalization reports unresolved listings rather than silently treating them as complete.
- Market text lookups prefer exact product names and return a controlled ambiguity response for multiple partial matches.
- Benchmark recalculation uses a robust median/MAD outlier rule when enough observations exist.
- Extreme outliers create persistent `SuspiciousListing` review records and are excluded from benchmark price calculation.
- Product/supplier list statistics are aggregated in set-based SQL instead of per-row N+1 queries.
- Supplier resolution during bulk ingestion is batched rather than queried once per listing.

## Testing

```powershell
python -m compileall app
python -m pytest tests -q
```

The root GitHub Actions workflow also runs frontend lint and production build gates.

## Production gaps

Do not treat the current backend as a complete public production boundary yet. Before public release, add:

- authentication/authorization and distributed abuse controls,
- durable queue/workers with retries and idempotency,
- Postgres and Alembic-owned migrations instead of startup `create_all`,
- fixed-point monetary columns instead of floating-point price storage,
- database uniqueness/upsert constraints for concurrent ingestion,
- object storage/lifecycle controls for cleaned exports,
- infrastructure-level scrape egress policy,
- dependency vulnerability/update automation and production observability.
