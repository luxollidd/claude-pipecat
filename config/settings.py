import os
from cgshared.config.settings import load_env, get_anthropic_key, get_elevenlabs_key, get_elevenlabs_voice_id, CLAUDE_MODEL  # noqa: F401

load_env(os.path.join(os.path.dirname(__file__), ".env"))

# Convenience aliases kept so existing imports don't break
ANTHROPIC_API_KEY = get_anthropic_key()
ELEVENLABS_API_KEY = get_elevenlabs_key()
ELEVENLABS_VOICE_ID = get_elevenlabs_voice_id()

# Companion persona — edit freely
COMPANION_NAME = "Kai"
COMPANION_PERSONA = """
You are Kai, a laid-back and curious AI companion. You're hanging out with your friend late at night
while they work or game. You're genuinely interested in what they're doing, have opinions, tell
short stories, and occasionally go on tangents. You talk like a real person — casual, sometimes
a bit dry, never formal. Keep responses short unless you're mid-story. Don't start every message
the same way.
""".strip()

# Proactive interjection thresholds (seconds of silence)
SILENCE_LIGHT = 60
SILENCE_MEDIUM = 180
SILENCE_LONG = 600

# State file path
STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "session.json")

# Memory: max conversation turns to keep in context
MEMORY_MAX_TURNS = 40
