"""Unit tests for payload_gen helpers — pure logic, no MiMo calls."""
from __future__ import annotations

from sentinel.agents import payload_gen


def test_format_endpoint_includes_required_fields():
    ep = {
        "method": "GET",
        "path": "/users/{id}",
        "parameters": [{"name": "id", "in": "path", "type": "integer"}],
        "inferred_table": "users",
        "db_fingerprint_guess": "postgres",
        "prior_findings": [],
    }
    formatted = payload_gen._format_endpoint(ep)
    assert "method: GET" in formatted
    assert "path: /users/{id}" in formatted
    assert "inferred_table: users" in formatted
    assert "db_fingerprint_guess: postgres" in formatted


def test_format_endpoint_handles_missing_optional_fields():
    ep = {
        "method": "POST",
        "path": "/search",
        "parameters": [{"name": "q", "in": "query"}],
    }
    formatted = payload_gen._format_endpoint(ep)
    assert "inferred_table: None" in formatted
    assert "db_fingerprint_guess: unknown" in formatted
    assert "prior_findings: []" in formatted


def test_format_endpoint_preserves_prior_findings():
    findings = ["error-based at id 2025-01-15", "blind boolean at search 2025-02-03"]
    ep = {
        "method": "GET",
        "path": "/api",
        "parameters": [],
        "prior_findings": findings,
    }
    formatted = payload_gen._format_endpoint(ep)
    assert "error-based at id" in formatted
    assert "blind boolean at search" in formatted
