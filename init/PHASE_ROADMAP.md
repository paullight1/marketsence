# MarketSense NG - Project Roadmap

**Nigerian Market Price Intelligence System**

---

## Project Overview

MarketSense NG is a price intelligence platform that aggregates product pricing data from multiple Nigerian e-commerce sources, normalizes messy product names, and provides market benchmarks with supplier reliability scoring. The system serves businesses and consumers seeking competitive pricing insights across the Nigerian market.

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, PostgreSQL
- **Data Processing**: Pandas, RapidFuzz, Sentence Transformers, NumPy
- **Scraping**: Playwright, requests-html
- **Frontend**: Next.js 14, shadcn/ui, Tailwind CSS, Recharts

### Data Sources

| Source | Type | Priority |
|--------|------|----------|
| Jiji.ng | E-commerce Marketplace | High |
| Konga.com | E-commerce Platform | High |
| Jumia.com.ng | E-commerce Platform | High |
| Facebook Marketplace | Social Commerce | Medium |
| CSV Imports | Manual Upload | Medium |
| WhatsApp Bot | Direct Input | Low |

---

## Phase 1: Frontend Dashboard

**Timeline**: 4-6 weeks  
**Complexity**: Medium  
**Priority**: Current Focus

### Objectives

Build an interactive dashboard for visualizing market data, price trends, and supplier insights. This phase establishes the UI foundation that all subsequent backend features will connect to.

### Key Tasks

#### 1.1 Project Setup & Infrastructure
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Configure Tailwind CSS and shadcn/ui components
- [ ] Set up project folder structure (components, lib, types, hooks)
- [ ] Configure environment variables and .env.example
- [ ] Set up ESLint and Prettier

#### 1.2 Core UI Components
- [ ] Build responsive layout with sidebar navigation
- [ ] Create dashboard shell with page routing
- [ ] Implement dark/light theme toggle
- [ ] Add loading states and error boundaries
- [ ] Build reusable data table component

#### 1.3 Dashboard Pages
- [ ] **Overview Page**: Key metrics cards, price distribution chart, recent activity
- [ ] **Products Page**: Product listing with search, filters, pagination
- [ ] **Price Trends Page**: Line charts for price history, category breakdown
- [ ] **Suppliers Page**: Supplier reliability scores, performance metrics
- [ ] **Benchmarks Page**: Market benchmarks table, outlier detection view

#### 1.4 Data Visualization
- [ ] Integrate Recharts for charts
- [ ] Build price distribution histogram
- [ ] Create trend line charts with date filtering
- [ ] Implement category pie/bar charts
- [ ] Add interactive tooltips and legends

#### 1.5 State Management
- [ ] Set up React Query for API data fetching
- [ ] Implement caching and invalidation strategies
- [ ] Handle loading/error states globally

#### 1.6 Mock Data Layer
- [ ] Create mock API handlers for development
- [ ] Generate realistic Nigerian product sample data
- [ ] Build JSON fixtures for all page types

### Success Criteria

- [ ] Dashboard loads without errors on all pages
- [ ] Theme toggle works correctly
- [ ] All charts render with mock data
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Navigation between all pages functions correctly
- [ ] Loading and error states display appropriately

### Dependencies

```
next: ^14.0.0
react: ^18.2.0
@tanstack/react-query: ^5.0.0
recharts: ^2.10.0
lucide-react: ^0.300.0
clsx: ^2.0.0
tailwind-merge: ^2.0.0
```

---

## Phase 2: Data Collection & Storage

**Timeline**: 6-8 weeks  
**Complexity**: High  
**Priority**: High

### Objectives

Build the data pipeline for collecting product prices from multiple Nigerian e-commerce sources. Establish PostgreSQL database schema and implement scrapers with proper rate limiting and error handling.

### Key Tasks

#### 2.1 Database Schema Design
- [ ] Design PostgreSQL schema (products, prices, suppliers, categories, sources)
- [ ] Create migrations for all tables
- [ ] Set up indexes for common queries
- [ ] Implement RLS (Row Level Security) policies
- [ ] Add created_at, updated_at timestamps to all tables
- [ ] Create enum types for source, category, price_quality

