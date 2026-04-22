# YouTube Whisper DeepSeek Pipeline

面向中文用户的 YouTube 课程视频翻译流水线：下载音频，使用 Whisper 转写，调用 DeepSeek API 翻译，生成原文/中文字幕/双语字幕，并可将双语 ASS 字幕和字体封装进 MKV。

> 默认文档为中文。English documentation: [README_EN.md](README_EN.md)

## 特性

- YouTube URL 或本地媒体文件输入。
- `yt-dlp` 下载音频，`ffmpeg` 转为 16 kHz mono WAV。
- `faster-whisper` CPU 后端，适合作为稳定 fallback。
- `whisper.cpp + Vulkan` 后端，适合 Intel Arc / AMD / NVIDIA 等 Vulkan GPU。
- DeepSeek OpenAI-compatible API 分批翻译。
- 翻译 checkpoint，支持中断后续跑。
- 输出 `.json`、`.srt`、`.vtt`、双语 `.srt`。
- 课程 profile：内置 MIT 6.S184 Flow Matching and Diffusion Models 术语表和 ASR 纠错。
- QA 检查：发现缺失翻译和常见术语漂移。
- 可下载最高画质原视频，并封装双语 ASS 字幕和字体到 MKV。

## 适用场景

这个项目最初为 MIT 6.S184: Introduction to Flow Matching and Diffusion Models 课程视频构建，但也可以用于普通英文 YouTube 视频翻译。

内置 MIT 课程 profile 会处理这类术语：

- `flow matching` -> `流匹配`
- `score matching` -> `score matching / 分数匹配`
- `classifier-free guidance` -> `无分类器引导`
- `Fokker-Planck equation` -> `Fokker-Planck 方程`
- `probability path` -> `概率路径`
- `vector field` -> `向量场`
- `SDE / ODE / CTMC / DiT / U-Net / VAE`

它还会修正常见 ASR 误听，例如 `floor matching` -> `flow matching`。

## 环境要求

- Windows + PowerShell
- Python 3.10
- `ffmpeg`
- Git
- DeepSeek API Key

可选但推荐：

- Intel Arc / 其他支持 Vulkan 的 GPU
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

- 安装/检查 `deno`
- 下载 Windows Vulkan 版 `whisper.cpp`
- 下载 `ggml-large-v3-turbo-q5_0.bin`
- 检查 Vulkan 设备

使用 GPU 转写：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --backend whispercpp-vulkan --source-language en --target zh-CN
```

## MIT 6.S184 课程模式

单个视频：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --mit-diffusion
```

批量视频：

```powershell
.\.venv\Scripts\yt-translate.exe --file urls.txt --mit-diffusion
```

`urls.txt` 格式：

```txt
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
```

`--mit-diffusion` 会自动启用：

- `whispercpp-vulkan`
- 英文源语言
- 简体中文目标语言
- VTT 输出
- MIT 课程术语表
- ASR/翻译术语后处理
- checkpoint 续跑

## 通用用法

单个 YouTube 视频：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --target zh-CN
```

本地文件：

```powershell
.\.venv\Scripts\yt-translate.exe ".\downloads\sample.webm" --target zh-CN
```

仅转写，不翻译：

```powershell
.\.venv\Scripts\yt-translate.exe "https://www.youtube.com/watch?v=VIDEO_ID" --skip-translation
```

## 输出结构

默认输出：

- `downloads/`: 下载的音频/媒体文件
- `cache/`: 16 kHz mono WAV 和中间文件
- `outputs/*.source.json`: 原文转写结构化结果
- `outputs/*.source.srt`: 原文字幕
- `outputs/*.zh-CN.json`: 翻译结构化结果
- `outputs/*.zh-CN.srt`: 中文字幕
- `outputs/*.bilingual.srt`: 双语字幕
- `outputs/*.vtt`: WebVTT 字幕

这些目录默认被 `.gitignore` 排除。

## QA 检查

检查某个翻译 JSON：

```powershell
.\.venv\Scripts\yt-translate.exe --qa "outputs\xxx.zh-CN.json" --profile mit-diffusion
```

QA 会报告：

- 字幕段数
- 缺失翻译数量
- 可疑术语，例如 `floor matching`、`楼层匹配`、`地板匹配`

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

## 整理和封装课程文件

将视频、字幕整理到同一个课程文件夹，并生成内嵌双语 ASS 字幕和字体的 MKV：

```powershell
.\.venv\Scripts\python.exe package_course.py
```

输出文件夹：

```txt
MIT 6.S184 Flow Matching and Diffusion Models (2026)/
```

每集会生成：

- `Lecture XX - Title.mp4`
- `Lecture XX - Title.zh-CN.srt`
- `Lecture XX - Title.source.srt`
- `Lecture XX - Title.bilingual.srt`
- `Lecture XX - Title.bilingual.ass`
- `Lecture XX - Title.bilingual.mkv`

ASS 字幕样式：

- 第一行中文
- 第二行英文
- 中文字体：楷体 / `simkai.ttf`
- 英文字体：Georgia
- 字体作为 MKV attachment 内嵌

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
- `whisper.cpp Vulkan + large-v3-turbo-q5_0` 在 Intel Arc A750 上速度明显更好。
- 长视频建议保留 checkpoint，不要使用 `--overwrite`，除非确实要重跑。

## 安全和仓库边界

不要提交这些内容：

- `.env`
- API Key
- `.venv/`
- `models/`
- `tools/`
- `downloads/`
- `outputs/`
- `cache/`
- `logs/`
- `videos/`
- 课程 MKV/MP4 成品

这些已经在 `.gitignore` 中排除。

## 项目结构

```txt
youtube_translator/
  audio.py          # ffmpeg 音频转码
  cli.py            # CLI 入口
  doctor.py         # 环境诊断
  downloader.py     # yt-dlp 下载
  pipeline.py       # 主流水线
  profiles.py       # 课程 profile 和术语表
  qa.py             # QA 检查
  subtitles.py      # SRT/VTT/JSON 输出
  transcriber.py    # faster-whisper 后端
  translator.py     # DeepSeek 翻译
  whispercpp.py     # whisper.cpp Vulkan 后端
```

## 许可证

当前仓库尚未声明许可证。开源发布前建议添加 `LICENSE`，例如 MIT License。

## 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [DeepSeek API](https://api-docs.deepseek.com/)

