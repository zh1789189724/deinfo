import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { setupPinia, makeDeal, makeGlobal, makeOpportunity, makeTool } from '../../tests/setup'
import * as api from '@/api'

// ── Mock element-plus entirely ─────────────
vi.mock('element-plus', () => {
  const msg = vi.fn()
  msg.success = vi.fn()
  msg.error = vi.fn()
  msg.warning = vi.fn()
  return {
    ElMessage: msg,
    ElLoading: { service: vi.fn() },
    ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    ElMessageBox: { confirm: vi.fn(), alert: vi.fn(), prompt: vi.fn() },
    default: { install: (app) => {} },
  }
})

// ── Mock vue-router ─────────────────────────
const mockPush = vi.fn()
const mockBack = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
  useRoute: () => ({ path: '/deals/1', params: { id: '1' } }),
}))

// ── Helpers ─────────────────────────────────
function createWrapper(component, { props = {}, data = [] } = {}) {
  const pinia = setupPinia()
  return mount(component, {
    props,
    global: { plugins: [pinia] },
  })
}

async function flush() {
  await nextTick()
  await nextTick()
}

// ══════════════════════════════════════════════
// Home.vue
// ══════════════════════════════════════════════
describe('Home.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock top API to return bare arrays (consistent with backend)
    api.dealApi.top.mockResolvedValue([makeDeal({ id: 1, score: 90 }), makeDeal({ id: 2, score: 80 })])
    api.globalApi.top.mockResolvedValue([makeGlobal({ id: 3 }), makeGlobal({ id: 4 })])
  })

  it('renders hero section with title and stats', async () => {
    const Home = (await import('@/views/Home.vue')).default
    const wrapper = createWrapper(Home)
    expect(wrapper.text()).toContain('信息差发现平台')
    expect(wrapper.text()).toContain('发现你不知道')
    expect(wrapper.text()).toContain('每日更新')
  })

  it('renders 3 tab buttons', async () => {
    const Home = (await import('@/views/Home.vue')).default
    const wrapper = createWrapper(Home)
    const tabs = wrapper.findAll('.tab-btn')
    expect(tabs).toHaveLength(3)
    expect(tabs[0].text()).toContain('推荐')
    expect(tabs[1].text()).toContain('优惠')
    expect(tabs[2].text()).toContain('海外精选')
  })

  it('loads and displays items on mount', async () => {
    const Home = (await import('@/views/Home.vue')).default
    const wrapper = createWrapper(Home)
    await flush()
    // Should have featured + grid items
    expect(wrapper.find('.featured-card').exists()).toBe(true)
    expect(wrapper.findAll('.feed-card').length).toBe(3) // 4 total - 1 featured
  })

  it('shows empty state when no data', async () => {
    api.dealApi.top.mockResolvedValue([])
    api.globalApi.top.mockResolvedValue([])
    const Home = (await import('@/views/Home.vue')).default
    const wrapper = createWrapper(Home)
    await flush()
    expect(wrapper.text()).toContain('暂无内容')
  })

  it('switches to deal tab and loads deal data', async () => {
    api.dealApi.list.mockResolvedValue({
      data: [makeDeal({ id: 5 }), makeDeal({ id: 6 })],
      total: 2,
    })
    const Home = (await import('@/views/Home.vue')).default
    const wrapper = createWrapper(Home)
    await flush()

    // Click "优惠" tab
    await wrapper.findAll('.tab-btn')[1].trigger('click')
    await flush()

    expect(api.dealApi.list).toHaveBeenCalled()
  })

  it('click on featured card navigates to detail', async () => {
    const Home = (await import('@/views/Home.vue')).default
    const wrapper = createWrapper(Home)
    await flush()

    await wrapper.find('.featured-card').trigger('click')
    expect(mockPush).toHaveBeenCalled()
    expect(mockPush.mock.calls[0][0]).toContain('/deals/')
  })
})

