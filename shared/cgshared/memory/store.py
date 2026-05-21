import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Turn:
    role: str          # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionState:
    turns: list[Turn] = field(default_factory=list)
    topics_discussed: list[str] = field(default_factory=list)
    last_user_utterance_at: float = field(default_factory=time.time)
    session_start: float = field(default_factory=time.time)


class MemoryStore:
    def __init__(self, state_path: str, max_turns: int = 40):
        self.state_path = state_path
        self.max_turns = max_turns
        self.state = self._load()

    def _load(self) -> SessionState:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path) as f:
                    raw = json.load(f)
                turns = [Turn(**t) for t in raw.get("turns", [])]
                return SessionState(
                    turns=turns,
                    topics_discussed=raw.get("topics_discussed", []),
                    last_user_utterance_at=raw.get("last_user_utterance_at", time.time()),
                    session_start=raw.get("session_start", time.time()),
                )
            except Exception:
                pass
        return SessionState()

    def save(self):
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        data = {
            "turns": [asdict(t) for t in self.state.turns],
            "topics_discussed": self.state.topics_discussed,
            "last_user_utterance_at": self.state.last_user_utterance_at,
            "session_start": self.state.session_start,
        }
        with open(self.state_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_turn(self, role: str, content: str):
        self.state.turns.append(Turn(role=role, content=content))
        if role == "user":
            self.state.last_user_utterance_at = time.time()
        if len(self.state.turns) > self.max_turns:
            self.state.turns = self.state.turns[-self.max_turns:]
        self.save()

    def mark_topic(self, topic: str):
        if topic not in self.state.topics_discussed:
            self.state.topics_discussed.append(topic)
        self.save()

    def seconds_since_user_spoke(self) -> float:
        return time.time() - self.state.last_user_utterance_at

    def recent_turns(self, n: Optional[int] = None) -> list[Turn]:
        turns = self.state.turns
        return turns[-n:] if n else turns

    def as_messages(self) -> list[dict]:
        return [{"role": t.role, "content": t.content} for t in self.state.turns]

    def reset(self):
        self.state = SessionState()
        self.save()
