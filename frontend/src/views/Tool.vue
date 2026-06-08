<template>
  <div class="tool-page">
    <div class="page-head">
      <div class="head-icon">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <path d="M26 16a10 10 0 11-20 0 10 10 0 0120 0z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M12 14l-2 2 2 2M20 14l2 2-2 2M17 12l-2 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">好用工具站</h1>
        <p class="page-desc">精选实用工具，提升效率</p>
      </div>
    </div>

    <div class="toolbar">
      <el-select v-model="tag" placeholder="全部分类" clearable @change="fetchList" class="tag-select">
        <el-option v-for="t in tags" :key="t" :label="t" :value="t" />
      </el-select>
    </div>

    <div v-loading="loading" class="card-grid">
      <div v-for="item in list" :key="item.id" class="tool-card" @click="openUrl(item.url)">
        <div class="card-icon-wrap">
          <div class="card-icon">
            <span class="icon-letter">{{ (item.name || '?')[0] }}</span>
          </div>
        </div>
        <div class="card-body">
          <h3 class="card-name">{{ item.name }}</h3>
          <p class="card-summary">{{ item.summary }}</p>
          <p class="card-desc">{{ item.description }}</p>
          <div class="card-tags">
            <span v-for="t in parseTags(item.tags)" :key="t" class="tag">{{ t }}</span>
          </div>
        </div>
        <div class="card-arrow">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>

      <div v-if="!loading && list.length === 0" class="empty-state">
        <p>暂无工具</p>
      </div>
    </div>

    <div class="pagination-wrap">
      <el-pagination
        v-if="total > 0"
        layout="prev, pager, next, total"
        :total="total"
        :page-size="size"
        v-model:current-page="page"
        @current-change="fetchList"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { toolApi } from '@/api'

const list = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const size = ref(12)
const tag = ref('')
const tags = ref([])

function parseTags(str) {
  if (!str) return []
  if (Array.isArray(str)) return str
  return str.split(/[,\s|]+/).filter(Boolean)
}

function openUrl(url) {
  if (url) window.open(url, '_blank', 'noopener')
}

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (tag.value) params.tag = tag.value
    const res = await toolApi.list(params.page, params.size, params.tag)
    list.value = res.data || res || []
    total.value = res.total ?? list.value.length
    const allTags = new Set()
    list.value.forEach((item) => parseTags(item.tags).forEach((t) => allTags.add(t)))
    tags.value = [...allTags]
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.tool-page {
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
  background: rgba(244, 180, 0, 0.12);
  color: var(--score-mid);
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

.toolbar {
  margin-bottom: 24px;
}

.tag-select { width: 200px; }

/* ── Grid ─────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

@media (max-width: 700px) {
  .card-grid { grid-template-columns: 1fr; }
}

.tool-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
}

.tool-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-icon-wrap {
  flex-shrink: 0;
}

.card-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--accent-soft);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-letter {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.card-summary {
  font-size: 0.85rem;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.card-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-muted);
}

.card-arrow {
  flex-shrink: 0;
  color: var(--text-muted);
  margin-top: 12px;
  transition: transform 0.2s var(--ease-out);
}

.tool-card:hover .card-arrow {
  transform: translateX(3px);
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
