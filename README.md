# MarketSense NG

MarketSense NG is a teaching-first full-stack price intelligence system focused on Nigerian market data. The project is designed to help you learn backend engineering in a realistic setting: ingest messy listings, normalize them into cleaner product records, calculate market benchmarks, and expose the results through HTTP APIs and a dashboard.

## Current focus

The backend is the strongest learning surface right now:

- FastAPI application setup
- route design
- request validation
- async database access with SQLAlchemy
- service-layer organization
- analytics and normalization workflows

## Backend quick start

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Suggested learning order

1. Read [backend/app/main.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/main.py).
2. Read [backend/app/api/ingest.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/api/ingest.py) and [backend/app/schemas.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/schemas.py).
3. Read [backend/app/db/database.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/db/database.py) and [backend/app/models/models.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/models/models.py).
4. Read [backend/app/services/catalog.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/services/catalog.py), [backend/app/services/normalizer.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/services/normalizer.py), and [backend/app/services/analytics.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/services/analytics.py).

## Interview framing

Describe this project as:

> A FastAPI-based backend that ingests marketplace listings, validates request payloads, stores data in a relational database, normalizes messy product names, and computes supplier-weighted market benchmarks.
