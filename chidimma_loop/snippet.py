"""Deterministic graph-loop guard."""

from orchestrator.config import MAX_ROUNDS
from contract import AgentState


def guarded_route(state: AgentState) -> str:
    state.round_number += 1
    if state.round_number >= MAX_ROUNDS:
        state.guardrail_events.append("Loop guard routed to partial output")
        return "partial_output"
    return "analyst"
