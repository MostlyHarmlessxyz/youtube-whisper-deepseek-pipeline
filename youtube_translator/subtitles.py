from __future__ import annotations

import json
from pathlib import Path

from .models import Segment


def srt_timestamp(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def vtt_timestamp(seconds: float) -> str:
    return srt_timestamp(seconds).replace(",", ".")


def write_json(path: Path, segments: list[Segment], metadata: dict | None = None) -> None:
    payload = {
        "metadata": metadata or {},
        "segments": [segment.to_dict() for segment in segments],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_segments(path: Path) -> list[Segment]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Segment(**item) for item in payload["segments"]]


def write_srt(path: Path, segments: list[Segment], mode: str = "source") -> None:
    lines: list[str] = []
    for idx, segment in enumerate(segments, start=1):
        source = segment.text.strip()
        translated = (segment.translated_text or "").strip()
        if mode == "translated":
            text = translated or source
        elif mode == "bilingual":
            text = f"{translated}\n{source}" if translated else source
        else:
            text = source
        lines.extend(
            [
                str(idx),
                f"{srt_timestamp(segment.start)} --> {srt_timestamp(segment.end)}",
                text,
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_vtt(path: Path, segments: list[Segment], mode: str = "source") -> None:
    lines = ["WEBVTT", ""]
    for segment in segments:
        source = segment.text.strip()
        translated = (segment.translated_text or "").strip()
        if mode == "translated":
            text = translated or source
        elif mode == "bilingual":
            text = f"{translated}\n{source}" if translated else source
        else:
            text = source
        lines.extend(
            [
                f"{vtt_timestamp(segment.start)} --> {vtt_timestamp(segment.end)}",
                text,
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")

