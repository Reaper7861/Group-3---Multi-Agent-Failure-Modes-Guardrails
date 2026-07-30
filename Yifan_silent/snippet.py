"""Pydantic schema guard with one retry maximum."""
from pydantic import ValidationError

from orchestrator.config import MAX_RETRIES
from contract import AnalysisPayload


def validate_with_retry(payloads: list[dict]) -> tuple[AnalysisPayload | None, int]:
    retries = 0
    for payload in payloads[: MAX_RETRIES + 1]:
        try:
            return AnalysisPayload.model_validate(payload), retries
        except ValidationError:
            if retries >= MAX_RETRIES:
                break
            retries += 1
    return None, retries
