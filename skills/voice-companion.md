# Skill: Voice Companion (Pipecat + Claude)

## What this project is

A local voice AI companion that:
- Listens via microphone (Deepgram STT)
- Thinks with Claude (Anthropic)
- Speaks via ElevenLabs TTS
- **Proactively interjects** when the user is silent — introduces new topics, asks questions, checks in

## Key architecture decisions

### Proactive interjection
- `src/agent/proactive.py` runs a background `asyncio` loop, polling silence every 10s
- Silence thresholds: 60s = light comment, 3min = new topic, 10min = check-in
- A 90s cooldown prevents back-to-back interjections
- Interjections are generated via a direct `anthropic` call (not through the pipeline LLM), then injected into the TTS queue

### Memory
- `src/memory/store.py` — `MemoryStore` persists turns + topics to `state/session.json`
- `src/memory/context.py` — builds the system prompt and message list for each LLM call
- Topics discussed are tracked to avoid repetition

### Pipeline
- Standard Pipecat pipeline: `mic → STT → user aggregator → LLM → TTS → speakers → assistant aggregator`
- `allow_interruptions=True` so the user can talk over the companion

## Config

All tunable values in `config/settings.py`:
- `COMPANION_PERSONA` — edit the personality here
- `COMPANION_NAME` — name shown in logs
- `SILENCE_LIGHT / SILENCE_MEDIUM / SILENCE_LONG` — interjection thresholds

## Running

```bash
cd ~/claude-gaming/pipecat
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config/.env.example config/.env   # fill in keys
python src/agent/companion.py
```

## API keys needed

- `ANTHROPIC_API_KEY` — claude.ai / Anthropic console
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` — elevenlabs.io (handles both STT via Scribe and TTS)

## Provider summary

ElevenLabs handles the full voice layer — STT (Scribe v2 Realtime) and TTS. Only two providers total: ElevenLabs + Anthropic.

## Swap TTS to free (edge-tts)

If you want zero TTS cost, replace the ElevenLabs TTS import in `companion.py` with:
```python
from pipecat.services.edge_tts import EdgeTTSService
tts = EdgeTTSService(voice="en-US-GuyNeural")
```
You'd still need ElevenLabs for STT (Scribe).
