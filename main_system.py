"""CLI and integrated guarded financial multi-agent orchestrator.

All trade execution is an in-memory simulation. Critical routing and safety
decisions are deterministic Python and never delegated to a model.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Callable

from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()

from orchestrator.config import (
    DEFAULT_PORTFOLIO,
    MAX_CONCENTRATION,
    MAX_QUANTITY,
    MAX_RETRIES,
    MAX_ROUNDS,
    MAX_TRADE_NOTIONAL,
    MODEL_NAME,
    SUPPORTED_SYMBOLS,
)
from orchestrator.context_manager import manage_context
from contract import (
    AgentState,
    AnalysisPayload,
    ToolRequest,
    ValidationResult,
)
from orchestrator.market_data import MarketDataError, get_market_snapshot
from orchestrator.mock_tools import InvalidToolCallException, execute_tool
from orchestrator.privacy import redact_for_telemetry


def route_from_coordinator(state: AgentState) -> str:
    if state.final_report is not None:
        return "end"
    if state.rejection_flag:
        return "error_handler"
    if state.error_log and state.retry_count > MAX_RETRIES:
        return "error_handler"
    if state.round_number >= MAX_ROUNDS:
        return "partial_output"
    if state.analysis_payload is None:
        return "analyst"
    if "Schema guard accepted structured analysis" not in state.guardrail_events:
        return "schema_guard"
    if state.execution_state is None:
        return "actor"
    if "Cascade guard accepted execution state" not in state.guardrail_events:
        return "cascade_guard"
    if not state.is_validated:
        return "validator"
    if state.final_report is None:
        return "reporter"
    return "end"


def _fallback_analysis(state: AgentState) -> AnalysisPayload:
    snapshot = state.market_data
    if snapshot is None:
        raise ValueError("Market snapshot is required")
    if snapshot.change_pct > 1:
        action, confidence, quantity = "BUY", 0.68, 10
    elif snapshot.change_pct < -1:
        action, confidence, quantity = "SELL", 0.64, 5
    else:
        action, confidence, quantity = "HOLD", 0.62, 0
    return AnalysisPayload(
        symbol=state.symbol,
        action=action,
        confidence=confidence,
        suggested_quantity=quantity,
        rationale=(
            f"Deterministic demo analysis based on a {snapshot.change_pct:.2f}% "
            "price change; provider-independent fallback."
        ),
        risk_score=min(1.0, abs(snapshot.change_pct) / 10 + 0.25),
    )


def analyst_node(state: AgentState) -> AgentState:
    """Use Gemini structured output when configured, otherwise safe fallback."""
    analysis: AnalysisPayload
    if os.getenv("GOOGLE_API_KEY"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)
            structured = model.with_structured_output(AnalysisPayload)
            prompt = json.dumps(
                {
                    "symbol": state.symbol,
                    "task": state.raw_input,
                    "market_data": state.market_data.model_dump() if state.market_data else None,
                    "portfolio": state.portfolio,
                    "retry_feedback": state.error_log[-1] if state.retry_count else None,
                    "instruction": "Return a conservative simulated BUY, SELL, or HOLD analysis.",
                },
                default=str,
            )
            analysis = structured.invoke(prompt)
        except Exception as exc:
            error_text = str(exc)
            configured_key = os.getenv("GOOGLE_API_KEY", "")
            if configured_key:
                error_text = error_text.replace(configured_key, "[REDACTED_SECRET]")
            error_text = str(redact_for_telemetry(error_text)).replace("\n", " ")[:500]
            state.error_log.append(
                f"Gemini unavailable; deterministic fallback used: "
                f"{type(exc).__name__}: {error_text}"
            )
            state.guardrail_events.append("LLM provider failure contained")
            analysis = _fallback_analysis(state)
    else:
        analysis = _fallback_analysis(state)
    state.analysis_payload = AnalysisPayload.model_validate(analysis)
    return state


def schema_guard_node(state: AgentState) -> AgentState:
    """Explicit Worker A boundary with one self-correcting retry."""
    if state.analysis_payload is None:
        raise ValueError("Schema guard requires an analysis payload")
    try:
        state.analysis_payload = AnalysisPayload.model_validate(
            state.analysis_payload.model_dump()
        )
    except ValidationError:
        state.analysis_payload = None
        raise
    state.guardrail_events.append("Schema guard accepted structured analysis")
    return state


def actor_node(state: AgentState) -> AgentState:
    analysis = state.analysis_payload
    snapshot = state.market_data
    if analysis is None or snapshot is None:
        raise ValueError("Actor requires validated analysis and market data")
    tool_name = f"mock_{analysis.action.lower()}"
    arguments: dict[str, object] = {"symbol": state.symbol}
    if analysis.action != "HOLD":
        arguments.update(
            quantity=analysis.suggested_quantity,
            price=float(snapshot.price),
        )
    state.requested_tool = ToolRequest(tool_name=tool_name, arguments=arguments)
    try:
        state.execution_state = execute_tool(state.requested_tool)
        state.guardrail_events.append(f"Tool guard approved {tool_name}")
    except InvalidToolCallException as exc:
        state.rejection_flag = True
        state.error_log.append(f"Tool guard blocked request: {exc}")
        state.guardrail_events.append("Rogue tool execution prevented")
    return state


def cascade_guard_node(state: AgentState) -> AgentState:
    """Validate Worker B output before Worker C performs any arithmetic."""
    reasons: list[str] = []
    execution = state.execution_state
    analysis = state.analysis_payload
    if execution is None or analysis is None:
        reasons.append("Cascade guard requires analysis and execution state")
    else:
        details = execution.details
        if execution.simulated is not True or execution.status != "SIMULATED":
            reasons.append("Only simulated execution state is permitted")
        if details.get("symbol") != state.symbol:
            reasons.append("Execution symbol does not match shared state")
        if details.get("action") != analysis.action:
            reasons.append("Execution action does not match analysis")
        if analysis.action in {"BUY", "SELL"}:
            quantity = details.get("quantity")
            price = details.get("price")
            if type(quantity) is not int:
                reasons.append("Execution quantity must be an integer")
            if type(price) is not float or price <= 0:
                reasons.append("Execution price must be a positive float")
        elif set(details) != {"action", "symbol"}:
            reasons.append("HOLD execution contains unexpected arguments")

    if reasons:
        state.rejection_flag = True
        state.validation_result = ValidationResult(
            approved=False,
            reasons=reasons,
            rollback_required=True,
        )
        state.error_log.append(f"Cascade guard rejected state: {'; '.join(reasons)}")
        state.guardrail_events.append("Cascade guard rejected malformed execution state")
    else:
        state.guardrail_events.append("Cascade guard accepted execution state")
    return state


def validator_node(state: AgentState) -> AgentState:
    reasons: list[str] = []
    analysis = state.analysis_payload
    snapshot = state.market_data
    execution = state.execution_state
    if not all((analysis, snapshot, execution)):
        reasons.append("Required upstream state is missing")
    else:
        quantity = analysis.suggested_quantity
        price = snapshot.price
        if state.symbol not in SUPPORTED_SYMBOLS:
            reasons.append("Unsupported symbol")
        if type(quantity) is not int or not 0 <= quantity <= MAX_QUANTITY:
            reasons.append("Quantity outside allowed integer bounds")
        if analysis.action == "HOLD" and quantity != 0:
            reasons.append("HOLD must have zero quantity")
        if analysis.action != "HOLD" and quantity <= 0:
            reasons.append("BUY/SELL requires positive quantity")
        notional = quantity * price
        if notional > MAX_TRADE_NOTIONAL:
            reasons.append("Trade notional exceeds $10,000")
        cash = float(state.portfolio.get("cash", 0))
        if analysis.action == "BUY" and notional > cash:
            reasons.append("Insufficient simulated cash")
        positions = state.portfolio.get("positions", {})
        current_value = sum(
            float(qty) * (price if symbol == state.symbol else 100.0)
            for symbol, qty in positions.items()
        )
        total_value = cash + current_value
        post_shares = float(positions.get(state.symbol, 0))
        if analysis.action == "BUY":
            post_shares += quantity
        elif analysis.action == "SELL":
            post_shares -= quantity
            if post_shares < 0:
                reasons.append("Cannot sell more shares than simulated holdings")
        post_concentration = (max(0, post_shares) * price / total_value) if total_value else 1.0
        if post_concentration > MAX_CONCENTRATION:
            reasons.append("Post-trade concentration exceeds 20%")
    state.is_validated = not reasons
    state.rejection_flag = bool(reasons)
    state.validation_result = ValidationResult(
        approved=not reasons,
        reasons=reasons,
        rollback_required=bool(reasons),
    )
    state.guardrail_events.append(
        "Risk validator approved simulation" if not reasons else "Cascade validator rejected malformed/unsafe state"
    )
    return state


def reporter_node(state: AgentState) -> AgentState:
    analysis = state.analysis_payload
    snapshot = state.market_data
    validation = state.validation_result
    state.final_report = "\n".join(
        [
            "SIMULATED FINANCIAL ANALYSIS — NOT INVESTMENT ADVICE",
            f"Symbol: {state.symbol}",
            f"Market price: ${snapshot.price:,.2f}" if snapshot else "Market price: unavailable",
            f"Recommendation: {analysis.action}" if analysis else "Recommendation: unavailable",
            f"Confidence: {analysis.confidence:.0%}" if analysis else "Confidence: unavailable",
            f"Quantity: {analysis.suggested_quantity}" if analysis else "Quantity: unavailable",
            f"Execution status: {state.execution_state.status if state.execution_state else 'NOT EXECUTED'}",
            f"Risk result: {'APPROVED' if validation and validation.approved else 'REJECTED'}",
            f"Risk reasons: {', '.join(validation.reasons) if validation and validation.reasons else 'None'}",
            f"Contained errors: {'; '.join(state.error_log) if state.error_log else 'None'}",
            f"Guardrails: {'; '.join(state.guardrail_events)}",
            "FINAL STATUS: No real trade occurred; all actions were simulated.",
        ]
    )
    return state


def partial_output_node(state: AgentState) -> AgentState:
    completed = [
        name for name, value in (
            ("market data", state.market_data),
            ("analysis", state.analysis_payload),
            ("simulated execution", state.execution_state),
            ("risk validation", state.validation_result),
        ) if value is not None
    ]
    state.partial_output = (
        f"SAFE PARTIAL OUTPUT\nSucceeded: {', '.join(completed) or 'initialization'}\n"
        f"Failed: {'; '.join(state.error_log) or 'maximum rounds reached'}\n"
        "No real trade occurred; all actions were simulated."
    )
    return state


def error_handler_node(state: AgentState) -> AgentState:
    state.guardrail_events.append("Error handler terminated flow safely")
    return partial_output_node(state)


def _safe_telemetry_payload(state: AgentState) -> dict:
    """Only this sanitized payload may be handed to an external tracer."""
    return redact_for_telemetry(state)


def _guarded_graph_node(
    worker: Callable[[AgentState], AgentState],
    *,
    increment_round: bool,
) -> Callable[[AgentState], dict]:
    """Adapt a worker to LangGraph and contain recoverable node failures."""
    def run(state: AgentState) -> dict:
        if increment_round:
            state.round_number += 1
        try:
            updated = worker(state)
        except Exception as exc:
            error_text = str(redact_for_telemetry(str(exc))).replace("\n", " ")[:500]
            state.error_log.append(
                f"{worker.__name__} failed: {type(exc).__name__}: {error_text}"
            )
            state.retry_count += 1
            state.guardrail_events.append(f"{worker.__name__} failure captured")
            updated = state
        if updated.rejection_flag:
            if "Validation rejected unsafe state" not in updated.error_log:
                updated.error_log.append("Validation rejected unsafe state")
        return AgentState.model_validate(_safe_telemetry_payload(updated)).model_dump()

    return run


def _context_transition_node(verbose: bool) -> Callable[[AgentState], dict]:
    """Run Student 6's token guard before every Coordinator transition."""
    def run(state: AgentState) -> dict:
        state.messages, metrics = manage_context(state.messages)
        state.guardrail_events.append(
            f"Context guard: {metrics['tokens_before']} -> {metrics['tokens_after']} tokens"
        )
        if verbose:
            print(
                f"[CONTEXT] {metrics['tokens_before']} -> "
                f"{metrics['tokens_after']} estimated tokens"
            )
        return AgentState.model_validate(_safe_telemetry_payload(state)).model_dump()

    return run


