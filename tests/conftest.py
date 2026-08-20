import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PKGS_DIR = PROJECT_ROOT / "_pkgs"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PKGS_DIR) not in sys.path:
    sys.path.insert(0, str(PKGS_DIR))


@pytest.fixture
def tmp_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def tmp_conversation_path(tmp_data_dir):
    return str(tmp_data_dir / "conversation_memory.json")


@pytest.fixture
def tmp_reminder_db_path(tmp_data_dir):
    return str(tmp_data_dir / "reminders.json")


@pytest.fixture
def tmp_vector_persist_dir(tmp_data_dir):
    d = tmp_data_dir / "chroma_db"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


@pytest.fixture
def tmp_profiles_path(tmp_data_dir):
    return str(tmp_data_dir / "user_profiles.json")


@pytest.fixture
def tmp_encodings_path(tmp_data_dir):
    return str(tmp_data_dir / "face_encodings.pkl")


@pytest.fixture
def tmp_plugins_dir(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    init = plugins_dir / "__init__.py"
    init.write_text("", encoding="utf-8")
    return str(plugins_dir)


@pytest.fixture
def mock_assistant():
    assistant = MagicMock()
    assistant.name = "Jarvis"
    assistant.config = MagicMock()
    assistant.memory = MagicMock()
    return assistant


@pytest.fixture
def sample_intents_file(tmp_data_dir):
    intents = [
        {
            "intent": "greeting",
            "patterns": ["hello", "hi", "hey there", "good morning"],
            "responses": ["Hello!", "Hi there!"]
        },
        {
            "intent": "time",
            "patterns": ["what time is it", "current time", "tell me the time"],
            "responses": ["The time is now."]
        },
        {
            "intent": "joke",
            "patterns": ["tell me a joke", "make me laugh", "joke please"],
            "responses": ["Why did the chicken cross the road?"]
        },
        {
            "intent": "name",
            "patterns": ["what is your name", "who are you", "your name"],
            "responses": ["I'm Jarvis."]
        },
        {
            "intent": "date",
            "patterns": ["what day is it", "current date", "today's date"],
            "responses": ["Today is."]
        }
    ]
    path = tmp_data_dir / "intents.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(intents, f, ensure_ascii=False, indent=2)
    return str(path)
