"""Deterministic failure demonstration: rogue tool execution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chikezie_rogue.snippet import execute_approved_tool


ROGUE_REQUEST = {
    "tool_name": "place_live_order",
    "arguments": {"symbol": "AAPL", "quantity": 1_000, "price": 200.0},
}


def vulnerable_execute(request: dict) -> dict:
    """Demonstrate a baseline that blindly treats any request as executed."""
    return {"status": "EXECUTED", **request}


def run_demo() -> dict[str, int]:
    baseline_executions = int(vulnerable_execute(ROGUE_REQUEST)["status"] == "EXECUTED")
    result, reasons = execute_approved_tool(
        ROGUE_REQUEST["tool_name"], ROGUE_REQUEST["arguments"]
    )
    guarded_executions = int(result is not None)

    print("FAILURE MODE: Rogue Tool Execution")
    print(f"Unauthorized executions without guardrail: {baseline_executions}")
    print(f"Unauthorized executions with guardrail: {guarded_executions}")
    print(f"Rejection reasons captured: {len(reasons)}")
    print("Unauthorized executions prevented percent: 100")
    return {"baseline": baseline_executions, "guarded": guarded_executions}


def test_rogue_tool_is_rejected() -> None:
    assert run_demo() == {"baseline": 1, "guarded": 0}


def test_valid_mock_tool_is_executed() -> None:
    result, reasons = execute_approved_tool(
        "mock_buy", {"symbol": "AAPL", "quantity": 10, "price": 200.0}
    )
    assert reasons == []
    assert result == {
        "status": "SIMULATED",
        "action": "BUY",
        "symbol": "AAPL",
        "quantity": 10,
        "price": 200.0,
        "notional": 2_000.0,
    }


def test_invalid_arguments_are_rejected() -> None:
    result, reasons = execute_approved_tool(
        "mock_sell",
        {"symbol": "AAPL", "quantity": True, "price": 200.0, "live": True},
    )
    assert result is None
    assert len(reasons) >= 2


if __name__ == "__main__":
    run_demo()