def build_graph(verbose: bool = False):
    """Compile the dynamic workflow with LangGraph conditional edges."""
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(AgentState)
    graph.add_node("context_manager", _context_transition_node(verbose))
    graph.add_node("coordinator", lambda state: {})
    graph.add_node("analyst", _guarded_graph_node(analyst_node, increment_round=True))
    graph.add_node(
        "schema_guard", _guarded_graph_node(schema_guard_node, increment_round=False)
    )
    graph.add_node("actor", _guarded_graph_node(actor_node, increment_round=True))
    graph.add_node(
        "cascade_guard", _guarded_graph_node(cascade_guard_node, increment_round=False)
    )
    graph.add_node("validator", _guarded_graph_node(validator_node, increment_round=True))
    graph.add_node("reporter", _guarded_graph_node(reporter_node, increment_round=True))
    graph.add_node(
        "error_handler",
        lambda state: AgentState.model_validate(
            _safe_telemetry_payload(error_handler_node(state))
        ).model_dump(),
    )
    graph.add_node(
        "partial_output",
        lambda state: AgentState.model_validate(
            _safe_telemetry_payload(partial_output_node(state))
        ).model_dump(),
    )
    graph.add_edge(START, "context_manager")
    graph.add_edge("context_manager", "coordinator")

    def logged_route(state: AgentState) -> str:
        route = route_from_coordinator(state)
        if verbose:
            print(f"[COORDINATOR] routing -> {route}")
        return route

    graph.add_conditional_edges(
        "coordinator",
        logged_route,
        {
            "analyst": "analyst",
            "schema_guard": "schema_guard",
            "actor": "actor",
            "cascade_guard": "cascade_guard",
            "validator": "validator",
            "reporter": "reporter",
            "error_handler": "error_handler",
            "partial_output": "partial_output",
            "end": END,
        },
    )
    for node in (
        "analyst",
        "schema_guard",
        "actor",
        "cascade_guard",
        "validator",
        "reporter",
    ):
        graph.add_edge(node, "context_manager")
    graph.add_edge("error_handler", END)
    graph.add_edge("partial_output", END)
    return graph.compile()


