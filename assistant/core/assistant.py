import os
import sys
import re
import json
import random
import datetime
import threading
import asyncio
from typing import Optional, Dict, Any

from ..nlp.intent_classifier import IntentClassifier
from ..voice.stt import SpeechToText
from ..voice.tts import TextToSpeech
from ..voice.wake_word import WakeWordEngine
from ..voice.advanced_wake_word import AdvancedWakeWordEngine
from ..memory.conversation_memory import ConversationMemory
from ..memory.vector_memory import VectorMemory
from ..skills.skill_handler import SkillHandler
from ..skills.reminder_scheduler import ReminderScheduler
from ..plugins.plugin_manager import PluginManager
from ..identity.user_profiles import UserProfileManager
from ..voice.multilingual import detect_language, get_voice_for_locale, edge_tts_speak_sync
from ..utils.logger import logger
from ..config import settings

from .llm_core import LLMCore
from .data_provider import DataProvider
from .pc_controller import PCController
from .agent import JarvisAgent
from .auto_learner import AutoLearner


class AIAssistant:
    def __init__(
        self,
        name: str = "Jarvis",
        use_voice: bool = True,
        wake_word: str = "jarvis",
        stt_engine: str = "sr",
        tts_engine: str = "pyttsx3",
        confidence_threshold: float = 0.20,
        language: str = "en-US",
        llm_model: str = "auto",
        enable_wake_word: bool = True,
        enable_agent: bool = True,
        user_id: str = "default",
        use_advanced_wake: bool = True,
    ):
        self.name = name or settings.assistant_name
        self.use_voice = use_voice
        self.wake_word = (wake_word or settings.wake_word).lower()
        self.confidence_threshold = confidence_threshold or settings.confidence_threshold
        self.language = language
        self.running = False
        self.enable_agent = enable_agent and settings.enable_agent
        self.current_user_id = user_id

        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.classifier = IntentClassifier()
        self.memory = ConversationMemory(max_history=settings.max_conversation_history)

        self.vector_memory: Optional[VectorMemory] = None
        if settings.enable_vector_memory:
            try:
                self.vector_memory = VectorMemory()
                logger.info(f"[AIAssistant] Vector memory ready ({self.vector_memory.count()} items)")
            except Exception as e:
                logger.warning(f"[AIAssistant] Vector memory unavailable: {e}")
                self.vector_memory = None

        self.user_profiles = UserProfileManager()

        self.reminder_scheduler = ReminderScheduler(on_fire=self._on_reminder_fired)
        try:
            self.reminder_scheduler.start()
        except Exception as e:
            logger.warning(f"[AIAssistant] Reminder scheduler start failed: {e}")

        self.skill_handler = SkillHandler(reminder_scheduler=self.reminder_scheduler)
        self.plugin_manager = PluginManager()
        self.plugin_manager.discover()

        self.llm = LLMCore(model=llm_model)
        self.data = DataProvider()
        self.pc = PCController()
        self.agent = JarvisAgent(self)
        self.learner = AutoLearner(self)

        self.stt: Optional[SpeechToText] = None
        self.tts: Optional[TextToSpeech] = None
        self.wake: Optional[WakeWordEngine] = None
        self.adv_wake: Optional[AdvancedWakeWordEngine] = None

        if use_voice:
            self.stt = SpeechToText(engine=stt_engine, language=language)
            self.tts = TextToSpeech(engine=tts_engine, language=language.split("-")[0])
            if use_advanced_wake:
                self.adv_wake = AdvancedWakeWordEngine(
                    wake_word=self.wake_word,
                    sensitivity=settings.jarvis_wake_sensitivity,
                    stt=self.stt,
                    on_wake=self._on_wake_word,
                    access_key=settings.porcupine_access_key,
                    use_porcupine=bool(settings.porcupine_access_key),
                )
            else:
                self.wake = WakeWordEngine(
                    wake_word=wake_word,
                    sensitivity=settings.jarvis_wake_sensitivity,
                    stt=self.stt,
                    on_wake=self._on_wake_word
                )

        self._greeted = False
        self._last_processed_at = 0.0
        self._wake_active = threading.Event()
        self._pending_reminders: list = []
        logger.info(f"[AIAssistant] {self.name} initialized (voice={'ON' if use_voice else 'OFF'}, user={self.current_user_id})")

    # ------------- Reminder callback -------------

    def _on_reminder_fired(self, reminder: Dict[str, Any]):
        text = reminder.get("text", "")
        alert = f"🔔 Reminder! {text}"
        logger.info(f"[AIAssistant] {alert}")
        self._pending_reminders.append(reminder)
        if self.tts:
            try:
                self.tts.speak(f"Reminder! {text}", block=False)
            except Exception as e:
                logger.debug(f"[AIAssistant] TTS reminder error: {e}")
        try:
            print(f"\n🔔 [{self.name}] {alert}")
        except Exception:
            pass

    # ------------- Greeting & Basic API -------------

    def greet(self, speak: bool = True) -> str:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            time_greeting = "Good morning"
        elif 12 <= hour < 17:
            time_greeting = "Good afternoon"
        elif 17 <= hour < 21:
            time_greeting = "Good evening"
        else:
            time_greeting = "Hello"

        info = self.pc.system_info()
        cpu = info.get("cpu_percent", 0)
        ram = info.get("ram_percent", 0)

        messages = [
            f"{time_greeting}! I'm {self.name}, online and fully operational. All systems nominal — CPU {cpu}%, memory {ram}%. How may I serve you, sir/madam?",
            f"{time_greeting}! {self.name} at your service. Boot sequence complete. Current CPU load: {cpu}%, RAM usage: {ram}%. What's first on the agenda?",
            f"Hey there — {self.name} reporting for duty. Environment scanned and ready for commands. What can I do for you?"
        ]
        greeting = random.choice(messages)
        self._greeted = True
        self.memory.add_assistant(greeting)
        if self.vector_memory:
            try:
                self.vector_memory.add_fact(f"Greeting at {datetime.datetime.now()}: {greeting}")
            except Exception:
                pass

        if speak and self.tts:
            self.tts.speak(greeting, block=False)
        return greeting

    # ------------- Core processing -------------

    def process_input(self, text: str, speak: bool = True) -> Dict[str, Any]:
        import time as _t
        if not text or not text.strip():
            return {"response": "I didn't catch that. Could you say it again?", "intent": "unknown"}

        text = text.strip()
        self._last_processed_at = _t.time()

        detected = detect_language(text)
        self.memory.add_user(text, metadata={"detected_language": detected})

        # 0) Plugins first
        plugin_result = self.plugin_manager.try_handle(text, assistant_ref=self)
        if plugin_result and plugin_result.get("text"):
            final_answer = plugin_result["text"]
            intent = plugin_result.get("intent", "plugin")
            self.memory.add_assistant(final_answer, metadata={"intent": intent, "plugin": plugin_result.get("plugin")})
            if speak and self.tts:
                self._speak_smart(final_answer, detected or self.language)
            return {
                "input": text, "response": final_answer, "intent": intent,
                "confidence": 1.0, "plugin": plugin_result.get("plugin"),
            }

        # 0b) Domain-specific static skill handlers (Screen Understanding / Smart Home / Productivity)
        from ..vision.screen_understanding import ScreenUnderstanding
        from ..smarthome.home_assistant import HomeAssistantBridge
        from ..skills.productivity_skills import _get_router
        _PRODUCTIVITY_ALLOWED_PREFIXES = (
            "email_", "calendar_", "todo_", "notion_", "schedule_", "gmail_", "google_",
            "meeting_", "event_", "inbox_", "draft_", "productivity_",
        )
        for handler_name, handler_fn in (
            ("screen", lambda t: ScreenUnderstanding.skill_handle(t, assistant_ref=self)),
            ("smarthome", lambda t: HomeAssistantBridge.skill_handle(t, assistant_ref=self)),
            ("productivity", lambda t: _get_router().handle(t, context={"assistant": self})),
        ):
            try:
                domain_res = handler_fn(text)
            except Exception as e:
                logger.debug(f"[AIAssistant] {handler_name} handler error: {e}")
                domain_res = None
            if not (domain_res and isinstance(domain_res, dict) and domain_res.get("text")):
                continue
            _intent_raw = str(domain_res.get("intent", handler_name))
            if handler_name == "productivity":
                if _intent_raw == "productivity_unknown":
                    continue
                if not any(_intent_raw.startswith(p) for p in _PRODUCTIVITY_ALLOWED_PREFIXES) and not any(k in _intent_raw.lower() for k in ("email", "calendar", "todo", "notion", "schedule", "meeting", "event", "inbox", "draft")):
                    continue
            final_answer = domain_res["text"]
            intent = _intent_raw
            self.memory.add_assistant(final_answer, metadata={
                "intent": intent, "source": handler_name,
                "data_keys": sorted(list(domain_res.get("data", {}).keys())) if isinstance(domain_res.get("data"), dict) else None,
            })
            if self.vector_memory:
                try:
                    self.vector_memory.add_fact(
                        f"[{handler_name}] Q: {text} A: {final_answer}",
                        tags=[handler_name, intent],
                    )
                except Exception:
                    pass
            if speak and self.tts:
                self._speak_smart(final_answer, detected or self.language)
            return {
                "input": text, "response": final_answer, "intent": intent,
                "confidence": 1.0, "source": handler_name,
                "skill_result": domain_res.get("data"),
            }

        # 1) Intent classification
        intent_result = self.classifier.get_intent(text, threshold=self.confidence_threshold)
        intent_name = intent_result["intent"]
        confidence = intent_result["confidence"]
        intent_responses = intent_result.get("responses", [])

        # 2) Custom QA first
        custom_qa = self.learner.lookup_custom_qa(text)
        if custom_qa:
            response_text = custom_qa["match"]["a"]
            self.memory.add_assistant(response_text, metadata={"intent": "custom_qa", "score": custom_qa["score"]})
            if self.vector_memory:
                try:
                    self.vector_memory.add_fact(f"Q: {text} A: {response_text}", tags=["custom_qa", "user_taught"])
                except Exception:
                    pass
            if speak and self.tts:
                self._speak_smart(response_text, detected or self.language)
            return {
                "input": text,
                "response": response_text,
                "intent": "custom_qa",
                "confidence": custom_qa["score"],
                "custom_qa": custom_qa,
            }

        # 3) Agent (chain-of-thought)
        final_answer = None
        agent_output: Optional[Dict[str, Any]] = None
        try:
            if self.enable_agent:
                agent_output = self.agent.reason(text)
                final_answer = agent_output.get("answer")
        except Exception as e:
            logger.debug(f"[AIAssistant] Agent error (falling back): {e}")

        # 4) Skill handler fallback
        skill_result = None
        if not final_answer:
            skill_result = self.skill_handler.handle(
                intent_name, text, context={"responses": intent_responses}
            )
            if skill_result and "text" in skill_result:
                final_answer = skill_result["text"]

        # 5) Final LLM fallback with vector memory context
        needs_llm = (
            not final_answer
            or len(str(final_answer)) < 30
            or (isinstance(final_answer, str) and "offline" in final_answer.lower() and self.llm.has_any_key())
        )
        if needs_llm:
            try:
                extra_ctx = ""
                if self.vector_memory:
                    try:
                        extra_ctx = self.vector_memory.get_context_for_prompt(text)
                    except Exception:
                        extra_ctx = ""
                recent = self.memory.get_recent_context(turns=3)
                combined_ctx = recent
                if extra_ctx:
                    combined_ctx = (combined_ctx + "\n\nLong-term memory:\n" + extra_ctx) if combined_ctx else ("Long-term memory:\n" + extra_ctx)
                llm_r = self.llm.answer(text, context=combined_ctx or None)
                final_answer = llm_r.text or final_answer
            except Exception as e:
                logger.debug(f"[AIAssistant] LLM fallback error: {e}")

        if not final_answer:
            final_answer = (
                intent_responses[0] if intent_responses
                else "I'm JARVIS — I processed your request but I need a moment or a bit more detail. Could you rephrase?"
            )

        self.memory.add_assistant(final_answer, metadata={
            "intent": intent_name,
            "confidence": confidence,
            "used_agent": bool(agent_output),
        })

        if self.vector_memory:
            try:
                self.vector_memory.add_conversation_pair(
                    text, final_answer,
                    metadata={"intent": intent_name, "user_id": self.current_user_id}
                )
            except Exception:
                pass

        if speak and self.tts:
            self._speak_smart(final_answer, detected or self.language)

        return {
            "input": text,
            "response": final_answer,
            "intent": intent_name,
            "confidence": confidence,
            "skill_result": skill_result or {},
            "agent": agent_output,
            "detected_language": detected,
        }

    async def process_input_async(self, text: str, speak: bool = True) -> Dict[str, Any]:
        """Async version of process_input for parallel execution of independent tasks."""
        # Run the synchronous process_input in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process_input, text, speak)

    def _speak_smart(self, text: str, language_hint: str = "en-US"):
        if self.tts is None:
            return
        engine = (getattr(self.tts, "engine", "") or "").lower()
        if engine == "edge-tts" or language_hint and language_hint != "en-US":
            try:
                gender = "neutral"
                profile = self.user_profiles.get_profile(self.current_user_id) or {}
                gender = profile.get("tts_voice_gender", "neutral")
                voice = get_voice_for_locale(language_hint or self.language, gender=gender)
                rate_pct = 0
                result = edge_tts_speak_sync(self._tts_clean(text), voice=voice, rate=f"{rate_pct:+d}%")
                if result:
                    return
            except Exception as e:
                logger.debug(f"[AIAssistant] edge-tts fallback failed: {e}")
        try:
            self.tts.speak(self._tts_clean(text), block=False)
        except Exception as e:
            logger.debug(f"[AIAssistant] TTS error: {e}")

    @staticmethod
    def _tts_clean(text: str) -> str:
        text = re.sub(r"https?://\S+", "link available below", text)
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 1200:
            text = text[:1200].rstrip() + " ... (truncated)"
        return text

    # ------------- Voice -------------

    def _on_wake_word(self, detected_text: str):
        if self._wake_active.is_set():
            return
        self._wake_active.set()
        try:
            ack = random.choice([
                f"At your service.",
                f"Yes, I'm here.",
                f"{self.name} online. Listening.",
                f"Go ahead, I'm listening.",
                f"Standing by."
            ])
            print(f"\n[{self.name}] {ack}")
            if self.tts:
                self.tts.speak(ack, block=False)
            result = self.listen_and_respond(timeout=6, phrase_time_limit=20)
            if result is None:
                silence_msg = "I didn't hear a command. I'll stand by for the wake word."
                print(f"[{self.name}] {silence_msg}")
                if self.tts:
                    self.tts.speak(silence_msg, block=False)
        finally:
            self._wake_active.clear()

    def listen_and_respond(self, timeout: int = 5, phrase_time_limit: int = 15) -> Optional[Dict[str, Any]]:
        if self.stt is None:
            print(f"[{self.name}] Voice input is not available. Use text mode.")
            return None

        text = self.stt.listen_from_microphone(
            timeout=timeout, phrase_time_limit=phrase_time_limit
        )
        if not text:
            return None

        text_clean = text
        ww = self.wake_word
        if text_clean.lower().startswith(ww):
            text_clean = text_clean[len(ww):].lstrip(" ,.:;-!")
        if text_clean.lower().startswith(f"hey {ww}"):
            text_clean = text_clean[len(f"hey {ww}"):].lstrip(" ,.:;-!")

        print(f"\n[You] {text}")
        result = self.process_input(text_clean, speak=True)
        self._print_response(result)
        self._maybe_ask_feedback(result)
        return result

    def chat_text(self, message: str, speak: bool = True) -> str:
        result = self.process_input(message, speak=speak and self.use_voice)
        return result["response"]

    def _print_response(self, result: Dict[str, Any]):
        agent = result.get("agent")
        resp = result["response"]
        lang = result.get("detected_language") or ""
        lang_note = f" [detected: {lang}]" if lang and lang != "en-US" else ""
        print(f"[{self.name}] {resp}{lang_note}")
        if agent:
            tools = agent.get("tool_calls", [])
            if tools:
                summary = ", ".join({t.get("tool", "?") for t in tools})
                print(f"   (tools used: {summary} | iterations: {agent.get('iterations')})")

    def _maybe_ask_feedback(self, result: Dict[str, Any]):
        conf = result.get("confidence", 1.0)
        if conf < 0.40:
            hint = (
                f"   tip: if my answer was wrong, reply with: "
                f"\"learn it: expected intent 'X'\" or "
                f"\"teach: '<question>' means '<answer>'\""
            )
            print(hint)

    # ------------- Meta commands -------------

    def handle_meta_command(self, user_input: str) -> Optional[str]:
        s = user_input.strip()
        low = s.lower()

        m = re.match(r"^retrain(?:\s+(?:model|classifier|ai|brain))?\s*$", low)
        if m:
            self.learner.retrain_classifier(force=True)
            return "I've re-trained my intent classification brain using all data and custom intents. Ready."

        m = re.match(r"^(correct it|my answer|no it was|it should be|expected intent):\s*(.+)$", low, re.IGNORECASE)
        if m:
            exp = m.group(2).strip()
            last_u = self.memory.get_last(role="user")
            last_a = self.memory.get_last(role="assistant")
            if last_u and last_a:
                self.learner.record_feedback(
                    last_u["content"], last_a["content"],
                    intent=last_a["metadata"].get("intent", "unknown"),
                    confidence=last_a["metadata"].get("confidence", 0.0),
                    was_correct=False,
                    expected_intent=exp if " " not in exp else None,
                    better_answer=exp if " " in exp else None,
                )
                self.learner.retrain_classifier(force=False)
                return f"Noted. I've updated my training data with the correction and re-trained. Thank you!"
            return "I don't have enough context. Please re-run the query first."

        m = re.match(r"^learn:\s*[\"']?(.+?)[\"']?\s*=\s*[\"']?(.+?)[\"']?\s*$", s, re.IGNORECASE)
        if not m:
            m = re.match(r"^teach:\s*(.+?)\s+means\s+(.+)$", s, re.IGNORECASE)
        if m:
            q, a = m.group(1).strip(), m.group(2).strip()
            self.learner.add_custom_qa(q, a, tags=["user_taught"])
            if self.vector_memory:
                try:
                    self.vector_memory.add_fact(f"Q: {q} A: {a}", tags=["user_taught", "custom_qa"])
                except Exception:
                    pass
            return f"Learnt: when asked '{q}' I'll answer: '{a}'. This will be remembered next time."

        m = re.match(r"^add intent:\s*(\w+)\s*patterns?\s*:\s*\[([^\]]+)\]\s*responses?\s*:\s*\[([^\]]*)\]$", s, re.IGNORECASE)
        if m:
            intent = m.group(1).strip()
            patterns = [p.strip().strip("\"' ") for p in m.group(2).split(",")]
            responses = [p.strip().strip("\"' ") for p in m.group(3).split(",") if p.strip()]
            self.learner.add_custom_intent(intent, patterns, responses=responses)
            self.learner.retrain_classifier(force=False)
            return f"New intent '{intent}' added with {len(patterns)} pattern(s) and classifier refreshed."

        if low in ("learn status", "learning status", "learning report", "what have you learned"):
            s_ = self.learner.summarize_learning()
            vm_count = self.vector_memory.count() if self.vector_memory else 0
            return (
                f"Learning summary: "
                f"{s_['custom_qa_entries']} Q&A entries, "
                f"{s_['custom_intents']} custom intents, "
                f"{s_['feedback_count']} feedback records stored. "
                f"Long-term vector memory: {vm_count} indexed items."
            )

        if low in ("system info", "my system", "computer specs", "pc info"):
            info = self.pc.system_info()
            hours, rem = divmod(info["uptime_seconds"], 3600)
            mins, _ = divmod(rem, 60)
            return (
                f"System: {info['os']} on {info['node']} ({info['arch']}). "
                f"CPU: {info['cores_logical']} logical cores ({info.get('cpu_percent','?')}% used). "
                f"RAM: {info['ram_used_gb']}/{info['ram_total_gb']} GB ({info['ram_percent']}%). "
                f"Disk: {info['disk_used_gb']}/{info['disk_total_gb']} GB ({info['disk_percent']}%). "
                f"Uptime: {hours}h {mins}m. Booted: {info['booted']}."
            )

        if low in ("processes", "running apps", "top processes", "task list"):
            procs = self.pc.list_running_processes(limit=10)
            lines = [f"{i+1}. {p['name']} (PID {p['pid']}) — {p['mem_mb']} MB" for i, p in enumerate(procs)]
            return "Top processes by memory:\n" + "\n".join(lines)

        if low in ("reminders", "my reminders", "list reminders", "show reminders"):
            sr = self.skill_handler.handle("show_reminders", low, context={})
            return sr.get("text", "") if sr else ""

        m2 = re.match(r"^switch (?:to )?(user|profile):?\s*(.+)$", low)
        if m2:
            uid = m2.group(2).strip()
            if self.user_profiles.get_profile(uid):
                self.current_user_id = uid
                prof = self.user_profiles.get_profile(uid) or {}
                return f"Switched to profile: {prof.get('name')} ({uid}). Role: {prof.get('role')}. Language: {prof.get('language')}."
            return f"Profile '{uid}' not found. Available: {', '.join(p['id'] for p in self.user_profiles.list_profiles())}"

        if low in ("profiles", "list profiles", "users", "my profile"):
            items = self.user_profiles.list_profiles()
            cur = self.current_user_id
            return "User profiles:\n" + "\n".join(
                f"  - {i['id']} ({i['name']}, role={i['role']}){' ← active' if i['id'] == cur else ''}" for i in items
            )

        m3 = re.match(r"^create profile[:]?\s*(\w+)\s*name[:]?\s*([\w ]+?)(?:\s*role[:]?\s*(admin|user|guest))?$", s, re.IGNORECASE)
        if m3:
            uid, name, role = m3.group(1), m3.group(2).strip(), m3.group(3) or "user"
            self.user_profiles.create_profile(uid, name, role=role)
            return f"Created profile '{uid}' ({name}, role={role})."

        if low in ("vector memory", "vector status", "memory stats", "long term memory"):
            if self.vector_memory:
                return f"Long-term vector memory: {self.vector_memory.count()} items indexed (ChromaDB). Top-K retrieval: {self.vector_memory.top_k}, min score {self.vector_memory.min_score}."
            return "Long-term vector memory not enabled."

        if low in ("plugins", "list plugins", "extensions"):
            ps = self.plugin_manager.list_plugins()
            if not ps:
                return "No plugins loaded. Drop .py files into plugins/ folder to install them."
            return "Installed plugins:\n" + "\n".join(
                f"  {p['icon']} {p['name']}: {p['description'][:80]}" for p in ps
            )

        if re.match(r"^(who are you|introduce yourself|tell me about yourself|what are your capabilities)\??$", low):
            return (
                f"I'm {self.name}, a professional personal AI assistant built with Python, ML, and DL. "
                f"My capabilities include:"
                f" 1) Voice interaction with wake-word detection (say '{self.wake_word}')."
                f" 2) Self-thinking agent that chooses the right tool per query (PC control, web search, LLM, weather, maps, file ops, math, system info)."
                f" 3) Broad knowledge across math, physics, chemistry, biology, medicine, engineering, AI/ML/data science, software engineering, humanities, law, finance — via LLMs (GPT-4o, Gemini, Claude) when API keys are set, plus real-time Wikipedia and DuckDuckGo search."
                f" 4) Real-time data: weather (wttr.in), currency rates, world-time per timezone/city, 25+ country database."
                f" 5) PC control: open/close apps, folders/files operations, screenshot, brightness, volume, lock/sleep/shutdown/restart, processes, system info."
                f" 6) Automatic continuous learning: feedback, corrected intents, user-taught Q&A, re-trainable classifier."
                f" 7) Maps, directions, Google/web/YouTube search, WhatsApp messaging."
                f" 8) Persistent conversation memory + LONG-TERM VECTOR MEMORY (ChromaDB) with semantic recall."
                f" 9) Persistent reminders via APScheduler (in X minutes, every weekday, cron schedules)."
                f" 10) Multi-language support: auto-detect input, 50+ Edge TTS voices, translation."
                f" 11) Multi-user profiles with optional face-recognition and role-based permissions."
                f" 12) Plugin/extension system — drop .py files into plugins/ folder."
                f" Type 'help' for commands."
            )

        if low == "help":
            self._print_help()
            return ""

        if low == "clear":
            self.memory.clear()
            return "Conversation memory cleared."

        if low == "clear long term memory":
            if self.vector_memory:
                self.vector_memory.clear()
                return "Long-term vector memory cleared."
            return "Vector memory not enabled."

        if low == "history":
            self._print_history()
            return ""

        if low == "voice on":
            self.use_voice = True
            return "Voice mode enabled."

        if low == "voice off":
            self.use_voice = False
            return "Voice mode disabled."

        if low == "wake word on":
            engine = self.adv_wake or self.wake
            if engine is None:
                return "Voice engine not initialized. Start with --voice flag."
            engine.start(self._on_wake_word)
            return f"Wake-word mode now active. Just say '{self.wake_word}' and I'll listen."

        if low == "wake word off":
            if self.adv_wake:
                self.adv_wake.stop()
            if self.wake:
                self.wake.stop()
            return "Wake-word mode paused."

        return None

    # ------------- CLI modes -------------

    def run_cli(self, mode: str = "text"):
        self.running = True
        greeting = self.greet(speak=self.use_voice)
        print(f"\n{'=' * 70}")
        print(f"   {self.name.upper()} - Professional AI Personal Assistant")
        print(f"   Wake word: '{self.wake_word}' | Mode: {mode.upper()}")
        print(f"   LLM provider ready: {self.llm.has_any_key()} (set keys in .env)")
        print(f"   Vector memory: {'ON (' + str(self.vector_memory.count()) + ' items)' if self.vector_memory else 'OFF'}")
        print(f"   Reminder scheduler: {'ACTIVE' if self.reminder_scheduler._running else 'OFF'} | Profiles: {len(self.user_profiles.list_profiles())}")
        print(f"   Type 'help' for commands | 'who are you' for full capabilities")
        print(f"{'=' * 70}")
        print(f"\n[{self.name}] {greeting}")

        wake_engine = self.adv_wake or self.wake
        if mode == "wake":
            if wake_engine is None:
                print(f"[{self.name}] Wake word mode requires voice engine. Falling back to text mode.")
                mode = "text"
            else:
                wake_engine.start(self._on_wake_word)
                print(f"[{self.name}] Wake word listener started. Say '{self.wake_word}' to wake me up. (Ctrl+C to exit)")

        while self.running:
            try:
                # Pending reminder notifications
                if self._pending_reminders:
                    while self._pending_reminders:
                        r = self._pending_reminders.pop(0)
                        print(f"🔔 Pending reminder noted: {r.get('text')}")

                if mode == "voice":
                    res = self.listen_and_respond()
                    if res and res.get("intent") == "farewell":
                        self.running = False
                    continue
                if mode == "wake":
                    import time as _t
                    _t.sleep(1.0)
                    continue

                prompt = f"\n[You] "
                try:
                    user_input = input(prompt).strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                meta = self.handle_meta_command(user_input)
                if meta is not None:
                    if meta:
                        print(f"[{self.name}] {meta}")
                        if self.use_voice and self.tts:
                            self._speak_smart(meta, self.language)
                    continue

                cmd = user_input.lower()
                if cmd in ("quit", "exit", "bye", "shutdown jarvis", "power down"):
                    farewell = self.chat_text(user_input, speak=self.use_voice)
                    print(f"[{self.name}] {farewell}")
                    self.running = False
                    break

                result = self.process_input(user_input, speak=self.use_voice)
                self._print_response(result)
                self._maybe_ask_feedback(result)

                if result["intent"] == "farewell":
                    self.running = False
                    break

            except KeyboardInterrupt:
                print(f"\n\n[{self.name}] Powering down safely. Have a productive day.")
                self.running = False
                if self.adv_wake:
                    self.adv_wake.stop()
                if self.wake:
                    self.wake.stop()
                try:
                    self.reminder_scheduler.stop()
                except Exception:
                    pass
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"[AIAssistant] CLI loop error: {e}")
                print(f"[{self.name}] Oops, something went wrong: {e}")

        if self.adv_wake:
            self.adv_wake.stop()
        if self.wake:
            self.wake.stop()
        try:
            self.reminder_scheduler.stop()
        except Exception:
            pass

    def _print_help(self):
        plugins = self.plugin_manager.list_plugins()
        plugin_names = ", ".join(p["name"] for p in plugins) if plugins else "(none)"
        print(f"""
[{self.name}] --- Available Commands ---
  help                     Show this help
  history                  Show conversation history
  clear                    Clear conversation memory
  clear long term memory   Clear ChromaDB vector memory
  voice on/off             Toggle speech output
  wake word on/off         Toggle wake-word listener (say '{self.wake_word}' to wake)
  who are you / capabilities   Full system capabilities overview
  system info / pc info    Detailed computer specs & uptime
  processes / task list    Top 10 running processes (by memory)
  retrain model            Force re-train my ML intent classifier
  learning status          What I've learned (Q&A, intents, feedback, vector memory)
  vector memory / memory stats   Long-term memory status
  reminders / my reminders List all scheduled persistent reminders
  plugins / extensions     List installed plugins: {plugin_names}
  profiles / list users    List user profiles
  switch user: ID          Switch to user profile by ID
  create profile: ID name: Name (role: admin/user/guest)

  TEACHING SYNTAX (continuous auto-learning):
    learn: "your question" = "my answer"        Store exact Q&A I must repeat
    teach: <question> means <answer>            Same as above
    correct it: better answer here / intent: X   Mark last answer as wrong; re-train
    add intent: IntentName patterns: ["a","b"] responses: ["r1","r2"]   New trained intent

  NEW CAPABILITIES:
    - "remind me in 30 minutes to..."   "remind me every weekday at 9am to..."
    - "translate hello world to Spanish"  /  "translate good morning to Hindi"
    - "switch to female voice" / "switch to Hindi voice" / "British male voice"
    - "send WhatsApp +91... saying Hi there"
    - Ask anything from last week: vector memory retrieves context automatically.

  EXAMPLES:
    - "open chrome" / "close notepad"
    - "list files in C:\\Users"  / "create folder C:\\Projects\\Demo"
    - "copy report.pdf to D:\\Backup" / "move D:\\old to D:\\archive"
    - "rename photo.jpg to vacation.jpg" / "delete temp.log"
    - "screenshot" / "set brightness to 50" / "volume to 70"
    - "lock screen" / "sleep" / "restart in 10" / "cancel shutdown"
    - "weather in London" / "time in Tokyo" / "convert 100 USD to INR"
    - "capital of India" / "population of Japan" / "country info Brazil"
    - "direction Mumbai to Pune" / "map of cafes near me"
    - "search for quantum entanglement" / "youtube python tutorial"
    - "explain gradient descent" / "derivative of sin(x)" / "what is metformin used for"
    - "tell me a joke" / "what time is it"
""")

    def _print_history(self):
        history = self.memory.get_history()
        if not history:
            print(f"[{self.name}] No conversation history yet.")
            return
        print(f"\n[{self.name}] --- Conversation History ({len(history)} messages) ---")
        for msg in history:
            label = "You" if msg["role"] == "user" else self.name
            print(f"  {label}: {msg['content'][:500]}{'...' if len(msg['content'])>500 else ''}")
        print()
