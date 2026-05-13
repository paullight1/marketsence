# Development Workflow

## 1. Project Structure

```
/backend      FastAPI application (API routes, models, services)
/frontend     Next.js application (React components, pages)
/scripts      Data processing scripts (scraping, ETL)
/data         CSVs and sample data
```

## 2. Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional, for caching)

### Environment Variables

**Backend** (`.env` in `/backend`):
```
DATABASE_URL=postgresql://user:pass@localhost:5432/price_intel
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000
```

**Frontend** (`.env.local` in `/frontend`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running Locally

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Scripts
cd scripts
pip install -r requirements.txt
```

## 3. Git Workflow

### Branch Naming
- `feature/price-scraping` - New features
- `fix/api-response-error` - Bug fixes
- `docs/setup-guide` - Documentation
- `refactor/dashboard-ui` - Refactoring

### Commit Messages
```
feat: add price tracking dashboard
fix: resolve API timeout issue
docs: update README
refactor: simplify data models
test: add unit tests for scraper
```

### Pull Request Process
1. Create feature branch from `main`
2. Make changes, commit frequently
3. Push and open PR with description
4. Request review
5. Address feedback
6. Squash and merge

## 4. Code Quality

### Linting
```bash
# Frontend
npm run lint

# Backend
ruff check .
```

### Type Checking
```bash
# Frontend
npm run typecheck

# Backend
mypy app/
```

### Pre-commit Hooks
Install: `pre-commit install`

Runs on every commit:
- Ruff (Python)
- ESLint (JS/TS)
- Prettier formatting

## 5. Testing Strategy

### Backend (pytest)
```bash
cd backend
pytest tests/ -v
```

### API Testing
```bash
pytest tests/api/ -v  # Uses httpx TestClient
```

### Frontend Testing
```bash
npm run test        # Jest unit tests
npm run test:e2e    # Playwright e2e tests
```

## 6. Project Milestones

| Milestone | Description | Deliverables |
|-----------|-------------|---------------|
| M1 | Frontend Dashboard with mock data | Dashboard UI, mock API responses |
| M2 | Backend API + database | FastAPI endpoints, PostgreSQL schema |
| M3 | Data pipeline working | Price scrapers, ETL scripts, data storage |
| M4 | Analytics complete | Charts, alerts, reports |

### M1 Checklist
- [ ] Next.js app scaffolded
- [ ] Dashboard layout with navigation
- [ ] Mock product data displayed
- [ ] Basic chart component (price trends)
- [ ] Responsive design

### M2 Checklist
- [ ] PostgreSQL schema (products, prices, alerts)
- [ ] CRUD API endpoints
- [ ] Database connection with SQLAlchemy
- [ ] Environment config
- [ ] API tests

### M3 Checklist
- [ ] Price scraper (configurable sources)
- [ ] ETL pipeline for data processing
- [ ] Scheduled data updates
- [ ] Data validation
- [ ] Error handling

### M4 Checklist
- [ ] Analytics dashboard with real data
- [ ] Price alert system
- [ ] Export functionality (CSV)
- [ ] Performance optimization
- [ ] Documentation
