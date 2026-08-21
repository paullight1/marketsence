# MarketSense - Price Intelligence System

![MarketSense logo](frontend/public/marketsense-mark.svg)

MarketSense is an open-source Nigerian market price-intelligence workspace for messy marketplace data. It can ingest raw listings, clean bounded CSV uploads, normalize product names, calculate trust-weighted benchmarks, persist extreme-price review flags, and expose the resulting state through a responsive analyst UI.

The codebase is intentionally learning-friendly, but the product paths use real backend data rather than frontend mock records.

## Features

- Public-network website scraping with URL, DNS, redirect, timeout, content-type, and response-size safety checks
- Optional browser scraping for explicitly trusted domains
- CSV cleaning with upload limits, normalized/unique headers, duplicate removal, spreadsheet-formula neutralization, and bounded local export retention
- Product normalization with RapidFuzz and explicit unresolved-match counts
- Trust-weighted benchmark recalculation with robust outlier detection and persistent analyst-review flags
- Supplier trust/source-quality views and canonical product market summaries
- Explicit loading, failure, empty-data, and review states across the analyst frontend
- Responsive dashboard, scrape, clean, analytics, suppliers, products, and pipeline-state views
- Data-processing lessons for Pandas, transformations, fuzzy matching, embeddings, and system design

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn-style components, Lucide icons |
| Backend | FastAPI, SQLAlchemy async sessions, Pydantic |
| Data | SQLite by default, async database support, Pandas learning scripts |
| Scraping | HTTPX + BeautifulSoup by default; Crawl4AI is optional for trusted-domain browser scraping |
| Matching | RapidFuzz |
| Testing | Pytest, Python compile check, ESLint, Next.js production build, GitHub Actions |

## App Screens

- `/dashboard` - live persisted operations state, review pressure, recent listings, products, and suppliers
- `/scrape` - scrape a public HTTP(S) target and optionally persist extracted raw listings
- `/clean` - clean a bounded CSV upload and download the sanitized export
- `/products` - searchable/sortable canonical product catalog with observed price statistics
- `/suppliers` - supplier trust, observed pricing, and flagged-listing counts
- `/analytics` - category mix, market coverage, source trust, and detected review signals
- `/tasks` - persisted pipeline/review status; this is not yet a background-worker queue

## Project Structure

```text
marketsence/
├── .github/workflows/quality.yml
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # runtime configuration and safety limits
│   │   ├── db/               # database/session setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # scraping, cleaning, analytics, matching, catalog logic
│   │   └── main.py           # FastAPI application entrypoint
│   ├── scripts/              # learning lessons and dataset generation
│   ├── tests/                # API and hardening regression tests
│   ├── requirements.txt      # core backend dependencies
│   └── requirements-browser.txt # optional trusted-domain browser scraper
├── frontend/
│   ├── public/
│   └── src/
│       ├── app/
│       ├── components/
│       └── lib/
├── data/
├── LICENSE
└── README.md
```

## Quick Start

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Backend API docs: `http://localhost:8000/docs`

### Optional browser scraper

The default scraper deliberately avoids browser automation. Only install and enable Crawl4AI when the target domains are trusted and explicitly allowlisted:

```powershell
cd backend
pip install -r requirements-browser.txt
crawl4ai-setup
```

Then configure both:

```env
BROWSER_SCRAPER_ENABLED=true
BROWSER_SCRAPE_ALLOWED_DOMAINS=["trusted.example"]
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev -- --port 3000
```

Open `http://localhost:3000/dashboard`.

## Environment and Safety Defaults

See `backend/.env.example`. Important defaults include:

```env
DATABASE_URL=sqlite+aiosqlite:///./marketsense.db
ALLOWED_ORIGINS=["http://localhost:3000"]
SQL_ECHO=false
MAX_CSV_UPLOAD_BYTES=5242880
CLEANED_CSV_RETENTION_HOURS=24
MAX_CLEANED_CSV_EXPORTS=50
MAX_SCRAPE_RESPONSE_BYTES=2097152
SCRAPE_TIMEOUT_SECONDS=15
MAX_SCRAPE_REDIRECTS=5
SCRAPE_ALLOWED_DOMAINS=[]
BROWSER_SCRAPER_ENABLED=false
BROWSER_SCRAPE_ALLOWED_DOMAINS=[]
```

