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
        ("DBMS", "DBMS（数据库管理系统）"),
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
        ("Bloom filter", "Bloom filter（布隆过滤器）"),
        ("latch", "latch（闩锁）"),
        ("lock", "lock（锁）"),
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
        ("two-phase locking / 2PL", "两阶段锁（2PL）"),
        ("timestamp ordering", "时间戳排序"),
        ("MVCC", "MVCC（多版本并发控制）"),
        ("write-ahead logging / WAL", "WAL（预写日志）"),
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
        (r"\bmulti[- ]version Concertitool\b", "multi-version concurrency control"),
        (r"\bmulti[- ]version current control\b", "multi-version concurrency control"),
        (r"\bmulti[- ]version courtesy trouble\b", "multi-version concurrency control"),
        (r"\bmulti[- ]versioning current control\b", "multi-version concurrency control"),
        (r"\bmultiversioning current control\b", "multi-version concurrency control"),
        (r"\bmulti[- ]version query control\b", "multi-version concurrency control"),
        (r"\bmultiverging\b", "multi-versioning"),
        (r"\bOptimistic Encournance-Tuber Protocols?\b", "Optimistic Concurrency Control Protocol"),
        (r"\bOptimistic Encournance protocol\b", "Optimistic Concurrency Control protocol"),
        (r"\bSAP SAC isolation\b", "snapshot isolation"),
        (r"\bweather transaction\b", "transaction"),
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
        (r"DBMS\s*/\s*数据库管理系统", "DBMS（数据库管理系统）"),
        (r"Bloom filter\s*/\s*布隆过滤器", "Bloom filter（布隆过滤器）"),
        (r"lock\s*/\s*锁", "lock（锁）"),
        (r"latch（latch\s*/\s*latch\s*/\s*闩锁）", "latch（闩锁）"),
        (r"latch\s*/\s*latch\s*/\s*闩锁", "latch（闩锁）"),
        (r"latch\s*/\s*闩锁", "latch（闩锁）"),
        (r"两阶段锁定", "两阶段锁"),
        (r"两阶段锁\s*/\s*2PL", "两阶段锁（2PL）"),
        (r"多版本控制", "MVCC（多版本并发控制）"),
        (r"MVCC\s*/\s*MVCC\s*/\s*MVCC\s*/\s*多版本并发控制", "MVCC（多版本并发控制）"),
        (r"MVCC\s*/\s*MVCC\s*/\s*多版本并发控制", "MVCC（多版本并发控制）"),
        (r"MVCC\s*/\s*多版本并发控制", "MVCC（多版本并发控制）"),
        (r"Optimistic Encournance-Tuber Protocols?", "乐观并发控制（OCC）协议"),
        (r"Optimistic Encournance协议", "乐观并发控制（OCC）协议"),
        (r"SAP SAC隔离级别", "快照隔离级别"),
        (r"写-写-技能", "写偏斜"),
        (r"写-技能", "写偏斜"),
        (r"创建它的天气事务", "创建它的事务"),
        (r"预写日志\s*/\s*WAL", "WAL（预写日志）"),
        (r"预写日志记录", "预写日志"),
        (r"阴影分页", "影子分页"),
        (r"崩溃恢复", "崩溃恢复"),
    ),
)

