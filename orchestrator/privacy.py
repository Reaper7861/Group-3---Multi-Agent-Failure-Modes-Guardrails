"""Recursive redaction that runs before telemetry payload construction."""

import re
from typing import Any

SENSITIVE_KEYS = {
    "email", "api_key", "apikey", "account_id", "account", "ssn",
    "database", "database_name", "password", "secret", "token",
}
PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_PII]"),
    (re.compile(r"\b(?:sk-[A-Za-z0-9_-]{8,}|AIza[A-Za-z0-9_-]{20,})\b"), "[REDACTED_SECRET]"),
    (re.compile(r"\b[A-Z][A-Z0-9_]*(?:DB|DATABASE)\b"), "[REDACTED_DATABASE]"),
    (re.compile(r"\b(?:acct|account)[-_]?[A-Za-z0-9]{4,}\b", re.I), "[REDACTED_ACCOUNT]"),
]


def _redact_text(value: str) -> str:
    for pattern, replacement in PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def redact_for_telemetry(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, dict):
        return {
            key: ("[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact_for_telemetry(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_for_telemetry(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_for_telemetry(item) for item in value)
    return _redact_text(value) if isinstance(value, str) else value


def count_sensitive_values(value: Any) -> int:
    text = re.sub(r"\[REDACTED_[A-Z]+\]|\[REDACTED\]", "", str(value))
    return sum(len(pattern.findall(text)) for pattern, _ in PATTERNS)
