<template>
  <div class="detail-page">
    <div class="detail-container">
      <!-- Back -->
      <div class="back-bar">
        <button class="back-btn" @click="router.back()">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M11 4L6 9l5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          返回
        </button>
      </div>

      <!-- Loading / Error -->
      <div v-if="loading" class="loading-state">
        <div class="skeleton-block" style="height:32px; width:60%; margin-bottom:16px;"></div>
        <div class="skeleton-block" style="height:16px; width:40%; margin-bottom:24px;"></div>
        <div class="skeleton-block" style="height:200px;"></div>
      </div>

      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 3"/>
            <path d="M24 16v8M24 28v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="error-text">未找到该内容</p>
        <button class="back-btn" @click="router.back()">返回</button>
      </div>

      <!-- Content -->
      <article v-else-if="item" class="detail-article">
        <header class="article-header">
          <div class="article-meta">
            <span :class="['article-cat', categoryType(item.category)]">
              {{ categoryLabel(item.category) }}
            </span>
            <span v-if="item.score != null" class="article-score">
              {{ item.score }}
            </span>
            <a
              v-if="item.original_url"
              :href="item.original_url"
              target="_blank"
              class="article-source"
            >
              原文
            </a>
          </div>
          <h1 class="article-title">{{ item.title_cn || item.title || '' }}</h1>
          <!-- 摘要行 -->
          <p class="article-summary" v-if="item.summary_cn || item.summary">
            {{ item.summary_cn || item.summary }}
          </p>
        </header>

        <div class="article-body">
          <!-- 全球内容：双语对照 -->
          <template v-if="isGlobal && item.content">
            <div class="bilingual-section">
              <h3 class="section-label">原文</h3>
              <div class="section-text">{{ item.content }}</div>
            </div>
            <div v-if="item.content_cn && item.content_cn !== item.content" class="bilingual-section translated">
              <h3 class="section-label">中文翻译</h3>
              <div class="section-text">{{ item.content_cn }}</div>
            </div>
          </template>
          <!-- 非全球内容 -->
          <div v-else-if="item.content" class="content-text">
            {{ item.content }}
          </div>
          <!-- 无内容时 -->
          <div v-else class="empty-content">
            <p>暂无详情内容</p>
            <a
              v-if="item.original_url"
              :href="item.original_url"
              target="_blank"
              rel="noopener"
              class="content-link"
            >查看原文</a>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { dealApi, globalApi } from '@/api'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const loading = ref(true)
const error = ref(false)

const isDeal = route.path.includes('/deals/')
const isGlobal = route.path.includes('/global/')

async function fetchDetail() {
  loading.value = true
  error.value = false
  try {
    const id = route.params.id
    if (isDeal) {
      item.value = await dealApi.get(id)
    } else {
      item.value = await globalApi.get(id)
    }
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

function categoryType(cat) {
  const map = { deal: 'cat-deal', opportunity: 'cat-opp', tool: 'cat-tool', info: 'cat-info' }
  return map[cat] || ''
}

function categoryLabel(cat) {
  const map = { deal: '实用技巧', opportunity: '全球信息', tool: '工具推荐', info: '一般信息' }
  return map[cat] || cat
}

onMounted(fetchDetail)
</script>

<style scoped>
.detail-page {
  min-height: calc(100vh - 64px);
  padding: 32px 24px 64px;
}

.detail-container {
  max-width: 740px;
  margin: 0 auto;
}

/* ── Back ─────────────────────────────────── */
.back-bar {
  margin-bottom: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

.back-btn:hover {
  border-color: var(--border-color);
  color: var(--text-primary);
}

/* ── Loading ──────────────────────────────── */
.loading-state {
  padding: 40px 0;
}

.skeleton-block {
  background: var(--bg-tertiary);
  border-radius: 8px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Error ────────────────────────────────── */
.error-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
}

.error-icon { margin-bottom: 12px; opacity: 0.4; }

.error-text {
  font-size: 15px;
  margin-bottom: 20px;
}

/* ── Article ──────────────────────────────── */
.detail-article {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  overflow: hidden;
}

.article-header {
  padding: 32px 32px 0;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.article-cat {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
}

.cat-deal { background: rgba(232, 93, 4, 0.1); color: var(--accent); }
.cat-opp { background: rgba(15, 157, 88, 0.1); color: var(--score-high); }
.cat-tool { background: rgba(244, 180, 0, 0.12); color: var(--score-mid); }
.cat-info { background: rgba(64, 128, 255, 0.1); color: #4080ff; }

.article-score {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(244, 180, 0, 0.12);
  color: var(--score-mid);
}

.article-source {
  font-size: 13px;
  color: var(--text-muted);
  text-decoration: none;
  margin-left: auto;
  transition: color 0.2s var(--ease-out);
}

.article-source:hover {
  color: var(--accent);
}

.article-title {
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1.35;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.article-summary {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 24px;
}

/* ── Body ─────────────────────────────────── */
.article-body {
  padding: 0 32px 32px;
}

.bilingual-section {
  padding: 20px;
  border-radius: 10px;
  background: var(--bg-tertiary);
  margin-bottom: 16px;
}

.bilingual-section.translated {
  background: var(--accent-soft);
}

.section-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 10px;
}

.section-text {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 0.95rem;
  color: var(--text-primary);
  padding: 8px 0;
}

.content-link {
  display: inline-block;
  margin-top: 12px;
  padding: 8px 20px;
  border-radius: 8px;
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.2s var(--ease-out);
}

.content-link:hover {
  opacity: 0.85;
}

.empty-content {
  text-align: center;
  padding: 48px 16px;
}

.empty-content p {
  color: var(--text-muted);
  font-size: 0.95rem;
  margin-bottom: 16px;
}

@media (max-width: 560px) {
  .article-header { padding: 24px 20px 0; }
  .article-body { padding: 0 20px 24px; }
  .article-title { font-size: 1.35rem; }
}
</style>
