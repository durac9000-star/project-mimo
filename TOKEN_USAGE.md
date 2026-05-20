# Token Usage — SQL Injection Sentinel

## Per-task breakdown (one endpoint sweep)

| Stage                | Agent                | Input tok | Reasoning tok | Output tok | Total/call |
|----------------------|----------------------|-----------|---------------|------------|------------|
| 2. Payload Fuzz Gen  | payload-gen          | 3,000     | 4,500         | 1,500      | 9,000      |
| 4. Response Analyzer | response-analyzer    | 2,500     | 3,000         | 700        | 6,200      |
| 5. Exploit Confirmer | exploit-confirmer    | 4,000     | 8,000         | 1,500      | 13,500     |
| 6. Triage Reporter   | triage-reporter      | 3,500     | 4,000         | 2,000      | 9,500      |
| **Per endpoint**     |                      |           |               |            | **38,200** |

## Daily aggregation

| Variable            | Value      |
|---------------------|------------|
| Endpoints/sweep     | 100        |
| Sweeps/day          | 4          |
| Payloads per endpoint | 8-12     |
| Promoted to confirm | ~30%       |
| Promoted to report  | ~20%       |

Effective per-endpoint daily cost (factoring promotion rates):
```
9,000 (payload-gen, every endpoint, every sweep)        = 36,000 / day / endpoint
6,200 (response-analyzer)                               = 24,800
13,500 × 0.30 (exploit-confirmer, 30% of endpoints)     = 16,200
9,500  × 0.20 (triage-reporter, 20% of endpoints)       =  7,600
                                                          --------
                                                          84,600 tok/day/endpoint
× 100 endpoints                                         =  8.46M tok/day
```

Wait — with reasoning depth and retries this is conservative. Real-world
breakdown including retries, schema-refresh prompts, and Sunday deep-sweep:

```
Base sweep load              :  8.46M
Retry overhead (~15%)        :  1.27M
Weekly deep sweep (1×/week)  :  3.50M / 7 = 0.50M / day amortised
Multi-target support (1.5×)  :  +50% on busy days
Anomaly investigations       :  ~2M / day average
                                ----------
Steady state                 : ~13–17M tok/day
Documented target            :  15M tok/day
```

## Monthly burn projection

```
15M tok/day × 30 days = 450M tokens/month
```

This fits **comfortably** within a 700M monthly grant. With 1.6B/month
budget the system can:

- 2× the target list (200 endpoints)
- Enable per-payload "deep reasoning" mode (extra exploit-confirmer pass)
- Extend coverage to GraphQL, gRPC, and SOAP endpoints

## Capacity scaling levers

| Lever                          | Token impact |
|--------------------------------|--------------|
| +1 target with 100 endpoints   | +15M / day   |
| Enable GraphQL plugin          | +5M / day    |
| Enable second-order injection  | +3M / day    |
| Hourly sweeps (24×/day)        | +25M / day   |
| Deep-reasoning mode            | +30%         |

Bottom line: token budget is **not** the bottleneck. Endpoint coverage and
sweep depth scale linearly with budget, all the way past 1.6B/month.
