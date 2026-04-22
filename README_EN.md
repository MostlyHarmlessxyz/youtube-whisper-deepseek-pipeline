# YouTube Whisper DeepSeek Pipeline

A local pipeline for translating YouTube videos into Chinese subtitles. It downloads audio, transcribes with Whisper, translates subtitle segments with the DeepSeek API, and writes source, translated, and bilingual subtitles.

Chinese documentation is the default: [README.md](README.md)

## Features

- YouTube URL or local media input.
- Audio download with `yt-dlp`.
- Audio preprocessing with `ffmpeg`.
- CPU transcription via `faster-whisper`.
- GPU transcription via `whisper.cpp + Vulkan`.
- DeepSeek OpenAI-compatible API translation.
- Checkpointed translation for resumable long videos.
- Outputs JSON, SRT, VTT, and bilingual subtitles.
- QA command for missing translations and suspicious text.
- Best-quality video download after subtitle generation.

## Requirements

- Windows + PowerShell
- Python 3.10
- `ffmpeg`
- Git
- DeepSeek API key

Optional but recommended:

- Intel Arc or another Vulkan-capable GPU
- `deno` for more robust YouTube JS challenge handling in `yt-dlp`

## Quick Start

Install Python dependencies:

```powershell
.\setup.ps1
```

If your PowerShell profile prints completion warnings in non-interactive commands, run setup with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

Create `.env` from `.env.example` and fill your API key:

```dotenv
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

Check the environment:

```powershell
.\.venv\Scripts\yt-translate.exe --doctor
```

## GPU Setup

```powershell
.\setup_gpu.ps1
```

This script installs or checks `deno`, downloads a Windows Vulkan build of `whisper.cpp`, downloads the default GGML Whisper model, and checks available Vulkan devices.

GPU transcription:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --backend whispercpp-vulkan --source-language en --target zh-CN
```

## Usage

Single YouTube video:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --target zh-CN
```

Batch:

```powershell
.\.venv\Scripts\yt-translate.exe --file urls.txt --target zh-CN --keep-going
```

`urls.txt` format:

```txt
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
```

Local media:

```powershell
.\.venv\Scripts\yt-translate.exe ".\downloads\sample.webm" --target zh-CN
```

Transcription only:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --skip-translation
```

Write WebVTT:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --target zh-CN --vtt
```

## Outputs

- `downloads/`: downloaded media
- `cache/`: 16 kHz mono WAV and intermediate files
- `outputs/*.source.json`: source transcription
- `outputs/*.source.srt`: source subtitles
- `outputs/*.zh-CN.json`: translated segments
- `outputs/*.zh-CN.srt`: Chinese subtitles
- `outputs/*.bilingual.srt`: bilingual subtitles
- `outputs/*.vtt`: WebVTT subtitles

## QA

```powershell
.\.venv\Scripts\yt-translate.exe --qa "outputs\xxx.zh-CN.json"
```

The QA command reports segment counts, missing translations, and suspicious text.

## Download Best-Quality Videos

After subtitles are done:

```powershell
.\download_best_video.ps1 -UrlFile urls.txt -OutputDir videos
```

The script uses:

```txt
bv*+ba/b
```

and tries to merge the result as MP4.

## Performance Notes

CPU fallback:

```powershell
.\.venv\Scripts\yt-translate.exe "URL" --model medium --compute-type int8 --target zh-CN
```

Recommended GPU path:

```powershell
.\.venv\Scripts\yt-translate.exe "URL" --backend whispercpp-vulkan --source-language en --target zh-CN --beam-size 1
```

Notes:

- `faster-whisper medium int8 CPU` is stable but slower.
- `whisper.cpp Vulkan` is usually faster on a Vulkan-capable discrete GPU.
- For long videos, keep checkpoints and avoid `--overwrite` unless you really want a full rerun.

## Project Structure

```txt
youtube_translator/
  audio.py          # ffmpeg audio conversion
  cli.py            # CLI entry point
  doctor.py         # environment diagnostics
  downloader.py     # yt-dlp download logic
  pipeline.py       # main pipeline
  profiles.py       # profiles and glossary rules
  qa.py             # QA checks
  subtitles.py      # SRT/VTT/JSON output
  transcriber.py    # faster-whisper backend
  translator.py     # DeepSeek translation
  whispercpp.py     # whisper.cpp Vulkan backend
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [DeepSeek API](https://api-docs.deepseek.com/)