```sql
-- Core Tables Schema
products: id, name, normalized_name, category_id, embeddings, created_at
prices: id, product_id, source, supplier_id, amount, currency, url, scraped_at
suppliers: id, name, source, reliability_score, total_products, last_scraped
categories: id, name, parent_id, slug
```

#### 2.2 Jiji.ng Scraper
- [ ] Set up Playwright with stealth configuration
- [ ] Build category listing page scraper
- [ ] Implement product detail page parser
- [ ] Add pagination handling
- [ ] Implement rate limiting (max 1 req/2sec)
- [ ] Handle JavaScript-rendered content
- [ ] Store raw HTML for debugging

#### 2.3 Konga Scraper
- [ ] Build product search API scraper
- [ ] Implement category endpoint parser
- [ ] Handle pagination and filtering
- [ ] Extract product variants (colors, sizes)
- [ ] Handle authentication tokens

#### 2.4 Jumia Scraper
- [ ] Create scraper for Jumia product listings
- [ ] Implement search API integration
- [ ] Handle pagination limits
- [ ] Extract seller information
- [ ] Process product specifications

#### 2.5 Facebook Marketplace Scraper
- [ ] Set up Facebook Marketplace parser
- [ ] Handle location-based search
- [ ] Implement post ID extraction
- [ ] Handle rate limiting and login requirements

#### 2.6 CSV Import Handler
- [ ] Build CSV upload endpoint (FastAPI)
- [ ] Implement column mapping UI
- [ ] Validate required fields (product_name, price, source)
- [ ] Handle different encodings (UTF-8, Latin-1)
- [ ] Bulk insert with batch processing

#### 2.7 WhatsApp Integration (Future)
- [ ] Design WhatsApp bot flow
- [ ] Set up Twilio webhook handlers
- [ ] Implement natural language price parsing
- [ ] Build admin approval queue

#### 2.8 Scraper Infrastructure
- [ ] Create scraper base class with common methods
- [ ] Implement retry logic with exponential backoff
- [ ] Build scraper scheduler (APScheduler)
- [ ] Set up Redis for request queue
- [ ] Create scraper health monitoring
- [ ] Implement proxy rotation (optional)

### Success Criteria

- [ ] All three major sources (Jiji, Konga, Jumia) scraping successfully
- [ ] Database schema handles all required data
- [ ] CSV import processes files with 1000+ rows
- [ ] Scraper error rate below 5%
- [ ] No IP blocks or rate limit triggers
- [ ] Data stored with proper timestamps and source tracking

### Dependencies

```
playwright: ^1.40.0
asyncpg: ^0.29.0
sqlalchemy: ^2.0.0
python-dotenv: ^1.0.0
apscheduler: ^3.10.0
redis: ^5.0.0
httpx: ^0.25.0
```

---

## Phase 3: Data Cleaning & Normalization

**Timeline**: 4-6 weeks  
**Complexity**: High  
**Priority**: High

### Objectives

Build robust data cleaning pipelines to standardize messy product names from various sources. Implement fuzzy matching and embedding-based similarity to deduplicate products.

### Key Tasks

#### 3.1 Product Name Cleaning Pipeline
- [ ] Build text cleaning utilities (lowercase, remove special chars)
- [ ] Implement Nigerian-specific cleaning (remove "Nigeria", "Lagos", etc.)
- [ ] Handle common OCR errors and typos
- [ ] Remove duplicate whitespace and unicode normalization

#### 3.2 Fuzzy Matching Implementation
- [ ] Set up RapidFuzz for Levenshtein distance
- [ ] Implement token-based matching for product names
- [ ] Create threshold configuration (score > 85 = match)
- [ ] Build batch matching with progress tracking
- [ ] Handle edge cases (abbreviations, measurements)

#### 3.3 Embedding-Based Matching
- [ ] Set up Sentence Transformers (paraphrase-multilingual-MiniLM-L12)
- [ ] Generate embeddings for all product names
- [ ] Implement cosine similarity matching
- [ ] Combine fuzzy + embedding for higher accuracy
- [ ] Build hybrid matching pipeline

