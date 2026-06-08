"""CrawlerPipeline — 数据清洗管道

参考接口契约第 5 章数据清洗规则。
流程: clean (HTML剥离 + 空白压缩) → truncate → validate → dedup_check

清洗步骤:
  | 步骤            | 规则                                    |
  |-----------------|----------------------------------------|
  | HTML 标签剥离    | 使用 parsel 去除所有 HTML 标签           |
  | 空白压缩         | 多个空白/换行压缩为单个空格               |
  | 长度截断         | title ≤ 300 字, content ≤ 50000 字     |
  | 编码统一         | 统一为 UTF-8 (Python 3 默认)            |
  | 敏感词过滤       | 命中黑名单关键词的直接丢弃                |
  | 必填字段检查     | source_type/source_name/title/content/original_url |
  | 去重检查         | 根据 original_url 检查是否已推送过       |
"""

import html
import logging
import os
import re

import parsel

from crawler.items import CrawlerItem

logger = logging.getLogger("pipeline")

# 默认敏感词黑名单
DEFAULT_BLOCKED_KEYWORDS: list[str] = [
    "赌博",
    "色情",
    "代开发票",
    "办证",
]

# 字段最大长度限制
MAX_TITLE_LENGTH = 300
MAX_CONTENT_LENGTH = 50000
MAX_SUMMARY_LENGTH = 300

# 必填字段列表
REQUIRED_FIELDS = [
    "source_type",
    "source_name",
    "lang",
    "title",
    "content",
    "original_url",
]

