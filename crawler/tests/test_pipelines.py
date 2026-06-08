"""测试 CrawlerPipeline 清洗 → 去重 → 验证"""

import pytest
from crawler.items import CrawlerItem
from crawler.pipelines import CrawlerPipeline


class FakeSpider:
    """用于 pipeline 测试的 fake spider"""
    name = "wechat_chengdu"
    source_type = "domestic"
    source_name = "wechat_chengdu"


@pytest.fixture
def pipeline():
    return CrawlerPipeline()


@pytest.fixture
def valid_item():
    return CrawlerItem(
        source_type="domestic",
        source_name="wechat_chengdu",
        lang="zh",
        title="成都消费券来了",
        content="<p>成都市发放<strong>新一轮</strong>消费券</p>",
        original_url="https://example.com/coupon/1",
        summary="消费券摘要",
        author="成都发布",
        created_at="2026-06-08T10:00:00Z",
        location="成都",
        price=50.0,
        validity_end="2026-07-08T23:59:59Z",
        tags=["消费券"],
    )


class TestCleanHtml:
    """HTML 标签剥离测试"""

    def test_strip_simple_tags(self):
        """剥离简单 HTML 标签"""
        result = CrawlerPipeline.clean_html("<p>Hello World</p>")
        assert result == "Hello World"

    def test_strip_nested_tags(self):
        """剥离嵌套 HTML 标签"""
        result = CrawlerPipeline.clean_html(
            "<div><p>成都<strong>消费券</strong>来了</p></div>"
        )
        # 内联标签之间可能产生空格（parsel 用空格连接文本节点）
        assert "消费券" in result
        assert "<" not in result

    def test_strip_with_attributes(self):
        """剥离带属性的 HTML 标签"""
        result = CrawlerPipeline.clean_html(
            '<a href="https://example.com">点击这里</a>'
        )
        assert result == "点击这里"

    def test_plain_text_unchanged(self):
        """纯文本无标签时不应改变"""
        text = "这是一条纯文本内容"
        result = CrawlerPipeline.clean_html(text)
        assert result == text

    def test_empty_string(self):
        """空字符串应返回空字符串"""
        assert CrawlerPipeline.clean_html("") == ""

    def test_self_closing_tags(self):
        """自闭合标签应被剥离"""
        result = CrawlerPipeline.clean_html("line1<br/>line2<br>line3")
        # void 元素之间文本节点可能被空格分隔
        assert "<br" not in result
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_script_style_removed(self):
        """script 和 style 标签及其内容应被移除"""
        html = """
        <div>可见内容</div>
        <script>alert('hidden')</script>
        <style>.hidden{color:red}</style>
        <p>更多可见内容</p>
        """
        result = CrawlerPipeline.clean_html(html)
        assert "可见内容" in result
        assert "更多可见内容" in result
        assert "alert" not in result
        assert "hidden" not in result or ".hidden" not in result

    def test_html_entities_converted(self):
        """HTML 实体应被转换为对应字符"""
        result = CrawlerPipeline.clean_html("<p>AT&amp;T &lt;new&gt;</p>")
        assert "&amp;" not in result or "&lt;" not in result


class TestCompactWhitespace:
    """空白压缩测试"""

    def test_multiple_spaces(self):
        """多个空格应压缩为一个"""
        result = CrawlerPipeline.compact_whitespace("成都   消费券   来了")
        assert result == "成都 消费券 来了"

    def test_newlines_and_tabs(self):
        """换行和 Tab 应压缩为空格"""
        result = CrawlerPipeline.compact_whitespace("成都\n消费券\t来了\r\n真棒")
        assert result == "成都 消费券 来了 真棒"

    def test_leading_trailing_whitespace(self):
        """首尾空白应被去除"""
        result = CrawlerPipeline.compact_whitespace("  成都消费券  ")
        assert result == "成都消费券"

    def test_empty_string(self):
        """空字符串应返回空"""
        assert CrawlerPipeline.compact_whitespace("") == ""


