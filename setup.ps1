$ErrorActionPreference = "Stop"

py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -e .

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example. Edit DEEPSEEK_API_KEY before translation."
}

.\.venv\Scripts\yt-translate.exe --doctor

