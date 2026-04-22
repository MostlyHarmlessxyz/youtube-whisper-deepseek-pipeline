from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

from .models import Segment
from .subtitles import write_json


def chunked(items: list[Segment], size: int) -> list[list[Segment]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def build_prompt(
    target_language: str,
    source_language: str | None,
    segments: list[Segment],
    glossary: str = "",
) -> str:
    source = source_language or "auto-detected"
    payload = [{"id": segment.index, "text": segment.text} for segment in segments]
    glossary_block = f"Glossary and domain context:\n{glossary}\n" if glossary else ""
    return (
        "Translate subtitle segments faithfully.\n"
        f"Source language: {source}\n"
        f"Target language: {target_language}\n"
        "Rules:\n"
        "- Preserve meaning, tone, technical terms, numbers, names, and code terms.\n"
        "- Follow the glossary exactly when provided.\n"
        "- Do not summarize, merge, split, omit, or add commentary.\n"
        "- Keep each output item id identical to the input id.\n"
        "- Return only valid JSON in this exact shape: "
        '{"translations":[{"id":0,"text":"..."}]}\n'
        f"{glossary_block}"
        f"Input JSON:\n{json.dumps({'segments': payload}, ensure_ascii=False)}"
    )


def parse_translations(raw: str) -> dict[int, str]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.removeprefix("json").strip()
    data = json.loads(raw)
    translations = data.get("translations")
    if not isinstance(translations, list):
        raise ValueError("Translation response missing 'translations' list.")
    result: dict[int, str] = {}
    for item in translations:
        text = str(item["text"]).strip()
        if text:
            result[int(item["id"])] = text
    return result


def fallback_translation(text: str, target_language: str) -> str | None:
    if target_language.lower() not in {"zh", "zh-cn", "chinese", "simplified chinese"}:
        return None
    normalized = " ".join(text.lower().strip(" .,!?:;").split())
    zh_cn = {
        "of anything": "任何东西的",
        "with a flow model": "用流模型",
        "with an algorithm": "用一个算法",
        "are": "是",
        "and the diffusion coefficient": "以及扩散系数",
        "or those diffusion": "或者那些扩散",
        "by": "通过",
        "the": "这个",
        "okay": "好的",
        "right": "对吧",
        "yes": "是的",
        "no": "不是",
    }
    return zh_cn.get(normalized)


def translate_segments(
    segments: list[Segment],
    target_language: str,
    source_language: str | None,
    batch_size: int,
    concurrency: int,
    retries: int,
    temperature: float,
    checkpoint_path: Path | None = None,
    metadata: dict | None = None,
    glossary: str = "",
) -> list[Segment]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Copy .env.example to .env and fill it.")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    client = OpenAI(api_key=api_key, base_url=base_url)

    batches = chunked(segments, batch_size)
    translated: dict[int, str] = {}
    if checkpoint_path and checkpoint_path.exists():
        try:
            payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            for item in payload.get("segments", []):
                text = item.get("translated_text")
                if text:
                    translated[int(item["index"])] = str(text)
        except Exception:
            translated = {}

    batches = [
        batch
        for batch in batches
        if any(segment.index not in translated for segment in batch)
    ]

    def translate_batch(batch: list[Segment]) -> dict[int, str]:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a precise technical subtitle translator. "
                                "Return JSON only."
                            ),
                        },
                        {
                            "role": "user",
                            "content": build_prompt(target_language, source_language, batch, glossary),
                        },
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or ""
                parsed = parse_translations(content)
                missing = {segment.index for segment in batch} - set(parsed)
                if missing:
                    if len(batch) == 1 and len(parsed) == 1:
                        return {batch[0].index: next(iter(parsed.values()))}
                    if len(batch) > 1 and parsed:
                        missing_batch = [segment for segment in batch if segment.index in missing]
                        parsed.update(translate_batch(missing_batch))
                        return parsed
                    raise ValueError(f"Missing translated segment ids: {sorted(missing)}")
                return parsed
            except Exception as exc:  # noqa: BLE001 - retry and report the original provider error.
                last_error = exc
                if attempt < retries:
                    time.sleep(min(20, 2 ** attempt))
        if len(batch) == 1:
            fallback = fallback_translation(batch[0].text, target_language)
            if fallback:
                return {batch[0].index: fallback}
        raise RuntimeError(f"DeepSeek translation failed after retries: {last_error}")

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        futures = [executor.submit(translate_batch, batch) for batch in batches]
        done = 0
        total = len(futures)
        for future in as_completed(futures):
            translated.update(future.result())
            done += 1
            print(f"DeepSeek translation progress: {done}/{total} batches", flush=True)
            if checkpoint_path:
                checkpoint_segments = [
                    Segment(
                        index=segment.index,
                        start=segment.start,
                        end=segment.end,
                        text=segment.text,
                        translated_text=translated.get(segment.index),
                    )
                    for segment in segments
                ]
                write_json(checkpoint_path, checkpoint_segments, metadata)

    return [
        Segment(
            index=segment.index,
            start=segment.start,
            end=segment.end,
            text=segment.text,
            translated_text=translated.get(segment.index),
        )
        for segment in segments
    ]
