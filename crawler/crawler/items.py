"""
信息差发现平台 — 爬虫系统 Spider Item 定义

定义爬虫产出的统一数据格式 CrawlerItem。
所有 spider 的 parse() 方法必须 yield CrawlerItem 实例。
参考接口契约第 4 章、第 6.4 节。
"""
from dataclasses import dataclass, field


@dataclass
class CrawlerItem:
    """爬虫统一输出 Item

    所有 spider 的 parse() 必须 yield 此类型的实例，
    严禁直接 yield dict。
    """

    # ── 必填字段 ──
    source_type: str  # "domestic" | "overseas"
    source_name: str  # 数据源名称，对应 config/sources.py 的 key
    lang: str  # "zh" | "en" | "ja" 等
    title: str  # 文章/产品标题
    content: str  # 清洗后的纯文本正文
    original_url: str  # 原文/产品链接

    # ── 可选字段 ──
    summary: str = ""  # 导语/摘要（原文自带）
    author: str = ""  # 作者/发布者
    created_at: str = ""  # 原文发布时间，ISO 格式 "2026-06-08T10:00:00Z"
    location: str = ""  # 位置信息（国内源用）
    price: float = 0.0  # 价格（优惠类用）
    validity_end: str = ""  # 有效期截止（优惠类用）
    tags: list = field(default_factory=list)  # 标签列表
    images: list = field(default_factory=list)  # 图片 URL 列表


@dataclass
class PushResult:
    """单条推送结果（接口契约第 6.4 节）"""
    success: bool
    status_code: int
    message: str = ""
    item_id: str = ""


@dataclass
class BulkPushResult:
    """批量推送结果（接口契约第 6.4 节）"""
    total: int
    success: int
    failed: int
    results: list[PushResult] = field(default_factory=list)
