import pytest


def test_get_voice_for_locale_en_us_male():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("en-US", gender="male")
    assert voice == "en-US-ChristopherNeural"


def test_get_voice_for_locale_hi_in_female():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("hi-IN", gender="female")
    assert voice == "hi-IN-KalpanaNeural"


def test_get_voice_for_locale_es_es_default():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("es-ES")
    assert voice == "es-ES-AriaNeural" or voice == "es-ES-AlvaroNeural" or voice == "es-ES-ElviraNeural"


def test_get_voice_for_locale_en_us_female():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("en-US", gender="female")
    assert voice == "en-US-JennyNeural"


def test_get_voice_for_locale_en_us_neutral():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("en-US", gender="neutral")
    assert voice == "en-US-AriaNeural"


def test_get_voice_for_locale_short_fallback():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("hi", gender="male")
    assert voice == "hi-IN-MadhurNeural"


def test_get_voice_for_locale_unknown_locale():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("xx-XX", gender="male")
    assert voice == "en-US-ChristopherNeural"


def test_get_voice_for_locale_missing_gender_falls_back():
    from assistant.voice.multilingual import get_voice_for_locale
    voice = get_voice_for_locale("en-GB", gender="neutral")
    assert "en-GB" in voice


def test_list_available_voices_returns_dict():
    from assistant.voice.multilingual import list_available_voices
    voices = list_available_voices()
    assert isinstance(voices, dict)
    assert len(voices) >= 5
    assert "en-US" in voices
    assert "hi-IN" in voices
    assert "es-ES" in voices
    assert "fr-FR" in voices
    for locale, group in voices.items():
        assert isinstance(locale, str)
        assert isinstance(group, dict)
        assert any(k in group for k in ("male", "female", "neutral"))


def test_list_available_voices_en_us_has_three_genders():
    from assistant.voice.multilingual import list_available_voices
    voices = list_available_voices()
    en_us = voices["en-US"]
    assert "male" in en_us
    assert "female" in en_us
    assert "neutral" in en_us
    assert en_us["male"] == "en-US-ChristopherNeural"
    assert en_us["female"] == "en-US-JennyNeural"
    assert en_us["neutral"] == "en-US-AriaNeural"


def test_detect_language_optional():
    from assistant.voice.multilingual import detect_language
    result = detect_language("Hello world")
    assert result is None or isinstance(result, str)


def test_translate_text_optional():
    from assistant.voice.multilingual import translate_text
    result = translate_text("Hello", "es")
    assert isinstance(result, str)
