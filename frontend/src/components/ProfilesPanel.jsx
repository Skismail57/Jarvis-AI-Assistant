import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users, Plus, Shield, ShieldCheck, ShieldAlert, User, Edit3,
  Languages, Volume2, CheckCircle2, XCircle, Lock, Power, Save
} from 'lucide-react'
import useJarvisStore from '../store/useJarvisStore'
import { jarvisApi } from '../api/client'

const ROLE_CONFIG = {
  admin: {
    label: 'Admin',
    icon: ShieldAlert,
    cls: 'text-rose-300',
    bg: 'linear-gradient(135deg, rgba(244,63,94,0.2), rgba(251,113,133,0.1))',
    border: 'rgba(244,63,94,0.4)',
    badge: 'badge-danger',
    desc: 'Full access: shutdown, delete, settings, API keys',
  },
  user: {
    label: 'User',
    icon: ShieldCheck,
    cls: 'neon-text-purple',
    bg: 'linear-gradient(135deg, rgba(123,47,247,0.2), rgba(168,85,247,0.1))',
    border: 'rgba(123,47,247,0.4)',
    badge: 'badge-gradient',
    desc: 'Standard chat, reminders, skills — no destructive actions',
  },
  guest: {
    label: 'Guest',
    icon: Shield,
    cls: 'text-slate-300',
    bg: 'linear-gradient(135deg, rgba(148,163,184,0.15), rgba(100,116,139,0.05))',
    border: 'rgba(148,163,184,0.25)',
    badge: 'bg-slate-500/20 border border-slate-500/30 text-slate-300 badge',
    desc: 'Read-only chat. No system modifications, no persistence.',
  },
}

const ProfileCard = ({ profile, active, onActivate, onEdit }) => {
  const role = ROLE_CONFIG[profile.role] || ROLE_CONFIG.user
  const RoleIcon = role.icon
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className={`glass card-hover p-5 relative overflow-hidden ${active ? 'glow-border' : ''}`}
    >
      <div className="absolute -top-16 -right-16 w-40 h-40 rounded-full blur-3xl opacity-15 pointer-events-none"
        style={{ background: profile.role === 'admin' ? '#f43f5e' : profile.role === 'user' ? '#7b2ff7' : '#64748b' }} />
      {active && (
        <div className="absolute top-4 right-4">
          <span className="badge-success flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Active
          </span>
        </div>
      )}
      <div className="relative z-10">
        <div className="flex items-start gap-4 mb-4">
          <div className="relative">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{ background: role.bg, border: `1px solid ${role.border}` }}
            >
              <User size={22} className={role.cls} />
            </div>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h4 className="text-lg font-bold text-white">{profile.name}</h4>
              <span className={`${role.badge} flex items-center gap-1`}>
                <RoleIcon size={10} />{role.label}
              </span>
            </div>
            <div className="text-xs text-white/40 font-mono mb-2">id: {profile.id}</div>
            <div className="text-xs text-white/55">{role.desc}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
          <div className="p-2.5 rounded-xl" style={{ background: 'rgba(0,234,255,0.04)', border: '1px solid rgba(0,234,255,0.15)' }}>
            <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono mb-0.5 flex items-center gap-1">
              <Languages size={9} /> Lang
            </div>
            <div className="font-semibold text-cyan-200">{profile.language || 'en-US'}</div>
          </div>
          <div className="p-2.5 rounded-xl" style={{ background: 'rgba(255,46,136,0.04)', border: '1px solid rgba(255,46,136,0.15)' }}>
            <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono mb-0.5 flex items-center gap-1">
              <Volume2 size={9} /> Voice
            </div>
            <div className="font-semibold text-pink-200 capitalize">{profile.tts_voice_gender || 'neutral'}</div>
          </div>
        </div>

        <div className="space-y-1.5 mb-4 pt-2 border-t border-jarvis-border/40">
          {[
            { k: 'can_shutdown_pc', label: 'Shutdown / Restart PC' },
            { k: 'can_delete_files', label: 'Delete files on disk' },
          ].map((perm) => {
            const ok = !!profile[perm.k]
            return (
              <div key={perm.k} className="flex items-center justify-between text-xs">
                <span className={`${ok ? 'text-white/70' : 'text-white/40'}`}>{perm.label}</span>
                {ok ? <CheckCircle2 size={13} className="text-emerald-400" /> : <XCircle size={13} className="text-white/20" />}
              </div>
            )
          })}
        </div>

        <div className="flex gap-2">
          {!active && (
            <button
              onClick={() => onActivate(profile.id)}
              className="flex-1 jarvis-btn-sm flex items-center justify-center gap-1.5"
            >
              <Power size={13} /> Activate
            </button>
          )}
          {active && (
            <div className="flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold text-center flex items-center justify-center gap-2"
              style={{
                background: 'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(16,185,129,0.02))',
                border: '1px solid rgba(16,185,129,0.3)',
                color: '#6ee7b7',
              }}
            >
              <CheckCircle2 size={14} /> Active Session
            </div>
          )}
          <button
            onClick={() => onEdit(profile)}
            className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 transition-all hover:bg-white/5 border border-jarvis-border text-white/60 hover:text-white"
          >
            <Edit3 size={15} />
          </button>
        </div>
      </div>
    </motion.div>
  )
}

