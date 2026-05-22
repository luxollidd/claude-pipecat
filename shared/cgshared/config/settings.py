"""
Config loader for the cgshared package.
Reads a .env file and exposes typed getters.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_env(env_path: str | Path | None = None) -> None:
    """
    Minimal .env loader — reads KEY=VALUE lines into os.environ.
    Skips comments and blank lines. Does NOT override existing env vars.
    """
    path = Path(env_path) if env_path else None

    # fallback: look for config/.env relative to cwd
    if path is None or not path.exists():
        candidates = [
            Path(env_path) if env_path else None,
            Path.cwd() / "config" / ".env",
            Path.cwd() / ".env",
        ]
        for c in candidates:
            if c and c.exists():
                path = c
                break

    if not path or not path.exists():
        return  # silently continue; values may come from real env vars

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # strip inline comments (e.g. value #comment)
        if " #" in value:
            value = value[:value.index(" #")].strip()
        if key and key not in os.environ:
            os.environ[key] = value


# ----------------------------------------------------------------- getters

def get_anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key or key.startswith("sk-ant-..."):
        raise EnvironmentError("ANTHROPIC_API_KEY is not set in config/.env")
    return key


def get_elevenlabs_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key or key == "...":
        raise EnvironmentError("ELEVENLABS_API_KEY is not set in config/.env")
    return key


def get_elevenlabs_voice_id() -> str:
    return os.environ.get("ELEVENLABS_VOICE_ID", "8EkOjt4xTPGMclNlh1pk")


CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
