from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Segment


@dataclass(frozen=True, slots=True)
class CourseProfile:
    name: str
    prompt_context: str
    glossary: tuple[tuple[str, str], ...]
    asr_corrections: tuple[tuple[str, str], ...]
    translation_corrections: tuple[tuple[str, str], ...]


MIT_DIFFUSION_PROFILE = CourseProfile(
    name="mit-diffusion",
    prompt_context=(
        "Domain: MIT 6.S184, Introduction to Flow Matching and Diffusion Models. "
        "Translate as technical lecture subtitles for Chinese readers. Keep math symbols, "
        "variable names, and English acronyms when they are clearer."
    ),
    glossary=(
        ("flow matching", "流匹配"),
        ("flow model", "流模型"),
        ("diffusion model", "扩散模型"),
        ("generative model", "生成模型"),
        ("ordinary differential equation / ODE", "常微分方程 / ODE"),
        ("stochastic differential equation / SDE", "随机微分方程 / SDE"),
        ("Fokker-Planck equation", "Fokker-Planck 方程"),
        ("probability path", "概率路径"),
        ("conditional probability path", "条件概率路径"),
        ("marginal probability path", "边缘概率路径"),
        ("vector field", "向量场"),
        ("velocity field", "速度场"),
        ("score function", "score 函数"),
        ("score matching", "score matching / 分数匹配"),
        ("denoising score matching", "去噪 score matching"),
        ("classifier guidance", "分类器引导"),
        ("classifier-free guidance", "无分类器引导"),
        ("latent space", "潜空间"),
        ("variational autoencoder / VAE", "变分自编码器 / VAE"),
        ("Diffusion Transformer / DiT", "Diffusion Transformer / DiT"),
        ("U-Net", "U-Net"),
        ("continuous-time Markov chain / CTMC", "连续时间马尔可夫链 / CTMC"),
        ("Brownian motion", "布朗运动"),
        ("Gaussian", "高斯分布"),
        ("prior", "先验"),
        ("posterior", "后验"),
        ("loss", "损失"),
        ("training objective", "训练目标"),
        ("sampling", "采样"),
        ("regression", "回归"),
    ),
    asr_corrections=(
        (r"\bfloor matching\b", "flow matching"),
        (r"\bfloor models?\b", "flow models"),
        (r"\bfloor model\b", "flow model"),
        (r"\bfloor and diffusion\b", "flow and diffusion"),
        (r"\bfloor matching loss\b", "flow matching loss"),
        (r"\bfloor matching objective\b", "flow matching objective"),
        (r"\bconditionable probability path\b", "conditional probability path"),
        (r"\bclassifier free guidance\b", "classifier-free guidance"),
        (r"\bfacher planck\b", "Fokker-Planck"),
        (r"\bfocker planck\b", "Fokker-Planck"),
    ),
    translation_corrections=(
        (r"\bfloor matching\b", "流匹配"),
        (r"\bfloor matching loss\b", "流匹配损失"),
        (r"\bfloor models?\b", "流模型"),
        (r"楼层匹配", "流匹配"),
        (r"地板匹配", "流匹配"),
        (r"楼层模型", "流模型"),
        (r"地板模型", "流模型"),
        (r"楼层和扩散", "流和扩散"),
        (r"地板和扩散", "流和扩散"),
        (r"分类器免费指导", "无分类器引导"),
        (r"无分类器指导", "无分类器引导"),
        (r"分类器指导", "分类器引导"),
        (r"得分函数", "score 函数"),
        (r"得分匹配", "score matching"),
        (r"去噪得分匹配", "去噪 score matching"),
        (r"潜在空间", "潜空间"),
    ),
)


PROFILES = {
    "general": None,
    MIT_DIFFUSION_PROFILE.name: MIT_DIFFUSION_PROFILE,
}


def get_profile(name: str | None) -> CourseProfile | None:
    if not name or name == "general":
        return None
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown profile: {name}") from exc


def apply_text_corrections(text: str, corrections: tuple[tuple[str, str], ...]) -> str:
    for pattern, replacement in corrections:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def apply_asr_profile(segments: list[Segment], profile: CourseProfile | None) -> list[Segment]:
    if not profile:
        return segments
    return [
        Segment(
            index=segment.index,
            start=segment.start,
            end=segment.end,
            text=apply_text_corrections(segment.text, profile.asr_corrections),
            translated_text=segment.translated_text,
        )
        for segment in segments
    ]


def apply_translation_profile(segments: list[Segment], profile: CourseProfile | None) -> list[Segment]:
    if not profile:
        return segments
    return [
        Segment(
            index=segment.index,
            start=segment.start,
            end=segment.end,
            text=segment.text,
            translated_text=(
                apply_text_corrections(segment.translated_text, profile.translation_corrections)
                if segment.translated_text
                else segment.translated_text
            ),
        )
        for segment in segments
    ]


def glossary_text(profile: CourseProfile | None) -> str:
    if not profile:
        return ""
    terms = "\n".join(f"- {source}: {target}" for source, target in profile.glossary)
    return f"{profile.prompt_context}\nRequired glossary:\n{terms}"
