from __future__ import annotations

import subprocess
from pathlib import Path


def convert_to_wav(input_path: Path, output_path: Path, overwrite: bool = False) -> Path:
    if output_path.exists() and not overwrite:
        return output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-y" if overwrite else "-n",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    proc = subprocess.run(command, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr}")
    return output_path
