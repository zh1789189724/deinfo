"""
成都同城抖音爬虫 DouyinChengduSpider

从抖音视频页面提取标题、描述、POI位置、话题标签等信息。
参考接口契约第 7.2 节 DouyinChengduSpider 字段提取规则。

提取方式：
- title:      meta[property="og:title"]
- content:    meta[name="description"]
- tags:       从描述中提取 #话题标签
- location:   div.poi-info 中的 POI 名称
"""
import re
from typing import Generator

from scrapy.http import HtmlResponse

from crawler.items import CrawlerItem
from crawler.spiders.base import BaseSpider

# 话题标签匹配正则：#中文、#英文、#数字 等
TAG_PATTERN = re.compile(r"#([^\s#]+)")


class DouyinChengduSpider(BaseSpider):
    """成都同城抖音爬虫"""

    name = "douyin_chengdu"
    source_type = "domestic"
    source_name = "douyin_chengdu"
    lang = "zh"

    allowed_domains = ["douyin.com"]
    start_urls: list[str] = []

    def parse(self, response: HtmlResponse) -> Generator[CrawlerItem, None, None]:
        """解析抖音视频页面，产出 CrawlerItem"""
        try:
            # 提取标题
            title = (
                response.css('meta[property="og:title"]::attr(content)').get()
                or ""
            ).strip()

            # 提取描述（含话题标签）
            description = (
                response.css('meta[name="description"]::attr(content)').get()
                or ""
            ).strip()

            # 标题或描述为空时跳过
            content = description or title
            if not content:
                self.logger.warning(f"视频内容为空，跳过: {response.url}")
                return

            # 获取视频链接
            original_url = (
                response.css('meta[property="og:url"]::attr(content)').get()
                or response.url
            )

            # 从描述中提取话题标签
            tags = self._extract_tags(description)

            # 提取 POI 位置信息
            location = (
                response.css(".poi-info .poi-name::text").get()
                or response.css('[class*="poi"] [class*="name"]::text').get()
                or ""
            ).strip()

            yield self.make_item(
                title=title,
                content=description,
                original_url=original_url,
                location=location,
                tags=tags,
            )
        except Exception as e:
            self.logger.error(
                f"解析失败: {response.url}, 错误: {e}",
                exc_info=True,
            )

    def _extract_tags(self, text: str) -> list[str]:
        """从描述文本中提取 #话题标签"""
        if not text:
            return []
        return TAG_PATTERN.findall(text)
