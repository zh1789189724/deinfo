"""
国内 Spider 单元测试

测试 4 个 domestic spider 的 parse() 方法：
- WechatChengduSpider  — 成都本地公众号文章
- DouyinChengduSpider  — 成都同城抖音
- LocalForumSpider     — 成都本地论坛
- GovChengduSpider     — 成都政府补贴/消费券

覆盖路径：正常提取、空结果、异常 HTML。
"""
import pytest
from scrapy.http import HtmlResponse

from crawler.items import CrawlerItem


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
# WechatChengduSpider 测试
# ============================================================

class TestWechatChengduSpider:
    """WechatChengduSpider parse() 测试"""

    NORMAL_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="成都高新区人才补贴新政发布" />
  <meta property="article:published_time" content="2026-06-08T10:00:00Z" />
  <meta name="profile:username" content="成都发布" />
</head>
<body>
  <article id="js_article">
    <h1>成都高新区人才补贴新政发布</h1>
    <p>成都高新区近日发布了最新的人才补贴政策，涵盖租房补贴、购房补贴和创业启动资金。</p>
    <p>本次新政覆盖高新区、天府新区、锦江区等多个区域。符合条件的申请人可通过官方渠道提交材料。</p>
  </article>
</body>
</html>"""

    EMPTY_HTML = """<!DOCTYPE html>
<html><head><title>页面不存在</title></head>
<body><p>该文章已被删除或页面不存在</p></body>
</html>"""

    MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Error</title></head>
<body>Service Unavailable</body>
</html>"""

    NO_META_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>成都美食攻略（不使用og:title的页面）</title>
</head>
<body>
  <article id="js_article">
    <h1>成都美食攻略</h1>
    <p>推荐成都本地人最爱吃的10家火锅店。</p>
  </article>
</body>
</html>"""

    def test_normal_parse(self):
        """正常路径：从 HTML 中提取 1 条公众号文章"""
        from crawler.spiders.domestic.wechat_chengdu import WechatChengduSpider
        spider = WechatChengduSpider()
        response = _mock_response(
            "https://mp.weixin.qq.com/s/test_article_001",
            self.NORMAL_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert isinstance(item, CrawlerItem)
        assert item.source_type == "domestic"
        assert item.source_name == "wechat_chengdu"
        assert item.lang == "zh"

        assert item.title == "成都高新区人才补贴新政发布"
        assert "租房补贴" in item.content
        assert "创业启动资金" in item.content
        assert item.original_url == "https://mp.weixin.qq.com/s/test_article_001"
        assert item.author == "成都发布"
        assert item.created_at == "2026-06-08T10:00:00Z"

    def test_missing_meta_tags(self):
        """缺少 og:title 和 profile:username 时，从页面其他位置提取"""
        from crawler.spiders.domestic.wechat_chengdu import WechatChengduSpider
        spider = WechatChengduSpider()
        response = _mock_response(
            "https://mp.weixin.qq.com/s/test_no_meta",
            self.NO_META_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert item.title != ""  # 至少能从 h1 或 title 取到值
        assert item.author == ""  # 无作者信息时保持空字符串

    def test_empty_parse(self):
        """空结果：页面无有效内容时返回空列表"""
        from crawler.spiders.domestic.wechat_chengdu import WechatChengduSpider
        spider = WechatChengduSpider()
        response = _mock_response(
            "https://mp.weixin.qq.com/s/test_empty",
            self.EMPTY_HTML,
        )
        items = list(spider.parse(response))
        assert len(items) == 0

    def test_malformed_html(self):
        """异常路径：HTML 结构不完整时不应抛出异常"""
        from crawler.spiders.domestic.wechat_chengdu import WechatChengduSpider
        spider = WechatChengduSpider()
        response = _mock_response(
            "https://mp.weixin.qq.com/s/test_broken",
            self.MALFORMED_HTML,
        )
        try:
            items = list(spider.parse(response))
            assert len(items) == 0
        except Exception as exc:
            pytest.fail(f"malformed HTML raised exception: {exc}")


# ============================================================
# DouyinChengduSpider 测试
# ============================================================

class TestDouyinChengduSpider:
    """DouyinChengduSpider parse() 测试"""

    NORMAL_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="成都探店！藏在巷子里的宝藏咖啡店" />
  <meta name="description" content="成都探店打卡 #成都美食 #咖啡探店 #成都旅游 这家藏在宽窄巷子附近的咖啡店真的太有感觉了！" />
  <meta property="og:url" content="https://www.douyin.com/video/123456789" />
</head>
<body>
  <div class="video-info">
    <div class="poi-info">
      <span class="poi-name">宽窄巷子·成都</span>
    </div>
  </div>
</body>
</html>"""

    NO_LOCATION_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="成都探店！藏在巷子里的宝藏咖啡店" />
  <meta name="description" content="成都探店打卡 #成都美食 #咖啡探店 这家店真的太有感觉了！" />
  <meta property="og:url" content="https://www.douyin.com/video/123456789" />
