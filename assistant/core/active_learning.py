"""
Active Learning and Clarification System
Implements active learning by asking for clarification on ambiguous queries and learning from feedback.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re


class AmbiguityType(Enum):
    MULTIPLE_INTENTS = "multiple_intents"
    MISSING_CONTEXT = "missing_context"
    UNCLEAR_REFERENCE = "unclear_reference"
    VAGUE_REQUEST = "vague_request"
    CONFLICTING_INFO = "conflicting_info"


class ClarificationStrategy(Enum):
    DIRECT_QUESTION = "direct_question"
    MULTIPLE_CHOICE = "multiple_choice"
    CONTEXT_REQUEST = "context_request"
    CONFIRMATION = "confirmation"


@dataclass
class AmbiguityDetection:
    query: str
    ambiguity_type: AmbiguityType
    confidence: float
    detected_at: str
    suggested_clarifications: List[str]
    context_needed: List[str]


@dataclass
class ClarificationRequest:
    request_id: str
    original_query: str
    ambiguity_detection: AmbiguityDetection
    strategy: ClarificationStrategy
    question: str
    options: List[str] = None
    context_provided: Dict[str, Any] = None
    resolved: bool = False
    resolution: str = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class LearningEvent:
    event_id: str
    query: str
    prediction: str
    user_feedback: str
    confidence: float
    learned_at: str
    metadata: Dict[str, Any] = None


class ActiveLearningSystem:
    def __init__(self, intent_classifier=None):
        self.intent_classifier = intent_classifier
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.clarifications_file = os.path.join(self.base_dir, "data", "clarifications.json")
        self.learning_events_file = os.path.join(self.base_dir, "data", "learning_events.json")
        
        # Load data
        self.clarification_history = self._load_clarifications()
        self.learning_events = self._load_learning_events()
        
        # Ambiguity patterns
        self.ambiguity_patterns = self._initialize_ambiguity_patterns()
        
        # Learning statistics
        self.learning_stats = self._calculate_learning_stats()

    def _load_clarifications(self) -> Dict[str, ClarificationRequest]:
        """Load clarification history from disk."""
        if os.path.exists(self.clarifications_file):
            try:
                with open(self.clarifications_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {req_id: ClarificationRequest(**req) for req_id, req in data.items()}
            except Exception:
                pass
        return {}

    def _save_clarifications(self):
        """Save clarification history to disk."""
        try:
            data = {req_id: asdict(req) for req_id, req in self.clarification_history.items()}
            with open(self.clarifications_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ActiveLearning] Failed to save clarifications: {e}")

    def _load_learning_events(self) -> Dict[str, LearningEvent]:
        """Load learning events from disk."""
        if os.path.exists(self.learning_events_file):
            try:
                with open(self.learning_events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {event_id: LearningEvent(**event) for event_id, event in data.items()}
            except Exception:
                pass
        return {}

    def _save_learning_events(self):
        """Save learning events to disk."""
        try:
            data = {event_id: asdict(event) for event_id, event in self.learning_events.items()}
            with open(self.learning_events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ActiveLearning] Failed to save learning events: {e}")

    def _initialize_ambiguity_patterns(self) -> Dict[AmbiguityType, List[str]]:
        """Initialize patterns for detecting ambiguity."""
        return {
            AmbiguityType.MULTIPLE_INTENTS: [
                r'\b(play|open|start|run)\b',  # Could be music, app, or system
                r'\b(send|write|create)\b',  # Could be email, message, or document
                r'\b(check|look at|see)\b',  # Could be weather, time, or file
            ],
            AmbiguityType.MISSING_CONTEXT: [
                r'\bit\b',  # "it" without context
                r'\bthat\b',  # "that" without context
                r'\bthis one\b',  # "this one" without context
            ],
            AmbiguityType.UNCLEAR_REFERENCE: [
                r'\bthe (file|document|app|song)\b',  # Which one?
                r'\bmy (calendar|schedule|email)\b',  # Which account?
            ],
            AmbiguityType.VAGUE_REQUEST: [
                r'\bdo something\b',
                r'\bhelp me\b',
                r'\bfix it\b',
            ],
            AmbiguityType.CONFLICTING_INFO: [
                r'\b(but|however|although)\b',  # May indicate conflicting requirements
            ]
        }

    def _calculate_learning_stats(self) -> Dict[str, Any]:
        """Calculate learning statistics."""
        total_events = len(self.learning_events)
        if total_events == 0:
            return {'total_events': 0, 'accuracy_improvement': 0.0}
        
        # Calculate recent accuracy improvement
        recent_events = sorted(self.learning_events.values(), 
                             key=lambda x: x.learned_at, reverse=True)[:100]
        
        positive_feedback = sum(1 for event in recent_events 
                              if event.user_feedback in ['correct', 'helpful'])
        
        return {
            'total_events': total_events,
            'recent_accuracy': positive_feedback / len(recent_events) if recent_events else 0,
            'clarification_resolution_rate': sum(1 for req in self.clarification_history.values() 
                                               if req.resolved) / len(self.clarification_history) 
                                           if self.clarification_history else 0
        }

    def detect_ambiguity(self, query: str) -> Optional[AmbiguityDetection]:
        """
        Detect if a query is ambiguous and needs clarification.
        
        Args:
            query: User query to analyze
            
        Returns:
            AmbiguityDetection if ambiguity found, None otherwise
        """
        query_lower = query.lower()
        
        # Check against ambiguity patterns
        for ambiguity_type, patterns in self.ambiguity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    # Calculate confidence based on pattern match strength
                    confidence = self._calculate_ambiguity_confidence(query, pattern)
                    
                    if confidence > 0.5:
                        suggested_clarifications = self._generate_clarifications(
                            query, ambiguity_type
                        )
                        
                        return AmbiguityDetection(
                            query=query,
                            ambiguity_type=ambiguity_type,
                            confidence=confidence,
                            detected_at=datetime.now().isoformat(),
                            suggested_clarifications=suggested_clarifications,
                            context_needed=self._identify_context_needed(query, ambiguity_type)
                        )
        
        # Check for low-confidence intent predictions
        if self.intent_classifier:
            try:
                prediction = self.intent_classifier.classify(query)
                if prediction.confidence < 0.6:
                    return AmbiguityDetection(
                        query=query,
                        ambiguity_type=AmbiguityType.MULTIPLE_INTENTS,
                        confidence=1.0 - prediction.confidence,
                        detected_at=datetime.now().isoformat(),
                        suggested_clarifications=[
                            f"Did you mean to {prediction.intent}?",
                            "Could you provide more details?"
                        ],
                        context_needed=['intent', 'specific_action']
                    )
            except Exception:
                pass
        
        return None

    def _calculate_ambiguity_confidence(self, query: str, pattern: str) -> float:
        """Calculate confidence score for ambiguity detection."""
        # Simple heuristic: pattern match strength
        match = re.search(pattern, query.lower(), re.IGNORECASE)
        if match:
            # Longer matches indicate higher confidence
            match_length = len(match.group())
            query_length = len(query)
            return min(0.9, 0.5 + (match_length / query_length) * 0.4)
        return 0.5

    def _generate_clarifications(self, query: str, 
                                ambiguity_type: AmbiguityType) -> List[str]:
        """Generate suggested clarification questions."""
        query_lower = query.lower()
        
        if ambiguity_type == AmbiguityType.MULTIPLE_INTENTS:
            if 'play' in query_lower:
                return [
                    "Do you want to play music, a video, or a game?",
                    "What would you like to play?"
                ]
            elif 'open' in query_lower:
                return [
                    "What application or file would you like to open?",
                    "Should I open an app, a file, or a website?"
                ]
            elif 'send' in query_lower:
                return [
                    "Do you want to send an email, a message, or a file?",
                    "Who should I send it to?"
                ]
            else:
                return ["Could you clarify what you'd like me to do?"]
        
        elif ambiguity_type == AmbiguityType.MISSING_CONTEXT:
            if 'it' in query_lower:
                return ["What does 'it' refer to?"]
            elif 'that' in query_lower:
                return ["What are you referring to with 'that'?"]
            else:
                return ["Could you provide more context?"]
        
        elif ambiguity_type == AmbiguityType.UNCLEAR_REFERENCE:
            if 'file' in query_lower:
                return ["Which file are you referring to?"]
            elif 'app' in query_lower:
                return ["Which application would you like me to use?"]
            else:
                return ["Could you specify which one you mean?"]
        
        elif ambiguity_type == AmbiguityType.VAGUE_REQUEST:
            return [
                "Could you be more specific about what you need?",
                "What task would you like me to help you with?"
            ]
        
        elif ambiguity_type == AmbiguityType.CONFLICTING_INFO:
            return [
                "I noticed some conflicting information. Could you clarify?",
                "Which aspect should I prioritize?"
            ]
        
        return ["Could you please clarify your request?"]

    def _identify_context_needed(self, query: str, 
                                ambiguity_type: AmbiguityType) -> List[str]:
        """Identify what context information is needed."""
        query_lower = query.lower()
        
        if ambiguity_type == AmbiguityType.MULTIPLE_INTENTS:
            return ['intent', 'specific_action']
        elif ambiguity_type == AmbiguityType.MISSING_CONTEXT:
            return ['previous_context', 'referenced_object']
        elif ambiguity_type == AmbiguityType.UNCLEAR_REFERENCE:
            return ['specific_identifier', 'selection_criteria']
        elif ambiguity_type == AmbiguityType.VAGUE_REQUEST:
            return ['task_description', 'desired_outcome']
        elif ambiguity_type == AmbiguityType.CONFLICTING_INFO:
            return ['priority', 'resolution_strategy']
        
        return []

    def create_clarification_request(self, query: str, 
                                    ambiguity_detection: AmbiguityDetection,
                                    strategy: ClarificationStrategy = None) -> ClarificationRequest:
        """
        Create a clarification request for the user.
        
        Args:
            query: Original ambiguous query
            ambiguity_detection: Detected ambiguity
            strategy: Clarification strategy to use
            
        Returns:
            ClarificationRequest with question and options
        """
        if strategy is None:
            strategy = self._select_strategy(ambiguity_detection)
        
        request_id = f"clarif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        question, options = self._generate_clarification_question(
            query, ambiguity_detection, strategy
        )
        
        request = ClarificationRequest(
            request_id=request_id,
            original_query=query,
            ambiguity_detection=ambiguity_detection,
            strategy=strategy,
            question=question,
            options=options
        )
        
        self.clarification_history[request_id] = request
        self._save_clarifications()
        
        return request

    def _select_strategy(self, ambiguity_detection: AmbiguityDetection) -> ClarificationStrategy:
        """Select the best clarification strategy based on ambiguity type."""
        if ambiguity_detection.ambiguity_type == AmbiguityType.MULTIPLE_INTENTS:
            return ClarificationStrategy.MULTIPLE_CHOICE
        elif ambiguity_detection.ambiguity_type == AmbiguityType.MISSING_CONTEXT:
            return ClarificationStrategy.CONTEXT_REQUEST
        elif ambiguity_detection.ambiguity_type == AmbiguityType.UNCLEAR_REFERENCE:
            return ClarificationStrategy.DIRECT_QUESTION
        else:
            return ClarificationStrategy.DIRECT_QUESTION

    def _generate_clarification_question(self, query: str,
                                        ambiguity_detection: AmbiguityDetection,
                                        strategy: ClarificationStrategy) -> Tuple[str, List[str]]:
        """Generate the clarification question and options."""
        if strategy == ClarificationStrategy.MULTIPLE_CHOICE:
            question = f"I'm not sure what you mean by '{query}'. Which of these did you intend?"
            options = ambiguity_detection.suggested_clarifications[:4]
            return question, options
        
        elif strategy == ClarificationStrategy.CONTEXT_REQUEST:
            question = f"To help you better with '{query}', could you provide some context?"
            options = ambiguity_detection.suggested_clarifications[:3]
            return question, options
        
        elif strategy == ClarificationStrategy.DIRECT_QUESTION:
            question = ambiguity_detection.suggested_clarifications[0]
            options = None
            return question, options
        
        elif strategy == ClarificationStrategy.CONFIRMATION:
            question = f"You said '{query}'. Did you mean:"
            options = ambiguity_detection.suggested_clarifications[:3]
            return question, options
        
        return "Could you please clarify?", None

    def resolve_clarification(self, request_id: str, user_response: str) -> bool:
        """
        Resolve a clarification request with user's response.
        
        Args:
            request_id: ID of the clarification request
            user_response: User's response to the clarification
            
        Returns:
            True if resolved successfully
        """
        if request_id not in self.clarification_history:
            return False
        
        request = self.clarification_history[request_id]
        request.resolved = True
        request.resolution = user_response
        request.context_provided = {
            'user_response': user_response,
            'resolved_at': datetime.now().isoformat()
        }
        
        self._save_clarifications()
        
        # Learn from this resolution
        self._learn_from_clarification(request, user_response)
        
        return True

    def _learn_from_clarification(self, request: ClarificationRequest, user_response: str):
        """Learn from a resolved clarification request."""
        event_id = f"learn_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create learning event
        event = LearningEvent(
            event_id=event_id,
            query=request.original_query,
            prediction=request.ambiguity_detection.ambiguity_type.value,
            user_feedback=user_response,
            confidence=request.ambiguity_detection.confidence,
            learned_at=datetime.now().isoformat(),
            metadata={
                'clarification_strategy': request.strategy.value,
                'context_needed': request.ambiguity_detection.context_needed
            }
        )
        
        self.learning_events[event_id] = event
        self._save_learning_events()
        
        # Update statistics
        self.learning_stats = self._calculate_learning_stats()

    def record_feedback(self, query: str, prediction: str, 
                      feedback: str, confidence: float = 1.0):
        """
        Record user feedback on a prediction.
        
        Args:
            query: Original query
            prediction: System's prediction
            feedback: User feedback ('correct', 'incorrect', 'helpful', 'not_helpful')
            confidence: Confidence of the prediction
        """
        event_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        event = LearningEvent(
            event_id=event_id,
            query=query,
            prediction=prediction,
            user_feedback=feedback,
            confidence=confidence,
            learned_at=datetime.now().isoformat(),
            metadata={'type': 'feedback'}
        )
        
        self.learning_events[event_id] = event
        self._save_learning_events()
        
        # Update statistics
        self.learning_stats = self._calculate_learning_stats()

    def should_ask_for_clarification(self, query: str, 
                                   threshold: float = 0.7) -> bool:
        """
        Determine if clarification should be requested.
        
        Args:
            query: User query
            threshold: Confidence threshold below which to ask
            
        Returns:
            True if clarification should be requested
        """
        ambiguity = self.detect_ambiguity(query)
        
        if ambiguity and ambiguity.confidence > threshold:
            return True
        
        # Check if similar queries have been clarified before
        if self._has_similar_resolved_clarification(query):
            return False
        
        return False

    def _has_similar_resolved_clarification(self, query: str) -> bool:
        """Check if a similar query has been resolved before."""
        query_lower = query.lower()
        
        for request in self.clarification_history.values():
            if request.resolved:
                # Simple similarity check
                if query_lower in request.original_query.lower() or \
                   request.original_query.lower() in query_lower:
                    return True
        
        return False

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning events."""
        if not self.learning_events:
            return {'message': 'No learning events recorded yet'}
        
        # Analyze common ambiguity types
        ambiguity_counts = {}
        for event in self.learning_events.values():
            if event.prediction in ambiguity_counts:
                ambiguity_counts[event.prediction] += 1
            else:
                ambiguity_counts[event.prediction] = 1
        
        # Analyze feedback patterns
        feedback_counts = {}
        for event in self.learning_events.values():
            if event.user_feedback in feedback_counts:
                feedback_counts[event.user_feedback] += 1
            else:
                feedback_counts[event.user_feedback] = 1
        
        return {
            'total_learning_events': len(self.learning_events),
            'ambiguity_types': ambiguity_counts,
            'feedback_distribution': feedback_counts,
            'learning_stats': self.learning_stats
        }

    def suggest_improvements(self) -> List[str]:
        """Suggest improvements based on learning insights."""
        insights = self.get_learning_insights()
        suggestions = []
        
        if 'ambiguity_types' in insights:
            # Find most common ambiguity type
            if insights['ambiguity_types']:
                most_common = max(insights['ambiguity_types'].items(), 
                                key=lambda x: x[1])
                suggestions.append(
                    f"Most common ambiguity: {most_common[0]} ({most_common[1]} occurrences). "
                    f"Consider adding more examples for this pattern."
                )
        
        if 'learning_stats' in insights:
            stats = insights['learning_stats']
            if stats.get('clarification_resolution_rate', 0) < 0.7:
                suggestions.append(
                    "Clarification resolution rate is low. Consider improving clarification questions."
                )
        
        if 'feedback_distribution' in insights:
            feedback = insights['feedback_distribution']
            if feedback.get('incorrect', 0) > feedback.get('correct', 0):
                suggestions.append(
                    "Incorrect predictions outnumber correct ones. Review intent classification patterns."
                )
        
        return suggestions

    def export_learning_data(self, export_path: str) -> Tuple[bool, str]:
        """Export learning data for analysis."""
        try:
            export_data = {
                'clarifications': {req_id: asdict(req) for req_id, req 
                                in self.clarification_history.items()},
                'learning_events': {event_id: asdict(event) for event_id, event 
                                  in self.learning_events.items()},
                'learning_stats': self.learning_stats,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Learning data exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def clear_old_events(self, days: int = 30) -> int:
        """Clear learning events older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        removed = 0
        for event_id, event in list(self.learning_events.items()):
            event_date = datetime.fromisoformat(event.learned_at)
            if event_date < cutoff_date:
                del self.learning_events[event_id]
                removed += 1
        
        if removed > 0:
            self._save_learning_events()
            self.learning_stats = self._calculate_learning_stats()
        
        return removed

    def get_clarification_statistics(self) -> Dict[str, Any]:
        """Get statistics about clarification requests."""
        total_requests = len(self.clarification_history)
        resolved = sum(1 for req in self.clarification_history.values() if req.resolved)
        
        # Count by ambiguity type
        type_counts = {}
        for req in self.clarification_history.values():
            amb_type = req.ambiguity_detection.ambiguity_type.value
            type_counts[amb_type] = type_counts.get(amb_type, 0) + 1
        
        # Count by strategy
        strategy_counts = {}
        for req in self.clarification_history.values():
            strategy = req.strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_requests': total_requests,
            'resolved_requests': resolved,
            'resolution_rate': resolved / total_requests if total_requests > 0 else 0,
            'ambiguity_types': type_counts,
            'strategies_used': strategy_counts
        }
