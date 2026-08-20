import React, { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Mic, MicOff, Square, ChevronDown, ChevronUp,
  Hexagon, Sparkles, Wrench, Clock, Hash
} from 'lucide-react'
import { format } from 'date-fns'
import useJarvisStore from '../store/useJarvisStore'
import { chatWS } from '../api/client'
import WaveformAnimation from './WaveformAnimation'

const JarvisAvatar = ({ size = 32 }) => (
  <motion.div
    className="flex-shrink-0 w-8 h-8 rounded-full bg-jarvis-gradient flex items-center justify-center shadow-neon-purple"
    animate={{ rotate: 360 }}
    transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
  >
    <span className="text-white font-bold text-sm">J</span>
  </motion.div>
)

const UserAvatar = ({ size = 32 }) => (
  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-jarvis-panel border border-jarvis-border flex items-center justify-center">
    <span className="text-jarvis-text font-semibold text-sm">U</span>
  </div>
)

const ToolResultCard = ({ result }) => {
  const [open, setOpen] = useState(false)
  const jsonStr = JSON.stringify(result, null, 2)

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      className="mt-3"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-2 px-4 py-2.5 rounded-xl text-xs font-medium"
        style={{
          background: 'linear-gradient(135deg, rgba(0,234,255,0.1), rgba(123,47,247,0.1))',
          border: '1px solid rgba(0,234,255,0.25)',
        }}
      >
        <span className="flex items-center gap-2 neon-text-cyan font-semibold">
          <Wrench size={14} />
          Skill Execution Result
        </span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="mt-2 code-block text-[11px] max-h-60 overflow-y-auto"
          >
            <pre className="whitespace-pre-wrap break-all text-white/80">{jsonStr}</pre>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

const MessageBubble = ({ msg }) => {
  const isUser = msg.role === 'user'
  const time = msg.timestamp ? format(new Date(msg.timestamp), 'HH:mm:ss') : '--:--:--'

  if (isUser) {
    return (
      <div className="flex items-end justify-end gap-3 mb-4">
        <div className="max-w-[70%] flex flex-col items-end">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl rounded-tr-sm p-3 text-jarvis-bg text-sm leading-relaxed bg-jarvis-gradient shadow-neon-pink"
          >
            {msg.content}
          </motion.div>
          <div className="flex items-center gap-2 mt-1.5 px-1">
            <span className="text-[10px] text-jarvis-textDim font-mono flex items-center gap-1">
              <Clock size={9} />{time}
            </span>
          </div>
        </div>
        <UserAvatar />
      </div>
    )
  }

  return (
    <div className="flex items-end gap-3 mb-4">
      <JarvisAvatar />
      <div className="max-w-[75%] flex flex-col">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl rounded-tl-sm p-3 border border-jarvis-border"
        >
          <p className="text-sm leading-relaxed text-jarvis-text whitespace-pre-wrap break-words">
            {msg.content}
            {msg.streaming && (
              <span className="inline-block w-2 h-4 ml-0.5 align-middle animate-pulse rounded-sm bg-jarvis-cyan shadow-neon-cyan" />
            )}
          </p>
          {!msg.streaming && msg.skill_result && Object.keys(msg.skill_result).length > 0 && (
            <ToolResultCard result={msg.skill_result} />
          )}
        </motion.div>
        <div className="flex flex-wrap items-center gap-2 mt-1.5 px-1">
          <span className="text-[10px] text-jarvis-textDim font-mono flex items-center gap-1">
            <Clock size={9} />{time}
          </span>
          {msg.intent && (
            <span className="text-[10px] text-jarvis-cyan flex items-center gap-1 neon-text">
              <Sparkles size={9} />
              {msg.intent}
            </span>
          )}
          {typeof msg.confidence === 'number' && (
            <span className="text-[10px] text-jarvis-textDim flex items-center gap-1">
              <Hash size={9} />
              {Math.round(msg.confidence * 100)}% confidence
            </span>
          )}
          {msg.detected_language && (
            <span className="text-[10px] text-jarvis-textDim">{msg.detected_language}</span>
          )}
        </div>
      </div>
    </div>
  )
}

const TypingIndicator = () => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex items-end gap-3 mb-4"
  >
    <JarvisAvatar size={38} />
    <div className="glass px-5 py-4 rounded-2xl rounded-tl-sm">
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="typing-dot"
            style={{ animationDelay: `${i * 0.18}s` }}
          />
        ))}
      </div>
    </div>
  </motion.div>
)

