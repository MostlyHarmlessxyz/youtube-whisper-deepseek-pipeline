from __future__ import annotations

import re

from .models import Segment


SENTENCE_END_RE = re.compile(r"""[.!?。！？]['")\]]*$""")


def _join_text(left: str, right: str) -> str:
    left = left.strip()
    right = right.strip()
    if not left:
        return right
    if not right:
        return left
    return f"{left} {right}"


def merge_sentence_segments(
    segments: list[Segment],
    *,
    max_gap: float = 0.9,
    min_duration: float = 3.0,
    min_chars: int = 45,
    max_duration: float = 14.0,
    max_chars: int = 240,
) -> list[Segment]:
    """Merge short ASR chunks into sentence-sized subtitle segments.

    Whisper backends often emit very small timestamp chunks. Translation quality
    improves when each request item contains enough context, but subtitles still
    need bounded duration and length for readability.
    """
    if not segments:
        return []

    merged: list[Segment] = []
    current: Segment | None = None

    def flush() -> None:
        nonlocal current
        if current and current.text.strip():
            merged.append(
                Segment(
                    index=len(merged),
                    start=current.start,
                    end=current.end,
                    text=current.text.strip(),
                    translated_text=current.translated_text,
                )
            )
        current = None

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        if current is None:
            current = Segment(
                index=0,
                start=segment.start,
                end=segment.end,
                text=text,
                translated_text=segment.translated_text,
            )
        else:
            gap = max(0.0, segment.start - current.end)
            if gap > max_gap:
                flush()
                current = Segment(
                    index=0,
                    start=segment.start,
                    end=segment.end,
                    text=text,
                    translated_text=segment.translated_text,
                )
            else:
                current.end = max(current.end, segment.end)
                current.text = _join_text(current.text, text)

        duration = current.end - current.start
        char_count = len(current.text)
        ends_sentence = bool(SENTENCE_END_RE.search(current.text))
        if duration >= max_duration or char_count >= max_chars:
            flush()
        elif ends_sentence and duration >= min_duration and char_count >= min_chars:
            flush()

    flush()
    return merged
