import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Cpu, HardDrive, Activity, Wifi, Clock,
  Layers, CheckCircle2, XCircle, Database, Bot, Plug
} from 'lucide-react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip,
  RadialBarChart, RadialBar, Cell
} from 'recharts'
import useJarvisStore from '../store/useJarvisStore'

const formatUptime = (s) => {
  const sec = Math.max(0, Math.floor(s))
  const d = Math.floor(sec / 86400)
  const h = Math.floor((sec % 86400) / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const secRem = sec % 60
  return `${d}d ${h}h ${m}m ${secRem}s`
}

const MetricCard = ({
  icon: Icon, label, value, subValue, percent = 0, unit = '%',
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass p-4 rounded-2xl border border-jarvis-border"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <Icon size={16} className="text-jarvis-cyan neon-text" />
            </motion.div>
            <span className="text-xs uppercase tracking-wider text-jarvis-textDim font-semibold">
              {label}
            </span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold gradient-text">
              {value}
            </span>
            <span className="text-sm text-jarvis-textDim">{unit}</span>
          </div>
          {subValue && (
            <p className="text-xs text-jarvis-textDim mt-1 font-mono">{subValue}</p>
          )}
        </div>
        <div className="w-16 h-16">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              innerRadius="70%"
              outerRadius="100%"
              barSize={6}
              data={[{ value: Math.min(100, percent || 0) }]}
              startAngle={90}
              endAngle={-270}
            >
              <RadialBar
                background={{ fill: 'rgba(0,234,255,0.1)' }}
                dataKey="value"
                fill="url(#jarvisGradient)"
              />
              <defs>
                <linearGradient id="jarvisGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#ff2e88" />
                  <stop offset="50%" stopColor="#7b2ff7" />
                  <stop offset="100%" stopColor="#00eaff" />
                </linearGradient>
              </defs>
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  )
}

const StatusRow = ({ label, value, icon: Icon, ok }) => (
  <div className="flex items-center justify-between py-2 border-b border-jarvis-border last:border-0">
    <div className="flex items-center gap-3">
      <Icon size={16} className="text-jarvis-textDim" />
      <span className="text-sm text-jarvis-text">{label}</span>
    </div>
    <div className="flex items-center gap-2">
      {typeof ok === 'boolean' && (
        ok ? <CheckCircle2 size={15} className="text-jarvis-cyan neon-text" /> : <XCircle size={15} className="text-jarvis-pink neon-text" />
      )}
      <span className={`text-sm font-mono ${typeof ok === 'boolean' ? (ok ? 'text-jarvis-cyan' : 'text-jarvis-pink') : 'text-jarvis-cyan neon-text'}`}>
        {value}
      </span>
    </div>
  </div>
)

const SystemDashboard = () => {
  const { metrics, metricsHistory, status } = useJarvisStore()

  const cpuUnit = '%'
  const cpuVal = metrics.cpu_percent.toFixed(1)
  const cpuSub = [
    metrics.cpu_freq_mhz ? `${(metrics.cpu_freq_mhz / 1000).toFixed(2)} GHz` : null,
    metrics.load_avg?.length ? `LA ${metrics.load_avg.map(v => v.toFixed(1)).join(' / ')}` : null,
  ].filter(Boolean).join('  ·  ')

  const ramPercent = metrics.ram_total_gb ? ((metrics.ram_used_gb / metrics.ram_total_gb) * 100) : 0
  const netUp = metrics.net_up_mbps.toFixed(2)
  const netDown = metrics.net_down_mbps.toFixed(2)
  const netSparkUp = metricsHistory.net_up.slice(-30)
  const netSparkDown = metricsHistory.net_down.slice(-30)

  const apiKeys = status.api_keys_configured || {}
  const features = status.features_enabled || {}

  return (
    <div className="h-full flex flex-col overflow-y-auto pr-2">
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <h2 className="text-lg font-bold gradient-text">System Dashboard</h2>
          <p className="text-xs text-jarvis-textDim mt-1 font-mono">
            Real-time telemetry · WS /ws/metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-jarvis-cyan flex items-center gap-1 neon-text">
            <span className="w-1.5 h-1.5 rounded-full bg-jarvis-cyan animate-pulse shadow-neon-cyan" />
            Live
          </span>
          <span className="text-xs font-mono text-jarvis-textDim flex items-center gap-1">
            <Clock size={10} />
            {formatUptime(metrics.uptime_seconds)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mb-4 flex-shrink-0">
        <MetricCard
          icon={Cpu}
          label="CPU"
          value={cpuVal}
          subValue={cpuSub}
          percent={metrics.cpu_percent}
          unit={cpuUnit}
        />
        <MetricCard
          icon={Activity}
          label="RAM"
          value={metrics.ram_used_gb.toFixed(1)}
          subValue={`${metrics.ram_total_gb.toFixed(1)} GB total`}
          percent={ramPercent}
          unit="GB"
        />
        <MetricCard
          icon={HardDrive}
          label="Disk"
          value={metrics.disk_used_gb.toFixed(0)}
          subValue={`${metrics.disk_total_gb.toFixed(0)} GB total`}
          percent={metrics.disk_percent}
          unit="GB"
        />
        <MetricCard
          icon={Wifi}
          label="Network"
          value={netDown}
          subValue={`↑ ${netUp} Mbps`}
          percent={0}
          unit="Mbps"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass p-4 rounded-2xl border border-jarvis-border"
        >
          <h3 className="text-sm font-semibold text-jarvis-text flex items-center gap-2 mb-3">
            <Layers size={16} className="text-jarvis-cyan neon-text" /> Core Telemetry
          </h3>
          <StatusRow
            label="Process Count"
            value={String(metrics.process_count)}
            icon={Layers}
          />
          <StatusRow
            label="System Uptime"
            value={formatUptime(metrics.uptime_seconds)}
            icon={Clock}
          />
          <StatusRow
            label="Load Average (1/5/15)"
            value={metrics.load_avg.map(v => v.toFixed(2)).join(' / ')}
            icon={Activity}
          />
          <StatusRow
            label="RAM Usage %"
            value={`${metrics.ram_percent.toFixed(1)}%`}
            icon={Database}
          />
          <StatusRow
            label="Disk Usage %"
            value={`${metrics.disk_percent.toFixed(1)}%`}
            icon={HardDrive}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass p-4 rounded-2xl border border-jarvis-border"
        >
          <h3 className="text-sm font-semibold text-jarvis-text flex items-center gap-2 mb-3">
            <Bot size={16} className="text-jarvis-pink neon-text" /> Assistant Status
          </h3>
          <StatusRow label="Assistant Name" value={status.name} icon={Bot} />
          <StatusRow label="Wake Word" value={status.wake_word} icon={Activity} />
          <StatusRow label="Language" value={status.language} icon={Layers} />
          <StatusRow label="LLM Model" value={status.llm_model} icon={Database} />
          <StatusRow label="Mode" value={status.mode} icon={Clock} />
          <StatusRow label="TTS / STT" value={`${status.tts_engine} / ${status.stt_engine}`} icon={Wifi} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass p-4 rounded-2xl border border-jarvis-border"
        >
          <h3 className="text-sm font-semibold text-jarvis-text flex items-center gap-2 mb-3">
            <Plug size={16} className="text-jarvis-purple neon-text" /> Integrations
          </h3>
          <div className="mb-3">
            <div className="text-[10px] uppercase tracking-wider text-jarvis-textDim font-mono mb-2">API Keys</div>
            <StatusRow label="OpenAI" value={apiKeys.openai ? 'Configured' : 'Missing'} icon={CheckCircle2} ok={!!apiKeys.openai} />
            <StatusRow label="Gemini" value={apiKeys.gemini ? 'Configured' : 'Missing'} icon={CheckCircle2} ok={!!apiKeys.gemini} />
            <StatusRow label="Anthropic" value={apiKeys.anthropic ? 'Configured' : 'Missing'} icon={CheckCircle2} ok={!!apiKeys.anthropic} />
            <StatusRow label="Porcupine" value={apiKeys.porcupine ? 'Configured' : 'Missing'} icon={CheckCircle2} ok={!!apiKeys.porcupine} />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-jarvis-textDim font-mono mb-2 mt-4">Features & Plugins</div>
            <StatusRow label={`Skills Available`} value={String(status.skills_available || 0)} icon={Bot} />
            <StatusRow label={`Plugins Loaded`} value={String(status.plugins_loaded || 0)} icon={Plug} />
            <StatusRow label="Agent Mode" value={features.agent ? 'Enabled' : 'Disabled'} icon={CheckCircle2} ok={!!features.agent} />
            <StatusRow label="Vector Memory" value={features.vector_memory ? 'Enabled' : 'Disabled'} icon={CheckCircle2} ok={!!features.vector_memory} />
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default SystemDashboard
