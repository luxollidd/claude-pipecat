# setup_windows.ps1
# One-shot setup for claude-pipecat on Windows.
# Run from the repo root in PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\setup_windows.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "`n=== claude-pipecat Windows setup ===" -ForegroundColor Cyan

# 1. Check Python
try {
    $pyver = python --version 2>&1
    Write-Host "[OK] $pyver"
} catch {
    Write-Error "Python not found. Install Python 3.11 or 3.12 from https://python.org/downloads (check 'Add to PATH')."
}

# 2. Create venv if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "[...] Creating virtual environment..."
    python -m venv .venv
    Write-Host "[OK]  .venv created"
} else {
    Write-Host "[OK]  .venv already exists"
}

# 3. Activate
Write-Host "[...] Activating venv..."
& .\.venv\Scripts\Activate.ps1

# 4. Upgrade pip
Write-Host "[...] Upgrading pip..."
python -m pip install --upgrade pip --quiet

# 5. Install cgshared first (other packages may import it at install time)
Write-Host "[...] Installing cgshared (shared package)..."
pip install -e ./shared --quiet

# 6. Install the rest
Write-Host "[...] Installing pipecat + dependencies (this may take a minute)..."
pip install "pipecat-ai[elevenlabs,anthropic,local]" anthropic python-dotenv --quiet

# 7. Install pyaudio — try wheel first, fall back to pipwin
Write-Host "[...] Installing pyaudio..."
try {
    pip install pyaudio --quiet
    Write-Host "[OK]  pyaudio installed"
} catch {
    Write-Host "[!]  Direct install failed — trying pipwin fallback..."
    pip install pipwin --quiet
    pipwin install pyaudio
}

# 8. Config file
if (-not (Test-Path "config\.env")) {
    Copy-Item "config\.env.example" "config\.env"
    Write-Host ""
    Write-Host "=== ACTION REQUIRED ===" -ForegroundColor Yellow
    Write-Host "Edit config\.env and fill in your API keys:" -ForegroundColor Yellow
    Write-Host "  ANTHROPIC_API_KEY=sk-ant-..." -ForegroundColor White
    Write-Host "  ELEVENLABS_API_KEY=sk_..." -ForegroundColor White
    Write-Host "  ELEVENLABS_VOICE_ID=8EkOjt4xTPGMclNlh1pk" -ForegroundColor White
    Write-Host ""
    notepad config\.env
} else {
    Write-Host "[OK]  config\.env already exists"
}

# 9. Create state dir
if (-not (Test-Path "state")) {
    New-Item -ItemType Directory -Path "state" | Out-Null
    Write-Host "[OK]  state/ directory created"
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To run the companion:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python src\agent\companion.py"
Write-Host ""
