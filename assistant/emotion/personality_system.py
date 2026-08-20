"""
Personality Customization System
Allows customization of assistant personality (formal, casual, humorous, etc.).
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class PersonalityType(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    SARCASTIC = "sarcastic"
    POETIC = "poetic"
    TECHNICAL = "technical"
    MINIMALIST = "minimalist"
    VERBOSE = "verbose"


class Tone(Enum):
    RESPECTFUL = "respectful"
    DIRECT = "direct"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    WARM = "warm"
    COOL = "cool"


@dataclass
class PersonalityProfile:
    profile_id: str
    name: str
    personality_type: PersonalityType
    tone: Tone
    greeting_style: str
    response_patterns: Dict[str, str]
    vocabulary_preferences: List[str]
    emoji_usage: str  # 'none', 'minimal', 'moderate', 'heavy'
    formality_level: int  # 0-10
    humor_level: int  # 0-10
    created_at: str
    is_default: bool = False


class PersonalitySystem:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.personality_dir = os.path.join(self.base_dir, "data", "personality")
        self.profiles_file = os.path.join(self.personality_dir, "profiles.json")
        self.user_preferences_file = os.path.join(self.personality_dir, "user_preferences.json")
        
        os.makedirs(self.personality_dir, exist_ok=True)
        
        # Load data
        self.profiles = self._load_profiles()
        self.user_preferences = self._load_user_preferences()
        
        # Initialize default personalities
        self._initialize_default_personalities()

    def _load_profiles(self) -> Dict[str, PersonalityProfile]:
        """Load personality profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {profile_id: PersonalityProfile(**profile) for profile_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save personality profiles to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {profile_id: asdict(profile) for profile_id, profile in self.profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[PersonalitySystem] Failed to save profiles: {e}")

    def _load_user_preferences(self) -> Dict[str, str]:
        """Load user personality preferences from disk."""
        if os.path.exists(self.user_preferences_file):
            try:
                with open(self.user_preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_user_preferences(self):
        """Save user personality preferences to disk."""
        try:
            with open(self.user_preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            print(f"[PersonalitySystem] Failed to save user preferences: {e}")

    def _initialize_default_personalities(self):
        """Initialize default personality profiles."""
        if not self.profiles:
            default_profiles = {
                'formal_professional': PersonalityProfile(
                    profile_id='formal_professional',
                    name='Formal Professional',
                    personality_type=PersonalityType.FORMAL,
                    tone=Tone.RESPECTFUL,
                    greeting_style="Good day. How may I assist you today?",
                    response_patterns={
                        'affirmative': "Certainly. I will proceed with that.",
                        'negative': "I apologize, but I cannot accommodate that request.",
                        'uncertain': "I require additional information to assist you properly.",
                        'greeting': "Greetings. It is a pleasure to assist you.",
                        'farewell': "Thank you for your time. Have a pleasant day."
                    },
                    vocabulary_preferences=['certainly', 'accommodate', 'proceed', 'assist', 'appreciate'],
                    emoji_usage='none',
                    formality_level=9,
                    humor_level=1,
                    created_at=datetime.now().isoformat(),
                    is_default=True
                ),
                'casual_friendly': PersonalityProfile(
                    profile_id='casual_friendly',
                    name='Casual Friendly',
                    personality_type=PersonalityType.CASUAL,
                    tone=Tone.WARM,
                    greeting_style="Hey there! What can I help you with?",
                    response_patterns={
                        'affirmative': "Sure thing! I'll get that done for you.",
                        'negative': "Sorry, I can't do that right now.",
                        'uncertain': "Hmm, I'm not sure about that. Can you give me more details?",
                        'greeting': "Hi! How's it going?",
                        'farewell': "See ya later! Take care!"
                    },
                    vocabulary_preferences=['sure', 'cool', 'awesome', 'great', 'thanks'],
                    emoji_usage='moderate',
                    formality_level=3,
                    humor_level=5,
                    created_at=datetime.now().isoformat(),
                    is_default=False
                ),
                'humorous': PersonalityProfile(
                    profile_id='humorous',
                    name='Humorous',
                    personality_type=PersonalityType.HUMOROUS,
                    tone=Tone.PLAYFUL,
                    greeting_style="Well hello there! Ready for some fun and productivity?",
                    response_patterns={
                        'affirmative': "You got it! Let's make some magic happen! ✨",
                        'negative': "Oops! My bad. Can't do that one, but I can still be your friend! 😄",
                        'uncertain': "My crystal ball is a bit foggy on that one. Care to clarify?",
                        'greeting': "Hey hey! The AI comedian is at your service!",
                        'farewell': "Stay awesome! Don't forget to feed your cat! 🐱"
                    },
                    vocabulary_preferences=['awesome', 'magic', 'crystal ball', 'foggy', 'awesome'],
                    emoji_usage='heavy',
                    formality_level=2,
                    humor_level=9,
                    created_at=datetime.now().isoformat(),
                    is_default=False
                ),
                'technical': PersonalityProfile(
                    profile_id='technical',
                    name='Technical',
                    personality_type=PersonalityType.TECHNICAL,
                    tone=Tone.DIRECT,
                    greeting_style="System ready. Awaiting input.",
                    response_patterns={
                        'affirmative': "Acknowledged. Executing requested operation.",
                        'negative': "Operation cannot be completed. Error encountered.",
                        'uncertain': "Insufficient data. Additional parameters required.",
                        'greeting': "System initialized. Ready for input.",
                        'farewell': "Session terminated. Goodbye."
                    },
                    vocabulary_preferences=['execute', 'operation', 'parameter', 'system', 'initialize'],
                    emoji_usage='none',
                    formality_level=8,
                    humor_level=1,
                    created_at=datetime.now().isoformat(),
                    is_default=False
                ),
                'minimalist': PersonalityProfile(
                    profile_id='minimalist',
                    name='Minimalist',
                    personality_type=PersonalityType.MINIMALIST,
                    tone=Tone.DIRECT,
                    greeting_style="Ready.",
                    response_patterns={
                        'affirmative': "Done.",
                        'negative': "Can't.",
                        'uncertain': "More info?",
                        'greeting': "Hi.",
                        'farewell': "Bye."
                    },
                    vocabulary_preferences=['done', 'ok', 'yes', 'no', 'maybe'],
                    emoji_usage='none',
                    formality_level=5,
                    humor_level=2,
                    created_at=datetime.now().isoformat(),
                    is_default=False
                )
            }
            
            self.profiles = default_profiles
            self._save_profiles()

    def create_custom_personality(self, name: str, personality_type: PersonalityType,
                                tone: Tone, greeting_style: str,
                                response_patterns: Dict[str, str],
                                formality_level: int = 5,
                                humor_level: int = 5,
                                emoji_usage: str = 'moderate') -> PersonalityProfile:
        """Create a custom personality profile."""
        profile_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        profile = PersonalityProfile(
            profile_id=profile_id,
            name=name,
            personality_type=personality_type,
            tone=tone,
            greeting_style=greeting_style,
            response_patterns=response_patterns,
            vocabulary_preferences=[],
            emoji_usage=emoji_usage,
            formality_level=formality_level,
            humor_level=humor_level,
            created_at=datetime.now().isoformat(),
            is_default=False
        )
        
        self.profiles[profile_id] = profile
        self._save_profiles()
        
        return profile

    def set_user_personality(self, user_id: str, profile_id: str) -> bool:
        """Set personality preference for a user."""
        if profile_id not in self.profiles:
            return False
        
        self.user_preferences[user_id] = profile_id
        self._save_user_preferences()
        
        return True

    def get_user_personality(self, user_id: str) -> Optional[PersonalityProfile]:
        """Get personality profile for a user."""
        profile_id = self.user_preferences.get(user_id)
        if profile_id:
            return self.profiles.get(profile_id)
        
        # Return default if no preference set
        for profile in self.profiles.values():
            if profile.is_default:
                return profile
        
        return None

    def apply_personality_to_response(self, response: str, user_id: str = None,
                                    profile_id: str = None) -> str:
        """
        Apply personality to a response.
        
        Args:
            response: Base response
            user_id: User ID (to get their personality preference)
            profile_id: Override profile ID
            
        Returns:
            Personality-adapted response
        """
        # Get profile
        if profile_id:
            profile = self.profiles.get(profile_id)
        elif user_id:
            profile = self.get_user_personality(user_id)
        else:
            profile = None
        
        if not profile:
            return response
        
        # Apply personality transformations
        adapted = response
        
        # Adjust formality
        if profile.formality_level > 7:
            adapted = self._make_formal(adapted)
        elif profile.formality_level < 4:
            adapted = self._make_casual(adapted)
        
        # Add emojis if configured
        if profile.emoji_usage == 'heavy':
            adapted = self._add_emojis(adapted, count=3)
        elif profile.emoji_usage == 'moderate':
            adapted = self._add_emojis(adapted, count=1)
        
        # Apply humor if configured
        if profile.humor_level > 7:
            adapted = self._add_humor(adapted)
        
        return adapted

    def _make_formal(self, text: str) -> str:
        """Make text more formal."""
        replacements = {
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "hey": "greetings",
            "hi": "hello",
            "ok": "acceptable",
            "yeah": "yes",
            "nope": "no",
            "stuff": "items",
            "things": "matters",
            "got": "received",
            "get": "obtain"
        }
        
        for informal, formal in replacements.items():
            text = text.replace(informal, formal)
        
        return text

    def _make_casual(self, text: str) -> str:
        """Make text more casual."""
        replacements = {
            "cannot": "can't",
            "will not": "won't",
            "do not": "don't",
            "greetings": "hey",
            "hello": "hi",
            "acceptable": "ok",
            "yes": "yeah",
            "obtain": "get",
            "received": "got"
        }
        
        for formal, informal in replacements.items():
            text = text.replace(formal, informal)
        
        return text

    def _add_emojis(self, text: str, count: int = 1) -> str:
        """Add emojis to text."""
        emojis = ['😊', '👍', '✨', '🎉', '💡', '🤔', '🚀', '💪']
        import random
        
        for _ in range(count):
            emoji = random.choice(emojis)
            text = text.rstrip('.') + f' {emoji}'
        
        return text

    def _add_humor(self, text: str) -> str:
        """Add humorous elements to text."""
        humorous_additions = [
            " (fingers crossed!)",
            " (fingers crossed 🤞)",
            " (knock on wood)",
            " (fingers crossed 🤞)",
            " (fingers crossed 🤞)"
        ]
        
        import random
        if random.random() > 0.5:
            addition = random.choice(humorous_additions)
            text = text.rstrip('.') + addition
        
        return text

    def get_greeting(self, user_id: str = None, profile_id: str = None) -> str:
        """Get a greeting based on personality."""
        profile = None
        
        if profile_id:
            profile = self.profiles.get(profile_id)
        elif user_id:
            profile = self.get_user_personality(user_id)
        
        if profile and profile.greeting_style:
            return profile.greeting_style
        
        return "Hello! How can I help you today?"

    def get_farewell(self, user_id: str = None, profile_id: str = None) -> str:
        """Get a farewell based on personality."""
        profile = None
        
        if profile_id:
            profile = self.profiles.get(profile_id)
        elif user_id:
            profile = self.get_user_personality(user_id)
        
        if profile and 'farewell' in profile.response_patterns:
            return profile.response_patterns['farewell']
        
        return "Goodbye! Have a great day!"

    def get_all_profiles(self) -> List[PersonalityProfile]:
        """Get all available personality profiles."""
        return list(self.profiles.values())

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a personality profile (if not default)."""
        if profile_id not in self.profiles:
            return False
        
        if self.profiles[profile_id].is_default:
            return False
        
        del self.profiles[profile_id]
        self._save_profiles()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get personality system statistics."""
        total_profiles = len(self.profiles)
        total_users = len(self.user_preferences)
        
        # Count by type
        by_type = {}
        for profile in self.profiles.values():
            ptype = profile.personality_type.value
            by_type[ptype] = by_type.get(ptype, 0) + 1
        
        return {
            'total_profiles': total_profiles,
            'total_users': total_users,
            'by_type': by_type
        }
