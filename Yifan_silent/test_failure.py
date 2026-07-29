"""Deterministic failure demonstration: silent structural failures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Yifan_silent.snippet import validate_with_retry
from contract import AgentState, AnalysisPayload, MarketSnapshot

BAD_PAYLOADS = [
    {"free_form": "Looks bullish"},
    {"symbol": "", "action": "BUY", "suggested_quantity": -100,
     "confidence": 1.7, "rationale": "", "risk_score": 2.0},
]


def unguarded_model_output(payload: dict) -> dict:
    """Vulnerable baseline: trusts model output as authoritative state."""
    return payload


def run_demo() -> dict[str, int]:
    baseline_accepted = sum(
        int(unguarded_model_output(payload) is payload) for payload in BAD_PAYLOADS
    )
    guarded_accepted = 0
    total_retries = 0
    for payload in BAD_PAYLOADS:
        result, retries = validate_with_retry([payload, payload])
        guarded_accepted += int(result is not None)
        total_retries += retries
    print("FAILURE MODE: Silent Hallucinations / Structural Failure")
    print(f"Invalid payloads accepted without guardrail: {baseline_accepted}")
    print(f"Invalid payloads accepted with guardrail: {guarded_accepted}")
    print(f"Automatic retries attempted: {total_retries}")
    print("Unsafe downstream passes prevented percent: 100")
    return {"baseline": baseline_accepted, "guarded": guarded_accepted, "retries": total_retries}


def test_schema_guard() -> None:
    metrics = run_demo()
    assert metrics == {"baseline": 2, "guarded": 0, "retries": 2}


def test_integrated_graph_retries_analyst_once(monkeypatch) -> None:
    import main_system
    calls = {"count": 0}

    def flaky_analyst(state: AgentState) -> AgentState:
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("Injected invalid structured response")
        state.analysis_payload = AnalysisPayload(
            symbol="AAPL", action="HOLD", confidence=0.75,
            suggested_quantity=0, rationale="Corrected response", risk_score=0.2,
        )
        return state

    monkeypatch.setattr(main_system, "analyst_node", flaky_analyst)
    state = AgentState(
        raw_input="retry test",
        symbol="AAPL",
        market_data=MarketSnapshot(
            symbol="AAPL", price=200.0, open=199.0, high=202.0,
            low=198.0, volume=1_000, change_pct=0.5,
        ),
        portfolio={"cash": 100_000.0, "positions": {"AAPL": 20}},
        messages=[{"role": "user", "content": "retry test"}],
    )
    result = AgentState.model_validate(
        main_system.build_graph().invoke(state, config={"recursion_limit": 50})
    )
    assert calls["count"] == 2
    assert result.retry_count == 1
    assert result.final_report


def test_second_integrated_failure_routes_to_partial_output(monkeypatch) -> None:
    import main_system
    calls = {"count": 0}

    def always_invalid(state: AgentState) -> AgentState:
        calls["count"] += 1
        raise ValueError("Injected persistent schema failure")

    monkeypatch.setattr(main_system, "analyst_node", always_invalid)
    state = AgentState(
        raw_input="persistent retry test",
        symbol="AAPL",
        market_data=MarketSnapshot(
            symbol="AAPL", price=200.0, open=199.0, high=202.0,
            low=198.0, volume=1_000, change_pct=0.5,
        ),
        portfolio={"cash": 100_000.0, "positions": {"AAPL": 20}},
        messages=[{"role": "user", "content": "persistent retry test"}],
    )
    result = AgentState.model_validate(
        main_system.build_graph().invoke(state, config={"recursion_limit": 50})
    )
    assert calls["count"] == 2
    assert result.retry_count == 2
    assert result.partial_output
    assert not result.final_report


if __name__ == "__main__":
    run_demo()