#### 3.4 Product Normalization Engine
- [ ] Create product canonical form generator
- [ ] Implement category inference from product name
- [ ] Build brand extraction logic
- [ ] Handle unit standardization (kg, pieces, liters)
- [ ] Create product variant grouping

#### 3.5 Deduplication System
- [ ] Build duplicate detection workflow
- [ ] Implement merge strategies (keep latest, highest confidence)
- [ ] Create duplicate resolution UI
- [ ] Build manual review queue for low-confidence matches
- [ ] Track deduplication statistics

#### 3.6 Data Validation
- [ ] Implement price validation rules (no negative, reasonable range)
- [ ] Create outlier flagging system
- [ ] Build URL validation and verification
- [ ] Handle missing required fields
- [ ] Create data quality scoring

### Success Criteria

- [ ] 90%+ product name matching accuracy
- [ ] Cleaned products have consistent naming
- [ ] Duplicate detection catches 95%+ of duplicates
- [ ] Data quality score above 80%
- [ ] Processing 10,000 products in under 10 minutes

### Dependencies

```
rapidfuzz: ^3.5.0
sentence-transformers: ^2.2.0
numpy: ^1.24.0
scikit-learn: ^1.3.0
```

---

## Phase 4: Market Analytics

**Timeline**: 5-7 weeks  
**Complexity**: High  
**Priority**: High

### Objectives

Build analytics engine that computes market benchmarks, detects suspicious prices, and generates supplier reliability scores. Create the core value proposition of the platform.

### Key Tasks

#### 4.1 Benchmark Calculations
- [ ] Implement statistical functions (mean, median, mode)
- [ ] Calculate min/max prices per product
- [ ] Compute price percentiles (25th, 50th, 75th, 90th)
- [ ] Build category-level aggregations
- [ ] Handle time-based benchmarks (daily, weekly, monthly)
- [ ] Create price distribution analysis

#### 4.2 Suspicious Price Detection
- [ ] Implement IQR (Interquartile Range) outlier detection
- [ ] Build Z-score based anomaly detection
- [ ] Create historical price deviation flags
- [ ] Handle seasonal price variations
- [ ] Build false listing detection (too good to be true)
- [ ] Create manual review queue for flagged items

#### 4.3 Supplier Reliability Scoring
- [ ] Build scoring algorithm based on:
  - Price consistency (low variance = higher score)
  - Update frequency (regular updates = trust)
  - Data completeness (all fields populated)
  - Historical accuracy (price matches actual)
  - Response rate (from WhatsApp bot)
- [ ] Implement score normalization (0-100 scale)
- [ ] Create supplier tiers (A, B, C, D)
- [ ] Build historical score tracking

#### 4.4 Trend Analysis
- [ ] Implement price trend calculations
- [ ] Build moving average calculations
- [ ] Create period-over-period comparisons
- [ ] Detect price spikes and drops
- [ ] Build category trend summaries

#### 4.5 Analytics API Endpoints
- [ ] Create `/api/v1/benchmarks/product/{id}`
- [ ] Create `/api/v1/analytics/trends`
- [ ] Create `/api/v1/analytics/outliers`
- [ ] Create `/api/v1/suppliers/scores`
- [ ] Implement caching for expensive queries

#### 4.6 Reporting Engine
- [ ] Build scheduled report generation
- [ ] Create PDF/CSV export functionality
- [ ] Implement email notifications for price alerts
- [ ] Build dashboard refresh scheduling

### Success Criteria

- [ ] Benchmarks calculated for all products with 3+ prices
- [ ] Outlier detection accuracy above 90%
- [ ] Supplier scores updated daily
- [ ] API response time under 500ms for analytics
- [ ] Trend data shows 30+ days of history

### Dependencies

```
scipy: ^1.11.0
statsmodels: ^0.14.0
redis: ^5.0.0
```

---

## Phase 5: API & Deployment

**Timeline**: 4-6 weeks  
**Complexity**: Medium  
**Priority**: High

### Objectives