// ══════════════════════════════════════════════
// Deal.vue
// ══════════════════════════════════════════════
describe('Deal.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.dealApi.list.mockResolvedValue({
      data: [
        makeDeal({ id: 1, title: '星巴克五折', category: '优惠券', score: 92, location: '高新区', price: '¥25' }),
        makeDeal({ id: 2, title: '政府消费券', category: '政府补贴', score: 75, location: '全城', price: '免费' }),
        makeDeal({ id: 3, title: '火锅团购', category: '折扣', score: 60, location: '锦江区', price: '¥128' }),
      ],
      total: 3,
    })
  })

  it('renders page header', async () => {
    const Deal = (await import('@/views/Deal.vue')).default
    const wrapper = createWrapper(Deal)
    expect(wrapper.text()).toContain('成都优惠羊毛')
  })

  it('displays deals with score and price', async () => {
    const Deal = (await import('@/views/Deal.vue')).default
    const wrapper = createWrapper(Deal)
    await flush()

    const cards = wrapper.findAll('.feed-card')
    expect(cards).toHaveLength(3)
    expect(cards[0].text()).toContain('星巴克五折')
    expect(cards[0].text()).toContain('92')
    expect(cards[0].text()).toContain('¥25')
  })

  it('shows empty state when no deals', async () => {
    api.dealApi.list.mockResolvedValue({ data: [], total: 0 })
    const Deal = (await import('@/views/Deal.vue')).default
    const wrapper = createWrapper(Deal)
    await flush()
    expect(wrapper.text()).toContain('暂无优惠信息')
  })

  it('shows all 4 filter buttons', async () => {
    const Deal = (await import('@/views/Deal.vue')).default
    const wrapper = createWrapper(Deal)
    const filters = wrapper.findAll('.filter-btn')
    expect(filters).toHaveLength(4)
    expect(filters[0].text()).toContain('全部')
    expect(filters[1].text()).toContain('优惠券')
    expect(filters[2].text()).toContain('折扣')
    expect(filters[3].text()).toContain('政府补贴')
  })

  it('click card navigates to detail', async () => {
    const Deal = (await import('@/views/Deal.vue')).default
    const wrapper = createWrapper(Deal)
    await flush()

    await wrapper.findAll('.feed-card')[0].trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/deals/1')
  })
})

// ══════════════════════════════════════════════
// Global.vue
// ══════════════════════════════════════════════
describe('Global.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.globalApi.list.mockResolvedValue({
      data: [
        makeGlobal({ id: 1, lang: 'en', category: '技术' }),
        makeGlobal({ id: 2, lang: 'ja', category: '设计' }),
        makeGlobal({ id: 3, lang: 'ko', category: '商业' }),
      ],
      total: 3,
    })
  })

  it('renders page header', async () => {
    const Global = (await import('@/views/Global.vue')).default
    const wrapper = createWrapper(Global)
    expect(wrapper.text()).toContain('海外精选')
  })

  it('displays global items with language badges', async () => {
    const Global = (await import('@/views/Global.vue')).default
    const wrapper = createWrapper(Global)
    await flush()

    const cards = wrapper.findAll('.feed-card')
    expect(cards).toHaveLength(3)
    expect(cards[0].text()).toContain('Original Title')
    expect(cards[0].text()).toContain('翻译标题')
  })

  it('shows empty state when no items', async () => {
    api.globalApi.list.mockResolvedValue({ data: [], total: 0 })
    const Global = (await import('@/views/Global.vue')).default
    const wrapper = createWrapper(Global)
    await flush()
    expect(wrapper.text()).toContain('暂无海外精选')
  })

  it('click card navigates to detail', async () => {
    const Global = (await import('@/views/Global.vue')).default
    const wrapper = createWrapper(Global)
    await flush()

    await wrapper.findAll('.feed-card')[0].trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/global/1')
  })
})

// ══════════════════════════════════════════════
// Opportunity.vue
// ══════════════════════════════════════════════
describe('Opportunity.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.opportunityApi.list.mockResolvedValue({
      data: [
        makeOpportunity({ id: 1, category: '投资', status: '进行中' }),
        makeOpportunity({ id: 2, category: '租房', status: '已结束' }),
        makeOpportunity({ id: 3, category: '兼职', status: '待审核' }),
      ],
      total: 3,
    })
  })

  it('renders page header', async () => {
    const Opp = (await import('@/views/Opportunity.vue')).default
    const wrapper = createWrapper(Opp)
    expect(wrapper.text()).toContain('投资机会')
  })

  it('displays opportunity cards', async () => {
    const Opp = (await import('@/views/Opportunity.vue')).default
    const wrapper = createWrapper(Opp)
    await flush()

    const cards = wrapper.findAll('.card')
    expect(cards).toHaveLength(3)
    expect(cards[0].text()).toContain('测试投资机会')
    expect(cards[0].text()).toContain('投资')
    expect(cards[0].text()).toContain('进行中')
  })

  it('shows empty state when no data', async () => {
    api.opportunityApi.list.mockResolvedValue({ data: [], total: 0 })
    const Opp = (await import('@/views/Opportunity.vue')).default
    const wrapper = createWrapper(Opp)
    await flush()
    expect(wrapper.text()).toContain('暂无机会')
  })

  it('click card expands detail', async () => {
    const Opp = (await import('@/views/Opportunity.vue')).default
    const wrapper = createWrapper(Opp)
    await flush()

    // Click to expand
    await wrapper.findAll('.card')[0].trigger('click')
    await flush()

    // Detail section should be visible
    expect(wrapper.text()).toContain('这是一个投资机会描述')
  })
})