BERKELEY_DUL_PROFILE = CourseProfile(
    name="berkeley-dul",
    asr_prompt=(
        "UC Berkeley CS294-158 Deep Unsupervised Learning lecture. "
        "Deep generative models, self-supervised learning, autoregressive models, "
        "normalizing flows, latent variable models, VAE, ELBO, GAN, diffusion models, "
        "score matching, contrastive learning, masked autoencoder, Transformer, LLM, "
        "video generation, multimodal models, NeRF, AI for science."
    ),
    prompt_context=(
        "Domain: UC Berkeley CS294-158 Deep Unsupervised Learning. "
        "Translate as technical deep learning lecture subtitles for Chinese readers. "
        "Keep mathematical symbols, model names, acronyms, loss names, and paper/system names in English "
        "when that is clearer; use standard Chinese terms for machine learning concepts."
    ),
    glossary=(
        ("deep unsupervised learning", "深度无监督学习"),
        ("deep generative model", "深度生成模型"),
        ("self-supervised learning", "自监督学习"),
        ("autoregressive model", "自回归模型"),
        ("language model", "语言模型"),
        ("Transformer", "Transformer"),
        ("attention", "注意力"),
        ("normalizing flow", "normalizing flow（归一化流）"),
        ("flow model", "流模型"),
        ("change of variables", "变量替换"),
        ("Jacobian", "Jacobian（雅可比矩阵）"),
        ("latent variable model", "潜变量模型"),
        ("variational autoencoder / VAE", "VAE（变分自编码器）"),
        ("evidence lower bound / ELBO", "ELBO（证据下界）"),
        ("encoder", "编码器"),
        ("decoder", "解码器"),
        ("posterior", "后验"),
        ("prior", "先验"),
        ("reparameterization trick", "重参数化技巧"),
        ("generative adversarial network / GAN", "GAN（生成对抗网络）"),
        ("implicit model", "隐式模型"),
        ("diffusion model", "扩散模型"),
        ("denoising diffusion", "去噪扩散"),
        ("score matching", "score matching（分数匹配）"),
        ("classifier-free guidance", "无分类器引导"),
        ("contrastive learning", "对比学习"),
        ("representation learning", "表征学习"),
        ("masked autoencoder / MAE", "MAE（掩码自编码器）"),
        ("large language model / LLM", "LLM（大语言模型）"),
        ("tokenizer", "tokenizer（分词器）"),
        ("video generation", "视频生成"),
        ("semi-supervised learning", "半监督学习"),
        ("distribution alignment", "分布对齐"),
        ("compression", "压缩"),
        ("multimodal model", "多模态模型"),
        ("parallelization", "并行化"),
        ("AI for science", "AI for Science"),
        ("neural radiance field / NeRF", "NeRF（神经辐射场）"),
        ("ray marching", "ray marching（光线步进）"),
        ("volume rendering", "体渲染"),
    ),
    asr_corrections=(
        (r"\bveryational auto ?encoder\b", "variational autoencoder"),
        (r"\bvariation auto ?encoder\b", "variational autoencoder"),
        (r"\bvariational auto encoder\b", "variational autoencoder"),
        (r"\be l b o\b", "ELBO"),
        (r"\bgans\b", "GANs"),
        (r"\bg a n\b", "GAN"),
        (r"\bv a e\b", "VAE"),
        (r"\bl l m\b", "LLM"),
        (r"\bnerf\b", "NeRF"),
        (r"\bnormalizing floor\b", "normalizing flow"),
        (r"\bfloor models?\b", "flow models"),
        (r"\bscore base(d)? models?\b", "score-based models"),
        (r"\bclassifier free guidance\b", "classifier-free guidance"),
        (r"\bself supervised\b", "self-supervised"),
        (r"\bsemi supervised\b", "semi-supervised"),
        (r"\bmulti modal\b", "multimodal"),
        (r"\bradiance fields?\b", "radiance fields"),
    ),
    translation_corrections=(
        (r"自我监督学习", "自监督学习"),
        (r"自动回归模型", "自回归模型"),
        (r"归一化流程", "normalizing flow（归一化流）"),
        (r"正常化流", "normalizing flow（归一化流）"),
        (r"流量模型", "流模型"),
        (r"楼层模型", "流模型"),
        (r"地板模型", "流模型"),
        (r"变量变化", "变量替换"),
        (r"潜在变量模型", "潜变量模型"),
        (r"变分自动编码器", "VAE（变分自编码器）"),
        (r"证据下限", "ELBO（证据下界）"),
        (r"重新参数化技巧", "重参数化技巧"),
        (r"生成对抗网络\s*/\s*GAN", "GAN（生成对抗网络）"),
        (r"得分匹配", "score matching（分数匹配）"),
        (r"分类器免费指导", "无分类器引导"),
        (r"无分类器指导", "无分类器引导"),
        (r"表示学习", "表征学习"),
        (r"大型语言模型", "LLM（大语言模型）"),
    ),
)

