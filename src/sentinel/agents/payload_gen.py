"""MiMo agent #1 — context-aware SQLi payload generation."""
from __future__ import annotations

from typing import Any

from sentinel.mimo_client import MiMoClient

_SYSTEM = """\
You are a SQL-injection payload generator embedded in an automated AppSec
pipeline. Given an HTTP endpoint description, parameter metadata, and an
inferred database fingerprint, you produce 8-12 contextual injection
payloads.

Constraints:
- Each payload targets a specific SQLi class: error-based, boolean-blind,
  time-based, union-based, second-order, or stacked.
- Payloads must be syntactically valid against the inferred DB engine.
- For each payload, emit:
  { "payload", "class", "rationale", "expected_signal" }.
- Never generate destructive payloads (no DROP, no DELETE without WHERE).
- Output strict JSON: {"payloads": [...]}. No prose.
"""


def generate(client: MiMoClient, endpoint: dict[str, Any]) -> list[dict[str, Any]]:
    user = (
        "Generate payloads for the following endpoint:\n\n"
        + _format_endpoint(endpoint)
    )
    out = client.chat(
        agent="payload_gen",
        system=_SYSTEM,
        user=user,
        temperature=0.2,
        max_tokens=2000,
        json_mode=True,
    )
    return out.get("payloads", [])


def _format_endpoint(e: dict[str, Any]) -> str:
    return (
        f"method: {e['method']}\n"
        f"path: {e['path']}\n"
        f"parameters: {e['parameters']}\n"
        f"inferred_table: {e.get('inferred_table')}\n"
        f"db_fingerprint_guess: {e.get('db_fingerprint_guess', 'unknown')}\n"
        f"prior_findings: {e.get('prior_findings', [])}\n"
    )