class CrawlerPipeline:
    """Scrapy Pipeline — 清洗 → 去重 → 验证

    作为 Scrapy 的 Item Pipeline 使用：
        pipeline = CrawlerPipeline()
        result = pipeline.process_item(item, spider)

    也可单独调用各步骤：
        cleaned_html = CrawlerPipeline.clean_html(html_text)
    """

    # 类级别去重集合（内存去重）
    _seen_urls: set[str] = set()

    @classmethod
    def clean_html(cls, text: str) -> str:
        """剥离 HTML 标签，仅保留纯文本内容。

        先移除 script/style 标签块，再用 parsel 或正则剥离剩余标签。
        同时处理 HTML 实体的反转义。

        Args:
            text: 包含 HTML 标签的原始文本

        Returns:
            剥离标签后的纯文本
        """
        if not text:
            return ""

        # 预清理：移除 script 和 style 块（避免 parsel 提取到它们的内容）
        text = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(
            r"<style[^>]*>.*?</style>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # 使用 parsel 进行 HTML 标签剥离
        selector = parsel.Selector(text=text)
        parts = selector.css("::text").getall()
        if parts:
            text = " ".join(parts)
        else:
            # 回退到正则表达式
            text = re.sub(r"<[^>]+>", "", text)

        # 反转义 HTML 实体（如 &amp; &lt; 等）
        text = html.unescape(text)

        return text

    @classmethod
    def compact_whitespace(cls, text: str) -> str:
        """压缩空白字符。

        将连续的空白字符（空格、换行、Tab）替换为单个空格，
        并去除首尾空白。

        Args:
            text: 原始文本

        Returns:
            空白压缩后的文本
        """
        if not text:
            return ""
        # 将所有空白序列（包括换行、Tab）替换为单个空格
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def truncate(cls, item: CrawlerItem) -> CrawlerItem:
        """截断超长字段。

        限制:
            - title ≤ 300 字符
            - content ≤ 50000 字符
            - summary ≤ 300 字符

        Args:
            item: CrawlerItem 实例

        Returns:
            截断后的新 CrawlerItem（不可变风格）
        """
        return CrawlerItem(
            source_type=item.source_type,
            source_name=item.source_name,
            lang=item.lang,
            title=item.title[:MAX_TITLE_LENGTH] if item.title else "",
            content=item.content[:MAX_CONTENT_LENGTH] if item.content else "",
            original_url=item.original_url,
            summary=item.summary[:MAX_SUMMARY_LENGTH] if item.summary else "",
            author=item.author,
            created_at=item.created_at,
            location=item.location,
            price=item.price,
            validity_end=item.validity_end,
            tags=list(item.tags),
            images=list(item.images),
        )

    @classmethod
    def validate(cls, item: CrawlerItem) -> tuple[bool, str]:
        """验证必填字段是否完整。

        必填字段: source_type, source_name, lang, title, content, original_url
        其中 source_type 必须为 "domestic" 或 "overseas"。
        命中敏感词黑名单的 item 也会被拒绝。

        Args:
            item: CrawlerItem 实例

        Returns:
            (valid, error_msg): valid=True 表示验证通过，error_msg 为空
        """
        # 检查必填字段是否为空
        for field in REQUIRED_FIELDS:
            value = getattr(item, field, "")
            if not value or not str(value).strip():
                return (False, f"必填字段 '{field}' 为空")

        # 检查 source_type 枚举值
        if item.source_type not in ("domestic", "overseas"):
            return (False, f"source_type 必须为 'domestic' 或 'overseas', 当前值: {item.source_type}")

        # 检查 title 和 content 去除空白后仍有内容
        if not item.title.strip():
            return (False, "title 仅包含空白字符")
        if not item.content.strip():
            return (False, "content 仅包含空白字符")

        # 敏感词过滤
        for keyword in DEFAULT_BLOCKED_KEYWORDS:
            if keyword in item.title or keyword in item.content:
                logger.warning("命中敏感词 '%s': %s", keyword, item.title)
                return (False, f"命中敏感词: {keyword}")

        return (True, "")

    @classmethod
    def classify_tags(cls, item: CrawlerItem) -> CrawlerItem:
        """根据关键词自动标记标签（接口契约第 11 章步骤 4）。

        当 tags 为空时，根据 title 和 content 中的关键词自动打标。
        仅对国内源有效。

        Args:
            item: CrawlerItem 实例

        Returns:
            带自动标签的新 CrawlerItem
        """
        if item.tags:
            return item  # 已有手动标签，跳过

        if item.source_type != "domestic":
            return item

        # 关键词 → 标签映射
        keyword_tag_map = [
            (["消费券", "优惠券", "补贴", "政府补贴"], "消费券"),
            (["招聘", "求职", "工作"], "招聘"),
            (["美食", "餐厅", "餐饮"], "美食"),
            (["展览", "演出", "活动"], "活动"),
            (["交通", "地铁", "公交"], "交通"),
            (["教育", "学校", "培训"], "教育"),
        ]

        combined_text = f"{item.title} {item.content}"
        new_tags = []
        for keywords, tag in keyword_tag_map:
            for kw in keywords:
                if kw in combined_text and tag not in new_tags:
                    new_tags.append(tag)
                    break

        return CrawlerItem(
            source_type=item.source_type,
            source_name=item.source_name,
            lang=item.lang,
            title=item.title,
            content=item.content,
            original_url=item.original_url,
            summary=item.summary,
            author=item.author,
            created_at=item.created_at,
            location=item.location,
            price=item.price,
            validity_end=item.validity_end,
            tags=new_tags or list(item.tags),
            images=list(item.images),
        )

    def dedup_check(self, item: CrawlerItem) -> tuple[bool, str]:
        """检查是否重复（按 original_url 去重）。

        先标准化 URL（移除末尾斜杠），然后在内存 set 中查找。
        可选择集成 Redis（当 REDIS_URL 环境变量设置时）。

        Args:
            item: CrawlerItem 实例

        Returns:
            (is_duplicate, source): 是否重复及来源描述
                is_duplicate=True 表示已存在，应丢弃
                source 描述去重来源（"memory" 或 "redis"）
        """
        # URL 标准化：统一移除末尾斜杠，但保留根路径 "/"
        url = item.original_url.rstrip("/") if item.original_url != "/" else item.original_url

        # 先尝试 Redis 去重（如果配置了 REDIS_URL）
        redis_available = self._check_redis(url)
        if redis_available is not None:
            return redis_available

        # 内存去重
        if url in self._seen_urls:
            return (True, "memory")

        self._seen_urls.add(url)
        return (False, "memory")

    def _check_redis(self, url: str) -> tuple[bool, str] | None:
        """尝试使用 Redis 进行去重检查。

        如果 REDIS_URL 环境变量未设置或连接失败，返回 None 表示降级到内存。

        Returns:
            (is_duplicate, "redis") 如果 Redis 可用
            None 如果 Redis 不可用
        """
        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url:
            return None

        try:
            import redis as redis_mod
            r = redis_mod.from_url(redis_url)
            key = f"crawler:seen_url:{url}"
            if r.exists(key):
                return (True, "redis")
            r.setex(key, 86400, "1")  # 24 小时过期
            return (False, "redis")
        except ImportError:
            return None
        except Exception as e:
            logger.warning("Redis 去重异常，降级到内存: %s", e)
            return None

    @classmethod
    def clear_dedup(cls) -> None:
        """清空内存去重集合。

        在 spider 完成爬取或需要重置去重状态时调用。
        """
        cls._seen_urls.clear()

    def process_item(self, item: CrawlerItem, spider) -> CrawlerItem | None:
        """Pipeline 主入口 — 依次执行清洗步骤。

        Args:
            item: spider 产出的 CrawlerItem
            spider: Scrapy Spider 实例（用于日志等）

        Returns:
            清洗后的 CrawlerItem，如果应丢弃则返回 None
        """
        spider_name = getattr(spider, "name", "unknown")
        logger.info("[%s] Pipeline 开始处理: %s", spider_name, item.original_url)

        # Step 1: 清洗 — HTML 剥离
        clean_title = self.clean_html(item.title)
        clean_content = self.clean_html(item.content)
        clean_summary = self.clean_html(item.summary) if item.summary else ""

        # Step 2: 清洗 — 空白压缩
        clean_title = self.compact_whitespace(clean_title)
        clean_content = self.compact_whitespace(clean_content)
        clean_summary = self.compact_whitespace(clean_summary) if clean_summary else ""

        # 构建清洗后的 Item（不可变风格，新建副本）
        cleaned_item = CrawlerItem(
            source_type=item.source_type,
            source_name=item.source_name,
            lang=item.lang,
            title=clean_title,
            content=clean_content,
            original_url=item.original_url,
            summary=clean_summary,
            author=item.author,
            created_at=item.created_at,
            location=item.location,
            price=item.price,
            validity_end=item.validity_end,
            tags=list(item.tags),
            images=list(item.images),
        )

        # Step 3: 截断
        cleaned_item = self.truncate(cleaned_item)

        # Step 4: 验证
        valid, error_msg = self.validate(cleaned_item)
        if not valid:
            logger.warning("[%s] 验证失败: %s | url=%s", spider_name, error_msg,
                           cleaned_item.original_url)
            return None

        # Step 5: 自动打标
        cleaned_item = self.classify_tags(cleaned_item)

        # Step 6: 去重检查
        is_dup, dup_source = self.dedup_check(cleaned_item)
        if is_dup:
            logger.info("[%s] 重复内容(%s)，已丢弃: %s", spider_name, dup_source,
                        cleaned_item.original_url)
            return None

        logger.info("[%s] Pipeline 处理完成: %s", spider_name, cleaned_item.title)
        return cleaned_item
