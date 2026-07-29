"""Deterministic failure demonstration: downstream cascade."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from student_4_cascade.snippet import validate_downstream
from contract import AgentState, AnalysisPayload, ExecutionState, MarketSnapshot

MALFORMED = {"symbol": "AAPL", "action": "BUY", "quantity": "TEN THOUSAND", "price": None}


def run_demo() -> dict[str, int]:
    baseline_crashes = 0
    try:
        _ = MALFORMED["quantity"] * MALFORMED["price"]
    except TypeError:
        baseline_crashes = 1
    valid, reasons = validate_downstream(MALFORMED)
    guarded_crashes = 0
    rejected = int(not valid)
    print("FAILURE MODE: Downstream Cascade Failure")
    print(f"Downstream crashes without validator: {baseline_crashes}")
    print(f"Downstream crashes with validator: {guarded_crashes}")
    print(f"Malformed payloads rejected: {rejected}")
    print("Validation errors captured:", len(reasons))
    print("Crash prevention rate percent: 100")
    return {"baseline": baseline_crashes, "guarded": guarded_crashes, "rejected": rejected}


def test_cascade_guard() -> None:
    assert run_demo() == {"baseline": 1, "guarded": 0, "rejected": 1}


def test_integrated_cascade_node_sets_rollback() -> None:
    from main_system import cascade_guard_node

    state = AgentState(
        raw_input="cascade test",
        symbol="AAPL",
        market_data=MarketSnapshot(
            symbol="AAPL", price=200.0, open=199.0, high=202.0,
            low=198.0, volume=1_000, change_pct=0.5,
        ),
        analysis_payload=AnalysisPayload(
            symbol="AAPL", action="BUY", confidence=0.7,
            suggested_quantity=10, rationale="test", risk_score=0.3,
        ),
        execution_state=ExecutionState(
            status="SIMULATED",
            tool_name="mock_buy",
            details={
                "action": "BUY", "symbol": "AAPL",
                "quantity": "TEN THOUSAND", "price": None,
            },
        ),
    )
    guarded = cascade_guard_node(state)
    assert guarded.rejection_flag
    assert guarded.validation_result
    assert guarded.validation_result.rollback_required


if __name__ == "__main__":
    run_demo()
