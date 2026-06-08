"""
稳定爬虫服务 — 持续不断采集数据

在项目启动后作为后台进程运行，按配置的间隔不断采集各数据源。
不使用 Scrapy 框架（Windows 代理兼容问题），
直接使用 requests + proxy 采集。

用法：
    python run_continuous.py                    # 按 sources.py 中的 cron 调度
    python run_continuous.py --interval 60      # 所有源统一每 60 分钟采集一次
    python run_continuous.py --once             # 执行一次采集循环后退出
"""
from __future__ import annotations

import argparse
import html as html_mod
import logging
import os
import re
import sys
import time
from datetime import datetime

# ── 路径设置 ──
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests
import trafilatura

from crawler.items import CrawlerItem
from crawler.pipelines import CrawlerPipeline
from crawler.push_client import PushClient

# ── 代理配置 ──
PROXY = os.environ.get("PROXY_URL", "http://127.0.0.1:7897")
proxies: dict[str, str] | None = {"http": PROXY, "https": PROXY} if PROXY else None

# ── 全局共享 ──
pipeline = CrawlerPipeline()
client = PushClient()
logger = logging.getLogger("continuous_crawler")

# ── 默认 User-Agent ──
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def extract_content(url: str, fallback_text: str, max_chars: int = 1000) -> str:
    """尝试用 trafilatura 从 URL 提取正文

    如果提取失败或正文太短，返回 fallback_text。

    Args:
        url: 目标文章链接
        fallback_text: 兜底文本（通常是标题）
        max_chars: 截取前 N 个字符，默认 1000

    Returns:
        提取的正文文本或 fallback_text
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if text and len(text.strip()) > 50:
                return text[:max_chars]
    except Exception as e:
        logger.warning("正文提取失败 %s: %s", url, e)
    return fallback_text


# ═══════════════════════════════════════════════════════════════
# 各源采集函数（从 quick_scrape.py 复制已验证的代码，适配 logging）
# ═══════════════════════════════════════════════════════════════

def scrape_hackernews() -> list[CrawlerItem]:
    """采集 Hacker News 热门"""
    logger.info("[HN] 正在采集...")
    r = requests.get("https://news.ycombinator.com/", proxies=proxies, timeout=15)
    r.encoding = "utf-8"
    html = r.text

    items: list[CrawlerItem] = []
    # 匹配 <span class="titleline"><a href="...">title</a></span>
    titlelines = re.findall(r'<span class="titleline">.*?</span>', html, re.DOTALL)
    for tl in titlelines[:15]:
        try:
            title_match = re.search(r'<a[^>]*>(.*?)</a>', tl)
            href_match = re.search(r'<a href="(.*?)"', tl)
            if not title_match or not href_match:
                continue
            title = html_mod.unescape(re.sub(r'<[^>]+>', '', title_match.group(1))).strip()
            href = href_match.group(1)
            if href.startswith("item?"):
                href = "https://news.ycombinator.com/" + href

            item = CrawlerItem(
                source_type="overseas",
                source_name="hackernews",
                lang="en",
                title=title,
                content=extract_content(href, title),
                original_url=href,
            )
            cleaned = pipeline.process_item(item, type("spider", (), {"name": "hackernews"})())
            if cleaned:
                items.append(cleaned)
        except Exception as e:
            logger.warning("[HN] 解析失败: %s", e)

    logger.info("[HN] 成功提取 %d 条", len(items))
    return items


def scrape_github_trending() -> list[CrawlerItem]:
    """采集 GitHub Trending"""
    logger.info("[GitHub] 正在采集...")
    r = requests.get("https://github.com/trending", proxies=proxies, timeout=15)
    html = r.text

    items: list[CrawlerItem] = []
    rows = re.findall(r'<article class="Box-row.*?</article>', html, re.DOTALL)
    for row in rows[:15]:
        try:
            # 在 h2 block 内提取 repo 名称（避开 data-hydro-click 中的干扰）
            h2_match = re.search(r'<h2 class="h3 lh-condensed">(.*?)</h2>', row, re.DOTALL)
            if not h2_match:
                continue
            href_match = re.search(r'href="/([^"]+)"', h2_match.group(1))
            desc_match = re.search(r'<p[^>]*>(.*?)</p>', row, re.DOTALL)
            lang_match = re.search(r'<span itemprop="programmingLanguage">(.*?)</span>', row)
            if not href_match:
                continue
            repo = href_match.group(1)
            desc = html_mod.unescape(re.sub(r'<[^>]+>', '', desc_match.group(1))).strip() if desc_match else ""
            lang = lang_match.group(1).strip() if lang_match else ""

            tags = [lang] if lang else []
            item = CrawlerItem(
                source_type="overseas",
                source_name="github_trending",
                lang="en",
                title=repo,
                content=desc or repo,
                original_url=f"https://github.com/{repo}",
                tags=tags,
            )
            cleaned = pipeline.process_item(item, type("spider", (), {"name": "github_trending"})())
            if cleaned:
                items.append(cleaned)
        except Exception as e:
            logger.warning("[GitHub] 解析失败: %s", e)

    logger.info("[GitHub] 成功提取 %d 条", len(items))
    return items


def scrape_producthunt() -> list[CrawlerItem]:
    """采集 Product Hunt（兜底返回空列表不报错）"""
    logger.info("[PH] 正在采集...")
    headers = {
        "User-Agent": DEFAULT_UA,
        "Accept": "text/html,application/xhtml+xml",
    }
    items: list[CrawlerItem] = []
    try:
        r = requests.get("https://www.producthunt.com/", proxies=proxies, headers=headers, timeout=15)
        html = r.text

        from parsel import Selector
        sel = Selector(text=html)
        products = sel.css("div[class*='styles_item__'], a[class*='postItem'], div[class*='postItem']")

        for product in products[:10]:
            try:
                title = product.css("a[class*='title']::text, h2::text, [class*='title']::text").get("").strip()
                href = product.css("a[class*='title']::attr(href), a::attr(href)").get("") or ""
                if not title or not href:
                    continue
                if href.startswith("/"):
                    href = "https://www.producthunt.com" + href

                item = CrawlerItem(
                    source_type="overseas",
                    source_name="producthunt",
                    lang="en",
                    title=title,
                    content=title,
                    original_url=href,
                )
                cleaned = pipeline.process_item(item, type("spider", (), {"name": "producthunt"})())
                if cleaned:
                    items.append(cleaned)
            except Exception as e:
                logger.warning("[PH] 解析失败: %s", e)
    except Exception as e:
        logger.warning("[PH] 采集异常（可忽略）: %s", e)

    logger.info("[PH] 成功提取 %d 条", len(items))
    return items


# ═══════════════════════════════════════════════════════════════
# 国内源
# ═══════════════════════════════════════════════════════════════

def scrape_domestic_sources() -> list[CrawlerItem]:
    """采集国内可访问的源"""
    items: list[CrawlerItem] = []

    logger.info("[政府] 正在采集...")
    try:
        r = requests.get("http://www.chengdu.gov.cn/", timeout=10)
        logger.info("[政府] 状态码: %s", r.status_code)
    except Exception as e:
        logger.warning("[政府] 失败: %s", e)

    return items


# ═══════════════════════════════════════════════════════════════
# 调度映射
# ═══════════════════════════════════════════════════════════════

# source_name -> (scrape_func, default_cron)
SOURCE_SCRAPERS: dict[str, tuple] = {
    "hackernews": (scrape_hackernews, "0 */2 * * *"),
    "github_trending": (scrape_github_trending, "0 */3 * * *"),
    "producthunt": (scrape_producthunt, "0 */6 * * *"),
    "wechat_chengdu": (scrape_domestic_sources, "0 */6 * * *"),
    "douyin_chengdu": (scrape_domestic_sources, "0 */6 * * *"),
    "local_forum": (scrape_domestic_sources, "0 */6 * * *"),
    "gov_chengdu": (scrape_domestic_sources, "0 */6 * * *"),
}


# ═══════════════════════════════════════════════════════════════
# 采集与推送
# ═══════════════════════════════════════════════════════════════

def collect_and_push(source_name: str, scrape_func) -> int:
    """执行单个源的采集 -> pipeline 清洗 -> PushClient 推送

    Args:
        source_name: 数据源名称
        scrape_func: 采集函数，返回 list[CrawlerItem]

    Returns:
        成功推送的条数
    """
    try:
        items = scrape_func()
    except Exception as e:
        logger.error("[%s] 采集函数异常: %s", source_name, e, exc_info=True)
        return 0

    if not items:
        logger.info("[%s] 无有效数据，跳过推送", source_name)
        return 0

    success_count = 0
    for item in items:
        result = client.push_one(item)
        if result.success:
            success_count += 1
        status = "OK" if result.success else "FAIL"
        logger.info("  [%s] %s %s... (%d)", source_name, status, item.title[:40], result.status_code)

    logger.info("[%s] 推送完成: %d/%d 成功", source_name, success_count, len(items))
    return success_count


def run_collect_once(source_names: list[str] | None = None) -> dict[str, int]:
    """执行一次全量采集循环

    Args:
        source_names: 要采集的源名称列表，None 表示采集所有启用的源

    Returns:
        {source_name: success_count}
    """
    from config.sources import get_enabled_sources

    enabled = get_enabled_sources()
    results: dict[str, int] = {}

    if source_names is None:
        source_names = list(enabled.keys())

    for name in source_names:
        cfg = enabled.get(name)
        if cfg is None:
            logger.warning("[%s] 未在配置中找到，跳过", name)
            continue

        scraper_info = SOURCE_SCRAPERS.get(name)
        if scraper_info is None:
            logger.warning("[%s] 未注册采集函数，跳过", name)
            continue

        scrape_func, _ = scraper_info
        logger.info(">>> [%s] 开始采集 (%s) <<<", name, cfg["description"])
        count = collect_and_push(name, scrape_func)
        results[name] = count

    return results


# ═══════════════════════════════════════════════════════════════
# APScheduler 定时调度
# ═══════════════════════════════════════════════════════════════

def _cron_to_seconds(cron_expr: str) -> int:
    """粗略估算 cron 表达式的间隔秒数（用于 --interval 兼容）

    仅处理常见简化模式：
      - 0 */2 * * *  => 2 小时
      - 0 8,18 * * * => 12 小时
      - 0 8 * * 1,3,5 => 按 24 小时估算
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return 6 * 3600  # 默认 6 小时

    hour_part = parts[1]
    minute_part = parts[0]

    # 处理 */N 模式（每 N 小时/分钟）
    if hour_part.startswith("*/"):
        try:
            return int(hour_part[2:]) * 3600
        except ValueError:
            pass
    if minute_part.startswith("*/"):
        try:
            return int(minute_part[2:]) * 60
        except ValueError:
            pass

    # 处理固定时刻列表（如 "8,18"），取最小间隔
    if "," in hour_part:
        hours = sorted(int(h) for h in hour_part.split(",") if h.strip().isdigit())
        if len(hours) >= 2:
            diffs = [hours[i + 1] - hours[i] for i in range(len(hours) - 1)]
            return min(diffs) * 3600

    return 6 * 3600  # 兜底 6 小时


