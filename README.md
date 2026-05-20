# SQL Injection Sentinel

> Continuous, reasoning-driven SQL injection scanner for production APIs.
> Powered by MiMo multi-agent pipelines.

[![ci](https://github.com/durac9000-star/project-mimo/actions/workflows/ci.yml/badge.svg)](https://github.com/durac9000-star/project-mimo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-alpha-orange)
![MiMo](https://img.shields.io/badge/MiMo-multi--agent-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-3776ab)

## Problem

Modern AppSec scanners (sqlmap, Nuclei, Burp Active Scan) follow rigid payload
playbooks. They miss:

- **Logic-based blind injections** that need contextual reasoning to detect
- **Second-order injections** where payload is stored, then triggered later
- **Chained ORM bypasses** that require understanding the application's data model

Traditional WAF + DAST stack triggers thousands of false positives daily.
Security teams ignore alerts. Real bugs ship.

## Why MiMo?

The detection problem is **long-chain reasoning**, not pattern matching:

1. Read OpenAPI spec → infer table schema
2. Generate context-aware payload (not generic `' OR 1=1`)
3. Read response → reason whether DB error, soft error, blind diff, or false positive
4. Confirm exploit chain → write triage report

Each step needs MiMo's reasoning depth. Cheaper models (GPT-3.5, Llama-7B)
hallucinate exploit paths.

## Architecture (one-paragraph)

A 5-agent pipeline runs continuously against a target's OpenAPI spec.
`schema-extractor` parses the API surface, `payload-fuzz-gen` (MiMo) crafts
injection candidates per endpoint, `response-analyzer` (MiMo) classifies
responses, `exploit-confirmer` (MiMo) chains successful payloads into PoCs,
and `triage-reporter` (MiMo) writes an analyst-grade report. The full
diagram lives in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Token economics

- **15M tokens/day** in continuous mode
- 4 MiMo calls per endpoint × 100 endpoints × 24 sweeps/day
- Full breakdown: [`TOKEN_USAGE.md`](TOKEN_USAGE.md)
- Burn projection: **450M tokens/month** (fits 700M grant comfortably; 1.6B
  unlocks deeper reasoning + more targets)

## Repo layout

```
sql-injection-sentinel/
├── README.md                ← you are here
├── ARCHITECTURE.md          ← full pipeline diagram + agent responsibilities
├── PROMPTS.md               ← every MiMo prompt, with examples
├── TOKEN_USAGE.md           ← per-task + daily aggregation
├── GRANT_PITCH.md           ← copy-paste content for MiMo form
├── LICENSE                  ← MIT
├── pyproject.toml           ← Python tooling
├── src/sentinel/
│   ├── __init__.py
│   ├── orchestrator.py      ← main pipeline runner
│   ├── agents/
│   │   ├── schema_extractor.py
│   │   ├── payload_gen.py   ← MiMo agent #1
│   │   ├── response_analyzer.py  ← MiMo agent #2
│   │   ├── exploit_confirmer.py  ← MiMo agent #3
│   │   └── triage_reporter.py    ← MiMo agent #4
│   └── mimo_client.py       ← thin wrapper around MiMo API
└── examples/
    └── target_openapi.yaml  ← demo target
```

## Quick start

```bash
git clone https://github.com/<account>/sql-injection-sentinel
cd sql-injection-sentinel
poetry install

export MIMO_API_KEY="..."
export TARGET_OPENAPI_URL="https://api.example.com/openapi.json"

python -m sentinel.orchestrator --target $TARGET_OPENAPI_URL --mode continuous
```

## Status

Alpha. PoC pipeline runs end-to-end on the bundled demo OpenAPI spec.
Production targets require auth-token configuration (see `examples/`).

## License

MIT.
