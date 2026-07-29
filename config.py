"""Central configuration: symbols and deterministic safety limits."""

SUPPORTED_SYMBOLS = frozenset(
    {
        "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "AMD", "INTC",
        "ORCL", "CRM", "JPM", "BAC", "GS", "MS", "V", "MA", "WMT",
        "COST", "HD", "MCD", "NKE", "JNJ", "UNH", "PFE", "ABBV", "CAT",
        "BA", "XOM", "CVX", "GE",
    }
)

MAX_ROUNDS = 5
MAX_RETRIES = 1
MAX_QUANTITY = 100
MAX_TRADE_NOTIONAL = 10_000.0
MAX_CONCENTRATION = 0.20
MAX_CONTEXT_TOKENS = 2_000
MODEL_NAME = "gemini-flash-latest"

DEFAULT_PORTFOLIO = {
    "cash": 100_000.0,
    "positions": {"AAPL": 20, "MSFT": 10, "NVDA": 5},
}
