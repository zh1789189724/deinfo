"""
HackerNewsSpider

采集 Hacker News 热门讨论。
目标页面：https://news.ycombinator.com/

提取字段：
- title: 帖子标题
- content: 链接页面的 description 或评论摘要
- original_url: 帖子链接（外部）
- author: 发帖人
"""
import logging
from typing import Generator

from crawler.spiders.base import BaseSpider
from crawler.items import CrawlerItem

logger = logging.getLogger("hackernews")


class HackerNewsSpider(BaseSpider):
    """Hacker News 热门爬虫"""

    name = "hackernews"
    source_type = "overseas"
    source_name = "hackernews"
    lang = "en"

    allowed_domains = ["news.ycombinator.com"]
    start_urls = ["https://news.ycombinator.com/"]

    # ---- CSS 选择器 ----
    _ROW_SELECTOR = "tr.athing"
    _TITLE_SELECTOR = "span.titleline > a::text"
    _TITLE_HREF_SELECTOR = "span.titleline > a::attr(href)"
    _SCORE_SELECTOR = "span.score::text"
    _AUTHOR_SELECTOR = "td.subtext > a[href^='user?']::text"
    _COMMENTS_SELECTOR = "td.subtext > a[href^='item?']:last-child::text"

    def parse(self, response) -> Generator[CrawlerItem, None, None]:
        """解析 Hacker News 首页，提取帖子列表"""
        rows = response.css(self._ROW_SELECTOR)
        logger.info("HN 页面找到 %d 个帖子行", len(rows))

        for row in rows:
            try:
                item = self._extract_post(row, response)
                if item:
                    yield item
            except Exception as exc:
                logger.warning("解析 HN 帖子失败: %s", exc)
                continue

    def _extract_post(self, row, response) -> CrawlerItem | None:
        """从单个帖子行中提取 CrawlerItem"""
        # ---- title ----
        title = row.css(self._TITLE_SELECTOR).get("").strip()
        if not title:
            return None

        # ---- original_url ----
        original_url = row.css(self._TITLE_HREF_SELECTOR).get("").strip()
        if not original_url:
            return None

        # ---- 获取帖子的 id，用于定位 subtext 行 ----
        post_id = row.attrib.get("id", "")

        # ---- subtext 行包含 author / points / comments ----
        # 使用 CSS 相邻兄弟选择器：tr.athing#{id} + tr 获取紧接的 subtext 行
        # ---- author ----
        author = response.css(
            f"tr.athing#{post_id} + tr {self._AUTHOR_SELECTOR}"
        ).get("").strip()

        # ---- points（用于质量评分参考） ----
        points_text = response.css(
            f"tr.athing#{post_id} + tr {self._SCORE_SELECTOR}"
        ).get("")
        try:
            points = int(points_text.replace(" points", "").replace(" point", ""))
        except (ValueError, AttributeError):
            points = 0
        if points > 0:
            logger.debug("帖子 %s 获 %d 分", title, points)

        # ---- comments_count（用于质量评分参考） ----
        comments_text = response.css(
            f"tr.athing#{post_id} + tr {self._COMMENTS_SELECTOR}"
        ).get("")
        try:
            comments_count = int(
                comments_text.replace(" comments", "")
                .replace(" comment", "")
                .strip()
            )
        except (ValueError, AttributeError):
            comments_count = 0
        if comments_count > 0:
            logger.debug("帖子 %s 有 %d 条评论", title, comments_count)

        # ---- content：提取链接页面的 description（简化版，仅用标题作摘要） ----
        content = title  # 后续 Pipeline 可补充详情页 description

        return self.make_item(
            title=title,
            content=content,
            original_url=original_url,
            author=author,
        )
