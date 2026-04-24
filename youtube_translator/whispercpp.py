from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .audio import extract_wav_chunk, probe_audio_duration
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
    raw = path.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
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


def _segment_key(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _run_whispercpp_once(
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
    initial_prompt: str | None,
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
    if initial_prompt:
        command.extend(["--prompt", initial_prompt, "--carry-initial-prompt"])

    proc = subprocess.run(command, text=True, encoding="utf-8", errors="replace", capture_output=True)
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
        "initial_prompt": initial_prompt,
    }
    return parse_srt(srt_path), metadata


def _stitch_chunk_segments(chunks: list[tuple[float, list[Segment]]]) -> list[Segment]:
    stitched: list[Segment] = []
    for chunk_start, chunk_segments in chunks:
        for segment in chunk_segments:
            absolute = Segment(
                index=len(stitched),
                start=segment.start + chunk_start,
                end=segment.end + chunk_start,
                text=segment.text.strip(),
                translated_text=segment.translated_text,
            )
            if not absolute.text:
                continue
            if stitched:
                prev = stitched[-1]
                if _segment_key(prev.text) == _segment_key(absolute.text) and absolute.start <= prev.end + 1.0:
                    prev.end = max(prev.end, absolute.end)
                    continue
                if absolute.end <= prev.end + 0.05:
                    continue
                if absolute.start < prev.end:
                    absolute.start = prev.end
                    if absolute.end - absolute.start <= 0.05:
                        continue
            absolute.index = len(stitched)
            stitched.append(absolute)
    return stitched


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
    initial_prompt: str | None,
    overwrite: bool,
) -> tuple[list[Segment], dict]:
    srt_path = Path(f"{output_stem}.srt")
    if srt_path.exists() and not overwrite:
        return parse_srt(srt_path), {"backend": "whisper.cpp", "cache": "srt"}

    duration = probe_audio_duration(audio_path)
    chunk_duration = 600.0
    chunk_overlap = 2.0
    if duration <= chunk_duration + chunk_overlap:
        return _run_whispercpp_once(
            audio_path,
            output_stem,
            exe_path,
            model_path,
            language,
            device,
            threads,
            beam_size,
            best_of,
            use_gpu,
            suppress_non_speech,
            initial_prompt,
            overwrite,
        )

    chunk_results: list[tuple[float, list[Segment]]] = []
    current_start = 0.0
    chunk_index = 0
    while current_start < duration:
        current_duration = min(chunk_duration, duration - current_start)
        chunk_audio = output_stem.parent / f"{output_stem.name}.chunk{chunk_index:03d}.wav"
        chunk_stem = output_stem.parent / f"{output_stem.name}.chunk{chunk_index:03d}"
        extract_wav_chunk(
            audio_path,
            chunk_audio,
            start_seconds=current_start,
            duration_seconds=current_duration,
            overwrite=overwrite,
        )
        chunk_segments, _ = _run_whispercpp_once(
            chunk_audio,
            chunk_stem,
            exe_path,
            model_path,
            language,
            device,
            threads,
            beam_size,
            best_of,
            use_gpu,
            suppress_non_speech,
            initial_prompt,
            overwrite,
        )
        chunk_results.append((current_start, chunk_segments))
        if current_start + current_duration >= duration:
            break
        current_start += chunk_duration - chunk_overlap
        chunk_index += 1

    stitched = _stitch_chunk_segments(chunk_results)
    lines: list[str] = []
    def fmt(ms: int) -> str:
        hours, rem = divmod(ms, 3_600_000)
        minutes, rem = divmod(rem, 60_000)
        seconds, millis = divmod(rem, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"
    for idx, segment in enumerate(stitched, start=1):
        start_ms = max(0, round(segment.start * 1000))
        end_ms = max(start_ms, round(segment.end * 1000))
        lines.extend([str(idx), f"{fmt(start_ms)} --> {fmt(end_ms)}", segment.text, ""])
    srt_path.write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "backend": "whisper.cpp",
        "model_path": str(model_path.resolve()),
        "device": device,
        "threads": threads,
        "use_gpu": use_gpu,
        "initial_prompt": initial_prompt,
        "chunked": True,
        "chunk_duration_seconds": chunk_duration,
        "chunk_overlap_seconds": chunk_overlap,
        "chunk_count": len(chunk_results),
        "audio_duration_seconds": duration,
    }
    return stitched, metadata
