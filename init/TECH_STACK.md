# MarketSense NG - Technology Stack Guide

A comprehensive guide to the technology choices behind Nigeria's market price intelligence system.

---

## 1. Backend Stack

### Python 3.11+

**Why We Chose It**
- Excellent ecosystem for data processing and ML
- Async support ideal for I/O-heavy web scraping operations
- Rich libraries for Nigerian language processing
- Strong typing with recent versions improves maintainability

**When to Use It**
- All backend API services
- Data processing pipelines
- Machine learning model serving
- Web scraping scripts

**Setup Notes**
```bash
# Install Python 3.11+ via pyenv or official installer
pyenv install 3.11.8

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Nigerian Context**
- Python's string handling works well with Yoruba, Igbo, Hausa character sets
- Unicode support handles ₦ (Naira symbol) and regional characters

---

### FastAPI

**Why We Chose It**
- Native async support matches Python 3.11+ capabilities
- Automatic OpenAPI documentation speeds up frontend integration
- Pydantic integration provides built-in validation
- High performance comparable to Node.js/Go
- Type hints flow through to API docs

**When to Use It**
- REST API endpoints for the frontend
- Webhook receivers for price feeds
- Internal microservices
- Real-time price streaming endpoints

**Basic Setup**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MarketSense API")

class PriceUpdate(BaseModel):
    market: str
    commodity: str
    price_ngn: float
    unit: str

@app.post("/prices/")
async def update_price(price: PriceUpdate):
    # Process and store price
    return {"status": "recorded"}
```

**Nigerian Context**
- Easy to handle multiple state-specific price schemas
- Validation rules can enforce Naira amounts (positive, reasonable ranges)

---

### SQLAlchemy + asyncpg

**Why We Chose It**
- SQLAlchemy provides ORM flexibility for complex queries
- asyncpg offers excellent async PostgreSQL performance
- Type safety with SQLModel (built on Pydantic)
- Migration support via Alembic

**When to Use It**
- Database models and schemas
- Query building for reports
- Migrations and schema management

**Basic Setup**
```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/marketsense"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession)

# Example model
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class MarketPrice(Base):
    __tablename__ = "market_prices"
    
    id = Column(String, primary_key=True)
    commodity = Column(String, index=True)
    market = Column(String, index=True)
    price_ngn = Column(Float)
    recorded_at = Column(DateTime)
```

**Nigerian Context**
- Perfect for multi-market, multi-commodity queries
- Efficient handling of Lagos, Abuja, Kano, Port Harcourt data

---

### Pydantic

**Why We Chose It**
- Native integration with FastAPI
- Data validation at API boundary
- Automatic serialization/deserialization
- Environment variable support for config

**When to Use It**
- API request/response models
- Configuration validation
- Data transformation between layers

**Basic Example**
```python
from pydantic import BaseModel, Field, validator
from datetime import datetime

class CommodityPrice(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0, description="Price in Naira")
    market: str
    state: str
    
    @validator('state')
    def validate_nigerian_state(cls, v):
        valid_states = ['Lagos', 'Kano', 'Abuja', 'Rivers', 'Oyo', 'Kaduna']
        if v not in valid_states:
            raise ValueError(f'Valid Nigerian states: {valid_states}')
        return v
```

---

### Pandas

**Why We Chose It**
- Industry standard for data manipulation
- Excellent for price trend analysis
- CSV/Excel import/export for market data
- GroupBy operations perfect for aggregation

**When to Use It**
- Historical price analysis
- Generating market reports
- Data cleaning pipelines
- Statistical calculations

**Basic Usage**
```python
import pandas as pd

# Load price data
df = pd.read_csv('lagos_prices.csv')

# Calculate trends
weekly_avg = df.groupby(['commodity', 'week'])['price_ngn'].mean()

# Find price changes
df['price_change_pct'] = df.groupby('commodity')['price_ngn'].pct_change() * 100
```

---

## 2. Data Processing

### RapidFuzz

**Why We Chose It**
- 10-50x faster than FuzzyWuzzy for Nigerian market names
- Handles common typos in market/commodity names
- Supports Levenshtein, JARO, token sort ratios
- Critical for matching "Tomato" vs "Tomatoe" vs "Tomatoes"

**When to Use It**
- Matching commodity names across different sources
- Normalizing market names (e.g., "Oke-Oja" vs "Oke Oja")
- Deduplicating scraped data

**Basic Usage**
```python
from rapidfuzz import fuzz, process

commodities = ["Tomato", "Onion", "Pepper", "Rice"]

# Match scraped value to canonical list
matched = process.extractOne(
    "Fresh tomatoes",
    choices=commodities,
    scorer=fuzz.token_set_ratio
)
# Returns: ('Tomato', 85, 0) - match, score, index
```

**Nigerian Context**
- Handles variations: "Samba" vs "Semovita", "Tuwo" vs "Tuwo rice"
- Language-agnostic matching works with transliterated names

---

### Sentence Transformers (all-MiniLM-L6-v2)

**Why We Chose It**
- Lightweight (80MB) model that runs on modest hardware
- Good semantic matching for commodity similarity
- Enables "find similar commodities" features
- pgvector integration for vector storage

