import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Cpu, Activity, Mic, User, Wifi, WifiOff, Battery,
  Settings as SettingsIcon, LogOut
} from 'lucide-react'
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import useJarvisStore from './store/useJarvisStore'
import useAuthStore from './store/authStore'
import { jarvisApi, chatWS, metricsWS } from './api/client'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import SystemDashboard from './components/SystemDashboard'
import SettingsPanel from './components/SettingsPanel'
import SkillsPanel from './components/SkillsPanel'
import RemindersPanel from './components/RemindersPanel'
import ProfilesPanel from './components/ProfilesPanel'
import MemoryPanel from './components/MemoryPanel'
import Login from './components/Login'
import Signup from './components/Signup'
import BiometricEnroll from './components/BiometricEnroll'

const formatShortUptime = (s) => {
  const sec = Math.max(0, Math.floor(s))
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  return `${h}h ${m}m`
}

const AnimatedOrbs = () => (
  <div className="fixed inset-0 overflow-hidden pointer-events-none">
    <motion.div
      className="absolute w-96 h-96 rounded-full blur-3xl opacity-20"
      style={{
        background: 'linear-gradient(135deg, #ff2e88, #7b2ff7)',
        top: '-10%',
        left: '-10%',
      }}
      animate={{
        x: [0, 100, 0],
        y: [0, -50, 0],
      }}
      transition={{
        duration: 20,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
    <motion.div
      className="absolute w-96 h-96 rounded-full blur-3xl opacity-20"
      style={{
        background: 'linear-gradient(135deg, #7b2ff7, #00eaff)',
        bottom: '-10%',
        right: '-10%',
      }}
      animate={{
        x: [0, -100, 0],
        y: [0, 50, 0],
      }}
      transition={{
        duration: 25,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
    <motion.div
      className="absolute w-64 h-64 rounded-full blur-3xl opacity-15"
      style={{
        background: 'linear-gradient(135deg, #00eaff, #ff2e88)',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      }}
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.15, 0.25, 0.15],
      }}
      transition={{
        duration: 15,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
  </div>
)

const CenteredJarvisLogo = () => (
  <motion.div
    className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none z-0"
    animate={{
      scale: [1, 1.05, 1],
      rotate: [0, 360],
    }}
    transition={{
      scale: {
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      },
      rotate: {
        duration: 20,
        repeat: Infinity,
        ease: 'linear',
      },
    }}
  >
    <svg
      width="200"
      height="200"
      viewBox="0 0 100 100"
      className="drop-shadow-2xl"
    >
      <defs>
        <linearGradient id="centerLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ff2e88">
            <animate attributeName="stop-color" values="#ff2e88;#7b2ff7;#00eaff;#ff2e88" dur="5s" repeatCount="indefinite" />
          </stop>
          <stop offset="50%" stopColor="#7b2ff7">
            <animate attributeName="stop-color" values="#7b2ff7;#00eaff;#ff2e88;#7b2ff7" dur="5s" repeatCount="indefinite" />
          </stop>
          <stop offset="100%" stopColor="#00eaff">
            <animate attributeName="stop-color" values="#00eaff;#ff2e88;#7b2ff7;#00eaff" dur="5s" repeatCount="indefinite" />
          </stop>
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <polygon
        points="50,5 90,27.5 90,72.5 50,95 10,72.5 10,27.5"
        fill="none"
        stroke="url(#centerLogoGrad)"
        strokeWidth="4"
        filter="url(#glow)"
        style={{
          filter: 'drop-shadow(0 0 20px rgba(123,47,247,0.8)) drop-shadow(0 0 40px rgba(0,234,255,0.6))',
        }}
      />
      <text
        x="50"
        y="62"
        textAnchor="middle"
        fontFamily="monospace"
        fontSize="28"
        fontWeight="bold"
        fill="url(#centerLogoGrad)"
        filter="url(#glow)"
        style={{
          filter: 'drop-shadow(0 0 10px rgba(255,46,136,0.8))',
        }}
      >
        J
      </text>
      <animateTransform
        attributeName="transform"
        type="rotate"
        from="0 50 50"
        to="360 50 50"
        dur="20s"
        repeatCount="indefinite"
      />
    </svg>
  </motion.div>
)

const StatusBar = () => {
  const { metrics, wsChatConnected, wsMetricsConnected } = useJarvisStore()

  const overallConnected = wsChatConnected && wsMetricsConnected

  return (
    <header className="h-14 flex-shrink-0 flex items-center justify-between px-6 glass border-b border-jarvis-border">
      <div className="flex items-center gap-8">
        <div className="flex items-center gap-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
          >
            <Cpu size={16} className="text-jarvis-cyan neon-text" />
          </motion.div>
          <span className="text-xs font-mono text-jarvis-text">CPU {metrics.cpu_percent.toFixed(0)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-jarvis-pink neon-text" />
          <span className="text-xs font-mono text-jarvis-text">RAM {metrics.ram_percent.toFixed(0)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <Battery size={16} className="text-jarvis-purple neon-text" />
          <span className="text-xs font-mono text-jarvis-text">{formatShortUptime(metrics.uptime_seconds)}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono ${
          overallConnected 
            ? 'text-jarvis-cyan bg-jarvis-cyan/10 border border-jarvis-cyan/30' 
            : 'text-jarvis-pink bg-jarvis-pink/10 border border-jarvis-pink/30'
        }`}>
          {overallConnected ? (
            <>
              <Wifi size={12} />
              <span>Connected</span>
            </>
          ) : (
            <>
              <WifiOff size={12} />
              <span>Disconnected</span>
            </>
          )}
        </div>
        <LogoutButton />
      </div>
    </header>
  )
}

const LogoutButton = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  if (!user) return null

  return (
    <button
      onClick={handleLogout}
      className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono text-jarvis-pink bg-jarvis-pink/10 border border-jarvis-pink/30 hover:bg-jarvis-pink/20 transition-colors"
    >
      <LogOut size={12} />
      <span>Logout</span>
    </button>
  )
}

const PanelContainer = ({ children }) => (
  <div className="flex-1 min-h-0 relative p-6 overflow-hidden">
    <AnimatePresence mode="wait">
      <motion.div
        key={useJarvisStore.getState().activeTab}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.95 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="h-full"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  </div>
)

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, checkAuth } = useAuthStore()
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const verifyAuth = async () => {
      const isValid = await checkAuth()
      setIsChecking(false)
      if (!isValid) {
        window.location.href = '/login'
      }
    }
    verifyAuth()
  }, [checkAuth])

  if (isChecking) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-jarvis-bg">
        <div className="text-jarvis-text">Loading...</div>
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  const {
    activeTab, setMetrics, setStatus, setSettings, setMemoryStats,
    setWsChatConnected, setWsMetricsConnected, setReminders, setProfiles,
    setPlugins, setActiveProfileId,
  } = useJarvisStore()

  const [bootStatus, setBootStatus] = useState('initializing')

  useEffect(() => {
    let cancelled = false
    const boot = async () => {
      try {
        const [health, status, settings, memory] = await Promise.allSettled([
          jarvisApi.health().catch(() => null),
          jarvisApi.status().catch(() => null),
          jarvisApi.getSettings().catch(() => ({})),
          jarvisApi.getMemoryStats().catch(() => null),
        ])
        if (cancelled) return
        if (status?.status === 'fulfilled' && status.value) setStatus(status.value)
        if (settings?.status === 'fulfilled' && settings.value) setSettings(settings.value)
        if (memory?.status === 'fulfilled' && memory.value) setMemoryStats(memory.value)
        setBootStatus(health?.status === 'fulfilled' ? 'ready' : 'degraded')
      } catch (e) {
        setBootStatus('degraded')
      }
    }
    boot()

    jarvisApi.listReminders()
      .then((d) => setReminders(Array.isArray(d?.reminders) ? d.reminders : []))
      .catch(() => {})

    jarvisApi.listProfiles()
      .then((d) => {
        setProfiles(Array.isArray(d?.profiles) ? d.profiles : [])
        if (d?.active_user_id) setActiveProfileId(d.active_user_id)
      })
      .catch(() => {})

    jarvisApi.listPlugins()
      .then((d) => setPlugins(Array.isArray(d) ? d : []))
      .catch(() => {})

    return () => { cancelled = true }
  }, [setStatus, setSettings, setMemoryStats, setReminders, setProfiles, setActiveProfileId, setPlugins])

  useEffect(() => {
    metricsWS.onConnect(() => setWsMetricsConnected(true))
    metricsWS.onDisconnect(() => setWsMetricsConnected(false))
    const unsub = metricsWS.on('message', (data) => {
      if (typeof data === 'object' && data !== null) {
        setMetrics(data)
      }
    })
    metricsWS.connect().catch(() => {})

    chatWS.onConnect(() => setWsChatConnected(true))
    chatWS.onDisconnect(() => setWsChatConnected(false))
    chatWS.connect().catch(() => {})

    const statusInterval = setInterval(() => {
      jarvisApi.status().then((d) => setStatus(d)).catch(() => {})
    }, 15000)

    return () => {
      clearInterval(statusInterval)
      unsub()
      metricsWS.disconnect()
      chatWS.disconnect()
    }
  }, [setMetrics, setStatus, setWsChatConnected, setWsMetricsConnected])

  const renderTab = () => {
    switch (activeTab) {
      case 'chat': return <ChatPanel />
      case 'dashboard': return <SystemDashboard />
      case 'skills': return <SkillsPanel />
      case 'reminders': return <RemindersPanel />
      case 'profiles': return <ProfilesPanel />
      case 'memory': return <MemoryPanel />
      case 'settings': return <SettingsPanel />
      default: return <ChatPanel />
    }
  }

  return (
    <Router>
      <div className="h-screen w-screen flex overflow-hidden font-sans text-jarvis-text antialiased bg-jarvis-bg">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/enroll" element={<BiometricEnroll />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <MainApp
                  activeTab={activeTab}
                  bootStatus={bootStatus}
                  renderTab={renderTab}
                />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </Router>
  )
}

const MainApp = ({ activeTab, bootStatus, renderTab }) => (
  <>
    <AnimatedOrbs />
    <CenteredJarvisLogo />
    <Sidebar />
    <div className="flex-1 flex flex-col min-w-0 h-full relative z-10">
      <StatusBar />
      <PanelContainer>
        {renderTab()}
      </PanelContainer>
    </div>
  </>
)

export default App
