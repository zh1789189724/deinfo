"""
快速采集脚本 — 绕过 Scrapy 的 Twisted 代理问题，直接用 requests
采集数据 → CrawlerPipeline 清洗 → PushClient 推送 → 后端
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

# 设置代理
PROXY = os.environ.get("PROXY_URL", "http://127.0.0.1:7897")
proxies = {"http": PROXY, "https": PROXY} if PROXY else None

# ── 导入 Pipeline 和 PushClient ──
from crawler.items import CrawlerItem
from crawler.pipelines import CrawlerPipeline
from crawler.push_client import PushClient

pipeline = CrawlerPipeline()
client = PushClient()

def scrape_hackernews():
    """采集 Hacker News 热门"""
    print("[HN] 正在采集...")
    r = requests.get("https://news.ycombinator.com/", proxies=proxies, timeout=15)
    r.encoding = "utf-8"
    html = r.text

    # 简单解析：提取标题行和 subtext
    import html as html_mod
    items = []
    # 匹配 <span class="titleline"><a href="...">title</a></span>
    titlelines = re.findall(r'<span class="titleline">.*?</span>', html, re.DOTALL)
    for tl in titlelines[:15]:  # 前 15 条
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
                content=title,
                original_url=href,
            )
            # 经过 pipeline 清洗
            cleaned = pipeline.process_item(item, type("spider", (), {"name": "hackernews"})())
            if cleaned:
                items.append(cleaned)
        except Exception as e:
            print(f"  [HN] 解析失败: {e}")

    print(f"  [HN] 成功提取 {len(items)} 条")
    return items

def scrape_github_trending():
    """采集 GitHub Trending"""
    print("[GitHub] 正在采集...")
    r = requests.get("https://github.com/trending", proxies=proxies, timeout=15)
    html = r.text

    import html as html_mod
    items = []
    # 匹配 article.Box-row
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
            print(f"  [GitHub] 解析失败: {e}")

    print(f"  [GitHub] 成功提取 {len(items)} 条")
    return items

def scrape_producthunt():
    """采集 Product Hunt"""
    print("[PH] 正在采集...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }
    r = requests.get("https://www.producthunt.com/", proxies=proxies, headers=headers, timeout=15)
    html = r.text

    items = []
    # 从页面提取产品卡片（Product Hunt 是 React 渲染，提取 JSON 数据）
    # 查找 __NEXT_DATA__ 或 posts 相关脚本
    posts_match = re.search(r'"posts":\[(.*?)\]', html)
    if posts_match:
        print("  [PH] 找到内嵌数据，尝试解析...")

    # 简单的 class 匹配
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
            print(f"  [PH] 解析失败: {e}")

    print(f"  [PH] 成功提取 {len(items)} 条")
    return items

def scrape_domestic_sources():
    """采集国内可访问的源"""
    items = []

    # 成都市人民政府 - 通知公告
    print("[政府] 正在采集...")
    try:
        r = requests.get("http://www.chengdu.gov.cn/", timeout=10)
        print(f"  [政府] 状态码: {r.status_code}")
    except Exception as e:
        print(f"  [政府] 失败: {e}")

    return items

if __name__ == "__main__":
    print("=" * 50)
    print("DeInfo 爬虫 — 快速采集")
    print("=" * 50)

    all_items = []

    # 海外源（走代理）
    print("\n>>> 海外源 <<<")
    try:
        all_items.extend(scrape_hackernews())
    except Exception as e:
        print(f"[HN] 采集失败: {e}")

    try:
        all_items.extend(scrape_github_trending())
    except Exception as e:
        print(f"[GitHub] 采集失败: {e}")

    try:
        all_items.extend(scrape_producthunt())
    except Exception as e:
        print(f"[PH] 采集失败: {e}")

    print(f"\n>>> 共提取 {len(all_items)} 条内容")

    # 推送到后端
    if all_items:
        print("\n>>> 推送到后端 <<<")
        success_count = 0
        for item in all_items:
            result = client.push_one(item)
            if result.success:
                success_count += 1
            status = "✓" if result.success else "✗"
            print(f"  {status} {item.title[:40]}... ({result.status_code})")

        print(f"\n推送完成: {success_count}/{len(all_items)} 成功")

    print("\n完成!")
