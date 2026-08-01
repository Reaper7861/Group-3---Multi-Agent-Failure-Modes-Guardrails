"""Allowlisted, in-memory financial simulation tools."""

from typing import Any

from contract import ExecutionState, ToolRequest


class InvalidToolCallException(Exception):
    pass


TOOL_PERMISSIONS: dict[str, dict[str, type]] = {
    "mock_buy": {"symbol": str, "quantity": int, "price": float},
    "mock_sell": {"symbol": str, "quantity": int, "price": float},
    "mock_hold": {"symbol": str},
    "mock_get_quote": {"symbol": str},
}


def _validate(request: ToolRequest) -> None:
    schema = TOOL_PERMISSIONS.get(request.tool_name)
    if schema is None:
        raise InvalidToolCallException(f"Tool is not allowlisted: {request.tool_name}")
    if set(request.arguments) != set(schema):
        raise InvalidToolCallException("Tool argument names do not match the contract")
    for name, expected in schema.items():
        value = request.arguments[name]
        if type(value) is not expected:
            raise InvalidToolCallException(f"{name} must be {expected.__name__}")
    quantity = request.arguments.get("quantity", 0)
    price = request.arguments.get("price", 0.0)
    if quantity < 0 or quantity > 100:
        raise InvalidToolCallException("Quantity outside 0..100")
    if quantity * price > 10_000:
        raise InvalidToolCallException("Trade notional exceeds $10,000")


def execute_tool(request: ToolRequest) -> ExecutionState:
    _validate(request)
    details: dict[str, Any] = {"action": request.tool_name.removeprefix("mock_").upper()}
    details.update(request.arguments)
    return ExecutionState(
        status="SIMULATED",
        simulated=True,
        tool_name=request.tool_name,
        details=details,
    )
