"""
成都本地论坛爬虫 LocalForumSpider

从成都本地论坛（如天府社区、成都论坛等）提取帖子信息。
参考接口契约第 7.2 节 LocalForumSpider 字段提取规则。

提取方式：
- title:       h1.post-title / h1
- content:     div.post-content
- author:      .author-name / .author
- created_at:  time[datetime] / .post-time
- location:    .forum-board / .board 板块信息
"""
from typing import Generator

from scrapy.http import HtmlResponse

from crawler.items import CrawlerItem
from crawler.spiders.base import BaseSpider


class LocalForumSpider(BaseSpider):
    """成都本地论坛爬虫"""

    name = "local_forum"
    source_type = "domestic"
    source_name = "local_forum"
    lang = "zh"

    allowed_domains: list[str] = []
    start_urls: list[str] = []

    def parse(self, response: HtmlResponse) -> Generator[CrawlerItem, None, None]:
        """解析论坛帖子页面，产出 CrawlerItem"""
        try:
            # 提取标题：优先 .post-title，回退到 h1
            title = (
                response.css(".post-title::text").get()
                or response.css("h1::text").get()
                or response.css("h1 a::text").get()
                or ""
            ).strip()

            # 提取正文：仅从 .post-content 提取，无匹配时跳过
            content_html = response.css(".post-content").get("")
            if content_html:
                content = self.clean_html(content_html)
            else:
                self.logger.warning(f"页面无帖子内容，跳过: {response.url}")
                return

            # 标题或正文为空时跳过
            if not title or not content:
                self.logger.warning(f"帖子内容不完整，跳过: {response.url}")
                return

            # 提取作者
            author = (
                response.css(".author-name::text").get()
                or response.css(".author::text").get()
                or response.css('[class*="author"]::text').get()
                or ""
            ).strip()

            # 提取发布时间
            created_at = (
                response.css("time::attr(datetime)").get()
                or response.css('[class*="time"]::attr(datetime)').get()
                or response.css('[class*="date"]::attr(datetime)').get()
                or ""
            ).strip()

            # 提取板块/区域信息（获取所有子文本并拼接）
            location_parts = (
                response.css(".forum-board *::text").getall()
                or response.css(".board *::text").getall()
                or response.css('[class*="board"] *::text').getall()
                or response.css('[class*="forum"] *::text').getall()
            )
            location = " ".join(p.strip() for p in location_parts if p.strip())

            yield self.make_item(
                title=title,
                content=content,
                original_url=response.url,
                author=author,
                created_at=created_at,
                location=location,
            )
        except Exception as e:
            self.logger.error(
                f"解析失败: {response.url}, 错误: {e}",
                exc_info=True,
            )
