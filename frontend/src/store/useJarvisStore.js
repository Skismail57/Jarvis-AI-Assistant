import { create } from 'zustand'

const useJarvisStore = create((set, get) => ({
  activeTab: 'chat',
  setActiveTab: (tab) => set({ activeTab: tab }),

  messages: [],
  isStreaming: false,
  isListening: false,
  streamingMessageId: null,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),

  appendStreamingToken: (token) => set((state) => {
    const id = state.streamingMessageId
    if (!id) return {}
    return {
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + token } : m
      ),
    }
  }),

  finalizeStreamingMessage: (data) => set((state) => {
    const id = state.streamingMessageId
    if (!id) return { isStreaming: false, streamingMessageId: null }
    return {
      messages: state.messages.map((m) =>
        m.id === id ? {
          ...m,
          content: data?.content || m.content,
          intent: data?.intent || m.intent,
          confidence: data?.confidence || m.confidence,
          detected_language: data?.detected_language || m.detected_language,
          skill_result: data?.skill_result || m.skill_result,
          streaming: false,
          timestamp: new Date().toISOString(),
        } : m
      ),
      isStreaming: false,
      streamingMessageId: null,
    }
  }),

  startStreaming: (messageId) => set({
    isStreaming: true,
    streamingMessageId: messageId,
  }),

  stopStreaming: () => set({ isStreaming: false, streamingMessageId: null }),

  setIsListening: (val) => set({ isListening: val }),

  clearMessages: () => set({ messages: [] }),

  metrics: {
    cpu_percent: 0,
    cpu_freq_mhz: 0,
    ram_total_gb: 0,
    ram_used_gb: 0,
    ram_percent: 0,
    disk_total_gb: 0,
    disk_used_gb: 0,
    disk_percent: 0,
    net_up_mbps: 0,
    net_down_mbps: 0,
    uptime_seconds: 0,
    process_count: 0,
    load_avg: [0, 0, 0],
    timestamp: '',
  },

  metricsHistory: {
    cpu: [],
    ram: [],
    net_up: [],
    net_down: [],
  },

  setMetrics: (m) => set((state) => {
    const now = Date.now()
    const maxPoints = 60
    const pushHist = (arr, val) => {
      const next = [...arr, { time: now, value: val }]
      return next.slice(-maxPoints)
    }
    return {
      metrics: m,
      metricsHistory: {
        cpu: pushHist(state.metricsHistory.cpu, m.cpu_percent),
        ram: pushHist(state.metricsHistory.ram, m.ram_percent),
        net_up: pushHist(state.metricsHistory.net_up, m.net_up_mbps),
        net_down: pushHist(state.metricsHistory.net_down, m.net_down_mbps),
      },
    }
  }),

  status: {
    name: 'Jarvis',
    version: '2.0.0',
    mode: 'idle',
    wake_word: 'jarvis',
    active_user_id: 'default',
    language: 'en-US',
    tts_engine: 'pyttsx3',
    stt_engine: 'sr',
    llm_model: 'auto',
    uptime_seconds: 0,
    diagnostics_passed: 0,
    diagnostics_total: 7,
    plugins_loaded: 0,
    skills_available: 0,
    api_keys_configured: {},
    features_enabled: {},
  },

  setStatus: (s) => set({ status: { ...get().status, ...s } }),

  settings: {},
  setSettings: (s) => set({ settings: { ...get().settings, ...s } }),

  reminders: [],
  setReminders: (r) => set({ reminders: r }),
  addReminder: (r) => set((state) => ({ reminders: [r, ...state.reminders] })),
  removeReminder: (id) => set((state) => ({
    reminders: state.reminders.filter((r) => r.id !== id),
  })),

  profiles: [],
  activeProfileId: 'default',
  setProfiles: (p) => set({ profiles: p }),
  setActiveProfileId: (id) => set({ activeProfileId: id }),
  addProfile: (p) => set((state) => ({ profiles: [...state.profiles, p] })),

  plugins: [],
  setPlugins: (p) => set({ plugins: p }),

  memoryStats: {
    short_term_turns: 0,
    long_term_items: 0,
    long_term_size_bytes: 0,
    top_k: 5,
    min_score: 0.35,
    vector_db: 'chromadb',
  },
  setMemoryStats: (m) => set({ memoryStats: m }),

  connectionStatus: 'disconnected',
  wsChatConnected: false,
  wsMetricsConnected: false,

  setConnectionStatus: (s) => set({ connectionStatus: s }),
  setWsChatConnected: (v) => set({ wsChatConnected: v }),
  setWsMetricsConnected: (v) => set({ wsMetricsConnected: v }),
}))

export default useJarvisStore
