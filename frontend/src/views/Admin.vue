<template>
  <div v-if="!isAdmin" class="no-access">
    <div class="no-access-inner">
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect x="6" y="6" width="36" height="36" rx="8" stroke="currentColor" stroke-width="1.5"/>
        <path d="M24 20v6M24 30v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <p>仅管理员可访问</p>
    </div>
  </div>
  <div v-else class="admin-page">
    <div class="page-head">
      <div class="head-icon">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <path d="M14 4a4 4 0 100 8 4 4 0 000-8zM6 22c0-4 3.6-8 8-8s8 4 8 8" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </div>
      <h1 class="page-title">管理后台</h1>
    </div>

    <div class="stats-row" v-if="activeTab === 'stats'">
      <div class="stat-card">
        <span class="stat-val">{{ stats.pending }}</span>
        <span class="stat-label">待审核</span>
      </div>
      <div class="stat-card">
        <span class="stat-val">{{ stats.total }}</span>
        <span class="stat-label">总提交</span>
      </div>
      <div class="stat-card">
        <span class="stat-val">{{ stats.today }}</span>
        <span class="stat-label">今日新增</span>
      </div>
    </div>

    <div class="tab-bar">
      <button :class="['tab-btn', { active: activeTab === 'pending' }]" @click="activeTab = 'pending'">
        待审核
      </button>
      <button :class="['tab-btn', { active: activeTab === 'stats' }]" @click="activeTab = 'stats'">
        统计
      </button>
    </div>

    <div v-if="activeTab === 'pending'" v-loading="loading" class="table-wrap">
      <el-empty v-if="!loading && list.length === 0" description="暂无待审核内容" />
      <el-table v-else :data="list" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="90" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <span :class="['status-tag', row.status === 'approved' ? 'approved' : 'pending']">
              {{ row.status }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <button class="action-btn approve" @click="handleApprove(row.id)">通过</button>
            <button class="action-btn reject" @click="openReject(row)">拒绝</button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Reject dialog -->
    <el-dialog v-model="rejectVisible" title="拒绝理由" width="380px" :close-on-click-modal="false">
      <el-input
        v-model="rejectReason"
        type="textarea"
        :rows="4"
        placeholder="请输入拒绝理由"
      />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" @click="submitReject" :loading="rejecting">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { adminApi } from '@/api'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin())

const activeTab = ref('pending')
const loading = ref(false)
const list = ref([])
const stats = ref({ pending: 0, total: 0, today: 0 })
const rejectVisible = ref(false)
const rejectReason = ref('')
const rejecting = ref(false)
const rejectTargetId = ref(null)

async function fetchPending() {
  loading.value = true
  try {
    const res = await adminApi.pending()
    list.value = Array.isArray(res) ? res : res.data?.list || res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await adminApi.stats()
    stats.value = res || stats.value
  } catch (e) {
    console.error('[Admin] Failed to load stats:', e)
  }
}

async function handleApprove(id) {
  try {
    await adminApi.approve(id)
    ElMessage.success('审核通过')
    fetchPending()
  } catch {
    ElMessage.error('操作失败')
  }
}

function openReject(row) {
  rejectTargetId.value = row.id
  rejectReason.value = ''
  rejectVisible.value = true
}

async function submitReject() {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入拒绝理由')
    return
  }
  rejecting.value = true
  try {
    await adminApi.reject(rejectTargetId.value, rejectReason.value)
    ElMessage.success('已拒绝')
    rejectVisible.value = false
    fetchPending()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    rejecting.value = false
  }
}

onMounted(() => {
  fetchPending()
  fetchStats()
})
</script>

<style scoped>
.admin-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 48px 24px;
}

.no-access {
  display: flex;
  justify-content: center;
  padding: 120px 0;
}

.no-access-inner {
  text-align: center;
  color: var(--text-muted);
}

.no-access-inner svg { margin-bottom: 12px; opacity: 0.3; }

.no-access-inner p { font-size: 15px; }

.page-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}

.head-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--accent-light);
  color: var(--accent);
  flex-shrink: 0;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
}

/* ── Stats ────────────────────────────────── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-val {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

/* ── Tabs ─────────────────────────────────── */
.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: var(--bg-tertiary);
  padding: 4px;
  border-radius: 10px;
  width: fit-content;
}

.tab-btn {
  padding: 7px 18px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

.tab-btn.active {
  background: var(--bg-secondary);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.tab-btn:hover:not(.active) { color: var(--text-primary); }

/* ── Table ────────────────────────────────── */
.table-wrap {
  min-height: 300px;
}

.status-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-tag.approved { background: rgba(15, 157, 88, 0.1); color: var(--score-high); }
.status-tag.pending { background: rgba(244, 180, 0, 0.12); color: var(--score-mid); }

.action-btn {
  padding: 5px 14px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin-right: 6px;
  transition: all 0.15s var(--ease-out);
}

.action-btn.approve {
  background: rgba(15, 157, 88, 0.1);
  color: var(--score-high);
}

.action-btn.approve:hover {
  background: var(--score-high);
  color: #fff;
}

.action-btn.reject {
  background: rgba(234, 67, 53, 0.1);
  color: var(--score-low);
}

.action-btn.reject:hover {
  background: var(--score-low);
  color: #fff;
}
</style>
