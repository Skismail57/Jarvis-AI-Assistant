import React from 'react'
import { motion } from 'framer-motion'
import {
  MessageSquare, LayoutDashboard, Zap, Bell, Users,
  Database, Settings, Hexagon
} from 'lucide-react'
import useJarvisStore from '../store/useJarvisStore'

const navItems = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'skills', label: 'Skills', icon: Zap },
  { id: 'reminders', label: 'Reminders', icon: Bell },
  { id: 'profiles', label: 'Profiles', icon: Users },
  { id: 'memory', label: 'Memory', icon: Database },
  { id: 'settings', label: 'Settings', icon: Settings },
]

const Sidebar = () => {
  const { activeTab, setActiveTab, wsChatConnected, wsMetricsConnected } = useJarvisStore()

  const connectionStatus = wsChatConnected && wsMetricsConnected
    ? 'connected'
    : wsChatConnected || wsMetricsConnected
      ? 'partial'
      : 'disconnected'

  return (
    <aside className="h-screen w-56 flex-shrink-0 flex flex-col glass border-r border-jarvis-border">
      <div className="p-4 border-b border-jarvis-border">
        <motion.div
          className="flex items-center gap-3"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          >
            <Hexagon size={24} className="text-jarvis-cyan neon-text" />
          </motion.div>
          <div>
            <h1 className="text-lg font-bold gradient-text">JARVIS</h1>
            <p className="text-[10px] text-jarvis-textDim uppercase tracking-wider">v2.0</p>
          </div>
        </motion.div>
      </div>

      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navItems.map(({ id, label, icon: Icon }, index) => {
          const isActive = activeTab === id
          return (
            <motion.button
              key={id}
              onClick={() => setActiveTab(id)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all relative overflow-hidden ${
                isActive
                  ? 'text-jarvis-cyan bg-jarvis-gradient-soft border border-jarvis-cyan/30 shadow-neon-cyan'
                  : 'text-jarvis-textDim hover:text-jarvis-text hover:bg-jarvis-panel/50'
              }`}
            >
              {isActive && (
                <motion.div
                  className="absolute inset-0 bg-jarvis-gradient opacity-10"
                  layoutId="activeTab"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <Icon size={16} className={isActive ? 'neon-text' : ''} />
              <span className="relative z-10">{label}</span>
            </motion.button>
          )
        })}
      </nav>

      <div className="p-3 border-t border-jarvis-border">
        <div className="flex items-center justify-between text-xs">
          <motion.span
            className={`flex items-center gap-1.5 ${
              connectionStatus === 'connected' ? 'text-jarvis-cyan' : 'text-jarvis-pink'
            }`}
            animate={connectionStatus === 'connected' ? { opacity: [0.5, 1, 0.5] } : {}}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <span className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-jarvis-cyan shadow-neon-cyan' : 'bg-jarvis-pink shadow-neon-pink'
            }`} />
            {connectionStatus}
          </motion.span>
          <span className="text-jarvis-textDim font-mono">build 2048</span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
