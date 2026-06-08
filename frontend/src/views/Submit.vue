<template>
  <div class="submit-page">
    <div class="hero-section">
      <div class="hero-shapes">
        <div class="shape s1"></div>
        <div class="shape s2"></div>
        <div class="shape s3"></div>
      </div>
      <div class="hero-content">
        <div class="hero-icon">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <path d="M20 6v28M6 20h28" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="20" cy="20" r="4" fill="currentColor"/>
          </svg>
        </div>
        <h1 class="hero-title">分享好信息</h1>
        <p class="hero-desc">发现那些你不知道但很有用的信息、机会、工具 — 让更多人看见</p>
      </div>
    </div>

    <div class="form-wrap">
      <div class="form-card">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="onSubmit"
        >
          <el-form-item label="标题" prop="title">
            <el-input
              v-model="form.title"
              placeholder="简要概括你要分享的信息"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="内容描述" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="6"
              placeholder="详细描述你要分享的信息，越具体越好"
              maxlength="2000"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="分类" prop="category">
            <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
              <el-option label="实用技巧 (deal)" value="deal" />
              <el-option label="全球信息 (opportunity)" value="opportunity" />
              <el-option label="工具推荐 (tool)" value="tool" />
              <el-option label="一般信息 (info)" value="info" />
            </el-select>
          </el-form-item>

          <el-form-item label="来源（可选）" prop="sourceInfo">
            <el-input
              v-model="form.sourceInfo"
              placeholder="来源链接或说明"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
              :disabled="loading"
              class="submit-btn"
            >
              {{ loading ? '提交中...' : '提交爆料' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { submitApi } from '@/api'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  title: '',
  description: '',
  category: '',
  sourceInfo: '',
})

const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { max: 200, message: '标题不能超过 200 个字符', trigger: 'blur' },
  ],
  description: [
    { required: true, message: '请输入内容描述', trigger: 'blur' },
    { max: 2000, message: '描述不能超过 2000 个字符', trigger: 'blur' },
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' },
  ],
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await submitApi.create(form)
    ElMessage.success('提交成功！')
    form.title = ''
    form.description = ''
    form.category = ''
    form.sourceInfo = ''
    formRef.value.resetFields()
    router.push('/')
  } catch (err) {
    ElMessage.error(err?.message || err?.error || '提交失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.submit-page {
  min-height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ── Hero ─────────────────────────────────── */
.hero-section {
  position: relative;
  width: 100%;
  padding: 64px 24px;
  text-align: center;
  overflow: hidden;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.hero-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}

.s1 {
  width: 400px; height: 400px;
  background: var(--accent, #f97316);
  top: -100px; right: -80px;
}

.s2 {
  width: 250px; height: 250px;
  background: #fff;
  bottom: -60px; left: -60px;
}

.s3 {
  width: 180px; height: 180px;
  background: var(--accent, #f97316);
  bottom: 20%; right: 15%;
}

.hero-content {
  position: relative;
  color: #fff;
}

.hero-icon {
  display: inline-flex;
  margin-bottom: 16px;
  opacity: 0.7;
}

.hero-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 10px;
}

.hero-desc {
  font-size: 1rem;
  opacity: 0.75;
  line-height: 1.6;
  max-width: 480px;
  margin: 0 auto;
}

/* ── Form ─────────────────────────────────── */
.form-wrap {
  width: 100%;
  max-width: 560px;
  margin: -40px auto 0;
  padding: 0 24px 64px;
  position: relative;
}

.form-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 32px;
  box-shadow: var(--shadow-lg);
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
}

@media (max-width: 560px) {
  .hero-section { padding: 48px 20px; }
  .form-wrap { margin-top: -30px; padding: 0 16px 48px; }
  .form-card { padding: 24px; }
}
</style>
