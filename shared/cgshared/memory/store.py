"""
MemoryStore — persistent conversation history + session state.
Saves/loads from a JSON file so context survives restarts.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Turn:
    role: str          # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionState:
    topics_discussed: list[str] = field(default_factory=list)
    last_user_spoke_at: float = field(default_factory=time.time)
    turns: list[Turn] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "topics_discussed": self.topics_discussed,
            "last_user_spoke_at": self.last_user_spoke_at,
            "turns": [asdict(t) for t in self.turns],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SessionState":
        turns = [Turn(**t) for t in d.get("turns", [])]
        return cls(
            topics_discussed=d.get("topics_discussed", []),
            last_user_spoke_at=d.get("last_user_spoke_at", time.time()),
            turns=turns,
        )


class MemoryStore:
    def __init__(self, state_path: str, max_turns: int = 40):
        self._path = Path(state_path)
        self._max_turns = max_turns
        self.state: SessionState = self._load()

    # ------------------------------------------------------------------ I/O

    def _load(self) -> SessionState:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                return SessionState.from_dict(raw)
            except Exception:
                pass
        return SessionState()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self.state.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ---------------------------------------------------------------- turns

    def add_turn(self, role: str, content: str) -> None:
        self.state.turns.append(Turn(role=role, content=content))
        if role == "user":
            self.state.last_user_spoke_at = time.time()
        # trim to max_turns
        if len(self.state.turns) > self._max_turns:
            self.state.turns = self.state.turns[-self._max_turns:]
        self.save()

    def recent_turns(self, n: int = 10) -> list[Turn]:
        return self.state.turns[-n:]

    def as_messages(self) -> list[dict]:
        """Return turns as Anthropic-style messages list."""
        return [{"role": t.role, "content": t.content} for t in self.state.turns]

    # --------------------------------------------------------------- silence

    def seconds_since_user_spoke(self) -> float:
        return time.time() - self.state.last_user_spoke_at

    # --------------------------------------------------------------- topics

    def add_topic(self, topic: str) -> None:
        if topic not in self.state.topics_discussed:
            self.state.topics_discussed.append(topic)
            self.save()
