"""
爬虫系统 Spider 基类。

所有 spider 继承此基类，获得公用方法。
"""
import re
import scrapy
from crawler.items import CrawlerItem


class BaseSpider(scrapy.Spider):
    """所有 spider 的基类，提供公用方法"""

    source_type: str = ""  # "domestic" | "overseas"，子类覆盖
    source_name: str = ""  # 数据源 key，子类覆盖
    lang: str = ""  # 语言代码，子类覆盖

    def clean_html(self, html: str) -> str:
        """去除 HTML 标签，压缩空白"""
        if not html:
            return ""
        # 去除 HTML 标签
        text = re.sub(r"<[^>]+>", " ", html)
        # 压缩空白：多个空格/换行 → 单个空格
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_content(self, response) -> str:
        """提取页面正文纯文本，子类可覆盖"""
        # 默认尝试提取 body 文本
        body = response.css("body").get("")
        return self.clean_html(body)

    def make_item(
        self,
        *,
        title: str,
        content: str,
        original_url: str,
        **kwargs,
    ) -> CrawlerItem:
        """构造 CrawlerItem，统一填充基类字段"""
        return CrawlerItem(
            source_type=self.source_type,
            source_name=self.source_name,
            lang=self.lang,
            title=title.strip() if title else "",
            content=content.strip() if content else "",
            original_url=original_url.strip() if original_url else "",
            author=kwargs.pop("author", ""),
            summary=kwargs.pop("summary", ""),
            created_at=kwargs.pop("created_at", ""),
            location=kwargs.pop("location", ""),
            price=kwargs.pop("price", 0.0),
            validity_end=kwargs.pop("validity_end", ""),
            tags=kwargs.pop("tags", []),
            images=kwargs.pop("images", []),
        )
