"""Deterministic context budgeting with recent-history preservation."""

import json
import re
from typing import Any

from orchestrator.config import MAX_CONTEXT_TOKENS


def count_tokens(messages: list[dict[str, Any]]) -> int:
    """Deterministic fallback approximation: words, punctuation, and JSON syntax."""
    serialized = json.dumps(messages, ensure_ascii=False, default=str)
    return len(re.findall(r"\w+|[^\w\s]", serialized))


def manage_context(
    messages: list[dict[str, Any]], max_tokens: int = MAX_CONTEXT_TOKENS
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    before = count_tokens(messages)
    if before <= max_tokens:
        return list(messages), {"tokens_before": before, "tokens_after": before}
    recent = list(messages[-12:])
    old = messages[:-12]
    summary = {
        "role": "system",
        "content": f"Earlier history summarized: {len(old)} messages; "
        f"roles={sorted({str(item.get('role', 'unknown')) for item in old})}.",
    }
    compact = [summary, *recent]
    while count_tokens(compact) > max_tokens and len(compact) > 2:
        compact.pop(1)
    return compact, {
        "tokens_before": before,
        "tokens_after": count_tokens(compact),
    }