CS144_NET_PROFILE = CourseProfile(
    name="cs144-net",
    asr_prompt=(
        "Stanford CS144 Introduction to Computer Networking lecture. "
        "Internet, IP, datagram, packet switching, encapsulation, multiplexing, "
        "TCP, UDP, ICMP, checksum, finite state machine, stop-and-wait, sliding window, "
        "retransmission, congestion control, AIMD, NAT, HTTP, DNS, DHCP, routing, "
        "Bellman-Ford, Dijkstra, RIP, OSPF, BGP, Ethernet, Wi-Fi, MAC, CSMA/CD, CSMA/CA, "
        "TLS, confidentiality, integrity."
    ),
    prompt_context=(
        "Domain: Stanford CS144 Introduction to Computer Networking. "
        "Translate as technical networking lecture subtitles for Chinese readers. "
        "Keep protocol names, RFC-style acronyms, algorithm names, and system terms in English "
        "when that is clearer; use standard Chinese networking terminology."
    ),
    glossary=(
        ("Internet", "互联网"),
        ("IP", "IP"),
        ("datagram", "数据报"),
        ("packet", "分组"),
        ("encapsulation", "封装"),
        ("multiplexing", "复用"),
        ("demultiplexing", "解复用"),
        ("service model", "服务模型"),
        ("reliability", "可靠性"),
        ("TCP", "TCP"),
        ("UDP", "UDP"),
        ("ICMP", "ICMP"),
        ("end-to-end principle", "端到端原则"),
        ("checksum", "校验和"),
        ("finite state machine", "有限状态机"),
        ("stop-and-wait", "停等协议"),
        ("sliding window", "滑动窗口"),
        ("retransmission", "重传"),
        ("connection establishment", "连接建立"),
        ("packet switching", "分组交换"),
        ("queueing delay", "排队时延"),
        ("congestion control", "拥塞控制"),
        ("AIMD", "AIMD"),
        ("NAT", "NAT"),
        ("HTTP", "HTTP"),
        ("BitTorrent", "BitTorrent"),
        ("DNS", "DNS"),
        ("DHCP", "DHCP"),
        ("routing", "路由"),
        ("Bellman-Ford", "Bellman-Ford"),
        ("Dijkstra", "Dijkstra"),
        ("RIP", "RIP"),
        ("OSPF", "OSPF"),
        ("BGP", "BGP"),
        ("multicast", "组播"),
        ("spanning tree", "生成树"),
        ("IPv6", "IPv6"),
        ("Shannon capacity", "Shannon 容量"),
        ("modulation", "调制"),
        ("bit error", "比特错误"),
        ("FEC", "FEC"),
        ("Reed-Solomon", "Reed-Solomon"),
        ("MAC", "MAC"),
        ("CSMA/CD", "CSMA/CD"),
        ("Ethernet", "以太网"),
        ("wireless", "无线网络"),
        ("CSMA/CA", "CSMA/CA"),
        ("RTS/CTS", "RTS/CTS"),
        ("Wi-Fi", "Wi-Fi"),
        ("fragmentation", "分片"),
        ("TLS", "TLS"),
        ("confidentiality", "机密性"),
        ("integrity", "完整性"),
        ("certificate", "证书"),
        ("public key cryptography", "公钥密码学"),
    ),
    asr_corrections=(
        (r"\bencapslation\b", "encapsulation"),
        (r"\bbyte order\b", "byte order"),
        (r"\blongest prefix match l p\b", "longest prefix match"),
        (r"\baddress resolution proto(?:col)?\b", "Address Resolution Protocol"),
        (r"\bend to end principle\b", "end-to-end principle"),
        (r"\bfinite state machines\b", "finite state machines"),
        (r"\breliable comm\b", "reliable communication"),
        (r"\bbellman ford\b", "Bellman-Ford"),
        (r"\bcsma cd\b", "CSMA/CD"),
        (r"\bcsma ca\b", "CSMA/CA"),
        (r"\brts cts\b", "RTS/CTS"),
        (r"\bwifi\b", "Wi-Fi"),
        (r"\bmac overflow attack\b", "MAC overflow attack"),
        (r"\bpublic key cryptography\b", "public key cryptography"),
    ),
    translation_corrections=(
        (r"网际网路|因特网", "互联网"),
        (r"数据包", "分组"),
        (r"封包", "分组"),
        (r"多路复用", "复用"),
        (r"去复用", "解复用"),
        (r"服务模型", "服务模型"),
        (r"可靠通信", "可靠通信"),
        (r"末端到末端原则", "端到端原则"),
        (r"校验码", "校验和"),
        (r"有限状态机器", "有限状态机"),
        (r"停止并等待|停-等", "停等协议"),
        (r"滑动视窗", "滑动窗口"),
        (r"重新传输", "重传"),
        (r"建立连接", "连接建立"),
        (r"包交换", "分组交换"),
        (r"排队延迟", "排队时延"),
        (r"壅塞控制", "拥塞控制"),
        (r"位洪流", "BitTorrent"),
        (r"生成树协议", "生成树"),
        (r"香农容量", "Shannon 容量"),
        (r"位错误", "比特错误"),
        (r"有线局域网", "以太网"),
        (r"无线网络", "无线网络"),
        (r"机密度", "机密性"),
        (r"完整度", "完整性"),
        (r"公开密钥密码学", "公钥密码学"),
    ),
)


PROFILES = {
    "general": None,
    MIT_DIFFUSION_PROFILE.name: MIT_DIFFUSION_PROFILE,
    CMU_DB_PROFILE.name: CMU_DB_PROFILE,
    BERKELEY_DUL_PROFILE.name: BERKELEY_DUL_PROFILE,
    CS144_NET_PROFILE.name: CS144_NET_PROFILE,
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