def start_scheduled_crawl(interval_minutes: int | None = None):
    """启动 APScheduler 定时调度

    Args:
        interval_minutes: 如果设置，所有源统一使用此间隔（分钟），不使用 cron
    """
    from config.sources import get_enabled_sources
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger

    enabled = get_enabled_sources()
    if not enabled:
        logger.warning("没有已启用的数据源")
        return

    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,
        }
    )

    registered_count = 0
    for name, cfg in enabled.items():
        scraper_info = SOURCE_SCRAPERS.get(name)
        if scraper_info is None:
            logger.warning("[%s] 未注册采集函数，跳过", name)
            continue

        scrape_func, default_cron = scraper_info

        # 确定触发方式
        if interval_minutes is not None:
            trigger = IntervalTrigger(minutes=interval_minutes)
            trigger_desc = f"每 {interval_minutes} 分钟"
        else:
            cron_str = cfg.get("cron", default_cron)
            try:
                parts = cron_str.strip().split()
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )
                trigger_desc = f"cron: {cron_str}"
            except Exception as e:
                logger.warning("[%s] cron 解析失败 '%s': %s，使用默认每 6 小时", name, cron_str, e)
                trigger = IntervalTrigger(hours=6)
                trigger_desc = "每 6 小时（兜底）"

        scheduler.add_job(
            func=collect_and_push,
            trigger=trigger,
            args=[name, scrape_func],
            id=name,
            name=name,
            replace_existing=True,
        )
        registered_count += 1
        logger.info("[%s] 定时任务已注册: %s", name, trigger_desc)

    logger.info("共注册 %d 个定时采集任务", registered_count)

    # 启动调度器
    scheduler.start()
    logger.info("调度器已启动，按 Ctrl+C 停止")

    try:
        # 保持主线程运行
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("收到停止信号，正在关闭...")
        scheduler.shutdown(wait=True)
        logger.info("爬虫服务已停止")


