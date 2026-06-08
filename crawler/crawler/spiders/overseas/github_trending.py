"""
GitHubTrendingSpider

采集 GitHub Trending 热门开源项目。
目标页面：https://github.com/trending

提取字段：
- title: repo 全名（owner/repo）
- content: repo description
- original_url: GitHub repo URL
- tags: 编程语言 + topic 标签
"""
import logging
import re
from typing import Generator
from urllib.parse import urljoin

from crawler.spiders.base import BaseSpider
from crawler.items import CrawlerItem

logger = logging.getLogger("github_trending")


class GitHubTrendingSpider(BaseSpider):
    """GitHub Trending 爬虫"""

    name = "github_trending"
    source_type = "overseas"
    source_name = "github_trending"
    lang = "en"

    allowed_domains = ["github.com"]
    start_urls = ["https://github.com/trending"]

    # ---- CSS 选择器 ----
    _ROW_SELECTOR = "article.Box-row"
    _REPO_LINK_SELECTOR = "h2 > a::attr(href)"
    _DESCRIPTION_SELECTOR = "p::text"
    _LANGUAGE_SELECTOR = "span[itemprop='programmingLanguage']::text"
    _TOPIC_SELECTOR = "a.topic-tag::text"
    _STARS_SELECTOR = "span.d-inline-block.float-sm-right::text"

    def parse(self, response) -> Generator[CrawlerItem, None, None]:
        """解析 GitHub Trending 页面，提取仓库列表"""
        rows = response.css(self._ROW_SELECTOR)
        logger.info("GitHub Trending 页面找到 %d 个仓库", len(rows))

        for row in rows:
            try:
                item = self._extract_repo(row, response)
                if item:
                    yield item
            except Exception as exc:
                logger.warning("解析 GitHub Trending 仓库项失败: %s", exc)
                continue

    def _extract_repo(self, row, response) -> CrawlerItem | None:
        """从单个仓库 HTML 块中提取 CrawlerItem"""
        # ---- title：owner/repo ----
        href = row.css(self._REPO_LINK_SELECTOR).get("").strip()
        if not href:
            return None

        # 从 href "/owner/repo" 提取 "owner/repo" 格式
        title = href.strip("/")

        # ---- original_url ----
        original_url = urljoin("https://github.com", href)

        # ---- content：repo description ----
        description = row.css(self._DESCRIPTION_SELECTOR).get("").strip()

        # ---- tags：编程语言 + topic 标签 ----
        tags = []

        # 编程语言
        lang = row.css(self._LANGUAGE_SELECTOR).get("").strip()
        if lang:
            tags.append(lang)

        # topic 标签
        topics = row.css(self._TOPIC_SELECTOR).getall()
        tags.extend([t.strip() for t in topics if t.strip()])

        # ---- stars（用于质量评分参考） ----
        stars_text = row.css(self._STARS_SELECTOR).get("").strip()
        try:
            # 格式如 "5,432 stars today"
            stars_match = re.search(r"([\d,]+)", stars_text)
            stars = int(stars_match.group(1).replace(",", "")) if stars_match else 0
        except (ValueError, AttributeError):
            stars = 0
        if stars > 0:
            logger.debug("仓库 %s 今日获 %d star", title, stars)

        return self.make_item(
            title=title,
            content=description,
            original_url=original_url,
            tags=tags,
        )