def _initialize_state(symbol: str, task: str | None) -> tuple[AgentState, str]:
    symbol = symbol.strip().upper()
    if symbol not in SUPPORTED_SYMBOLS:
        raise ValueError(f"Choose a supported symbol: {', '.join(sorted(SUPPORTED_SYMBOLS))}")
    snapshot, source = get_market_snapshot(symbol)
    return AgentState(
        raw_input=task or f"Analyze {symbol} and decide whether to BUY, SELL, or HOLD.",
        symbol=symbol,
        market_data=snapshot,
        portfolio=deepcopy(DEFAULT_PORTFOLIO),
        messages=[{"role": "user", "content": task or f"Analyze {symbol}"}],
    ), source


def _prepare_graph_input(state: AgentState) -> AgentState:
    """Apply the privacy boundary before automatic LangSmith tracing begins."""
    return AgentState.model_validate(redact_for_telemetry(state))


def _render_result(state: AgentState, verbose: bool) -> AgentState:
    if verbose:
        print(state.final_report or state.partial_output)
        print("[END] clean termination")
    return state


def run_orchestrator(symbol: str, task: str | None = None, verbose: bool = True) -> AgentState:
    state, source = _initialize_state(symbol, task)
    if verbose:
        print(f"[MARKET DATA] {source}")
    result = build_graph(verbose=verbose).invoke(
        _prepare_graph_input(state),
        config={"recursion_limit": 50},
    )
    state = AgentState.model_validate(result)
    return _render_result(state, verbose)


