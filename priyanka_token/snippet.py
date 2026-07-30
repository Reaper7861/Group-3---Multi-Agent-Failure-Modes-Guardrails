"""Token-aware context compaction."""

from typing import Any

from orchestrator.config import MAX_CONTEXT_TOKENS
from orchestrator.context_manager import manage_context


def compact(messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    return manage_context(messages, MAX_CONTEXT_TOKENS)
