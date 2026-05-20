"""Schema extractor — deterministic, no MiMo.

Parses an OpenAPI 3.x spec and ranks endpoints by SQL-injection prior.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class EndpointTarget:
    method: str
    path: str
    parameters: list[dict[str, Any]]
    inferred_table: str | None = None
    rank: float = 0.0


# Heuristic: noun-like path segments often map to DB tables.
_DB_HINT_WORDS = {
    "user", "users", "account", "accounts", "order", "orders",
    "product", "products", "post", "posts", "comment", "comments",
    "transaction", "transactions", "session", "sessions",
}


def load_spec(text: str) -> dict[str, Any]:
    return yaml.safe_load(text)


def extract_endpoints(spec: dict[str, Any]) -> list[EndpointTarget]:
    endpoints: list[EndpointTarget] = []
    for path, ops in (spec.get("paths") or {}).items():
        for method, op in ops.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            params = (op.get("parameters") or []) + _request_body_params(op)
            target = EndpointTarget(
                method=method.upper(),
                path=path,
                parameters=params,
                inferred_table=_infer_table(path),
            )
            target.rank = _rank(target)
            endpoints.append(target)
    endpoints.sort(key=lambda e: e.rank, reverse=True)
    return endpoints


def _request_body_params(op: dict[str, Any]) -> list[dict[str, Any]]:
    rb = op.get("requestBody") or {}
    content = rb.get("content") or {}
    out = []
    for media in content.values():
        schema = (media.get("schema") or {}).get("properties") or {}
        for name, propspec in schema.items():
            out.append({"name": name, "in": "body", "schema": propspec})
    return out


def _infer_table(path: str) -> str | None:
    for seg in path.strip("/").split("/"):
        s = seg.lower().rstrip("s")
        if seg.lower() in _DB_HINT_WORDS or s in _DB_HINT_WORDS:
            return seg.lower()
    return None


def _rank(target: EndpointTarget) -> float:
    score = 0.0
    if target.inferred_table:
        score += 1.0
    if any(p.get("name", "").lower() in {"id", "user_id", "sort", "filter", "q"}
           for p in target.parameters):
        score += 0.5
    if target.method in {"GET", "POST"}:
        score += 0.2
    return score
