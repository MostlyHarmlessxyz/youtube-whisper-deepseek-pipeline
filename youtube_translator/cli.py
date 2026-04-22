from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

from .doctor import run_doctor
from .pipeline import run_pipeline
from .qa import qa_report
from .transcriber import recommended_cpu_threads


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate YouTube videos with faster-whisper and DeepSeek API."
    )
    parser.add_argument("source", nargs="?", help="YouTube URL or local media file.")
    parser.add_argument("--file", help="Text file containing one URL/path per line.")
    parser.add_argument("--target", default="zh-CN", help="Target language, default: zh-CN.")
    parser.add_argument("--source-language", default="auto", help="Source language or auto.")
    parser.add_argument(
        "--profile",
        choices=["general", "mit-diffusion", "cmu-db"],
        default="general",
        help="Domain profile for ASR cleanup and glossary-guided translation.",
    )
    parser.add_argument(
        "--mit-diffusion",
        action="store_true",
        help="Shortcut preset for MIT 6.S184 diffusion course: Arc Vulkan, English, zh-CN, VTT.",
    )
    parser.add_argument(
        "--cmu-db",
        action="store_true",
        help="Shortcut preset for CMU 15-445/645 database systems: Arc Vulkan, English, zh-CN, VTT.",
    )
    parser.add_argument("--model", default="medium", help="Whisper model size, e.g. small, medium, large-v3.")
    parser.add_argument("--device", default="cpu", help="faster-whisper device: cpu, cuda, or auto.")
    parser.add_argument("--compute-type", default="int8", help="faster-whisper compute type.")
    parser.add_argument("--cpu-threads", type=int, default=recommended_cpu_threads())
    parser.add_argument("--workers", type=int, default=2, help="faster-whisper worker count.")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--no-vad", action="store_true", help="Disable voice activity filtering.")
    parser.add_argument("--batch-size", type=int, default=24, help="Subtitle segments per translation request.")
    parser.add_argument("--translation-concurrency", type=int, default=3)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument(
        "--initial-prompt",
        help="Short English Whisper initial prompt. Defaults to the selected course profile prompt.",
    )
    parser.add_argument("--skip-translation", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--keep-going", action="store_true", default=True, help="Continue batch after one source fails.")
    parser.add_argument(
        "--no-merge-segments",
        action="store_true",
        help="Keep raw Whisper subtitle segmentation instead of merging short chunks.",
    )
    parser.add_argument("--vtt", action="store_true", help="Also output WebVTT files.")
    parser.add_argument("--doctor", action="store_true", help="Check local environment and exit.")
    parser.add_argument("--qa", help="Run QA on an output JSON file and exit.")
    parser.add_argument(
        "--backend",
        choices=["faster-whisper", "whispercpp-vulkan"],
        default="faster-whisper",
        help="Transcription backend.",
    )
    parser.add_argument(
        "--whispercpp-exe",
        default="tools/whisper.cpp-vulkan/whisper-cli.exe",
        help="Path to whisper.cpp whisper-cli.exe.",
    )
    parser.add_argument(
        "--whispercpp-model",
        default="models/ggml-large-v3-turbo-q5_0.bin",
        help="Path to a ggml whisper.cpp model.",
    )
    parser.add_argument("--whispercpp-device", type=int, default=0, help="Vulkan device id; A750 is usually 0.")
    parser.add_argument("--whispercpp-threads", type=int, default=recommended_cpu_threads())
    parser.add_argument("--whispercpp-no-gpu", action="store_true")
    parser.add_argument("--whispercpp-keep-nst", action="store_true", help="Do not suppress non-speech tokens.")
    return parser


def iter_sources(source: str | None, file: str | None) -> list[str]:
    sources: list[str] = []
    if source:
        sources.append(source)
    if file:
        with open(file, "r", encoding="utf-8") as handle:
            sources.extend(line.strip() for line in handle if line.strip() and not line.startswith("#"))
    if not sources:
        raise SystemExit("Provide a YouTube URL/local media path or --file urls.txt")
    return sources


def main() -> None:
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args()
    if args.doctor:
        run_doctor()
        return
    if args.qa:
        qa_report(Path(args.qa), args.profile)
        return
    if args.mit_diffusion:
        args.profile = "mit-diffusion"
        args.backend = "whispercpp-vulkan"
        args.source_language = "en"
        args.target = "zh-CN"
        args.beam_size = 1
        args.batch_size = min(args.batch_size, 20)
        args.translation_concurrency = min(args.translation_concurrency, 3)
        args.vtt = True
    if args.cmu_db:
        args.profile = "cmu-db"
        args.backend = "whispercpp-vulkan"
        args.source_language = "en"
        args.target = "zh-CN"
        args.beam_size = 1
        args.batch_size = min(args.batch_size, 20)
        args.translation_concurrency = min(args.translation_concurrency, 3)
        args.vtt = True
    for source in iter_sources(args.source, args.file):
        try:
            result = run_pipeline(
                source=source,
                target_language=args.target,
                source_language=args.source_language,
                model_size=args.model,
                device=args.device,
                compute_type=args.compute_type,
                cpu_threads=args.cpu_threads,
                num_workers=args.workers,
                beam_size=args.beam_size,
                vad_filter=not args.no_vad,
                batch_size=args.batch_size,
                translation_concurrency=args.translation_concurrency,
                retries=args.retries,
                temperature=args.temperature,
                skip_translation=args.skip_translation,
                overwrite=args.overwrite,
                output_vtt=args.vtt,
                backend=args.backend,
                whispercpp_exe=args.whispercpp_exe,
                whispercpp_model=args.whispercpp_model,
                whispercpp_device=args.whispercpp_device,
                whispercpp_threads=args.whispercpp_threads,
                whispercpp_no_gpu=args.whispercpp_no_gpu,
                whispercpp_suppress_non_speech=not args.whispercpp_keep_nst,
                profile_name=args.profile,
                merge_segments=not args.no_merge_segments,
                initial_prompt=args.initial_prompt,
            )
        except Exception:
            print(f"Failed: {source}", flush=True)
            traceback.print_exc()
            if args.keep_going:
                continue
            raise
        print(f"Completed: {result.work_id}")
        print(f"Source SRT: {result.source_srt}")
        if result.translated_srt:
            print(f"Translated SRT: {result.translated_srt}")
        if result.bilingual_srt:
            print(f"Bilingual SRT: {result.bilingual_srt}")


if __name__ == "__main__":
    main()
