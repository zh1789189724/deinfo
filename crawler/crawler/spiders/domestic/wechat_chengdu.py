"""
成都本地公众号文章爬虫 WechatChengduSpider

从微信公众号文章页面提取标题、正文、作者、发布时间等信息。
参考接口契约第 7.2 节 WechatChengduSpider 字段提取规则。

提取方式：
- title:      meta[property="og:title"] / meta[property="article:tag:title"]
- content:    <article> 标签内的纯文本
- author:     meta[name="profile:username"] / 公众号名称
- created_at: meta[property="article:published_time"]
- location:   从正文中提取成都地名（如高新区、天府新区等）
"""
from typing import Generator

from scrapy.http import HtmlResponse

from crawler.items import CrawlerItem
from crawler.spiders.base import BaseSpider


# 成都主要区域/地名关键词，用于从正文中提取 location
CHENGDU_DISTRICTS = [
    "高新区", "天府新区", "锦江区", "青羊区", "金牛区",
    "武侯区", "成华区", "龙泉驿区", "青白江区", "新都区",
    "温江区", "双流区", "郫都区", "新津区", "都江堰市",
    "彭州市", "邛崃市", "崇州市", "金堂县", "大邑县",
    "蒲江县", "简阳市", "东部新区",
]


class WechatChengduSpider(BaseSpider):
    """成都本地公众号文章爬虫"""

    name = "wechat_chengdu"
    source_type = "domestic"
    source_name = "wechat_chengdu"
    lang = "zh"

    allowed_domains = ["mp.weixin.qq.com"]
    start_urls: list[str] = []

    def parse(self, response: HtmlResponse) -> Generator[CrawlerItem, None, None]:
        """解析微信公众号文章页面，产出 CrawlerItem"""
        try:
            # 提取标题：优先 og:title，回退到 h1 / <title>
            title = (
                response.css('meta[property="og:title"]::attr(content)').get()
                or response.css('meta[property="article:tag:title"]::attr(content)').get()
                or response.css("h1::text").get()
                or response.css("title::text").get()
                or ""
            ).strip()

            # 提取正文：仅从 <article> 标签提取，无 article 时跳过
            article_html = response.css("article").get("")
            if article_html:
                content = self.clean_html(article_html)
            else:
                self.logger.warning(f"页面无 article 标签，跳过: {response.url}")
                return

            # 内容为空时跳过
            if not content:
                self.logger.warning(f"正文为空，跳过: {response.url}")
                return

            # 提取作者
            author = (
                response.css('meta[name="profile:username"]::attr(content)').get()
                or response.css('meta[property="profile:username"]::attr(content)').get()
                or ""
            ).strip()

            # 提取发布时间
            created_at = (
                response.css('meta[property="article:published_time"]::attr(content)').get()
                or ""
            ).strip()

            # 从正文中提取成都地名作为 location
            location = self._extract_location(content)

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

    def _extract_location(self, text: str) -> str:
        """从正文中提取成都地名"""
        if not text:
            return ""
        for district in CHENGDU_DISTRICTS:
            if district in text:
                return district
        return ""
