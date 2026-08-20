import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Zap, RefreshCw, BookOpen, MessageSquareText, BarChart3,
  Puzzle, Play, Pause, Volume2, Search, Calendar, Music,
  Camera, Globe, Clock, Trash2, Send, Calculator, Lock,
  Lightbulb, FileText, Settings2, Bot, Package
} from 'lucide-react'
import useJarvisStore from '../store/useJarvisStore'
import { jarvisApi } from '../api/client'

const SKILLS = [
  { name: 'Web Search', icon: Search, examples: ['Search for quantum computing', 'Find recipes for pasta'], intent: 'web_search', enabled: true },
  { name: 'Time & Date', icon: Clock, examples: ['What time is it in Tokyo?', 'When is next Monday?'], intent: 'time_date', enabled: true },
  { name: 'Weather', icon: Globe, examples: ['Weather in London', 'Forecast for tomorrow'], intent: 'weather', enabled: true },
  { name: 'Reminders', icon: Calendar, examples: ['Remind me in 30 min to stretch', 'Set reminder at 6pm'], intent: 'reminder', enabled: true },
  { name: 'TTS Speak', icon: Volume2, examples: ['Read this text', 'Say hello world'], intent: 'speak', enabled: true },
  { name: 'Calculator', icon: Calculator, examples: ['What is 15% of 240?', 'Calculate (256 * 14) + 7'], intent: 'calculator', enabled: true },
  { name: 'Media Player', icon: Music, examples: ['Play some music', 'Pause playback', 'Next song'], intent: 'media', enabled: false },
  { name: 'System Control', icon: Settings2, examples: ['Open browser', 'Shutdown PC in 1 hour', 'Volume up'], intent: 'system', enabled: true },
  { name: 'Screenshot / Vision', icon: Camera, examples: ['Take a screenshot', 'What is on my screen?'], intent: 'vision', enabled: false },
  { name: 'Email / Messaging', icon: Send, examples: ['Send email to John', 'Text mom hello'], intent: 'communicate', enabled: false },
  { name: 'Productivity', icon: FileText, examples: ['Create a note', 'List my todos', 'Add task buy milk'], intent: 'productivity', enabled: true },
  { name: 'Knowledge Q&A', icon: BookOpen, examples: ['Explain relativity', 'Who wrote 1984?'], intent: 'qa', enabled: true },
  { name: 'Smart Home', icon: Lightbulb, examples: ['Turn off bedroom lights', 'Set temp to 22°C'], intent: 'smarthome', enabled: false },
  { name: 'Face Recognition', icon: Lock, examples: ['Who is at the desk?', 'Add this face as Sarah'], intent: 'face', enabled: false },
  { name: 'Code Assistant', icon: Bot, examples: ['Write a Python bubble sort', 'Explain this JavaScript'], intent: 'code', enabled: true },
  { name: 'Translation', icon: Globe, examples: ['Translate hello to Japanese', 'How do I say thanks in French?'], intent: 'translate', enabled: true },
  { name: 'News / RSS', icon: FileText, examples: ['Top tech news today', 'Latest AI papers'], intent: 'news', enabled: false },
  { name: 'Timers', icon: Clock, examples: ['Set a pomodoro timer', 'Countdown 5 minutes'], intent: 'timer', enabled: true },
  { name: 'File Operations', icon: Package, examples: ['List files in Documents', 'Create folder projects'], intent: 'files', enabled: false },
  { name: 'Learning / Teaching', icon: BookOpen, examples: ['Teach me Spanish basics', 'Quiz me on Python'], intent: 'learn', enabled: true },
]

