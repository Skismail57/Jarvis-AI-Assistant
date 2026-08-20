import os
import re
import sys
import time
import threading
from typing import Callable, Optional


class WakeWordEngine:
    def __init__(
        self,
        wake_word: str = "jarvis",
        sensitivity: float = 0.7,
        on_wake: Optional[Callable] = None,
        stt=None,
    ):
        self.wake_word = wake_word.lower()
        self.wake_variants = [
            wake_word.lower(),
            "hey " + wake_word.lower(),
            "okay " + wake_word.lower(),
            "ok " + wake_word.lower(),
            "hi " + wake_word.lower(),
            wake_word.lower() + " you there",
            "yo " + wake_word.lower(),
        ]
        self.sensitivity = sensitivity
        self.on_wake = on_wake
        self.stt = stt
        self.active = False
        self._thread: Optional[threading.Thread] = None
        self._listening_event = threading.Event()
        self._stop_event = threading.Event()
        self.last_wake_at = 0.0

    def set_stt(self, stt):
        self.stt = stt

    def contains_wake_word(self, text: str) -> bool:
        if not text:
            return False
        t = text.lower().strip()
        for variant in self.wake_variants:
            if variant in t:
                return True
        pattern = r"\b" + re.escape(self.wake_word) + r"\b"
        if re.search(pattern, t):
            return True
        if self._fuzzy_match(t):
            return True
        return False

    def _fuzzy_match(self, text: str) -> bool:
        import difflib
        for word in text.split():
            ratio = difflib.SequenceMatcher(None, word, self.wake_word).ratio()
            if ratio >= self.sensitivity:
                return True
        for variant in self.wake_variants:
            ratio = difflib.SequenceMatcher(None, text, variant).ratio()
            if ratio >= self.sensitivity:
                return True
        return False

    def start(self, callback: Optional[Callable] = None) -> threading.Thread:
        if self._thread and self._thread.is_alive():
            return self._thread
        self._stop_event.clear()
        self._listening_event.set()
        if callback:
            self.on_wake = callback

        def run():
            print(f"[WakeWord] Listening for wake word: '{self.wake_word}'... (press Ctrl+C to stop)")
            while not self._stop_event.is_set():
                if not self._listening_event.is_set():
                    time.sleep(0.2)
                    continue
                try:
                    if self.stt is None:
                        text = self._listen_via_sr()
                    else:
                        text = self.stt.listen_from_microphone(timeout=2, phrase_time_limit=4)
                    if text and self.contains_wake_word(text):
                        now = time.time()
                        if now - self.last_wake_at > 1.5:
                            self.last_wake_at = now
                            print(f"\n[WakeWord] Detected: '{text}'")
                            if self.on_wake:
                                try:
                                    self.on_wake(text)
                                except Exception as e:
                                    print(f"[WakeWord] on_wake callback error: {e}")
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[WakeWord] Listen error: {e}")
                    time.sleep(0.5)

        self._thread = threading.Thread(target=run, name="WakeWord-Listener", daemon=True)
        self._thread.start()
        self.active = True
        return self._thread

    def stop(self):
        self._stop_event.set()
        self._listening_event.clear()
        self.active = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def pause(self):
        self._listening_event.clear()

    def resume(self):
        self._listening_event.set()

    def _listen_via_sr(self) -> Optional[str]:
        try:
            import speech_recognition as sr
        except ImportError:
            return None
        try:
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 250
            recognizer.pause_threshold = 0.6
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=4)
            try:
                return recognizer.recognize_google(audio, language="en-US").strip()
            except Exception:
                return None
        except Exception:
            return None
