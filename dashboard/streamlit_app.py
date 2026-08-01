"""Streamlit dashboard for the guarded financial orchestrator.

This is a presentation layer only. The CLI and orchestration logic remain in
main_system.py and are imported without modification.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path

# Keep repository modules importable from this nested Streamlit entry point.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import streamlit as st

from orchestrator.config import MAX_ROUNDS, SUPPORTED_SYMBOLS
from contract import AgentState
from main_system import run_orchestrator

st.set_page_config(
    page_title="Guarded financial orchestrator",
    page_icon=":material/account_balance:",
    layout="wide",
)

st.session_state.setdefault("analysis_result", None)
st.session_state.setdefault("execution_log", "")
st.session_state.setdefault("market_source", "Not run")


def run_analysis(symbol: str, task: str) -> None:
    """Run one graph invocation and keep its safe result for dashboard reruns."""
    output = io.StringIO()
    with redirect_stdout(output):
        state = run_orchestrator(symbol, task, verbose=True)
    execution_log = output.getvalue()
    source = "Unknown"
    for line in execution_log.splitlines():
        if line.startswith("[MARKET DATA]"):
            source = line.removeprefix("[MARKET DATA]").strip()
            break
    st.session_state.analysis_result = state.model_dump(mode="json")
    st.session_state.execution_log = execution_log
    st.session_state.market_source = source


def current_state() -> AgentState | None:
    raw = st.session_state.get("analysis_result")
    return AgentState.model_validate(raw) if raw else None


def render_header() -> None:
    with st.container(
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
    ):
        st.title(":material/account_balance: Guarded financial orchestrator")
        st.badge("Simulation only", icon=":material/shield:", color="blue")
    st.caption(
        "Multi-agent market analysis with deterministic safety controls. "
        "Educational use only—no real trades or funds are involved."
    )


def render_empty_state() -> None:
    with st.container(border=True, horizontal_alignment="center"):
        st.space("medium")
        st.subheader(":material/query_stats: Ready for analysis")
        st.write(
            "Choose a supported equity and submit a task from the sidebar. "
            "The dashboard will show the complete guarded agent workflow."
        )
        st.caption("NVDA is selected by default for the integration demonstration.")
        st.space("medium")


def render_overview(state: AgentState) -> None:
    analysis = state.analysis_payload
    market = state.market_data
    validation = state.validation_result
    execution = state.execution_state
    if not analysis or not market:
        st.warning("Only partial output is available for this run.", icon=":material/warning:")
        st.code(state.partial_output or "No partial output was generated.")
        return

    action_color = {"BUY": "green", "SELL": "red", "HOLD": "blue"}[analysis.action]
    with st.container(horizontal=True):
        st.metric(
            "Market price",
            f"${market.price:,.2f}",
            f"{market.change_pct:+.2f}%",
            border=True,
        )
        st.metric(
            "Recommendation",
            analysis.action,
            f"{analysis.confidence:.0%} confidence",
            border=True,
        )
        st.metric(
            "Quantity",
            f"{analysis.suggested_quantity} shares",
            "Simulated",
            border=True,
        )
        st.metric(
            "Risk score",
            f"{analysis.risk_score:.2f}",
            "0 = lower risk",
            border=True,
        )

    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True, height="stretch"):
            st.subheader("Recommendation")
            st.markdown(f":{action_color}-badge[{analysis.action}]")
            st.write(analysis.rationale)
            st.caption(
                f"Structured output validated for {analysis.symbol} · "
                f"Market source: {st.session_state.market_source}"
            )
    with right:
        with st.container(border=True, height="stretch"):
            st.subheader("Decision status")
            approved = bool(validation and validation.approved)
            if approved:
                st.success("Risk and compliance approved", icon=":material/check_circle:")
            else:
                st.error("Risk and compliance rejected", icon=":material/block:")
            st.write(f"**Execution:** {execution.status if execution else 'Not executed'}")
            st.write(f"**Simulated:** {'Yes' if execution and execution.simulated else 'No'}")
            st.write(f"**Rounds:** {state.round_number} of {MAX_ROUNDS}")

    prices = pd.DataFrame(
        {
            "Price point": ["Open", "Low", "Current", "High"],
            "Price": [market.open, market.low, market.price, market.high],
        }
    )
    with st.container(border=True):
        st.subheader("Session price snapshot")
        st.bar_chart(prices, x="Price point", y="Price", horizontal=True)


def render_agent_flow(state: AgentState) -> None:
    stages = [
        ("Context manager", True, "Token budget checked before graph execution"),
        ("Market analyst", state.analysis_payload is not None, "Structured recommendation"),
        ("Tool middleware", state.execution_state is not None, "Allowlisted simulation only"),
        ("Risk validator", state.validation_result is not None, "Portfolio constraints"),
        ("Audit reporter", state.final_report is not None, "Final no-real-trade report"),
    ]
    st.subheader("Execution path")
    for index, (name, completed, description) in enumerate(stages, start=1):
        with st.container(border=True):
            cols = st.columns([1, 6], vertical_alignment="center")
            cols[0].metric("Stage", f"{index}")
            with cols[1]:
                status = ":green-badge[Completed]" if completed else ":orange-badge[Not reached]"
                st.markdown(f"**{name}** {status}")
                st.caption(description)

    with st.expander("Raw execution log", icon=":material/terminal:"):
        st.code(st.session_state.execution_log, language="text")


def render_risk(state: AgentState) -> None:
    analysis = state.analysis_payload
    market = state.market_data
    validation = state.validation_result
    if not analysis or not market:
        st.info("Risk metrics require a completed analysis.", icon=":material/info:")
        return

    notional = analysis.suggested_quantity * market.price
    cash = float(state.portfolio.get("cash", 0))
    positions = deepcopy(state.portfolio.get("positions", {}))
    current_shares = int(positions.get(state.symbol, 0))
    projected_shares = current_shares
    if analysis.action == "BUY":
        projected_shares += analysis.suggested_quantity
    elif analysis.action == "SELL":
        projected_shares -= analysis.suggested_quantity

    with st.container(horizontal=True):
        st.metric("Trade notional", f"${notional:,.2f}", "Limit: $10,000", border=True)
        st.metric("Available cash", f"${cash:,.2f}", border=True)
        st.metric("Current shares", current_shares, border=True)
        st.metric("Projected shares", projected_shares, border=True)

    with st.container(border=True):
        st.subheader("Validation result")
        if validation and validation.approved:
            st.success("All deterministic portfolio checks passed.", icon=":material/verified:")
        else:
            st.error("The simulation was rejected.", icon=":material/block:")
        reasons = validation.reasons if validation else ["Validation did not run"]
        if reasons:
            for reason in reasons:
                st.write(f"- {reason}")
        else:
            st.caption("No rejection reasons.")

    portfolio_rows = [
        {"Symbol": symbol, "Shares": quantity, "Selected symbol": symbol == state.symbol}
        for symbol, quantity in positions.items()
    ]
    st.subheader("Simulated portfolio")
    st.dataframe(
        pd.DataFrame(portfolio_rows),
        hide_index=True,
        column_config={
            "Shares": st.column_config.NumberColumn(format="%d"),
            "Selected symbol": st.column_config.CheckboxColumn(),
        },
    )


def render_guardrails(state: AgentState) -> None:
    events = [
        {"Order": index, "Guardrail event": event, "Status": "Triggered"}
        for index, event in enumerate(state.guardrail_events, start=1)
    ]
    with st.container(horizontal=True):
        st.metric("Events recorded", len(events), border=True)
        st.metric("Rounds prevented", MAX_ROUNDS - state.round_number, border=True)
        st.metric("Real trades", 0, border=True)
        st.metric("Contained errors", len(state.error_log), border=True)

    st.subheader("Active safeguards")
    st.dataframe(
        pd.DataFrame(events),
        hide_index=True,
        column_config={
            "Order": st.column_config.NumberColumn(width="small"),
            "Guardrail event": st.column_config.TextColumn(width="large"),
            "Status": st.column_config.TextColumn(width="small"),
        },
    )

    if state.error_log:
        with st.expander("Contained errors", icon=":material/warning:"):
            for error in state.error_log:
                st.warning(error)

    with st.container(border=True):
        st.subheader("Six demonstrated failure modes")
        st.markdown(
            """
            1. Infinite graph loops → bounded rounds and partial output  
            2. Silent structural failures → Pydantic validation and one retry  
            3. Rogue tool execution → strict tool allowlist and argument checks  
            4. Downstream cascades → boundary validation before arithmetic  
            5. Telemetry privacy leaks → recursive redaction before tracing  
            6. Context explosion → token estimation and history compaction
            """
        )


def render_audit(state: AgentState) -> None:
    report = state.final_report or state.partial_output or "No report available."
    with st.container(border=True):
        st.subheader("Audit report")
        st.code(report, language="text")
    st.download_button(
        "Download audit report",
        data=report,
        file_name=f"{state.symbol.lower()}_guarded_analysis.txt",
        mime="text/plain",
        icon=":material/download:",
    )
    with st.expander("Validated shared state", icon=":material/data_object:"):
        st.json(state.model_dump(mode="json"))


render_header()

with st.sidebar:
    st.subheader(":material/tune: Analysis controls")
    with st.form("analysis_form"):
        selected_symbol = st.selectbox(
            "Equity symbol",
            options=sorted(SUPPORTED_SYMBOLS),
            index=sorted(SUPPORTED_SYMBOLS).index("NVDA"),
        )
        task = st.text_area(
            "Analysis task",
            value="Analyze current conditions and determine whether a simulated BUY, SELL, or HOLD is appropriate.",
            height=120,
        )
        submitted = st.form_submit_button(
            "Run guarded analysis",
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
        )
    st.caption("One symbol and one simulated decision per run.")
    st.markdown(":blue-badge[No real trading] :green-badge[Guardrails active]")
    if st.button("Clear dashboard", icon=":material/restart_alt:", width="stretch"):
        st.session_state.analysis_result = None
        st.session_state.execution_log = ""
        st.session_state.market_source = "Not run"
        st.rerun()

if submitted:
    if not task.strip():
        st.error("Enter an analysis task.", icon=":material/error:")
    else:
        try:
            with st.spinner(f"Running guarded analysis for {selected_symbol}..."):
                run_analysis(selected_symbol, task.strip())
            st.toast("Analysis completed safely", icon=":material/check_circle:")
        except Exception as exc:
            st.error(
                f"The dashboard could not complete the analysis: {type(exc).__name__}",
                icon=":material/error:",
            )

state = current_state()
if state is None:
    render_empty_state()
else:
    st.caption(
        f"Latest run · {state.symbol} · market data: {st.session_state.market_source} · "
        f"{state.round_number}/{MAX_ROUNDS} graph rounds"
    )
    overview_tab, flow_tab, risk_tab, guardrails_tab, audit_tab = st.tabs(
        [
            ":material/monitoring: Overview",
            ":material/account_tree: Agent flow",
            ":material/policy: Risk",
            ":material/shield: Guardrails",
            ":material/description: Audit",
        ]
    )
    with overview_tab:
        render_overview(state)
    with flow_tab:
        render_agent_flow(state)
    with risk_tab:
        render_risk(state)
    with guardrails_tab:
        render_guardrails(state)
    with audit_tab:
        render_audit(state)
