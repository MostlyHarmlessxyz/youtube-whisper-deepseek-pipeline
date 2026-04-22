from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from .audio import convert_to_wav
from .downloader import download_audio
from .models import DownloadResult, PipelineResult
from .profiles import (
    apply_asr_profile,
    apply_translation_profile,
    get_profile,
    glossary_text,
)
from .subtitles import read_json_segments, write_json, write_srt, write_vtt
from .transcriber import recommended_cpu_threads, transcribe_audio
from .translator import translate_segments
from .utils import PROJECT_ROOT, ensure_dirs, safe_stem, stable_id
from .whispercpp import transcribe_with_whispercpp


def prepare_source(source: str, download_dir: Path) -> DownloadResult:
    source_path = Path(source)
    if source_path.exists():
        title = safe_stem(source_path.stem)
        return DownloadResult(
            source=str(source_path),
            title=title,
            video_id=stable_id(str(source_path.resolve())),
            media_path=source_path,
            work_id=f"{title} [{stable_id(str(source_path.resolve()))}]",
        )
    return download_audio(source, download_dir)


def run_pipeline(
    source: str,
    target_language: str,
    source_language: str | None = None,
    model_size: str = "medium",
    device: str = "cpu",
    compute_type: str = "int8",
    cpu_threads: int | None = None,
    num_workers: int = 2,
    beam_size: int = 5,
    vad_filter: bool = True,
    batch_size: int = 24,
    translation_concurrency: int = 3,
    retries: int = 3,
    temperature: float = 0.1,
    skip_translation: bool = False,
    overwrite: bool = False,
    output_vtt: bool = False,
    backend: str = "faster-whisper",
    whispercpp_exe: Path | None = None,
    whispercpp_model: Path | None = None,
    whispercpp_device: int = 0,
    whispercpp_threads: int | None = None,
    whispercpp_no_gpu: bool = False,
    whispercpp_suppress_non_speech: bool = True,
    profile_name: str | None = None,
) -> PipelineResult:
    load_dotenv(PROJECT_ROOT / ".env")
    profile = get_profile(profile_name)

    downloads = PROJECT_ROOT / "downloads"
    outputs = PROJECT_ROOT / "outputs"
    cache = PROJECT_ROOT / "cache"
    ensure_dirs(downloads, outputs, cache, PROJECT_ROOT / "logs")

    download = prepare_source(source, downloads)
    stem = safe_stem(download.work_id)
    wav_path = cache / f"{stem}.16k.wav"
    transcript_json = outputs / f"{stem}.source.json"
    source_srt = outputs / f"{stem}.source.srt"
    translated_json = outputs / f"{stem}.{target_language}.json"
    translated_srt = outputs / f"{stem}.{target_language}.srt"
    bilingual_srt = outputs / f"{stem}.bilingual.srt"

    convert_to_wav(download.media_path, wav_path, overwrite=overwrite)

    if transcript_json.exists() and not overwrite:
        segments = read_json_segments(transcript_json)
        metadata = {"cache": "transcript_json"}
    else:
        if backend == "whispercpp-vulkan":
            if not whispercpp_exe or not whispercpp_model:
                raise RuntimeError("--whispercpp-exe and --whispercpp-model are required for whispercpp-vulkan.")
            whispercpp_stem = cache / f"{stem}.whispercpp"
            segments, metadata = transcribe_with_whispercpp(
                wav_path,
                output_stem=whispercpp_stem,
                exe_path=Path(whispercpp_exe),
                model_path=Path(whispercpp_model),
                language=source_language,
                device=whispercpp_device,
                threads=whispercpp_threads or recommended_cpu_threads(),
                beam_size=beam_size,
                best_of=1,
                use_gpu=not whispercpp_no_gpu,
                suppress_non_speech=whispercpp_suppress_non_speech,
                overwrite=overwrite,
            )
        elif backend == "faster-whisper":
            segments, metadata = transcribe_audio(
                wav_path,
                model_size=model_size,
                language=source_language,
                device=device,
                compute_type=compute_type,
                cpu_threads=cpu_threads or recommended_cpu_threads(),
                num_workers=num_workers,
                beam_size=beam_size,
                vad_filter=vad_filter,
            )
        else:
            raise RuntimeError(f"Unsupported backend: {backend}")
    segments = apply_asr_profile(segments, profile)
    if profile:
        metadata["profile"] = profile.name
    write_json(transcript_json, segments, metadata)
    write_srt(source_srt, segments, mode="source")
    if output_vtt:
        write_vtt(outputs / f"{stem}.source.vtt", segments, mode="source")

    if skip_translation:
        return PipelineResult(
            title=download.title,
            work_id=download.work_id,
            source_media=download.media_path,
            wav_path=wav_path,
            transcript_json=transcript_json,
            source_srt=source_srt,
            translated_json=None,
            translated_srt=None,
            bilingual_srt=None,
        )

    if translated_json.exists() and not overwrite:
        cached_translated_segments = read_json_segments(translated_json)
        translated_by_index = {
            segment.index: segment.translated_text for segment in cached_translated_segments
        }
        translated_segments = [
            type(segment)(
                index=segment.index,
                start=segment.start,
                end=segment.end,
                text=segment.text,
                translated_text=translated_by_index.get(segment.index),
            )
            for segment in segments
        ]
        missing_translations = [
            segment.index for segment in translated_segments if not segment.translated_text
        ]
    else:
        translated_segments = []
        missing_translations = []

    if translated_segments and not missing_translations:
        pass
    else:
        if missing_translations:
            print(f"Resuming DeepSeek translation for {len(missing_translations)} missing segments.", flush=True)
        translated_segments = translate_segments(
            segments,
            target_language=target_language,
            source_language=metadata.get("language") or source_language,
            batch_size=batch_size,
            concurrency=translation_concurrency,
            retries=retries,
            temperature=temperature,
            checkpoint_path=translated_json,
            metadata=metadata,
            glossary=glossary_text(profile),
        )
        translated_segments = apply_translation_profile(translated_segments, profile)
        write_json(translated_json, translated_segments, metadata)

    translated_segments = apply_translation_profile(translated_segments, profile)
    write_json(translated_json, translated_segments, metadata)
    write_srt(translated_srt, translated_segments, mode="translated")
    write_srt(bilingual_srt, translated_segments, mode="bilingual")
    if output_vtt:
        write_vtt(outputs / f"{stem}.{target_language}.vtt", translated_segments, mode="translated")
        write_vtt(outputs / f"{stem}.bilingual.vtt", translated_segments, mode="bilingual")

    return PipelineResult(
        title=download.title,
        work_id=download.work_id,
        source_media=download.media_path,
        wav_path=wav_path,
        transcript_json=transcript_json,
        source_srt=source_srt,
        translated_json=translated_json,
        translated_srt=translated_srt,
        bilingual_srt=bilingual_srt,
    )
