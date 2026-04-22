# YouTube Whisper DeepSeek Pipeline

This project downloads YouTube audio, transcribes it with `faster-whisper`, translates subtitle segments with the DeepSeek OpenAI-compatible API, and writes source, translated, and bilingual subtitles.

## Hardware Defaults

For this i5-13400 + 64 GB RAM machine, the default path uses CPU `int8` inference with high thread count. This is the most reliable Windows path today. Intel Arc A750 acceleration is kept configurable through `--device` and future backends, but the stable first-run backend is `faster-whisper` on CPU.

Recommended first run:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --model medium --target zh-CN
```

For faster but lower quality transcription:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --model small --target zh-CN
```

For higher quality on long videos:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --model large-v3 --target zh-CN --batch-size 18
```

Intel Arc A750 Vulkan backend:

```powershell
.\setup_gpu.ps1
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --backend whispercpp-vulkan --target zh-CN --source-language en
```

MIT 6.S184 diffusion course preset:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --mit-diffusion
```

Batch translate MIT 6.S184 videos:

```powershell
.\.venv\Scripts\yt-translate.exe --file urls.txt --mit-diffusion
```

Download original videos at best quality after subtitles are done:

```powershell
.\download_best_video.ps1 -UrlFile urls.txt -OutputDir videos
```

## Setup

```powershell
.\setup.ps1
```

Edit `.env`:

```dotenv
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

If your PowerShell profile prints completion warnings in non-interactive commands, run setup with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

## Usage

Single video:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --target zh-CN
```

Local file:

```powershell
.\.venv\Scripts\yt-translate.exe ".\downloads\sample.webm" --target zh-CN
```

Batch:

```powershell
.\.venv\Scripts\yt-translate.exe --file urls.txt --target zh-CN
```

Transcription only:

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --skip-translation
```

## Outputs

- `downloads/`: downloaded media
- `cache/`: 16 kHz mono WAV files for Whisper
- `outputs/*.source.srt`: original subtitles
- `outputs/*.zh-CN.srt`: translated subtitles
- `outputs/*.bilingual.srt`: translated text plus source text
- `outputs/*.json`: structured segments and metadata

## Performance Notes

- `--model medium` is the default balance for this CPU.
- `--model large-v3` gives better recognition but is much slower on CPU.
- `--compute-type int8` is recommended for CPU throughput.
- `--cpu-threads` defaults to most logical cores while leaving a small reserve for the OS.
- `--translation-concurrency 3` keeps DeepSeek API calls parallel without being too aggressive.
- If a run is interrupted, existing transcript/translation JSON files are reused unless `--overwrite` is passed.
- `--backend whispercpp-vulkan` uses `tools/whisper.cpp-vulkan/whisper-cli.exe` and `models/ggml-large-v3-turbo-q5_0.bin` by default.
- `setup_gpu.ps1` installs Deno for more robust YouTube extraction, downloads a Windows Vulkan build of `whisper.cpp`, and downloads the quantized `large-v3-turbo` GGML model.
- `--mit-diffusion` enables the Intel Arc Vulkan backend, English source language, Chinese target language, VTT output, DeepSeek checkpointing, and a course glossary/profile for MIT 6.S184.
- The MIT course profile corrects common ASR/translation drift such as `floor matching` -> `flow matching` / `流匹配`, and guides DeepSeek with course terms including SDE, ODE, Fokker-Planck, probability path, vector field, score matching, classifier-free guidance, DiT, U-Net, VAE, and CTMC.
