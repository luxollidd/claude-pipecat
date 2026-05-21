## [2026-05-21 00:00:00] Initial Project Scaffold
**Status:** Complete
**Goal:** Build a proactive voice AI companion using Pipecat + Claude for late-night gaming/work sessions.
**Key Files:**
- src/agent/companion.py
- src/agent/proactive.py
- src/memory/store.py
- src/memory/context.py
- src/topics/engine.py
- config/settings.py
**Checklist:**
- [x] Project structure scaffolded
- [x] Skills file written
- [x] README written
- [x] Core pipeline (companion.py) implemented
- [x] Proactive loop (proactive.py) implemented
- [x] Memory store implemented
- [x] Topic engine implemented
- [x] Config and .env.example created
- [x] requirements.txt written

---

## [2026-05-22] Port to Windows (local PC)
**Status:** Complete
**Goal:** Move from headless Ubuntu VM (no audio hardware) to Windows local machine with mic + speakers.
**Changes:**
- Reconstructed `cgshared` shared package (was only on VM, never pushed to GitHub)
  - `shared/cgshared/memory/store.py` — MemoryStore, Turn, SessionState
  - `shared/cgshared/llm/claude.py` — chat() wrapper
  - `shared/cgshared/config/settings.py` — .env loader + typed getters
  - `shared/pyproject.toml` — installable as local package
- Updated `requirements.txt` to use `-e ./shared` (self-contained, no sibling repo needed)
- Added `setup_windows.ps1` — one-shot PowerShell setup script for Windows
**Checklist:**
- [x] cgshared reconstructed from import signatures
- [x] requirements.txt updated
- [x] Windows setup script written
- [ ] End-to-end test on Windows with real mic/speakers
- [ ] Push shared/ to GitHub
