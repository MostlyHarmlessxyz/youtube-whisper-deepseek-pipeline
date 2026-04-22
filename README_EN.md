# YouTube Whisper DeepSeek Pipeline

A local pipeline for translating YouTube lecture videos into Chinese subtitles. It downloads audio, transcribes with Whisper, translates subtitle segments with the DeepSeek API, writes source/translated/bilingual subtitles, and can package styled bilingual ASS subtitles into MKV files.

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
- MIT 6.S184 course profile with glossary and ASR cleanup.
- QA command for missing translations and terminology drift.
- Best-quality video download and MKV packaging with embedded ASS subtitles and fonts.

## Target Use Case

This project was built for MIT 6.S184: Introduction to Flow Matching and Diffusion Models, but it can also translate general English YouTube videos.

The MIT course profile handles terms such as:

- `flow matching` -> `流匹配`
- `score matching` -> `score matching / 分数匹配`
- `classifier-free guidance` -> `无分类器引导`
- `Fokker-Planck equation` -> `Fokker-Planck 方程`
- `probability path` -> `概率路径`
- `vector field` -> `向量场`
- `SDE / ODE / CTMC / DiT / U-Net / VAE`

It also corrects common ASR drift such as `floor matching` -> `flow matching`.

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

This downloads a Windows Vulkan build of `whisper.cpp` and the `ggml-large-v3-turbo-q5_0.bin` model.

GPU transcription:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --backend whispercpp-vulkan --source-language en --target zh-CN
```

## MIT 6.S184 Preset

Single video:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --mit-diffusion
```

Batch:

```powershell
.\.venv\Scripts\yt-translate.exe --file urls.txt --mit-diffusion
```

## General Usage

Single video:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --target zh-CN
```

Local media:

```powershell
.\.venv\Scripts\yt-translate.exe ".\downloads\sample.webm" --target zh-CN
```

Transcription only:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --skip-translation
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
.\.venv\Scripts\yt-translate.exe --qa "outputs\xxx.zh-CN.json" --profile mit-diffusion
```

The QA command reports missing translations and suspicious terms.

## Download Best-Quality Videos

After subtitles are done:

```powershell
.\download_best_video.ps1 -UrlFile urls.txt -OutputDir videos
```

## Package Course Files

```powershell
.\.venv\Scripts\python.exe package_course.py
```

This creates:

```txt
MIT 6.S184 Flow Matching and Diffusion Models (2026)/
```

Each lecture gets simplified MP4, SRT, ASS, and MKV files. The MKV contains the original video/audio, an ASS subtitle track, and embedded `simkai.ttf` and `georgia.ttf` font attachments.

## Repository Safety

Do not commit:

- `.env`
- API keys
- `.venv/`
- `models/`
- `tools/`
- `downloads/`
- `outputs/`
- `cache/`
- `logs/`
- `videos/`
- packaged MKV/MP4 course files

These are ignored by `.gitignore`.

## License

No license has been declared yet. Add a `LICENSE` file before public release if you want this to be an open-source project.

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [DeepSeek API](https://api-docs.deepseek.com/)

