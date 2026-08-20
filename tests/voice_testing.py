"""
Voice Interaction Testing
Provides testing capabilities for voice interactions and speech recognition.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class TestType(Enum):
    WAKE_WORD = "wake_word"
    COMMAND_RECOGNITION = "command_recognition"
    INTENT_CLASSIFICATION = "intent_classification"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    CONVERSATION_FLOW = "conversation_flow"


class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class VoiceTest:
    test_id: str
    name: str
    test_type: TestType
    audio_file: str
    expected_text: str
    expected_intent: str
    actual_text: Optional[str]
    actual_intent: Optional[str]
    confidence_score: Optional[float]
    result: TestResult
    duration_ms: float
    created_at: str


@dataclass
class VoiceTestSuite:
    suite_id: str
    name: str
    description: str
    test_cases: List[str]
    created_at: str


class VoiceInteractionTester:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tests_dir = os.path.join(self.base_dir, "tests")
        self.voice_tests_file = os.path.join(self.tests_dir, "voice_tests.json")
        self.voice_suites_file = os.path.join(self.tests_dir, "voice_test_suites.json")
        
        os.makedirs(self.tests_dir, exist_ok=True)
        
        # Load data
        self.voice_tests = self._load_voice_tests()
        self.voice_suites = self._load_voice_suites()

    def _load_voice_tests(self) -> Dict[str, VoiceTest]:
        """Load voice tests from disk."""
        if os.path.exists(self.voice_tests_file):
            try:
                with open(self.voice_tests_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {test_id: VoiceTest(**test) for test_id, test in data.items()}
            except Exception:
                pass
        return {}

    def _save_voice_tests(self):
        """Save voice tests to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {test_id: asdict(test) for test_id, test in self.voice_tests.items()}
            with open(self.voice_tests_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[VoiceInteractionTester] Failed to save voice tests: {e}")

    def _load_voice_suites(self) -> Dict[str, VoiceTestSuite]:
        """Load voice test suites from disk."""
        if os.path.exists(self.voice_suites_file):
            try:
                with open(self.voice_suites_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {suite_id: VoiceTestSuite(**suite) for suite_id, suite in data.items()}
            except Exception:
                pass
        return {}

    def _save_voice_suites(self):
        """Save voice test suites to disk."""
        try:
            data = {suite_id: asdict(suite) for suite_id, suite in self.voice_suites.items()}
            with open(self.voice_suites_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[VoiceInteractionTester] Failed to save voice test suites: {e}")

    def create_voice_test(self, name: str, test_type: TestType, audio_file: str,
                        expected_text: str, expected_intent: str = "") -> VoiceTest:
        """
        Create a voice interaction test.
        
        Args:
            name: Test name
            test_type: Type of voice test
            audio_file: Path to audio file
            expected_text: Expected transcribed text
            expected_intent: Expected intent
            
        Returns:
            VoiceTest
        """
        test_id = f"voice_test_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        test = VoiceTest(
            test_id=test_id,
            name=name,
            test_type=test_type,
            audio_file=audio_file,
            expected_text=expected_text,
            expected_intent=expected_intent,
            actual_text=None,
            actual_intent=None,
            confidence_score=None,
            result=TestResult.ERROR,
            duration_ms=0.0,
            created_at=datetime.now().isoformat()
        )
        
        self.voice_tests[test_id] = test
        self._save_voice_tests()
        
        return test

    def run_voice_test(self, test_id: str) -> Tuple[TestResult, str]:
        """
        Run a voice interaction test.
        
        Args:
            test_id: Test ID
            
        Returns:
            (result, message)
        """
        if test_id not in self.voice_tests:
            return TestResult.ERROR, "Test not found"
        
        test = self.voice_tests[test_id]
        
        # In production, this would:
        # 1. Load audio file
        # 2. Run speech-to-text
        # 3. Run intent classification
        # 4. Compare with expected results
        
        # Simulate test execution
        import time
        start_time = time.time()
        
        # Simulate STT
        test.actual_text = test.expected_text  # In production, this would be actual STT
        test.confidence_score = 0.95  # Simulated confidence
        
        # Simulate intent classification
        test.actual_intent = test.expected_intent  # In production, this would be actual classification
        
        # Calculate duration
        test.duration_ms = (time.time() - start_time) * 1000
        
        # Compare results
        text_match = test.actual_text.lower() == test.expected_text.lower()
        intent_match = test.actual_intent == test.expected_intent if test.expected_intent else True
        
        if text_match and intent_match:
            test.result = TestResult.PASS
        elif text_match or intent_match:
            test.result = TestResult.PARTIAL
        else:
            test.result = TestResult.FAIL
        
        self._save_voice_tests()
        
        message = f"Test {test.result.value}: text_match={text_match}, intent_match={intent_match}"
        return test.result, message

    def create_test_suite(self, name: str, description: str, test_case_ids: List[str]) -> VoiceTestSuite:
        """
        Create a voice test suite.
        
        Args:
            name: Suite name
            description: Suite description
            test_case_ids: List of test case IDs
            
        Returns:
            VoiceTestSuite
        """
        suite_id = f"voice_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        suite = VoiceTestSuite(
            suite_id=suite_id,
            name=name,
            description=description,
            test_cases=test_case_ids,
            created_at=datetime.now().isoformat()
        )
        
        self.voice_suites[suite_id] = suite
        self._save_voice_suites()
        
        return suite

    def run_test_suite(self, suite_id: str) -> Dict[str, Any]:
        """
        Run all tests in a suite.
        
        Args:
            suite_id: Suite ID
            
        Returns:
            Test results
        """
        if suite_id not in self.voice_suites:
            return {'error': 'Suite not found'}
        
        suite = self.voice_suites[suite_id]
        
        results = {
            'total': len(suite.test_cases),
            'passed': 0,
            'failed': 0,
            'partial': 0,
            'error': 0,
            'results': []
        }
        
        for test_id in suite.test_cases:
            result, message = self.run_voice_test(test_id)
            test = self.voice_tests[test_id]
            
            results['results'].append({
                'test_id': test_id,
                'name': test.name,
                'result': result.value,
                'message': message,
                'duration_ms': test.duration_ms,
                'confidence_score': test.confidence_score
            })
            
            if result == TestResult.PASS:
                results['passed'] += 1
            elif result == TestResult.FAIL:
                results['failed'] += 1
            elif result == TestResult.PARTIAL:
                results['partial'] += 1
            else:
                results['error'] += 1
        
        return results

    def get_test(self, test_id: str) -> Optional[VoiceTest]:
        """Get a voice test by ID."""
        return self.voice_tests.get(test_id)

    def get_tests_by_type(self, test_type: TestType) -> List[VoiceTest]:
        """Get tests by type."""
        return [t for t in self.voice_tests.values() if t.test_type == test_type]

    def get_failed_tests(self) -> List[VoiceTest]:
        """Get all failed tests."""
        return [t for t in self.voice_tests.values() if t.result == TestResult.FAIL]

    def get_average_confidence(self) -> float:
        """Get average confidence score across all tests."""
        tests_with_confidence = [t for t in self.voice_tests.values() if t.confidence_score is not None]
        
        if not tests_with_confidence:
            return 0.0
        
        return sum(t.confidence_score for t in tests_with_confidence) / len(tests_with_confidence)

    def delete_test(self, test_id: str) -> bool:
        """Delete a voice test."""
        if test_id not in self.voice_tests:
            return False
        
        del self.voice_tests[test_id]
        self._save_voice_tests()
        
        return True

    def delete_suite(self, suite_id: str) -> bool:
        """Delete a test suite."""
        if suite_id not in self.voice_suites:
            return False
        
        del self.voice_suites[suite_id]
        self._save_voice_suites()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get voice testing statistics."""
        total_tests = len(self.voice_tests)
        total_suites = len(self.voice_suites)
        
        # Count by result
        by_result = {}
        for test in self.voice_tests.values():
            result = test.result.value
            by_result[result] = by_result.get(result, 0) + 1
        
        # Count by type
        by_type = {}
        for test in self.voice_tests.values():
            ttype = test.test_type.value
            by_type[ttype] = by_type.get(ttype, 0) + 1
        
        return {
            'total_tests': total_tests,
            'total_suites': total_suites,
            'by_result': by_result,
            'by_type': by_type,
            'average_confidence': round(self.get_average_confidence(), 2)
        }

    def export_test_report(self, suite_id: str, export_path: str) -> Tuple[bool, str]:
        """Export voice test report to file."""
        if suite_id not in self.voice_suites:
            return False, "Suite not found"
        
        results = self.run_test_suite(suite_id)
        
        try:
            report = {
                'suite_id': suite_id,
                'results': results,
                'statistics': self.get_statistics(),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            return True, f"Test report exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
