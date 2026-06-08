<template>
  <div class="feed-page">
    <!-- Page Head -->
    <div class="page-head">
      <div class="head-icon">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect x="3" y="3" width="22" height="22" rx="6" stroke="currentColor" stroke-width="1.5"/>
          <path d="M14 8v12M8 14h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">发现广场</h1>
        <p class="page-desc">看看大家都在分享什么</p>
      </div>
    </div>

    <!-- Action bar -->
    <div class="action-bar">
      <input
        v-model="content"
        class="post-input"
        placeholder="分享你今天发现的信息差…"
        @focus="showCreate = true"
      />
      <button v-if="showCreate" class="btn-publish" :disabled="!content.trim()" @click="handlePublish">
        发布
      </button>
    </div>

    <!-- Create panel -->
    <transition name="slide">
      <div v-if="showCreate" class="create-panel">
        <textarea
          v-model="content"
          class="content-area"
          placeholder="写点什么…"
          rows="4"
        ></textarea>
        <div class="create-actions">
          <label class="upload-btn">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="2" y="2" width="14" height="14" rx="3" stroke="currentColor" stroke-width="1.3"/>
              <circle cx="7" cy="7" r="1.5" stroke="currentColor" stroke-width="1.3"/>
              <path d="M2 12l4-4 3 3 3-2 4 4" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
            </svg>
            <span>图片</span>
            <input type="file" accept="image/*" multiple hidden @change="handleImages" />
          </label>
          <label class="upload-btn">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 4v10M4 9h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <span>链接</span>
            <input v-model="link" class="link-input" placeholder="https://…" />
          </label>
          <div class="create-right">
            <button class="btn-cancel" @click="cancelCreate">取消</button>
            <button class="btn-publish" :disabled="!content.trim()" @click="handlePublish">发布</button>
          </div>
        </div>
        <!-- Image previews -->
        <div v-if="imagePreviews.length" class="image-previews">
          <div v-for="(img, i) in imagePreviews" :key="i" class="preview-item">
            <img :src="img" />
            <button class="preview-remove" @click="removeImage(i)">&times;</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Waterfall grid -->
    <div class="waterfall" ref="waterfallRef">
      <div
        v-for="post in posts"
        :key="post.id"
        class="waterfall-card"
        @click="viewPost(post)"
      >
        <!-- Images -->
        <div v-if="post.images" class="card-media">
          <img
            v-for="(img, i) in parseImages(post.images)"
            :key="i"
            :src="img"
            class="card-img"
            :class="{ single: parseImages(post.images).length === 1 }"
          />
        </div>
        <!-- Content -->
        <div class="card-body">
          <p class="card-text">{{ post.content }}</p>
          <div class="card-meta">
            <span class="card-user">{{ post.userId ? '用户' : '匿名' }}</span>
            <span class="card-time">{{ formatTime(post.createdAt) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && posts.length === 0" class="empty-state">
      <p>还没有人发帖，来做第一个分享的人吧</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <span class="loader"></span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { postApi } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const posts = ref([])
const loading = ref(false)
const showCreate = ref(false)
const content = ref('')
const link = ref('')
const imageFiles = ref([])
const imagePreviews = ref([])
const page = ref(1)
const hasMore = ref(true)

async function fetchPosts() {
  if (loading.value) return
  loading.value = true
  try {
    const res = await postApi.list(page.value, 20)
    const list = res.data || []
    posts.value = [...posts.value, ...list]
    hasMore.value = list.length === 20
    page.value++
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

function handleImages(e) {
  const files = Array.from(e.target.files)
  imageFiles.value = [...imageFiles.value, ...files]
  files.forEach((f) => {
    const url = URL.createObjectURL(f)
    imagePreviews.value.push(url)
  })
}

function removeImage(i) {
  URL.revokeObjectURL(imagePreviews.value[i])
  imagePreviews.value.splice(i, 1)
  imageFiles.value.splice(i, 1)
}

function parseImages(images) {
  if (!images) return []
  try {
    const parsed = typeof images === 'string' ? JSON.parse(images) : images
    return Array.isArray(parsed) ? parsed : [String(images)]
  } catch {
    return [images]
  }
}

async function handlePublish() {
  if (!content.value.trim()) return
  const data = { content: content.value.trim() }
  if (link.value) data.link = link.value
  try {
    await postApi.create(data)
    ElMessage.success('发布成功，等待审核')
    content.value = ''
    link.value = ''
    imageFiles.value = []
    imagePreviews.value = []
    posts.value = []
    page.value = 1
    showCreate.value = false
    fetchPosts()
  } catch {
    ElMessage.error('发布失败')
  }
}

function cancelCreate() {
  showCreate.value = false
  content.value = ''
  link.value = ''
}

function viewPost(post) {
  // For now, expand detail inline or navigate
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.feed-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px 80px;
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
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--accent-light);
  color: var(--accent);
  flex-shrink: 0;
}

.page-title {
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.page-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ── Action bar ─────────────────────────── */
.action-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.post-input {
  flex: 1;
  padding: 12px 16px;
  border: 1.5px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.9rem;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s var(--ease-out);
}
.post-input:focus {
  border-color: var(--accent);
}

.btn-publish {
  padding: 0 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s var(--ease-out);
  white-space: nowrap;
}
.btn-publish:hover { background: var(--accent-hover); }
.btn-publish:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Create panel ───────────────────────── */
.create-panel {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.content-area {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s var(--ease-out);
}
.content-area:focus { border-color: var(--accent); }

.create-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s var(--ease-out);
}
.upload-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.link-input {
  width: 180px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.8rem;
  outline: none;
}

.create-right {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.btn-cancel {
  padding: 7px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s var(--ease-out);
}
.btn-cancel:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

/* ── Image previews ─────────────────────── */
.image-previews {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.preview-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
}

.preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Waterfall grid ─────────────────────── */
.waterfall {
  column-count: 2;
  column-gap: 16px;
  margin-top: 12px;
}

.waterfall-card {
  break-inside: avoid;
  margin-bottom: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}
.waterfall-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-media {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-img {
  width: 100%;
  object-fit: cover;
  display: block;
}
.card-img.single {
  max-height: 360px;
}

.card-body {
  padding: 14px;
}

.card-text {
  font-size: 0.9rem;
  line-height: 1.55;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.card-user {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent);
}

.card-time {
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* ── States ─────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.loader {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Transitions ─────────────────────────── */
.slide-enter-active, .slide-leave-active {
  transition: all 0.2s var(--ease-out);
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── Responsive ─────────────────────────── */
@media (max-width: 640px) {
  .waterfall { column-count: 1; }
}
</style>
