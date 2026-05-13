# MarketSense - Price Intelligence System

![MarketSense logo](frontend/public/marketsense-mark.svg)

MarketSense is an open-source price intelligence workspace for messy marketplace data. It helps teams scrape raw product listings, clean CSV datasets, normalize product names, flag suspicious prices, and review market benchmarks through a responsive analyst dashboard.

The project is built as a learning-friendly full-stack system: the backend exposes real ingestion and analytics APIs, while the frontend reads from those APIs instead of relying on mock data.

## Features

- Live website scraping into raw product listings
- CSV upload and automated cleaning workflow
- Product normalization with fuzzy matching concepts
- Suspicious price detection and review queues
- Supplier trust and source quality views
- Product catalog search, sorting, and benchmark summaries
- Responsive frontend with dashboard, scrape, clean, analytics, suppliers, products, and task views
- Data-processing lessons for Pandas, cleaning, transformations, fuzzy matching, embeddings, and system design

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, shadcn-style components, Lucide icons |
| Backend | FastAPI, SQLAlchemy async sessions, Pydantic |
| Data | SQLite by default, async database support, Pandas learning scripts |
| Scraping | Crawl4AI with BeautifulSoup fallback |
| Matching | RapidFuzz |
| Testing | Pytest, ESLint, Next.js production build |

## App Screens

- `/dashboard` - live operations overview, queue health, review pressure, recent listings
- `/scrape` - scrape a target website and optionally ingest results
- `/clean` - upload a messy CSV and download the cleaned result
- `/products` - searchable and sortable product benchmark catalog
- `/suppliers` - source trust, supplier quality, and flagged listing counts
- `/analytics` - category mix, market health, and benchmark coverage
- `/tasks` - queue-style workflow board for scraping, review, and publishing

## Project Structure

```text
PRICE INTELLIGENCE SYSTEM/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── db/               # database setup and models
│   │   ├── services/         # scraping, cleaning, analytics, matching logic
│   │   └── main.py           # FastAPI application entrypoint
│   ├── scripts/              # learning lessons and dataset generation
│   ├── tests/                # backend API tests
│   └── requirements.txt
├── frontend/
│   ├── public/               # logo and static assets
│   └── src/
│       ├── app/              # Next.js routes
│       ├── components/       # layout and UI components
│       └── lib/              # API client and utilities
├── data/                     # local learning datasets, ignored for generated large files
├── LICENSE
└── README.md
```

## Quick Start

### 1. Clone the repository

```powershell
git clone https://github.com/paullight1/marketsence.git
cd marketsence
```

### 2. Start the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
crawl4ai-setup
uvicorn app.main:app --reload --port 8000
```

Backend API docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --port 3000
```

Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard).

## Environment

Backend defaults are provided in `backend/.env.example`:

```env
DATABASE_URL=sqlite+aiosqlite:///./marketsense.db
ALLOWED_ORIGINS=["http://localhost:3000"]
SQL_ECHO=false
```

Frontend can point to another backend with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Main API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/ingest/listings` | Ingest raw listing records |
| `POST` | `/api/ingest/scrape` | Scrape a website and optionally ingest results |
| `POST` | `/api/ingest/clean-csv` | Upload and clean a CSV file |
| `GET` | `/api/ingest/clean-csv/{file_id}/download` | Download the cleaned CSV |
| `GET` | `/api/products/` | List normalized products |
| `GET` | `/api/suppliers/` | List supplier summaries |
| `GET` | `/api/analytics/summary` | Dashboard counts and trust score |
| `GET` | `/api/analytics/categories` | Category breakdown |
| `GET` | `/api/ops/overview` | Queue, review, and recent-listing overview |

## Learning Dataset Scripts

Generate a large practice dataset:

```powershell
cd backend
python scripts/generate_learning_dataset.py --rows 1000000 --out ..\data\raw_learning_listings_1m.csv
```

Run the lessons in order:

```powershell
python scripts\lesson_01_inspect_data.py
python scripts\lesson_02_clean_data.py
python scripts\lesson_03_transform_data.py
python scripts\lesson_04_human_review_queue.py
python scripts\lesson_05_fuzzy_matching.py
python scripts\lesson_06_embeddings_intro.py
```

Generated large CSVs are ignored by Git so the repository stays lightweight.

## Testing

Backend:

```powershell
python -m pytest backend\tests
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Architecture

Current flow:

```text
website or CSV -> ingestion -> raw listings -> cleaning -> matching -> review -> analytics -> frontend
```

Production direction:

```text
frontend -> API -> queue -> workers -> database -> cache -> analytics publishing
```

For a larger production deployment, the next improvements should be background workers, scheduled scrapes, durable job retries, Redis caching, richer human-review approvals, and Postgres-backed analytics.

## Scraping Note

Use the scraper responsibly. Respect each website's terms, robots guidance, rate limits, and data usage rules. The scraping feature is designed for learning, controlled research, and sources you are allowed to process.

## License

This project is released under the [MIT License](LICENSE).
