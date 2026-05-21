# Claude Gaming Companion (Pipecat)

A voice-based AI companion powered by Claude, built on [Pipecat](https://github.com/pipecat-ai/pipecat).

Designed for late-night solo sessions — the companion can **proactively** interject, introduce topics, and keep conversation flowing without waiting for the user to speak first.

---

## Architecture

```
User mic → STT → Claude (LLM) → TTS → User speakers
              ↑
     Proactive Interjection Loop (background)
              ↑
     Topic Engine + Memory Store
```

### Core Components

| Component | Path | Purpose |
|---|---|---|
| `src/agent/companion.py` | Agent pipeline | Main Pipecat pipeline wiring |
| `src/agent/proactive.py` | Proactive loop | Background thread that fires unprompted speech |
| `src/memory/store.py` | Memory store | Conversation + topic history |
| `src/memory/context.py` | Context builder | Builds system prompt from memory |
| `src/topics/engine.py` | Topic engine | Generates fresh topics using Claude |
| `src/voice/transport.py` | Voice I/O | STT + TTS wiring (Deepgram / ElevenLabs) |
| `config/settings.py` | Config | API keys, thresholds, persona |
| `state/` | Runtime state | Persisted session state (JSON) |

---

## Proactive Interjection Logic

The companion monitors conversation silence. When silence exceeds a threshold, a background loop:

1. Checks how long since the last utterance
2. Asks the Topic Engine for a new topic (or resurfaces an old thread)
3. Generates a natural-sounding interjection via Claude
4. Injects the audio output into the Pipecat pipeline

Thresholds (configurable in `config/settings.py`):
- **Short silence (60s):** light comment / question about current context
- **Medium silence (3min):** introduce a new topic
- **Long silence (10min):** check-in ("still there?")

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/.env.example config/.env
# fill in API keys
python src/agent/companion.py
```

---

## Dependencies

- `pipecat-ai` — voice pipeline framework
- `anthropic` — Claude LLM
- `elevenlabs` — STT (Scribe v2 Realtime) + TTS — single provider for the full voice layer
- `pyaudio` — local mic/speaker access
