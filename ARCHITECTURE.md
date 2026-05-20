# Architecture — SQL Injection Sentinel

## Pipeline overview

```
┌──────────────────────┐
│  Continuous trigger  │ ← cron, every 1h sweep
│  (per target)        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 1. Schema Extractor  │  deterministic, no MiMo
│  - parse OpenAPI     │
│  - infer DB table    │
│  - rank endpoints    │
└──────────┬───────────┘
           │ endpoint list + inferred schema
           ▼
┌──────────────────────┐
│ 2. Payload Fuzz Gen  │  ★ MiMo call
│  - per endpoint      │
│  - context-aware     │
│  - 8-12 payloads     │
└──────────┬───────────┘
           │ payload candidates
           ▼
┌──────────────────────┐
│ 3. HTTP Executor     │  deterministic
│  - send candidates   │
│  - record responses  │
│  - timing diff       │
└──────────┬───────────┘
           │ response bundle
           ▼
┌──────────────────────┐
│ 4. Response Analyzer │  ★ MiMo call
│  - classify response │
│  - blind/error/diff  │
│  - confidence score  │
└──────────┬───────────┘
           │ candidate exploits
           ▼
┌──────────────────────┐
│ 5. Exploit Confirmer │  ★ MiMo call (deeper reasoning)
│  - chain payloads    │
│  - extract evidence  │
│  - reduce false +    │
└──────────┬───────────┘
           │ confirmed bugs
           ▼
┌──────────────────────┐
│ 6. Triage Reporter   │  ★ MiMo call
│  - severity, CWE     │
│  - PoC steps         │
│  - remediation       │
└──────────┬───────────┘
           ▼
     Report (JSON + MD)
     Storage + alert
```

## Agent responsibilities

### 1. Schema Extractor (deterministic)
Parses OpenAPI 3.x specs, extracts request schemas, infers likely backing
tables/columns based on endpoint nouns. Outputs a ranked list of endpoints
most likely to be SQL-backed.

**No MiMo.**

### 2. Payload Fuzz Gen (MiMo)
For each endpoint and parameter, MiMo generates 8-12 contextual SQLi
payloads. Context includes: parameter type, inferred column type,
surrounding query structure (e.g., `WHERE`, `ORDER BY`, `LIMIT`), database
fingerprint guess.

**MiMo call:** `~3,000 input + 4,500 reasoning + 1,500 output = ~9,000 tokens`

### 3. HTTP Executor (deterministic)
Fires payloads via `httpx`, records status codes, response bodies, response
times, and headers. Three runs per payload to capture timing variance.

**No MiMo.**

### 4. Response Analyzer (MiMo)
Reads response bundle, classifies into: `error-based / blind / time-based /
boolean-based / no-injection`. Confidence score 0-1. Skips obvious negatives
to save tokens.

**MiMo call:** `~2,500 input + 3,000 reasoning + 700 output = ~6,200 tokens`

### 5. Exploit Confirmer (MiMo, deepest reasoning)
For high-confidence candidates, MiMo chains payloads to extract proof
(version banner, db name, table count). False-positive killer.

**MiMo call:** `~4,000 input + 8,000 reasoning + 1,500 output = ~13,500 tokens`

### 6. Triage Reporter (MiMo)
Writes analyst-grade report: severity, CWE classification, exploit narrative,
suggested fix (parameterized query, prepared statement, ORM-specific
escape).

**MiMo call:** `~3,500 input + 4,000 reasoning + 2,000 output = ~9,500 tokens`

## Continuous mode

- **Sweep interval**: 1 hour per target
- **Targets supported**: any OpenAPI 3.x JSON/YAML spec
- **Rate limiting**: configurable; default 1 RPS per endpoint
- **Storage**: SQLite by default; Postgres for production deployments
- **Alerting**: webhook + Slack + Discord adapters

## Why long-chain reasoning matters here

A blind injection on a `LIMIT` clause looks like a 200 OK every time. To
detect it, the model has to:

1. Notice the response is *too consistent* across payloads
2. Hypothesise the parameter is in a non-rendered SQL position
3. Generate a timing-based payload (`SLEEP(5)`)
4. Re-run, measure delta
5. Cross-correlate with baseline timing

That's a 5-step reasoning chain per finding. GPT-3.5-class models routinely
emit hallucinated SQL and false positives. MiMo's reasoning tokens preserve
the chain.

## Resilience

- All agent calls are idempotent; retry on 429/5xx with exponential backoff
- Per-endpoint cache prevents re-scanning unchanged endpoints (ETag + body
  hash)
- Token budget enforced per-target via `MAX_TOKENS_PER_SWEEP` env var