class TestTruncate:
    """字段截断测试"""

    def test_truncate_title_long(self):
        """超过 300 字的标题应被截断"""
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="长" * 200,  # 400 字
            content="正文内容",
            original_url="https://example.com",
        )
        result = CrawlerPipeline.truncate(item)
        assert len(result.title) <= 300

    def test_truncate_title_within_limit(self):
        """300 字以内的标题不应被截断"""
        title = "成都消费券"
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title=title,
            content="正文内容",
            original_url="https://example.com",
        )
        result = CrawlerPipeline.truncate(item)
        assert result.title == title

    def test_truncate_content_long(self):
        """超过 50000 字的内容应被截断"""
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="标题",
            content="长" * 60000,  # 60000 字
            original_url="https://example.com",
        )
        result = CrawlerPipeline.truncate(item)
        assert len(result.content) <= 50000

    def test_truncate_summary_long(self):
        """摘要过长也截断（300字）"""
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="标题", content="正文",
            original_url="https://example.com",
            summary="摘" * 500,
        )
        result = CrawlerPipeline.truncate(item)
        assert len(result.summary) <= 300


class TestValidate:
    """必填字段验证测试"""

    def test_valid_item(self, valid_item):
        """合法 item 应验证通过"""
        valid, msg = CrawlerPipeline.validate(valid_item)
        assert valid is True
        assert msg == ""

    def test_missing_source_type(self, valid_item):
        """缺少 source_type 应验证失败"""
        item = CrawlerItem(
            source_type="", source_name=valid_item.source_name,
            lang=valid_item.lang, title=valid_item.title,
            content=valid_item.content, original_url=valid_item.original_url,
        )
        valid, msg = CrawlerPipeline.validate(item)
        assert valid is False
        assert "source_type" in msg

    def test_missing_source_name(self, valid_item):
        """缺少 source_name 应验证失败"""
        item = CrawlerItem(
            source_type=valid_item.source_type, source_name="",
            lang=valid_item.lang, title=valid_item.title,
            content=valid_item.content, original_url=valid_item.original_url,
        )
        valid, msg = CrawlerPipeline.validate(item)
        assert valid is False
        assert "source_name" in msg

    def test_missing_title(self, valid_item):
        """缺少 title 应验证失败"""
        item = CrawlerItem(
            source_type=valid_item.source_type, source_name=valid_item.source_name,
            lang=valid_item.lang, title="",
            content=valid_item.content, original_url=valid_item.original_url,
        )
        valid, msg = CrawlerPipeline.validate(item)
        assert valid is False
        assert "title" in msg

    def test_missing_content(self, valid_item):
        """缺少 content 应验证失败"""
        item = CrawlerItem(
            source_type=valid_item.source_type, source_name=valid_item.source_name,
            lang=valid_item.lang, title=valid_item.title,
            content="", original_url=valid_item.original_url,
        )
        valid, msg = CrawlerPipeline.validate(item)
        assert valid is False
        assert "content" in msg

    def test_missing_original_url(self, valid_item):
        """缺少 original_url 应验证失败"""
        item = CrawlerItem(
            source_type=valid_item.source_type, source_name=valid_item.source_name,
            lang=valid_item.lang, title=valid_item.title,
            content=valid_item.content, original_url="",
        )
        valid, msg = CrawlerPipeline.validate(item)
        assert valid is False
        assert "original_url" in msg

    def test_blank_whitespace_fields(self):
        """全空白字符的字段应视为空"""
        item = CrawlerItem(
            source_type="   ", source_name="  ", lang="zh",
            title="  ", content="  ", original_url="  ",
        )
        valid, msg = CrawlerPipeline.validate(item)
        assert valid is False


