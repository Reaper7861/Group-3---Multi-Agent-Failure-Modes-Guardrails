"""Deterministic failure demonstration: context/token explosion."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from student_6_tokens.snippet import compact
from contract import AgentState, AnalysisPayload, MarketSnapshot


def run_demo() -> dict[str, int]:
    messages = [
        {"role": "tool" if index % 3 == 0 else "assistant",
         "content": ("redundant market analysis and verbose tool output " * 18) + str(index)}
        for index in range(120)
    ]
    after_messages, metrics = compact(messages)
    core_preserved = int(bool(after_messages) and "119" in str(after_messages))
    reduction = 100 * (metrics["tokens_before"] - metrics["tokens_after"]) / metrics["tokens_before"]
    print("FAILURE MODE: Context Window Explosion / Token Burn")
    print(f"Messages before: {len(messages)}")
    print(f"Messages after: {len(after_messages)}")
    print(f"Tokens before: {metrics['tokens_before']}")
    print(f"Tokens after: {metrics['tokens_after']}")
    print(f"Reduction percent: {reduction:.1f}")
    print(f"Core state preserved: {core_preserved}")
    return {
        "before": metrics["tokens_before"],
        "after": metrics["tokens_after"],
        "core": core_preserved,
    }


def test_context_guard() -> None:
    metrics = run_demo()
    assert metrics["after"] <= 2_000
    assert metrics["after"] < metrics["before"]
    assert metrics["core"] == 1


def test_context_guard_runs_before_every_transition(monkeypatch) -> None:
    import main_system

    def deterministic_analyst(state: AgentState) -> AgentState:
        state.analysis_payload = AnalysisPayload(
            symbol="AAPL", action="HOLD", confidence=0.8,
            suggested_quantity=0, rationale="Context test", risk_score=0.2,
        )
        return state

    monkeypatch.setattr(main_system, "analyst_node", deterministic_analyst)
    state = AgentState(
        raw_input="context transition test",
        symbol="AAPL",
        market_data=MarketSnapshot(
            symbol="AAPL", price=200.0, open=199.0, high=202.0,
            low=198.0, volume=1_000, change_pct=0.5,
        ),
        portfolio={"cash": 100_000.0, "positions": {"AAPL": 20}},
        messages=[{"role": "user", "content": "context transition test"}],
    )
    result = AgentState.model_validate(
        main_system.build_graph().invoke(state, config={"recursion_limit": 50})
    )
    context_events = [
        event for event in result.guardrail_events if event.startswith("Context guard:")
    ]
    assert len(context_events) == 7


if __name__ == "__main__":
    run_demo()
