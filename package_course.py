from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
OUTPUTS = ROOT / "outputs"
COURSE_DIR = ROOT / "MIT 6.S184 Flow Matching and Diffusion Models (2026)"
FONT_ZH = Path(r"C:\Windows\Fonts\simkai.ttf")
FONT_EN = Path(r"C:\Windows\Fonts\georgia.ttf")


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


def simplify_title(name: str) -> str:
    match = re.search(r"(Lecture\s+\d+[A-Z]?)\s*(?:-|：|:)?\s*(.*?)\s*\(2026\)", name)
    if not match:
        return re.sub(r"\s*\[[^\]]+\].*$", "", name).strip()
    lecture = match.group(1).strip()
    title = re.sub(r"\s+", " ", match.group(2)).strip(" -:：")
    title = title.replace("Neural networks", "Neural Networks")
    return f"{lecture} - {title}"


def video_id(path: Path) -> str:
    match = re.search(r"\[([A-Za-z0-9_-]{11})\]", path.name)
    if not match:
        raise ValueError(f"Cannot find YouTube id in {path.name}")
    return match.group(1)


def write_ass(json_path: Path, ass_path: Path) -> None:
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
Title: MIT 6.S184 Bilingual Subtitles
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


def run_ffmpeg(video: Path, ass: Path, mkv: Path) -> None:
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
        "title=中文 / English",
        "-disposition:s:0",
        "default",
    ]
    attachments: list[tuple[Path, str]] = []
    if FONT_ZH.exists():
        attachments.append((FONT_ZH, "application/x-truetype-font"))
    if FONT_EN.exists():
        attachments.append((FONT_EN, "application/x-truetype-font"))
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
    subprocess.run(command, check=True)


def main() -> None:
    COURSE_DIR.mkdir(parents=True, exist_ok=True)
    json_by_id = {video_id(path): path for path in OUTPUTS.glob("*.zh-CN.json")}
    source_srt_by_id = {video_id(path): path for path in OUTPUTS.glob("*.source.srt")}
    zh_srt_by_id = {video_id(path): path for path in OUTPUTS.glob("*.zh-CN.srt")}
    bilingual_srt_by_id = {video_id(path): path for path in OUTPUTS.glob("*.bilingual.srt")}

    for video in sorted(VIDEOS.glob("*.mp4"), key=lambda path: simplify_title(path.name)):
        vid = video_id(video)
        simple = simplify_title(video.name)
        print(f"Packaging {simple}")
        simple_mp4 = COURSE_DIR / f"{simple}.mp4"
        ass_path = COURSE_DIR / f"{simple}.bilingual.ass"
        mkv_path = COURSE_DIR / f"{simple}.bilingual.mkv"

        if not simple_mp4.exists() or simple_mp4.stat().st_size != video.stat().st_size:
            shutil.copy2(video, simple_mp4)
        write_ass(json_by_id[vid], ass_path)

        for suffix, mapping in (
            (".zh-CN.srt", zh_srt_by_id),
            (".source.srt", source_srt_by_id),
            (".bilingual.srt", bilingual_srt_by_id),
        ):
            if vid in mapping:
                shutil.copy2(mapping[vid], COURSE_DIR / f"{simple}{suffix}")

        run_ffmpeg(simple_mp4, ass_path, mkv_path)


if __name__ == "__main__":
    main()
