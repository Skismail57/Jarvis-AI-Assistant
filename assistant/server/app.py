import os
import sys
import time
import json
import asyncio
import threading
import datetime as _dt
from pathlib import Path
from typing import Optional, Dict, Any, List

ROOT_DIR_BACK = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR_BACK) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR_BACK))
# LOCAL_PKGS = ROOT_DIR_BACK / "_pkgs"
# if LOCAL_PKGS.is_dir() and str(LOCAL_PKGS) not in sys.path:
#     sys.path.insert(0, str(LOCAL_PKGS))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore
    _PSUTIL_AVAILABLE = False

from ..config import settings, ROOT_DIR, FRONTEND_DIR, DATA_DIR
from ..utils.logger import logger
from .schemas import (
    ChatRequest, ChatResponse, SystemMetrics, SettingsUpdate,
    Reminder, UserProfile, PluginInfo, MemoryStats, AssistantStatus, WsMessage
)
from .auth import (
    login, signup, logout, verify_token, biometric_authenticate, enroll_biometric, check_biometric_enrollment,
    LoginRequest, SignupRequest, BiometricRequest, AuthResponse
)

_assistant_singleton = None
_assistant_singleton_lock = threading.Lock()
_start_time = time.time()
_last_net_io = {"sent": 0, "recv": 0, "ts": time.time()}
_active_ws_chat: List[WebSocket] = []
_active_ws_metrics: List[WebSocket] = []
_metrics_thread: Optional[threading.Thread] = None
_metrics_stop = threading.Event()


def _get_assistant():
    global _assistant_singleton
    with _assistant_singleton_lock:
        if _assistant_singleton is None:
            from ..core.assistant import AIAssistant
            try:
                _assistant_singleton = AIAssistant(
                    name=settings.assistant_name,
                    use_voice=False,
                    enable_agent=settings.enable_agent,
                    enable_wake_word=False,
                )
                logger.info("[Server] AIAssistant singleton initialized")
            except Exception as e:
                logger.error(f"[Server] Failed to init assistant: {e}")
                raise
        return _assistant_singleton


def collect_metrics_once() -> SystemMetrics:
    m = SystemMetrics()
    if not _PSUTIL_AVAILABLE:
        return m
    try:
        m.cpu_percent = float(psutil.cpu_percent(interval=None))
        try:
            freq = psutil.cpu_freq()
            if freq:
                m.cpu_freq_mhz = float(freq.current)
        except Exception:
            pass
        vm = psutil.virtual_memory()
        m.ram_total_gb = round(vm.total / (1024 ** 3), 2)
        m.ram_used_gb = round(vm.used / (1024 ** 3), 2)
        m.ram_percent = float(vm.percent)
        try:
            du = psutil.disk_usage(str(ROOT_DIR))
            m.disk_total_gb = round(du.total / (1024 ** 3), 2)
            m.disk_used_gb = round(du.used / (1024 ** 3), 2)
            m.disk_percent = float(du.percent)
        except Exception:
            pass
        try:
            net = psutil.net_io_counters()
            now = time.time()
            dt = max(now - _last_net_io["ts"], 0.001)
            up_bytes = max(net.bytes_sent - _last_net_io["sent"], 0)
            dn_bytes = max(net.bytes_recv - _last_net_io["recv"], 0)
            m.net_up_mbps = round((up_bytes * 8) / (dt * 1_000_000), 2)
            m.net_down_mbps = round((dn_bytes * 8) / (dt * 1_000_000), 2)
            _last_net_io["sent"] = net.bytes_sent
            _last_net_io["recv"] = net.bytes_recv
            _last_net_io["ts"] = now
        except Exception:
            pass
        m.uptime_seconds = round(time.time() - _start_time, 2)
        try:
            m.process_count = len(psutil.pids())
        except Exception:
            m.process_count = 0
        try:
            lavg = psutil.getloadavg()
            m.load_avg = [round(x, 2) for x in lavg]
        except Exception:
            m.load_avg = [0.0, 0.0, 0.0]
    except Exception as e:
        logger.debug(f"[Server] Metrics error: {e}")
    return m