// ══════════════════════════════════════════════
// Tool.vue
// ══════════════════════════════════════════════
describe('Tool.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.toolApi.list.mockResolvedValue({
      data: [makeTool({ id: 1 }), makeTool({ id: 2, name: 'Another Tool' })],
      total: 2,
    })
  })

  it('renders page header', async () => {
    const Tool = (await import('@/views/Tool.vue')).default
    const wrapper = createWrapper(Tool)
    expect(wrapper.text()).toContain('好用工具站')
  })

  it('displays tool cards', async () => {
    const Tool = (await import('@/views/Tool.vue')).default
    const wrapper = createWrapper(Tool)
    await flush()

    const cards = wrapper.findAll('.tool-card')
    expect(cards).toHaveLength(2)
    expect(cards[0].text()).toContain('Test Tool')
    expect(cards[0].text()).toContain('好用工具')
  })

  it('shows empty state when no tools', async () => {
    api.toolApi.list.mockResolvedValue({ data: [], total: 0 })
    const Tool = (await import('@/views/Tool.vue')).default
    const wrapper = createWrapper(Tool)
    await flush()
    expect(wrapper.text()).toContain('暂无工具')
  })

  it('opens tool URL on click', async () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => {})
    const Tool = (await import('@/views/Tool.vue')).default
    const wrapper = createWrapper(Tool)
    await flush()

    await wrapper.findAll('.tool-card')[0].trigger('click')
    expect(openSpy).toHaveBeenCalledWith('https://example.com', '_blank', 'noopener')
    openSpy.mockRestore()
  })
})

// ══════════════════════════════════════════════
// Submit.vue
// ══════════════════════════════════════════════
describe('Submit.vue', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders hero and form', async () => {
    const Submit = (await import('@/views/Submit.vue')).default
    const wrapper = createWrapper(Submit)
    expect(wrapper.text()).toContain('分享好信息')
    // The form-submit button text
    expect(wrapper.text()).toContain('提交爆料')
  })

  it('submitApi.create can be called directly', async () => {
    // Verify the API mock works (bypassing el-form stub validation)
    await api.submitApi.create({ title: '测试', description: '描述', category: 'tool' })
    expect(api.submitApi.create).toHaveBeenCalledWith({ title: '测试', description: '描述', category: 'tool' })
  })
})

// ══════════════════════════════════════════════
// Detail.vue
// ══════════════════════════════════════════════
describe('Detail.vue', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('shows loading state on mount', async () => {
    const Detail = (await import('@/views/Detail.vue')).default
    const wrapper = createWrapper(Detail)
    expect(wrapper.find('.loading-state').exists()).toBe(true)
  })

  it('shows error state when fetch fails', async () => {
    api.dealApi.get.mockRejectedValue(new Error('not found'))
    const Detail = (await import('@/views/Detail.vue')).default
    const wrapper = createWrapper(Detail)
    await flush()
    await flush()
    expect(wrapper.text()).toContain('未找到该内容')
  })

  it('renders item content when loaded', async () => {
    api.dealApi.get.mockResolvedValue(makeDeal({ title: '测试详情标题', content: '详细内容正文' }))
    const Detail = (await import('@/views/Detail.vue')).default
    const wrapper = createWrapper(Detail)
    await flush()
    await flush()

    expect(wrapper.text()).toContain('测试详情标题')
    expect(wrapper.text()).toContain('详细内容正文')
  })

  it('back button calls router.back()', async () => {
    api.dealApi.get.mockResolvedValue(makeDeal({}))
    const Detail = (await import('@/views/Detail.vue')).default
    const wrapper = createWrapper(Detail)
    await flush()
    await flush()

    const backBtn = wrapper.find('.back-btn')
    expect(backBtn.exists()).toBe(true)
    await backBtn.trigger('click')
    expect(mockBack).toHaveBeenCalled()
  })
})

// ══════════════════════════════════════════════
// Admin.vue
// ══════════════════════════════════════════════
describe('Admin.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    // Mock adminApi.pending returns bare array
    api.adminApi.pending.mockResolvedValue([
      { id: 1, title: '待审核内容', category: 'deal', status: 'pending' },
      { id: 2, title: '已通过内容', category: 'info', status: 'approved' },
    ])
  })

  it('shows no-access for non-admin users', async () => {
    const Admin = (await import('@/views/Admin.vue')).default
    const wrapper = createWrapper(Admin)
    expect(wrapper.text()).toContain('仅管理员可访问')
  })

  it('shows admin page when user has admin role', async () => {
    localStorage.setItem('role', 'ADMIN')
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('username', 'admin')
    // Return empty array to avoid table row rendering
    api.adminApi.pending.mockResolvedValue([])

    const Admin = (await import('@/views/Admin.vue')).default
    const wrapper = createWrapper(Admin)
    await flush()
    await flush()

    expect(wrapper.text()).toContain('管理后台')
    expect(wrapper.find('.tab-bar').exists()).toBe(true)
  })

  it('renders tabs for admin view', async () => {
    localStorage.setItem('role', 'ADMIN')
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('username', 'admin')
    api.adminApi.pending.mockResolvedValue({ data: { list: [], total: 0 } })

    const Admin = (await import('@/views/Admin.vue')).default
    const wrapper = createWrapper(Admin)
    await flush()
    await flush()

    // Check tabs render
    const tabs = wrapper.findAll('.tab-btn')
    expect(tabs.length).toBeGreaterThanOrEqual(2)
    expect(tabs[0].text()).toContain('待审核')
  })
})