</head>
<body>
  <div class="video-info">
    <!-- 没有 POI 信息 -->
  </div>
</body>
</html>"""

    NO_TAGS_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="成都的晚霞太美了" />
  <meta name="description" content="成都的晚霞真的让人心醉，随手一拍就是大片" />
  <meta property="og:url" content="https://www.douyin.com/video/987654321" />
</head>
<body>
  <div class="video-info">
    <div class="poi-info">
      <span class="poi-name">成都·金融城</span>
    </div>
  </div>
</body>
</html>"""

    EMPTY_HTML = """<!DOCTYPE html>
<html><head><title>抖音</title></head>
<body><p>视频不存在或已删除</p></body>
</html>"""

    MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Broken</title></head>
<body>No proper video data</body>
</html>"""

    def test_normal_parse(self):
        """正常路径：从 HTML 中提取 1 条抖音视频"""
        from crawler.spiders.domestic.douyin_chengdu import DouyinChengduSpider
        spider = DouyinChengduSpider()
        response = _mock_response(
            "https://www.douyin.com/video/123456789",
            self.NORMAL_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert isinstance(item, CrawlerItem)
        assert item.source_type == "domestic"
        assert item.source_name == "douyin_chengdu"
        assert item.lang == "zh"

        assert item.title == "成都探店！藏在巷子里的宝藏咖啡店"
        assert "咖啡探店" in item.content
        assert "成都旅游" in item.content
        assert item.original_url == "https://www.douyin.com/video/123456789"
        assert item.location == "宽窄巷子·成都"
        # 验证话题标签被提取
        assert "成都美食" in item.tags
        assert "咖啡探店" in item.tags
        assert "成都旅游" in item.tags

    def test_no_location(self):
        """没有 POI 位置信息时 location 为空"""
        from crawler.spiders.domestic.douyin_chengdu import DouyinChengduSpider
        spider = DouyinChengduSpider()
        response = _mock_response(
            "https://www.douyin.com/video/123456789",
            self.NO_LOCATION_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert item.location == ""
        assert "成都美食" in item.tags

    def test_no_tags(self):
        """没有话题标签时 tags 为空列表"""
        from crawler.spiders.domestic.douyin_chengdu import DouyinChengduSpider
        spider = DouyinChengduSpider()
        response = _mock_response(
            "https://www.douyin.com/video/987654321",
            self.NO_TAGS_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert item.location == "成都·金融城"
        assert item.tags == []

    def test_empty_parse(self):
        """空结果：视频不存在时返回空列表"""
        from crawler.spiders.domestic.douyin_chengdu import DouyinChengduSpider
        spider = DouyinChengduSpider()
        response = _mock_response(
            "https://www.douyin.com/video/000000",
            self.EMPTY_HTML,
        )
        items = list(spider.parse(response))
        assert len(items) == 0

    def test_malformed_html(self):
        """异常路径：HTML 结构不完整时不应抛出异常"""
        from crawler.spiders.domestic.douyin_chengdu import DouyinChengduSpider
        spider = DouyinChengduSpider()
        response = _mock_response(
            "https://www.douyin.com/video/broken",
            self.MALFORMED_HTML,
        )
        try:
            items = list(spider.parse(response))
            assert len(items) == 0
        except Exception as exc:
            pytest.fail(f"malformed HTML raised exception: {exc}")


# ============================================================
# LocalForumSpider 测试
# ============================================================

class TestLocalForumSpider:
    """LocalForumSpider parse() 测试"""

    NORMAL_HTML = """<!DOCTYPE html>
