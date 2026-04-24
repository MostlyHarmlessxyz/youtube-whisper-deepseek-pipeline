from __future__ import annotations

import re

from .models import Segment


SENTENCE_END_RE = re.compile(r"""[.!?。！？]['")\]]*$""")
SENTENCE_TOKEN_RE = re.compile(r"""[^.!?。！？]+[.!?。！？]*['")\]]*""")


def _join_text(left: str, right: str) -> str:
    left = left.strip()
    right = right.strip()
    if not left:
        return right
    if not right:
        return left
    return f"{left} {right}"


def _normalize_repeat_key(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _collapse_repeated_sentence_pattern(text: str) -> str:
    tokens = [token.strip() for token in SENTENCE_TOKEN_RE.findall(text) if token.strip()]
    if len(tokens) < 2:
        return text.strip()

    normalized = [_normalize_repeat_key(token) for token in tokens]
    for unit in range(1, len(tokens) // 2 + 1):
        if len(tokens) % unit:
            continue
        pattern = normalized[:unit]
        if all(normalized[i : i + unit] == pattern for i in range(0, len(tokens), unit)):
            return " ".join(tokens[:unit]).strip()
    return " ".join(tokens).strip()


def _dedupe_repeated_runs(
    segments: list[Segment],
    *,
    min_repeats: int,
    max_gap: float,
    min_chars: int,
    max_segment_duration: float,
) -> list[Segment]:
    if not segments:
        return []

    deduped: list[Segment] = []
    run: list[Segment] = []

    def qualifies(segment: Segment) -> bool:
        return (
            len(_normalize_repeat_key(segment.text)) >= min_chars
            and (segment.end - segment.start) <= max_segment_duration
        )

    def same_run(left: Segment, right: Segment) -> bool:
        return (
            qualifies(left)
            and qualifies(right)
            and _normalize_repeat_key(left.text) == _normalize_repeat_key(right.text)
            and max(0.0, right.start - left.end) <= max_gap
        )

    def flush() -> None:
        nonlocal run
        if not run:
            return
        if len(run) >= min_repeats:
            first = run[0]
            deduped.append(
                Segment(
                    index=len(deduped),
                    start=first.start,
                    end=run[-1].end,
                    text=first.text.strip(),
                    translated_text=first.translated_text,
                )
            )
        else:
            for segment in run:
                deduped.append(
                    Segment(
                        index=len(deduped),
                        start=segment.start,
                        end=segment.end,
                        text=segment.text.strip(),
                        translated_text=segment.translated_text,
                    )
                )
        run = []

    for segment in segments:
        cleaned_text = _collapse_repeated_sentence_pattern(segment.text.strip())
        if not cleaned_text:
            continue
        cleaned = Segment(
            index=segment.index,
            start=segment.start,
            end=segment.end,
            text=cleaned_text,
            translated_text=segment.translated_text,
        )
        if not run or same_run(run[-1], cleaned):
            run.append(cleaned)
            continue
        flush()
        run = [cleaned]

    flush()
    return deduped


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
    segments = _dedupe_repeated_runs(
        segments,
        min_repeats=3,
        max_gap=0.25,
        min_chars=24,
        max_segment_duration=2.5,
    )

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
        text = _collapse_repeated_sentence_pattern(segment.text.strip())
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
    return _dedupe_repeated_runs(
        merged,
        min_repeats=2,
        max_gap=0.5,
        min_chars=24,
        max_segment_duration=6.0,
    )
