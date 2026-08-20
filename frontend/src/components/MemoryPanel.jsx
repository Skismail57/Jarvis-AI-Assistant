import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Database, Clock, Trash2, HardDrive, Layers, Server,
  CheckCircle2, AlertTriangle, RefreshCw, Zap, ArrowRight
} from 'lucide-react'
import useJarvisStore from '../store/useJarvisStore'
import { jarvisApi } from '../api/client'

const BarVis = ({ total, max = 200, color = '#7b2ff7' }) => {
  const pct = Math.min(100, (total / max) * 100)
  const bars = 24
  const filled = Math.round((pct / 100) * bars)
  return (
    <div className="flex items-end gap-1 h-16">
      {Array.from({ length: bars }).map((_, i) => {
        const on = i < filled
        const h = 20 + (i % 5) * 15
        return (
          <div
            key={i}
            className="flex-1 rounded-t-sm transition-all duration-500"
            style={{
              height: on ? `${h}%` : '10%',
              background: on
                ? `linear-gradient(180deg, ${color}, ${color}66)`
                : 'rgba(255,255,255,0.05)',
              boxShadow: on ? `0 0 8px ${color}55` : 'none',
              opacity: on ? 1 : 0.6,
            }}
          />
        )
      })}
    </div>
  )
}

const StatPill = ({ label, value, icon: Icon, color }) => (
  <div className="flex items-center gap-3 p-3 rounded-xl"
    style={{ background: `${color}10`, border: `1px solid ${color}33` }}>
    <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: `${color}20` }}>
      <Icon size={16} style={{ color }} />
    </div>
    <div>
      <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono">{label}</div>
      <div className="text-lg font-extrabold" style={{ color }}>{value}</div>
    </div>
  </div>
)

