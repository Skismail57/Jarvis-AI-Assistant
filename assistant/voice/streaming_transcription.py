"""
Streaming Speech-to-Text
Provides real-time transcription with streaming STT capabilities.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import numpy as np


class TranscriptionState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class TranscriptionSegment:
    segment_id: str
    text: str
    start_time: float
    end_time: float
    confidence: float
    is_final: bool
    created_at: str


@dataclass
class TranscriptionSession:
    session_id: str
    state: TranscriptionState
    segments: List[TranscriptionSegment]
    full_transcript: str
    start_time: float
    end_time: Optional[float]
    language: str
    created_at: str


class StreamingTranscriber:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.transcription_dir = os.path.join(self.base_dir, "data", "transcriptions")
        self.sessions_file = os.path.join(self.transcription_dir, "sessions.json")
        
        os.makedirs(self.transcription_dir, exist_ok=True)
        
        # Load sessions
        self.sessions = self._load_sessions()
        
        # Active session
        self.active_session = None
        
        # Audio buffer for streaming
        self.audio_buffer = deque(maxlen=100)
        
        # Callback for real-time updates
        self.on_transcript_callback = None

    def _load_sessions(self) -> Dict[str, TranscriptionSession]:
        """Load transcription sessions from disk."""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {session_id: TranscriptionSession(**session) for session_id, session in data.items()}
            except Exception:
                pass
        return {}

    def _save_sessions(self):
        """Save sessions to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {session_id: asdict(session) for session_id, session in self.sessions.items()}
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[StreamingTranscriber] Failed to save sessions: {e}")

    def start_session(self, language: str = "en") -> TranscriptionSession:
        """
        Start a new transcription session.
        
        Args:
            language: Language code
            
        Returns:
            TranscriptionSession
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        session = TranscriptionSession(
            session_id=session_id,
            state=TranscriptionState.LISTENING,
            segments=[],
            full_transcript="",
            start_time=datetime.now().timestamp(),
            end_time=None,
            language=language,
            created_at=datetime.now().isoformat()
        )
        
        self.sessions[session_id] = session
        self.active_session = session
        self.audio_buffer.clear()
        
        self._save_sessions()
        
        return session

    def process_audio_chunk(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """
        Process a chunk of audio for transcription.
        
        Args:
            audio_data: Audio chunk
            sample_rate: Sample rate
            
        Returns:
            Transcribed text if available
        """
        if not self.active_session or self.active_session.state != TranscriptionState.LISTENING:
            return None
        
        # Add to buffer
        self.audio_buffer.append(audio_data)
        
        # Process when buffer has enough data
        if len(self.audio_buffer) >= 5:
            # Combine buffer
            combined_audio = np.concatenate(list(self.audio_buffer))
            
            # Transcribe
            text = self._transcribe_audio(combined_audio, sample_rate)
            
            if text:
                # Create segment
                segment_id = f"segment_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                segment = TranscriptionSegment(
                    segment_id=segment_id,
                    text=text,
                    start_time=self.active_session.start_time,
                    end_time=datetime.now().timestamp(),
                    confidence=0.8,
                    is_final=False,
                    created_at=datetime.now().isoformat()
                )
                
                self.active_session.segments.append(segment)
                self.active_session.full_transcript += " " + text
                
                # Update state
                self.active_session.state = TranscriptionState.PROCESSING
                
                # Call callback if set
                if self.on_transcript_callback:
                    self.on_transcript_callback(text)
                
                self._save_sessions()
                
                return text
        
        return None

    def _transcribe_audio(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            
        Returns:
            Transcribed text
        """
        try:
            # Try using speech_recognition library
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            # Convert to AudioData
            audio_bytes = (audio_data * 32767).astype(np.int16)
            audio_source = sr.AudioData(audio_bytes.tobytes(), sample_rate, 2)
            
            # Recognize
            try:
                text = recognizer.recognize_google(audio_source, language=self.active_session.language)
                return text
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                # Fallback to offline recognition
                return self._offline_transcription(audio_data)
                
        except ImportError:
            # Fallback to simple transcription
            return self._offline_transcription(audio_data)

    def _offline_transcription(self, audio_data: np.ndarray) -> str:
        """
        Offline transcription fallback.
        
        Args:
            audio_data: Audio data
            
        Returns:
            Transcribed text (placeholder)
        """
        # This is a placeholder - in production, use an offline STT model
        # like Vosk, Whisper, or similar
        return "[Transcription requires offline STT model]"

    def end_session(self) -> TranscriptionSession:
        """End the current transcription session."""
        if not self.active_session:
            raise ValueError("No active session")
        
        self.active_session.state = TranscriptionState.FINISHED
        self.active_session.end_time = datetime.now().timestamp()
        
        # Mark all segments as final
        for segment in self.active_session.segments:
            segment.is_final = True
        
        session = self.active_session
        self.active_session = None
        
        self._save_sessions()
        
        return session

    def get_session(self, session_id: str) -> Optional[TranscriptionSession]:
        """Get a transcription session by ID."""
        return self.sessions.get(session_id)

    def get_full_transcript(self, session_id: str) -> str:
        """Get full transcript for a session."""
        session = self.get_session(session_id)
        if session:
            return session.full_transcript.strip()
        return ""

    def set_transcript_callback(self, callback: Callable[[str], None]):
        """Set callback for real-time transcript updates."""
        self.on_transcript_callback = callback

    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        duration = (session.end_time or datetime.now().timestamp()) - session.start_time
        word_count = len(session.full_transcript.split())
        
        return {
            'session_id': session_id,
            'state': session.state.value,
            'duration': round(duration, 2),
            'segment_count': len(session.segments),
            'word_count': word_count,
            'language': session.language
        }

    def delete_session(self, session_id: str) -> bool:
        """Delete a transcription session."""
        if session_id not in self.sessions:
            return False
        
        del self.sessions[session_id]
        self._save_sessions()
        
        return True

    def clear_old_sessions(self, days: int = 7) -> int:
        """Clear sessions older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            session_id for session_id, session in self.sessions.items()
            if datetime.fromisoformat(session.created_at) < cutoff_date
        ]
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        if to_remove:
            self._save_sessions()
        
        return len(to_remove)
