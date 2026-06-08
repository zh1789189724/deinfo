"""
信息差发现平台 — 爬虫系统 数据源配置

定义所有 7 个数据源的 URL、频率、类型等。
与接口契约第 3 章完全一致。
"""
from typing import TypedDict


class SourceConfig(TypedDict, total=False):
    """单个数据源的配置结构"""
    type: str          # "domestic" | "overseas"
    lang: str          # "zh" | "en" | "ja" 等
    enabled: bool      # 是否启用
    cron: str          # 5 段 cron 表达式
    priority: str      # "P0" | "P1" | "P2"
    description: str   # 中文描述
    seed_urls: list[str]  # 入口 URL 列表


SOURCES: dict[str, SourceConfig] = {
    # ── 国内源（成都本地）──
    "wechat_chengdu": {
        "type": "domestic",
        "lang": "zh",
        "enabled": True,
        "cron": "0 8,18 * * *",        # 每天 8:00 和 18:00
        "priority": "P0",
        "description": "成都本地公众号文章",
        "seed_urls": [
            "https://mp.weixin.qq.com/",
        ],
    },
    "douyin_chengdu": {
        "type": "domestic",
        "lang": "zh",
        "enabled": True,
        "cron": "0 */4 * * *",          # 每 4 小时
        "priority": "P0",
        "description": "成都同城抖音",
        "seed_urls": [],
    },
    "local_forum": {
        "type": "domestic",
        "lang": "zh",
        "enabled": True,
        "cron": "0 9,21 * * *",        # 每天 9:00 和 21:00
        "priority": "P0",
        "description": "成都本地论坛",
        "seed_urls": [],
    },
    "gov_chengdu": {
        "type": "domestic",
        "lang": "zh",
        "enabled": True,
        "cron": "0 10 * * 1,3,5",      # 周一三五 10:00
        "priority": "P0",
        "description": "成都政府补贴/消费券网站",
        "seed_urls": [],
    },
    # ── 海外源 ──
    "producthunt": {
        "type": "overseas",
        "lang": "en",
        "enabled": True,
        "cron": "0 7 * * *",            # 每天 7:00
        "priority": "P0",
        "description": "Product Hunt 每日新品",
        "seed_urls": ["https://www.producthunt.com/"],
    },
    "hackernews": {
        "type": "overseas",
        "lang": "en",
        "enabled": True,
        "cron": "0 */2 * * *",          # 每 2 小时
        "priority": "P0",
        "description": "Hacker News 热门",
        "seed_urls": ["https://news.ycombinator.com/"],
    },
    "github_trending": {
        "type": "overseas",
        "lang": "en",
        "enabled": True,
        "cron": "0 8 * * *",            # 每天 8:00
        "priority": "P0",
        "description": "GitHub Trending",
        "seed_urls": ["https://github.com/trending"],
    },
    # ── 新增海外源 ──
    "36kr": {
        "type": "overseas",
        "lang": "zh",
        "enabled": True,
        "cron": "0 */3 * * *",          # 每 3 小时
        "priority": "P0",
        "description": "36氪 快讯（投资/商业）",
        "seed_urls": ["https://36kr.com/newsflashes"],
    },
    "designtaxi": {
        "type": "overseas",
        "lang": "en",
        "enabled": True,
        "cron": "0 */6 * * *",          # 每 6 小时
        "priority": "P1",
        "description": "DesignTAXI 设计新闻",
        "seed_urls": ["https://designtaxi.com/"],
    },
}


def get_enabled_sources() -> dict[str, SourceConfig]:
    """获取所有已启用的数据源"""
    return {name: cfg for name, cfg in SOURCES.items() if cfg.get("enabled", True)}


def get_source_by_name(name: str) -> SourceConfig | None:
    """根据名称获取数据源配置"""
    return SOURCES.get(name)
