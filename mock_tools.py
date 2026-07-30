"""Side-effect-free tools used by the rogue-tool guardrail demonstration."""

from typing import Any


def mock_buy(*, symbol: str, quantity: int, price: float) -> dict[str, Any]:
    """Return a simulated buy result without placing a real order."""
    return {
        "status": "SIMULATED",
        "action": "BUY",
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "notional": round(quantity * price, 2),
    }


def mock_sell(*, symbol: str, quantity: int, price: float) -> dict[str, Any]:
    """Return a simulated sell result without placing a real order."""
    return {
        "status": "SIMULATED",
        "action": "SELL",
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "notional": round(quantity * price, 2),
    }


def mock_hold(*, symbol: str, quantity: int, price: float) -> dict[str, Any]:
    """Return a simulated hold result."""
    return {
        "status": "SIMULATED",
        "action": "HOLD",
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "notional": 0.0,
    }


MOCK_TOOL_REGISTRY = {
    "mock_buy": mock_buy,
    "mock_sell": mock_sell,
    "mock_hold": mock_hold,
}
