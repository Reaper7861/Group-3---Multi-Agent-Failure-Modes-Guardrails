# Silent Hallucination Metrics

Measured with the deterministic failure demonstration in `test_failure.py`.

| Metric | Without Guardrail | With Guardrail | Improvement |
|---|---:|---:|---:|
| Invalid payloads accepted | 2 | 0 | 100% prevented |
| Automatic correction retries | 0 | 2 | One retry per invalid payload |

The unguarded baseline trusted both malformed model outputs. Schema validation
rejected both payloads and attempted a controlled correction retry for each.

```powershell
python Yifan_silent/test_failure.py
```
