import pytest
from pydantic import ValidationError


def test_settings_defaults_load():
    from assistant.config import Settings
    s = Settings()
    assert s.jarvis_wake_sensitivity == pytest.approx(0.65)
    assert s.jarvis_language == "en-US"
    assert s.fastapi_port == 8000
    assert s.max_conversation_history == 200
    assert s.vector_memory_top_k == 5
    assert s.wake_word == "jarvis"
    assert s.assistant_name == "Jarvis"
    assert s.confidence_threshold == pytest.approx(0.20)
    assert s.enable_agent is True
    assert s.enable_vector_memory is True
    assert isinstance(s.cors_origins, list)
    assert len(s.cors_origins) > 0


def test_settings_wake_sensitivity_bounds():
    from assistant.config import Settings
    with pytest.raises(ValidationError):
        Settings(jarvis_wake_sensitivity=1.5)
    with pytest.raises(ValidationError):
        Settings(jarvis_wake_sensitivity=-0.1)


def test_settings_log_level_validator_valid():
    from assistant.config import Settings
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "info", "debug"]:
        s = Settings(log_level=level)
        assert s.log_level == level.upper()


def test_settings_log_level_validator_invalid():
    from assistant.config import Settings
    with pytest.raises(ValidationError):
        Settings(log_level="NOT_A_LEVEL")


def test_settings_cors_origins_is_list():
    from assistant.config import Settings
    s = Settings(cors_origins=["http://a.com"])
    assert s.cors_origins == ["http://a.com"]


def test_settings_numeric_fields_types():
    from assistant.config import Settings
    s = Settings(
        max_conversation_history=100,
        vector_memory_top_k=3,
        vector_memory_min_score=0.5,
        default_tts_rate=180,
        default_tts_volume=0.7,
        face_recognition_tolerance=0.5,
    )
    assert isinstance(s.max_conversation_history, int)
    assert isinstance(s.vector_memory_top_k, int)
    assert isinstance(s.vector_memory_min_score, float)
    assert isinstance(s.default_tts_rate, int)
    assert isinstance(s.default_tts_volume, float)
    assert isinstance(s.face_recognition_tolerance, float)


def test_settings_singleton_instance_exists():
    from assistant.config import settings
    assert settings is not None
    assert isinstance(settings.jarvis_language, str)
