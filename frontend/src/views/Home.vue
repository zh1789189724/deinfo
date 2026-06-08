<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-badge">信息差发现平台</div>
        <h1 class="hero-title">发现你不知道<br/>但很有用的信息</h1>
        <p class="hero-desc">跨语言、跨平台的信息聚合，AI 翻译与摘要，帮你打破信息壁垒</p>
        <div class="hero-stats">
          <div class="hero-stat" v-for="s in stats" :key="s.label">
            <span class="hero-stat-val">{{ s.val }}</span>
            <span class="hero-stat-label">{{ s.label }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tabs + Grid -->
    <div class="page-section">
      <div class="section-header">
        <nav class="tab-nav">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab-btn', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Featured item (first item) -->
      <template v-if="!loading && items.length > 0">
        <div class="featured-card" @click="goTo(items[0])">
          <div class="featured-body">
            <div class="featured-meta">
              <span :class="['featured-cat', `cat-${activeTab}`]">
                {{ catLabel(items[0].category, activeTab) }}
              </span>
              <span class="featured-score" v-if="items[0].score != null">
                {{ items[0].score }}
              </span>
            </div>
            <h2 class="featured-title">{{ items[0].title }}</h2>
            <p class="featured-summary">{{ items[0].summary || items[0].summary_cn || '暂无摘要' }}</p>
            <div class="featured-action">
              <span class="read-more">阅读全文</span>
            </div>
          </div>
        </div>
      </template>

      <!-- Grid -->
      <div class="feed" v-loading="loading">
        <template v-if="!loading && items.length === 0">
          <div class="empty-state">
            <div class="empty-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <rect x="6" y="6" width="36" height="36" rx="8" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 3"/>
                <path d="M24 14v20M14 24h20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              </svg>
            </div>
            <p class="empty-text">暂无内容</p>
          </div>
        </template>
        <template v-else>
          <div
            v-for="(item, idx) in feedItems"
            :key="item.id"
            :class="['feed-card', `card-${idx % 4}`]"
            @click="goTo(item)"
          >
            <div class="feed-card-meta">
              <span v-if="item.category" class="feed-cat-tag">{{ item.category }}</span>
              <span v-if="item.score != null" :class="['feed-score', scoreClass(item.score)]">
                {{ item.score }}
              </span>
            </div>
            <h3 class="feed-card-title">{{ item.title }}</h3>
            <p class="feed-card-summary">{{ item.summary || item.summary_cn || '暂无摘要' }}</p>
            <div class="feed-card-footer">
              <span class="feed-source" v-if="item.source_url || item.original_url">原文</span>
              <span class="feed-lang" v-if="item.lang">{{ item.lang }}</span>
            </div>
          </div>
        </template>
      </div>

      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination
          layout="prev, pager, next"
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { dealApi, globalApi } from '@/api'

const router = useRouter()
const activeTab = ref('all')
const loading = ref(false)
const items = ref([])
const page = ref(1)
const total = ref(0)
const pageSize = ref(20)

const tabs = [
  { key: 'all', label: '推荐' },
  { key: 'deal', label: '优惠' },
  { key: 'global', label: '海外精选' },
]

const stats = [
  { val: '100+', label: '每日更新' },
  { val: '3', label: '信息来源' },
  { val: 'AI', label: '智能摘要' },
]

const feedItems = computed(() => items.value.slice(1))

const catLabel = (category, tab) => category || (tab === 'deal' ? '优惠' : tab === 'global' ? '海外' : '推荐')

const scoreClass = (score) => {
  if (score == null) return ''
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-mid'
  return 'score-low'
}

const loadData = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'deal') {
      const res = await dealApi.list(page.value, pageSize.value)
      const list = res.data || res
      list.forEach((item) => (item._source = 'deals'))
      items.value = list
      total.value = res.total ?? list.length
    } else if (activeTab.value === 'global') {
      const res = await globalApi.list(page.value, pageSize.value)
      const list = res.data || res
      list.forEach((item) => (item._source = 'global'))
      items.value = list
      total.value = res.total ?? list.length
    } else {
      const [dealsRes, globalRes] = await Promise.all([
        dealApi.top(),
        globalApi.top(),
      ])
      const deals = ((dealsRes.data || dealsRes).slice?.(0, 10) || []).map((d) => ({ ...d, _source: 'deals' }))
      const globals = ((globalRes.data || globalRes).slice?.(0, 10) || []).map((g) => ({ ...g, _source: 'global' }))
      items.value = [...deals, ...globals]
      total.value = items.value.length
    }
  } catch (e) {
    console.error('[Home] Failed to load data:', e)
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handlePageChange = (p) => {
  page.value = p
  loadData()
}

const goTo = (item) => {
  const source = item._source || (activeTab.value === 'global' ? 'global' : 'deals')
  router.push(`/${source}/${item.id}`)
}

watch(activeTab, () => { page.value = 1; loadData() })
onMounted(loadData)
</script>

<style scoped>
/* ── Hero ─────────────────────────────────── */
.hero {
  position: relative;
  padding: 80px 24px 60px;
  text-align: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 50% 0%, color-mix(in srgb, var(--accent) 8%, transparent) 0%, transparent 70%),
    radial-gradient(ellipse 40% 40% at 80% 60%, color-mix(in srgb, var(--accent) 4%, transparent) 0%, transparent 60%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  max-width: 680px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-flex;
  padding: 4px 14px;
  border-radius: 999px;
  background: var(--accent-light);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  margin-bottom: 20px;
}

.hero-title {
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.02em;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.hero-desc {
  font-size: 1.05rem;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 520px;
  margin: 0 auto 32px;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.hero-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hero-stat-val {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent);
}

.hero-stat-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

/* ── Section ──────────────────────────────── */
.page-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 64px;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 28px;
}

.tab-nav {
  display: flex;
  gap: 4px;
  background: var(--bg-tertiary);
  padding: 4px;
  border-radius: 10px;
}

.tab-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

.tab-btn.active {
  background: var(--bg-secondary);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.tab-btn:hover:not(.active) {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--bg-secondary) 50%, transparent);
}

