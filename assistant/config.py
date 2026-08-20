import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
LOGS_DIR = ROOT_DIR / "logs"
PLUGINS_DIR = ROOT_DIR / "plugins"
FRONTEND_DIR = ROOT_DIR / "frontend"

for d in (DATA_DIR, MODELS_DIR, LOGS_DIR, PLUGINS_DIR):
    d.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    porcupine_access_key: Optional[str] = None

    jarvis_wake_sensitivity: float = Field(default=0.65, ge=0.0, le=1.0)
    jarvis_language: str = "en-US"
    jarvis_tts_engine: str = "pyttsx3"
    jarvis_stt_engine: str = "sr"

    fastapi_host: str = "127.0.0.1"
    fastapi_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

    chroma_persist_dir: str = str(DATA_DIR / "chroma_db")
    chroma_collection_name: str = "jarvis_memory"
    embedding_model: str = "all-MiniLM-L6-v2"

    log_level: str = "INFO"
    log_file: str = str(LOGS_DIR / "jarvis_{time}.log")

    max_conversation_history: int = 200
    vector_memory_top_k: int = 5
    vector_memory_min_score: float = 0.35

    reminder_db_path: str = str(DATA_DIR / "reminders.json")
    user_profiles_path: str = str(DATA_DIR / "user_profiles.json")
    custom_qa_path: str = str(DATA_DIR / "custom_qa.json")

    default_tts_voice: str = "en-US-ChristopherNeural"
    default_tts_rate: int = 200
    default_tts_volume: float = 1.0

    face_recognition_tolerance: float = 0.6
    face_encodings_path: str = str(DATA_DIR / "face_encodings.pkl")

    wake_word: str = "jarvis"
    assistant_name: str = "Jarvis"
    confidence_threshold: float = 0.20

    enable_agent: bool = True
    enable_vector_memory: bool = True
    enable_face_recognition: bool = False

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        vv = v.upper()
        if vv not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return vv


settings = Settings()
