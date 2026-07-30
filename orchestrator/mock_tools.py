"""Side-effect-free tools used by the rogue-tool guardrail demonstration."""

from typing import Any

from contract import ExecutionState, ToolRequest


class InvalidToolCallException(Exception):
    """Raised when a requested tool violates the deterministic permission policy."""


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

TOOL_PERMISSIONS: dict[str, dict[str, type]] = {
    "mock_buy": {"symbol": str, "quantity": int, "price": float},
    "mock_sell": {"symbol": str, "quantity": int, "price": float},
    "mock_hold": {"symbol": str},
}


def _validate_request(request: ToolRequest) -> None:
    schema = TOOL_PERMISSIONS.get(request.tool_name)
    if schema is None:
        raise InvalidToolCallException(f"Tool is not allowlisted: {request.tool_name}")
    if set(request.arguments) != set(schema):
        raise InvalidToolCallException("Tool argument names do not match the contract")
    for name, expected_type in schema.items():
        if type(request.arguments[name]) is not expected_type:
            raise InvalidToolCallException(f"{name} must be {expected_type.__name__}")

    quantity = request.arguments.get("quantity", 0)
    price = request.arguments.get("price", 0.0)
    if quantity < 0 or quantity > 100:
        raise InvalidToolCallException("Quantity outside 0..100")
    if quantity * price > 10_000:
        raise InvalidToolCallException("Trade notional exceeds $10,000")


def execute_tool(request: ToolRequest) -> ExecutionState:
    """Validate and execute only an in-memory mock financial tool."""
    _validate_request(request)
    action = request.tool_name.removeprefix("mock_").upper()
    details: dict[str, Any] = {"action": action, **request.arguments}
    if request.tool_name == "mock_hold":
        mock_hold(symbol=request.arguments["symbol"], quantity=0, price=0.0)
    else:
        MOCK_TOOL_REGISTRY[request.tool_name](**request.arguments)
    return ExecutionState(
        status="SIMULATED",
        simulated=True,
        tool_name=request.tool_name,
        details=details,
    )
