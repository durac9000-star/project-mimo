"""Lightweight orchestrator — wires the 5 agents into a sweep loop."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from sentinel.agents import (
    exploit_confirmer,
    payload_gen,
    response_analyzer,
    schema_extractor,
    triage_reporter,
)
from sentinel.mimo_client import MiMoClient

logger = logging.getLogger(__name__)


@dataclass
class SweepConfig:
    target_openapi_url: str
    base_url: str
    sweep_interval_sec: int = 3600
    rps: float = 1.0
    max_endpoints: int = 100


def run_once(cfg: SweepConfig, mimo: MiMoClient) -> dict:
    """One sweep over the target. Returns aggregate report payload."""
    spec_text = httpx.get(cfg.target_openapi_url, timeout=15).text
    spec = schema_extractor.load_spec(spec_text)
    endpoints = schema_extractor.extract_endpoints(spec)[: cfg.max_endpoints]
    logger.info("sweep: %d endpoints", len(endpoints))

    findings: list[dict] = []
    for ep in endpoints:
        ep_dict = {
            "method": ep.method,
            "path": ep.path,
            "parameters": ep.parameters,
            "inferred_table": ep.inferred_table,
        }
        payloads = payload_gen.generate(mimo, ep_dict)

        for p in payloads:
            obs = _execute(cfg.base_url, ep, p)
            verdict = response_analyzer.analyze(mimo, obs)
            if verdict.get("verdict") in {"error-based", "time-based", "boolean-blind"} \
                    and verdict.get("confidence", 0) >= 0.7:
                confirmed = exploit_confirmer.confirm(
                    mimo,
                    {"endpoint": ep_dict, "payload": p, "verdict": verdict},
                )
                if confirmed.get("verdict") == "confirmed":
                    rep = triage_reporter.report(
                        mimo,
                        {**confirmed, "endpoint": ep_dict},
                    )
                    findings.append(rep)
            time.sleep(1.0 / cfg.rps)

    return {
        "endpoints_scanned": len(endpoints),
        "findings": findings,
        "tokens": mimo.ledger.snapshot(),
    }


def _execute(base: str, ep, payload: dict) -> dict:
    """Send a single payload, capture response shape and timing."""
    url = base.rstrip("/") + ep.path
    method = ep.method
    started = time.monotonic()
    try:
        r = httpx.request(method, url, params={"_": payload["payload"]}, timeout=15)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return {
            "payload": payload,
            "status": r.status_code,
            "time_ms": elapsed_ms,
            "body_excerpt": r.text[:600],
        }
    except httpx.RequestError as exc:
        return {"payload": payload, "error": str(exc)}


def run_continuous(cfg: SweepConfig, mimo: MiMoClient) -> None:
    while True:
        run_once(cfg, mimo)
        time.sleep(cfg.sweep_interval_sec)
