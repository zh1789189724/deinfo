import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// ── Mock Element Plus CSS imports ──────────
// Element Plus ESM entries import CSS files via bare specifiers.
// These must be mocked so vitest doesn't try to load them as JS.
vi.mock('element-plus/theme-chalk/base.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-button.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-card.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-tag.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-tabs.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-input.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-select.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-form.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-table.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-pagination.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-dialog.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-loading.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-empty.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-message.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-divider.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-icon.css', () => ({}))
vi.mock('@/api', () => {
  const mockData = (data) => ({ data, total: data.length })

  return {
    authApi: {
      login: vi.fn().mockResolvedValue({ token: 'test-token', role: 'ADMIN', username: 'admin' }),
    },
    dealApi: {
      list: vi.fn().mockResolvedValue(mockData([])),
      get: vi.fn().mockResolvedValue({ id: 1, title: 'Test Deal', content: 'detail' }),
      top: vi.fn().mockResolvedValue(mockData([])),
    },
    globalApi: {
      list: vi.fn().mockResolvedValue(mockData([])),
      get: vi.fn().mockResolvedValue({ id: 1, title: 'Test Global', content: 'detail' }),
      top: vi.fn().mockResolvedValue(mockData([])),
    },
    opportunityApi: {
      list: vi.fn().mockResolvedValue(mockData([])),
    },
    toolApi: {
      list: vi.fn().mockResolvedValue(mockData([])),
    },
    submitApi: {
      create: vi.fn().mockResolvedValue({ id: 1 }),
    },
    adminApi: {
      pending: vi.fn().mockResolvedValue(mockData([])),
      approve: vi.fn().mockResolvedValue({}),
      reject: vi.fn().mockResolvedValue({}),
    },
  }
})

// ── Mock localStorage ───────────────────────
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, val) => { store[key] = String(val) }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// ── Mock Element Plus icons ─────────────────
vi.mock('@element-plus/icons-vue', () => ({
  Search: { render: () => {} },
  ArrowLeft: { render: () => {} },
  Link: { render: () => {} },
  Location: { render: () => {} },
}))

// ── Global stubs ────────────────────────────
config.global.stubs = {
  'router-link': {
    props: ['to'],
    template: '<a :href="typeof to === \'string\' ? to : to?.path || \'/\'" class="router-link-stub"><slot /></a>',
  },
  'router-view': { template: '<div class="router-view-stub"><slot /></div>' },
  'el-tabs': { template: '<div class="el-tabs-stub"><slot /></div>' },
  'el-tab-pane': { template: '<div class="el-tab-pane-stub"><slot /></div>' },
  'el-row': { template: '<div class="el-row-stub"><slot /></div>' },
  'el-col': { template: '<div class="el-col-stub"><slot /></div>' },
  'el-card': { template: '<div class="el-card-stub"><slot /></div>' },
  'el-empty': { template: '<div class="el-empty-stub">{{ description }}</div>', props: ['description', 'imageSize'] },
  'el-skeleton': { template: '<div class="el-skeleton-stub"><slot /></div>' },
  'el-pagination': { template: '<div class="el-pagination-stub"><slot /></div>', props: ['currentPage', 'pageSize', 'total'] },
  'el-tag': { template: '<span class="el-tag-stub"><slot /></span>', props: ['type', 'size', 'effect'] },
  'el-input': { template: '<input class="el-input-stub" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" @keyup.enter="$emit(\'keyup.enter\')" @clear="$emit(\'clear\')" />', props: ['modelValue', 'placeholder', 'clearable', 'prefixIcon'] },
  'el-button': { template: '<button class="el-button-stub" :disabled="disabled" :type="nativeType || \'button\'" @click="$emit(\'click\')"><slot /></button>', props: ['type', 'size', 'loading', 'disabled', 'nativeType', 'text'] },
  'el-select': { template: '<div class="el-select-stub"><slot /></div>', props: ['modelValue'] },
  'el-option': { template: '<div class="el-option-stub"><slot /></div>', props: ['label', 'value'] },
  'el-form': { template: '<form class="el-form-stub"><slot /></form>' },
  'el-form-item': { template: '<div class="el-form-item-stub"><label v-if="label" class="el-form-item-label">{{ label }}</label><slot /></div>', props: ['label', 'prop'] },
  'el-radio-group': { template: '<div class="el-radio-group-stub"><slot /></div>', props: ['modelValue'] },
  'el-radio-button': { template: '<label class="el-radio-button-stub"><slot /></label>', props: ['value'] },
  'el-icon': { template: '<i class="el-icon-stub"><slot /></i>' },
  'el-table': { template: '<div class="el-table-stub"><slot :row="{}" :$index="0" /></div>' },
  'el-table-column': { template: '<div class="el-table-column-stub"><slot :row="{}" :$index="0" /></div>', props: ['prop', 'label', 'width', 'minWidth'] },
  'el-dialog': { template: '<div class="el-dialog-stub"><slot name="footer" /></div>', props: ['modelValue', 'title', 'width', 'closeOnClickModal'] },
  'el-divider': { template: '<hr class="el-divider-stub" />' },
}

// ── Register v-loading directive stub ──────
config.global.directives = {
  loading: {
    mounted: () => {},
    updated: () => {},
  },
}

// ── Element Plus mock helpers ───────────────
// Provide ElMessage stub
config.global.provide = {
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}

// ── Setup Pinia ─────────────────────────────
export function setupPinia() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return pinia
}

// ── Mock data factories ─────────────────────
export function makeDeal(overrides = {}) {
  return {
    id: 1,
    title: '测试优惠标题',
    summary: '这是一个测试优惠摘要',
    category: '优惠券',
    score: 85,
    location: '成都',
    price: '¥99',
    source_url: 'https://example.com',
    ...overrides,
  }
}

export function makeGlobal(overrides = {}) {
  return {
    id: 1,
    title: 'Original Title',
    title_cn: '翻译标题',
    summary_cn: '这是中文摘要内容',
    category: '技术',
    lang: 'en',
    original_url: 'https://example.com',
    createdAt: '2026-06-01T00:00:00Z',
    ...overrides,
  }
}

export function makeOpportunity(overrides = {}) {
  return {
    id: 1,
    title: '测试投资机会',
    description: '这是一个投资机会描述',
    category: '投资',
    status: '进行中',
    createdAt: '2026-06-01T00:00:00Z',
    ...overrides,
  }
}

export function makeTool(overrides = {}) {
  return {
    id: 1,
    name: 'Test Tool',
    summary: '好用工具',
    description: '工具详细描述',
    tags: '效率, 开发',
    url: 'https://example.com',
    ...overrides,
  }
}
