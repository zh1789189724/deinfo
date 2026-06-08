import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('@/views/Home.vue') },
  { path: '/global', component: () => import('@/views/Global.vue') },
  { path: '/deals', component: () => import('@/views/Deal.vue') },
  { path: '/deals/:id', component: () => import('@/views/Detail.vue'), props: true },
  { path: '/opportunities', component: () => import('@/views/Opportunity.vue') },
  { path: '/tools', component: () => import('@/views/Tool.vue') },
  { path: '/submit', component: () => import('@/views/Submit.vue') },
  { path: '/admin', component: () => import('@/views/Admin.vue'), meta: { admin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to, from, next) => {
  if (to.meta.admin) {
    const token = localStorage.getItem('token')
    if (!token) {
      alert('请先登录')
      next('/')
      return
    }
  }
  next()
})

export default router