Build production-ready REST API with FastAPI, set up CI/CD pipelines, and deploy to cloud infrastructure. Complete the full system integration.

### Key Tasks

#### 5.1 FastAPI Backend Development
- [ ] Set up FastAPI project structure
- [ ] Implement authentication (JWT tokens)
- [ ] Create rate limiting middleware
- [ ] Build API versioning strategy
- [ ] Implement request validation (Pydantic models)
- [ ] Add OpenAPI documentation
- [ ] Create error handling and logging

#### 5.2 API Endpoints Structure
```python
# Core Endpoints
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/products
GET    /api/v1/products/{id}
GET    /api/v1/prices/history/{product_id}
GET    /api/v1/benchmarks/{product_id}
GET    /api/v1/analytics/trends
GET    /api/v1/analytics/outliers
GET    /api/v1/suppliers
GET    /api/v1/suppliers/{id}/scores
POST   /api/v1/import/csv
GET    /api/v1/categories
GET    /api/v1/search
```

#### 5.3 Frontend-Backend Integration
- [ ] Connect dashboard to real API endpoints
- [ ] Implement authentication flow
- [ ] Build API service layer in frontend
- [ ] Handle JWT token refresh
- [ ] Implement proper error handling

#### 5.4 Database Optimization
- [ ] Add query optimization (EXPLAIN ANALYZE)
- [ ] Implement connection pooling
- [ ] Add database caching layer
- [ ] Create materialized views for analytics
- [ ] Set up database backup strategy

#### 5.5 CI/CD Pipeline
- [ ] Set up GitHub Actions workflow
- [ ] Create lint/format checks (Black, Ruff)
- [ ] Implement test suite (pytest)
- [ ] Build Docker containers
- [ ] Set up staging environment

#### 5.6 Cloud Deployment
- [ ] Deploy to Render/Railway/Vercel
- [ ] Set up PostgreSQL database (Supabase/Neon)
- [ ] Configure environment variables
- [ ] Set up domain and SSL
- [ ] Configure monitoring (Sentry, Logs)
- [ ] Set up cron jobs for scrapers

#### 5.7 Performance & Security
- [ ] Implement API rate limiting
- [ ] Add CORS configuration
- [ ] Set up request logging
- [ ] Implement health check endpoints
- [ ] Configure Redis caching
- [ ] Add security headers

### Success Criteria

- [ ] All API endpoints return correct data
- [ ] Authentication flow works correctly
- [ ] Frontend fully integrated with backend
- [ ] CI/CD pipeline runs successfully
- [ ] Application deploys without errors
- [ ] Response times meet SLA (< 500ms)

---

## Overall Timeline Summary

| Phase | Duration | Total Weeks |
|-------|----------|-------------|
| Phase 1: Frontend Dashboard | 4-6 weeks | 4-6 |
| Phase 2: Data Collection & Storage | 6-8 weeks | 10-14 |
| Phase 3: Data Cleaning & Normalization | 4-6 weeks | 14-20 |
| Phase 4: Market Analytics | 5-7 weeks | 19-27 |
| Phase 5: API & Deployment | 4-6 weeks | 23-33 |

**Estimated Total**: 6-8 months for MVP

---

## Critical Path Items

1. **Database Schema** (Phase 2) - Foundation for all data
2. **Product Normalization** (Phase 3) - Core value proposition
3. **Benchmark Calculations** (Phase 4) - Analytics engine
4. **API Integration** (Phase 5) - Frontend-backend connection

---

## Risk Factors & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scraper blocks | High | Implement proxy rotation, reduce request rate |
| Data quality issues | High | Build robust validation, manual review queue |
| Performance at scale | Medium | Implement caching, optimize queries |
| API rate limits | Medium | Use official APIs where available |
| Nigerian payment issues | Low | Focus on free tier first |

---

## Next Steps

1. **Immediate**: Complete Phase 1 (Frontend Dashboard)
2. **After Phase 1**: Begin Phase 2 database setup and scraper development
3. **Parallel**: Start product normalization research during Phase 2
4. **Final**: Deploy MVP after Phase 5

---

*Last Updated: May 2026*
*Version: 1.0*