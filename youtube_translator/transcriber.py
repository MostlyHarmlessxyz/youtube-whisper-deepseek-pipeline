from __future__ import annotations

import os
from pathlib import Path

from .models import Segment


def recommended_cpu_threads() -> int:
    count = os.cpu_count() or 8
    return max(4, count - 2)


def transcribe_audio(
    audio_path: Path,
    model_size: str,
    language: str | None,
    device: str,
    compute_type: str,
    cpu_threads: int | None,
    num_workers: int,
    beam_size: int,
    vad_filter: bool,
) -> tuple[list[Segment], dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        cpu_threads=cpu_threads or recommended_cpu_threads(),
        num_workers=num_workers,
    )
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=None if language in (None, "auto") else language,
        beam_size=beam_size,
        vad_filter=vad_filter,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    segments = [
        Segment(index=i, start=item.start, end=item.end, text=item.text.strip())
        for i, item in enumerate(segments_iter)
        if item.text.strip()
    ]
    metadata = {
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "model_size": model_size,
        "device": device,
        "compute_type": compute_type,
    }
    return segments, metadata