<html>
<head><title>成都吃喝玩乐 - 天府社区</title></head>
<body>
  <div class="forum-board">
    <span>成都生活 > 美食探店</span>
  </div>
  <h1 class="post-title">推荐一家性价比超高的川菜馆</h1>
  <div class="post-meta">
    <span class="author-name">美食达人小王</span>
    <time datetime="2026-06-07T14:30:00Z">2026-06-07 14:30</time>
  </div>
  <div class="post-content">
    <p>今天在春熙路附近发现了一家新开的川菜馆，价格实惠味道正宗。</p>
    <p>推荐菜品：水煮鱼、麻婆豆腐、回锅肉。人均消费50元左右。</p>
  </div>
</body>
</html>"""

    MISSING_AUTHOR_HTML = """<!DOCTYPE html>
<html>
<head><title>成都租房信息</title></head>
<body>
  <div class="forum-board">
    <span>成都生活 > 租房信息</span>
  </div>
  <h1 class="post-title">高新区套一转租</h1>
  <div class="post-meta">
    <!-- 没有作者信息 -->
    <time datetime="2026-06-06T09:00:00Z">2026-06-06 09:00</time>
  </div>
  <div class="post-content">
    <p>高新区地铁口精装套一转租，月租1800。</p>
  </div>
</body>
</html>"""

    EMPTY_HTML = """<!DOCTYPE html>
