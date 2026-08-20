"""
Adaptive Response System
Adapts responses based on user mood and emotional context.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict

from .sentiment_analyzer import Emotion, Sentiment


class ResponseStyle(Enum):
    EMPATHETIC = "empathetic"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    CALMING = "calming"
    DIRECT = "direct"
    SUPPORTIVE = "supportive"
    PLAYFUL = "playful"


@dataclass
class ResponseTemplate:
    template_id: str
    emotion: Emotion
    sentiment: Sentiment
    style: ResponseStyle
    template: str
    variations: List[str]
    created_at: str


@dataclass
class UserMoodProfile:
    user_id: str
    current_mood: Emotion
    mood_history: List[Dict[str, Any]]
    preferred_style: ResponseStyle
    last_updated: str


class AdaptiveResponseSystem:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.adaptive_dir = os.path.join(self.base_dir, "data", "adaptive")
        self.templates_file = os.path.join(self.adaptive_dir, "response_templates.json")
        self.profiles_file = os.path.join(self.adaptive_dir, "mood_profiles.json")
        
        os.makedirs(self.adaptive_dir, exist_ok=True)
        
        # Load data
        self.templates = self._load_templates()
        self.user_profiles = self._load_profiles()
        
        # Initialize default templates
        self._initialize_default_templates()

    def _load_templates(self) -> Dict[str, ResponseTemplate]:
        """Load response templates from disk."""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {template_id: ResponseTemplate(**template) for template_id, template in data.items()}
            except Exception:
                pass
        return {}

    def _save_templates(self):
        """Save response templates to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {template_id: asdict(template) for template_id, template in self.templates.items()}
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[AdaptiveResponse] Failed to save templates: {e}")

    def _load_profiles(self) -> Dict[str, UserMoodProfile]:
        """Load user mood profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {user_id: UserMoodProfile(**profile) for user_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save user mood profiles to disk."""
        try:
            data = {user_id: asdict(profile) for user_id, profile in self.user_profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AdaptiveResponse] Failed to save profiles: {e}")

    def _initialize_default_templates(self):
        """Initialize default response templates."""
        if not self.templates:
            default_templates = {
                'happy_positive': ResponseTemplate(
                    template_id='happy_positive',
                    emotion=Emotion.HAPPY,
                    sentiment=Sentiment.POSITIVE,
                    style=ResponseStyle.ENTHUSIASTIC,
                    template="That's wonderful! I'm so glad to hear that! {response}",
                    variations=[
                        "Great news! {response}",
                        "That's fantastic! {response}",
                        "I'm thrilled for you! {response}"
                    ],
                    created_at=datetime.now().isoformat()
                ),
                'sad_negative': ResponseTemplate(
                    template_id='sad_negative',
                    emotion=Emotion.SAD,
                    sentiment=Sentiment.NEGATIVE,
                    style=ResponseStyle.EMPATHETIC,
                    template="I understand this is difficult. I'm here to help. {response}",
                    variations=[
                        "I'm sorry to hear that. Let me help. {response}",
                        "That sounds tough. I'm here for you. {response}",
                        "I understand. Let's work through this together. {response}"
                    ],
                    created_at=datetime.now().isoformat()
                ),
                'angry_negative': ResponseTemplate(
                    template_id='angry_negative',
                    emotion=Emotion.ANGRY,
                    sentiment=Sentiment.NEGATIVE,
                    style=ResponseStyle.CALMING,
                    template="I can see you're frustrated. Let me help resolve this. {response}",
                    variations=[
                        "I understand your frustration. Let's fix this. {response}",
                        "I hear you. Let me help address this. {response}",
                        "I get it. Let's work on a solution. {response}"
                    ],
                    created_at=datetime.now().isoformat()
                ),
                'neutral_neutral': ResponseTemplate(
                    template_id='neutral_neutral',
                    emotion=Emotion.NEUTRAL,
                    sentiment=Sentiment.NEUTRAL,
                    style=ResponseStyle.PROFESSIONAL,
                    template="{response}",
                    variations=[
                        "Here's what I can do: {response}",
                        "I'll help with that: {response}",
                        "Of course: {response}"
                    ],
                    created_at=datetime.now().isoformat()
                ),
                'anxious_negative': ResponseTemplate(
                    template_id='anxious_negative',
                    emotion=Emotion.ANXIOUS,
                    sentiment=Sentiment.NEGATIVE,
                    style=ResponseStyle.CALMING,
                    template="Don't worry, I'll help you through this. {response}",
                    variations=[
                        "Take a breath. We'll handle this together. {response}",
                        "I'm here to help. Let's take this step by step. {response}",
                        "No need to worry. I've got this. {response}"
                    ],
                    created_at=datetime.now().isoformat()
                ),
                'excited_positive': ResponseTemplate(
                    template_id='excited_positive',
                    emotion=Emotion.EXCITED,
                    sentiment=Sentiment.POSITIVE,
                    style=ResponseStyle.ENTHUSIASTIC,
                    template="That's exciting! Let's get started! {response}",
                    variations=[
                        "Awesome! I'm on it! {response}",
                        "Let's do this! {response}",
                        "Fantastic! Here we go! {response}"
                    ],
                    created_at=datetime.now().isoformat()
                )
            }
            
            self.templates = default_templates
            self._save_templates()

    def update_user_mood(self, user_id: str, emotion: Emotion, sentiment: Sentiment):
        """Update user's current mood."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserMoodProfile(
                user_id=user_id,
                current_mood=emotion,
                mood_history=[],
                preferred_style=ResponseStyle.PROFESSIONAL,
                last_updated=datetime.now().isoformat()
            )
        
        profile = self.user_profiles[user_id]
        profile.current_mood = emotion
        profile.mood_history.append({
            'emotion': emotion.value,
            'sentiment': sentiment.value,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 mood entries
        if len(profile.mood_history) > 50:
            profile.mood_history = profile.mood_history[-50:]
        
        profile.last_updated = datetime.now().isoformat()
        
        # Update preferred style based on mood
        profile.preferred_style = self._determine_preferred_style(emotion, sentiment)
        
        self._save_profiles()

    def _determine_preferred_style(self, emotion: Emotion, sentiment: Sentiment) -> ResponseStyle:
        """Determine preferred response style based on emotion and sentiment."""
        style_mapping = {
            (Emotion.HAPPY, Sentiment.POSITIVE): ResponseStyle.ENTHUSIASTIC,
            (Emotion.SAD, Sentiment.NEGATIVE): ResponseStyle.EMPATHETIC,
            (Emotion.ANGRY, Sentiment.NEGATIVE): ResponseStyle.CALMING,
            (Emotion.ANXIOUS, Sentiment.NEGATIVE): ResponseStyle.CALMING,
            (Emotion.EXCITED, Sentiment.POSITIVE): ResponseStyle.ENTHUSIASTIC,
            (Emotion.CALM, Sentiment.NEUTRAL): ResponseStyle.CASUAL,
            (Emotion.NEUTRAL, Sentiment.NEUTRAL): ResponseStyle.PROFESSIONAL,
            (Emotion.FEARFUL, Sentiment.NEGATIVE): ResponseStyle.SUPPORTIVE,
        }
        
        return style_mapping.get((emotion, sentiment), ResponseStyle.PROFESSIONAL)

    def generate_adaptive_response(self, base_response: str, user_id: str = None,
                                  emotion: Emotion = None, sentiment: Sentiment = None) -> str:
        """
        Generate an adaptive response based on user mood.
        
        Args:
            base_response: The base response to adapt
            user_id: User ID (to get mood profile)
            emotion: Override emotion
            sentiment: Override sentiment
            
        Returns:
            Adapted response
        """
        # Get emotion/sentiment from profile if not provided
        if user_id and (emotion is None or sentiment is None):
            profile = self.user_profiles.get(user_id)
            if profile:
                if emotion is None:
                    emotion = profile.current_mood
                if sentiment is None:
                    # Get sentiment from history
                    if profile.mood_history:
                        last_mood = profile.mood_history[-1]
                        sentiment = Sentiment(last_mood['sentiment'])
        
        # Default to neutral if still not set
        if emotion is None:
            emotion = Emotion.NEUTRAL
        if sentiment is None:
            sentiment = Sentiment.NEUTRAL
        
        # Find matching template
        template_key = f"{emotion.value}_{sentiment.value}"
        template = self.templates.get(template_key)
        
        if not template:
            # Try to find a close match
            for t in self.templates.values():
                if t.emotion == emotion:
                    template = t
                    break
            
            if not template:
                # Use neutral template
                template = self.templates.get('neutral_neutral')
        
        if template:
            # Select a variation
            import random
            selected_template = random.choice([template.template] + template.variations)
            
            # Insert base response
            adapted_response = selected_template.format(response=base_response)
            return adapted_response
        
        return base_response

    def add_custom_template(self, emotion: Emotion, sentiment: Sentiment,
                          style: ResponseStyle, template: str,
                          variations: List[str] = None) -> ResponseTemplate:
        """Add a custom response template."""
        template_id = f"{emotion.value}_{sentiment.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        new_template = ResponseTemplate(
            template_id=template_id,
            emotion=emotion,
            sentiment=sentiment,
            style=style,
            template=template,
            variations=variations or [],
            created_at=datetime.now().isoformat()
        )
        
        self.templates[template_id] = new_template
        self._save_templates()
        
        return new_template

    def get_user_mood_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get mood history for a user."""
        if user_id not in self.user_profiles:
            return []
        
        profile = self.user_profiles[user_id]
        return profile.mood_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get adaptive response statistics."""
        total_templates = len(self.templates)
        total_users = len(self.user_profiles)
        
        # Count by style
        by_style = defaultdict(int)
        for template in self.templates.values():
            by_style[template.style.value] += 1
        
        # Count by emotion
        by_emotion = defaultdict(int)
        for template in self.templates.values():
            by_emotion[template.emotion.value] += 1
        
        return {
            'total_templates': total_templates,
            'total_users': total_users,
            'by_style': dict(by_style),
            'by_emotion': dict(by_emotion)
        }