**When to Use It**
- Semantic search for commodities
- Recommending related goods
- Finding price patterns across similar items

**Basic Usage**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings
descriptions = ["Fresh tomatoes per basket", "red tomatoes wholesale"]
embeddings = model.encode(descriptions)

# Find similar
query = model.encode("tomatoes for cooking")
similarities = cosine_similarity([query], embeddings)[0]
```

**Nigerian Context**
- Understands that "Egusi" relates to "Melon seeds"
- Handles Pidgin English descriptions

---

### Playwright

**Why We Chose It**
- Headless browser automation for dynamic sites
- Handles JavaScript-rendered price tables
- Built-in wait mechanisms prevent flaky scrapes
- Cross-browser support (Chromium, Firefox, WebKit)

**When To Use It**
- Scraping government price portals
- E-commerce sites with dynamic content
- PDF download automation

**Basic Setup**
```python
from playwright.async_api import async_playwright

async def scrape_prices():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("https://nigerian-market-prices.gov.ng")
        await page.wait_for_selector(".price-table")
        
        prices = await page.eval_on_selector_all(
            ".price-table tr",
            "rows => rows.map(r => r.innerText)"
        )
        
        await browser.close()
        return prices
```

**Nigerian Context**
- Works with .gov.ng sites that often use dynamic loading
- Handles pages in English with Nigerian market terminology

---

## 3. Frontend Stack

### Next.js 14 (App Router)

**Why We Chose It**
- App Router provides better performance with React Server Components
- Built-in routing and API routes
- SEO benefits for public market dashboards
- Excellent TypeScript support
- Vercel deployment optimization

**When to Use It**
- Main web dashboard
- Market price explorer
- Admin panel for data management

**Project Structure**
```
/app
  /page.tsx              # Dashboard home
  /markets/page.tsx      # Markets listing
  /commodities/page.tsx  # Commodity prices
  /api/prices/route.ts   # API endpoints
  /layout.tsx            # Root layout
/components
  /ui/                   # shadcn components
  /charts/               # Chart components
/lib
  /api.ts               # API fetch utilities
```

**Nigerian Context**
- RTL support if needed for Hausa interface
- Optimized for Nigerian network conditions (smaller bundles)

---

### shadcn/ui Components

**Why We Chose It**
- Accessible components out of the box
- Fully customizable - you own the code
- Tailwind integration
- Regular updates and community support

**When to Use It**
- Building consistent UI elements
- Forms for data entry
- Dashboard components

**Installation**
```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card table input dialog chart
```

**Components Used**
- `Card` - Price summary display
- `Table` - Market price listings
- `Dialog` - Commodity details
- `Input` - Search/filter forms
- `Select` - State/market dropdowns

---

### Tailwind CSS

**Why We Chose It**
- Utility-first speeds up styling
- Consistent design system via config
- Easy dark mode support
- Small production bundle

**Basic Configuration**
```javascript
// tailwind.config.js
module.exports = {
  darkMode: ["class"],
  theme: {
    extend: {
      colors: {
        naira: "#008751", // Nigerian green
        market: {
          north: "#FF6B6B",
          south: "#4ECDC4",
          west: "#45B7D1",
        }
      }
    }
  }
}
```

---

### Recharts

**Why We Chose It**
- React-native composability
- Responsive and animated
- Good documentation
- TypeScript support

**When to Use It**
- Price trend charts
- Market comparison graphs
- Historical analysis visualizations

**Basic Usage**
```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

<LineChart data={priceHistory}>
  <XAxis dataKey="date" />
  <YAxis tickFormatter={(v) => `₦${v}`} />
  <Tooltip 
    formatter={(value) => [`₦${value}`, 'Price']}
    contentStyle={{ backgroundColor: '#008751' }}
  />
  <Line 
    type="monotone" 
    dataKey="price" 
    stroke="#008751" 
    strokeWidth={2}
  />
</LineChart>
```

---

### React Query

**Why We Chose It**
- Caching reduces API calls (important for Nigerian data costs)
- Background refetch keeps prices current
- Error handling built-in
- Optimistic updates for better UX

**Setup**
```tsx
// providers.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: true,
    },
  },
});

// Wrap app with QueryClientProvider
```

**Usage**
```tsx
import { useQuery } from '@tanstack/react-query';

function MarketPrices({ marketId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['prices', marketId],
    queryFn: () => fetch(`/api/prices/${marketId}`).then(r => r.json()),
  });

  if (isLoading) return <Skeleton />;
  if (error) return <Alert>Failed to load prices</Alert>;
  
  return <PriceList prices={data} />;
}
```

---

## 4. Database

### PostgreSQL 15+

**Why We Chose It**
- Robust relational database
- JSONB support for flexible schemas
- Window functions for analytics
- Excellent for time-series price data

**When to Use It**
- Core data storage
- Price records, markets, commodities
- User data and authentication

**Schema Example**
```sql
CREATE TABLE markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    state VARCHAR(50) NOT NULL,
    lga VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id),
    commodity_id UUID REFERENCES commodities(id),
    price_ngn DECIMAL(12, 2) NOT NULL,
    unit VARCHAR(50) NOT NULL, -- 'kg', 'cup', 'basket'
    recorded_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(100) -- 'manual', 'scraper', 'api'
);

