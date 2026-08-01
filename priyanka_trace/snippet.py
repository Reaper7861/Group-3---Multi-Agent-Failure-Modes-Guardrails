"""Privacy interceptor applied before telemetry."""

from typing import Any

from orchestrator.privacy import redact_for_telemetry


def telemetry_payload(state: Any) -> Any:
    return redact_for_telemetry(state)
