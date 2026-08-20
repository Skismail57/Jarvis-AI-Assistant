import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bell, Plus, X, Clock, Repeat, Calendar as CalendarIcon,
  AlertCircle, CheckCircle2, Trash2, Zap
} from 'lucide-react'
import { format, formatRelative, parseISO, isBefore } from 'date-fns'
import useJarvisStore from '../store/useJarvisStore'
import { jarvisApi } from '../api/client'

const ReminderCard = ({ reminder, onCancel }) => {
  const fire_at = reminder.fire_at ? parseISO(reminder.fire_at) : null
  const created_at = reminder.created_at ? parseISO(reminder.created_at) : new Date()
  const isPast = fire_at && isBefore(fire_at, new Date())
  const status = reminder.cancelled
    ? 'cancelled'
    : reminder.fired
      ? 'fired'
      : isPast
        ? 'overdue'
        : 'scheduled'

  const statusConfig = {
    scheduled: { label: 'Scheduled', cls: 'badge-info', icon: Clock },
    fired: { label: 'Fired', cls: 'badge-success', icon: CheckCircle2 },
    cancelled: { label: 'Cancelled', cls: 'badge-danger', icon: X },
    overdue: { label: 'Overdue', cls: 'badge-warning', icon: AlertCircle },
  }

  const cfg = statusConfig[status]
  const Icon = cfg.icon

  const recurrence = reminder.recurrence || (reminder.cron ? 'cron' : reminder.interval_seconds ? 'interval' : 'once')

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 30, scale: 0.95 }}
      className="glass card-hover p-4 relative overflow-hidden"
    >
      <div className="absolute -bottom-10 -right-10 w-28 h-28 rounded-full blur-3xl opacity-10"
        style={{
          background:
            status === 'fired' ? '#34d399' :
              status === 'cancelled' ? '#ef4444' :
                status === 'overdue' ? '#fbbf24' : '#7b2ff7'
        }} />
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0`}
              style={{
                background:
                  status === 'scheduled' ? 'linear-gradient(135deg, rgba(0,234,255,0.2), rgba(123,47,247,0.15))' :
                    status === 'fired' ? 'rgba(16,185,129,0.15)' :
                      status === 'cancelled' ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.15)',
                border: `1px solid ${
                  status === 'scheduled' ? 'rgba(0,234,255,0.35)' :
                    status === 'fired' ? 'rgba(16,185,129,0.35)' :
                      status === 'cancelled' ? 'rgba(239,68,68,0.25)' : 'rgba(245,158,11,0.35)'
                }`,
              }}
            >
              <Bell size={17} className={
                status === 'scheduled' ? 'text-cyan-300' :
                  status === 'fired' ? 'text-emerald-300' :
                    status === 'cancelled' ? 'text-rose-300/60' : 'text-amber-300'
              } />
            </div>
            <div className="min-w-0">
              <div className={`text-sm font-semibold leading-snug ${status === 'cancelled' ? 'text-white/40 line-through' : 'text-white'}`}>
                {reminder.text || '(no text)'}
              </div>
              <div className="text-[11px] text-white/40 font-mono mt-0.5 flex items-center gap-2">
                <span>#{reminder.id.slice(0, 8)}</span>
                <span>·</span>
                <span>{format(created_at, 'MMM d HH:mm')}</span>
              </div>
            </div>
          </div>
          <span className={`${cfg.cls} flex items-center gap-1 flex-shrink-0`}>
            <Icon size={11} />
            {cfg.label}
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          <div className="p-3 rounded-xl" style={{ background: 'rgba(123,47,247,0.05)', border: '1px solid rgba(123,47,247,0.15)' }}>
            <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono mb-1 flex items-center gap-1.5">
              <CalendarIcon size={10} /> Fire At
            </div>
            <div className="text-sm font-semibold text-white/90">
              {fire_at ? format(fire_at, 'MMM d, yyyy HH:mm') : '—'}
            </div>
            {fire_at && (
              <div className="text-[11px] neon-text-purple mt-0.5 font-medium">
                {formatRelative(fire_at, new Date())}
              </div>
            )}
          </div>
          <div className="p-3 rounded-xl" style={{ background: 'rgba(255,46,136,0.05)', border: '1px solid rgba(255,46,136,0.15)' }}>
            <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono mb-1 flex items-center gap-1.5">
              <Repeat size={10} /> Recurrence
            </div>
            <div className="text-sm font-semibold text-white/90 capitalize">
              {recurrence}
            </div>
            <div className="text-[11px] text-white/50 mt-0.5 font-mono truncate">
              {reminder.interval_seconds ? `Every ${reminder.interval_seconds}s` : reminder.cron ? JSON.stringify(reminder.cron) : 'One-time'}
            </div>
          </div>
        </div>

        {status === 'scheduled' && (
          <div className="flex justify-end">
            <button
              onClick={() => onCancel(reminder.id)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 text-rose-300 hover:bg-rose-500/10 border border-rose-500/20 transition-colors"
            >
              <Trash2 size={12} /> Cancel Reminder
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}

const RemindersPanel = () => {
  const { reminders, setReminders, addReminder, removeReminder } = useJarvisStore()
  const [text, setText] = useState('')
  const [when, setWhen] = useState('in 1 hour')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState(null)

  const refresh = () => {
    jarvisApi.listReminders()
      .then((data) => {
        const list = (data?.reminders) || []
        setReminders(list)
      })
      .catch((e) => setError(String(e)))
  }

  useEffect(() => { refresh() }, [])

  const handleAdd = async () => {
    const t = text.trim()
    const w = when.trim() || 'in 1 hour'
    if (!t) return
    setAdding(true)
    setError(null)
    try {
      const res = await jarvisApi.addReminder(t, w)
      const newRem = {
        id: res.id,
        text: t,
        fire_at: res.fire_at,
        recurrence: 'once',
        fired: false,
        cancelled: false,
        created_at: new Date().toISOString(),
      }
      addReminder(newRem)
      setText('')
      setWhen('in 1 hour')
      setTimeout(refresh, 1500)
    } catch (err) {
      setError(typeof err === 'string' ? err : err?.detail || 'Failed to add reminder')
    } finally {
      setAdding(false)
    }
  }

  const handleCancel = async (id) => {
    try {
      await jarvisApi.cancelReminder(id)
      removeReminder(id)
    } catch (err) {
      setError(String(err))
    }
  }

  const stats = {
    scheduled: reminders.filter(r => !r.fired && !r.cancelled).length,
    fired: reminders.filter(r => r.fired).length,
    cancelled: reminders.filter(r => r.cancelled).length,
  }

  return (
    <div className="h-full overflow-y-auto pr-2">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-2xl font-bold">
            <span className="neon-text-cyan">Reminders</span>
            <span className="text-white/40 mx-2">·</span>
            <span className="text-white/80">Scheduler</span>
          </h2>
          <p className="text-xs text-white/40 mt-1 font-mono">
            Natural language scheduling · APScheduler backed · CRON + intervals
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-gradient flex items-center gap-1.5">
            <Bell size={11} />
            {reminders.length} total
          </span>
          <span className="badge-info">{stats.scheduled} scheduled</span>
          <span className="badge-success">{stats.fired} fired</span>
          <span className="badge-danger">{stats.cancelled} cancelled</span>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass p-5 mb-6 relative overflow-hidden"
      >
        <div className="absolute -top-20 right-0 w-64 h-64 rounded-full blur-3xl opacity-10 pointer-events-none"
          style={{ background: 'radial-gradient(circle, #00eaff, transparent 70%)' }} />
        <div className="relative z-10">
          <h3 className="text-sm font-bold uppercase tracking-wider text-white/70 mb-4 flex items-center gap-2">
            <Plus size={16} className="neon-text-cyan" /> Schedule New Reminder
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-4">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="md:col-span-3">
                <label className="block text-xs font-semibold text-white/60 mb-2 uppercase tracking-wider">
                  <Bell size={10} className="inline mr-1" /> Reminder Text
                </label>
                <input
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                  placeholder="e.g. Water the plants, take medicine, stand up and stretch..."
                  className="input-glass"
                  disabled={adding}
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-white/60 mb-2 uppercase tracking-wider">
                  <Zap size={10} className="inline mr-1" /> When (natural)
                </label>
                <input
                  value={when}
                  onChange={(e) => setWhen(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                  placeholder="in 30 minutes · 6pm · every day 09:00 · tomorrow at noon"
                  className="input-glass"
                  disabled={adding}
                />
              </div>
            </div>
            <div className="flex md:items-end">
              <button
                onClick={handleAdd}
                disabled={adding || !text.trim()}
                className="jarvis-btn w-full md:w-auto flex items-center justify-center gap-2 h-12 md:px-6 disabled:opacity-40"
              >
                {adding ? (
                  <><Repeat size={16} className="animate-spin" /> Scheduling...</>
                ) : (
                  <><Plus size={16} /> Add Reminder</>
                )}
              </button>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-[10px] uppercase tracking-wider text-white/30 font-mono self-center mr-1">Quick:</span>
            {[
              { t: 'Drink water', w: 'in 45 minutes' },
              { t: 'Take a break', w: 'in 30 minutes' },
              { t: 'Stand up & stretch', w: 'in 1 hour' },
              { t: 'Team standup', w: 'every weekday at 09:30' },
            ].map((q) => (
              <button
                key={q.t}
                onClick={() => { setText(q.t); setWhen(q.w) }}
                className="px-3 py-1.5 rounded-lg text-[11px] font-medium border border-jarvis-border hover:border-jarvis-purple/40 text-white/60 hover:text-white hover:bg-white/5 transition-all"
              >
                {q.t}
              </button>
            ))}
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-4 p-3 rounded-xl flex items-center gap-2 text-sm"
              style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5' }}
            >
              <AlertCircle size={15} /> {error}
            </motion.div>
          )}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pb-6">
        <AnimatePresence mode="popLayout">
          {reminders.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="lg:col-span-2 glass p-12 text-center"
            >
              <div className="mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4"
                style={{ background: 'linear-gradient(135deg, rgba(123,47,247,0.15), rgba(0,234,255,0.1))' }}
              >
                <Bell size={28} className="text-white/40" />
              </div>
              <h3 className="text-lg font-semibold text-white/70">No reminders yet</h3>
              <p className="text-sm text-white/40 mt-1">Create your first reminder using the form above.</p>
            </motion.div>
          ) : (
            reminders
              .slice()
              .sort((a, b) => {
                const ta = a.fire_at ? new Date(a.fire_at).getTime() : 0
                const tb = b.fire_at ? new Date(b.fire_at).getTime() : 0
                return tb - ta
              })
              .map((r) => (
                <ReminderCard key={r.id} reminder={r} onCancel={handleCancel} />
              ))
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default RemindersPanel
