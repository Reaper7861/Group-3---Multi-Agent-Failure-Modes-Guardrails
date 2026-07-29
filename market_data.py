"""Twelve Data adapter with explicit, visible fallback behavior."""

import json
import os
from pathlib import Path

import requests

from config import SUPPORTED_SYMBOLS
from contract import MarketSnapshot

FIXTURE_PATH = Path(__file__).with_name("demo_market_data.json")


class MarketDataError(RuntimeError):
    pass


def _fixture(symbol: str) -> MarketSnapshot:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw = fixtures.get(symbol)
    if raw is None:
        base = 100.0 + sum(map(ord, symbol)) % 300
        raw = {
            "symbol": symbol, "price": base, "open": base * 0.99,
            "high": base * 1.02, "low": base * 0.98,
            "volume": 1_000_000, "change_pct": 1.01,
        }
    return MarketSnapshot.model_validate(raw)


def get_market_snapshot(symbol: str) -> tuple[MarketSnapshot, str]:
    symbol = symbol.strip().upper()
    if symbol not in SUPPORTED_SYMBOLS:
        raise MarketDataError(f"Unsupported symbol: {symbol}")
    api_key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not api_key:
        return _fixture(symbol), "FALLBACK FIXTURE"
    try:
        response = requests.get(
            "https://api.twelvedata.com/quote",
            params={"symbol": symbol, "apikey": api_key},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "error":
            raise MarketDataError(data.get("message", "Twelve Data error"))
        snapshot = MarketSnapshot(
            symbol=symbol,
            price=float(data["close"]),
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            volume=int(float(data.get("volume", 0))),
            change_pct=float(data.get("percent_change", 0)),
        )
        return snapshot, "LIVE"
    except (requests.RequestException, KeyError, TypeError, ValueError, MarketDataError):
        return _fixture(symbol), "FALLBACK FIXTURE"