const ContextSample = ({ messages }) => {
  if (!messages || messages.length === 0) {
    return (
      <div className="text-center py-6 text-sm text-white/40">
        <Zap size={20} className="mx-auto mb-2 text-white/20" />
        No conversation context yet.
      </div>
    )
  }
  const recent = messages.slice(-6)
  return (
    <div className="space-y-2">
      {recent.map((m, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
          className="p-2.5 rounded-xl text-xs"
          style={{
            background: m.role === 'user'
              ? 'linear-gradient(135deg, rgba(255,46,136,0.08), rgba(123,47,247,0.05))'
              : 'rgba(255,255,255,0.03)',
            border: `1px solid ${m.role === 'user' ? 'rgba(255,46,136,0.2)' : 'rgba(255,255,255,0.06)'}`,
          }}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-mono uppercase tracking-wider font-semibold ${m.role === 'user' ? 'neon-text-pink' : 'neon-text-cyan'}`}>
              {m.role}
            </span>
            <ArrowRight size={9} className="text-white/20" />
            <span className="text-[10px] font-mono text-white/30 truncate flex-1">
              {m.content.slice(0, 80)}{m.content.length > 80 ? '…' : ''}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  )
}

const MemoryPanel = () => {
  const { memoryStats, setMemoryStats, messages } = useJarvisStore()
  const [loading, setLoading] = useState(false)
  const [confirm, setConfirm] = useState(null)
  const [notice, setNotice] = useState(null)

  const refresh = async () => {
    setLoading(true)
    try {
      const data = await jarvisApi.getMemoryStats()
      setMemoryStats(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  const sizeMb = (memoryStats.long_term_size_bytes || 0) / (1024 * 1024)
  const vectorDb = memoryStats.vector_db || 'chromadb'

  const clearMem = async (kind) => {
    try {
      const res = await jarvisApi.clearMemory(kind)
      setNotice(`Cleared: ${(res.cleared || []).join(', ') || 'nothing'}`)
      setConfirm(null)
      setTimeout(refresh, 400)
      setTimeout(() => setNotice(null), 3500)
    } catch (e) {
      setNotice(`Error: ${String(e)}`)
      setTimeout(() => setNotice(null), 4000)
    }
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <div className="flex items-center justify-between mb-5 sticky top-0 z-10 py-2 backdrop-blur-md -mx-2 px-2">
        <div>
          <h2 className="text-2xl font-bold">
            <span className="neon-text-pink">Memory</span>
            <span className="text-white/40 mx-2">·</span>
            <span className="neon-text-cyan">Neural Storage</span>
          </h2>
          <p className="text-xs text-white/40 mt-1 font-mono">
            Short-term context window · Long-term vector DB (ChromaDB) · GET /api/memory
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={refresh} className="px-3 py-2 rounded-xl text-xs font-medium border border-jarvis-border hover:border-jarvis-purple/50 text-white/70 hover:text-white transition-all flex items-center gap-2">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <span className="badge-gradient flex items-center gap-1">
            <Server size={11} /> {vectorDb.toUpperCase()} Online
          </span>
        </div>
      </div>

      {notice && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass px-4 py-3 mb-4 border-emerald-400/30 flex items-center justify-between"
          style={{ borderColor: 'rgba(16,185,129,0.35)' }}
        >
          <div className="flex items-center gap-2 text-sm text-emerald-200">
            <CheckCircle2 size={15} />
            {notice}
          </div>
          <button onClick={() => setNotice(null)} className="text-white/40 hover:text-white text-lg leading-none">×</button>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass p-6 relative overflow-hidden"
        >
          <div className="absolute -top-20 -left-10 w-60 h-60 rounded-full blur-3xl opacity-15 pointer-events-none"
            style={{ background: 'radial-gradient(circle, #7b2ff7, transparent 70%)' }} />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white/70 flex items-center gap-2">
                <Clock size={16} className="neon-text-purple" /> Short-Term Memory
              </h3>
              <span className="badge-gradient">{memoryStats.short_term_turns || 0} turns</span>
            </div>

            <div className="mb-5">
              <BarVis total={memoryStats.short_term_turns || 0} max={200} color="#7b2ff7" />
              <div className="flex justify-between text-[10px] font-mono text-white/40 mt-2">
                <span>0 turns</span>
                <span>Context window · 200 turns max</span>
                <span>200 turns</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <StatPill label="Turns" value={memoryStats.short_term_turns || 0} icon={Layers} color="#7b2ff7" />
              <StatPill label="Messages" value={messages.length} icon={Database} color="#ff2e88" />
              <StatPill label="Engine" value="In-Memory" icon={Server} color="#00eaff" />
            </div>

            <div className="mt-5 p-4 rounded-xl" style={{ background: 'rgba(123,47,247,0.05)', border: '1px solid rgba(123,47,247,0.15)' }}>
              <h4 className="text-[11px] uppercase tracking-widest text-white/50 font-mono mb-3 flex items-center gap-1.5">
                <Zap size={11} /> Recent Conversation Context
              </h4>
              <ContextSample messages={messages} />
            </div>

            <div className="mt-5 flex items-center justify-between pt-4 border-t border-jarvis-border/40">
              <div className="text-xs text-white/50">
                <AlertTriangle size={12} className="inline mr-1.5 text-amber-300" />
                Clearing short-term resets the chat context window.
              </div>
              <button
                onClick={() => setConfirm('short')}
                className="px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 border border-rose-500/25 text-rose-300 hover:bg-rose-500/10 transition-colors"
              >
                <Trash2 size={13} /> Clear Short-Term
              </button>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass p-6 relative overflow-hidden"
        >
          <div className="absolute -top-20 -right-10 w-60 h-60 rounded-full blur-3xl opacity-15 pointer-events-none"
            style={{ background: 'radial-gradient(circle, #00eaff, transparent 70%)' }} />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white/70 flex items-center gap-2">
                <Database size={16} className="neon-text-cyan" /> Long-Term Vector Memory
              </h3>
              <span className="badge-info">{vectorDb}</span>
            </div>

            <div className="mb-5">
              <BarVis total={memoryStats.long_term_items || 0} max={1000} color="#00eaff" />
              <div className="flex justify-between text-[10px] font-mono text-white/40 mt-2">
                <span>0 entries</span>
                <span>Vector collection: {memoryStats.long_term_items || 0} items</span>
                <span>1,000</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-5">
              <StatPill label="Vector Items" value={memoryStats.long_term_items || 0} icon={Layers} color="#00eaff" />
              <StatPill label="Storage" value={`${sizeMb.toFixed(1)} MB`} icon={HardDrive} color="#34d399" />
              <StatPill label="Top-K Retrieval" value={memoryStats.top_k || 5} icon={Zap} color="#ff2e88" />
              <StatPill label="Min Score" value={(memoryStats.min_score || 0).toFixed(2)} icon={CheckCircle2} color="#7b2ff7" />
            </div>

            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="p-4 rounded-xl" style={{ background: 'rgba(0,234,255,0.05)', border: '1px solid rgba(0,234,255,0.2)' }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] uppercase tracking-widest text-white/40 font-mono">ChromaDB Status</span>
                  <CheckCircle2 size={13} className="text-emerald-400" />
                </div>
                <div className="text-sm font-bold text-cyan-200">Connected & Persistent</div>
                <div className="text-[11px] text-white/50 font-mono mt-0.5">Embedding: all-MiniLM-L6-v2</div>
              </div>
              <div className="p-4 rounded-xl" style={{ background: 'rgba(255,46,136,0.05)', border: '1px solid rgba(255,46,136,0.2)' }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] uppercase tracking-widest text-white/40 font-mono">Retrieval Config</span>
                  <Zap size={13} className="neon-text-pink" />
                </div>
                <div className="text-sm font-bold text-pink-200">
                  Top-{memoryStats.top_k || 5} · ≥ {(memoryStats.min_score || 0).toFixed(2)}
                </div>
                <div className="text-[11px] text-white/50 font-mono mt-0.5">Hybrid search ready</div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-jarvis-border/40 gap-3 flex-wrap">
              <div className="text-xs text-white/50 flex-1 min-w-[200px]">
                <AlertTriangle size={12} className="inline mr-1.5 text-amber-300" />
                Long-term memory retains learned facts permanently. Clear with caution.
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setConfirm('long')}
                  className="px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 border border-rose-500/25 text-rose-300 hover:bg-rose-500/10 transition-colors"
                >
                  <Trash2 size={13} /> Clear Long-Term
                </button>
                <button
                  onClick={() => setConfirm('all')}
                  className="px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 text-white"
                  style={{ background: 'linear-gradient(135deg,#ef4444,#f43f5e)', boxShadow: '0 0 15px rgba(239,68,68,0.4)' }}
                >
                  <Trash2 size={13} /> Wipe All Memory
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass p-5"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, rgba(255,46,136,0.2), rgba(123,47,247,0.15))', border: '1px solid rgba(123,47,247,0.3)' }}
            >
              <Layers size={18} className="neon-text" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Hybrid Memory Architecture</h3>
              <div className="text-[11px] text-white/40 font-mono">Dual-store retrieval</div>
            </div>
          </div>
          <ul className="text-xs text-white/60 space-y-2">
            <li className="flex items-start gap-2">
              <span className="neon-text-pink mt-0.5">›</span>
              <span><strong className="text-white/80">Episodic</strong> — last N turns in RAM for fast, coherent context.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="neon-text-cyan mt-0.5">›</span>
              <span><strong className="text-white/80">Semantic</strong> — ChromaDB embeddings, retrieved by similarity search.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="neon-text-purple mt-0.5">›</span>
              <span><strong className="text-white/80">Autonomous</strong> — agent writes new facts automatically after each turn.</span>
            </li>
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass p-5"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, rgba(0,234,255,0.2), rgba(123,47,247,0.1))', border: '1px solid rgba(0,234,255,0.3)' }}
            >
              <Zap size={18} className="neon-text-cyan" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Teaching the Assistant</h3>
              <div className="text-[11px] text-white/40 font-mono">Build long-term memory from chat</div>
            </div>
          </div>
          <div className="code-block text-[11px] space-y-1 leading-relaxed">
            <div><span className="neon-text-pink">jarvis remember:</span> <span className="text-amber-200">I am allergic to peanuts</span></div>
            <div><span className="neon-text-cyan">learn fact:</span> <span className="text-amber-200">Project deadline is March 15</span></div>
            <div><span className="neon-text-purple">teach qa:</span> <span className="text-white/70">Q: What's my wifi? A: Jarvis_5G</span></div>
            <div className="pt-1 mt-1 border-t border-white/5 text-[10px] text-white/40">
              …facts are embedded and stored in the vector store permanently.
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass p-5"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, rgba(123,47,247,0.2), rgba(16,185,129,0.15))', border: '1px solid rgba(16,185,129,0.3)' }}
            >
              <Server size={18} className="neon-text-purple" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Persistence Paths</h3>
              <div className="text-[11px] text-white/40 font-mono">Where JARVIS stores data</div>
            </div>
          </div>
          <ul className="text-xs font-mono space-y-2 text-white/60">
            <li className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="text-[10px] text-white/40 uppercase">Short-Term</div>
              <div className="neon-text-purple">RAM · TTL max-history</div>
            </li>
            <li className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="text-[10px] text-white/40 uppercase">Long-Term</div>
              <div className="neon-text-cyan">/data/chroma_db/</div>
            </li>
            <li className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="text-[10px] text-white/40 uppercase">Profiles / Reminders</div>
              <div className="neon-text-pink">/data/*.json</div>
            </li>
          </ul>
        </motion.div>
      </div>

      {confirm && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)' }}
          onClick={() => setConfirm(null)}
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            className="glass p-6 max-w-md w-full"
            style={{ borderColor: 'rgba(239,68,68,0.4)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: 'linear-gradient(135deg, rgba(239,68,68,0.25), rgba(244,63,94,0.1))', border: '1px solid rgba(239,68,68,0.4)' }}>
                <AlertTriangle size={22} className="text-rose-300" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-1">
                  Confirm: Clear {confirm.toUpperCase()} Memory
                </h3>
                <p className="text-sm text-white/60 leading-relaxed">
                  This action permanently deletes <strong className="text-rose-300">{confirm === 'all' ? 'ALL short-term AND long-term memory' : confirm + '-term memory'}</strong>.
                  This cannot be undone. JARVIS will lose access to the stored facts immediately.
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirm(null)} className="px-5 py-2.5 rounded-xl text-sm font-medium border border-white/10 text-white/70 hover:bg-white/5 transition-colors">
                Cancel
              </button>
              <button
                onClick={() => clearMem(confirm)}
                className="px-5 py-2.5 rounded-xl text-sm font-bold text-white"
                style={{ background: 'linear-gradient(135deg,#ef4444,#f43f5e)', boxShadow: '0 0 20px rgba(239,68,68,0.5)' }}
              >
                <Trash2 size={14} className="inline mr-2" />
                Permanently Delete
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  )
}

export default MemoryPanel
