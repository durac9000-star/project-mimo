"""MiMo agent #2 — response classification."""
from __future__ import annotations

from typing import Any

from sentinel.mimo_client import MiMoClient

_SYSTEM = """\
You are a SQL-injection response classifier. Given a payload, the baseline
HTTP response, and the test HTTP response (with metadata), you decide whether
the test response indicates SQL injection.

Output one of:
  - error-based   (DB error string leaked)
  - boolean-blind (response body content differs in a deterministic way)
  - time-based    (response time delta exceeds threshold)
  - no-injection  (no signal)
  - inconclusive  (need more samples)

Always return strict JSON:
  { "verdict", "confidence", "evidence", "next_action" }
Never guess. If unsure, return "inconclusive" with confidence < 0.5.
"""


def analyze(client: MiMoClient, observation: dict[str, Any]) -> dict[str, Any]:
    return client.chat(
        agent="response_analyzer",
        system=_SYSTEM,
        user=f"Observation: {observation}",
        temperature=0.0,
        max_tokens=800,
        json_mode=True,
    )