const SkillCard = ({ skill, onToggle }) => {
  const [on, setOn] = useState(skill.enabled)
  const Icon = skill.icon
  const toggle = () => {
    const next = !on
    setOn(next)
    if (onToggle) onToggle(skill, next)
  }
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass card-hover p-4 relative overflow-hidden group"
    >
      <div className={`absolute -top-16 -right-16 w-32 h-32 rounded-full blur-3xl opacity-15 pointer-events-none transition-opacity group-hover:opacity-30`}
        style={{
          background: on
            ? 'radial-gradient(circle, #ff2e88, transparent 70%)'
            : 'radial-gradient(circle, #64748b, transparent 70%)',
        }} />
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all`}
              style={{
                background: on
                  ? 'linear-gradient(135deg, rgba(255,46,136,0.25), rgba(123,47,247,0.25))'
                  : 'rgba(255,255,255,0.03)',
                border: `1px solid ${on ? 'rgba(123,47,247,0.4)' : 'rgba(255,255,255,0.08)'}`,
                boxShadow: on ? '0 0 15px rgba(123,47,247,0.2)' : 'none',
              }}
            >
              <Icon size={19} className={on ? 'neon-text' : 'text-white/40'} />
            </div>
            <div>
              <div className={`text-sm font-bold ${on ? 'text-white' : 'text-white/60'}`}>{skill.name}</div>
              <div className="text-[10px] font-mono text-white/30 uppercase tracking-wider">{skill.intent}</div>
            </div>
          </div>
          <button
            onClick={toggle}
            role="switch"
            aria-checked={on}
            data-checked={on}
            className={`switch ${on ? '' : ''}`}
          >
            <span className="switch-handle" />
          </button>
        </div>
        <div className="space-y-1.5">
          {skill.examples.map((ex, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-white/55">
              <span className="neon-text-cyan mt-0.5">›</span>
              <span className="leading-relaxed">{ex}</span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

const StatCard = ({ label, value, icon: Icon, color = '#7b2ff7', sub }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.96 }}
    animate={{ opacity: 1, scale: 1 }}
    className="glass card-hover p-4 flex items-center gap-4"
  >
    <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
      style={{
        background: `linear-gradient(135deg, ${color}33, ${color}11)`,
        border: `1px solid ${color}44`,
      }}
    >
      <Icon size={20} style={{ color }} />
    </div>
    <div className="min-w-0 flex-1">
      <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono mb-0.5">{label}</div>
      <div className="text-2xl font-extrabold" style={{ color }}>{value}</div>
      {sub && <div className="text-[11px] text-white/40 mt-0.5">{sub}</div>}
    </div>
  </motion.div>
)

const SkillsPanel = () => {
  const { plugins, setPlugins, memoryStats } = useJarvisStore()
  const [retraining, setRetraining] = useState(false)
  const [retrainResult, setRetrainResult] = useState(null)
  const [customCounts, setCustomCounts] = useState({ qa: 42, intents: 18, feedback: 137 })

  useEffect(() => {
    jarvisApi.listPlugins()
      .then((data) => setPlugins(Array.isArray(data) ? data : []))
      .catch(() => setPlugins([]))
  }, [setPlugins])

  const handleRetrain = async () => {
    setRetraining(true)
    setRetrainResult(null)
    try {
      const res = await jarvisApi.retrainClassifier()
      setRetrainResult(res)
    } catch (err) {
      setRetrainResult({ error: String(err) })
    } finally {
      setRetraining(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-2xl font-bold">
            <span className="neon-text-pink">Skills</span>
            <span className="text-white/40 mx-2">·</span>
            <span className="neon-text-purple">Learning</span>
          </h2>
          <p className="text-xs text-white/40 mt-1 font-mono">
            20+ built-in skills · Classifier retrain · Plugins · Teach your assistant
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="jarvis-btn-sm flex items-center gap-2"
          >
            {retraining ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
            {retraining ? 'Retraining...' : 'Retrain Classifier'}
          </button>
        </div>
      </div>

      {retrainResult && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className={`glass p-4 mb-5 border ${retrainResult.error ? 'border-rose-500/40' : 'border-emerald-400/40'}`}
          style={{ borderColor: retrainResult.error ? 'rgba(244,63,94,0.4)' : 'rgba(16,185,129,0.4)' }}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {retrainResult.error ? (
                <><Trash2 size={16} className="text-rose-400" /><span className="text-sm text-rose-200 font-medium">{retrainResult.error}</span></>
              ) : (
                <><Zap size={16} className="text-emerald-400" /><span className="text-sm text-emerald-200 font-medium">Classifier retrained · {retrainResult.classes?.length || 0} classes</span></>
              )}
            </div>
            <button onClick={() => setRetrainResult(null)} className="text-white/40 hover:text-white text-sm">×</button>
          </div>
          {retrainResult.classes && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {retrainResult.classes.map((c) => (
                <span key={c} className="badge-gradient text-[10px]">{c}</span>
              ))}
            </div>
          )}
        </motion.div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div className="xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-white/70 flex items-center gap-2">
              <Zap size={16} className="neon-text-pink" /> Available Skills
              <span className="badge-gradient ml-2">{SKILLS.length}</span>
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SKILLS.map((skill) => (
              <SkillCard key={skill.intent} skill={skill} />
            ))}
          </div>
        </div>

        <div className="space-y-5">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-white/70 flex items-center gap-2 mb-4">
              <BarChart3 size={16} className="neon-text-purple" /> Learning Dashboard
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Custom Q&A" value={customCounts.qa} icon={MessageSquareText} color="#ff2e88" sub="Taught answers" />
              <StatCard label="Intents" value={customCounts.intents} icon={Zap} color="#7b2ff7" sub="Custom patterns" />
              <StatCard label="Feedback" value={customCounts.feedback} icon={BarChart3} color="#00eaff" sub="Human labels" />
              <StatCard label="Vector Items" value={memoryStats.long_term_items || 0} icon={BookOpen} color="#34d399" sub={`Top-K ${memoryStats.top_k || 5}`} />
            </div>
          </div>

          <div className="glass p-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-white/70 flex items-center gap-2 mb-4">
              <Puzzle size={16} className="neon-text-cyan" /> Plugins
              <span className="badge-info ml-2">{plugins.length}</span>
            </h3>
            {plugins.length === 0 ? (
              <div className="text-sm text-white/40 py-8 text-center">
                <Package size={28} className="mx-auto mb-2 text-white/20" />
                No plugins detected. Place Python packages in <span className="font-mono text-white/60">/plugins</span>.
              </div>
            ) : (
              <div className="space-y-3">
                {plugins.map((p) => (
                  <motion.div
                    key={p.name}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-3 rounded-xl border border-jarvis-border/60 hover:border-jarvis-purple/40 transition-colors"
                    style={{ background: 'linear-gradient(135deg, rgba(123,47,247,0.05), rgba(0,234,255,0.03))' }}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{p.icon || '🧩'}</span>
                      <div>
                        <div className="text-sm font-semibold text-white">{p.name}</div>
                        <div className="text-[10px] text-white/40 font-mono uppercase">{p.intent_patterns?.length || 0} patterns</div>
                      </div>
                    </div>
                    {p.examples?.length > 0 && (
                      <div className="pl-9 space-y-1">
                        {p.examples.slice(0, 2).map((ex, i) => (
                          <div key={i} className="text-xs text-white/50">
                            <span className="neon-text-pink mr-1">›</span>{ex}
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          <div className="glass p-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-white/70 flex items-center gap-2 mb-4">
              <BookOpen size={16} className="neon-text-purple" /> Teaching Syntax
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="text-white/50 text-[10px] uppercase font-sans mb-1">Custom Q&A Pattern</div>
              <div className="code-block text-[11px] leading-relaxed">
                <span className="neon-text-pink">jarvis teach:</span>
                <span className="text-white"> {"{"}</span>
                <br />&nbsp;&nbsp;<span className="neon-text-cyan">question</span>: <span className="text-amber-200">"your question?"</span>,
                <br />&nbsp;&nbsp;<span className="neon-text-cyan">answer</span>: <span className="text-amber-200">"your answer"</span>
                <br />{`"}`}
              </div>
              <div className="text-white/50 text-[10px] uppercase font-sans mb-1 mt-4">Custom Intent</div>
              <div className="code-block text-[11px] leading-relaxed">
                <span className="neon-text-pink">learn intent</span> <span className="neon-text-purple">ORDER_PIZZA</span>
                <br /><span className="text-white/60">examples:</span>
                <br />- Order me a large pepperoni
                <br />- Can you get a pizza delivered?
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SkillsPanel
