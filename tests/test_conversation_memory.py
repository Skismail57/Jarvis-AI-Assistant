import json
import pytest


def test_add_user_and_assistant(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=10, storage_path=tmp_conversation_path)
    cm.clear()
    cm.add_user("Hello there")
    cm.add_assistant("Hi! How can I help?")
    assert cm.count() == 2
    hist = cm.get_history()
    assert hist[0]["role"] == "user"
    assert hist[0]["content"] == "Hello there"
    assert hist[1]["role"] == "assistant"
    assert hist[1]["content"] == "Hi! How can I help?"
    for msg in hist:
        assert "timestamp" in msg


def test_get_recent_context_turns(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=20, storage_path=tmp_conversation_path)
    cm.clear()
    for i in range(6):
        cm.add_user(f"User msg {i}")
        cm.add_assistant(f"Assistant reply {i}")
    ctx = cm.get_recent_context(turns=2)
    lines = [l for l in ctx.split("\n") if l.strip()]
    assert len(lines) == 4
    assert "User msg 4" in ctx
    assert "Assistant reply 4" in ctx
    assert "User msg 5" in ctx
    assert "Assistant reply 5" in ctx


def test_get_recent_context_zero_turns(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=10, storage_path=tmp_conversation_path)
    cm.clear()
    cm.add_user("Hello")
    assert cm.get_recent_context(turns=0) == ""
    assert cm.get_recent_context(turns=-5) == ""


def test_get_last(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=10, storage_path=tmp_conversation_path)
    cm.clear()
    assert cm.get_last() is None
    cm.add_user("First")
    cm.add_assistant("Reply one")
    cm.add_user("Second")
    last = cm.get_last()
    assert last["role"] == "user"
    assert last["content"] == "Second"
    last_assistant = cm.get_last(role="assistant")
    assert last_assistant["role"] == "assistant"
    assert last_assistant["content"] == "Reply one"
    assert cm.get_last(role="nonexistent") is None


def test_count_and_clear(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=10, storage_path=tmp_conversation_path)
    cm.clear()
    for i in range(5):
        cm.add_user(f"msg {i}")
    assert cm.count() == 5
    cm.clear()
    assert cm.count() == 0
    assert cm.context == {}


def test_search_keyword(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=20, storage_path=tmp_conversation_path)
    cm.clear()
    cm.add_user("What's the weather in Paris?")
    cm.add_assistant("Paris weather is sunny")
    cm.add_user("Tell me about Python programming")
    cm.add_assistant("Python is a great language")
    results = cm.search("python")
    assert len(results) == 2
    for r in results:
        assert "python" in r["content"].lower()
    weather_results = cm.search("paris")
    assert len(weather_results) == 2


def test_search_no_match(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=10, storage_path=tmp_conversation_path)
    cm.clear()
    cm.add_user("Hello world")
    assert cm.search("zzzzz") == []


def test_export_and_import_via_load(tmp_conversation_path, tmp_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=10, storage_path=tmp_conversation_path)
    cm.clear()
    cm.add_user("Import test question")
    cm.add_assistant("Import test answer")
    cm.set_context("topic", "testing")

    export_path = cm.export()
    assert export_path == tmp_conversation_path

    alt_export = tmp_path / "alt_export.json"
    path2 = cm.export(output_path=str(alt_export))
    assert Path(path2).exists()
    with open(alt_export, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "history" in data
    assert "context" in data
    assert "exported_at" in data
    assert len(data["history"]) == 2
    assert data["context"]["topic"] == "testing"

    cm2 = ConversationMemory(max_history=10, storage_path=str(alt_export))
    assert cm2.count() == 2
    assert cm2.get_context("topic") == "testing"
    assert cm2.get_last()["content"] == "Import test answer"


def test_max_history_enforced(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=3, storage_path=tmp_conversation_path)
    cm.clear()
    for i in range(5):
        cm.add_user(f"msg {i}")
    assert cm.count() == 3
    hist = cm.get_history()
    assert hist[0]["content"] == "msg 2"
    assert hist[2]["content"] == "msg 4"


def test_add_with_metadata(tmp_conversation_path):
    from assistant.memory.conversation_memory import ConversationMemory
    cm = ConversationMemory(max_history=10, storage_path=tmp_conversation_path)
    cm.clear()
    cm.add_user("hello", metadata={"source": "voice", "confidence": 0.95})
    last = cm.get_last()
    assert last["metadata"]["source"] == "voice"
    assert last["metadata"]["confidence"] == pytest.approx(0.95)


from pathlib import Path
