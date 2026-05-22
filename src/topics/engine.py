from config.settings import COMPANION_PERSONA
from cgshared.llm.claude import chat
from cgshared.memory.store import MemoryStore


def generate_interjection(memory: MemoryStore, silence_seconds: float, context=None) -> str:
    if context and context.messages:
        recent_msgs = context.messages[-10:]
        history_text = "\n".join(
            f"{m['role']}: {m['content'] if isinstance(m['content'], str) else ' '.join(p.get('text', '') for p in m['content'] if isinstance(p, dict))}"
            for m in recent_msgs
        )
    else:
        recent = memory.recent_turns(n=10)
        history_text = "\n".join(f"{t.role}: {t.content}" for t in recent) or "(no conversation yet)"
    topics_done = ", ".join(memory.state.topics_discussed) or "none"

    if silence_seconds >= 1800:
        instruction = "The user has been silent for a long time. Briefly check if they're still there — one short sentence, low-key."
    elif silence_seconds >= 900:
        instruction = "The user has been quiet for a while. A single short sentence to check in. Do NOT introduce a new topic or fill space with a story."
    else:
        instruction = "Brief check-in only. One short sentence max. Do not start a conversation or ask a leading question."

    prompt = f"""
Recent conversation:
{history_text}

{instruction}

Hard rules:
- One short sentence. Never more.
- No opinions, takes, fun facts, anecdotes, or tangents.
- Don't reference how long the silence was.
- Output ONLY what you'd say out loud — no quotes, no labels.
- Use the same language as the recent conversation above. Never default to English unless the conversation is in English.
""".strip()

    return chat(
        messages=[{"role": "user", "content": prompt}],
        system=COMPANION_PERSONA,
        max_tokens=60,
    )
