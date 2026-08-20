"""
Speaker Diarization System
Identifies and separates different speakers in audio for multi-user environments.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np


class SpeakerLabel(Enum):
    SPEAKER_1 = "speaker_1"
    SPEAKER_2 = "speaker_2"
    SPEAKER_3 = "speaker_3"
    SPEAKER_4 = "speaker_4"
    UNKNOWN = "unknown"


@dataclass
class SpeakerSegment:
    segment_id: str
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float
    features: List[float]
    transcript: str = ""
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class SpeakerProfile:
    speaker_id: str
    name: Optional[str]
    voice_features: List[float]
    segment_count: int
    first_seen: str
    last_seen: str
    is_registered: bool = False


class SpeakerDiarization:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.diarization_dir = os.path.join(self.base_dir, "data", "speaker_diarization")
        self.segments_file = os.path.join(self.diarization_dir, "segments.json")
        self.profiles_file = os.path.join(self.diarization_dir, "speaker_profiles.json")
        
        os.makedirs(self.diarization_dir, exist_ok=True)
        
        # Load data
        self.segments = self._load_segments()
        self.speaker_profiles = self._load_profiles()
        
        # Speaker embedding model placeholder
        self.speaker_embeddings = {}
        
        # Clustering threshold
        self.similarity_threshold = 0.7

    def _load_segments(self) -> Dict[str, SpeakerSegment]:
        """Load speaker segments from disk."""
        if os.path.exists(self.segments_file):
            try:
                with open(self.segments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {segment_id: SpeakerSegment(**segment) for segment_id, segment in data.items()}
            except Exception:
                pass
        return {}

    def _save_segments(self):
        """Save speaker segments to disk."""
        try:
            data = {segment_id: asdict(segment) for segment_id, segment in self.segments.items()}
            with open(self.segments_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SpeakerDiarization] Failed to save segments: {e}")

    def _load_profiles(self) -> Dict[str, SpeakerProfile]:
        """Load speaker profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {speaker_id: SpeakerProfile(**profile) for speaker_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save speaker profiles to disk."""
        try:
            data = {speaker_id: asdict(profile) for speaker_id, profile in self.speaker_profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SpeakerDiarization] Failed to save profiles: {e}")

    def extract_audio_features(self, audio_data: np.ndarray, sample_rate: int = 16000) -> List[float]:
        """
        Extract MFCC features from audio for speaker identification.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio
            
        Returns:
            Feature vector
        """
        try:
            import librosa
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            
            # Take mean across time
            features = np.mean(mfcc, axis=1).tolist()
            
            return features
            
        except ImportError:
            # Fallback: simple statistical features
            features = [
                np.mean(audio_data),
                np.std(audio_data),
                np.max(audio_data),
                np.min(audio_data),
                len(audio_data)
            ]
            return features

    def compare_speaker_features(self, features1: List[float], features2: List[float]) -> float:
        """
        Compare two speaker feature vectors.
        
        Args:
            features1: First feature vector
            features2: Second feature vector
            
        Returns:
            Similarity score (0-1)
        """
        try:
            vec1 = np.array(features1)
            vec2 = np.array(features2)
            
            # Ensure same length
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(abs(similarity))
            
        except Exception as e:
            print(f"[SpeakerDiarization] Feature comparison failed: {e}")
            return 0.0

    def identify_speaker(self, features: List[float]) -> Tuple[str, float]:
        """
        Identify speaker from features.
        
        Args:
            features: Audio features
            
        Returns:
            (speaker_id, confidence)
        """
        best_match = None
        best_confidence = 0.0
        
        for speaker_id, profile in self.speaker_profiles.items():
            if profile.voice_features:
                similarity = self.compare_speaker_features(features, profile.voice_features)
                if similarity > best_confidence:
                    best_confidence = similarity
                    best_match = speaker_id
        
        if best_match and best_confidence >= self.similarity_threshold:
            return best_match, best_confidence
        
        # Create new speaker
        new_speaker_id = f"speaker_{len(self.speaker_profiles) + 1}"
        return new_speaker_id, 0.0

    def process_audio_segment(self, audio_data: np.ndarray, start_time: float,
                            end_time: float, sample_rate: int = 16000) -> SpeakerSegment:
        """
        Process an audio segment and identify speaker.
        
        Args:
            audio_data: Audio data
            start_time: Start time in seconds
            end_time: End time in seconds
            sample_rate: Sample rate
            
        Returns:
            SpeakerSegment
        """
        # Extract features
        features = self.extract_audio_features(audio_data, sample_rate)
        
        # Identify speaker
        speaker_id, confidence = self.identify_speaker(features)
        
        # Create segment
        segment_id = f"segment_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        segment = SpeakerSegment(
            segment_id=segment_id,
            speaker_id=speaker_id,
            start_time=start_time,
            end_time=end_time,
            confidence=confidence,
            features=features
        )
        
        # Update speaker profile
        if speaker_id not in self.speaker_profiles:
            self.speaker_profiles[speaker_id] = SpeakerProfile(
                speaker_id=speaker_id,
                name=None,
                voice_features=features,
                segment_count=1,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                is_registered=False
            )
        else:
            profile = self.speaker_profiles[speaker_id]
            profile.voice_features = features  # Update with latest features
            profile.segment_count += 1
            profile.last_seen = datetime.now().isoformat()
        
        self.segments[segment_id] = segment
        self._save_segments()
        self._save_profiles()
        
        return segment

    def diarize_audio(self, audio_data: np.ndarray, sample_rate: int = 16000,
                     segment_length: float = 3.0) -> List[SpeakerSegment]:
        """
        Perform speaker diarization on audio.
        
        Args:
            audio_data: Full audio data
            sample_rate: Sample rate
            segment_length: Length of each segment in seconds
            
        Returns:
            List of SpeakerSegments
        """
        segments = []
        total_duration = len(audio_data) / sample_rate
        
        current_time = 0.0
        while current_time < total_duration:
            end_time = min(current_time + segment_length, total_duration)
            
            # Extract segment
            start_sample = int(current_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            segment_audio = audio_data[start_sample:end_sample]
            
            # Process segment
            segment = self.process_audio_segment(segment_audio, current_time, end_time, sample_rate)
            segments.append(segment)
            
            current_time = end_time
        
        return segments

    def register_speaker(self, speaker_id: str, name: str, audio_samples: List[np.ndarray],
                       sample_rate: int = 16000) -> bool:
        """
        Register a speaker with name and voice samples.
        
        Args:
            speaker_id: Speaker ID
            name: Speaker name
            audio_samples: List of audio samples for training
            sample_rate: Sample rate
            
        Returns:
            True if successful
        """
        if not audio_samples:
            return False
        
        # Extract features from all samples and average
        all_features = []
        for sample in audio_samples:
            features = self.extract_audio_features(sample, sample_rate)
            all_features.append(features)
        
        # Average features
        avg_features = np.mean(all_features, axis=0).tolist()
        
        # Update or create profile
        if speaker_id in self.speaker_profiles:
            profile = self.speaker_profiles[speaker_id]
            profile.name = name
            profile.voice_features = avg_features
            profile.is_registered = True
        else:
            self.speaker_profiles[speaker_id] = SpeakerProfile(
                speaker_id=speaker_id,
                name=name,
                voice_features=avg_features,
                segment_count=0,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                is_registered=True
            )
        
        self._save_profiles()
        return True

    def get_speaker_profile(self, speaker_id: str) -> Optional[SpeakerProfile]:
        """Get speaker profile by ID."""
        return self.speaker_profiles.get(speaker_id)

    def get_speaker_segments(self, speaker_id: str) -> List[SpeakerSegment]:
        """Get all segments for a speaker."""
        return [segment for segment in self.segments.values() if segment.speaker_id == speaker_id]

    def rename_speaker(self, speaker_id: str, new_name: str) -> bool:
        """Rename a speaker."""
        if speaker_id not in self.speaker_profiles:
            return False
        
        self.speaker_profiles[speaker_id].name = new_name
        self._save_profiles()
        
        return True

    def merge_speakers(self, source_speaker_id: str, target_speaker_id: str) -> bool:
        """Merge two speaker profiles."""
        if source_speaker_id not in self.speaker_profiles or target_speaker_id not in self.speaker_profiles:
            return False
        
        # Update segments
        for segment in self.segments.values():
            if segment.speaker_id == source_speaker_id:
                segment.speaker_id = target_speaker_id
        
        # Update target profile
        target_profile = self.speaker_profiles[target_speaker_id]
        source_profile = self.speaker_profiles[source_speaker_id]
        target_profile.segment_count += source_profile.segment_count
        
        # Remove source profile
        del self.speaker_profiles[source_speaker_id]
        
        self._save_segments()
        self._save_profiles()
        
        return True

    def get_diarization_statistics(self) -> Dict[str, Any]:
        """Get diarization statistics."""
        total_segments = len(self.segments)
        total_speakers = len(self.speaker_profiles)
        
        # Segment count per speaker
        speaker_counts = {}
        for segment in self.segments.values():
            speaker_counts[segment.speaker_id] = speaker_counts.get(segment.speaker_id, 0) + 1
        
        # Registered speakers
        registered = sum(1 for profile in self.speaker_profiles.values() if profile.is_registered)
        
        return {
            'total_segments': total_segments,
            'total_speakers': total_speakers,
            'registered_speakers': registered,
            'segments_per_speaker': speaker_counts
        }

    def export_transcript(self, speaker_id: str = None) -> str:
        """
        Export transcript with speaker labels.
        
        Args:
            speaker_id: Optional speaker ID to filter by
            
        Returns:
            Formatted transcript
        """
        segments = self.segments.values()
        
        if speaker_id:
            segments = [s for s in segments if s.speaker_id == speaker_id]
        
        # Sort by start time
        segments = sorted(segments, key=lambda x: x.start_time)
        
        transcript_lines = []
        for segment in segments:
            profile = self.speaker_profiles.get(segment.speaker_id)
            speaker_name = profile.name if profile and profile.name else segment.speaker_id
            
            line = f"[{segment.start_time:.2f}s - {segment.end_time:.2f}s] {speaker_name}: {segment.transcript}"
            transcript_lines.append(line)
        
        return '\n'.join(transcript_lines)

    def clear_old_segments(self, days: int = 30) -> int:
        """Clear segments older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            segment_id for segment_id, segment in self.segments.items()
            if datetime.fromisoformat(segment.created_at) < cutoff_date
        ]
        
        for segment_id in to_remove:
            del self.segments[segment_id]
        
        if to_remove:
            self._save_segments()
        
        return len(to_remove)
