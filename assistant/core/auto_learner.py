import os
import json
import time
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime


class AutoLearner:
    def __init__(self, assistant_ref):
        self.assistant = assistant_ref
        self.base_dir = assistant_ref.base_dir if hasattr(assistant_ref, "base_dir") else os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.feedback_path = os.path.join(self.base_dir, "data", "feedback.json")
        self.custom_intents_path = os.path.join(self.base_dir, "data", "custom_intents.json")
        self.custom_qa_path = os.path.join(self.base_dir, "data", "custom_qa.json")
        self._ensure_files()
        self._lock = threading.Lock()

    def _ensure_files(self):
        for p in (self.feedback_path, self.custom_intents_path, self.custom_qa_path):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if not os.path.exists(p):
                with open(p, "w", encoding="utf-8") as f:
                    if p.endswith("custom_qa.json"):
                        json.dump({"entries": []}, f, indent=2, ensure_ascii=False)
                    else:
                        json.dump([], f, indent=2, ensure_ascii=False)

    # --- Feedback-driven learning ---
    def record_feedback(self, query: str, response: str, intent: str, confidence: float,
                        was_correct: Optional[bool] = None, expected_intent: Optional[str] = None,
                        better_answer: Optional[str] = None, user_comment: Optional[str] = None):
        item = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "was_correct": was_correct,
            "expected_intent": expected_intent,
            "better_answer": better_answer,
            "user_comment": user_comment,
        }
        with self._lock:
            try:
                with open(self.feedback_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []
            data.append(item)
            with open(self.feedback_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        # Auto-repair low-confidence or known-wrong intents by adding as training pattern
        if expected_intent and was_correct is False:
            self._add_pattern_to_intents(expected_intent, query)
        if better_answer:
            self.add_custom_qa(query, better_answer, tags=["user_corrected"])

    def _add_pattern_to_intents(self, intent: str, pattern: str):
        base_intents = self.assistant.classifier.intents_path
        with open(base_intents, "r", encoding="utf-8") as f:
            data = json.load(f)
        matched = False
        for item in data:
            if item["intent"] == intent:
                if pattern.lower() not in [p.lower() for p in item["patterns"]]:
                    item["patterns"].append(pattern)
                matched = True
                break
        if not matched:
            data.append({
                "intent": intent,
                "patterns": [pattern],
                "responses": []
            })
        with open(base_intents, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_custom_intent(self, intent: str, patterns: List[str], responses: Optional[List[str]] = None,
                          action_handler: Optional[str] = None):
        with self._lock:
            try:
                with open(self.custom_intents_path, "r", encoding="utf-8") as f:
                    custom = json.load(f)
            except Exception:
                custom = []
            existing = next((c for c in custom if c["intent"] == intent), None)
            if existing:
                existing["patterns"] = list(set(existing["patterns"] + patterns))
                if responses:
                    existing["responses"] = list(set(existing.get("responses", []) + responses))
                if action_handler:
                    existing["action"] = action_handler
            else:
                custom.append({
                    "intent": intent,
                    "patterns": patterns,
                    "responses": responses or [],
                    "action": action_handler or "",
                    "created_at": datetime.now().isoformat()
                })
            with open(self.custom_intents_path, "w", encoding="utf-8") as f:
                json.dump(custom, f, indent=2, ensure_ascii=False)
            # Also write to main intents to be included on next retrain
            self._merge_custom_into_main()
            return True

    def _merge_custom_into_main(self):
        try:
            with open(self.custom_intents_path, "r", encoding="utf-8") as f:
                custom = json.load(f)
            with open(self.assistant.classifier.intents_path, "r", encoding="utf-8") as f:
                main = json.load(f)
            main_intents = {item["intent"]: item for item in main}
            for c in custom:
                if c["intent"] in main_intents:
                    m = main_intents[c["intent"]]
                    m["patterns"] = list(set(m["patterns"] + c["patterns"]))
                    if c.get("responses"):
                        m["responses"] = list(set(m["responses"] + c["responses"]))
                else:
                    main.append({
                        "intent": c["intent"],
                        "patterns": c["patterns"],
                        "responses": c.get("responses", [])
                    })
            with open(self.assistant.classifier.intents_path, "w", encoding="utf-8") as f:
                json.dump(main, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AutoLearner] Merge error: {e}")

    def add_custom_qa(self, question: str, answer: str, tags: Optional[List[str]] = None):
        with self._lock:
            try:
                with open(self.custom_qa_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {"entries": []}
            entries = data.get("entries", [])
            entries.append({
                "q": question.strip(),
                "a": answer.strip(),
                "tags": tags or [],
                "created_at": datetime.now().isoformat()
            })
            data["entries"] = entries
            with open(self.custom_qa_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True

    def lookup_custom_qa(self, question: str, threshold: float = 0.75) -> Optional[Dict[str, Any]]:
        try:
            with open(self.custom_qa_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None
        entries = data.get("entries", [])
        if not entries:
            return None
        q = question.lower()
        import difflib
        best = None
        best_score = 0.0
        for e in entries:
            eq = e["q"].lower()
            score = difflib.SequenceMatcher(None, q, eq).ratio()
            if score > best_score:
                best_score = score
                best = e
        if best and best_score >= threshold:
            return {"match": best, "score": best_score}
        return None

    def retrain_classifier(self, force: bool = False):
        try:
            self._merge_custom_into_main()
        except Exception:
            pass
        import os as _os
        mp = self.assistant.classifier.model_path
        dp = self.assistant.classifier.intents_data_path
        if force:
            for p in (mp, dp):
                if _os.path.exists(p):
                    _os.remove(p)
        from ..nlp.intent_classifier import IntentClassifier
        self.assistant.classifier = IntentClassifier(
            model_dir=self.assistant.classifier.model_dir,
            intents_path=self.assistant.classifier.intents_path,
        )
        return True

    def summarize_learning(self) -> Dict[str, Any]:
        def count(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, list):
                    return len(d)
                if isinstance(d, dict) and "entries" in d:
                    return len(d["entries"])
                return 0
            except Exception:
                return 0
        return {
            "feedback_count": count(self.feedback_path),
            "custom_intents": count(self.custom_intents_path),
            "custom_qa_entries": count(self.custom_qa_path),
            "feedback_file": self.feedback_path,
            "custom_intents_file": self.custom_intents_path,
            "custom_qa_file": self.custom_qa_path,
        }