# ═══════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════

def setup_logging():
    """配置日志格式"""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="[%(asctime)s] [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DeInfo 稳定爬虫服务 — 持续不断采集数据",
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=None,
        help="统一采集间隔（分钟），覆盖 sources.py 中的 cron 配置",
    )
    parser.add_argument(
        "--once", "-o",
        action="store_true",
        help="只执行一次全量采集后退出",
    )
    return parser.parse_args()


def main():
    setup_logging()

    banner = """
    ╔══════════════════════════════════════════╗
    ║       DeInfo 稳定爬虫服务 v1.0           ║
    ╚══════════════════════════════════════════╝
    """
    logger.info(banner)
    logger.info("代理: %s", PROXY)
    logger.info("后端: %s", client.base_url)

    args = parse_args()

    if args.once:
        logger.info(">>> 执行一次全量采集 <<<")
        results = run_collect_once()
        total = sum(results.values())
        logger.info(">>> 全量采集完成: 共推送 %d 条 <<<", total)
        return

    # 启动前先执行一次
    logger.info(">>> 启动时执行一次全量采集 <<<")
    try:
        results = run_collect_once()
        total = sum(results.values())
        logger.info(">>> 启动采集完成: 共推送 %d 条 <<<", total)
    except Exception as e:
        logger.error("启动采集失败: %s", e, exc_info=True)

    # 进入定时调度
    start_scheduled_crawl(interval_minutes=args.interval)


if __name__ == "__main__":
    main()
