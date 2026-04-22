# YouTube Whisper DeepSeek Pipeline

面向中文用户的本地 YouTube 视频翻译流水线：下载音频，使用 Whisper 转写，调用 DeepSeek API 翻译，生成原文字幕、中文字幕和双语字幕。

> 默认文档为中文。English documentation: [README_EN.md](README_EN.md)

## 特性

- 支持 YouTube URL 或本地媒体文件输入。
- 使用 `yt-dlp` 下载音频，使用 `ffmpeg` 转为 16 kHz mono WAV。
- 支持 `faster-whisper` CPU 后端，适合作为稳定 fallback。
- 支持 `whisper.cpp + Vulkan` 后端，适合 Intel Arc / AMD / NVIDIA 等 Vulkan GPU。
- 使用 DeepSeek OpenAI-compatible API 分批翻译字幕。
- 支持翻译 checkpoint，长视频中断后可以续跑。
- 输出 `.json`、`.srt`、`.vtt` 和双语 `.srt`。
- 提供 QA 检查，用于发现缺失翻译和常见异常。
- 可在字幕完成后单独下载最高画质原视频。

## 环境要求

- Windows + PowerShell
- Python 3.10
- `ffmpeg`
- Git
- DeepSeek API Key

可选但推荐：

- Intel Arc 或其他支持 Vulkan 的 GPU
- `deno`，用于提升 `yt-dlp` 处理 YouTube JS challenge 的稳定性

## 快速开始

### 1. 安装 Python 依赖

```powershell
.\setup.ps1
```

如果你的 PowerShell profile 在非交互命令里输出补全警告，可以使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

### 2. 配置 DeepSeek

复制 `.env.example` 为 `.env`，填入 API Key：

```dotenv
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 检查环境

```powershell
.\.venv\Scripts\yt-translate.exe --doctor
```

## GPU 后端

初始化 Vulkan Whisper 后端：

```powershell
.\setup_gpu.ps1
```

该脚本会：

- 安装或检查 `deno`
- 下载 Windows Vulkan 版 `whisper.cpp`
- 下载默认 GGML Whisper 模型
- 检查 Vulkan 设备

使用 GPU 转写：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --backend whispercpp-vulkan --source-language en --target zh-CN
```

## 通用用法

单个 YouTube 视频：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --target zh-CN
```

批量视频：

```powershell
.\.venv\Scripts\yt-translate.exe --file urls.txt --target zh-CN --keep-going
```

`urls.txt` 格式：

```txt
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
```

本地文件：

```powershell
.\.venv\Scripts\yt-translate.exe ".\downloads\sample.webm" --target zh-CN
```

仅转写，不翻译：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --skip-translation
```

输出 WebVTT：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --target zh-CN --vtt
```

## 输出结构

默认输出：

- `downloads/`: 下载的音频或媒体文件
- `cache/`: 16 kHz mono WAV 和中间文件
- `outputs/*.source.json`: 原文转写结构化结果
- `outputs/*.source.srt`: 原文字幕
- `outputs/*.zh-CN.json`: 翻译结构化结果
- `outputs/*.zh-CN.srt`: 中文字幕
- `outputs/*.bilingual.srt`: 双语字幕
- `outputs/*.vtt`: WebVTT 字幕

## QA 检查

检查某个翻译 JSON：

```powershell
.\.venv\Scripts\yt-translate.exe --qa "outputs\xxx.zh-CN.json"
```

QA 会报告字幕段数、缺失翻译数量和可疑文本。

## 下载最高画质原视频

字幕完成后，可单独下载最高画质视频：

```powershell
.\download_best_video.ps1 -UrlFile urls.txt -OutputDir videos
```

该脚本使用：

```txt
bv*+ba/b
```

并尽量合并为 MP4。

## 性能建议

CPU fallback：

```powershell
.\.venv\Scripts\yt-translate.exe "URL" --model medium --compute-type int8 --target zh-CN
```

GPU 推荐：

```powershell
.\.venv\Scripts\yt-translate.exe "URL" --backend whispercpp-vulkan --source-language en --target zh-CN --beam-size 1
```

经验值：

- `faster-whisper medium int8 CPU` 稳定但慢。
- `whisper.cpp Vulkan` 在支持 Vulkan 的独立显卡上通常更快。
- 长视频建议保留 checkpoint，不要使用 `--overwrite`，除非确实要重跑。

## 项目结构

```txt
youtube_translator/
  audio.py          # ffmpeg 音频转码
  cli.py            # CLI 入口
  doctor.py         # 环境诊断
  downloader.py     # yt-dlp 下载
  pipeline.py       # 主流水线
  profiles.py       # profile 和术语表
  qa.py             # QA 检查
  subtitles.py      # SRT/VTT/JSON 输出
  transcriber.py    # faster-whisper 后端
  translator.py     # DeepSeek 翻译
  whispercpp.py     # whisper.cpp Vulkan 后端
```

## 许可证

本项目使用 MIT License。详见 [LICENSE](LICENSE)。

## 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [DeepSeek API](https://api-docs.deepseek.com/)
