"""Student 5: privacy interceptor applied before telemetry."""

from typing import Any

from privacy import redact_for_telemetry


def telemetry_payload(state: Any) -> Any:
    return redact_for_telemetry(state)
