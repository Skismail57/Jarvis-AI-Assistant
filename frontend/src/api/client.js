import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('[API Error]', error.message, error.response?.data)
    return Promise.reject(error.response?.data || error.message)
  }
)

export default api

export const jarvisApi = {
  health: () => api.get('/health'),
  status: () => api.get('/status'),
  metrics: () => api.get('/metrics'),

  chat: (message, { user_id = 'default', speak = false, mode = 'text', stream = true } = {}) =>
    api.post('/chat', { message, user_id, speak, mode, stream }),

  getSettings: () => api.get('/settings'),
  updateSettings: (updates) => api.put('/settings', updates),

  getMemoryStats: () => api.get('/memory'),
  clearMemory: (kind = 'all') => api.delete('/memory', { params: { kind } }),

  listReminders: () => api.get('/reminders'),
  addReminder: (text, when_natural = 'in 1 hour') =>
    api.post('/reminders', null, { params: { text, when_natural } }),
  cancelReminder: (id) => api.delete(`/reminders/${id}`),

  listProfiles: () => api.get('/profiles'),
  createProfile: (profile) => api.post('/profiles', profile),
  updateProfile: (id, profile) => api.put(`/profiles/${id}`, profile),
  activateProfile: (id) => api.post(`/profiles/${id}/activate`),

  listPlugins: () => api.get('/plugins'),

  retrainClassifier: () => api.post('/skills/retrain'),
}

const WS_PROTOCOLS = () =>
  window.location.protocol === 'https:' ? ['wss:', 'wss:'] : ['ws:', 'ws:']

class JarvisWS {
  constructor(endpoint) {
    this.endpoint = endpoint
    this.ws = null
    this.listeners = {}
    this.reconnectTimer = null
    this.reconnectAttempts = 0
    this.maxReconnectDelay = 10000
    this.manualClose = false
    this.onConnectHandlers = []
    this.onDisconnectHandlers = []
  }

  _getFullUrl() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${proto}//${host}${this.endpoint}`
  }

  connect() {
    this.manualClose = false
    return new Promise((resolve, reject) => {
      try {
        const url = this._getFullUrl()
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          this.reconnectAttempts = 0
          this._fire('connect')
          this.onConnectHandlers.forEach((fn) => fn())
          resolve(true)
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this._fire('message', data)
          } catch {
            this._fire('message', event.data)
          }
        }

        this.ws.onerror = (err) => {
          console.error(`[WS ${this.endpoint}] error`, err)
          this._fire('error', err)
          reject(err)
        }

        this.ws.onclose = (event) => {
          this._fire('close', event)
          this.onDisconnectHandlers.forEach((fn) => fn())
          if (!this.manualClose) {
            this._scheduleReconnect()
          }
        }
      } catch (err) {
        reject(err)
      }
    })
  }

  _scheduleReconnect() {
    this.reconnectAttempts++
    const delay = Math.min(
      1000 * Math.pow(1.5, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    )
    console.warn(
      `[WS ${this.endpoint}] reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts})`
    )
    clearTimeout(this.reconnectTimer)
    this.reconnectTimer = setTimeout(() => this.connect(), delay)
  }

  disconnect() {
    this.manualClose = true
    clearTimeout(this.reconnectTimer)
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const payload = typeof data === 'string' ? data : JSON.stringify(data)
      this.ws.send(payload)
      return true
    }
    console.warn(`[WS ${this.endpoint}] not connected, cannot send`)
    return false
  }

  on(event, handler) {
    if (!this.listeners[event]) this.listeners[event] = []
    this.listeners[event].push(handler)
    return () => this.off(event, handler)
  }

  off(event, handler) {
    if (!this.listeners[event]) return
    this.listeners[event] = this.listeners[event].filter((fn) => fn !== handler)
  }

  _fire(event, data) {
    (this.listeners[event] || []).forEach((fn) => {
      try { fn(data) } catch (e) { console.error(e) }
    })
  }

  onConnect(fn) { this.onConnectHandlers.push(fn); return () => this.onConnectHandlers = this.onConnectHandlers.filter(x => x !== fn) }
  onDisconnect(fn) { this.onDisconnectHandlers.push(fn); return () => this.onDisconnectHandlers = this.onDisconnectHandlers.filter(x => x !== fn) }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

export const chatWS = new JarvisWS('/ws/chat')
export const metricsWS = new JarvisWS('/ws/metrics')
