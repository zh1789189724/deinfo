<template>
  <div class="deal-page">
    <div class="page-head">
      <div class="head-icon">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <path d="M6 16h4l3-8 4 16 3-8h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">成都优惠羊毛</h1>
        <p class="page-desc">优惠券、折扣、政府补贴 — 在成都，会花不如会省</p>
      </div>
    </div>

    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="搜索优惠..."
        clearable
        prefix-icon="Search"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
        class="search-input"
      />
      <div class="filter-group">
        <button
          v-for="cat in categories"
          :key="cat.key"
          :class="['filter-btn', { active: category === cat.key }]"
          @click="handleFilter(cat.key)"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <div class="feed" v-loading="loading">
      <template v-if="!loading && deals.length === 0">
        <div class="empty-state">
          <p>暂无优惠信息</p>
        </div>
      </template>
      <template v-else>
        <div v-for="deal in deals" :key="deal.id" class="feed-card" @click="goTo(deal)">
          <div class="card-top">
            <span v-if="deal.category" class="cat-badge">{{ deal.category }}</span>
            <span :class="['score-badge', scoreClass(deal.score)]" v-if="deal.score != null">
              {{ deal.score }}
            </span>
          </div>

          <h3 class="card-title">{{ deal.title }}</h3>
          <p class="card-summary">{{ deal.summary || '暂无摘要' }}</p>

          <div class="card-foot">
            <span v-if="deal.location" class="card-location">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1a4.5 4.5 0 00-4.5 4.5C2.5 8.5 7 13 7 13s4.5-4.5 4.5-7.5A4.5 4.5 0 007 1z" stroke="currentColor" stroke-width="1.2"/>
                <circle cx="7" cy="5.5" r="1.5" stroke="currentColor" stroke-width="1.2"/>
              </svg>
              {{ deal.location }}
            </span>
            <span v-if="deal.price" class="card-price">{{ deal.price }}</span>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dealApi } from '@/api'

const router = useRouter()
const keyword = ref('')
const category = ref('')
const loading = ref(false)
const deals = ref([])
const page = ref(1)
const total = ref(0)
const pageSize = ref(20)

const categories = [
  { key: '', label: '全部' },
  { key: '优惠券', label: '优惠券' },
  { key: '折扣', label: '折扣' },
  { key: '政府补贴', label: '政府补贴' },
]

const scoreClass = (score) => {
  if (score == null) return ''
  if (score >= 80) return 's-high'
  if (score >= 60) return 's-mid'
  return 's-low'
}

const loadDeals = async () => {
  loading.value = true
  try {
    const res = await dealApi.list(page.value, pageSize.value)
    let list = res.data || res
    if (keyword.value) {
      const kw = keyword.value.toLowerCase()
      list = list.filter(
        (d) =>
          (d.title || '').toLowerCase().includes(kw) ||
          (d.summary || '').toLowerCase().includes(kw)
      )
    }
    if (category.value) {
      list = list.filter((d) => d.category === category.value)
    }
    list.sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    deals.value = list
    total.value = res.total ?? res.data?.total ?? list.length
  } catch (e) {
    console.error('[Deal] Failed to load:', e)
    deals.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handlePageChange = (p) => { page.value = p; loadDeals() }
const handleSearch = () => { page.value = 1; loadDeals() }
const handleFilter = (cat) => { category.value = cat; page.value = 1; loadDeals() }
const goTo = (deal) => { router.push(`/deals/${deal.id}`) }

onMounted(loadDeals)
</script>

<style scoped>
.deal-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 24px;
}

.page-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.head-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--score-high) 10%, transparent);
  color: var(--score-high);
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

/* ── Toolbar ──────────────────────────────── */
.toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input {
  max-width: 320px;
}

.filter-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 6px 16px;
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
  background: var(--score-high);
  border-color: var(--score-high);
  color: #fff;
}

/* ── Feed ─────────────────────────────────── */
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
  gap: 8px;
  margin-bottom: 10px;
}

.cat-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(15, 157, 88, 0.08);
  color: var(--score-high);
}

.score-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: auto;
}

.s-high { background: rgba(15, 157, 88, 0.1); color: var(--score-high); }
.s-mid { background: rgba(244, 180, 0, 0.12); color: var(--score-mid); }
.s-low { background: rgba(234, 67, 53, 0.1); color: var(--score-low); }

.card-title {
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.35;
  margin-bottom: 8px;
  color: var(--text-primary);
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

.card-location {
  font-size: 12px;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.card-price {
  font-size: 15px;
  font-weight: 700;
  color: var(--score-low);
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
