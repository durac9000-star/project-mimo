# Demo

The bundled example pipes a fixture OpenAPI spec into the orchestrator
without hitting the live MiMo API.

```bash
poetry install
export MIMO_API_KEY="<key>"
python -m sentinel.cli \
  --target ./examples/target_openapi.yaml \
  --base-url https://demo-target.local \
  --mode once \
  --max-endpoints 5
```

Expected: scanner extracts ranked endpoints, generates payloads, hits the
target, classifies responses, and writes a triage report when a finding
crosses the confidence threshold.

## Sample reports

- `sample_report.md` — human-readable triage report
- `sample_blind_sqli.json` — confirmed time-based blind SQLi finding (machine-readable)
- `sample_neg_finding.json` — rejected finding showcasing false-positive filtering

The JSON samples mirror the schema produced by `sentinel --output report.json`.
