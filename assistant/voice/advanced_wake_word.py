import os
import re
import sys
import time
import threading
from collections import deque
from typing import Callable, Optional, List, Tuple


class AdvancedWakeWordEngine:
    """Enhanced wake-word engine with VAD, phonetic matching, and optional Porcupine support."""

    def __init__(
        self,
        wake_word: str = "jarvis",
        sensitivity: float = 0.7,
        on_wake: Optional[Callable] = None,
        stt=None,
        access_key: Optional[str] = None,
        use_porcupine: bool = False,
    ):
        self.wake_word = wake_word.lower()
        self.wake_variants = self._build_variants(wake_word)
        self.sensitivity = max(0.2, min(1.0, sensitivity))
        self.on_wake = on_wake
        self.stt = stt
        self.access_key = access_key
        self.use_porcupine = use_porcupine

        self.active = False
        self._thread: Optional[threading.Thread] = None
        self._listening_event = threading.Event()
        self._stop_event = threading.Event()
        self.last_wake_at = 0.0
        self.min_interval_sec = 1.5

        self._audio_buffer: deque = deque(maxlen=30)
        self._porcupine = None
        self._pv_recorder = None
        if use_porcupine and access_key:
            self._init_porcupine()

        self._stats = {"detections": 0, "false_positive_suspected": 0}

    @staticmethod
    def _build_variants(wake_word: str) -> List[str]:
        w = wake_word.lower()
        variants = [
            w,
            f"hey {w}",
            f"okay {w}",
            f"ok {w}",
            f"hi {w}",
            f"yo {w}",
            f"{w} you there",
            f"{w} are you there",
            f"listen {w}",
            f"oi {w}",
        ]
        return variants

    def _init_porcupine(self):
        try:
            import pvporcupine
            from pvrecorder import PvRecorder
            kw = self.wake_word.capitalize()
            keywords = [pvporcupine.KEYWORDS.index(kw.lower())] if kw.lower() in pvporcupine.KEYWORDS else [0]
            self._porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=keywords,
                sensitivities=[self.sensitivity],
            )
            self._pv_recorder = PvRecorder(
                device_index=-1,
                frame_length=self._porcupine.frame_length,
            )
            print(f"[WakeWord] Porcupine initialized with keyword: {kw}")
        except Exception as e:
            print(f"[WakeWord] Porcupine init failed: {e}. Falling back to STT-based detection.")
            self.use_porcupine = False
            self._porcupine = None
            self._pv_recorder = None

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
        if self._phonetic_match(t):
            return True
        if self._fuzzy_match(t):
            return True
        return False

    def _phonetic_match(self, text: str) -> bool:
        try:
            from difflib import SequenceMatcher
            target = self.wake_word
            for word in re.findall(r"\b[a-zA-Z]{2,}\b", text):
                ratio = SequenceMatcher(None, word, target).ratio()
                if ratio >= self.sensitivity:
                    return True
            for variant in self.wake_variants:
                ratio = SequenceMatcher(None, text[: len(variant) + 10], variant).ratio()
                if ratio >= self.sensitivity * 0.95:
                    return True
        except Exception:
            pass
        return False

    def _fuzzy_match(self, text: str) -> bool:
        try:
            from difflib import SequenceMatcher
            for word in text.split():
                ratio = SequenceMatcher(None, word, self.wake_word).ratio()
                if ratio >= self.sensitivity:
                    return True
            for variant in self.wake_variants:
                ratio = SequenceMatcher(None, text, variant).ratio()
                if ratio >= self.sensitivity:
                    return True
        except Exception:
            pass
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
            if self.use_porcupine and self._porcupine and self._pv_recorder:
                self._run_porcupine()
            else:
                self._run_stt_based()

        self._thread = threading.Thread(target=run, name="WakeWord-Listener", daemon=True)
        self._thread.start()
        self.active = True
        return self._thread

    def _run_porcupine(self):
        try:
            self._pv_recorder.start()
            while not self._stop_event.is_set():
                if not self._listening_event.is_set():
                    time.sleep(0.1)
                    continue
                try:
                    pcm = self._pv_recorder.read()
                    keyword_index = self._porcupine.process(pcm)
                    if keyword_index >= 0:
                        now = time.time()
                        if now - self.last_wake_at > self.min_interval_sec:
                            self.last_wake_at = now
                            self._stats["detections"] += 1
                            print(f"\n[WakeWord] Porcupine detected '{self.wake_word}'")
                            if self.on_wake:
                                try:
                                    self.on_wake(self.wake_word)
                                except Exception as e:
                                    print(f"[WakeWord] on_wake callback error: {e}")
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[WakeWord] Porcupine read error: {e}")
                    time.sleep(0.5)
        finally:
            try:
                if self._pv_recorder:
                    self._pv_recorder.stop()
            except Exception:
                pass

    def _run_stt_based(self):
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
                    if now - self.last_wake_at > self.min_interval_sec:
                        self.last_wake_at = now
                        self._stats["detections"] += 1
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

    def stop(self):
        self._stop_event.set()
        self._listening_event.clear()
        self.active = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        try:
            if self._porcupine:
                self._porcupine.delete()
            if self._pv_recorder:
                self._pv_recorder.delete()
        except Exception:
            pass

    def pause(self):
        self._listening_event.clear()

    def resume(self):
        self._listening_event.set()

    def get_stats(self) -> dict:
        return dict(self._stats)

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
