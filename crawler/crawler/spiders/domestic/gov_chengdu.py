"""
成都政府补贴/消费券爬虫 GovChengduSpider

从成都市政府网站提取公告信息，并自动标记补贴、消费券、税收优惠等标签。
参考接口契约第 7.2 节 GovChengduSpider 字段提取规则。

提取方式：
- title:       h1 / meta[og:title]
- content:     .article-content / .content
- created_at:  .date / meta[publish-date] / .publish-time
- tags:        根据正文关键词自动标记 ["消费券", "补贴", "税收优惠"]
"""
from typing import Generator

from scrapy.http import HtmlResponse

from crawler.items import CrawlerItem
from crawler.spiders.base import BaseSpider

# 关键词 → 标签映射
KEYWORD_TAG_MAP: dict[str, str] = {
    "消费券": "消费券",
    "补贴": "补贴",
    "税收优惠": "税收优惠",
    "创业补贴": "补贴",
    "购房补贴": "补贴",
    "租房补贴": "补贴",
    "购车补贴": "补贴",
    "减税": "税收优惠",
    "免税": "税收优惠",
    "消费补贴": "消费券",
}


class GovChengduSpider(BaseSpider):
    """成都政府补贴/消费券爬虫"""

    name = "gov_chengdu"
    source_type = "domestic"
    source_name = "gov_chengdu"
    lang = "zh"

    allowed_domains = ["cd.gov.cn", "chengdu.gov.cn"]
    start_urls: list[str] = []

    def parse(self, response: HtmlResponse) -> Generator[CrawlerItem, None, None]:
        """解析政府公告页面，产出 CrawlerItem"""
        try:
            # 提取标题：优先 h1，回退到 og:title / <title>
            title = (
                response.css("h1::text").get()
                or response.css('meta[property="og:title"]::attr(content)').get()
                or response.css("title::text").get()
                or ""
            ).strip()

            # 提取正文：仅从指定容器提取，无匹配时跳过
            content_html = (
                response.css(".article-content").get("")
                or response.css(".content").get("")
                or response.css(".article-container").get("")
            )
            if content_html:
                content = self.clean_html(content_html)
            else:
                self.logger.warning(f"页面无公告内容容器，跳过: {response.url}")
                return

            # 标题或正文为空时跳过
            if not title or not content:
                self.logger.warning(f"公告内容不完整，跳过: {response.url}")
                return

            # 提取发布日期
            created_at = (
                response.css('meta[name="publish-date"]::attr(content)').get()
                or response.css(".date::text").get()
                or response.css(".publish-time::text").get()
                or response.css('[class*="date"]::text').get()
                or response.css('[class*="time"]::text').get()
                or ""
            ).strip()

            # 根据正文关键词自动打标签
            tags = self._detect_tags(title, content)

            yield self.make_item(
                title=title,
                content=content,
                original_url=response.url,
                created_at=created_at,
                tags=tags,
            )
        except Exception as e:
            self.logger.error(
                f"解析失败: {response.url}, 错误: {e}",
                exc_info=True,
            )

    def _detect_tags(self, title: str, content: str) -> list[str]:
        """根据标题和正文关键词自动标记标签"""
        combined_text = f"{title} {content}"
        detected = set()
        for keyword, tag in KEYWORD_TAG_MAP.items():
            if keyword in combined_text:
                detected.add(tag)
        return sorted(detected)