For a production deployment, prefer a non-empty `SCRAPE_ALLOWED_DOMAINS` list in addition to network-level egress restrictions.

Frontend API target:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Main API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/ingest/listings` | Ingest validated raw listing records |
| `POST` | `/api/ingest/scrape` | Scrape a safe public target and optionally ingest results |
| `POST` | `/api/ingest/clean-csv` | Upload and clean a bounded CSV file |
| `GET` | `/api/ingest/clean-csv/{file_id}/download` | Download a retained cleaned export |
| `POST` | `/api/ingest/normalize` | Link unresolved listings to canonical products |
| `POST` | `/api/ingest/benchmark` | Recalculate benchmarks and persist extreme-price flags |
| `GET` | `/api/products/` | List canonical products with aggregate observed-price statistics |
| `GET` | `/api/suppliers/` | List suppliers with aggregate observed-price/flag statistics |
| `GET` | `/api/market/compare` | Compare source prices for one unambiguous product |
| `GET` | `/api/analytics/summary` | Dashboard counts and average source trust |
| `GET` | `/api/analytics/categories` | Category breakdown |
| `GET` | `/api/ops/overview` | Persisted pipeline, review, and recent-listing state |

## Testing

The PR quality workflow runs both backend and frontend gates.

Backend:

```powershell
cd backend
python -m compileall app
python -m pytest tests -q
```

Frontend:

```powershell
cd frontend
npm ci
npm run lint
npm run build
```

## Current Architecture

```text
public website -> guarded HTTP scrape -> raw listing ingestion
CSV upload     -> bounded cleaning     -> retained sanitized export
raw listings   -> explicit normalization -> linked products
linked prices  -> benchmark/outlier detection -> benchmark history + review flags
persisted data -> analytics/ops API -> analyst frontend
```

Long-running scrape, normalization, and benchmark work still executes inline with API requests. The `/tasks` screen reports persisted state; it is not a durable job scheduler.

## Production Readiness Boundary

The hardening work in this branch materially improves safety, correctness, observability, UI trust, and query efficiency, but **MarketSense should not yet be exposed as an unauthenticated public production service**.

The remaining release blockers are:

1. **Authentication, authorization, CSRF/session strategy, and distributed rate limiting.** Mutating ingestion/scrape/normalization/benchmark endpoints currently have no user identity boundary.
2. **Durable background execution.** Move scrape, normalization, benchmark, and large import work to a queue/worker system with idempotency, retries, timeouts, cancellation, and job audit state.
3. **Postgres plus real migrations.** Startup still relies on metadata table creation; production schema evolution should be owned by Alembic migrations, not `create_all`.
4. **Financial precision.** Price fields currently use floating-point storage; migrate monetary values to fixed-point `NUMERIC/Decimal` before relying on them for financial decisions.
5. **Race-safe uniqueness.** Add database uniqueness/upsert rules for supplier/product identities and ingestion idempotency to prevent concurrent duplicate creation.
6. **Object storage.** Local cleaned-export retention is bounded, but multi-instance production should use authenticated object storage with lifecycle policies and access controls.
7. **Network egress controls.** Application SSRF defenses reduce risk, but production scraping also needs infrastructure-level egress policy/DNS controls and preferably an explicit domain allowlist.
8. **Dependency/security lifecycle.** Add recurring dependency vulnerability checks and a controlled upgrade policy before release.

Until those gates exist, this repository is best described as a hardened learning/pilot system rather than a fully public production service.

## Scraping Note

Only process sources you are authorized to access. Respect site terms, robots guidance where applicable, rate limits, privacy obligations, and data-usage rules. Application-level URL checks are not a substitute for production egress policy.

## License

This project is released under the [MIT License](LICENSE).
