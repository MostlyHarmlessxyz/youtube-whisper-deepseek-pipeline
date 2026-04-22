from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_COURSE_DIR = ROOT / "MIT 6.S184 Flow Matching and Diffusion Models (2026)"
FONT_ZH = Path(r"C:\Windows\Fonts\simkai.ttf")
FONT_EN = Path(r"C:\Windows\Fonts\georgia.ttf")


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def ass_escape(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("\r", " ")
        .replace("\n", r"\N")
        .strip()
    )


def ass_time(seconds: float) -> str:
    centis = max(0, round(seconds * 100))
    hours, rem = divmod(centis, 360_000)
    minutes, rem = divmod(rem, 6_000)
    secs, centis = divmod(rem, 100)
    return f"{hours}:{minutes:02}:{secs:02}.{centis:02}"


def sanitize_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]', " - ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" .-")


def simplify_title(name: str) -> str:
    base = Path(name).stem
    base = re.sub(r"\s*\[[A-Za-z0-9_-]{11}\]\s*$", "", base).strip()

    mit = re.search(r"(Lecture\s+\d+[A-Z]?)\s*(?:-|：|:)?\s*(.*?)\s*\(2026\)", base)
    if mit:
        lecture = mit.group(1).strip()
        title = re.sub(r"\s+", " ", mit.group(2)).strip(" -:：")
        title = title.replace("Neural networks", "Neural Networks")
        return sanitize_filename(f"{lecture} - {title}")

    cmu = re.search(r"#\s*(\d+[A-Z]?)\s*(?:-|：|:)?\s*(.*?)(?:\s*\(CMU Intro to Database Systems\))?$", base)
    if cmu:
        number = cmu.group(1).upper()
        if number.isdigit():
            number = f"{int(number):02d}"
        title = re.sub(r"\s{2,}", " - ", cmu.group(2)).strip(" -:：")
        title = re.sub(r"\s+", " ", title)
        return sanitize_filename(f"Lecture {number} - {title}")

    return sanitize_filename(re.sub(r"\s*\[[^\]]+\].*$", "", base).strip())


def video_id(path: Path) -> str:
    match = re.search(r"\[([A-Za-z0-9_-]{11})\]", path.name)
    if not match:
        raise ValueError(f"Cannot find YouTube id in {path.name}")
    return match.group(1)


def ffmpeg_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", r"\:")


def write_ass(json_path: Path, ass_path: Path, title: str) -> None:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    events: list[str] = []
    for item in payload["segments"]:
        zh = ass_escape(item.get("translated_text") or item.get("text") or "")
        en = ass_escape(item.get("text") or "")
        text = rf"{{\rZh}}{zh}\N{{\rEn}}{en}"
        events.append(
            "Dialogue: 0,"
            f"{ass_time(float(item['start']))},"
            f"{ass_time(float(item['end']))},"
            f"Zh,,0,0,0,,{text}"
        )

    ass = f"""[Script Info]
Title: {title} Bilingual Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Zh,KaiTi,52,&H00F4F4F4,&H000000FF,&H00111111,&H99000000,0,0,0,0,100,100,0,0,1,3,0,2,80,80,44,1
Style: En,Georgia,36,&H00D7D7D7,&H000000FF,&H00111111,&H99000000,0,0,0,0,100,100,0,0,1,2,0,2,80,80,44,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{chr(10).join(events)}
"""
    ass_path.write_text(ass, encoding="utf-8-sig")


def run(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd)


def is_complete_file(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def mux_soft_subbed(video: Path, ass: Path, mkv: Path, font_zh: Path, font_en: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i",
        str(video),
        "-i",
        str(ass),
        "-map",
        "0",
        "-map",
        "1",
        "-c",
        "copy",
        "-c:s",
        "ass",
        "-metadata:s:s:0",
        "language=chi",
        "-metadata:s:s:0",
        "title=Chinese / English",
        "-disposition:s:0",
        "default",
    ]
    attachments: list[tuple[Path, str]] = []
    if font_zh.exists():
        attachments.append((font_zh, "application/x-truetype-font"))
    if font_en.exists():
        attachments.append((font_en, "application/x-truetype-font"))
    for index, (font, mimetype) in enumerate(attachments):
        command.extend(
            [
                "-attach",
                str(font),
                f"-metadata:s:t:{index}",
                f"filename={font.name}",
                f"-metadata:s:t:{index}",
                f"mimetype={mimetype}",
            ]
        )
    command.append(str(mkv))
    run(command)


def mux_hard_subbed(
    video: Path,
    ass: Path,
    mkv: Path,
    font_dir: Path,
    codec: str,
    quality: str,
    preset: str,
) -> None:
    filter_arg = f"subtitles=filename='{ass.name}':fontsdir='{ffmpeg_filter_path(font_dir)}'"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i",
        str(video),
        "-vf",
        filter_arg,
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-sn",
        "-c:v",
        codec,
        "-global_quality",
        quality,
        "-preset",
        preset,
        "-c:a",
        "copy",
        str(mkv),
    ]
    run(command, cwd=ass.parent)


