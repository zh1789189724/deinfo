<template>
  <div class="app">
    <!-- Header -->
    <header :class="['app-header', { scrolled: isScrolled }]">
      <div class="header-inner">
        <router-link to="/" class="masthead">
          <span class="masthead-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect x="3" y="3" width="22" height="22" rx="6" stroke="currentColor" stroke-width="1.5"/>
              <path d="M14 8v12M8 14h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              <circle cx="14" cy="14" r="2" fill="currentColor"/>
            </svg>
          </span>
          <span class="masthead-text">
            <span class="masthead-title">DeInfo</span>
            <span class="masthead-sub">信息差发现</span>
          </span>
        </router-link>

        <nav class="nav">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            @click="closeMobileMenu"
          >
            {{ item.label }}
            <span class="nav-underline"></span>
          </router-link>
        </nav>

        <div class="header-actions">
          <template v-if="userStore.isLoggedIn()">
            <div class="avatar-wrapper" @mouseenter="showDropdown = true" @mouseleave="showDropdown = false" @focusin="showDropdown = true" @focusout="showDropdown = false">
              <div class="avatar" tabindex="0" role="button" aria-haspopup="true" :aria-expanded="showDropdown" :title="userStore.username">
                {{ userStore.username.charAt(0).toUpperCase() }}
              </div>
              <transition name="fade">
                <div v-if="showDropdown" class="dropdown-panel">
                  <div class="dropdown-user">{{ userStore.username }}</div>
                  <div v-if="userStore.isAdmin()" class="dropdown-item" @click="handleCommand('admin')">管理后台</div>
                  <div class="dropdown-divider"></div>
                  <div class="dropdown-item danger" @click="handleCommand('logout')">退出登录</div>
                </div>
              </transition>
            </div>
          </template>
          <button v-else class="btn-login" @click="showLogin = true">登录</button>
        </div>
      </div>
    </header>

    <!-- Main -->
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="footer-title">DeInfo</span>
          <p class="footer-desc">跨越语言、地域、信息圈层 — 发现你不知道的信息差</p>
        </div>
        <div class="footer-links">
          <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="footer-link">
            {{ item.label }}
          </router-link>
        </div>
        <div class="footer-copy">
          &copy; {{ new Date().getFullYear() }} 信息差发现平台
        </div>
      </div>
    </footer>

    <!-- Login Overlay -->
    <transition name="overlay">
      <div v-if="showLogin" class="login-overlay" @click.self="showLogin = false">
        <div class="login-card">
          <button class="login-close" @click="showLogin = false">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M4 4l10 10M14 4l-10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
          <div class="login-brand">
            <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
              <rect x="3" y="3" width="22" height="22" rx="6" stroke="currentColor" stroke-width="1.5"/>
              <path d="M14 8v12M8 14h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              <circle cx="14" cy="14" r="2" fill="currentColor"/>
            </svg>
          </div>
          <h2 class="login-title">欢迎回来</h2>
          <p class="login-sub">登录后即可爆料和管理内容</p>
          <form @submit.prevent="handleLogin" class="login-form">
            <label class="login-field">
              <span>用户名</span>
              <input v-model="loginForm.username" type="text" placeholder="请输入用户名" autocomplete="username" required />
            </label>
            <label class="login-field">
              <span>密码</span>
              <input v-model="loginForm.password" type="password" placeholder="请输入密码" autocomplete="current-password" required />
            </label>
            <button type="submit" class="btn-submit" :disabled="loading">
              <span v-if="loading" class="btn-loading"></span>
              {{ loading ? '登录中…' : '登录' }}
            </button>
          </form>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const isScrolled = ref(false)
const showLogin = ref(false)
const showDropdown = ref(false)
const loading = ref(false)
const loginForm = ref({ username: '', password: '' })

const navItems = [
  { path: '/', label: '首页' },
  { path: '/global', label: '海外精选' },
  { path: '/deals', label: '优惠' },
  { path: '/feed', label: '广场' },
  { path: '/opportunities', label: '投资机会' },
  { path: '/tools', label: '工具站' },
  { path: '/submit', label: '爆料' },
]

const onScroll = () => {
  const scrolled = window.scrollY > 8
  if (scrolled !== isScrolled.value) isScrolled.value = scrolled
}
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const closeMobileMenu = () => {}

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) return
  loading.value = true
  try {
    const res = await authApi.login(loginForm.value)
    userStore.login(res.token, res.role, res.username)
    showLogin.value = false
    ElMessage.success('登录成功')
  } catch {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

const handleCommand = (cmd) => {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/')
    ElMessage.success('已退出')
  } else if (cmd === 'admin') {
    router.push('/admin')
  }
}
</script>