const ProfilesPanel = () => {
  const { profiles, setProfiles, activeProfileId, setActiveProfileId } = useJarvisStore()
  const [form, setForm] = useState({
    id: '', name: '', role: 'user', language: 'en-US', tts_voice_gender: 'neutral',
    can_shutdown_pc: false, can_delete_files: false, email: '',
  })
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState(null)

  const refresh = () => {
    jarvisApi.listProfiles().then((d) => {
      setProfiles(Array.isArray(d.profiles) ? d.profiles : [])
      if (d.active_user_id) setActiveProfileId(d.active_user_id)
    }).catch((e) => setErr(String(e)))
  }

  useEffect(() => { refresh() }, [])

  const setF = (k, v) => setForm((prev) => ({ ...prev, [k]: v }))

  const resetForm = () => {
    setForm({ id: '', name: '', role: 'user', language: 'en-US', tts_voice_gender: 'neutral', can_shutdown_pc: false, can_delete_files: false, email: '' })
    setEditing(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.id.trim() || !form.name.trim()) return
    setSaving(true)
    setErr(null)
    try {
      if (editing) {
        await jarvisApi.updateProfile(editing.id, form)
      } else {
        await jarvisApi.createProfile(form)
      }
      resetForm()
      setTimeout(refresh, 300)
    } catch (e) {
      setErr(typeof e === 'string' ? e : e?.detail || 'Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (p) => {
    setEditing(p)
    setForm({
      id: p.id,
      name: p.name,
      role: p.role,
      language: p.language || 'en-US',
      tts_voice_gender: p.tts_voice_gender || 'neutral',
      can_shutdown_pc: !!p.can_shutdown_pc,
      can_delete_files: !!p.can_delete_files,
      email: p.email || '',
    })
  }

  const activate = async (id) => {
    try {
      await jarvisApi.activateProfile(id)
      setActiveProfileId(id)
    } catch (e) {
      setErr(String(e))
    }
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-2xl font-bold">
            <span className="neon-text-purple">User Profiles</span>
            <span className="text-white/40 mx-2">·</span>
            <span className="text-white/80">Access Control</span>
          </h2>
          <p className="text-xs text-white/40 mt-1 font-mono">
            Role-based permissions · Admin / User / Guest · POST /api/profiles
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-gradient">{profiles.length} Profiles</span>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="xl:col-span-1"
        >
          <div className="glass p-5 sticky top-2">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-jarvis-border/40">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white/75 flex items-center gap-2">
                <Plus size={15} className="neon-text-purple" />
                {editing ? 'Edit Profile' : 'Create Profile'}
              </h3>
              {editing && (
                <button onClick={resetForm} className="text-xs text-white/40 hover:text-white/70 underline">
                  Cancel edit
                </button>
              )}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">Profile ID</label>
                <input
                  className="input-glass font-mono text-sm"
                  placeholder="e.g. admin01, sarah, guest_01"
                  value={form.id}
                  onChange={(e) => setF('id', e.target.value)}
                  disabled={!!editing || saving}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">Display Name</label>
                <input
                  className="input-glass"
                  placeholder="e.g. Sarah, Admin, Guest"
                  value={form.name}
                  onChange={(e) => setF('name', e.target.value)}
                  disabled={saving}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">Role</label>
                <select
                  className="select-glass"
                  value={form.role}
                  onChange={(e) => setF('role', e.target.value)}
                  disabled={saving}
                >
                  {Object.entries(ROLE_CONFIG).map(([k, v]) => (
                    <option key={k} value={k} className="bg-[#0a0a12]">{k.toUpperCase()} — {v.label}</option>
                  ))}
                </select>
                <p className="text-[11px] text-white/40 mt-1.5">{ROLE_CONFIG[form.role].desc}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">Language</label>
                  <select
                    className="select-glass text-sm"
                    value={form.language}
                    onChange={(e) => setF('language', e.target.value)}
                    disabled={saving}
                  >
                    {['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR', 'ru-RU', 'zh-CN', 'ja-JP', 'ar-SA'].map(l => (
                      <option key={l} value={l} className="bg-[#0a0a12]">{l}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">TTS Voice</label>
                  <select
                    className="select-glass text-sm"
                    value={form.tts_voice_gender}
                    onChange={(e) => setF('tts_voice_gender', e.target.value)}
                    disabled={saving}
                  >
                    <option value="male" className="bg-[#0a0a12]">Male</option>
                    <option value="female" className="bg-[#0a0a12]">Female</option>
                    <option value="neutral" className="bg-[#0a0a12]">Neutral</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">Email (optional)</label>
                <input
                  type="email"
                  className="input-glass"
                  placeholder="user@domain.com"
                  value={form.email}
                  onChange={(e) => setF('email', e.target.value)}
                  disabled={saving}
                />
              </div>

              <div className="pt-2 border-t border-jarvis-border/40 space-y-3">
                <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono flex items-center gap-1">
                  <Lock size={10} /> Permissions
                </div>
                {[
                  { k: 'can_shutdown_pc', label: 'Can shutdown PC', desc: 'Halt / restart system' },
                  { k: 'can_delete_files', label: 'Can delete files', desc: 'Remove files from disk' },
                ].map((p) => (
                  <label key={p.k} className="flex items-start justify-between py-1.5 cursor-pointer group">
                    <div>
                      <div className="text-sm text-white/80 group-hover:text-white">{p.label}</div>
                      <div className="text-[11px] text-white/40">{p.desc}</div>
                    </div>
                    <div
                      role="switch"
                      aria-checked={!!form[p.k]}
                      data-checked={!!form[p.k]}
                      onClick={() => setF(p.k, !form[p.k])}
                      className={`switch flex-shrink-0`}
                    >
                      <span className="switch-handle" />
                    </div>
                  </label>
                ))}
              </div>

              {err && (
                <div className="p-3 rounded-xl text-xs"
                  style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5' }}>
                  {err}
                </div>
              )}

              <button
                type="submit"
                disabled={saving || !form.id.trim() || !form.name.trim()}
                className="jarvis-btn w-full flex items-center justify-center gap-2 disabled:opacity-40"
              >
                <Save size={15} />
                {saving ? 'Saving...' : editing ? 'Update Profile' : 'Create Profile'}
              </button>
            </form>
          </div>
        </motion.div>

        <div className="xl:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-6">
            <AnimatePresence>
              {profiles.length === 0 ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="md:col-span-2 glass p-12 text-center"
                >
                  <div className="mx-auto w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                    style={{ background: 'linear-gradient(135deg, rgba(123,47,247,0.15), rgba(0,234,255,0.08))' }}
                  >
                    <Users size={28} className="text-white/40" />
                  </div>
                  <h3 className="text-lg font-semibold text-white/70">No profiles yet</h3>
                  <p className="text-sm text-white/40 mt-1">Start by creating the first profile with the form on the left.</p>
                </motion.div>
              ) : (
                profiles.map((p) => (
                  <ProfileCard
                    key={p.id}
                    profile={p}
                    active={p.id === activeProfileId}
                    onActivate={activate}
                    onEdit={startEdit}
                  />
                ))
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfilesPanel
