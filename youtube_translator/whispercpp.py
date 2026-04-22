from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .models import Segment


SRT_TIMING_RE = re.compile(
    r"(?P<start>\d\d:\d\d:\d\d,\d\d\d)\s+-->\s+(?P<end>\d\d:\d\d:\d\d,\d\d\d)"
)


def parse_srt_timestamp(value: str) -> float:
    hours = int(value[0:2])
    minutes = int(value[3:5])
    seconds = int(value[6:8])
    millis = int(value[9:12])
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def parse_srt(path: Path) -> list[Segment]:
    raw = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    blocks = [block.strip() for block in raw.split("\n\n") if block.strip()]
    segments: list[Segment] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        match = SRT_TIMING_RE.search(lines[1])
        if not match:
            continue
        text = " ".join(lines[2:]).strip()
        if not text:
            continue
        segments.append(
            Segment(
                index=len(segments),
                start=parse_srt_timestamp(match.group("start")),
                end=parse_srt_timestamp(match.group("end")),
                text=text,
            )
        )
    return segments


def transcribe_with_whispercpp(
    audio_path: Path,
    output_stem: Path,
    exe_path: Path,
    model_path: Path,
    language: str | None,
    device: int,
    threads: int,
    beam_size: int,
    best_of: int,
    use_gpu: bool,
    suppress_non_speech: bool,
    overwrite: bool,
) -> tuple[list[Segment], dict]:
    srt_path = Path(f"{output_stem}.srt")
    if srt_path.exists() and not overwrite:
        return parse_srt(srt_path), {"backend": "whisper.cpp", "cache": "srt"}

    exe_path = exe_path.resolve()
    model_path = model_path.resolve()
    output_stem.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(exe_path),
        "-m",
        str(model_path),
        "-f",
        str(audio_path),
        "-l",
        "auto" if language in (None, "auto") else language,
        "-dev",
        str(device),
        "-t",
        str(threads),
        "-bs",
        str(beam_size),
        "-bo",
        str(best_of),
        "-osrt",
        "-of",
        str(output_stem),
    ]
    if not use_gpu:
        command.append("-ng")
    if suppress_non_speech:
        command.append("-sns")

    proc = subprocess.run(command, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"whisper.cpp failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    if not srt_path.exists():
        raise RuntimeError(f"whisper.cpp did not create expected SRT: {srt_path}")

    metadata = {
        "backend": "whisper.cpp",
        "model_path": str(model_path),
        "device": device,
        "threads": threads,
        "use_gpu": use_gpu,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }
    return parse_srt(srt_path), metadata
