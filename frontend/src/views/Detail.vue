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
              v-if="item.sourceInfo"
              :href="item.sourceInfo"
              target="_blank"
              class="article-source"
            >
              来源
            </a>
          </div>
          <h1 class="article-title">{{ item.title }}</h1>
        </header>

        <div class="article-body">
          <div v-if="item.category === 'opportunity'" class="bilingual">
            <div class="bilingual-section">
              <h3 class="section-label">原始内容</h3>
              <p class="section-text">{{ item.originalContent || item.content }}</p>
            </div>
            <div class="bilingual-section translated">
              <h3 class="section-label">中文翻译</h3>
              <p class="section-text">{{ item.content }}</p>
            </div>
          </div>
          <div v-else class="content-text">
            {{ item.content }}
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

const isDeal = route.path.includes('deals')

async function fetchDetail() {
  loading.value = true
  error.value = false
  try {
    const id = route.params.id
    item.value = isDeal
      ? await dealApi.get(id)
      : await globalApi.get(id)
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

@media (max-width: 560px) {
  .article-header { padding: 24px 20px 0; }
  .article-body { padding: 0 20px 24px; }
  .article-title { font-size: 1.35rem; }
}
</style>
