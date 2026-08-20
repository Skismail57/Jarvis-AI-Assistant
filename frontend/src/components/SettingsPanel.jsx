import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Settings as SettingsIcon, User, Mic, Eye, Database, KeyRound,
  Volume2, Languages, Brain, Save, EyeOff, RefreshCw, Trash2
} from 'lucide-react'
import useJarvisStore from '../store/useJarvisStore'
import { jarvisApi } from '../api/client'

const SectionCard = ({ icon: Icon, title, gradientClass, children }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass card-hover p-5 mb-4"
  >
    <div className="flex items-center gap-3 mb-5 pb-3 border-b border-jarvis-border/40">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center`}
        style={{
          background: 'linear-gradient(135deg, rgba(255,46,136,0.15), rgba(123,47,247,0.15))',
          border: '1px solid rgba(123,47,247,0.25)',
        }}
      >
        <Icon size={18} className={gradientClass} />
      </div>
      <h3 className="text-sm font-bold tracking-wide uppercase text-white/80">{title}</h3>
    </div>
    {children}
  </motion.div>
)

const Label = ({ children, hint }) => (
  <label className="block mb-2">
    <div className="text-xs font-semibold text-white/70 mb-1 tracking-wide uppercase tracking-wider">{children}</div>
    {hint && <div className="text-[10px] text-white/35 font-mono">{hint}</div>}
  </label>
)

const FieldRow = ({ label, hint, children }) => (
  <div className="mb-4 last:mb-0">
    <Label hint={hint}>{label}</Label>
    {children}
  </div>
)

const Switch = ({ checked, onChange, label, description }) => (
  <div className="flex items-start justify-between py-2">
    <div className="pr-4">
      <div className="text-sm font-medium text-white/90">{label}</div>
      {description && <div className="text-xs text-white/40 mt-0.5">{description}</div>}
    </div>
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      data-checked={checked}
      onClick={() => onChange(!checked)}
      className={`switch flex-shrink-0 mt-0.5 ${checked ? '' : ''}`}
    >
      <span className="switch-handle" />
    </button>
  </div>
)

const Slider = ({ value, onChange, min, max, step = 1, suffix = '' }) => (
  <div>
    <div className="flex items-center justify-between mb-2">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="slider-track flex-1 mr-4"
      />
      <div className="font-mono text-sm neon-text-purple flex-shrink-0 w-16 text-right">
        {typeof value === 'number' ? (step < 1 ? value.toFixed(2) : value.toFixed(0)) : value}{suffix}
      </div>
    </div>
  </div>
)

const SecretInput = ({ value, onChange, placeholder }) => {
  const [shown, setShown] = useState(false)
  return (
    <div className="relative">
      <input
        type={shown ? 'text' : 'password'}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="input-glass pr-12 font-mono text-xs"
      />
      <button
        type="button"
        onClick={() => setShown(!shown)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors"
      >
        {shown ? <EyeOff size={16} /> : <KeyRound size={16} />}
      </button>
    </div>
  )
}

const SettingsPanel = () => {
  const { settings, setSettings, memoryStats } = useJarvisStore()
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)
  const [confirmClear, setConfirmClear] = useState(null)

  const [local, setLocal] = useState({
    assistant_name: 'Jarvis',
    wake_word: 'jarvis',
    jarvis_language: 'en-US',
    confidence_threshold: 0.2,
    jarvis_wake_sensitivity: 0.65,
    openai_api_key: '',
    gemini_api_key: '',
    anthropic_api_key: '',
    porcupine_access_key: '',
    jarvis_tts_engine: 'pyttsx3',
    jarvis_stt_engine: 'sr',
    default_tts_voice: 'en-US-ChristopherNeural',
    default_tts_rate: 200,
    default_tts_volume: 1.0,
    enable_agent: true,
    enable_vector_memory: true,
    enable_face_recognition: false,
    vector_memory_top_k: 5,
    vector_memory_min_score: 0.35,
    face_recognition_tolerance: 0.6,
  })

  useEffect(() => {
    jarvisApi.getSettings().then((data) => {
      setSettings(data)
      setLocal((prev) => ({ ...prev, ...data }))
    }).catch(() => {})
  }, [setSettings])

  const updateLocal = (k, v) => setLocal((prev) => ({ ...prev, [k]: v }))

  const showToast = (msg, ok = true) => {
    setToast({ msg, ok })
    setTimeout(() => setToast(null), 3000)
  }

  const saveSection = async (keys) => {
    const payload = {}
    for (const k of keys) {
      if (local[k] !== undefined) payload[k] = local[k]
    }
    setSaving(true)
    try {
      const res = await jarvisApi.updateSettings(payload)
      showToast(`Saved ${keys.length} field(s). ${res.reload_required ? 'Restart server to apply.' : ''}`)
      setSettings((s) => ({ ...s, ...payload }))
    } catch (err) {
      showToast(`Save failed: ${err?.detail || String(err)}`, false)
    } finally {
      setSaving(false)
    }
  }

  const clearMemory = async (kind) => {
    try {
      const res = await jarvisApi.clearMemory(kind)
      showToast(`Cleared: ${res.cleared.join(', ') || 'none'}`)
      setConfirmClear(null)
    } catch (err) {
      showToast(String(err), false)
    }
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <div className="flex items-center justify-between mb-5 sticky top-0 z-10 py-2 backdrop-blur-md -mx-2 px-2">
        <div>
          <h2 className="text-2xl font-bold">
            <span className="neon-text">Configuration Center</span>
          </h2>
          <p className="text-xs text-white/40 mt-1 font-mono">
            Configure models, keys, features, memory · PUT /api/settings
          </p>
        </div>
        {toast && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`px-4 py-2 rounded-xl text-sm font-medium ${
              toast.ok
                ? 'bg-emerald-500/15 border border-emerald-400/30 text-emerald-300'
                : 'bg-rose-500/15 border border-rose-400/30 text-rose-300'
            }`}
          >
            {toast.msg}
          </motion.div>
        )}
      </div>

      <SectionCard icon={User} title="General" gradientClass="neon-text-pink">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FieldRow label="Assistant Name">
            <input
              className="input-glass"
              value={local.assistant_name}
              onChange={(e) => updateLocal('assistant_name', e.target.value)}
            />
          </FieldRow>
          <FieldRow label="Wake Word" hint="Phrase that activates voice input">
            <input
              className="input-glass"
              value={local.wake_word}
              onChange={(e) => updateLocal('wake_word', e.target.value)}
            />
          </FieldRow>
          <FieldRow label="Language">
            <select
              className="select-glass"
              value={local.jarvis_language}
              onChange={(e) => updateLocal('jarvis_language', e.target.value)}
            >
              {['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR', 'ru-RU', 'ar-SA', 'zh-CN', 'ja-JP', 'hi-IN'].map((l) => (
                <option key={l} value={l} className="bg-[#0a0a12]">{l}</option>
              ))}
            </select>
          </FieldRow>
          <FieldRow label="Confidence Threshold" hint="Minimum intent confidence to act (0–1)">
            <Slider value={local.confidence_threshold} onChange={(v) => updateLocal('confidence_threshold', v)} min={0} max={1} step={0.01} />
          </FieldRow>
          <FieldRow label="Wake Sensitivity" hint="Porcupine / engine sensitivity">
            <Slider value={local.jarvis_wake_sensitivity} onChange={(v) => updateLocal('jarvis_wake_sensitivity', v)} min={0} max={1} step={0.01} />
          </FieldRow>
        </div>
        <div className="mt-5 flex justify-end">
          <button onClick={() => saveSection(['assistant_name', 'wake_word', 'jarvis_language', 'confidence_threshold', 'jarvis_wake_sensitivity'])} disabled={saving} className="jarvis-btn-sm flex items-center gap-2">
            <Save size={14} />{saving ? 'Saving...' : 'Save General'}
          </button>
        </div>
      </SectionCard>

      <SectionCard icon={KeyRound} title="API Keys" gradientClass="neon-text-purple">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <FieldRow label="OpenAI API Key" hint="gpt-* models, embeddings, etc.">
            <SecretInput value={local.openai_api_key} onChange={(v) => updateLocal('openai_api_key', v)} placeholder="sk-... or leave blank to keep existing" />
          </FieldRow>
          <FieldRow label="Gemini API Key" hint="Google Gemini models">
            <SecretInput value={local.gemini_api_key} onChange={(v) => updateLocal('gemini_api_key', v)} placeholder="AIza..." />
          </FieldRow>
          <FieldRow label="Anthropic API Key" hint="Claude models">
            <SecretInput value={local.anthropic_api_key} onChange={(v) => updateLocal('anthropic_api_key', v)} placeholder="sk-ant-..." />
          </FieldRow>
          <FieldRow label="Porcupine Access Key" hint="Wake word engine access key">
            <SecretInput value={local.porcupine_access_key} onChange={(v) => updateLocal('porcupine_access_key', v)} placeholder="..." />
          </FieldRow>
        </div>
        <div className="mt-5 flex justify-end">
          <button onClick={() => saveSection(['openai_api_key', 'gemini_api_key', 'anthropic_api_key', 'porcupine_access_key'])} disabled={saving} className="jarvis-btn-sm flex items-center gap-2">
            <Save size={14} />{saving ? 'Saving Keys...' : 'Save API Keys'}
          </button>
        </div>
      </SectionCard>

      <SectionCard icon={Volume2} title="Speech & Audio" gradientClass="neon-text-cyan">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FieldRow label="TTS Engine">
            <select className="select-glass" value={local.jarvis_tts_engine} onChange={(e) => updateLocal('jarvis_tts_engine', e.target.value)}>
              <option value="pyttsx3" className="bg-[#0a0a12]">pyttsx3 (offline SAPI5)</option>
              <option value="gtts" className="bg-[#0a0a12]">gtts (Google Translate)</option>
              <option value="edge-tts" className="bg-[#0a0a12]">edge-tts (Microsoft Edge)</option>
            </select>
          </FieldRow>
          <FieldRow label="STT Engine">
            <select className="select-glass" value={local.jarvis_stt_engine} onChange={(e) => updateLocal('jarvis_stt_engine', e.target.value)}>
              <option value="sr" className="bg-[#0a0a12]">SpeechRecognition (default)</option>
              <option value="whisper" className="bg-[#0a0a12]">Whisper (OpenAI)</option>
            </select>
          </FieldRow>
          <FieldRow label="Default TTS Voice">
            <input className="input-glass font-mono text-xs" value={local.default_tts_voice} onChange={(e) => updateLocal('default_tts_voice', e.target.value)} />
          </FieldRow>
          <FieldRow label="Face Tolerance" hint="Face recognition tolerance 0.3–0.9">
            <Slider value={local.face_recognition_tolerance} onChange={(v) => updateLocal('face_recognition_tolerance', v)} min={0.3} max={0.9} step={0.01} />
          </FieldRow>
          <FieldRow label="TTS Rate" hint="Words per minute-ish factor (50–400)">
            <Slider value={local.default_tts_rate} onChange={(v) => updateLocal('default_tts_rate', v)} min={50} max={400} />
          </FieldRow>
          <FieldRow label="TTS Volume" hint="Output volume (0.0–1.0)">
            <Slider value={local.default_tts_volume} onChange={(v) => updateLocal('default_tts_volume', v)} min={0} max={1} step={0.01} />
          </FieldRow>
        </div>
        <div className="mt-5 flex justify-end">
          <button onClick={() => saveSection(['jarvis_tts_engine', 'jarvis_stt_engine', 'default_tts_voice', 'default_tts_rate', 'default_tts_volume', 'face_recognition_tolerance'])} disabled={saving} className="jarvis-btn-sm flex items-center gap-2">
            <Save size={14} />Save Speech
          </button>
        </div>
      </SectionCard>

      <SectionCard icon={Brain} title="Features & Agent" gradientClass="neon-text-purple">
        <div className="divide-y divide-jarvis-border/40">
          <Switch
            label="Enable Agent Thinking"
            description="Allow the agent to chain tools & reason multi-step"
            checked={!!local.enable_agent}
            onChange={(v) => updateLocal('enable_agent', v)}
          />
          <Switch
            label="Enable Vector Memory"
            description="Long-term memory backed by ChromaDB embeddings"
            checked={!!local.enable_vector_memory}
            onChange={(v) => updateLocal('enable_vector_memory', v)}
          />
          <Switch
            label="Enable Face Recognition"
            description="Identify users from camera (requires face_recognition lib)"
            checked={!!local.enable_face_recognition}
            onChange={(v) => updateLocal('enable_face_recognition', v)}
          />
        </div>
        <div className="mt-5 flex justify-end">
          <button onClick={() => saveSection(['enable_agent', 'enable_vector_memory', 'enable_face_recognition'])} disabled={saving} className="jarvis-btn-sm flex items-center gap-2">
            <Save size={14} />Save Features
          </button>
        </div>
      </SectionCard>

      <SectionCard icon={Database} title="Memory Tuning" gradientClass="neon-text-cyan">
        <div className="mb-5 space-y-5">
          <FieldRow label={`Vector Memory Top-K`} hint={`Currently ${memoryStats.top_k}. Max retrieved contexts.`}>
            <Slider value={local.vector_memory_top_k} onChange={(v) => updateLocal('vector_memory_top_k', v)} min={1} max={50} />
          </FieldRow>
          <FieldRow label={`Vector Memory Min Score`} hint={`Currently ${memoryStats.min_score}. 0 = allow everything, 1 = exact only.`}>
            <Slider value={local.vector_memory_min_score} onChange={(v) => updateLocal('vector_memory_min_score', v)} min={0} max={1} step={0.01} />
          </FieldRow>
        </div>
        <div className="mt-5 flex justify-end gap-3">
          <button onClick={() => saveSection(['vector_memory_top_k', 'vector_memory_min_score'])} disabled={saving} className="jarvis-btn-sm flex items-center gap-2">
            <Save size={14} />Save Tuning
          </button>
        </div>

        <div className="mt-8 border-t border-jarvis-border/40 pt-5">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-white/80">Danger Zone</h4>
            <span className="badge-danger">irreversible</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <button
              onClick={() => setConfirmClear('short')}
              className="p-3 rounded-xl text-sm flex items-center justify-center gap-2 hover:bg-rose-500/10 transition-colors border border-rose-500/20 text-rose-300"
            >
              <RefreshCw size={15} />
              Clear Short Term
            </button>
            <button
              onClick={() => setConfirmClear('long')}
              className="p-3 rounded-xl text-sm flex items-center justify-center gap-2 hover:bg-rose-500/10 transition-colors border border-rose-500/20 text-rose-300"
            >
              <Database size={15} />
              Clear Long Term
            </button>
            <button
              onClick={() => setConfirmClear('all')}
              className="p-3 rounded-xl text-sm flex items-center justify-center gap-2 hover:bg-rose-500/10 transition-colors border border-rose-500/40 text-rose-200 font-semibold"
              style={{ background: 'linear-gradient(135deg, rgba(239,68,68,0.08), rgba(239,68,68,0.02))' }}
            >
              <Trash2 size={15} />
              Factory Reset Memory
            </button>
          </div>
          {confirmClear && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-4 glass p-4 border-rose-500/30"
              style={{ borderColor: 'rgba(239,68,68,0.35)' }}
            >
              <p className="text-sm text-rose-200 mb-3">
                <strong>Confirm:</strong> Clear <span className="font-mono uppercase">{confirmClear}</span> memory? This cannot be undone.
              </p>
              <div className="flex justify-end gap-2">
                <button onClick={() => setConfirmClear(null)} className="px-4 py-2 text-sm rounded-xl border border-white/10 text-white/70 hover:bg-white/5">Cancel</button>
                <button onClick={() => clearMemory(confirmClear)} className="px-4 py-2 text-sm rounded-xl text-white font-semibold"
                  style={{ background: 'linear-gradient(135deg,#ef4444,#f43f5e)', boxShadow: '0 0 15px rgba(239,68,68,0.4)' }}>
                  Yes, Clear {confirmClear}
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </SectionCard>
    </div>
  )
}

export default SettingsPanel