const ChatPanel = () => {
  const {
    messages, isStreaming, isListening, wsChatConnected,
    addMessage, appendStreamingToken, finalizeStreamingMessage,
    startStreaming, stopStreaming, setIsListening, activeProfileId,
  } = useJarvisStore()

  const [input, setInput] = useState('')
  const scrollRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isStreaming])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 180) + 'px'
    }
  }, [input])

  useEffect(() => {
    const unsubMsg = chatWS.on('message', (data) => {
      if (typeof data !== 'object' || !data.type) return
      if (data.type === 'start') {
        const assistantMsg = {
          id: 'assist-' + Date.now(),
          role: 'assistant',
          content: '',
          streaming: true,
          intent: '',
          confidence: 0,
          timestamp: new Date().toISOString(),
        }
        addMessage(assistantMsg)
        startStreaming(assistantMsg.id)
      } else if (data.type === 'token') {
        appendStreamingToken(data.content || '')
      } else if (data.type === 'end') {
        finalizeStreamingMessage({
          content: data.content,
          intent: data?.data?.intent,
          confidence: data?.data?.confidence,
          detected_language: data?.data?.detected_language,
          skill_result: data?.data?.skill_result,
        })
      }
    })
    return () => unsubMsg()
  }, [addMessage, appendStreamingToken, finalizeStreamingMessage, startStreaming])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isStreaming) return
    const userMsg = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMsg)
    setInput('')
    chatWS.send({ message: text, user_id: activeProfileId })
  }

  const handleStop = () => {
    stopStreaming()
  }

  const toggleListen = () => setIsListening(!isListening)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold gradient-text">Chat</h2>
          <p className="text-xs text-jarvis-textDim mt-1 font-mono">
            WebSocket: /ws/chat
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono ${wsChatConnected ? 'text-jarvis-cyan neon-text' : 'text-jarvis-pink'}`}>
            {wsChatConnected ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto pr-2 mb-4 scroll-smooth"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center px-8">
            <JarvisAvatar />
            <h3 className="mt-4 text-lg font-bold text-jarvis-text">
              Welcome. I am JARVIS.
            </h3>
            <p className="mt-2 max-w-md text-sm text-jarvis-textDim leading-relaxed">
              Ask me anything — manage your system, schedule reminders, automate tasks.
            </p>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble key={m.id} msg={m} />
        ))}
        {isStreaming && !messages.find(m => m.streaming) && (
          <TypingIndicator />
        )}
      </div>

      <div className="glass p-3 rounded-2xl border border-jarvis-border">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask JARVIS anything... (Enter to send, Shift+Enter for new line)"
            rows={1}
            disabled={isStreaming}
            className="input-glass resize-none"
          />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleListen}
            disabled={isStreaming}
            className={`w-10 h-10 rounded-full flex items-center justify-center border ${
              isListening
                ? 'bg-jarvis-pink border-jarvis-pink text-white shadow-neon-pink'
                : 'bg-jarvis-panel border-jarvis-border text-jarvis-textDim hover:text-jarvis-text hover:border-jarvis-cyan'
            }`}
          >
            {isListening ? <MicOff size={16} /> : <Mic size={16} />}
          </motion.button>
          {isStreaming ? (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStop}
              className="w-10 h-10 rounded-full flex items-center justify-center bg-jarvis-pink/10 border border-jarvis-pink/30 text-jarvis-pink"
            >
              <Square size={14} fill="currentColor" />
            </motion.button>
          ) : (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSend}
              disabled={!input.trim()}
              className="w-10 h-10 rounded-full flex items-center justify-center bg-jarvis-gradient text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-neon-purple"
            >
              <Send size={16} />
            </motion.button>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatPanel
