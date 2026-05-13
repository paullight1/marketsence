# MarketSense NG Backend

This backend is a small FastAPI service for a Nigerian price intelligence project. It is intentionally scoped to teach core backend ideas that show up in interviews:

- `FastAPI`: application setup, dependency injection, request validation, response models.
- `Routes`: product, supplier, market, analytics, and ingest endpoints.
- `Requests`: POSTing listing payloads into the system and reading JSON responses back.
- `Databases`: async SQLAlchemy sessions, models, persistence, and query services.

## Run locally

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open the docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Key files

- [app/main.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/main.py): FastAPI app factory and router registration.
- [app/db/database.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/db/database.py): async engine and session dependency.
- [app/models/models.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/models/models.py): SQLAlchemy models.
- [app/schemas.py](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/schemas.py): request and response contracts.
- [app/services](C:/Users/USER/Desktop/app-projects/zlearning/PRICE%20INTELLIGENCE%20SYSTEM/backend/app/services): backend business logic.

## Teaching notes

### FastAPI

FastAPI gives you three important pieces quickly:

1. Route declaration with decorators like `@router.get(...)`.
2. Request parsing and validation with Pydantic.
3. Dependency injection with `Depends(get_db)`.

That means your handler can stay thin and focus on orchestration, while schemas and services do the heavy lifting.

### Routes

Routes should do four things only:

1. Read validated input.
2. Call a service function.
3. Convert `None` or invalid state into an HTTP error where needed.
4. Return a typed response.

Example from this project:

```python
@router.get("/{product_id}", response_model=ProductDetail)
async def get_product_route(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```

### Requests

Use an HTTP client to exercise the backend. Example with Python `requests`:

```python
import requests

payload = {
    "listings": [
        {
            "source": "Jumia",
            "original_name": "Dangote Sugar 50kg bag",
            "price": 85000,
            "seller_name": "Jumia Nigeria",
            "seller_source": "online",
            "location": "Lagos",
            "url": "https://example.com/dangote-sugar"
        }
    ]
}

response = requests.post("http://localhost:8000/api/ingest/listings", json=payload)
print(response.json())
```

The interview point here is simple: know the difference between request body validation, path/query parameters, and response shaping.

### Databases

This project uses:

- SQLAlchemy models to define tables.
- An async engine to connect.
- A session dependency to give each request a unit of work.

The important design split is:

- `models.py`: database structure
- `schemas.py`: API contract
- `services/*.py`: query and business logic
- `api/*.py`: HTTP layer

That separation is what you should be able to explain in an interview.
