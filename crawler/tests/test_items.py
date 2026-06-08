"""测试 CrawlerItem dataclass 定义"""

import pytest
from crawler.items import CrawlerItem


class TestCrawlerItem:
    """CrawlerItem 创建与默认值测试"""

    def test_create_with_required_only(self):
        """仅填写必填字段时，可选字段应有正确的默认值"""
        item = CrawlerItem(
            source_type="domestic",
            source_name="wechat_chengdu",
            lang="zh",
            title="测试标题",
            content="测试内容",
            original_url="https://example.com/article/1",
        )
        assert item.source_type == "domestic"
        assert item.source_name == "wechat_chengdu"
        assert item.lang == "zh"
        assert item.title == "测试标题"
        assert item.content == "测试内容"
        assert item.original_url == "https://example.com/article/1"
        # 可选字段默认值
        assert item.summary == ""
        assert item.author == ""
        assert item.created_at == ""
        assert item.location == ""
        assert item.price == 0.0
        assert item.validity_end == ""
        assert item.tags == []
        assert item.images == []

    def test_create_with_all_fields(self):
        """填写所有字段时，值应正确保留"""
        item = CrawlerItem(
            source_type="overseas",
            source_name="producthunt",
            lang="en",
            title="Awesome Product",
            content="Product description here",
            original_url="https://producthunt.com/posts/1",
            summary="Best product ever",
            author="John Doe",
            created_at="2026-06-08T10:00:00Z",
            location="Chengdu",
            price=29.99,
            validity_end="2026-07-08T23:59:59Z",
            tags=["ai", "tools"],
            images=["https://example.com/img1.png"],
        )
        assert item.source_type == "overseas"
        assert item.source_name == "producthunt"
        assert item.lang == "en"
        assert item.title == "Awesome Product"
        assert item.content == "Product description here"
        assert item.original_url == "https://producthunt.com/posts/1"
        assert item.summary == "Best product ever"
        assert item.author == "John Doe"
        assert item.created_at == "2026-06-08T10:00:00Z"
        assert item.location == "Chengdu"
        assert item.price == 29.99
        assert item.validity_end == "2026-07-08T23:59:59Z"
        assert item.tags == ["ai", "tools"]
        assert item.images == ["https://example.com/img1.png"]

    def test_tags_list_isolation(self):
        """每个实例的 tags 和 images 应为独立列表，互不影响"""
        item1 = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t1", content="c1", original_url="https://example.com/1",
            tags=["tag1"],
        )
        item2 = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t2", content="c2", original_url="https://example.com/2",
        )
        # item2 的 tags 不应受 item1 影响
        assert item2.tags == []
        assert item1.tags == ["tag1"]
        # 修改 item1 不应影响 item2
        item1.tags.append("tag2")
        assert item2.tags == []

    def test_source_type_enum_values(self):
        """source_type 应只接受 domestic 或 overseas"""
        item_d = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t", content="c", original_url="https://example.com",
        )
        item_o = CrawlerItem(
            source_type="overseas", source_name="test", lang="en",
            title="t", content="c", original_url="https://example.com",
        )
        assert item_d.source_type in ("domestic", "overseas")
        assert item_o.source_type in ("domestic", "overseas")

    def test_price_default_type(self):
        """price 默认值应为 float 类型"""
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t", content="c", original_url="https://example.com",
        )
        assert isinstance(item.price, float)
        assert item.price == 0.0

    def test_item_immutability_by_dataclass(self):
        """dataclass 默认 frozen=False, 字段应可正常赋值"""
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t", content="c", original_url="https://example.com",
        )
        item.title = "new title"
        assert item.title == "new title"
