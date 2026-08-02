# Downstream Cascade Failure Metrics

Measured with the deterministic failure demonstration in `test_failure.py`.

| Metric | Without Guardrail | With Guardrail | Improvement |
|---|---:|---:|---:|
| Downstream crashes | 1 | 0 | 100% prevented |
| Malformed payloads rejected | 0 | 1 | Bad state stopped upstream |
| Validation errors captured | 0 | 2 | Quantity and price errors identified |

The malformed quantity `"TEN THOUSAND"` and `None` price caused a baseline
arithmetic failure. The cascade guard rejected the payload before downstream
calculation and marked the integrated state for rollback.

```powershell
python subhan_cascade/test_failure.py
```
