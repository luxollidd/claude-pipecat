"""
Thin wrapper around the Anthropic SDK for simple single-turn calls.
Used by topics/engine.py for proactive interjection generation.
"""
from __future__ import annotations

import anthropic
from cgshared.config.settings import get_anthropic_key, CLAUDE_MODEL


def chat(
    messages: list[dict],
    system: str = "",
    max_tokens: int = 300,
    model: str | None = None,
) -> str:
    """
    Send a single-turn (or short multi-turn) chat to Claude and return the
    text response as a plain string.
    """
    client = anthropic.Anthropic(api_key=get_anthropic_key())
    kwargs: dict = dict(
        model=model or CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=messages,
    )
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    # Extract first text block
    for block in response.content:
        if hasattr(block, "text"):
            return block.text.strip()
    return ""
