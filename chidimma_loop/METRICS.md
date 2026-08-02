# Infinite Graph Loop Metrics

Measured with the deterministic failure demonstration in `test_failure.py`.

| Metric | Without Guardrail | With Guardrail | Improvement |
|---|---:|---:|---:|
| Coordinator loop iterations | 100 | 5 | 95% reduction |
| Forced safe termination | No | Yes | Infinite continuation prevented |

The baseline coordinator continued routing to the Analyst for all 100 measured
iterations. The round-limit guard stopped execution after 5 iterations and
routed the graph to partial output.

```powershell
python chidimma_loop/test_failure.py
```
