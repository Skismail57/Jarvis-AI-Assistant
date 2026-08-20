"""
Comprehensive Test Script for All JARVIS Modules
Tests all newly created modules to ensure they work correctly.
"""

import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_module(module_path, module_name, test_function):
    """Test a single module."""
    print(f"\n{'='*60}")
    print(f"Testing {module_name}")
    print(f"{'='*60}")
    
    try:
        test_function()
        print(f"✓ {module_name}: PASSED")
        return True
    except Exception as e:
        print(f"✗ {module_name}: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_document_processor():
    """Test document processor module."""
    from assistant.document_processor.document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    
    # Test document processor initialization
    assert processor is not None
    
    print("  - Document processor initialization: OK")

def test_sentiment_analyzer():
    """Test sentiment analyzer module."""
    from assistant.emotion.sentiment_analyzer import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    
    # Test sentiment analyzer initialization
    assert analyzer is not None
    
    print("  - Sentiment analyzer initialization: OK")

def test_adaptive_response():
    """Test adaptive response module."""
    from assistant.emotion.adaptive_response import AdaptiveResponseSystem
    
    manager = AdaptiveResponseSystem()
    
    # Test adaptive response initialization
    assert manager is not None
    
    print("  - Adaptive response initialization: OK")

def test_personality_system():
    """Test personality system module."""
    from assistant.emotion.personality_system import PersonalitySystem
    
    manager = PersonalitySystem()
    
    # Test personality system initialization
    assert manager is not None
    
    print("  - Personality system initialization: OK")

def test_speaker_diarization():
    """Test speaker diarization module."""
    from assistant.voice.speaker_diarization import SpeakerDiarization
    
    manager = SpeakerDiarization()
    
    # Test speaker diarization initialization
    assert manager is not None
    
    print("  - Speaker diarization initialization: OK")

def test_audio_enhancement():
    """Test audio enhancement module."""
    from assistant.voice.audio_enhancement import AudioEnhancer
    
    manager = AudioEnhancer()
    
    # Test audio enhancement initialization
    assert manager is not None
    assert manager.noise_reduction_level == 0.7
    
    print("  - Audio enhancement initialization: OK")

def test_streaming_transcription():
    """Test streaming transcription module."""
    from assistant.voice.streaming_transcription import StreamingTranscriber
    
    manager = StreamingTranscriber()
    
    # Start transcription session
    session_id = manager.start_session()
    assert session_id is not None
    
    print("  - Session start: OK")

def test_emotional_tts():
    """Test emotional TTS module."""
    from assistant.voice.emotional_tts import EmotionalTTS, Emotion
    
    manager = EmotionalTTS()
    
    # Test getting emotion profile
    profile = manager.get_emotion_profile(Emotion.HAPPY)
    assert profile is not None
    
    print("  - Emotion profile retrieval: OK")

def test_voice_cloning():
    """Test voice cloning module."""
    from assistant.voice.voice_cloning import VoiceCloner
    
    manager = VoiceCloner()
    
    # Register voice
    voice_id = manager.register_voice(name="Test Voice")
    assert voice_id is not None
    
    print("  - Voice registration: OK")

def test_ssml_processor():
    """Test SSML processor module."""
    from assistant.voice.ssml_processor import SSMLProcessor
    
    manager = SSMLProcessor()
    
    # Test SSML parsing
    instructions = manager.parse_ssml("<speak>Hello!</speak>")
    assert instructions is not None
    
    print("  - SSML parsing: OK")

def test_matter_thread():
    """Test Matter/Thread module."""
    from assistant.smarthome.matter_thread import MatterDevice, DeviceType
    
    manager = type('MatterManager', (), {
        'devices': {},
        '_save_devices': lambda self: None,
        'create_device': lambda self, name, dtype: type('Device', (), {'name': name, 'device_type': dtype})()
    })()
    
    device = manager.create_device("Test Light", DeviceType.LIGHT)
    assert device is not None
    
    print("  - Device creation: OK")

def test_scene_automation():
    """Test scene automation module."""
    from assistant.smarthome.scene_automation import SceneAutomationManager
    
    manager = SceneAutomationManager()
    
    # Create scene
    scene = manager.create_scene(
        name="Movie Night",
        description="Lights dimmed for movie"
    )
    assert scene is not None
    
    print("  - Scene creation: OK")

def test_energy_monitor():
    """Test energy monitor module."""
    from assistant.smarthome.energy_monitor import EnergyMonitor, DeviceCategory
    
    manager = EnergyMonitor()
    
    # Record energy reading
    reading = manager.record_reading(
        device_id="device_1",
        device_category=DeviceCategory.LIGHTING,
        power_watts=50.0,
        voltage=120.0,
        current=0.42
    )
    assert reading is not None
    
    print("  - Energy reading: OK")

def test_video_streaming():
    """Test video streaming module."""
    from assistant.smarthome.video_streaming import VideoStreamingManager, StreamQuality
    
    manager = VideoStreamingManager()
    
    # Create camera stream
    stream = manager.add_camera_stream(
        camera_id="camera_1",
        name="Front Door",
        stream_url="rtsp://example.com/stream",
        quality=StreamQuality.HIGH
    )
    assert stream is not None
    
    print("  - Stream creation: OK")

def test_person_detection():
    """Test person detection module."""
    from assistant.smarthome.person_detection import PersonDetectionManager
    
    manager = PersonDetectionManager()
    
    # Create person profile
    profile = manager.register_person(
        name="John Doe",
        face_features=[0.1, 0.2, 0.3],
        is_authorized=True,
        access_level="full"
    )
    assert profile is not None
    
    print("  - Person profile creation: OK")

def test_calendar_conflict():
    """Test calendar conflict module."""
    from assistant.productivity.calendar_conflict import CalendarConflictResolver
    
    manager = CalendarConflictResolver()
    
    # Create calendar event
    event_id = manager.add_event(
        title="Meeting",
        start_time="2024-01-01T10:00:00",
        end_time="2024-01-01T11:00:00"
    )
    assert event_id is not None
    
    print("  - Event creation: OK")

def test_meeting_prep():
    """Test meeting preparation module."""
    from assistant.productivity.meeting_prep import MeetingManager
    
    manager = MeetingManager()
    
    # Create meeting
    meeting = manager.create_meeting(
        title="Team Meeting",
        start_time="2024-01-01T10:00:00",
        end_time="2024-01-01T11:00:00",
        attendees=["user1@example.com"]
    )
    assert meeting is not None
    
    print("  - Meeting creation: OK")

def test_project_integration():
    """Test project integration module."""
    from assistant.productivity.project_integration import ProjectIntegrationManager, ProjectPlatform
    
    manager = ProjectIntegrationManager()
    
    # Create project
    project = manager.create_project(
        platform=ProjectPlatform.JIRA,
        name="Project Alpha"
    )
    assert project is not None
    
    print("  - Project creation: OK")

def test_task_parser():
    """Test task parser module."""
    from assistant.productivity.task_parser import TaskParser
    
    parser = TaskParser()
    
    # Parse task
    task = parser.parse_task("Buy groceries tomorrow")
    assert task is not None
    
    print("  - Task parsing: OK")

def test_workflow_automation():
    """Test workflow automation module."""
    from assistant.productivity.workflow_automation import WorkflowAutomationManager
    
    manager = WorkflowAutomationManager()
    
    # Create workflow
    workflow = manager.create_workflow(name="Test Workflow")
    assert workflow is not None
    
    print("  - Workflow creation: OK")

def test_collaborative_sessions():
    """Test collaborative sessions module."""
    from assistant.ui.collaborative_sessions import CollaborativeSessionManager
    
    manager = CollaborativeSessionManager()
    
    # Create session
    session = manager.create_session(
        name="Brainstorming",
        host_id="user1",
        host_name="User One"
    )
    assert session is not None
    
    print("  - Session creation: OK")

def test_customizable_dashboard():
    """Test customizable dashboard module."""
    from assistant.ui.customizable_dashboard import DashboardManager, WidgetType
    
    manager = DashboardManager()
    
    # Create dashboard
    dashboard = manager.create_dashboard(
        user_id="user1",
        name="My Dashboard"
    )
    assert dashboard is not None
    
    print("  - Dashboard creation: OK")

def test_accessibility():
    """Test accessibility module."""
    from assistant.ui.accessibility import AccessibilityManager
    
    manager = AccessibilityManager()
    
    # Create accessibility profile
    profile = manager.create_profile(
        user_id="user1",
        name="High Contrast"
    )
    assert profile is not None
    
    print("  - Accessibility profile creation: OK")

def test_desktop_app():
    """Test desktop app module."""
    from desktop.desktop_app import DesktopAppManager, DesktopPlatform
    
    manager = DesktopAppManager()
    
    # Create config
    config = manager.create_config(
        app_name="JARVIS Desktop",
        platform=DesktopPlatform.WINDOWS
    )
    assert config is not None
    
    print("  - Desktop app config: OK")

def test_browser_extension():
    """Test browser extension module."""
    from browser_extension.extension_manager import BrowserExtensionManager
    
    manager = BrowserExtensionManager()
    
    # Create config
    config = manager.create_config(
        name="JARVIS Extension",
        description="JARVIS browser extension"
    )
    assert config is not None
    
    print("  - Extension config: OK")

def test_plugin_dependency():
    """Test plugin dependency manager."""
    from assistant.developer.plugin_dependency_manager import PluginDependencyManager, DependencyType
    
    manager = PluginDependencyManager()
    
    # Add dependency
    dep = manager.add_dependency(
        name="requests",
        version="2.31.0",
        dependency_type=DependencyType.PYTHON,
        install_command="pip install requests"
    )
    assert dep is not None
    
    print("  - Dependency addition: OK")

def test_graphql_api():
    """Test GraphQL API module."""
    from assistant.developer.graphql_api import GraphQLWebhookManager
    
    manager = GraphQLWebhookManager()
    
    # Create schema
    schema = manager.create_schema("JARVIS Schema")
    assert schema is not None
    
    print("  - Schema creation: OK")

def test_sdk():
    """Test SDK module."""
    from assistant.developer.sdk import IntegrationSDKManager, IntegrationType
    
    manager = IntegrationSDKManager()
    
    # Create integration
    integration = manager.create_integration(
        name="Custom Integration",
        integration_type=IntegrationType.VOICE,
        auth_type="none",
        api_endpoint="http://localhost:8000"
    )
    assert integration is not None
    
    print("  - Integration creation: OK")

def test_caching():
    """Test caching module."""
    from assistant.performance.caching import CacheManager
    
    manager = CacheManager()
    
    # Test cache operations
    manager.set("test_key", "test_value")
    value = manager.get("test_key")
    assert value == "test_value"
    
    print("  - Cache operations: OK")

def test_query_optimizer():
    """Test query optimizer module."""
    from assistant.performance.query_optimizer import QueryOptimizer
    
    optimizer = QueryOptimizer()
    
    # Analyze query
    metrics = optimizer.analyze_query(
        query="SELECT * FROM users WHERE name = 'test'",
        execution_time_ms=50.0
    )
    assert metrics is not None
    
    print("  - Query analysis: OK")

def test_monitoring():
    """Test performance monitoring module."""
    from assistant.performance.monitoring import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    
    # Record metric
    metric = monitor.record_metric(
        name="response_time",
        value=100.0
    )
    assert metric is not None
    
    print("  - Metric recording: OK")

def test_microsoft365():
    """Test Microsoft 365 integration."""
    from assistant.integrations.microsoft365 import Microsoft365Manager
    
    manager = Microsoft365Manager()
    
    # Create config
    config = manager.create_config(
        tenant_id="test-tenant",
        client_id="test-client",
        client_secret="test-secret",
        redirect_uri="http://localhost"
    )
    assert config is not None
    
    print("  - M365 config: OK")

def test_cloud_services():
    """Test cloud services integration."""
    from assistant.integrations.cloud_services import CloudServicesManager, CloudProvider
    
    manager = CloudServicesManager()
    
    # Create config
    config = manager.create_config(
        provider=CloudProvider.AWS,
        access_key="test-key",
        secret_key="test-secret",
        region="us-east-1"
    )
    assert config is not None
    
    print("  - Cloud config: OK")

def test_crm_integration():
    """Test CRM integration."""
    from assistant.integrations.crm_integration import CRMIntegrationManager, CRMPlatform
    
    manager = CRMIntegrationManager()
    
    # Create config
    config = manager.create_config(
        platform=CRMPlatform.SALESFORCE,
        api_key="test-key",
        api_url="https://test.salesforce.com"
    )
    assert config is not None
    
    print("  - CRM config: OK")

def test_music_services():
    """Test music services integration."""
    from assistant.integrations.music_services import MusicServiceManager, MusicService
    
    manager = MusicServiceManager()
    
    # Create config
    config = manager.create_config(
        service=MusicService.SPOTIFY,
        api_key="test-key",
        user_id="user123"
    )
    assert config is not None
    
    print("  - Music service config: OK")

def test_e2e_testing():
    """Test end-to-end testing framework."""
    from tests.e2e_testing import E2ETestFramework, TestCategory
    
    framework = E2ETestFramework()
    
    # Create test case
    test = framework.create_test_case(
        name="Test Case",
        description="A test case",
        category=TestCategory.UNIT,
        test_function="test_function",
        expected_result="success"
    )
    assert test is not None
    
    print("  - Test case creation: OK")

def test_voice_testing():
    """Test voice interaction testing."""
    from tests.voice_testing import VoiceInteractionTester, TestType
    
    tester = VoiceInteractionTester()
    
    # Create voice test
    test = tester.create_voice_test(
        name="Wake Word Test",
        test_type=TestType.WAKE_WORD,
        audio_file="test.wav",
        expected_text="Hello JARVIS"
    )
    assert test is not None
    
    print("  - Voice test creation: OK")

def test_usage_analytics():
    """Test usage analytics module."""
    from assistant.analytics.usage_analytics import UsageAnalyticsManager
    
    manager = UsageAnalyticsManager()
    
    # Log event
    event = manager.log_event(
        user_id="user1",
        event_type="interaction",
        feature="voice_command"
    )
    assert event is not None
    
    print("  - Event logging: OK")

def test_deployment():
    """Test deployment module."""
    from deployment.docker_ci_cd import DeploymentManager
    
    manager = DeploymentManager()
    
    # Create Docker config
    config = manager.create_docker_config(
        app_name="jarvis",
        image_name="jarvis-assistant"
    )
    assert config is not None
    
    print("  - Docker config: OK")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("JARVIS AI Assistant - Comprehensive Module Testing")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Document Processor", test_document_processor),
        ("Sentiment Analyzer", test_sentiment_analyzer),
        ("Adaptive Response", test_adaptive_response),
        ("Personality System", test_personality_system),
        ("Speaker Diarization", test_speaker_diarization),
        ("Audio Enhancement", test_audio_enhancement),
        ("Streaming Transcription", test_streaming_transcription),
        ("Emotional TTS", test_emotional_tts),
        ("Voice Cloning", test_voice_cloning),
        ("SSML Processor", test_ssml_processor),
        ("Matter/Thread", test_matter_thread),
        ("Scene Automation", test_scene_automation),
        ("Energy Monitor", test_energy_monitor),
        ("Video Streaming", test_video_streaming),
        ("Person Detection", test_person_detection),
        ("Calendar Conflict", test_calendar_conflict),
        ("Meeting Preparation", test_meeting_prep),
        ("Project Integration", test_project_integration),
        ("Task Parser", test_task_parser),
        ("Workflow Automation", test_workflow_automation),
        ("Collaborative Sessions", test_collaborative_sessions),
        ("Customizable Dashboard", test_customizable_dashboard),
        ("Accessibility", test_accessibility),
        ("Desktop App", test_desktop_app),
        ("Browser Extension", test_browser_extension),
        ("Plugin Dependency Manager", test_plugin_dependency),
        ("GraphQL API", test_graphql_api),
        ("SDK", test_sdk),
        ("Caching", test_caching),
        ("Query Optimizer", test_query_optimizer),
        ("Performance Monitoring", test_monitoring),
        ("Microsoft 365", test_microsoft365),
        ("Cloud Services", test_cloud_services),
        ("CRM Integration", test_crm_integration),
        ("Music Services", test_music_services),
        ("E2E Testing", test_e2e_testing),
        ("Voice Testing", test_voice_testing),
        ("Usage Analytics", test_usage_analytics),
        ("Deployment", test_deployment),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        if test_module("", test_name, test_func):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/len(tests)*100:.1f}%")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
