from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from .transcriber import recommended_cpu_threads
from .utils import PROJECT_ROOT


def command_version(command: str, args: list[str]) -> str:
    exe = shutil.which(command)
    local_exe = Path(sys.executable).parent / f"{command}.exe"
    if not exe and local_exe.exists():
        exe = str(local_exe)
    if not exe:
        return "missing"
    try:
        proc = subprocess.run(
            [exe, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic should not crash on odd tools.
        return f"error: {exc}"
    line = (proc.stdout or proc.stderr).splitlines()
    return line[0] if line else "available"


def run_doctor() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("DEEPSEEK_API_KEY") or ""
    api_key_state = "set"
    if not api_key or api_key == "sk-your-key-here":
        api_key_state = "missing"
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"ffmpeg: {command_version('ffmpeg', ['-version'])}")
    print(f"ffprobe: {command_version('ffprobe', ['-version'])}")
    print(f"yt-dlp: {command_version('yt-dlp', ['--version'])}")
    print(f"deno: {command_version('deno', ['--version'])}")
    print(f"CPU logical cores: {os.cpu_count()}")
    print(f"Recommended Whisper CPU threads: {recommended_cpu_threads()}")
    print(f"DEEPSEEK_API_KEY: {api_key_state}")
    print(f"DEEPSEEK_BASE_URL: {os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')}")
    print(f"DEEPSEEK_MODEL: {os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')}")
