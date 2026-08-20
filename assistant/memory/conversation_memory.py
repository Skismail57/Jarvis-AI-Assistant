import json
import os
import datetime
from typing import List, Dict, Any, Optional
from collections import deque


class ConversationMemory:
    def __init__(self, max_history: int = 50, storage_path: str = None):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_path = storage_path or os.path.join(self.base_dir, "data", "conversation_memory.json")
        self.context: Dict[str, Any] = {}
        self._load()

    def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.history.append(message)
        self._persist()

    def add_user(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.add("user", content, metadata)

    def add_assistant(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.add("assistant", content, metadata)

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        items = list(self.history)
        if limit:
            return items[-limit:]
        return items

    def get_recent_context(self, turns: int = 5) -> str:
        if turns <= 0:
            return ""
        recent = list(self.history)[-turns * 2:]
        parts = []
        for msg in recent:
            label = "User" if msg["role"] == "user" else "Assistant"
            parts.append(f"{label}: {msg['content']}")
        return "\n".join(parts)

    def get_last(self, role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.history:
            return None
        if role is None:
            return self.history[-1]
        for msg in reversed(self.history):
            if msg["role"] == role:
                return msg
        return None

    def clear(self):
        self.history.clear()
        self.context.clear()
        self._persist()

    def set_context(self, key: str, value: Any):
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    def pop_context(self, key: str, default: Any = None) -> Any:
        return self.context.pop(key, default)

    def count(self) -> int:
        return len(self.history)

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        keyword_lower = keyword.lower()
        return [msg for msg in self.history if keyword_lower in msg["content"].lower()]

    def export(self, output_path: Optional[str] = None) -> str:
        path = output_path or self.storage_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "exported_at": datetime.datetime.now().isoformat(),
            "max_history": self.max_history,
            "history": list(self.history),
            "context": self.context
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def _persist(self):
        try:
            self.export()
        except Exception as e:
            print(f"[ConversationMemory] Warning: Could not persist memory: {e}")

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                hist = data.get("history", [])
                for msg in hist[-self.max_history:]:
                    self.history.append(msg)
                self.context = data.get("context", {})
                print(f"[ConversationMemory] Loaded {len(self.history)} message(s) from disk.")
            except Exception as e:
                print(f"[ConversationMemory] Warning: Could not load memory: {e}")
                self.history.clear()
                self.context.clear()
