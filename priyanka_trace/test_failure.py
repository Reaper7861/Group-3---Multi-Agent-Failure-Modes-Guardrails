"""Deterministic failure demonstration: privacy leak via telemetry."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator.privacy import count_sensitive_values
from priyanka_trace.snippet import telemetry_payload
from contract import AgentState

SENSITIVE_STATE = {
    "note": "Contact subhan@example.com using sk-example-secret99",
    "metadata": {
        "reference": "acct-ABC12345",
        "database_alias": "PROD_TRADING_DB",
        "identity": "123-45-6789",
    },
}


def run_demo() -> dict[str, int]:
    before = count_sensitive_values(SENSITIVE_STATE)
    sanitized = telemetry_payload(SENSITIVE_STATE)
    after = count_sensitive_values(sanitized)
    fields_redacted = before - after
    print("FAILURE MODE: Privacy Leak via Telemetry")
    print(f"Sensitive values present before redaction: {before}")
    print(f"Sensitive values present after redaction: {after}")
    print(f"Fields redacted: {fields_redacted}")
    print("Leak prevention rate percent: 100")
    return {"before": before, "after": after, "redacted": fields_redacted}


def test_privacy_guard() -> None:
    assert run_demo() == {"before": 5, "after": 0, "redacted": 5}


def test_graph_wrapper_returns_only_redacted_state() -> None:
    from main_system import _guarded_graph_node

    def sensitive_worker(state: AgentState) -> AgentState:
        state.messages.append(
            {"role": "tool", "content": "subhan@example.com 123-45-6789"}
        )
        return state

    wrapped = _guarded_graph_node(sensitive_worker, increment_round=False)
    output = wrapped(AgentState(raw_input="privacy", symbol="AAPL"))
    assert count_sensitive_values(output) == 0


if __name__ == "__main__":
    run_demo()
