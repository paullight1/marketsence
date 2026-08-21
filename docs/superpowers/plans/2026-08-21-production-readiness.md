# MarketSense Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the eight remaining production-release blockers in the existing MarketSense hardening PR without weakening the evidence-gated review boundary.

**Architecture:** Keep the existing FastAPI + Next.js product shape, add security and operations primitives behind focused services, migrate persistence deliberately through Alembic, and make production mode fail closed when required infrastructure is absent. Each gate is test-first and ends with backend compile/tests plus frontend lint/build before the next gate begins.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL/SQLite test compatibility, Redis, Next.js 16, React 19, Pytest, GitHub Actions.

**Spec:** PR #1 production-readiness blockers and this plan.

## Global Constraints

- Never write directly to `main`; continue on `review/marketsence-hardening-20260821`.
- Preserve current API behavior unless a security/correctness contract requires a breaking change.
- Production mode must fail closed when required secrets/infrastructure are missing.
- Add failing regression evidence before each behavior change.
- Do not mark the PR ready while any software P0/P1 gate or required CI verification is red.
- External credentials/services may remain deployment inputs, but their software integration, validation, fallbacks, and failure modes must be implemented and tested.

---

### Task 1: Authentication, authorization, CSRF strategy, and distributed rate limiting

**Files:**
- Create: `backend/app/api/auth.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/rate_limit.py`
- Create: `backend/tests/test_auth_rate_limit.py`
- Create: `frontend/src/app/login/page.tsx`
- Modify: backend config/main/routes, requirements, frontend API/session utilities and header controls.

**Interfaces:**
- Bearer access tokens signed with HMAC-SHA256 and short expiration.
- Scrypt password hashes; no plaintext production password storage.
- Roles: `viewer < analyst < admin`.
- Cookie credentials are not accepted; bearer-only auth is the CSRF strategy.
- Redis fixed-window limiter in production; in-memory limiter only for dev/test.

- [ ] Write RED endpoint tests for auth, roles, cookie rejection, throttling, and production fail-closed config.
- [ ] Implement security primitives and protected route dependencies.
- [ ] Implement Redis/in-memory limiter and production validation.
- [ ] Add frontend login/session-token flow and authenticated API helper.
- [ ] Run full quality gate and record evidence.

### Task 2: Durable background jobs

**Files:**
- Create job model/service/worker modules and job API routes.
- Modify scrape, normalization, benchmark, and bulk import write paths to enqueue durable work where appropriate.

**Interfaces:**
- Persisted job states: queued, running, retrying, review, completed, failed, cancelled.
- Idempotency key, attempts, retry schedule, cancellation, structured error/result metadata.
- Worker leases prevent duplicate concurrent execution.

- [ ] RED tests for persistence, retry, idempotency, lease recovery, and cancellation.
- [ ] Implement durable DB-backed queue and worker command.
- [ ] Convert long-running operations to jobs while preserving small synchronous read paths.
- [ ] Update Tasks UI to display real jobs.
- [ ] Run full quality gate.

### Task 3: PostgreSQL and Alembic-owned schema lifecycle

**Files:**
- Create Alembic environment/config and baseline migration(s).
- Modify database startup and CI migration verification.

**Interfaces:**
- Production requires PostgreSQL.
- App startup never mutates schema with `create_all` in production.
- Alembic `upgrade head` owns schema creation/evolution.

- [ ] RED tests/config checks proving production rejects SQLite/startup schema creation.
- [ ] Implement Alembic baseline including all current tables/jobs/auth-supporting schema.
- [ ] Add migration smoke verification to CI.
- [ ] Run full quality gate.

### Task 4: Fixed-point monetary storage

**Files:**
- Modify models/schemas/services/analytics/catalog/market code and migrations.

**Interfaces:**
- Prices use `Decimal` and SQL `NUMERIC`, with explicit scale/rounding.
- API JSON remains numeric-compatible without binary-float benchmark drift.

- [ ] RED precision/rounding regression tests.
- [ ] Migrate Float prices/history to NUMERIC safely.
- [ ] Remove float conversions from pricing calculations.
- [ ] Run full quality gate.

### Task 5: Concurrent-safe uniqueness, upserts, and idempotency

**Files:**
- Modify models/migrations/ingest services and tests.

**Interfaces:**
- Supplier identity has a database uniqueness constraint.
- Listing ingestion accepts/derives stable idempotency keys.
- Concurrent retries do not inflate listing/supplier counts.

- [ ] RED duplicate/concurrency/idempotency tests.
- [ ] Add constraints/indexes and dialect-safe upserts.
- [ ] Make API report added vs duplicate records accurately.
- [ ] Run full quality gate.

### Task 6: Authenticated object storage for cleaned exports

**Files:**
- Create storage abstraction and S3-compatible implementation.
- Modify CSV cleaning/download flow and config/tests.

**Interfaces:**
- Production uses private object storage with lifecycle-compatible keys and authenticated download endpoints/presigned URLs.
- Local filesystem remains dev/test-only.

- [ ] RED tests for private object keys, authorization, expiry, and production fail-closed storage config.
- [ ] Implement storage abstraction and S3-compatible adapter.
- [ ] Preserve local adapter for tests/development.
- [ ] Run full quality gate.

### Task 7: Infrastructure egress policy and production scrape allowlist

**Files:**
- Add deploy/network policy examples and startup enforcement.
- Strengthen scraper resolver/redirect behavior and tests.

**Interfaces:**
- Production requires non-empty domain allowlist.
- DNS pinning/re-resolution behavior is explicit.
- Deployment artifacts document/block metadata/private egress where platform supports it.

- [ ] RED production-policy tests.
- [ ] Enforce production allowlist and hardened destination checks.
- [ ] Add container/deployment network-security documentation/config where repository deploy targets permit.
- [ ] Run full quality gate.

### Task 8: Dependency security automation and observability

**Files:**
- Modify GitHub workflows/dependency config.
- Add structured logging/request IDs/metrics/health-readiness support.
- Add frontend security headers and error instrumentation hooks.

**Interfaces:**
- CI performs dependency vulnerability audit and lock/version drift checks.
- Runtime emits structured request/job logs with correlation IDs and useful readiness checks.
- Production health distinguishes liveness from dependency readiness.

- [ ] RED observability/readiness tests.
- [ ] Implement request IDs, structured logs, readiness checks, job metrics, and security headers.
- [ ] Add dependency audit/update automation.
- [ ] Run the final full quality gate and update PR evidence/blocker list.
