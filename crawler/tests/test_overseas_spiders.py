"""
海外 Spider 单元测试

测试 3 个海外 spider 的 parse() 方法：
- ProductHuntSpider
- HackerNewsSpider
- GitHubTrendingSpider

覆盖路径：正常提取、空结果、异常 HTML。
"""
import pytest
from scrapy.http import HtmlResponse

from crawler.items import CrawlerItem
from crawler.spiders.overseas.producthunt import ProductHuntSpider
from crawler.spiders.overseas.hackernews import HackerNewsSpider
from crawler.spiders.overseas.github_trending import GitHubTrendingSpider


# ============================================================
# 辅助函数
# ============================================================

def _mock_response(url: str, html: str) -> HtmlResponse:
    """创建模拟的 Scrapy HtmlResponse"""
    return HtmlResponse(
        url=url,
        body=html.encode("utf-8"),
        encoding="utf-8",
    )


# ============================================================
# ProductHuntSpider 测试
# ============================================================

class TestProductHuntSpider:
    """ProductHuntSpider parse() 测试"""

    NORMAL_HTML = """<!DOCTYPE html>
<html>
<head><title>Product Hunt</title></head>
<body>
  <div class="styles_item__zgJhV">
    <a class="styles_title__rbVwl" href="/posts/ai-writer-pro">AI Writer Pro</a>
    <div class="styles_tagline__vHkFj">The best AI writing assistant for professionals</div>
    <div class="styles_topics__pOjXA">
      <a class="topic" href="/topics/ai">AI</a>
      <a class="topic" href="/topics/writing">Writing</a>
    </div>
    <button class="styles_vote__U2GdT">
      <span class="styles_votes_count__xYzAb">456</span>
    </button>
  </div>
  <div class="styles_item__zgJhV">
    <a class="styles_title__rbVwl" href="/posts/design-toolkit">Design Toolkit 2026</a>
    <div class="styles_tagline__vHkFj">A complete design system for modern web apps</div>
    <div class="styles_topics__pOjXA">
      <a class="topic" href="/topics/design">Design</a>
      <a class="topic" href="/topics/developer-tools">Developer Tools</a>
    </div>
    <button class="styles_vote__U2GdT">
      <span class="styles_votes_count__xYzAb">789</span>
    </button>
  </div>
</body>
</html>"""

    EMPTY_HTML = """<!DOCTYPE html>
<html><head><title>Product Hunt</title></head>
<body><p>No posts today</p></body>
</html>"""

    MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Broken</title></head>
<body><div>No proper structure here</div></body>
</html>"""

    def test_normal_parse(self):
        """正常路径：从 HTML 中提取 2 条产品"""
        spider = ProductHuntSpider()
        response = _mock_response("https://www.producthunt.com/", self.NORMAL_HTML)
        items = list(spider.parse(response))

        assert len(items) == 2
        for item in items:
            assert isinstance(item, CrawlerItem)
            assert item.source_type == "overseas"
            assert item.source_name == "producthunt"
            assert item.lang == "en"

        # 验证第一条产品的字段
        item0 = items[0]
        assert item0.title == "AI Writer Pro"
        assert "The best AI writing assistant for professionals" in item0.content
        assert item0.original_url == "https://www.producthunt.com/posts/ai-writer-pro"
        assert "AI" in item0.tags
        assert "Writing" in item0.tags

        # 验证第二条产品
        item1 = items[1]
        assert item1.title == "Design Toolkit 2026"
        assert "design system for modern web apps" in item1.content
        assert item1.original_url == "https://www.producthunt.com/posts/design-toolkit"
        assert "Design" in item1.tags
        assert "Developer Tools" in item1.tags

    def test_empty_parse(self):
        """空结果：页面无产品时返回空列表"""
        spider = ProductHuntSpider()
        response = _mock_response("https://www.producthunt.com/", self.EMPTY_HTML)
        items = list(spider.parse(response))

        assert len(items) == 0

    def test_malformed_html(self):
        """异常路径：HTML 结构不完整时不应抛出异常"""
        spider = ProductHuntSpider()
        response = _mock_response("https://www.producthunt.com/", self.MALFORMED_HTML)
        try:
            items = list(spider.parse(response))
            assert len(items) == 0
        except Exception as exc:
            pytest.fail(f"malformed HTML raised exception: {exc}")


# ============================================================
# HackerNewsSpider 测试
# ============================================================

class TestHackerNewsSpider:
    """HackerNewsSpider parse() 测试"""

    NORMAL_HTML = """<!DOCTYPE html>
<html>
<head><title>Hacker News</title></head>
<body>
  <table class="itemlist">
    <tr class="athing" id="40000001">
      <td class="title">
        <span class="titleline">
          <a href="https://example.com/rust-optimization">Rust Optimization Techniques</a>
        </span>
      </td>
    </tr>
    <tr>
      <td class="subtext">
        <span class="score" id="score_40000001">342 points</span>
        by <a href="user?id=rustacean">rustacean</a>
        <a href="item?id=40000001">87 comments</a>
      </td>
    </tr>
    <tr class="spacer"><td></td></tr>
    <tr class="athing" id="40000002">
      <td class="title">
        <span class="titleline">
          <a href="https://example.com/ai-paper-2026">A New Approach to LLM Reasoning</a>
        </span>
      </td>
    </tr>
    <tr>
      <td class="subtext">
        <span class="score" id="score_40000002">568 points</span>
        by <a href="user?id=airesearcher">airesearcher</a>
        <a href="item?id=40000002">234 comments</a>
      </td>
    </tr>
  </table>
