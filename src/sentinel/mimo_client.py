"""Thin wrapper around the Xiaomi MiMo chat-completions endpoint.

The wrapper centralises:
- API-key handling (`MIMO_API_KEY` env var)
- Retry with exponential backoff
- Token-budget accounting per agent
- Optional debug logging of prompts/responses

Keep this file minimal so all reasoning lives inside the agents themselves.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

MIMO_BASE = os.getenv("MIMO_API_BASE", "https://platform.xiaomimimo.com/v1")
DEFAULT_MODEL = os.getenv("MIMO_MODEL", "mimo-7b-rl")


@dataclass
class TokenLedger:
    """Tracks token usage per agent for budget enforcement & reporting."""

    by_agent: dict[str, int] = field(default_factory=dict)
    total: int = 0

    def record(self, agent: str, tokens: int) -> None:
        self.by_agent[agent] = self.by_agent.get(agent, 0) + tokens
        self.total += tokens
        logger.debug("ledger: %s += %d (total %d)", agent, tokens, self.total)

    def snapshot(self) -> dict[str, Any]:
        return {"total": self.total, "by_agent": dict(self.by_agent)}


class MiMoClient:
    """Minimal MiMo chat-completions client with retry + ledger."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        ledger: TokenLedger | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ["MIMO_API_KEY"]
        self.model = model
        self.ledger = ledger or TokenLedger()
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def chat(
        self,
        agent: str,
        system: str,
        user: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4000,
        json_mode: bool = True,
    ) -> dict[str, Any]:
        """Run a single MiMo chat call and return parsed JSON when possible."""
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = self._client.post(
            f"{MIMO_BASE}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        resp.raise_for_status()
        body = resp.json()

        # Token accounting (whatever the API reports; field name may vary)
        usage = body.get("usage", {})
        total_tokens = usage.get("total_tokens") or (
            usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        )
        self.ledger.record(agent, int(total_tokens or 0))

        choice = body["choices"][0]["message"]["content"]
        if json_mode:
            try:
                return json.loads(choice)
            except json.JSONDecodeError:
                logger.warning("agent %s returned non-JSON; surfacing raw text", agent)
                return {"_raw": choice}
        return {"content": choice}
