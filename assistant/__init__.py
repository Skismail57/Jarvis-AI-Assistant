import sys as _sys
import os as _os

_PKG_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_LOCAL_PKGS = _os.path.join(_PKG_DIR, "_pkgs")
# if _os.path.isdir(_LOCAL_PKGS) and _LOCAL_PKGS not in _sys.path:
#     _sys.path.insert(0, _LOCAL_PKGS)
#     _bin_dir = _os.path.join(_LOCAL_PKGS, "bin")
#     if _os.path.isdir(_bin_dir):
#         _os.environ["PATH"] = _bin_dir + _os.pathsep + _os.environ.get("PATH", "")

from .core.assistant import AIAssistant
from .core.llm_core import LLMCore
from .core.data_provider import DataProvider
from .core.pc_controller import PCController
from .core.agent import JarvisAgent
from .core.auto_learner import AutoLearner
from .nlp.intent_classifier import IntentClassifier
from .voice.stt import SpeechToText
from .voice.tts import TextToSpeech
from .voice.wake_word import WakeWordEngine
from .memory.conversation_memory import ConversationMemory

__version__ = "2.0.0"
__all__ = [
    "AIAssistant", "LLMCore", "DataProvider", "PCController",
    "JarvisAgent", "AutoLearner", "IntentClassifier",
    "SpeechToText", "TextToSpeech", "WakeWordEngine", "ConversationMemory"
]
