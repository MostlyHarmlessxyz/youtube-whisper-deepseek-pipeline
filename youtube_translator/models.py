from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Segment:
    index: int
    start: float
    end: float
    text: str
    translated_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DownloadResult:
    source: str
    title: str
    video_id: str
    media_path: Path
    work_id: str


@dataclass(slots=True)
class PipelineResult:
    title: str
    work_id: str
    source_media: Path
    wav_path: Path
    transcript_json: Path
    source_srt: Path
    translated_json: Path | None
    translated_srt: Path | None
    bilingual_srt: Path | None

