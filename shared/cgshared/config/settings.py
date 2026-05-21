import os
from dotenv import load_dotenv

# Load from whichever .env is closest to the calling project
# Each project calls load_env() with its own path before importing settings.
_loaded = False

def load_env(env_path: str):
    global _loaded
    load_dotenv(env_path)
    _loaded = True

# Shared API keys — used by all claude-gaming projects
def get_anthropic_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "")

def get_elevenlabs_key() -> str:
    return os.getenv("ELEVENLABS_API_KEY", "")

def get_elevenlabs_voice_id() -> str:
    return os.getenv("ELEVENLABS_VOICE_ID", "")

# Shared model default
CLAUDE_MODEL = "claude-sonnet-4-6"
