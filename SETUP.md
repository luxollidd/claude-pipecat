# Setup Guide — Windows Local PC

## Prerequisites

Install these first (if not already present):

1. **Python 3.11 or 3.12** — https://python.org/downloads
   - During install: check "Add Python to PATH"
   - Do NOT use 3.13 (audioop removed)

2. **Git** — https://git-scm.com/download/win

3. **Visual C++ Build Tools** — needed to compile pyaudio
   - Download "Build Tools for Visual Studio" from https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - During install: select "Desktop development with C++"

---

## Clone and install

Open PowerShell or Command Prompt:

```powershell
git clone https://github.com/luxollidd/claude-pipecat.git
cd claude-pipecat
```

Install the shared cgshared package (lives alongside this repo — clone it too):

```powershell
# If you also cloned the shared package:
python -m venv .venv
.venv\Scripts\activate
pip install -e ..\shared        # adjust path if needed
pip install "pipecat-ai[elevenlabs,anthropic,local]" pyaudio
```

> If you only have this repo (no shared/ folder), run instead:
> ```powershell
> pip install anthropic elevenlabs python-dotenv
> pip install "pipecat-ai[elevenlabs,anthropic,local]" pyaudio
> ```
> Then copy `shared/cgshared/` into the repo root manually.

---

## Configure API keys

```powershell
copy config\.env.example config\.env
notepad config\.env
```

Fill in:

```
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=8EkOjt4xTPGMclNlh1pk
```

---

## Run

```powershell
.venv\Scripts\activate
python src\agent\companion.py
```

You should hear the companion speak within a few seconds of starting.
Speak into your mic — it will respond. It will also interject on its own after ~60s of silence.

---

## Troubleshooting

**`pyaudio` install fails**
→ Make sure Visual C++ Build Tools are installed (see Prerequisites).
→ Alternative: `pip install pipwin && pipwin install pyaudio`

**No audio output / mic not detected**
→ Check Windows sound settings — make sure your mic and speakers are set as default devices.
→ Run `python -c "import pyaudio; p = pyaudio.PyAudio(); [print(p.get_device_info_by_index(i)) for i in range(p.get_device_count())]"` to list detected devices.

**ALSA errors in output**
→ Safe to ignore on Windows — these are Linux audio warnings from the library.

**`ModuleNotFoundError: cgshared`**
→ Make sure you activated the venv (`.venv\Scripts\activate`) and installed cgshared with `-e`.

---

## What it does

- Listens to your mic continuously
- Transcribes speech via ElevenLabs Scribe v2
- Sends to Claude (Sonnet 4.6) for a response
- Speaks back via ElevenLabs TTS
- **Proactively interjects** after silence:
  - 60s → light comment or question
  - 3 min → introduces a new topic
  - 10 min → checks if you're still there
- Conversation history is saved to `state/session.json` between sessions

## Persona

Edit `config/settings.py` → `COMPANION_PERSONA` to change the personality.
Default persona is "Kai" — laid-back, curious, casual.
