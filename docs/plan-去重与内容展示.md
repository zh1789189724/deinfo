# Plan: 后端去重 + 详情页完整内容

## Phase 1：后端去重（低难度，立即做）

### 改动文件

| 文件 | 改动 |
|------|------|
| `GlobalService.java` | `processAndSave()` 开头检查 `original_url` 是否已存在 |
| `ContentService.java` | `processAndSave()` 开头检查 `original_url` 是否已存在 |
| `schema.sql` | 给 `global_content.original_url` 和 `deal.original_url` 加唯一索引 |

### 逻辑

```java
// GlobalService.processAndSave() 开头:
if (contentData.get("originalUrl") != null) {
    String url = (String) contentData.get("originalUrl");
    LambdaQueryWrapper<GlobalContent> wrapper = new LambdaQueryWrapper<>();
    wrapper.eq(GlobalContent::getOriginalUrl, url);
    if (globalContentService.count(wrapper) > 0) {
        log.info("重复内容，跳过: {}", url);
        return null; // 或返回已有记录
    }
}
```

### 预计工时：10 分钟

---

## Phase 2：爬虫抓正文（中难度）

### 问题

当前 HN 爬虫 `content=title`，因为 HN 首页只有标题没有正文。GitHub Trending 有 description。

### 方案

**2a. HN 爬虫升级**：从 HN 首页拿到外部链接后，再用 requests 请求那个链接，用 `html2text` 或 `trafilatura` 提取正文首段。

```python
import trafilatura

def extract_article_content(url):
    """从文章链接提取正文前500字"""
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text[:500] if text else ""
    except:
        return ""
```

**2b. GitHub 爬虫**：多抓一个 description 字段（当前已有），如果能有 README 首段更好。

**2c. 依赖**：`pip install trafilatura`（纯 Python，无系统依赖）

### 预计工时：30 分钟

---

## Phase 3：详情页展示完整内容（低难度）

### 改动文件

| 文件 | 改动 |
|------|------|
| `Detail.vue` | 显示 content + content_cn 双语对比，末尾加"查看原文"按钮 |
| `Global.vue` | 卡片显示 summary_cn 在标题下方（当前已有，但可能不完整，加 line-clamp 控制） |

### 显示逻辑

```html
<!-- Detail.vue 内容区 -->
<div class="content-section" v-if="item.content">
  <h3>内容</h3>
  <div class="bilingual">
    <div class="original">
      <p>{{ item.content }}</p>
    </div>
    <div class="translated" v-if="item.contentCn && item.contentCn !== item.content">
      <p>{{ item.contentCn }}</p>
    </div>
  </div>
</div>
<div class="source-link" v-if="item.original_url">
  <a :href="item.original_url" target="_blank" rel="noopener">查看原文 →</a>
</div>
```

### 预计工时：15 分钟

---

## 总工时：约 55 分钟

## 多智能体分配

| Agent | 负责 | 文件 | 预计 |
|:-----:|------|------|:----:|
| **A** 🔙 | 后端去重 | GlobalService.java, ContentService.java | 10min |
| **B** 🕷️ | 爬虫抓正文 | quick_scrape.py / run_continuous.py + trafilatura | 30min |
| **C** 🖥️ | 详情页展示 | Detail.vue, Global.vue | 15min |

## 验证方式

1. 后端去重：爬虫跑两次，检查数据库无重复 `original_url`
2. 正文抓取：爬虫跑一次，检查 `content` 字段有实际文章内容而非标题
3. 详情页：浏览器点卡片进 Detail，看到完整内容 + 原文链接