async def run_orchestrator_async(
    symbol: str,
    task: str | None = None,
    verbose: bool = True,
) -> AgentState:
    """Asynchronous equivalent for concurrent applications and services."""
    import asyncio

    normalized = symbol.strip().upper()
    if normalized not in SUPPORTED_SYMBOLS:
        raise ValueError(f"Choose a supported symbol: {', '.join(sorted(SUPPORTED_SYMBOLS))}")
    snapshot, source = await asyncio.to_thread(get_market_snapshot, normalized)
    state = AgentState(
        raw_input=task or f"Analyze {normalized} and decide whether to BUY, SELL, or HOLD.",
        symbol=normalized,
        market_data=snapshot,
        portfolio=deepcopy(DEFAULT_PORTFOLIO),
        messages=[{"role": "user", "content": task or f"Analyze {normalized}"}],
    )
    if verbose:
        print(f"[MARKET DATA] {source}")
    result = await build_graph(verbose=verbose).ainvoke(
        _prepare_graph_input(state),
        config={"recursion_limit": 50},
    )
    return _render_result(AgentState.model_validate(result), verbose)


def run_integration_demo() -> None:
    state = run_orchestrator("NVDA")
    print("\nGUARDRAIL METRICS")
    print(f"Rounds used: {state.round_number}/{MAX_ROUNDS}")
    print(f"Guardrail events: {len(state.guardrail_events)}")
    print(f"Real trades executed: 0")


def main() -> None:
    print("=" * 60)
    print("GUARDED MULTI-AGENT FINANCIAL TRADING ORCHESTRATOR")
    print("=" * 60)
    print("1. Run normal analysis\n2. Run full integration demonstration\n3. Exit")
    choice = input("Select option [1]: ").strip() or "1"
    if choice == "3":
        return
    if choice == "2":
        run_integration_demo()
        return
    symbol = input("Enter symbol [NVDA]: ").strip().upper() or "NVDA"
    task = input("Enter task [default analysis]: ").strip() or None
    try:
        run_orchestrator(symbol, task)
    except (ValueError, MarketDataError) as exc:
        print(f"Input error: {exc}")


if __name__ == "__main__":
    main()
