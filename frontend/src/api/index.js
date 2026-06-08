import http from './http'

export const authApi = {
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data),
}

export const dealApi = {
  list: (page = 1, size = 20, keyword = '', category = '') => http.get('/deals', { params: { page, size, keyword, category } }),
  get: (id) => http.get(`/deals/${id}`),
  top: () => http.get('/deals/top'),
  create: (data) => http.post('/deals', data),
  update: (id, data) => http.put(`/deals/${id}`, data),
  delete: (id) => http.delete(`/deals/${id}`),
}

export const globalApi = {
  list: (page = 1, size = 20) => http.get('/global', { params: { page, size } }),
  get: (id) => http.get(`/global/${id}`),
  top: () => http.get('/global/top'),
  create: (data) => http.post('/global', data),
  update: (id, data) => http.put(`/global/${id}`, data),
  delete: (id) => http.delete(`/global/${id}`),
}

export const opportunityApi = {
  list: (page = 1, size = 20) => http.get('/opportunities', { params: { page, size } }),
  get: (id) => http.get(`/opportunities/${id}`),
  create: (data) => http.post('/opportunities', data),
  update: (id, data) => http.put(`/opportunities/${id}`, data),
  delete: (id) => http.delete(`/opportunities/${id}`),
}

export const toolApi = {
  list: (page = 1, size = 20, tag) => http.get('/tools', { params: { page, size, tag } }),
  get: (id) => http.get(`/tools/${id}`),
  create: (data) => http.post('/tools', data),
  update: (id, data) => http.put(`/tools/${id}`, data),
  delete: (id) => http.delete(`/tools/${id}`),
}

export const submitApi = {
  create: (data) => http.post('/submit', data),
}

export const adminApi = {
  pending: () => http.get('/admin/pending'),
  approve: (id) => http.put(`/admin/submit/${id}/approve`),
  reject: (id, reason) => http.put(`/admin/submit/${id}/reject`, { reason }),
  stats: () => http.get('/admin/stats'),
}
