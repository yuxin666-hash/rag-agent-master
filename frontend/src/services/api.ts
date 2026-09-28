import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动注入 Bearer Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理，401 自动清除 token 并刷新页面回到登录页
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.reload()
      return Promise.reject(new Error('登录已过期，请重新登录'))
    }
    const msg = error.response?.data?.msg || '网络请求失败，请稍后重试'
    return Promise.reject(new Error(msg))
  }
)

export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

export const authApi = {
  login: (username: string, password: string): Promise<ApiResponse<{ token: string; username: string }>> =>
    api.post('/login', { username, password }),

  register: (username: string, password: string): Promise<ApiResponse<null>> =>
    api.post('/register', { username, password }),

  logout: (): Promise<ApiResponse<null>> =>
    api.post('/logout'),

  getMe: (): Promise<ApiResponse<{ username: string }>> =>
    api.get('/me')
}

export interface SessionItem {
  session_id: string
  title: string
  message_count: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export const chatApi = {
  createSession: (): Promise<ApiResponse<{ session_id: string }>> =>
    api.post('/chat/sessions'),

  listSessions: (): Promise<ApiResponse<{ sessions: SessionItem[] }>> =>
    api.get('/chat/sessions'),

  getSessionHistory: (sessionId: string): Promise<ApiResponse<{ session_id: string; messages: ChatMessage[] }>> =>
    api.get(`/chat/sessions/${sessionId}`),

  deleteSession: (sessionId: string): Promise<ApiResponse<null>> =>
    api.delete(`/chat/sessions/${sessionId}`),

  sendMessage: (message: string, sessionId?: string): Promise<ApiResponse<{ reply: string; session_id: string }>> =>
    api.post('/chat', { message, session_id: sessionId })
}

export default api
