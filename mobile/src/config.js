// Jarvis Mobile App Configuration
// Update these values to match your Jarvis server

export const JARVIS_SERVER_URL = 'http://192.168.1.100:8000';
export const WS_CHAT_URL = 'ws://192.168.1.100:8000/ws/chat';
export const WS_METRICS_URL = 'ws://192.168.1.100:8000/ws/metrics';

// API Endpoints
export const API_ENDPOINTS = {
  HEALTH: `${JARVIS_SERVER_URL}/api/health`,
  STATUS: `${JARVIS_SERVER_URL}/api/status`,
  METRICS: `${JARVIS_SERVER_URL}/api/metrics`,
  CHAT: `${JARVIS_SERVER_URL}/api/chat`,
  SETTINGS: `${JARVIS_SERVER_URL}/api/settings`,
  MEMORY: `${JARVIS_SERVER_URL}/api/memory`,
  REMINDERS: `${JARVIS_SERVER_URL}/api/reminders`,
  PROFILES: `${JARVIS_SERVER_URL}/api/profiles`,
  PLUGINS: `${JARVIS_SERVER_URL}/api/plugins`,
};

// App Settings
export const APP_CONFIG = {
  RECONNECT_INTERVAL: 5000, // ms
  MAX_RECONNECT_ATTEMPTS: 10,
  MESSAGE_TIMEOUT: 30000, // ms
  METRICS_UPDATE_INTERVAL: 2000, // ms
};
