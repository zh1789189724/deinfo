<template>
  <div class="opportunity-page">
    <div class="page-head">
      <div class="head-icon">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <path d="M16 4a12 12 0 100 24 12 12 0 000-24z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M16 10v6l4 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">投资机会</h1>
        <p class="page-desc">发现身边的投资、租房、兼职和政策机会</p>
      </div>
    </div>

    <div v-loading="loading" class="card-grid">
      <el-card
        v-for="item in list"
        :key="item.id"
        :class="['card', { expanded: expandedItem?.id === item.id }]"
        shadow="never"
        @click="selectItem(item)"
      >
        <div class="card-head">
          <span class="card-title">{{ item.title }}</span>
          <span :class="['card-cat', `cat-${categories.indexOf(item.category) % 4}`]">
            {{ item.category }}
          </span>
        </div>

        <p class="card-desc">{{ item.description }}</p>

        <div class="card-foot">
          <span :class="['status-tag', `status-${item.status}`]">
            {{ item.status }}
          </span>
          <span class="card-date" v-if="item.createdAt">{{ formatDate(item.createdAt) }}</span>
        </div>

        <!-- Inline expand -->
        <transition name="expand">
          <div v-if="expandedItem?.id === item.id" class="card-detail">
            <div class="detail-divider"></div>
            <p><strong>详细描述：</strong>{{ item.description }}</p>
            <p><strong>创建时间：</strong>{{ formatDate(item.createdAt) }}</p>
          </div>
        </transition>
      </el-card>

      <div v-if="!loading && list.length === 0" class="empty-state">
        <p>暂无机会</p>
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
import { opportunityApi } from '@/api'

const list = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const size = ref(12)
const expandedItem = ref(null)

const categories = ['投资', '租房', '兼职', '政策']

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function fetchList() {
  loading.value = true
  try {
    const res = await opportunityApi.list(page.value, size.value)
    list.value = res.data || res || []
    total.value = res.total ?? list.value.length
  } catch (e) {
    console.error('[Opportunity] Failed to load:', e)
    list.value = []
  } finally {
    loading.value = false
  }
}

function selectItem(item) {
  expandedItem.value = expandedItem.value?.id === item.id ? null : item
}

onMounted(fetchList)
</script>

<style scoped>
.opportunity-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 24px;
}

.page-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 36px;
}

.head-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--accent-light);
  color: var(--accent);
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

/* ── Grid ─────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 700px) {
  .card-grid { grid-template-columns: 1fr; }
}

.card {
  border: 1px solid var(--border-light) !important;
  border-radius: 12px !important;
  cursor: pointer;
  transition: all 0.25s var(--ease-out) !important;
}

.card:hover {
  border-color: var(--border-color) !important;
  transform: translateY(-2px);
}

.card.expanded {
  border-color: var(--accent) !important;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
  flex: 1;
}

.card-cat {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.cat-0 { background: color-mix(in srgb, #4080ff 10%, transparent); color: #4080ff; }
.cat-1 { background: color-mix(in srgb, var(--score-high) 10%, transparent); color: var(--score-high); }
.cat-2 { background: color-mix(in srgb, var(--score-mid) 12%, transparent); color: var(--score-mid); }
.cat-3 { background: color-mix(in srgb, var(--accent) 10%, transparent); color: var(--accent); }

.card-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.55;
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

.status-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
}

.status-进行中 { background: rgba(15, 157, 88, 0.1); color: var(--score-high); }
.status-已结束 { background: rgba(153, 153, 153, 0.1); color: var(--text-muted); }
.status-待审核 { background: rgba(244, 180, 0, 0.12); color: var(--score-mid); }

.card-date {
  font-size: 12px;
  color: var(--text-muted);
}

/* ── Expand detail ────────────────────────── */
.card-detail {
  overflow: hidden;
}

.detail-divider {
  height: 1px;
  background: var(--border-light);
  margin: 14px 0;
}

.card-detail p {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 6px;
}

.card-detail strong {
  color: var(--text-primary);
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s var(--ease-out);
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 300px;
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
