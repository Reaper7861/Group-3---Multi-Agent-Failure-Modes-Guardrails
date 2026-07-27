"""Frozen shared state contract for every orchestrator node."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Action = Literal["BUY", "SELL", "HOLD"]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MarketSnapshot(FrozenModel):
    symbol: str = Field(min_length=1)
    price: float = Field(gt=0)
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    volume: int = Field(ge=0)
    change_pct: float


class AnalysisPayload(FrozenModel):
    symbol: str = Field(min_length=1)
    action: Action
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_quantity: int = Field(ge=0)
    rationale: str = Field(min_length=1)
    risk_score: float = Field(ge=0.0, le=1.0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class ToolRequest(FrozenModel):
    tool_name: str
    arguments: Dict[str, Any]


class ExecutionState(FrozenModel):
    status: str
    simulated: bool = True
    tool_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(FrozenModel):
    approved: bool = False
    reasons: List[str] = Field(default_factory=list)
    rollback_required: bool = False


class AgentState(FrozenModel):
    task_domain: str = "financial_trading"
    raw_input: str
    symbol: str
    round_number: int = 0
    retry_count: int = 0
    market_data: Optional[MarketSnapshot] = None
    analysis_payload: Optional[AnalysisPayload] = None
    requested_tool: Optional[ToolRequest] = None
    execution_state: Optional[ExecutionState] = None
    validation_result: Optional[ValidationResult] = None
    portfolio: Dict[str, Any] = Field(default_factory=dict)
    is_validated: bool = False
    rejection_flag: bool = False
    error_log: List[str] = Field(default_factory=list)
    guardrail_events: List[str] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    final_report: Optional[str] = None
    partial_output: Optional[str] = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()
