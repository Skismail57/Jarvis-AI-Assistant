from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User's text message")
    user_id: str = Field(default="default", description="Active user profile ID")
    speak: bool = Field(default=False, description="If true, assistant will TTS the reply server-side")
    mode: Literal["text", "voice"] = Field(default="text")
    stream: bool = Field(default=True, description="If true, stream response tokens over WS")


class ChatResponse(BaseModel):
    input: str
    response: str
    intent: str = "unknown"
    confidence: float = 0.0
    detected_language: Optional[str] = None
    skill_result: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    thinking_ms: Optional[int] = None


class WsMessage(BaseModel):
    type: Literal["token", "start", "end", "error", "status", "wake"]
    content: str = ""
    data: Optional[Dict[str, Any]] = None


class SystemMetrics(BaseModel):
    cpu_percent: float = 0.0
    cpu_freq_mhz: Optional[float] = None
    ram_total_gb: float = 0.0
    ram_used_gb: float = 0.0
    ram_percent: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    net_up_mbps: float = 0.0
    net_down_mbps: float = 0.0
    uptime_seconds: float = 0.0
    process_count: int = 0
    load_avg: List[float] = [0.0, 0.0, 0.0]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SettingsUpdate(BaseModel):
    assistant_name: Optional[str] = None
    wake_word: Optional[str] = None
    jarvis_wake_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    jarvis_language: Optional[str] = None
    jarvis_tts_engine: Optional[Literal["pyttsx3", "gtts", "edge-tts"]] = None
    jarvis_stt_engine: Optional[Literal["sr", "whisper"]] = None
    default_tts_voice: Optional[str] = None
    default_tts_rate: Optional[int] = Field(None, ge=50, le=400)
    enable_agent: Optional[bool] = None
    enable_vector_memory: Optional[bool] = None
    enable_face_recognition: Optional[bool] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    vector_memory_top_k: Optional[int] = Field(None, ge=1, le=50)
    vector_memory_min_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    face_recognition_tolerance: Optional[float] = Field(None, ge=0.3, le=0.9)
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    porcupine_access_key: Optional[str] = None


class Reminder(BaseModel):
    id: str
    text: str
    fire_at: Optional[str] = None
    recurrence: Optional[str] = None
    interval_seconds: Optional[int] = None
    cron: Optional[Dict[str, Any]] = None
    fired: bool = False
    cancelled: bool = False
    created_at: str


class UserProfile(BaseModel):
    id: str
    name: str
    role: Literal["admin", "user", "guest"] = "user"
    language: str = "en-US"
    tts_voice_gender: Literal["male", "female", "neutral"] = "neutral"
    can_shutdown_pc: bool = False
    can_delete_files: bool = False
    email: Optional[str] = None


class PluginInfo(BaseModel):
    name: str
    icon: str
    examples: List[str]
    intent_patterns: List[str]


class MemoryStats(BaseModel):
    short_term_turns: int
    long_term_items: int
    long_term_size_bytes: int = 0
    top_k: int
    min_score: float
    vector_db: str = "chromadb"


class AssistantStatus(BaseModel):
    name: str
    version: str = "2.0.0"
    mode: Literal["idle", "listening", "speaking", "thinking"] = "idle"
    wake_word: str
    active_user_id: str
    language: str
    tts_engine: str
    stt_engine: str
    llm_model: str
    uptime_seconds: float = 0.0
    diagnostics_passed: int = 0
    diagnostics_total: int = 7
    plugins_loaded: int = 0
    skills_available: int = 0
    api_keys_configured: Dict[str, bool] = {}
    features_enabled: Dict[str, bool] = {}
