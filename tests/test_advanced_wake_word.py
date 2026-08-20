import pytest


def test_build_variants_includes_basic_forms():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    variants = AdvancedWakeWordEngine._build_variants("jarvis")
    assert "jarvis" in variants
    assert "hey jarvis" in variants
    assert "okay jarvis" in variants
    assert "ok jarvis" in variants
    assert "hi jarvis" in variants
    assert "yo jarvis" in variants


def test_build_variants_includes_are_you_there():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    variants = AdvancedWakeWordEngine._build_variants("jarvis")
    assert "jarvis you there" in variants
    assert "jarvis are you there" in variants


def test_build_variants_includes_listen_and_oi():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    variants = AdvancedWakeWordEngine._build_variants("jarvis")
    assert "listen jarvis" in variants
    assert "oi jarvis" in variants
    assert len(variants) >= 10


def test_build_variants_is_lowercase():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    variants = AdvancedWakeWordEngine._build_variants("Jarvis")
    for v in variants:
        assert v == v.lower()


def test_build_variants_different_wake_word():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    variants = AdvancedWakeWordEngine._build_variants("alexa")
    assert "alexa" in variants
    assert "hey alexa" in variants
    assert "ok alexa" in variants


def test_contains_wake_word_exact_match():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.7)
    assert engine.contains_wake_word("jarvis") is True
    assert engine.contains_wake_word("Jarvis") is True
    assert engine.contains_wake_word("JARVIS") is True


def test_contains_wake_word_hey_variant():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.7)
    assert engine.contains_wake_word("hey jarvis are you there") is True
    assert engine.contains_wake_word("Hey Jarvis, good morning") is True


def test_contains_wake_word_okay_variant():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.7)
    assert engine.contains_wake_word("okay jarvis what time is it") is True
    assert engine.contains_wake_word("ok jarvis, open browser") is True


def test_contains_wake_word_no_match():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.7)
    assert engine.contains_wake_word("hello computer") is False
    assert engine.contains_wake_word("what time is it") is False


def test_contains_wake_word_empty_or_whitespace():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.7)
    assert engine.contains_wake_word("") is False
    assert engine.contains_wake_word("   ") is False


def test_contains_wake_word_word_boundary_regex():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.7)
    assert engine.contains_wake_word("tell jarvis to start") is True


def test_engine_sensitivity_clamped():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    e1 = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.05)
    assert e1.sensitivity == pytest.approx(0.2)
    e2 = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=2.0)
    assert e2.sensitivity == pytest.approx(1.0)
    e3 = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.5)
    assert e3.sensitivity == pytest.approx(0.5)


def test_engine_init_defaults():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine()
    assert engine.wake_word == "jarvis"
    assert len(engine.wake_variants) >= 10
    assert engine.active is False
    assert isinstance(engine._stats, dict)
    assert engine._stats["detections"] == 0


def test_get_stats_returns_dict():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis")
    stats = engine.get_stats()
    assert isinstance(stats, dict)
    assert "detections" in stats
    assert "false_positive_suspected" in stats


def test_contains_wake_word_hi_yo_variants():
    from assistant.voice.advanced_wake_word import AdvancedWakeWordEngine
    engine = AdvancedWakeWordEngine(wake_word="jarvis", sensitivity=0.7)
    assert engine.contains_wake_word("hi jarvis") is True
    assert engine.contains_wake_word("yo jarvis help me") is True
