from config.settings import COMPANION_PERSONA
from cgshared.memory.store import MemoryStore


def build_system_prompt(memory: MemoryStore) -> str:
    topics = memory.state.topics_discussed
    topics_str = ""
    if topics:
        topics_str = f"\n\nTopics already covered this session: {', '.join(topics)}. Avoid revisiting unless the user brings them up."
    return f"{COMPANION_PERSONA}{topics_str}"


def build_messages(memory: MemoryStore) -> list[dict]:
    return memory.as_messages()
