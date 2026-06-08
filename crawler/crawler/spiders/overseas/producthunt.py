"""
ProductHuntSpider

采集 Product Hunt 每日新产品信息。
目标页面：https://www.producthunt.com/

提取字段：
- title: 产品名称
- content: 产品描述 + 评论摘要
- original_url: 产品链接
- tags: 产品标签 categories
"""
import logging
from typing import Generator
from urllib.parse import urljoin

from crawler.spiders.base import BaseSpider
from crawler.items import CrawlerItem

logger = logging.getLogger("producthunt")


class ProductHuntSpider(BaseSpider):
    """Product Hunt 每日新品爬虫"""

    name = "producthunt"
    source_type = "overseas"
    source_name = "producthunt"
    lang = "en"

    allowed_domains = ["www.producthunt.com"]
    start_urls = ["https://www.producthunt.com/"]

    # ---- CSS 选择器（集中管理，便于维护） ----
    _PRODUCT_SELECTOR = "div[class*='styles_item__']"
    _TITLE_SELECTOR = "a[class*='styles_title__']::text"
    _TITLE_HREF_SELECTOR = "a[class*='styles_title__']::attr(href)"
    _TAGLINE_SELECTOR = "div[class*='styles_tagline__']::text"
    _TOPIC_SELECTOR = "a.topic::text"
    _VOTES_SELECTOR = "span[class*='styles_votes_count__']::text"

    def parse(self, response) -> Generator[CrawlerItem, None, None]:
        """解析 Product Hunt 首页，提取产品列表"""
        products = response.css(self._PRODUCT_SELECTOR)
        logger.info("ProductHunt 页面找到 %d 个产品项", len(products))

        for product in products:
            try:
                item = self._extract_product(product, response)
                if item:
                    yield item
            except Exception as exc:
                logger.warning("解析 ProductHunt 产品项失败: %s", exc)
                continue

    def _extract_product(self, product, response) -> CrawlerItem | None:
        """从单个产品 HTML 块中提取 CrawlerItem"""
        # ---- title ----
        title = product.css(self._TITLE_SELECTOR).get("").strip()
        if not title:
            return None

        # ---- original_url ----
        rel_path = product.css(self._TITLE_HREF_SELECTOR).get("")
        original_url = urljoin("https://www.producthunt.com", rel_path) if rel_path else ""

        # ---- content：描述 + 评论摘要 ----
        tagline = product.css(self._TAGLINE_SELECTOR).get("").strip()
        content = tagline  # 评论摘要需要进一步请求详情页，此处先用描述

        # ---- tags ----
        tags = product.css(self._TOPIC_SELECTOR).getall()
        tags = [t.strip() for t in tags if t.strip()]

        # ---- votes（用于质量评分参考，暂不放入 item）----
        votes_text = product.css(self._VOTES_SELECTOR).get("").strip()
        try:
            votes = int(votes_text.replace(",", ""))
        except (ValueError, AttributeError):
            votes = 0
        if votes > 0:
            logger.debug("产品 %s 获 %d 票", title, votes)

        return self.make_item(
            title=title,
            content=content,
            original_url=original_url,
            tags=tags,
        )
