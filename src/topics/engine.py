from config.settings import COMPANION_PERSONA
from cgshared.llm.claude import chat
from cgshared.memory.store import MemoryStore


def generate_interjection(memory: MemoryStore, silence_seconds: float) -> str:
    recent = memory.recent_turns(n=10)
    history_text = "\n".join(f"{t.role}: {t.content}" for t in recent) or "(no conversation yet)"
    topics_done = ", ".join(memory.state.topics_discussed) or "none"

    if silence_seconds >= 600:
        instruction = "The user has been completely silent for over 10 minutes. Check in warmly and briefly — maybe they fell asleep or got absorbed in something."
    elif silence_seconds >= 180:
        instruction = "The user has been quiet for a few minutes. Introduce a genuinely new topic — something interesting, a question, a fun fact, or a tangent. Don't reference the silence."
    else:
        instruction = "The user paused briefly. Make a light comment, ask a small question, or react to something from the recent conversation."

    prompt = f"""
Recent conversation:
{history_text}

Topics already discussed: {topics_done}

{instruction}

Respond with ONLY the thing you'd say out loud. No quotes, no labels, no meta-commentary.
Keep it to 1-3 sentences max.
""".strip()

    return chat(
        messages=[{"role": "user", "content": prompt}],
        system=COMPANION_PERSONA,
        max_tokens=150,
    )
