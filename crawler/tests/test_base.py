"""测试 BaseSpider 基类"""

import pytest
from unittest.mock import Mock
from crawler.spiders.base import BaseSpider
from crawler.items import CrawlerItem


class ConcreteSpider(BaseSpider):
    """用于测试的具象 Spider 子类"""
    name = "test_spider"
    source_type = "domestic"
    source_name = "test_source"
    lang = "zh"


class TestCleanHtml:
    """clean_html 方法测试"""

    def setup_method(self):
        self.spider = ConcreteSpider()

    def test_strips_simple_tags(self):
        """剥离简单 HTML 标签"""
        html = "<p>Hello World</p>"
        result = self.spider.clean_html(html)
        assert result == "Hello World"

    def test_strips_nested_tags(self):
        """剥离嵌套 HTML 标签"""
        html = "<div><p>成都<strong>消费券</strong>来了</p></div>"
        result = self.spider.clean_html(html)
        # 标签被替换为空格后压缩，形成正常分词
        assert result == "成都 消费券 来了"

    def test_compresses_multiple_spaces(self):
        """多个连续空格应压缩为单个空格"""
        html = "<p>成都    消费券    来了</p>"
        result = self.spider.clean_html(html)
        assert result == "成都 消费券 来了"

    def test_compresses_newlines_and_tabs(self):
        """换行符和制表符应压缩为空格"""
        html = "<p>成都\n消费券\t来了</p>"
        result = self.spider.clean_html(html)
        assert "  " not in result
        assert "\n" not in result
        assert result == "成都 消费券 来了"

    def test_strips_leading_trailing_whitespace(self):
        """首尾空白应被去除"""
        html = "  <p>成都消费券</p>  "
        result = self.spider.clean_html(html)
        assert result == "成都消费券"

    def test_handles_empty_string(self):
        """空字符串应返回空字符串"""
        assert self.spider.clean_html("") == ""

    def test_handles_none(self):
        """None 输入应返回空字符串，不应抛出异常"""
        assert self.spider.clean_html(None) == ""

    def test_handles_no_html_tags(self):
        """纯文本无标签时应原样返回"""
        text = "这是一条纯文本内容"
        result = self.spider.clean_html(text)
        assert result == text

    def test_handles_self_closing_tags(self):
        """自闭合标签应被剥离"""
        html = "line1<br/>line2<br>line3"
        result = self.spider.clean_html(html)
        assert result == "line1 line2 line3"


class TestExtractContent:
    """extract_content 方法测试"""

    def setup_method(self):
        self.spider = ConcreteSpider()

    def test_extracts_body_text(self):
        """从页面 body 中提取纯文本"""
        mock_response = Mock()
        mock_response.css.return_value.get.return_value = (
            "<body><h1>标题</h1><p>正文内容</p></body>"
        )
        result = self.spider.extract_content(mock_response)
        assert "标题" in result
        assert "正文内容" in result
        assert "<body>" not in result
        assert "<h1>" not in result

    def test_handles_empty_body(self):
        """页面无 body 时应返回空字符串"""
        mock_response = Mock()
        mock_response.css.return_value.get.return_value = ""
        result = self.spider.extract_content(mock_response)
        assert result == ""

    def test_css_selector_is_body(self):
        """应使用 'body' CSS 选择器"""
        mock_response = Mock()
        mock_response.css.return_value.get.return_value = "some text"
        self.spider.extract_content(mock_response)
        mock_response.css.assert_called_once_with("body")


class TestMakeItem:
    """make_item 方法测试"""

    def setup_method(self):
        self.spider = ConcreteSpider()

    def test_returns_crawler_item(self):
        """应返回 CrawlerItem 实例"""
        item = self.spider.make_item(
            title="测试标题",
            content="测试正文",
            original_url="https://example.com/article/1",
        )
        assert isinstance(item, CrawlerItem)

    def test_fills_source_fields(self):
        """应自动填充 source_type、source_name、lang"""
        item = self.spider.make_item(
            title="测试标题",
            content="测试正文",
            original_url="https://example.com/article/1",
        )
        assert item.source_type == "domestic"
        assert item.source_name == "test_source"
        assert item.lang == "zh"

    def test_passes_required_fields(self):
        """必填字段应正确传递"""
        item = self.spider.make_item(
            title="测试标题",
            content="测试正文",
            original_url="https://example.com/article/1",
        )
        assert item.title == "测试标题"
        assert item.content == "测试正文"
        assert item.original_url == "https://example.com/article/1"

    def test_passes_optional_fields(self):
        """通过 **kwargs 传递的可选字段应正确设置"""
        item = self.spider.make_item(
            title="测试标题",
            content="测试正文",
            original_url="https://example.com/article/1",
            author="作者名",
            summary="这是摘要",
            created_at="2026-06-08T10:00:00Z",
            location="成都",
            price=25.0,
            validity_end="2026-07-08T23:59:59Z",
            tags=["消费券", "成都"],
            images=["https://example.com/img1.png"],
        )
        assert item.author == "作者名"
        assert item.summary == "这是摘要"
        assert item.created_at == "2026-06-08T10:00:00Z"
        assert item.location == "成都"
        assert item.price == 25.0
        assert item.validity_end == "2026-07-08T23:59:59Z"
        assert item.tags == ["消费券", "成都"]
        assert item.images == ["https://example.com/img1.png"]

    def test_strips_title_whitespace(self):
        """title 首尾空白应被去除"""
        item = self.spider.make_item(
            title="  测试标题  ",
            content="测试正文",
            original_url="https://example.com/article/1",
        )
        assert item.title == "测试标题"

    def test_strips_content_whitespace(self):
        """content 首尾空白应被去除"""
        item = self.spider.make_item(
            title="测试标题",
            content="  测试正文  ",
            original_url="https://example.com/article/1",
        )
        assert item.content == "测试正文"

    def test_strips_url_whitespace(self):
        """original_url 首尾空白应被去除"""
        item = self.spider.make_item(
            title="测试标题",
            content="测试正文",
            original_url="  https://example.com/article/1  ",
        )
        assert item.original_url == "https://example.com/article/1"

    def test_handles_empty_title(self):
        """title 为空时应返回空字符串"""
        item = self.spider.make_item(
            title="",
            content="测试正文",
            original_url="https://example.com/article/1",
        )
        assert item.title == ""

    def test_handles_none_title(self):
        """title 为 None 时应返回空字符串"""
        item = self.spider.make_item(
            title=None,
            content="测试正文",
            original_url="https://example.com/article/1",
        )
        assert item.title == ""

    def test_extra_kwargs_not_passed_to_item(self):
        """不在 CrawlerItem 字段中的 kwargs 应被忽略"""
        item = self.spider.make_item(
            title="测试标题",
            content="测试正文",
            original_url="https://example.com/article/1",
            unknown_field="should_be_ignored",
        )
        # 不应抛出异常，unknown_field 已被 pop 消耗
        assert item.title == "测试标题"

    def test_subclass_override_source_fields(self):
        """子类覆盖 source_type/source_name/lang 后，make_item 应使用子类值"""

        class OverseasSpider(BaseSpider):
            name = "overseas_test"
            source_type = "overseas"
            source_name = "producthunt"
            lang = "en"

        spider = OverseasSpider()
        item = spider.make_item(
            title="Awesome Product",
            content="Description here",
            original_url="https://producthunt.com/posts/1",
        )
        assert item.source_type == "overseas"
        assert item.source_name == "producthunt"
        assert item.lang == "en"
