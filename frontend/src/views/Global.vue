<template>
  <div class="global-page">
    <div class="page-head">
      <div class="head-icon">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="12" stroke="currentColor" stroke-width="1.5"/>
          <ellipse cx="16" cy="16" rx="6" ry="12" stroke="currentColor" stroke-width="1.5"/>
          <path d="M4 16h24M16 4v24" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">海外精选</h1>
        <p class="page-desc">跨语言信息 — AI 翻译和摘要，帮你第一时间获取全球有价值的资讯</p>
      </div>
    </div>

    <div class="filter-bar">
      <button
        v-for="cat in categories"
        :key="cat.key"
        :class="['filter-btn', { active: category === cat.key }]"
        @click="category = cat.key"
      >
        {{ cat.label }}
      </button>
    </div>

    <div class="feed" v-loading="loading">
      <template v-if="!loading && items.length === 0">
        <div class="empty-state">
          <p>暂无海外精选</p>
        </div>
      </template>
      <template v-else>
        <div v-for="item in filteredItems" :key="item.id" class="feed-card" @click="goTo(item)">
          <div class="card-top">
            <span :class="['lang-badge', `lang-${(item.lang || 'en').toLowerCase()}`]">
              {{ item.lang || 'EN' }}
            </span>
            <span class="card-date" v-if="item.createdAt">{{ formatDate(item.createdAt) }}</span>
          </div>

          <div class="card-titles">
            <p class="original-title">{{ item.title || item.original_title }}</p>
            <p class="cn-title">{{ item.title_cn || '翻译加载中...' }}</p>
          </div>

          <p class="card-summary">{{ item.summary_cn || '暂无中文摘要' }}</p>

          <div class="card-foot">
            <span v-if="item.category" class="card-cat">{{ item.category }}</span>
            <a
              v-if="item.original_url"
              :href="item.original_url"
              target="_blank"
              rel="noopener"
              class="card-link"
              @click.stop
            >
              原文
            </a>
          </div>
        </div>
      </template>
    </div>

    <div class="pagination-wrap">
      <el-pagination
        v-if="total > pageSize"
        layout="prev, pager, next"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { globalApi } from '@/api'

const router = useRouter()
const category = ref('')
const loading = ref(false)
const items = ref([])
const page = ref(1)
const total = ref(0)
const pageSize = ref(20)

const categories = [
  { key: '', label: '全部' },
  { key: '技术', label: '技术' },
  { key: '产品', label: '产品' },
  { key: '设计', label: '设计' },
  { key: '商业', label: '商业' },
]

const filteredItems = computed(() => {
  if (!category.value) return items.value
  return items.value.filter((i) => i.category === category.value)
})

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { month: 'short', day: 'numeric' })
}

const loadItems = async () => {
  loading.value = true
  try {
    const res = await globalApi.list(page.value, pageSize.value)
    items.value = res.data || res || []
    total.value = res.total ?? items.value.length
  } catch (e) {
    console.error('[Global] Failed to load:', e)
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handlePageChange = (p) => { page.value = p; loadItems() }
const goTo = (item) => { router.push(`/global/${item.id}`) }

watch(category, () => { page.value = 1 })
onMounted(loadItems)
</script>

<style scoped>
.global-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 24px;
}

.page-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 32px;
}

.head-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: color-mix(in srgb, #347ff0 10%, transparent);
  color: #347ff0;
  flex-shrink: 0;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
}

.page-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ── Filter ───────────────────────────────── */
.filter-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 7px 18px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

.filter-btn:hover {
  border-color: var(--border-color);
  color: var(--text-primary);
}

.filter-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

/* ── Grid ─────────────────────────────────── */
.feed {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 700px) {
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
  transform: translateY(-2px);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.lang-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.lang-en { background: color-mix(in srgb, #4080ff 10%, transparent); color: #4080ff; }
.lang-ja { background: color-mix(in srgb, var(--score-mid) 12%, transparent); color: var(--score-mid); }
.lang-ko { background: color-mix(in srgb, var(--score-high) 10%, transparent); color: var(--score-high); }
.lang-de { background: color-mix(in srgb, var(--score-low) 10%, transparent); color: var(--score-low); }

.card-date {
  font-size: 12px;
  color: var(--text-muted);
}

.card-titles {
  margin-bottom: 10px;
}

.original-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cn-title {
  font-size: 0.9rem;
  color: var(--accent);
  font-weight: 500;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-summary {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-cat {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--accent-soft);
  color: var(--accent);
}

.card-link {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.2s var(--ease-out);
}

.card-link:hover {
  color: var(--accent);
}

/* ── Empty ────────────────────────────────── */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 64px 0;
  color: var(--text-muted);
  font-size: 15px;
}

/* ── Pagination ───────────────────────────── */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 36px;
}
</style>