</body>
</html>"""

    EMPTY_HTML = """<!DOCTYPE html>
<html><head><title>Hacker News</title></head>
<body><table class="itemlist"><tr><td>No stories yet.</td></tr></table></body>
</html>"""

    MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Broken</title></head>
<body>Not a proper HN page</body>
</html>"""

    def test_normal_parse(self):
        """正常路径：从 HTML 中提取 2 条帖子"""
        spider = HackerNewsSpider()
        response = _mock_response("https://news.ycombinator.com/", self.NORMAL_HTML)
        items = list(spider.parse(response))

        assert len(items) == 2
        for item in items:
            assert isinstance(item, CrawlerItem)
            assert item.source_type == "overseas"
            assert item.source_name == "hackernews"
            assert item.lang == "en"

        # 验证第一条帖子
        item0 = items[0]
        assert item0.title == "Rust Optimization Techniques"
        assert item0.original_url == "https://example.com/rust-optimization"
        assert item0.author == "rustacean"

        # 验证第二条帖子
        item1 = items[1]
        assert item1.title == "A New Approach to LLM Reasoning"
        assert item1.original_url == "https://example.com/ai-paper-2026"
        assert item1.author == "airesearcher"

    def test_empty_parse(self):
        """空结果：页面无帖子时返回空列表"""
        spider = HackerNewsSpider()
        response = _mock_response("https://news.ycombinator.com/", self.EMPTY_HTML)
        items = list(spider.parse(response))

        assert len(items) == 0

    def test_malformed_html(self):
        """异常路径：HTML 结构不完整时不应抛出异常"""
        spider = HackerNewsSpider()
        response = _mock_response("https://news.ycombinator.com/", self.MALFORMED_HTML)
        try:
            items = list(spider.parse(response))
            assert len(items) == 0
        except Exception as exc:
            pytest.fail(f"malformed HTML raised exception: {exc}")


# ============================================================
# GitHubTrendingSpider 测试
# ============================================================

class TestGitHubTrendingSpider:
    """GitHubTrendingSpider parse() 测试"""

    NORMAL_HTML = """<!DOCTYPE html>
<html>
<head><title>GitHub Trending</title></head>
<body>
  <article class="Box-row">
    <h2>
      <a href="/torvalds/linux">torvalds / linux</a>
    </h2>
    <p>The Linux kernel source tree</p>
    <div class="f6 color-fg-muted mt-2">
      <span class="d-inline-block mr-3" itemprop="programmingLanguage">C</span>
      <a class="topic-tag" href="/torvalds/linux/topics/kernel">kernel</a>
      <a class="topic-tag" href="/torvalds/linux/topics/os">os</a>
      <span class="d-inline-block float-sm-right">5,432 stars today</span>
    </div>
  </article>
  <article class="Box-row">
    <h2>
      <a href="/fastapi/fastapi">fastapi / fastapi</a>
    </h2>
    <p>A high-performance web framework for building APIs with Python</p>
    <div class="f6 color-fg-muted mt-2">
      <span class="d-inline-block mr-3" itemprop="programmingLanguage">Python</span>
      <a class="topic-tag" href="/fastapi/fastapi/topics/python">python</a>
      <a class="topic-tag" href="/fastapi/fastapi/topics/api">api</a>
      <span class="d-inline-block float-sm-right">1,234 stars today</span>
    </div>
  </article>
</body>
</html>"""

    EMPTY_HTML = """<!DOCTYPE html>
<html><head><title>GitHub Trending</title></head>
<body><p>No trending repositories today.</p></body>
</html>"""

    MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Broken</title></head>
<body>No proper structure here</body>
</html>"""

    def test_normal_parse(self):
        """正常路径：从 HTML 中提取 2 个仓库"""
        spider = GitHubTrendingSpider()
        response = _mock_response("https://github.com/trending", self.NORMAL_HTML)
        items = list(spider.parse(response))

        assert len(items) == 2
        for item in items:
            assert isinstance(item, CrawlerItem)
            assert item.source_type == "overseas"
            assert item.source_name == "github_trending"
            assert item.lang == "en"

        # 验证第一个仓库
        item0 = items[0]
        assert item0.title == "torvalds/linux"
        assert "Linux kernel source tree" in item0.content
        assert item0.original_url == "https://github.com/torvalds/linux"
        assert "C" in item0.tags
        assert "kernel" in item0.tags
        assert "os" in item0.tags

        # 验证第二个仓库
        item1 = items[1]
        assert item1.title == "fastapi/fastapi"
        assert "high-performance web framework" in item1.content
        assert item1.original_url == "https://github.com/fastapi/fastapi"
        assert "Python" in item1.tags
        assert "python" in item1.tags
        assert "api" in item1.tags

    def test_empty_parse(self):
        """空结果：页面无仓库时返回空列表"""
        spider = GitHubTrendingSpider()
        response = _mock_response("https://github.com/trending", self.EMPTY_HTML)
        items = list(spider.parse(response))

        assert len(items) == 0

    def test_malformed_html(self):
        """异常路径：HTML 结构不完整时不应抛出异常"""
        spider = GitHubTrendingSpider()
        response = _mock_response("https://github.com/trending", self.MALFORMED_HTML)
        try:
            items = list(spider.parse(response))
            assert len(items) == 0
        except Exception as exc:
            pytest.fail(f"malformed HTML raised exception: {exc}")
