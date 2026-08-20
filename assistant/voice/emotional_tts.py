"""
Emotional Text-to-Speech
Adds emotional prosody (happy, sad, excited, calm) to speech synthesis.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class Emotion(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    CALM = "calm"
    ANGRY = "angry"
    SURPRISED = "surprised"


class ProsodyParameter(Enum):
    PITCH = "pitch"
    RATE = "rate"
    VOLUME = "volume"
    STRESS = "stress"


@dataclass
class EmotionProfile:
    profile_id: str
    emotion: Emotion
    pitch_modifier: float  # 0.5 to 2.0
    rate_modifier: float  # 0.5 to 2.0
    volume_modifier: float  # 0.5 to 2.0
    pitch_range: float  # 0.0 to 1.0
    stress_pattern: str  # 'flat', 'rising', 'falling', 'variable'
    created_at: str


class EmotionalTTS:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.tts_dir = os.path.join(self.base_dir, "data", "emotional_tts")
        self.profiles_file = os.path.join(self.tts_dir, "emotion_profiles.json")
        
        os.makedirs(self.tts_dir, exist_ok=True)
        
        # Load emotion profiles
        self.emotion_profiles = self._load_profiles()
        
        # Initialize default emotion profiles
        self._initialize_default_profiles()

    def _load_profiles(self) -> Dict[str, EmotionProfile]:
        """Load emotion profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {profile_id: EmotionProfile(**profile) for profile_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save emotion profiles to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {profile_id: asdict(profile) for profile_id, profile in self.emotion_profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[EmotionalTTS] Failed to save profiles: {e}")

    def _initialize_default_profiles(self):
        """Initialize default emotion profiles."""
        if not self.emotion_profiles:
            default_profiles = {
                'neutral': EmotionProfile(
                    profile_id='neutral',
                    emotion=Emotion.NEUTRAL,
                    pitch_modifier=1.0,
                    rate_modifier=1.0,
                    volume_modifier=1.0,
                    pitch_range=0.3,
                    stress_pattern='variable',
                    created_at=datetime.now().isoformat()
                ),
                'happy': EmotionProfile(
                    profile_id='happy',
                    emotion=Emotion.HAPPY,
                    pitch_modifier=1.2,
                    rate_modifier=1.1,
                    volume_modifier=1.1,
                    pitch_range=0.5,
                    stress_pattern='variable',
                    created_at=datetime.now().isoformat()
                ),
                'sad': EmotionProfile(
                    profile_id='sad',
                    emotion=Emotion.SAD,
                    pitch_modifier=0.8,
                    rate_modifier=0.8,
                    volume_modifier=0.9,
                    pitch_range=0.2,
                    stress_pattern='falling',
                    created_at=datetime.now().isoformat()
                ),
                'excited': EmotionProfile(
                    profile_id='excited',
                    emotion=Emotion.EXCITED,
                    pitch_modifier=1.3,
                    rate_modifier=1.3,
                    volume_modifier=1.2,
                    pitch_range=0.6,
                    stress_pattern='variable',
                    created_at=datetime.now().isoformat()
                ),
                'calm': EmotionProfile(
                    profile_id='calm',
                    emotion=Emotion.CALM,
                    pitch_modifier=0.95,
                    rate_modifier=0.9,
                    volume_modifier=1.0,
                    pitch_range=0.2,
                    stress_pattern='flat',
                    created_at=datetime.now().isoformat()
                ),
                'angry': EmotionProfile(
                    profile_id='angry',
                    emotion=Emotion.ANGRY,
                    pitch_modifier=1.1,
                    rate_modifier=1.2,
                    volume_modifier=1.2,
                    pitch_range=0.5,
                    stress_pattern='rising',
                    created_at=datetime.now().isoformat()
                ),
                'surprised': EmotionProfile(
                    profile_id='surprised',
                    emotion=Emotion.SURPRISED,
                    pitch_modifier=1.25,
                    rate_modifier=1.15,
                    volume_modifier=1.1,
                    pitch_range=0.6,
                    stress_pattern='variable',
                    created_at=datetime.now().isoformat()
                )
            }
            
            self.emotion_profiles = default_profiles
            self._save_profiles()

    def apply_emotion_to_text(self, text: str, emotion: Emotion) -> str:
        """
        Apply emotion markers to text for TTS processing.
        
        Args:
            text: Input text
            emotion: Emotion to apply
            
        Returns:
            Text with emotion markers
        """
        profile = self.emotion_profiles.get(emotion.value)
        if not profile:
            return text
        
        # Add emotion markers (SSML-like)
        emotion_markers = {
            Emotion.HAPPY: f"<emotion='happy'>{text}</emotion>",
            Emotion.SAD: f"<emotion='sad'>{text}</emotion>",
            Emotion.EXCITED: f"<emotion='excited'>{text}</emotion>",
            Emotion.CALM: f"<emotion='calm'>{text}</emotion>",
            Emotion.ANGRY: f"<emotion='angry'>{text}</emotion>",
            Emotion.SURPRISED: f"<emotion='surprised'>{text}</emotion>",
            Emotion.NEUTRAL: text
        }
        
        return emotion_markers.get(emotion, text)

    def get_prosody_parameters(self, emotion: Emotion) -> Dict[str, float]:
        """
        Get prosody parameters for an emotion.
        
        Args:
            emotion: Emotion
            
        Returns:
            Dictionary of prosody parameters
        """
        profile = self.emotion_profiles.get(emotion.value)
        if not profile:
            profile = self.emotion_profiles.get('neutral')
        
        return {
            'pitch': profile.pitch_modifier,
            'rate': profile.rate_modifier,
            'volume': profile.volume_modifier,
            'pitch_range': profile.pitch_range
        }

    def create_custom_emotion(self, emotion_name: str, pitch_modifier: float,
                             rate_modifier: float, volume_modifier: float,
                             pitch_range: float = 0.3,
                             stress_pattern: str = 'variable') -> EmotionProfile:
        """
        Create a custom emotion profile.
        
        Args:
            emotion_name: Name of the emotion
            pitch_modifier: Pitch modifier
            rate_modifier: Rate modifier
            volume_modifier: Volume modifier
            pitch_range: Pitch range
            stress_pattern: Stress pattern
            
        Returns:
            Created EmotionProfile
        """
        profile_id = f"custom_{emotion_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        profile = EmotionProfile(
            profile_id=profile_id,
            emotion=Emotion(emotion_name.lower()),
            pitch_modifier=pitch_modifier,
            rate_modifier=rate_modifier,
            volume_modifier=volume_modifier,
            pitch_range=pitch_range,
            stress_pattern=stress_pattern,
            created_at=datetime.now().isoformat()
        )
        
        self.emotion_profiles[profile_id] = profile
        self._save_profiles()
        
        return profile

    def get_emotion_profile(self, emotion: Emotion) -> Optional[EmotionProfile]:
        """Get emotion profile."""
        return self.emotion_profiles.get(emotion.value)

    def list_emotions(self) -> List[str]:
        """List available emotions."""
        return list(self.emotion_profiles.keys())

    def detect_emotion_from_text(self, text: str) -> Emotion:
        """
        Detect appropriate emotion from text content.
        
        Args:
            text: Input text
            
        Returns:
            Detected emotion
        """
        text_lower = text.lower()
        
        # Simple keyword-based detection
        happy_keywords = ['happy', 'great', 'awesome', 'wonderful', 'love', 'excited', 'fantastic']
        sad_keywords = ['sad', 'sorry', 'unhappy', 'depressed', 'cry', 'tears', 'miss']
        excited_keywords = ['excited', 'wow', 'amazing', 'incredible', 'thrilled', 'cant wait']
        calm_keywords = ['calm', 'relax', 'peaceful', 'quiet', 'serene', 'gentle']
        angry_keywords = ['angry', 'furious', 'mad', 'hate', 'frustrated', 'annoyed']
        
        emotion_scores = {
            Emotion.HAPPY: sum(1 for word in happy_keywords if word in text_lower),
            Emotion.SAD: sum(1 for word in sad_keywords if word in text_lower),
            Emotion.EXCITED: sum(1 for word in excited_keywords if word in text_lower),
            Emotion.CALM: sum(1 for word in calm_keywords if word in text_lower),
            Emotion.ANGRY: sum(1 for word in angry_keywords if word in text_lower)
        }
        
        # Return emotion with highest score
        if emotion_scores:
            max_emotion = max(emotion_scores, key=emotion_scores.get)
            if emotion_scores[max_emotion] > 0:
                return max_emotion
        
        return Emotion.NEUTRAL

    def modify_emotion_profile(self, emotion: Emotion, **kwargs) -> bool:
        """Modify an existing emotion profile."""
        profile = self.emotion_profiles.get(emotion.value)
        if not profile:
            return False
        
        if 'pitch_modifier' in kwargs:
            profile.pitch_modifier = kwargs['pitch_modifier']
        if 'rate_modifier' in kwargs:
            profile.rate_modifier = kwargs['rate_modifier']
        if 'volume_modifier' in kwargs:
            profile.volume_modifier = kwargs['volume_modifier']
        if 'pitch_range' in kwargs:
            profile.pitch_range = kwargs['pitch_range']
        if 'stress_pattern' in kwargs:
            profile.stress_pattern = kwargs['stress_pattern']
        
        self._save_profiles()
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get emotional TTS statistics."""
        return {
            'total_profiles': len(self.emotion_profiles),
            'emotions': list(self.emotion_profiles.keys())
        }
