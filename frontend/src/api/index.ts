import http from './http'

export const authApi = {
  login: (data: any) => http.post('/auth/login', data).then((r) => r.data),
  register: (data: any) => http.post('/auth/register', data).then((r) => r.data),
  changePassword: (data: any) => http.post('/auth/change-password', data).then((r) => r.data),
}

export const convApi = {
  list: () => http.get('/conversations').then((r) => r.data),
  create: (data?: any) => http.post('/conversations', data || {}).then((r) => r.data),
  messages: (id: number) => http.get(`/conversations/${id}/messages`).then((r) => r.data),
  remove: (id: number) => http.delete(`/conversations/${id}`).then((r) => r.data),
}

export const kbApi = {
  list: () => http.get('/knowledge').then((r) => r.data),
  create: (data: any) => http.post('/knowledge', data).then((r) => r.data),
  remove: (id: number) => http.delete(`/knowledge/${id}`).then((r) => r.data),
  docs: (id: number) => http.get(`/knowledge/${id}/documents`).then((r) => r.data),
  upload: (id: number, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post(`/knowledge/${id}/documents`, fd).then((r) => r.data)
  },
  removeDoc: (id: number, docId: number) =>
    http.delete(`/knowledge/${id}/documents/${docId}`).then((r) => r.data),
}

export const chatApi = {
  feedback: (msgId: number, feedback: string) =>
    http.post(`/chat/messages/${msgId}/feedback`, { feedback }).then((r) => r.data),
}

export const adminApi = {
  stats: () => http.get('/admin/stats').then((r) => r.data),
  users: () => http.get('/admin/users').then((r) => r.data),
}
