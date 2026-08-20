import os
import tempfile
import threading
from typing import Optional


class SpeechToText:
    def __init__(self, engine: str = "sr", language: str = "en-US"):
        self.engine = engine.lower()
        self.language = language
        self.recognizer = None
        self.whisper_model = None
        self._init_engine()

    def _init_engine(self):
        if self.engine == "sr":
            try:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 300
                self.recognizer.pause_threshold = 0.8
                self.recognizer.non_speaking_duration = 0.5
            except ImportError:
                print("[SpeechToText] SpeechRecognition not installed. Install with: pip install SpeechRecognition pyaudio")
                self.recognizer = None
        elif self.engine == "whisper":
            try:
                import torch
                from transformers import WhisperForConditionalGeneration, WhisperProcessor
                self._whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-small")
                self.whisper_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
                if torch.cuda.is_available():
                    self.whisper_model = self.whisper_model.to("cuda")
                self.whisper_model.eval()
            except ImportError:
                print("[SpeechToText] Whisper dependencies missing. Falling back to SpeechRecognition.")
                self.engine = "sr"
                self._init_engine()

    def listen_from_microphone(self, timeout: int = 5, phrase_time_limit: int = 15) -> Optional[str]:
        if self.recognizer is None:
            return None

        import speech_recognition as sr
        try:
            with sr.Microphone() as source:
                print("[Listening...] Speak now.")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            return self._recognize_with_sr(audio)
        except sr.WaitTimeoutError:
            print("[SpeechToText] No speech detected within timeout.")
            return None
        except sr.UnknownValueError:
            print("[SpeechToText] Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"[SpeechToText] Service error: {e}")
            return None
        except Exception as e:
            print(f"[SpeechToText] Microphone error: {e}")
            return None

    def _recognize_with_sr(self, audio) -> Optional[str]:
        import speech_recognition as sr
        recognizers = [
            ("google", lambda: self.recognizer.recognize_google(audio, language=self.language)),
        ]
        try:
            recognizers.append(("sphinx", lambda: self.recognizer.recognize_sphinx(audio, language=self.language)))
        except Exception:
            pass

        last_error = None
        for name, fn in recognizers:
            try:
                text = fn()
                if text and len(text.strip()) > 0:
                    return text.strip()
            except sr.UnknownValueError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue
        if last_error:
            return None
        return None

    def transcribe_file(self, audio_path: str) -> Optional[str]:
        if self.engine == "whisper" and self.whisper_model is not None:
            return self._transcribe_whisper(audio_path)

        if self.recognizer is not None:
            import speech_recognition as sr
            try:
                with sr.AudioFile(audio_path) as source:
                    audio = self.recognizer.record(source)
                return self._recognize_with_sr(audio)
            except Exception as e:
                print(f"[SpeechToText] File transcription error: {e}")
                return None
        return None

    def _transcribe_whisper(self, audio_path: str) -> Optional[str]:
        try:
            import librosa
            import torch
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            inputs = self._whisper_processor(
                audio, sampling_rate=sr, return_tensors="pt"
            )
            input_features = inputs.input_features
            if torch.cuda.is_available():
                input_features = input_features.to("cuda")
            with torch.no_grad():
                predicted_ids = self.whisper_model.generate(input_features)
            transcription = self._whisper_processor.batch_decode(
                predicted_ids, skip_special_tokens=True
            )[0]
            return transcription.strip()
        except Exception as e:
            print(f"[SpeechToText] Whisper transcription error: {e}")
            return None
