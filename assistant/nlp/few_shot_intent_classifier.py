"""
Few-Shot Learning Intent Classifier
Enhances intent classification with few-shot learning capabilities using examples and patterns.
"""

import os
import json
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import numpy as np


@dataclass
class IntentExample:
    text: str
    intent: str
    confidence: float
    source: str  # 'user', 'system', 'pretrained'
    created_at: str
    metadata: Dict[str, Any] = None


@dataclass
class FewShotPrediction:
    intent: str
    confidence: float
    matched_examples: List[IntentExample]
    reasoning: str


class FewShotIntentClassifier:
    def __init__(self, base_classifier=None):
        self.base_classifier = base_classifier
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.examples_file = os.path.join(self.base_dir, "data", "intent_examples.json")
        self.patterns_file = os.path.join(self.base_dir, "data", "intent_patterns.json")
        
        # Load examples and patterns
        self.examples = self._load_examples()
        self.patterns = self._load_patterns()
        
        # Initialize example index
        self.example_index = self._build_example_index()
        
        # Initialize with pretrained examples
        self._initialize_pretrained_examples()

    def _load_examples(self) -> Dict[str, List[IntentExample]]:
        """Load intent examples from disk."""
        if os.path.exists(self.examples_file):
            try:
                with open(self.examples_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {intent: [IntentExample(**ex) for ex in examples] 
                       for intent, examples in data.items()}
            except Exception:
                pass
        return {}

    def _save_examples(self):
        """Save intent examples to disk."""
        try:
            data = {intent: [asdict(ex) for ex in examples] 
                   for intent, examples in self.examples.items()}
            with open(self.examples_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[FewShotClassifier] Failed to save examples: {e}")

    def _load_patterns(self) -> Dict[str, List[str]]:
        """Load intent patterns from disk."""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_patterns(self):
        """Save intent patterns to disk."""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            print(f"[FewShotClassifier] Failed to save patterns: {e}")

    def _build_example_index(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build inverted index of words to examples."""
        index = defaultdict(list)
        
        for intent, examples in self.examples.items():
            for example in examples:
                words = set(example.text.lower().split())
                for word in words:
                    index[word].append((intent, example.text))
        
        return dict(index)

    def _initialize_pretrained_examples(self):
        """Initialize with pretrained intent examples."""
        if not self.examples:
            pretrained_examples = {
                'greeting': [
                    IntentExample(text="hello", intent="greeting", confidence=1.0, 
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="hi there", intent="greeting", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="good morning", intent="greeting", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="hey", intent="greeting", confidence=0.9,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
                'farewell': [
                    IntentExample(text="goodbye", intent="farewell", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="see you later", intent="farewell", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="bye", intent="farewell", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
                'time': [
                    IntentExample(text="what time is it", intent="time", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="current time", intent="time", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="tell me the time", intent="time", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
                'weather': [
                    IntentExample(text="what's the weather", intent="weather", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="weather today", intent="weather", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="is it raining", intent="weather", confidence=0.9,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
                'search': [
                    IntentExample(text="search for", intent="search", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="find information about", intent="search", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="look up", intent="search", confidence=0.9,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
                'calculator': [
                    IntentExample(text="calculate", intent="calculator", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="what is", intent="calculator", confidence=0.8,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="add", intent="calculator", confidence=0.9,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
                'music': [
                    IntentExample(text="play music", intent="music", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="play song", intent="music", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="stop music", intent="music", confidence=1.0,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
                'system_control': [
                    IntentExample(text="open", intent="system_control", confidence=0.9,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="close", intent="system_control", confidence=0.9,
                               source="pretrained", created_at=datetime.now().isoformat()),
                    IntentExample(text="start", intent="system_control", confidence=0.8,
                               source="pretrained", created_at=datetime.now().isoformat()),
                ],
            }
            
            self.examples = pretrained_examples
            self._save_examples()
            self.example_index = self._build_example_index()

    def add_example(self, text: str, intent: str, confidence: float = 1.0,
                   source: str = "user", metadata: Dict[str, Any] = None) -> bool:
        """
        Add a new intent example.
        
        Args:
            text: Example text
            intent: Intent label
            confidence: Confidence score
            source: Source of the example
            metadata: Additional metadata
        """
        try:
            example = IntentExample(
                text=text.lower(),
                intent=intent.lower(),
                confidence=confidence,
                source=source,
                created_at=datetime.now().isoformat(),
                metadata=metadata or {}
            )
            
            if intent not in self.examples:
                self.examples[intent] = []
            
            self.examples[intent].append(example)
            
            # Update index
            words = set(text.lower().split())
            for word in words:
                if word not in self.example_index:
                    self.example_index[word] = []
                self.example_index[word].append((intent, text.lower()))
            
            self._save_examples()
            return True
            
        except Exception as e:
            print(f"[FewShotClassifier] Failed to add example: {e}")
            return False

    def add_pattern(self, intent: str, pattern: str) -> bool:
        """
        Add a regex pattern for an intent.
        
        Args:
            intent: Intent label
            pattern: Regex pattern
        """
        try:
            if intent not in self.patterns:
                self.patterns[intent] = []
            
            self.patterns[intent].append(pattern)
            self._save_patterns()
            return True
            
        except Exception as e:
            print(f"[FewShotClassifier] Failed to add pattern: {e}")
            return False

    def classify(self, text: str, top_k: int = 3) -> FewShotPrediction:
        """
        Classify intent using few-shot learning.
        
        Args:
            text: Input text to classify
            top_k: Number of top intents to consider
            
        Returns:
            FewShotPrediction with intent, confidence, and matched examples
        """
        text_lower = text.lower()
        
        # First, try pattern matching
        pattern_match = self._match_patterns(text_lower)
        if pattern_match:
            return FewShotPrediction(
                intent=pattern_match,
                confidence=0.95,
                matched_examples=self.examples.get(pattern_match, [])[:3],
                reasoning="Matched regex pattern"
            )
        
        # Calculate similarity scores using example matching
        intent_scores = defaultdict(float)
        matched_examples = defaultdict(list)
        
        # Word overlap scoring
        text_words = set(text_lower.split())
        
        for word in text_words:
            if word in self.example_index:
                for intent, example_text in self.example_index[word]:
                    intent_scores[intent] += 1
                    # Find the actual example
                    for example in self.examples.get(intent, []):
                        if example.text == example_text:
                            matched_examples[intent].append(example)
                            break
        
        # Normalize scores
        max_score = max(intent_scores.values()) if intent_scores else 0
        if max_score > 0:
            for intent in intent_scores:
                intent_scores[intent] /= max_score
        
        # If no matches, try base classifier
        if not intent_scores and self.base_classifier:
            try:
                base_result = self.base_classifier.get_intent(text)
                return FewShotPrediction(
                    intent=base_result['intent'],
                    confidence=base_result.get('confidence', 0.7),
                    matched_examples=[],
                    reasoning="Base classifier fallback"
                )
            except Exception:
                pass
        
        # Return top prediction
        if intent_scores:
            top_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[top_intent]
            
            return FewShotPrediction(
                intent=top_intent,
                confidence=confidence,
                matched_examples=matched_examples[top_intent][:5],
                reasoning=f"Matched {len(matched_examples[top_intent])} examples with word overlap"
            )
        
        # Default to unknown
        return FewShotPrediction(
            intent="unknown",
            confidence=0.0,
            matched_examples=[],
            reasoning="No matching examples found"
        )

    def _match_patterns(self, text: str) -> Optional[str]:
        """Match text against intent patterns."""
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        return intent
                except re.error:
                    continue
        return None

    def classify_with_explanation(self, text: str) -> Dict[str, Any]:
        """
        Classify intent with detailed explanation.
        
        Args:
            text: Input text to classify
            
        Returns:
            Detailed classification result with explanation
        """
        prediction = self.classify(text)
        
        explanation = {
            'intent': prediction.intent,
            'confidence': prediction.confidence,
            'reasoning': prediction.reasoning,
            'matched_examples': [
                {
                    'text': ex.text,
                    'intent': ex.intent,
                    'confidence': ex.confidence,
                    'source': ex.source
                }
                for ex in prediction.matched_examples
            ],
            'alternative_intents': self._get_alternative_intents(text, prediction.intent)
        }
        
        return explanation

    def _get_alternative_intents(self, text: str, top_intent: str) -> List[Dict[str, float]]:
        """Get alternative intent predictions."""
        text_lower = text.lower()
        text_words = set(text_lower.split())
        
        intent_scores = defaultdict(float)
        
        for word in text_words:
            if word in self.example_index:
                for intent, _ in self.example_index[word]:
                    if intent != top_intent:
                        intent_scores[intent] += 1
        
        # Normalize and sort
        max_score = max(intent_scores.values()) if intent_scores else 0
        alternatives = []
        
        if max_score > 0:
            for intent, score in sorted(intent_scores.items(), key=lambda x: x[1], reverse=True):
                alternatives.append({
                    'intent': intent,
                    'confidence': score / max_score
                })
        
        return alternatives[:3]

    def get_examples_for_intent(self, intent: str, limit: int = 10) -> List[IntentExample]:
        """Get examples for a specific intent."""
        return self.examples.get(intent, [])[:limit]

    def get_all_intents(self) -> List[str]:
        """Get all available intents."""
        return list(self.examples.keys())

    def get_intent_statistics(self) -> Dict[str, Any]:
        """Get statistics about intent examples."""
        stats = {
            'total_intents': len(self.examples),
            'total_examples': sum(len(examples) for examples in self.examples.values()),
            'intents': {}
        }
        
        for intent, examples in self.examples.items():
            stats['intents'][intent] = {
                'count': len(examples),
                'avg_confidence': sum(ex.confidence for ex in examples) / len(examples) if examples else 0,
                'sources': defaultdict(int)
            }
            
            for example in examples:
                stats['intents'][intent]['sources'][example.source] += 1
        
        return stats

    def remove_example(self, intent: str, text: str) -> bool:
        """Remove an example."""
        if intent not in self.examples:
            return False
        
        text_lower = text.lower()
        original_count = len(self.examples[intent])
        
        self.examples[intent] = [ex for ex in self.examples[intent] if ex.text != text_lower]
        
        if len(self.examples[intent]) == original_count:
            return False
        
        # Rebuild index
        self.example_index = self._build_example_index()
        self._save_examples()
        
        return True

    def update_example_confidence(self, intent: str, text: str, new_confidence: float) -> bool:
        """Update confidence of an existing example."""
        if intent not in self.examples:
            return False
        
        text_lower = text.lower()
        
        for example in self.examples[intent]:
            if example.text == text_lower:
                example.confidence = new_confidence
                self._save_examples()
                return True
        
        return False

    def export_examples(self, export_path: str) -> Tuple[bool, str]:
        """Export examples to a file."""
        try:
            export_data = {
                'examples': {intent: [asdict(ex) for ex in examples] 
                           for intent, examples in self.examples.items()},
                'patterns': self.patterns,
                'exported_at': datetime.now().isoformat(),
                'statistics': self.get_intent_statistics()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Examples exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def import_examples(self, import_path: str) -> Tuple[bool, str]:
        """Import examples from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Import examples
            for intent, examples_data in import_data['examples'].items():
                if intent not in self.examples:
                    self.examples[intent] = []
                
                for ex_data in examples_data:
                    example = IntentExample(**ex_data)
                    self.examples[intent].append(example)
            
            # Import patterns
            if 'patterns' in import_data:
                for intent, patterns in import_data['patterns'].items():
                    if intent not in self.patterns:
                        self.patterns[intent] = []
                    self.patterns[intent].extend(patterns)
            
            # Rebuild index
            self.example_index = self._build_example_index()
            
            self._save_examples()
            self._save_patterns()
            
            return True, f"Examples imported from {import_path}"
            
        except Exception as e:
            return False, f"Import failed: {str(e)}"

    def learn_from_feedback(self, text: str, predicted_intent: str, 
                          correct_intent: str, feedback_type: str = "correction") -> bool:
        """
        Learn from user feedback.
        
        Args:
            text: Original text
            predicted_intent: Intent that was predicted
            correct_intent: Correct intent according to user
            feedback_type: Type of feedback ('correction', 'confirmation', 'rejection')
        """
        try:
            if feedback_type == "correction":
                # Add corrected example
                self.add_example(
                    text=text,
                    intent=correct_intent,
                    confidence=1.0,
                    source="user_correction",
                    metadata={"original_prediction": predicted_intent}
                )
                
                # Reduce confidence of wrong prediction
                if predicted_intent in self.examples:
                    for example in self.examples[predicted_intent]:
                        if example.text == text.lower():
                            example.confidence = max(0.1, example.confidence - 0.3)
                            break
                
                self._save_examples()
                return True
            
            elif feedback_type == "confirmation":
                # Increase confidence of correct prediction
                if predicted_intent in self.examples:
                    for example in self.examples[predicted_intent]:
                        if example.text == text.lower():
                            example.confidence = min(1.0, example.confidence + 0.1)
                            break
                else:
                    # Add new example
                    self.add_example(
                        text=text,
                        intent=predicted_intent,
                        confidence=0.8,
                        source="user_confirmation"
                    )
                
                self._save_examples()
                return True
            
            elif feedback_type == "rejection":
                # Add as negative example (could be implemented differently)
                # For now, just add to unknown intent
                self.add_example(
                    text=text,
                    intent="unknown",
                    confidence=0.5,
                    source="user_rejection",
                    metadata={"rejected_intent": predicted_intent}
                )
                
                self._save_examples()
                return True
            
            return False
            
        except Exception as e:
            print(f"[FewShotClassifier] Failed to learn from feedback: {e}")
            return False

    def suggest_examples(self, intent: str, count: int = 5) -> List[str]:
        """
        Suggest example phrases for an intent based on patterns.
        
        Args:
            intent: Intent to suggest examples for
            count: Number of suggestions to generate
        """
        # This would use an LLM to generate example phrases
        # For now, return existing examples as suggestions
        existing = self.get_examples_for_intent(intent)
        
        if len(existing) >= count:
            return [ex.text for ex in existing[:count]]
        
        # Generate simple variations
        suggestions = []
        for ex in existing:
            words = ex.text.split()
            if len(words) > 2:
                # Simple variation: remove one word
                for i in range(len(words)):
                    variation = ' '.join(words[:i] + words[i+1:])
                    if len(variation.split()) >= 2:
                        suggestions.append(variation)
                        if len(suggestions) >= count:
                            break
            if len(suggestions) >= count:
                break
        
        return suggestions[:count]

    def merge_intents(self, old_intent: str, new_intent: str) -> bool:
        """Merge examples from one intent into another."""
        if old_intent not in self.examples:
            return False
        
        if new_intent not in self.examples:
            self.examples[new_intent] = []
        
        # Move examples
        for example in self.examples[old_intent]:
            example.intent = new_intent
            self.examples[new_intent].append(example)
        
        # Remove old intent
        del self.examples[old_intent]
        
        # Update patterns
        if old_intent in self.patterns:
            if new_intent not in self.patterns:
                self.patterns[new_intent] = []
            self.patterns[new_intent].extend(self.patterns[old_intent])
            del self.patterns[old_intent]
        
        # Rebuild index
        self.example_index = self._build_example_index()
        
        self._save_examples()
        self._save_patterns()
        
        return True

    def prune_examples(self, min_confidence: float = 0.3, max_per_intent: int = 100) -> int:
        """
        Prune low-confidence examples and limit examples per intent.
        
        Args:
            min_confidence: Minimum confidence threshold
            max_per_intent: Maximum examples to keep per intent
            
        Returns:
            Number of examples removed
        """
        removed = 0
        
        for intent in list(self.examples.keys()):
            original_count = len(self.examples[intent])
            
            # Filter by confidence
            self.examples[intent] = [
                ex for ex in self.examples[intent] 
                if ex.confidence >= min_confidence
            ]
            
            # Limit count
            if len(self.examples[intent]) > max_per_intent:
                # Keep highest confidence examples
                self.examples[intent].sort(key=lambda x: x.confidence, reverse=True)
                self.examples[intent] = self.examples[intent][:max_per_intent]
            
            removed += original_count - len(self.examples[intent])
            
            # Remove intent if no examples left
            if not self.examples[intent]:
                del self.examples[intent]
        
        if removed > 0:
            self.example_index = self._build_example_index()
            self._save_examples()
        
        return removed