/* ── Featured Card ────────────────────────── */
.featured-card {
  border-radius: 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  padding: 32px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
  position: relative;
  overflow: hidden;
}

.featured-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 4%, transparent) 0%, transparent 50%);
  pointer-events: none;
}

.featured-card:hover {
  border-color: color-mix(in srgb, var(--accent) 20%, transparent);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.featured-body {
  position: relative;
}

.featured-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.featured-cat {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.cat-all { background: color-mix(in srgb, var(--accent) 10%, transparent); color: var(--accent); }
.cat-deal { background: color-mix(in srgb, var(--score-high) 10%, transparent); color: var(--score-high); }
.cat-global { background: color-mix(in srgb, #347ff0 10%, transparent); color: #347ff0; }

.featured-score {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
}

.featured-title {
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.35;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.featured-summary {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.read-more {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.read-more::after {
  content: '→';
  transition: transform 0.2s var(--ease-out);
}

.featured-card:hover .read-more::after {
  transform: translateX(4px);
}

/* ── Feed Grid ────────────────────────────── */
.feed {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 900px) {
  .feed { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .feed { grid-template-columns: 1fr; }
}

.feed-card {
  border-radius: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  padding: 24px;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
}

.feed-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}

.feed-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.feed-cat-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--accent-soft);
  color: var(--accent);
}

.feed-score {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.score-high { background: color-mix(in srgb, var(--score-high) 10%, transparent); color: var(--score-high); }
.score-mid { background: color-mix(in srgb, var(--score-mid) 12%, transparent); color: var(--score-mid); }
.score-low { background: color-mix(in srgb, var(--score-low) 10%, transparent); color: var(--score-low); }

.feed-card-title {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 8px;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.feed-card-summary {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.feed-card-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-muted);
}

.feed-source, .feed-lang {
  font-weight: 500;
}

/* ── Empty state ──────────────────────────── */
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 0;
  color: var(--text-muted);
}

.empty-icon { margin-bottom: 12px; opacity: 0.4; }

.empty-text { font-size: 15px; }

/* ── Pagination ───────────────────────────── */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 36px;
}
</style>
