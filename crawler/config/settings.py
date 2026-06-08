"""
信息差发现平台 — 爬虫系统 Scrapy 设置

包含 AutoThrottle、去重、Pipeline 注册、扩展设置等。
"""
# ── 基础设置 ──
BOT_NAME = "deinfo_crawler"
SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

# ── 爬取策略 ──
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN = 4
COOKIES_ENABLED = False

# ── AutoThrottle 扩展 ──
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# ── 去重 ──
DUPEFILTER_CLASS = "scrapy.dupefilters.RFPDupeFilter"
# 可选 Redis 去重（当 REDIS_URL 环境变量设置时启用）
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# ── 请求头 ──
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

# ── 中间件 ──
DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.RandomUserAgentMiddleware": 400,
    "crawler.middlewares.ProxyMiddleware": 500,
    "crawler.middlewares.RequestLogMiddleware": 550,
}

# ── Pipeline ──
# 注意：CrawlerPipeline 由 Agent C 实现
# 暂用字符串路径注册，Scrapy 在运行时懒加载
ITEM_PIPELINES = {
    "crawler.pipelines.CrawlerPipeline": 300,
}

# ── 扩展 ──
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,  # 禁用 telnet
}

# ── 日志 ──
LOG_LEVEL = "INFO"
LOG_ENABLED = True

# ── 下载设置 ──
DOWNLOAD_TIMEOUT = 30
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# 禁用 Scrapy 内置代理
HTTPPROXY_ENABLED = False

# 系统代理配置
import os
_PROXY = os.environ.get('PROXY_URL') or 'http://127.0.0.1:7897'
if _PROXY:
    os.environ.setdefault('HTTPS_PROXY', _PROXY)
    os.environ.setdefault('HTTP_PROXY', _PROXY)

# ── 爬虫设置 ──
DEPTH_LIMIT = 3
# 禁止爬取范围之外 URL
OFFSITE_ENABLED = False
