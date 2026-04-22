from __future__ import annotations

import json
import re
from pathlib import Path

from .profiles import get_profile


DEFAULT_SUSPICIOUS = (
    r"\bfloor matching\b",
    r"\bfloor model\b",
    r"楼层匹配",
    r"地板匹配",
    r"分类器免费指导",
)


def qa_report(path: Path, profile_name: str | None = None) -> None:
    profile = get_profile(profile_name)
    payload = json.loads(path.read_text(encoding="utf-8"))
    segments = payload.get("segments", [])
    missing = [item.get("index") for item in segments if not item.get("translated_text") and "translated_text" in item]
    text = path.read_text(encoding="utf-8")

    suspicious = list(DEFAULT_SUSPICIOUS)
    if profile:
        suspicious.extend(pattern for pattern, _ in profile.asr_corrections)

    print(f"QA file: {path}")
    print(f"Segments: {len(segments)}")
    print(f"Missing translations: {len(missing)}")
    if missing:
        print(f"Missing ids: {missing[:50]}")

    hits: list[str] = []
    for pattern in suspicious:
        count = len(re.findall(pattern, text, flags=re.IGNORECASE))
        if count:
            hits.append(f"{pattern}: {count}")
    print(f"Suspicious terms: {len(hits)}")
    for hit in hits[:50]:
        print(f"- {hit}")