<style>
/* ── Page transitions ─────────────────────── */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── Header ───────────────────────────────── */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.25s var(--ease-out);
}

.app-header.scrolled {
  background: color-mix(in srgb, var(--bg-secondary) 80%, transparent);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-light);
}
.app-header:not(.scrolled) {
  background: transparent;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 32px;
  height: 64px;
}

/* ── Masthead ─────────────────────────────── */
.masthead {
  text-decoration: none;
  color: var(--text-primary);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.masthead-icon {
  display: flex;
  align-items: center;
  color: var(--accent);
}

.masthead-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.masthead-title {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.masthead-sub {
  font-size: 0.625rem;
  font-weight: 500;
  letter-spacing: 0.2em;
  color: var(--text-muted);
  text-transform: uppercase;
}

/* ── Nav ──────────────────────────────────── */
.nav {
  flex: 1;
  display: flex;
  gap: 4px;
}

.nav-link {
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
  position: relative;
  transition: color 0.2s var(--ease-out), background 0.2s var(--ease-out);
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--accent-soft);
}

.nav-link.router-link-active {
  color: var(--accent);
  background: var(--accent-light);
}

/* ── Actions ──────────────────────────────── */
.header-actions { display: flex; align-items: center; }

.avatar-wrapper { position: relative; cursor: pointer; }

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  transition: box-shadow 0.2s var(--ease-out);
}
.avatar:hover {
  box-shadow: 0 0 0 3px var(--accent-light);
}

.dropdown-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 6px 0;
  min-width: 150px;
  box-shadow: var(--shadow-lg);
  z-index: 101;
}

.dropdown-user {
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.dropdown-divider {
  height: 1px;
  background: var(--border-light);
  margin: 4px 0;
}

.dropdown-item {
  padding: 8px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s var(--ease-out);
}
.dropdown-item:hover {
  background: var(--accent-soft);
  color: var(--text-primary);
}
.dropdown-item.danger {
  color: var(--score-low);
}
.dropdown-item.danger:hover {
  background: rgba(234, 67, 53, 0.08);
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.btn-login {
  padding: 7px 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}
.btn-login:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
}

/* ── Main ─────────────────────────────────── */
.app-main {
  flex: 1;
  min-height: calc(100vh - 64px);
}

/* ── Footer ───────────────────────────────── */
.app-footer {
  border-top: 1px solid var(--border-light);
  padding: 48px 24px 32px;
  margin-top: 80px;
}

.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  text-align: center;
}

.footer-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.footer-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.footer-links {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  justify-content: center;
}

.footer-link {
  font-size: 13px;
  color: var(--text-secondary);
  transition: color 0.2s var(--ease-out);
}
.footer-link:hover {
  color: var(--accent);
}

.footer-copy {
  font-size: 12px;
  color: var(--text-muted);
}

/* ── Login overlay ────────────────────────── */
.login-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--bg-primary) 60%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.login-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 40px 36px 36px;
  width: 370px;
  position: relative;
  box-shadow: var(--shadow-xl);
  text-align: center;
}

.login-close {
  position: absolute;
  top: 14px;
  right: 14px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  transition: all 0.15s var(--ease-out);
}
.login-close:hover {
  background: var(--accent-soft);
  color: var(--text-primary);
}

.login-brand {
  display: inline-flex;
  color: var(--accent);
  margin-bottom: 16px;
}

.login-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.login-sub {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 28px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  text-align: left;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.login-field span {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.03em;
}

.login-field input {
  padding: 10px 14px;
  border: 1.5px solid var(--border-color);
  border-radius: 8px;
  font-size: 0.875rem;
  background: transparent;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.2s var(--ease-out);
}
.login-field input::placeholder {
  color: var(--text-muted);
  font-weight: 400;
}
.login-field input:focus {
  border-color: var(--accent);
}

.btn-submit {
  padding: 11px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 4px;
}
.btn-submit:hover { background: var(--accent-hover); }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.overlay-enter-active, .overlay-leave-active {
  transition: opacity 0.2s ease;
}
.overlay-enter-from, .overlay-leave-to { opacity: 0; }

/* ── Responsive ───────────────────────────── */
@media (max-width: 768px) {
  .nav { display: none; }
  .header-inner { gap: 16px; }
  .login-card { width: calc(100% - 32px); padding: 32px 24px; }
  .footer-links { gap: 16px; }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .nav { gap: 0; }
}
</style>
