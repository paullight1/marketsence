import json
import logging
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_request_id_echoes_valid_client_correlation_id(client):
    response = client.get("/health", headers={"X-Request-ID": "market-trace-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "market-trace-123"


def test_request_id_replaces_unbounded_or_invalid_value(client):
    supplied = "x" * 200
    response = client.get("/health", headers={"X-Request-ID": supplied})

    assert response.status_code == 200
    generated = response.headers["X-Request-ID"]
    assert generated != supplied
    uuid.UUID(generated)


def test_request_log_contains_structured_correlation_fields(client, caplog):
    with caplog.at_level(logging.INFO, logger="marketsense.request"):
        response = client.get("/health", headers={"X-Request-ID": "log-trace-1"})

    assert response.status_code == 200
    payloads = []
    for record in caplog.records:
        if record.name != "marketsense.request":
            continue
        try:
            payloads.append(json.loads(record.getMessage()))
        except json.JSONDecodeError:
            continue

    assert any(
        payload.get("request_id") == "log-trace-1"
        and payload.get("method") == "GET"
        and payload.get("path") == "/health"
        and payload.get("status") == 200
        and payload.get("duration_ms", -1) >= 0
        for payload in payloads
    )


def test_readiness_checks_runtime_dependencies(client):
    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"] == {
        "database": "ready",
        "rate_limiter": "ready",
        "export_storage": "ready",
    }


def test_job_metrics_expose_queue_backlog(client):
    queued = client.post(
        "/api/jobs/normalize",
        headers={"Idempotency-Key": "metrics-normalize-1"},
    )
    assert queued.status_code == 202

    response = client.get("/api/ops/job-metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["queued"] == 1
    assert payload["running"] == 0
    assert payload["retrying"] == 0
    assert payload["failed"] == 0
    assert payload["oldest_queued_seconds"] >= 0


def test_dependency_and_update_automation_is_required_in_repo():
    workflow = (REPO_ROOT / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")
    dependabot = (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert "pip-audit==2.10.1" in workflow
    assert "pip-audit -r requirements.txt" in workflow
    assert "npm audit --audit-level=high" in workflow
    assert "npm audit --omit=dev --audit-level=high" not in workflow
    assert 'package-ecosystem: "pip"' in dependabot
    assert 'package-ecosystem: "npm"' in dependabot
    assert 'package-ecosystem: "github-actions"' in dependabot


def test_nextjs_global_security_headers_are_declared():
    config = (REPO_ROOT / "frontend" / "next.config.ts").read_text(encoding="utf-8")

    for header in [
        "Content-Security-Policy",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Strict-Transport-Security",
    ]:
        assert header in config
