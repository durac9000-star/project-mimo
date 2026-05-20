"""MiMo agent #4 — analyst-grade triage report writer."""
from __future__ import annotations

from typing import Any

from sentinel.mimo_client import MiMoClient

_SYSTEM = """\
You write security analyst-grade reports for confirmed SQL injection
vulnerabilities. Audience: senior engineers and AppSec leads.

Each report contains:
- Title (CWE-89 format)
- Severity (CVSS 3.1 vector + score)
- Affected endpoint + parameter
- Reproduction steps
- Suggested fix with code-level snippet (parameterized query in the
  detected stack)
- References (OWASP, CWE, vendor docs)

Tone: precise, no flourish. Markdown output (return JSON: {"markdown": "..."}).
"""


def report(client: MiMoClient, finding: dict[str, Any]) -> dict[str, Any]:
    return client.chat(
        agent="triage_reporter",
        system=_SYSTEM,
        user=f"Confirmed finding: {finding}",
        temperature=0.1,
        max_tokens=2500,
        json_mode=True,
    )
