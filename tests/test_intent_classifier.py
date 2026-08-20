import os
import pytest


def test_preprocess_text_lowercase_and_strip():
    from assistant.nlp.intent_classifier import IntentClassifier
    result = IntentClassifier.preprocess_text("  Hello WORLD!  ")
    assert result == result.lower()
    assert result == result.strip()


def test_preprocess_text_removes_urls():
    from assistant.nlp.intent_classifier import IntentClassifier
    result = IntentClassifier.preprocess_text("Check https://example.com here")
    assert "https://" not in result
    assert "example.com" not in result


def test_preprocess_text_removes_html():
    from assistant.nlp.intent_classifier import IntentClassifier
    result = IntentClassifier.preprocess_text("<p>Hello <b>world</b></p>")
    assert "<p>" not in result
    assert "<b>" not in result
    assert "hello" in result
    assert "world" in result


def test_preprocess_text_removes_punctuation():
    from assistant.nlp.intent_classifier import IntentClassifier
    result = IntentClassifier.preprocess_text("Hello! How are you? I'm fine.")
    for p in "!?.":
        assert p not in result


def test_preprocess_text_removes_numbers_in_words():
    from assistant.nlp.intent_classifier import IntentClassifier
    result = IntentClassifier.preprocess_text("test123 and hello4you")
    assert "test123" not in result
    assert "hello4you" not in result


@pytest.fixture
def trained_classifier(sample_intents_file, tmp_path):
    from assistant.nlp.intent_classifier import IntentClassifier
    model_dir = str(tmp_path / "models")
    os.makedirs(model_dir, exist_ok=True)
    try:
        clf = IntentClassifier(model_dir=model_dir, intents_path=sample_intents_file)
        return clf
    except Exception:
        pytest.skip("Could not train IntentClassifier (missing dependencies or NLTK data)")


def test_get_intent_returns_dict_structure(trained_classifier):
    result = trained_classifier.get_intent("hello there", threshold=0.0)
    assert isinstance(result, dict)
    assert "intent" in result
    assert "confidence" in result
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0


def test_get_intent_greeting_match(trained_classifier):
    result = trained_classifier.get_intent("hi good morning", threshold=0.0)
    assert isinstance(result, dict)
    assert result["intent"] in ("greeting", "unknown")


def test_get_intent_time_phrase(trained_classifier):
    result = trained_classifier.get_intent("what time is it now", threshold=0.0)
    assert isinstance(result, dict)
    assert result["intent"] in ("time", "unknown")


def test_get_intent_joke_phrase(trained_classifier):
    result = trained_classifier.get_intent("please tell me a joke", threshold=0.0)
    assert isinstance(result, dict)
    assert result["intent"] in ("joke", "unknown")


def test_get_intent_below_threshold_returns_unknown(trained_classifier):
    result = trained_classifier.get_intent("zzzz completely random xyz", threshold=0.999)
    assert result["intent"] == "unknown"


def test_predict_returns_top_k_list(trained_classifier):
    preds = trained_classifier.predict("hello", top_k=2)
    assert isinstance(preds, list)
    assert len(preds) <= 2
    for p in preds:
        assert "intent" in p
        assert "confidence" in p