def _metrics_worker():
    global _active_ws_metrics
    while not _metrics_stop.is_set():
        try:
            m = collect_metrics_once()
            payload = json.dumps(m.model_dump())
            for ws in list(_active_ws_metrics):
                try:
                    asyncio.run_coroutine_threadsafe(ws.send_text(payload), ws.app.state.loop)
                except Exception:
                    pass
        except Exception:
            pass
        _metrics_stop.wait(1.5)


async def _broadcast_ws_chat(msg: WsMessage):
    payload = json.dumps(msg.model_dump())
    for ws in list(_active_ws_chat):
        try:
            await ws.send_text(payload)
        except Exception:
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="JARVIS AI Assistant API",
        version="2.0.0",
        description="Real-time JARVIS backend with WebSockets for chat and metrics streaming.",
    )
    app.state.loop = asyncio.get_event_loop()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    dist_dir = FRONTEND_DIR / "dist"
    if dist_dir.is_dir():
        app.mount("/app", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    @app.on_event("startup")
    async def on_startup():
        global _metrics_thread, _assistant_singleton
        try:
            loop = asyncio.get_running_loop()
            app.state.loop = loop
        except Exception:
            pass
        _metrics_stop.clear()
        if _metrics_thread is None or not _metrics_thread.is_alive():
            _metrics_thread = threading.Thread(target=_metrics_worker, daemon=True)
            _metrics_thread.start()
        threading.Thread(target=lambda: _get_assistant(), daemon=True).start()

    @app.on_event("shutdown")
    async def on_shutdown():
        _metrics_stop.set()
        global _assistant_singleton
        if _assistant_singleton:
            try:
                rs = getattr(_assistant_singleton, "reminder_scheduler", None)
                if rs:
                    rs.stop()
            except Exception:
                pass

    @app.get("/api/health", tags=["system"])
    async def health():
        return {"status": "ok", "uptime_sec": round(time.time() - _start_time, 2)}

    @app.get("/api/status", tags=["system"], response_model=AssistantStatus)
    async def get_status():
        assistant = _get_assistant()
        keys = {
            "openai": bool(settings.openai_api_key),
            "gemini": bool(settings.gemini_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "porcupine": bool(settings.porcupine_access_key),
        }
        features = {
            "vector_memory": bool(getattr(assistant, "vector_memory", None)),
            "reminder_scheduler": bool(getattr(assistant, "reminder_scheduler", None)),
            "agent": bool(settings.enable_agent),
            "face_recognition": bool(settings.enable_face_recognition),
        }
        skills_count = 20
        try:
            handlers = getattr(assistant.skill_handler, "handlers", None) or {}
            skills_count = len(handlers)
        except Exception:
            pass
        plugins = 0
        try:
            plugins = len(assistant.plugin_manager.list_plugins())
        except Exception:
            pass
        return AssistantStatus(
            name=assistant.name,
            mode="idle",
            wake_word=assistant.wake_word,
            active_user_id=assistant.current_user_id,
            language=assistant.language,
            tts_engine=settings.jarvis_tts_engine,
            stt_engine=settings.jarvis_stt_engine,
            llm_model=getattr(getattr(assistant, "llm", None), "current_model", "auto"),
            uptime_seconds=round(time.time() - _start_time, 2),
            plugins_loaded=plugins,
            skills_available=skills_count,
            api_keys_configured=keys,
            features_enabled=features,
        )

    @app.get("/api/metrics", tags=["system"], response_model=SystemMetrics)
    async def get_metrics():
        return collect_metrics_once()

    @app.post("/api/chat", tags=["chat"], response_model=ChatResponse)
    async def chat(req: ChatRequest):
        t0 = time.time()
        assistant = _get_assistant()
        assistant.current_user_id = req.user_id
        raw = assistant.process_input(req.message)
        reply = raw.get("response") or raw.get("text") or "I couldn't generate a response."
        resp = ChatResponse(
            input=req.message,
            response=reply,
            intent=raw.get("intent", "unknown"),
            confidence=float(raw.get("confidence", 0.0)),
            detected_language=raw.get("detected_language"),
            skill_result=raw.get("skill_result"),
            thinking_ms=int((time.time() - t0) * 1000),
        )
        if req.speak:
            try:
                assistant._speak_smart(reply, resp.detected_language)
            except Exception:
                pass
        return resp

    @app.get("/api/settings", tags=["settings"])
    async def get_settings():
        data = settings.model_dump()
        for k in list(data.keys()):
            if "api_key" in k.lower() or "access_key" in k.lower() or "secret" in k.lower():
                if data.get(k):
                    mask = str(data[k])
                    data[k] = mask[:4] + "****" + mask[-2:] if len(mask) > 8 else "****"
        return data

    @app.put("/api/settings", tags=["settings"])
    async def update_settings(upd: SettingsUpdate):
        env_path = ROOT_DIR / ".env"
        lines = []
        existing: Dict[str, str] = {}
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                lines.append(line)
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    existing[k.strip().upper()] = (v.strip().strip('"').strip("'"), len(lines) - 1)
        updates = upd.model_dump(exclude_unset=True)
        for k, v in updates.items():
            env_key = k.upper()
            value_str = ""
            if isinstance(v, bool):
                value_str = "true" if v else "false"
            elif isinstance(v, (int, float)):
                value_str = str(v)
            else:
                value_str = f'"{v}"' if v else ""
            if env_key in existing:
                idx = existing[env_key][1]
                lines[idx] = f"{env_key}={value_str}"
            else:
                lines.append(f"{env_key}={value_str}")
        try:
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception as e:
            raise HTTPException(500, f"Could not write .env: {e}")
        return {"status": "updated", "reload_required": True, "fields": list(updates.keys())}

    @app.get("/api/memory", tags=["memory"], response_model=MemoryStats)
    async def memory_stats():
        assistant = _get_assistant()
        long_count = 0
        vm = getattr(assistant, "vector_memory", None)
        if vm:
            try:
                long_count = int(vm.count())
            except Exception:
                long_count = 0
        size_bytes = 0
        try:
            cdir = Path(settings.chroma_persist_dir)
            if cdir.is_dir():
                size_bytes = sum(p.stat().st_size for p in cdir.rglob("*") if p.is_file())
        except Exception:
            pass
        short = 0
        try:
            short = assistant.memory.count()
        except Exception:
            pass
        return MemoryStats(
            short_term_turns=short,
            long_term_items=long_count,
            long_term_size_bytes=size_bytes,
            top_k=settings.vector_memory_top_k,
            min_score=settings.vector_memory_min_score,
        )

    @app.delete("/api/memory", tags=["memory"])
    async def clear_memory(kind: str = "all"):
        assistant = _get_assistant()
        cleared = []
        if kind in ("all", "short"):
            try:
                assistant.memory.clear()
                cleared.append("short_term")
            except Exception:
                pass
        if kind in ("all", "long"):
            vm = getattr(assistant, "vector_memory", None)
            if vm:
                try:
                    vm.clear()
                    cleared.append("long_term")
                except Exception:
                    pass
        return {"cleared": cleared}

    @app.get("/api/reminders", tags=["reminders"])
    async def list_reminders():
        assistant = _get_assistant()
        rs = getattr(assistant, "reminder_scheduler", None)
        if not rs:
            return {"reminders": []}
        out = []
        for r in rs.list_reminders(include_fired=True):
            out.append(Reminder(
                id=r["id"], text=r.get("text", ""), fire_at=r.get("fire_at"),
                recurrence=r.get("recurrence"), interval_seconds=r.get("interval_seconds"),
                cron=r.get("cron"), fired=bool(r.get("fired")),
                cancelled=bool(r.get("cancelled")), created_at=r.get("created_at", ""),
            ))
        return {"reminders": out, "count": len(out)}

    @app.post("/api/reminders", tags=["reminders"])
    async def add_reminder(text: str, when_natural: str = "in 1 hour"):
        assistant = _get_assistant()
        rs = getattr(assistant, "reminder_scheduler", None)
        if not rs:
            raise HTTPException(503, "Reminder scheduler unavailable (install APScheduler)")
        r = rs.parse_and_add(text, when_natural)
        return {"status": "added", "id": r["id"], "fire_at": r.get("fire_at")}

    @app.delete("/api/reminders/{rid}", tags=["reminders"])
    async def cancel_reminder(rid: str):
        assistant = _get_assistant()
        rs = getattr(assistant, "reminder_scheduler", None)
        if not rs:
            return {"cancelled": False}
        ok = rs.cancel(rid)
        return {"cancelled": ok}

    @app.get("/api/profiles", tags=["profiles"])
    async def list_profiles():
        assistant = _get_assistant()
        return {"profiles": assistant.user_profiles.list_profiles(),
                "active_user_id": assistant.current_user_id}

    @app.post("/api/profiles", tags=["profiles"])
    async def create_profile(p: UserProfile):
        assistant = _get_assistant()
        prof = assistant.user_profiles.create_profile(
            user_id=p.id, name=p.name, role=p.role, language=p.language,
            tts_voice_gender=p.tts_voice_gender, can_shutdown_pc=p.can_shutdown_pc,
            can_delete_files=p.can_delete_files, email=p.email,
        )
        return {"created": prof["id"], "profile": prof}

    @app.put("/api/profiles/{pid}", tags=["profiles"])
    async def update_profile(pid: str, p: UserProfile):
        assistant = _get_assistant()
        ok = assistant.user_profiles.update_profile(pid, **p.model_dump(exclude_unset=True, exclude={"id"}))
        return {"updated": ok}

    @app.post("/api/profiles/{pid}/activate", tags=["profiles"])
    async def activate_profile(pid: str):
        assistant = _get_assistant()
        if pid not in assistant.user_profiles.profiles:
            raise HTTPException(404, f"Profile {pid} not found")
        assistant.current_user_id = pid
        prof = assistant.user_profiles.get_profile(pid)
        assistant.language = prof.get("language", assistant.language)
        return {"active": pid, "profile": prof}

    @app.get("/api/plugins", tags=["plugins"], response_model=List[PluginInfo])
    async def list_plugins():
        assistant = _get_assistant()
        out = []
        for plug in assistant.plugin_manager.list_plugins():
            out.append(PluginInfo(
                name=plug["name"], icon=plug.get("icon", "🧩"),
                examples=plug.get("examples", []),
                intent_patterns=[getattr(p, "pattern", str(p)) for p in plug.get("compiled_patterns", [])],
            ))
        return out

    @app.post("/api/skills/retrain", tags=["skills"])
    async def retrain_classifier():
        from ..nlp.intent_classifier import IntentClassifier
        model_path = ROOT_DIR / "models" / "intent_classifier.pkl"
        data_path = ROOT_DIR / "models" / "intents_data.pkl"
        for p in (model_path, data_path):
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        clf = IntentClassifier()
        return {"status": "retrained", "classes": sorted(list(set(clf._labels)))}

    # Authentication endpoints
    @app.post("/api/auth/login", tags=["auth"])
    async def auth_login(request: LoginRequest):
        """Handle user login with username and password."""
        result = await login(request)
        return result.model_dump()

    @app.post("/api/auth/signup", tags=["auth"])
    async def auth_signup(request: SignupRequest):
        """Handle user registration."""
        result = await signup(request)
        return result.model_dump()

    @app.post("/api/auth/logout", tags=["auth"])
    async def auth_logout(token: str):
        """Handle user logout."""
        result = await logout(token)
        return result.model_dump()

    @app.get("/api/auth/verify", tags=["auth"])
    async def auth_verify(token: str):
        """Verify if a token is valid."""
        result = await verify_token(token)
        return result.model_dump()

    @app.post("/api/auth/biometric", tags=["auth"])
    async def auth_biometric(request: BiometricRequest):
        """Handle biometric authentication (face/voice)."""
        result = await biometric_authenticate(request)
        return result.model_dump()

    @app.post("/api/auth/enroll", tags=["auth"])
    async def auth_enroll(username: str, auth_method: str, features: list):
        """Enroll biometric data for a user."""
        result = await enroll_biometric(username, auth_method, features)
        return result.model_dump()

    @app.post("/api/auth/check-biometric", tags=["auth"])
    async def auth_check_biometric(username: str):
        """Check if user has biometric enrollment."""
        result = await check_biometric_enrollment(username)
        return result

    @app.websocket("/ws/chat")
    async def ws_chat(ws: WebSocket):
        await ws.accept()
        _active_ws_chat.append(ws)
        assistant = _get_assistant()
        try:
            while True:
                data = await ws.receive_text()
                try:
                    payload = json.loads(data)
                except Exception:
                    payload = {"message": data}
                user_msg = payload.get("message", "")
                user_id = payload.get("user_id", assistant.current_user_id)
                if not user_msg:
                    continue
                assistant.current_user_id = user_id
                start = WsMessage(type="start", content="", data={"message": user_msg})
                await ws.send_text(json.dumps(start.model_dump()))
                loop = asyncio.get_running_loop()
                result_future = loop.run_in_executor(None, lambda: assistant.process_input(user_msg))
                raw = await result_future
                reply = raw.get("response") or raw.get("text") or "I have no answer."
                for i, ch in enumerate(reply):
                    tok = WsMessage(type="token", content=ch, data={"pos": i})
                    await ws.send_text(json.dumps(tok.model_dump()))
                    await asyncio.sleep(0.005)
                end = WsMessage(type="end", content=reply, data={
                    "intent": raw.get("intent", "unknown"),
                    "confidence": float(raw.get("confidence", 0.0)),
                    "detected_language": raw.get("detected_language"),
                    "skill_result": raw.get("skill_result"),
                })
                await ws.send_text(json.dumps(end.model_dump()))
        except WebSocketDisconnect:
            pass
        finally:
            if ws in _active_ws_chat:
                _active_ws_chat.remove(ws)

    @app.websocket("/ws/metrics")
    async def ws_metrics(ws: WebSocket):
        await ws.accept()
        _active_ws_metrics.append(ws)
        try:
            while True:
                m = collect_metrics_once()
                await ws.send_text(json.dumps(m.model_dump()))
                await asyncio.sleep(1.5)
        except WebSocketDisconnect:
            pass
        finally:
            if ws in _active_ws_metrics:
                _active_ws_metrics.remove(ws)

    @app.get("/", tags=["root"])
    async def root():
        dist_dir = FRONTEND_DIR / "dist"
        if dist_dir.is_dir():
            return {"hint": "Frontend built — visit /app/"}
        return {
            "name": "JARVIS AI Assistant",
            "version": "2.0.0",
            "docs": "/docs",
            "api_base": "/api",
            "ws_chat": "/ws/chat",
            "ws_metrics": "/ws/metrics",
            "frontend_hint": "Run: cd frontend ; npm install ; npm run dev",
        }

    return app


_fastapi_app_singleton: Optional[FastAPI] = None


def get_app() -> FastAPI:
    global _fastapi_app_singleton
    if _fastapi_app_singleton is None:
        _fastapi_app_singleton = create_app()
    return _fastapi_app_singleton