def prepare_dirs(course_dir: Path, font_zh: Path, font_en: Path) -> dict[str, Path]:
    dirs = {
        "source": course_dir / "source-videos",
        "subtitles": course_dir / "subtitles",
        "soft": course_dir / "soft-subbed-mkv",
        "hard": course_dir / "hard-subbed-mkv",
        "fonts": course_dir / "fonts",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    for font in (font_zh, font_en):
        if font.exists():
            shutil.copy2(font, dirs["fonts"] / font.name)
    return dirs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package course videos with bilingual subtitles.")
    parser.add_argument("--videos-dir", type=Path, default=ROOT / "videos")
    parser.add_argument("--outputs-dir", type=Path, default=ROOT / "outputs")
    parser.add_argument("--course-dir", type=Path, default=DEFAULT_COURSE_DIR)
    parser.add_argument("--course-name", default=None)
    parser.add_argument("--font-zh", type=Path, default=FONT_ZH)
    parser.add_argument("--font-en", type=Path, default=FONT_EN)
    parser.add_argument("--hard-codec", default="av1_qsv")
    parser.add_argument("--hard-quality", default="30")
    parser.add_argument("--hard-preset", default="medium")
    parser.add_argument("--skip-soft-subbed", action="store_true")
    parser.add_argument("--skip-hard-subbed", action="store_true")
    return parser


def main() -> None:
    configure_stdio()
    args = build_parser().parse_args()
    videos_dir = args.videos_dir.resolve()
    outputs_dir = args.outputs_dir.resolve()
    course_dir = args.course_dir.resolve()
    course_name = args.course_name or course_dir.name
    dirs = prepare_dirs(course_dir, args.font_zh, args.font_en)

    json_by_id = {video_id(path): path for path in outputs_dir.glob("*.zh-CN.json")}
    source_srt_by_id = {video_id(path): path for path in outputs_dir.glob("*.source.srt")}
    zh_srt_by_id = {video_id(path): path for path in outputs_dir.glob("*.zh-CN.srt")}
    bilingual_srt_by_id = {video_id(path): path for path in outputs_dir.glob("*.bilingual.srt")}

    videos = sorted(videos_dir.glob("*.*"), key=lambda path: simplify_title(path.name))
    if not videos:
        raise RuntimeError(f"No source videos found in {videos_dir}")

    for video in videos:
        vid = video_id(video)
        simple = simplify_title(video.name)
        if vid not in json_by_id:
            raise RuntimeError(f"Missing translated JSON for video id {vid}: {video.name}")

        print(f"Packaging {simple}", flush=True)
        source_video = dirs["source"] / f"{simple}{video.suffix.lower()}"
        ass_path = dirs["subtitles"] / f"{simple}.bilingual.ass"
        soft_mkv = dirs["soft"] / f"{simple}.soft-subbed.mkv"
        hard_mkv = dirs["hard"] / f"{simple}.hard-subbed.mkv"

        if not source_video.exists() or source_video.stat().st_size != video.stat().st_size:
            shutil.copy2(video, source_video)
        write_ass(json_by_id[vid], ass_path, course_name)

        for suffix, mapping in (
            (".zh-CN.srt", zh_srt_by_id),
            (".source.srt", source_srt_by_id),
            (".bilingual.srt", bilingual_srt_by_id),
        ):
            if vid in mapping:
                shutil.copy2(mapping[vid], dirs["subtitles"] / f"{simple}{suffix}")

        if not args.skip_soft_subbed and not is_complete_file(soft_mkv):
            mux_soft_subbed(source_video, ass_path, soft_mkv, args.font_zh, args.font_en)
        if not args.skip_hard_subbed and not is_complete_file(hard_mkv):
            mux_hard_subbed(
                source_video,
                ass_path,
                hard_mkv,
                dirs["fonts"],
                args.hard_codec,
                args.hard_quality,
                args.hard_preset,
            )


if __name__ == "__main__":
    main()
