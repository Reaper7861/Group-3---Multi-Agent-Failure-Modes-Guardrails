# Telemetry Privacy Metrics

Measured with the deterministic failure demonstration in `test_failure.py`.

| Metric | Before Redaction | After Redaction | Improvement |
|---|---:|---:|---:|
| Sensitive values visible | 5 | 0 | 100% removed |
| Sensitive fields redacted | 0 | 5 | All detected values sanitized |

The test payload contains an email address, API key, account identifier,
database name, and Social Security number. The privacy interceptor redacted all
five before producing the telemetry payload.

```powershell
python priyanka_trace/test_failure.py
```
