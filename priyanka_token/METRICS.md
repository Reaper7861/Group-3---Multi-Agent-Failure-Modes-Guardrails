# Context Window and Token Metrics

Measured with the deterministic failure demonstration in `test_failure.py`.

| Metric | Without Guardrail | With Guardrail | Improvement |
|---|---:|---:|---:|
| Messages retained | 120 | 13 | 89.2% reduction |
| Estimated context tokens | 17,281 | 1,765 | 89.8% reduction |
| Most recent core state preserved | Yes | Yes | No loss of current state |

The context manager summarized older history, removed redundant tool output,
and retained the newest high-value state while remaining below the 2,000-token
demonstration budget.

```powershell
python priyanka_token/test_failure.py
```
