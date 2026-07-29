"""Deterministic failure demonstration: infinite graph loop."""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contract import AgentState
from contract import AnalysisPayload, MarketSnapshot
from chidimma_loop.snippet import guarded_route


def vulnerable_route(state: AgentState) -> str:
    """Deliberately broken Coordinator: always loops back to Analyst."""
    state.round_number += 1
    return "analyst"


def run_demo() -> dict[str, float]:
    vulnerable_state = AgentState(raw_input="loop", symbol="AAPL")
    for _ in range(100):
        assert vulnerable_route(vulnerable_state) == "analyst"
    baseline = vulnerable_state.round_number

    state = AgentState(raw_input="loop", symbol="AAPL")
    route = "analyst"
    while route == "analyst":
        route = guarded_route(state)
    reduction = (baseline - state.round_number) / baseline * 100
    print("FAILURE MODE: Infinite Graph Loop")
    print(f"Baseline vulnerable iterations: {baseline}")
    print(f"Guarded iterations: {state.round_number}")
    print(f"Infinite continuation prevented: {int(route == 'partial_output')}")
    print(f"Reduction percent: {reduction:.1f}")
    return {"baseline": baseline, "guarded": state.round_number, "reduction": reduction}


def test_loop_guard() -> None:
    metrics = run_demo()
    assert metrics["guarded"] == 5
    assert metrics["reduction"] == 95


def test_async_graph_execution(monkeypatch) -> None:
    """The same frozen graph supports asynchronous integration."""
    import main_system

    snapshot = MarketSnapshot(
        symbol="AAPL", price=200.0, open=199.0, high=202.0,
        low=198.0, volume=1_000, change_pct=0.5,
    )

    def deterministic_analyst(state: AgentState) -> AgentState:
        state.analysis_payload = AnalysisPayload(
            symbol="AAPL", action="HOLD", confidence=0.8,
            suggested_quantity=0, rationale="Async test", risk_score=0.2,
        )
        return state

    monkeypatch.setattr(
        main_system,
        "get_market_snapshot",
        lambda symbol: (snapshot, "TEST FIXTURE"),
    )
    monkeypatch.setattr(main_system, "analyst_node", deterministic_analyst)
    result = asyncio.run(main_system.run_orchestrator_async("AAPL", verbose=False))
    assert result.final_report
    assert result.is_validated


if __name__ == "__main__":
    run_demo()