CREATE INDEX idx_prices_market_date ON prices(market_id, recorded_at DESC);
CREATE INDEX idx_prices_commodity_date ON prices(commodity_id, recorded_at DESC);
```

**Nigerian Context**
- Handle Lagos, Kano, Port Harcourt as major markets
- Store local government areas (LGAs)

---

### pgvector

**Why We Chose It**
- Native vector storage in PostgreSQL
- Enables semantic search on commodity descriptions
- Simplifies the stack (no separate vector DB)
- K-nearest neighbor search for similarity

**When to Use It**
- Storing Sentence Transformer embeddings
- Semantic commodity matching
- Finding similar market descriptions

**Setup**
```sql
-- Enable extension
CREATE EXTENSION vector;

-- Create embedding column
ALTER TABLE commodities ADD COLUMN embedding vector(384);

-- Create index for fast similarity search
CREATE INDEX ON commodities USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Usage**
```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

class Commodity(Base):
    __tablename__ = "commodities"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String)
    description = Column(String)
    embedding = Column(Vector(384))  # all-MiniLM-L6-v2 output size

# Semantic search query
"""
SELECT name, description, 1 - (embedding <=> :query_embedding) as similarity
FROM commodities
ORDER BY embedding <=> :query_embedding
LIMIT 5;
"""
```

---

### Redis

**Why We Chose It**
- Sub-millisecond response for frequently accessed prices
- Session storage for user auth
- Pub/sub for real-time updates
- TTL support for temporary caching

**When to Use It**
- Caching API responses
- Rate limiting scrapers
- Real-time price notifications
- Session management

**Basic Usage**
```python
import redis.asyncio as redis

redis_client = redis.Redis.from_url("redis://localhost:6379")

# Cache price data
await redis_client.setex(
    f"prices:{market_id}:latest",
    300,  # 5 minute TTL
    json.dumps(price_data)
)

# Get cached data
cached = await redis_client.get(f"prices:{market_id}:latest")
```

**Nigerian Context**
- Cache popular markets (Lagos, Kano, Abuja) heavily
- Reduce database load during peak hours

---

## 5. DevOps

### Docker

**Why We Chose It**
- Consistent environments across development and production
- Easy to run full stack locally
- Simplified deployment
- Isolation between services

**When to Use It**
- Development environment
- CI/CD pipelines
- Production deployment
- Testing environments

**Docker Compose Setup**
```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: marketsense
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  web:
    build: ./frontend
    ports:
      - "3000:3000"

volumes:
  postgres_data:
```

**Building**
```bash
# Build all services
docker-compose build

# Run full stack
docker-compose up -d

# View logs
docker-compose logs -f api
```

---

### GitHub Actions

**Why We Chose It**
- Free for public repos
- Native integration with GitHub
- Large community actions available
- Secrets management

**When to Use It**
- CI/CD pipelines
- Running tests on PRs
- Automated deployments

**Workflow Example**
```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
          
      - name: Run tests
        run: pytest --cov=app tests/
        
      - name: Build Docker
        run: docker build -t marketsense/api:latest ./backend
```

**Production Deployment**
```yaml
deploy:
  runs-on: ubuntu-latest
  needs: test
  if: github.ref == 'refs/heads/main'
  
  steps:
    - name: Deploy to server
      uses: appleboy/ssh-action@v1
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USER }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/marketsense
          docker-compose pull
          docker-compose up -d
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│   Dashboard │ Price Explorer │ Admin │ Public Reports           │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼────────────────────────────────────┐
│                     API Layer (FastAPI)                          │
│   REST Endpoints │ WebSocket │ Authentication │ Validation      │
└───────┬────────────────────┬────────────────────┬───────────────┘
        │                    │                    │
   ┌────▼────┐         ┌─────▼─────┐       ┌────▼────┐
   │ PostgreSQL│        │  Redis    │       │ Scrapers│
   │ +pgvector│         │ Cache     │       │(Playwright)
   └──────────┘         └───────────┘       └──────────┘
```

---

## Quick Start Commands

```bash
# Clone and start development
git clone marketsense-ng
cd marketsense-ng

# Backend
cd backend
cp .env.example .env
docker-compose up -d postgres redis
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

---

## Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/marketsense
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
SCRAPER_CONCURRENCY=5

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=MarketSense NG
```

---

## Performance Considerations

- Use connection pooling (50-100 connections for PostgreSQL)
- Set Redis TTL based on data freshness requirements
- Compress embeddings storage if needed
- Use CDN for static assets (Next.js default)
- Implement request debouncing for search

---

## Security Notes

- Never commit `.env` files
- Rotate database passwords regularly
- Use HTTPS in production
- Implement rate limiting on public APIs
- Sanitize all user inputs (XSS protection via React)
- Use prepared statements (SQLAlchemy does this by default)

---

*MarketSense NG - Powering Nigerian market intelligence*