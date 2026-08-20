"""
Sentiment Analyzer
Analyzes emotional context from text and audio for emotional intelligence.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class Emotion(Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    CALM = "calm"


class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class EmotionAnalysis:
    analysis_id: str
    text: str
    primary_emotion: Emotion
    secondary_emotion: Optional[Emotion]
    sentiment: Sentiment
    confidence: float
    emotion_scores: Dict[str, float]
    analyzed_at: str
    user_id: Optional[str] = None
    context: Dict[str, Any] = None


class SentimentAnalyzer:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.emotion_dir = os.path.join(self.base_dir, "data", "emotion")
        self.history_file = os.path.join(self.emotion_dir, "analysis_history.json")
        
        os.makedirs(self.emotion_dir, exist_ok=True)
        
        # Load history
        self.analysis_history = self._load_history()
        
        # Emotion lexicons
        self.emotion_lexicons = self._initialize_lexicons()
        
        # Sentiment lexicons
        self.sentiment_lexicons = self._initialize_sentiment_lexicons()

    def _load_history(self) -> Dict[str, EmotionAnalysis]:
        """Load analysis history from disk."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {analysis_id: EmotionAnalysis(**analysis) for analysis_id, analysis in data.items()}
            except Exception:
                pass
        return {}

    def _save_history(self):
        """Save analysis history to disk."""
        try:
            data = {analysis_id: asdict(analysis) for analysis_id, analysis in self.analysis_history.items()}
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SentimentAnalyzer] Failed to save history: {e}")

    def _initialize_lexicons(self) -> Dict[Emotion, List[str]]:
        """Initialize emotion word lexicons."""
        return {
            Emotion.HAPPY: ['happy', 'joy', 'glad', 'delighted', 'pleased', 'cheerful', 'joyful', 'elated', 'ecstatic', 'thrilled', 'content', 'satisfied', 'grateful', 'blessed', 'wonderful', 'amazing', 'great', 'fantastic', 'awesome', 'love', 'enjoy'],
            Emotion.SAD: ['sad', 'unhappy', 'depressed', 'down', 'miserable', 'heartbroken', 'grief', 'sorrow', 'crying', 'tears', 'lonely', 'hopeless', 'devastated', 'upset', 'disappointed', 'regret', 'miss', 'loss'],
            Emotion.ANGRY: ['angry', 'furious', 'mad', 'irate', 'rage', 'annoyed', 'frustrated', 'irritated', 'upset', 'hostile', 'aggressive', 'hate', 'disgusted', 'outraged', 'offended', 'resentful'],
            Emotion.FEARFUL: ['afraid', 'scared', 'fearful', 'terrified', 'anxious', 'worried', 'nervous', 'panic', 'dread', 'apprehensive', 'concerned', 'uneasy', 'frightened', 'horrified'],
            Emotion.DISGUSTED: ['disgusted', 'revolted', 'repulsed', 'sick', 'nauseous', 'appalled', 'dislike', 'hate', 'loathe', 'abhor'],
            Emotion.SURPRISED: ['surprised', 'shocked', 'amazed', 'astonished', 'stunned', 'startled', 'unexpected', 'sudden', 'wow', 'incredible'],
            Emotion.EXCITED: ['excited', 'thrilled', 'pumped', 'energetic', 'enthusiastic', 'eager', 'anticipating', 'cant wait', 'looking forward', 'hyped'],
            Emotion.ANXIOUS: ['anxious', 'worried', 'nervous', 'stressed', 'tense', 'uneasy', 'apprehensive', 'concerned', 'restless', 'overwhelmed'],
            Emotion.CALM: ['calm', 'relaxed', 'peaceful', 'serene', 'tranquil', 'composed', 'collected', 'steady', 'unperturbed', 'at ease']
        }

    def _initialize_sentiment_lexicons(self) -> Dict[Sentiment, List[str]]:
        """Initialize sentiment word lexicons."""
        return {
            Sentiment.POSITIVE: ['good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic', 'awesome', 'love', 'like', 'happy', 'pleased', 'satisfied', 'delighted', 'enjoy', 'best', 'better', 'beautiful', 'perfect', 'brilliant', 'success', 'win', 'positive'],
            Sentiment.NEGATIVE: ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike', 'sad', 'angry', 'upset', 'disappointed', 'frustrated', 'fail', 'failure', 'negative', 'wrong', 'problem', 'issue', 'error', 'mistake', 'poor']
        }

    def analyze_text(self, text: str, user_id: str = None) -> EmotionAnalysis:
        """
        Analyze sentiment and emotion from text.
        
        Args:
            text: Text to analyze
            user_id: User ID for tracking
            
        Returns:
            EmotionAnalysis with results
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        # Calculate emotion scores
        emotion_scores = {}
        for emotion, lexicon in self.emotion_lexicons.items():
            score = 0
            for word in words:
                if word in lexicon:
                    score += 1
            emotion_scores[emotion.value] = score / len(words) if words else 0
        
        # Determine primary emotion
        if not any(emotion_scores.values()):
            primary_emotion = Emotion.NEUTRAL
            confidence = 0.5
        else:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[primary_emotion.value]
        
        # Determine secondary emotion
        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        secondary_emotion = None
        if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0:
            secondary_emotion = Emotion(sorted_emotions[1][0])
        
        # Determine sentiment
        positive_score = sum(1 for word in words if word in self.sentiment_lexicons[Sentiment.POSITIVE])
        negative_score = sum(1 for word in words if word in self.sentiment_lexicons[Sentiment.NEGATIVE])
        
        if positive_score > negative_score:
            sentiment = Sentiment.POSITIVE
        elif negative_score > positive_score:
            sentiment = Sentiment.NEGATIVE
        elif positive_score == negative_score and positive_score > 0:
            sentiment = Sentiment.MIXED
        else:
            sentiment = Sentiment.NEUTRAL
        
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        analysis = EmotionAnalysis(
            analysis_id=analysis_id,
            text=text,
            primary_emotion=primary_emotion,
            secondary_emotion=secondary_emotion,
            sentiment=sentiment,
            confidence=min(1.0, confidence * 10),  # Scale confidence
            emotion_scores=emotion_scores,
            analyzed_at=datetime.now().isoformat(),
            user_id=user_id,
            context={'word_count': len(words)}
        )
        
        self.analysis_history[analysis_id] = analysis
        self._save_history()
        
        return analysis

    def analyze_conversation_context(self, messages: List[str], user_id: str = None) -> Dict[str, Any]:
        """
        Analyze emotional context of a conversation.
        
        Args:
            messages: List of messages in conversation
            user_id: User ID
            
        Returns:
            Context analysis summary
        """
        analyses = [self.analyze_text(msg, user_id) for msg in messages]
        
        # Count emotions
        emotion_counts = defaultdict(int)
        sentiment_counts = defaultdict(int)
        
        for analysis in analyses:
            emotion_counts[analysis.primary_emotion.value] += 1
            sentiment_counts[analysis.sentiment.value] += 1
        
        # Calculate averages
        avg_confidence = sum(a.confidence for a in analyses) / len(analyses) if analyses else 0
        
        # Determine overall sentiment
        if sentiment_counts[Sentiment.POSITIVE.value] > sentiment_counts[Sentiment.NEGATIVE.value]:
            overall_sentiment = Sentiment.POSITIVE
        elif sentiment_counts[Sentiment.NEGATIVE.value] > sentiment_counts[Sentiment.POSITIVE.value]:
            overall_sentiment = Sentiment.NEGATIVE
        else:
            overall_sentiment = Sentiment.NEUTRAL
        
        # Detect emotion trends
        if len(analyses) >= 3:
            recent = analyses[-3:]
            emotion_trend = [a.primary_emotion.value for a in recent]
        else:
            emotion_trend = []
        
        return {
            'total_messages': len(messages),
            'emotion_distribution': dict(emotion_counts),
            'sentiment_distribution': dict(sentiment_counts),
            'overall_sentiment': overall_sentiment.value,
            'average_confidence': round(avg_confidence, 2),
            'emotion_trend': emotion_trend,
            'dominant_emotion': max(emotion_counts, key=emotion_counts.get) if emotion_counts else Emotion.NEUTRAL.value
        }

    def get_user_emotion_profile(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get emotion profile for a user over time.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            User emotion profile
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        user_analyses = [
            analysis for analysis in self.analysis_history.values()
            if analysis.user_id == user_id and datetime.fromisoformat(analysis.analyzed_at) >= cutoff_date
        ]
        
        if not user_analyses:
            return {'message': 'No data available for user'}
        
        # Count emotions
        emotion_counts = defaultdict(int)
        sentiment_counts = defaultdict(int)
        
        for analysis in user_analyses:
            emotion_counts[analysis.primary_emotion.value] += 1
            sentiment_counts[analysis.sentiment.value] += 1
        
        # Calculate averages
        avg_confidence = sum(a.confidence for a in user_analyses) / len(user_analyses)
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_analyses': len(user_analyses),
            'emotion_distribution': dict(emotion_counts),
            'sentiment_distribution': dict(sentiment_counts),
            'average_confidence': round(avg_confidence, 2),
            'dominant_emotion': max(emotion_counts, key=emotion_counts.get),
            'dominant_sentiment': max(sentiment_counts, key=sentiment_counts.get)
        }

    def suggest_response_tone(self, emotion: Emotion) -> str:
        """
        Suggest appropriate response tone based on detected emotion.
        
        Args:
            emotion: Detected emotion
            
        Returns:
            Suggested response tone
        """
        tone_mapping = {
            Emotion.HAPPY: "enthusiastic and positive",
            Emotion.SAD: "empathetic and supportive",
            Emotion.ANGRY: "calm and understanding",
            Emotion.FEARFUL: "reassuring and confident",
            Emotion.DISGUSTED: "neutral and objective",
            Emotion.SURPRISED: "attentive and responsive",
            Emotion.NEUTRAL: "professional and helpful",
            Emotion.EXCITED: "energetic and engaging",
            Emotion.ANXIOUS: "calming and reassuring",
            Emotion.CALM: "relaxed and friendly"
        }
        
        return tone_mapping.get(emotion, "professional and helpful")

    def get_emotion_statistics(self) -> Dict[str, Any]:
        """Get overall emotion analysis statistics."""
        total_analyses = len(self.analysis_history)
        
        if total_analyses == 0:
            return {'total_analyses': 0, 'by_emotion': {}, 'by_sentiment': {}}
        
        # Count by emotion
        by_emotion = defaultdict(int)
        for analysis in self.analysis_history.values():
            by_emotion[analysis.primary_emotion.value] += 1
        
        # Count by sentiment
        by_sentiment = defaultdict(int)
        for analysis in self.analysis_history.values():
            by_sentiment[analysis.sentiment.value] += 1
        
        return {
            'total_analyses': total_analyses,
            'by_emotion': dict(by_emotion),
            'by_sentiment': dict(by_sentiment)
        }

    def clear_old_analyses(self, days: int = 90) -> int:
        """Clear analyses older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            analysis_id for analysis_id, analysis in self.analysis_history.items()
            if datetime.fromisoformat(analysis.analyzed_at) < cutoff_date
        ]
        
        for analysis_id in to_remove:
            del self.analysis_history[analysis_id]
        
        if to_remove:
            self._save_history()
        
        return len(to_remove)