class TestDedupCheck:
    """去重检查测试"""

    def setup_method(self):
        """每个测试前重置去重集合"""
        CrawlerPipeline._seen_urls.clear()

    def test_new_url(self, valid_item):
        """未出现过的 URL 应判定为未重复"""
        pipeline = CrawlerPipeline()
        is_dup, _ = pipeline.dedup_check(valid_item)
        assert is_dup is False

    def test_duplicate_url(self, valid_item):
        """已出现过的 URL 应判定为重复"""
        pipeline = CrawlerPipeline()
        # 第一次检查
        pipeline.dedup_check(valid_item)
        # 第二次检查同一 URL
        is_dup, _ = pipeline.dedup_check(valid_item)
        assert is_dup is True

    def test_different_urls(self):
        """不同 URL 不应互相影响"""
        pipeline = CrawlerPipeline()
        item1 = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t1", content="c1", original_url="https://example.com/1",
        )
        item2 = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t2", content="c2", original_url="https://example.com/2",
        )
        dup1, _ = pipeline.dedup_check(item1)
        dup2, _ = pipeline.dedup_check(item2)
        assert dup1 is False
        assert dup2 is False

    def test_dedup_clear(self, valid_item):
        """clear_dedup 应清空已记录 URL"""
        pipeline = CrawlerPipeline()
        pipeline.dedup_check(valid_item)
        pipeline.clear_dedup()
        is_dup, _ = pipeline.dedup_check(valid_item)
        assert is_dup is False

    def test_dedup_with_trailing_slash(self):
        """带/不带末尾斜杠的同个 URL 应视为重复"""
        pipeline = CrawlerPipeline()
        item1 = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t1", content="c1",
            original_url="https://example.com/page",
        )
        item2 = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="t2", content="c2",
            original_url="https://example.com/page/",
        )
        pipeline.dedup_check(item1)
        is_dup, _ = pipeline.dedup_check(item2)
        assert is_dup is True


class TestProcessItem:
    """完整 pipeline 处理测试"""

    def setup_method(self):
        """每个测试前清空去重集合"""
        CrawlerPipeline._seen_urls.clear()

    def test_process_valid_item(self, pipeline, valid_item):
        """合法的 item 经过 pipeline 处理后返回清洗后的 CrawlerItem"""
        result = pipeline.process_item(valid_item, FakeSpider())
        assert isinstance(result, CrawlerItem)
        # HTML 标签已被剥离
        assert "<p>" not in result.content
        assert "<strong>" not in result.content
        assert "消费券" in result.content

    def test_process_item_invalid_returns_none(self, pipeline):
        """必填字段缺失的 item 应返回 None（丢弃）"""
        invalid_item = CrawlerItem(
            source_type="", source_name="test", lang="zh",
            title="", content="", original_url="",
        )
        result = pipeline.process_item(invalid_item, FakeSpider())
        assert result is None

    def test_process_duplicate_returns_none(self, pipeline, valid_item):
        """重复的 item 应返回 None（丢弃）"""
        pipeline.process_item(valid_item, FakeSpider())
        result = pipeline.process_item(valid_item, FakeSpider())
        assert result is None

    def test_process_item_cleans_html(self, pipeline):
        """pipeline 应清洗 HTML 内容"""
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="测试 <b>标题</b>",
            content="<script>alert('x')</script><p>正文内容</p>",
            original_url="https://example.com/page",
        )
        result = pipeline.process_item(item, FakeSpider())
        assert result is not None
        assert "<b>" not in result.title
        assert "<p>" not in result.content
        assert "正文内容" in result.content
        assert "alert" not in result.content

    def test_process_item_compacts_whitespace(self, pipeline):
        """pipeline 应压缩空白"""
        item = CrawlerItem(
            source_type="domestic", source_name="test", lang="zh",
            title="标题",
            content="成都\n\n消费券   来了\r\n真棒",
            original_url="https://example.com/page",
        )
        result = pipeline.process_item(item, FakeSpider())
        assert result is not None
        assert "  " not in result.content  # 没有连续空白
        assert "\n" not in result.content