<html><head><title>天府社区</title></head>
<body><p>暂无内容</p></body>
</html>"""

    MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Broken</title></head>
<body>Forum temporarily unavailable</body>
</html>"""

    def test_normal_parse(self):
        """正常路径：从 HTML 中提取 1 条论坛帖子"""
        from crawler.spiders.domestic.local_forum import LocalForumSpider
        spider = LocalForumSpider()
        response = _mock_response(
            "https://bbs.tianfuchengdu.com/thread/12345",
            self.NORMAL_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert isinstance(item, CrawlerItem)
        assert item.source_type == "domestic"
        assert item.source_name == "local_forum"
        assert item.lang == "zh"

        assert item.title == "推荐一家性价比超高的川菜馆"
        assert "春熙路" in item.content
        assert "水煮鱼" in item.content
        assert item.original_url == "https://bbs.tianfuchengdu.com/thread/12345"
        assert item.author == "美食达人小王"
        assert item.created_at == "2026-06-07T14:30:00Z"
        assert item.location == "成都生活 > 美食探店"

    def test_missing_author(self):
        """缺少作者信息时 author 为空"""
        from crawler.spiders.domestic.local_forum import LocalForumSpider
        spider = LocalForumSpider()
        response = _mock_response(
            "https://bbs.tianfuchengdu.com/thread/67890",
            self.MISSING_AUTHOR_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert item.title == "高新区套一转租"
        assert item.author == ""
        assert item.created_at == "2026-06-06T09:00:00Z"
        assert item.location == "成都生活 > 租房信息"

    def test_empty_parse(self):
        """空结果：页面无帖子时返回空列表"""
        from crawler.spiders.domestic.local_forum import LocalForumSpider
        spider = LocalForumSpider()
        response = _mock_response(
            "https://bbs.tianfuchengdu.com/empty",
            self.EMPTY_HTML,
        )
        items = list(spider.parse(response))
        assert len(items) == 0

    def test_malformed_html(self):
        """异常路径：HTML 结构不完整时不应抛出异常"""
        from crawler.spiders.domestic.local_forum import LocalForumSpider
        spider = LocalForumSpider()
        response = _mock_response(
            "https://bbs.tianfuchengdu.com/broken",
            self.MALFORMED_HTML,
        )
        try:
            items = list(spider.parse(response))
            assert len(items) == 0
        except Exception as exc:
            pytest.fail(f"malformed HTML raised exception: {exc}")


# ============================================================
# GovChengduSpider 测试
# ============================================================

class TestGovChengduSpider:
    """GovChengduSpider parse() 测试"""

    NORMAL_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>成都市商务局关于发放2026年第二批消费券的通知</title>
  <meta name="publish-date" content="2026-06-05" />
</head>
<body>
  <div class="article-container">
    <h1>成都市商务局关于发放2026年第二批消费券的通知</h1>
    <div class="article-meta">
      <span class="date">发布日期：2026-06-05</span>
      <span class="source">来源：成都市商务局</span>
    </div>
    <div class="article-content">
      <p>为促进消费回暖，成都市商务局决定发放2026年第二批消费券，总金额5000万元。</p>
      <p>本次消费券涵盖餐饮、零售、文旅等多个领域，市民可通过支付宝、微信等平台领取。</p>
      <p>领取时间：2026年6月15日至6月30日。</p>
    </div>
  </div>
</body>
</html>"""

    # 包含多重补贴关键词
    TAGS_MULTIPLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>成都高新区企业研发补贴和税收优惠政策通知</title>
  <meta name="publish-date" content="2026-06-01" />
</head>
<body>
  <div class="article-container">
    <h1>成都高新区企业研发补贴和税收优惠政策通知</h1>
    <div class="article-content">
      <p>成都高新区对符合条件的企业给予研发补贴，同时享受税收优惠政策。</p>
      <p>补贴金额最高可达500万元，税收优惠涵盖企业所得税减免。</p>
    </div>
  </div>
</body>
</html>"""

    NO_DATE_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>成都市垃圾分类新规</title>
</head>
<body>
  <div class="article-container">
    <h1>成都市垃圾分类新规</h1>
    <div class="article-content">
      <p>成都市将于下月起实施垃圾分类新规，请市民提前做好准备。</p>
    </div>
  </div>
</body>
</html>"""

    EMPTY_HTML = """<!DOCTYPE html>
<html><head><title>成都市政府</title></head>
<body><p>页面维护中</p></body>
</html>"""

    MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Broken</title></head>
<body>Server Error</body>
</html>"""

    def test_normal_parse(self):
        """正常路径：从 HTML 中提取 1 条政府公告"""
        from crawler.spiders.domestic.gov_chengdu import GovChengduSpider
        spider = GovChengduSpider()
        response = _mock_response(
            "https://www.cd.gov.cn/gov/2026/notice/001",
            self.NORMAL_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert isinstance(item, CrawlerItem)
        assert item.source_type == "domestic"
        assert item.source_name == "gov_chengdu"
        assert item.lang == "zh"

        assert item.title == "成都市商务局关于发放2026年第二批消费券的通知"
        assert "消费券" in item.content
        assert "5000万元" in item.content
        assert item.original_url == "https://www.cd.gov.cn/gov/2026/notice/001"
        assert item.created_at == "2026-06-05"
        # 验证自动标签：内容包含"消费券"
        assert "消费券" in item.tags

    def test_tags_detection(self):
        """自动标签：内容包含多个补贴关键词时生成对应标签"""
        from crawler.spiders.domestic.gov_chengdu import GovChengduSpider
        spider = GovChengduSpider()
        response = _mock_response(
            "https://www.cd.gov.cn/gov/2026/notice/002",
            self.TAGS_MULTIPLE_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        # 应检测到"补贴"和"税收优惠"两个标签
        assert "补贴" in item.tags
        assert "税收优惠" in item.tags

    def test_no_date(self):
        """缺少发布日期时 created_at 为空"""
        from crawler.spiders.domestic.gov_chengdu import GovChengduSpider
        spider = GovChengduSpider()
        response = _mock_response(
            "https://www.cd.gov.cn/gov/2026/notice/003",
            self.NO_DATE_HTML,
        )
        items = list(spider.parse(response))

        assert len(items) == 1
        item = items[0]
        assert item.title == "成都市垃圾分类新规"
        assert item.created_at == ""

    def test_empty_parse(self):
        """空结果：页面无公告时返回空列表"""
        from crawler.spiders.domestic.gov_chengdu import GovChengduSpider
        spider = GovChengduSpider()
        response = _mock_response(
            "https://www.cd.gov.cn/gov/empty",
            self.EMPTY_HTML,
        )
        items = list(spider.parse(response))
        assert len(items) == 0

    def test_malformed_html(self):
        """异常路径：HTML 结构不完整时不应抛出异常"""
        from crawler.spiders.domestic.gov_chengdu import GovChengduSpider
        spider = GovChengduSpider()
        response = _mock_response(
            "https://www.cd.gov.cn/gov/broken",
            self.MALFORMED_HTML,
        )
        try:
            items = list(spider.parse(response))
            assert len(items) == 0
        except Exception as exc:
            pytest.fail(f"malformed HTML raised exception: {exc}")
