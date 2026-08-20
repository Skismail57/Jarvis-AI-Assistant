import os
import sys
import tempfile
import threading
from typing import Optional


class TextToSpeech:
    def __init__(self, engine: str = "pyttsx3", language: str = "en", rate: int = 180, volume: float = 1.0):
        self.engine_name = engine.lower()
        self.language = language
        self.rate = rate
        self.volume = volume
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        if self.engine_name == "pyttsx3":
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", self.rate)
                self._engine.setProperty("volume", self.volume)
                voices = self._engine.getProperty("voices")
                if voices:
                    try:
                        for voice in voices:
                            if "english" in voice.name.lower() or "en" in voice.languages:
                                self._engine.setProperty("voice", voice.id)
                                break
                    except Exception:
                        pass
            except ImportError:
                print("[TextToSpeech] pyttsx3 not installed. Install with: pip install pyttsx3")
                self._engine = None
        elif self.engine_name == "gtts":
            try:
                from gtts import gTTS
                self._gtts = gTTS
            except ImportError:
                print("[TextToSpeech] gTTS not installed. Install with: pip install gTTS playsound")
                self._gtts = None

    def set_rate(self, rate: int):
        self.rate = rate
        if self.engine_name == "pyttsx3" and self._engine is not None:
            self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if self.engine_name == "pyttsx3" and self._engine is not None:
            self._engine.setProperty("volume", self.volume)

    def speak(self, text: str, block: bool = True) -> bool:
        if not text or not text.strip():
            return False

        text = text.strip()

        if self.engine_name == "pyttsx3" and self._engine is not None:
            return self._speak_pyttsx3(text, block)
        elif self.engine_name == "gtts" and hasattr(self, "_gtts") and self._gtts is not None:
            return self._speak_gtts(text, block)
        else:
            print(f"[Assistant] {text}")
            return True

    def _speak_pyttsx3(self, text: str, block: bool) -> bool:
        try:
            self._engine.say(text)
            if block:
                self._engine.runAndWait()
            else:
                t = threading.Thread(target=self._engine.runAndWait, daemon=True)
                t.start()
            return True
        except Exception as e:
            print(f"[TextToSpeech] pyttsx3 error: {e}")
            return False

    def _speak_gtts(self, text: str, block: bool) -> bool:
        try:
            tts = self._gtts(text=text, lang=self.language, slow=False)
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp_path = tmp.name
            tmp.close()
            tts.save(tmp_path)

            def play():
                try:
                    if sys.platform == "win32":
                        try:
                            playsound_path = tmp_path.replace("\\", "/")
                            import playsound
                            playsound.playsound(playsound_path)
                        except Exception:
                            os.startfile(tmp_path)
                    elif sys.platform == "darwin":
                        os.system(f"afplay '{tmp_path}'")
                    else:
                        os.system(f"mpg123 -q '{tmp_path}' 2>/dev/null || ffplay -nodisp -autoexit '{tmp_path}' 2>/dev/null")
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

            if block:
                play()
            else:
                t = threading.Thread(target=play, daemon=True)
                t.start()
            return True
        except Exception as e:
            print(f"[TextToSpeech] gTTS error: {e}")
            return False

    def stop(self):
        if self.engine_name == "pyttsx3" and self._engine is not None:
            self._engine.stop()

    def save_to_file(self, text: str, output_path: str) -> bool:
        if not text:
            return False

        try:
            if self.engine_name == "gtts" and hasattr(self, "_gtts"):
                tts = self._gtts(text=text, lang=self.language, slow=False)
                tts.save(output_path)
                return True
            elif self.engine_name == "pyttsx3" and self._engine is not None:
                self._engine.save_to_file(text, output_path)
                self._engine.runAndWait()
                return True
        except Exception as e:
            print(f"[TextToSpeech] Save error: {e}")
        return False
