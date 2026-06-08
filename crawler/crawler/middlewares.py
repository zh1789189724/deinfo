"""
信息差发现平台 — 爬虫系统 中间件

包含代理切换、User-Agent 轮换、请求日志等中间件。
"""
import logging
import random
import os
from scrapy import signals
from scrapy.http import Request, Response

logger = logging.getLogger(__name__)

# ── 常用 User-Agent 列表（覆盖主流浏览器各版本）──
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]


class RandomUserAgentMiddleware:
    """随机 User-Agent 中间件

    每个请求随机选择一个 UA，降低被封概率。
    """

    def __init__(self, user_agents: list[str] | None = None):
        self.user_agents = user_agents or USER_AGENTS

    @classmethod
    def from_crawler(cls, crawler):
        """从 Scrapy Crawler 创建中间件实例"""
        ua_list = crawler.settings.getlist("USER_AGENTS") or USER_AGENTS
        middleware = cls(user_agents=ua_list)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        logger.debug(f"[{spider.name}] RandomUserAgentMiddleware 已启用, UA 池大小: {len(self.user_agents)}")

    def process_request(self, request: Request, spider) -> Request | None:
        """为请求设置随机 User-Agent"""
        ua = random.choice(self.user_agents)
        request.headers["User-Agent"] = ua
        return None


class ProxyMiddleware:
    """代理中间件

    支持从环境变量 PROXY_URL 读取代理地址。
    海外源（type=overseas）默认走代理。

    代理格式支持：
    - http://proxy:8080
    - http://user:pass@proxy:8080
    - socks5://proxy:1080
    """

    def __init__(self, proxy_url: str | None = None):
        proxy_from_env = os.environ.get("PROXY_URL", "").strip()
        self.proxy_url = proxy_url or proxy_from_env or None

    @classmethod
    def from_crawler(cls, crawler):
        proxy_url = crawler.settings.get("PROXY_URL", None) or os.environ.get("PROXY_URL", "")
        middleware = cls(proxy_url=proxy_url or None)
        if not middleware.proxy_url:
            logger.info("ProxyMiddleware: PROXY_URL 未设置，代理中间件将跳过所有请求")
        return middleware

    def process_request(self, request: Request, spider) -> Request | None:
        """为请求设置代理地址"""
        if not self.proxy_url:
            return None
        request.meta["proxy"] = self.proxy_url
        logger.debug(f"[代理] {request.url} → {self.proxy_url}")
        return None


class RequestLogMiddleware:
    """请求日志中间件

    记录每次请求的 URL、状态码、耗时，用于调试和监控。
    """

    def __init__(self, stats=None):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(stats=crawler.stats)
        return middleware

    def process_request(self, request: Request, spider) -> Request | None:
        """记录请求开始"""
        request.meta["_request_start_time"] = None  # 由 Downloader 设置时间戳
        return None

    def process_response(self, request: Request, response: Response, spider) -> Response:
        """记录响应日志"""
        status = response.status
        url = request.url[:120]  # 截断过长 URL
        logger.info(f"[{spider.name}] {status} {url}")
        return response

    def process_exception(self, request: Request, exception: Exception, spider):
        """记录请求异常"""
        logger.warning(f"[{spider.name}] 请求失败: {request.url[:120]} - {exception}")
        return None
