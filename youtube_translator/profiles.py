from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Segment


@dataclass(frozen=True, slots=True)
class CourseProfile:
    name: str
    asr_prompt: str
    prompt_context: str
    glossary: tuple[tuple[str, str], ...]
    asr_corrections: tuple[tuple[str, str], ...]
    translation_corrections: tuple[tuple[str, str], ...]


MIT_DIFFUSION_PROFILE = CourseProfile(
    name="mit-diffusion",
    asr_prompt=(
        "MIT 6.S184 lecture on flow matching, diffusion models, ODE, SDE, "
        "Fokker-Planck equation, probability path, vector field, score function, "
        "classifier-free guidance, Brownian motion, Gaussian, U-Net, DiT, VAE."
    ),
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

CMU_DB_PROFILE = CourseProfile(
    name="cmu-db",
    asr_prompt=(
        "CMU 15-445 15-645 Intro to Database Systems lecture. "
        "Relational model, relational algebra, SQL, DBMS, tuple, page, slotted page, "
        "buffer pool, LRU, Clock, LSM tree, column-store, row-store, hash table, "
        "B+ tree, inverted index, skip list, Bloom filter, latch, lock, hash join, "
        "sort-merge join, query optimizer, transaction, two-phase locking, MVCC, WAL, "
        "ARIES, distributed database."
    ),
    prompt_context=(
        "Domain: CMU 15-445/645 Intro to Database Systems. "
        "Translate as technical database systems lecture subtitles for Chinese readers. "
        "Keep database acronyms, system names, SQL keywords, C++ terms, and algorithm names in English "
        "when that is clearer, and provide concise Chinese translations for concepts."
    ),
    glossary=(
        ("relational model", "关系模型"),
        ("relational algebra", "关系代数"),
        ("SQL", "SQL"),
        ("DBMS", "DBMS / 数据库管理系统"),
        ("database management system", "数据库管理系统"),
        ("tuple", "元组"),
        ("page", "页"),
        ("slotted page", "槽页"),
        ("buffer pool", "缓冲池"),
        ("buffer pool manager", "缓冲池管理器"),
        ("page table", "页表"),
        ("replacement policy", "替换策略"),
        ("LRU", "LRU"),
        ("clock algorithm", "Clock 算法"),
        ("log-structured storage", "日志结构化存储"),
        ("LSM tree", "LSM tree"),
        ("column-store", "列式存储"),
        ("row-store", "行式存储"),
        ("compression", "压缩"),
        ("hash table", "哈希表"),
        ("B+ tree", "B+ tree"),
        ("index", "索引"),
        ("inverted index", "倒排索引"),
        ("skip list", "跳表"),
        ("Bloom filter", "Bloom filter / 布隆过滤器"),
        ("latch", "latch / 闩锁"),
        ("lock", "lock / 锁"),
        ("sorting", "排序"),
        ("aggregation", "聚合"),
        ("hash join", "哈希连接"),
        ("sort-merge join", "排序归并连接"),
        ("nested loop join", "嵌套循环连接"),
        ("query execution", "查询执行"),
        ("query optimizer", "查询优化器"),
        ("query optimization", "查询优化"),
        ("cost model", "成本模型"),
        ("cardinality estimation", "基数估计"),
        ("transaction", "事务"),
        ("concurrency control", "并发控制"),
        ("serializability", "可串行化"),
        ("two-phase locking / 2PL", "两阶段锁 / 2PL"),
        ("timestamp ordering", "时间戳排序"),
        ("MVCC", "MVCC / 多版本并发控制"),
        ("write-ahead logging / WAL", "预写日志 / WAL"),
        ("shadow paging", "影子分页"),
        ("crash recovery", "崩溃恢复"),
        ("checkpoint", "检查点"),
        ("ARIES", "ARIES"),
        ("distributed database", "分布式数据库"),
        ("replication", "复制"),
        ("partitioning", "分区"),
        ("sharding", "分片"),
        ("consensus", "共识"),
    ),
    asr_corrections=(
        (r"\bsequel\b", "SQL"),
        (r"\bB plus tree\b", "B+ tree"),
        (r"\bbtree\b", "B-tree"),
        (r"\bb tree\b", "B-tree"),
        (r"\bls m\b", "LSM"),
        (r"\blsm\b", "LSM"),
        (r"\bm v c c\b", "MVCC"),
        (r"\bw a l\b", "WAL"),
        (r"\btwo phase locking\b", "two-phase locking"),
        (r"\btwo-phase lacking\b", "two-phase locking"),
        (r"\bsort merge join\b", "sort-merge join"),
        (r"\bhash joins\b", "hash joins"),
    ),
    translation_corrections=(
        (r"续集", "SQL"),
        (r"SQL语言", "SQL"),
        (r"B加树", "B+ tree"),
        (r"B\+树", "B+ tree"),
        (r"缓冲池经理", "缓冲池管理器"),
        (r"页面", "页"),
        (r"闩锁", "latch / 闩锁"),
        (r"两阶段锁定", "两阶段锁"),
        (r"多版本并发控制", "MVCC / 多版本并发控制"),
        (r"预写日志记录", "预写日志"),
        (r"阴影分页", "影子分页"),
        (r"崩溃恢复", "崩溃恢复"),
    ),
)


PROFILES = {
    "general": None,
    MIT_DIFFUSION_PROFILE.name: MIT_DIFFUSION_PROFILE,
    CMU_DB_PROFILE.name: CMU_DB_PROFILE,
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
