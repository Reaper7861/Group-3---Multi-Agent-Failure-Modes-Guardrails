"""Rogue-tool guard: validate requests before invoking approved mock tools."""

from __future__ import annotations

from typing import Any

from config import MAX_QUANTITY, MAX_TRADE_NOTIONAL, SUPPORTED_SYMBOLS
from mock_tools import MOCK_TOOL_REGISTRY

REQUIRED_ARGUMENTS = frozenset({"symbol", "quantity", "price"})


def execute_approved_tool(
    tool_name: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any] | None, list[str]]:
    """Fail closed unless the tool and all arguments satisfy the policy."""
    reasons: list[str] = []

    if tool_name not in MOCK_TOOL_REGISTRY:
        return None, [f"Tool is not approved: {tool_name}"]

    if set(arguments) != REQUIRED_ARGUMENTS:
        reasons.append("Arguments must be exactly: price, quantity, symbol")

    symbol = arguments.get("symbol")
    quantity = arguments.get("quantity")
    price = arguments.get("price")

    if not isinstance(symbol, str) or symbol not in SUPPORTED_SYMBOLS:
        reasons.append("Symbol is not supported")
    if type(quantity) is not int or not 0 <= quantity <= MAX_QUANTITY:
        reasons.append(f"Quantity must be an integer from 0 to {MAX_QUANTITY}")
    if type(price) not in (int, float) or isinstance(price, bool) or price <= 0:
        reasons.append("Price must be a positive number")

    expected_tool = {
        "mock_buy": "BUY",
        "mock_sell": "SELL",
        "mock_hold": "HOLD",
    }[tool_name]
    if expected_tool == "HOLD" and quantity != 0:
        reasons.append("HOLD requests must have quantity 0")

    if (
        type(quantity) is int
        and type(price) in (int, float)
        and not isinstance(price, bool)
        and quantity * price > MAX_TRADE_NOTIONAL
    ):
        reasons.append(
            f"Trade notional cannot exceed ${MAX_TRADE_NOTIONAL:,.2f}"
        )

    if reasons:
        return None, reasons

    result = MOCK_TOOL_REGISTRY[tool_name](
        symbol=symbol, quantity=quantity, price=float(price)
    )
    return result, []
