from __future__ import annotations

from pathlib import Path

from .models import DownloadResult
from .utils import safe_stem, stable_id


def download_audio(url: str, download_dir: Path, skip_download: bool = False) -> DownloadResult:
    from yt_dlp import YoutubeDL

    download_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(download_dir / "%(title).160B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "windowsfilenames": True,
        "quiet": False,
        "no_warnings": False,
        "skip_download": skip_download,
        "js_runtimes": {"deno": {}},
        "remote_components": {"ejs:github"},
        "continuedl": True,
        "retries": 20,
        "fragment_retries": 20,
        "extractor_retries": 5,
        "socket_timeout": 30,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=not skip_download)
        if info is None:
            raise RuntimeError("yt-dlp did not return video metadata.")
        title = safe_stem(info.get("title") or "video")
        video_id = str(info.get("id") or stable_id(url))
        prepared = Path(ydl.prepare_filename(info))
        requested = info.get("requested_downloads") or []
        media_path = Path(requested[0]["filepath"]) if requested else prepared

    return DownloadResult(
        source=url,
        title=title,
        video_id=video_id,
        media_path=media_path,
        work_id=f"{safe_stem(title)} [{video_id}]",
    )
