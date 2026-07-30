"""Sanitize downstream execution payloads before arithmetic."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class DownstreamPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str = Field(min_length=1)
    action: str
    quantity: int = Field(ge=0, le=100)
    price: float = Field(gt=0)


def validate_downstream(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    try:
        DownstreamPayload.model_validate(payload)
        return True, []
    except ValidationError as exc:
        return False, [error["msg"] for error in exc.errors()]
