# Sample triage report

## CWE-89: SQL Injection in `/api/v1/products` parameter `sort_by`

**Severity:** High — CVSS 3.1: 8.6
(`AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:L`)

**Endpoint:** `GET /api/v1/products?sort_by={input}`

**Reproduction:**

1. Baseline:
   `curl 'https://api.example.com/v1/products?sort_by=name'` → 142 ms
2. Time-based probe:
   `curl 'https://api.example.com/v1/products?sort_by=name,(SELECT SLEEP(5))'`
   → 5184 ms
3. Fingerprint confirmation:
   `?sort_by=name,IF(MID(@@version,1,1)='8',SLEEP(5),0)` → > 5 s

DB engine confirmed: MySQL 8.x.

**Fix:** Whitelist allowed sort columns; never inject user input into
`ORDER BY`.

```python
ALLOWED = {"name", "price", "created_at"}
sort_by = request.args.get("sort_by")
if sort_by not in ALLOWED:
    abort(400, "invalid sort column")
```

**References:**
- OWASP SQL Injection Prevention Cheat Sheet
- CWE-89: Improper Neutralization of Special Elements used in an SQL Command
