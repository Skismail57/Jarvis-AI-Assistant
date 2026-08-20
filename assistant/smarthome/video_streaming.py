"""
Real-time Video Streaming and Analysis
Provides video streaming and analysis capabilities for smart home cameras.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class StreamState(Enum):
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    ERROR = "error"


class StreamQuality(Enum):
    LOW = "low"  # 480p
    MEDIUM = "medium"  # 720p
    HIGH = "high"  # 1080p
    ULTRA = "ultra"  # 4K


@dataclass
class CameraStream:
    stream_id: str
    camera_id: str
    name: str
    stream_url: str
    state: StreamState
    quality: StreamQuality
    fps: int
    bitrate: int
    width: int
    height: int
    is_recording: bool
    last_frame_time: str
    created_at: str


@dataclass
class VideoAnalysis:
    analysis_id: str
    stream_id: str
    analysis_type: str
    results: Dict[str, Any]
    confidence: float
    timestamp: str


class VideoStreamingManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.smarthome_dir = os.path.join(self.base_dir, "data", "smarthome")
        self.streams_file = os.path.join(self.smarthome_dir, "video_streams.json")
        self.analysis_file = os.path.join(self.smarthome_dir, "video_analysis.json")
        self.recordings_dir = os.path.join(self.smarthome_dir, "recordings")
        
        os.makedirs(self.smarthome_dir, exist_ok=True)
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # Load data
        self.streams = self._load_streams()
        self.analysis = self._load_analysis()

    def _load_streams(self) -> Dict[str, CameraStream]:
        """Load camera streams from disk."""
        if os.path.exists(self.streams_file):
            try:
                with open(self.streams_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {stream_id: CameraStream(**stream) for stream_id, stream in data.items()}
            except Exception:
                pass
        return {}

    def _save_streams(self):
        """Save camera streams to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {stream_id: asdict(stream) for stream_id, stream in self.streams.items()}
            with open(self.streams_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[VideoStreaming] Failed to save streams: {e}")

    def _load_analysis(self) -> Dict[str, VideoAnalysis]:
        """Load video analysis from disk."""
        if os.path.exists(self.analysis_file):
            try:
                with open(self.analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {analysis_id: VideoAnalysis(**analysis) for analysis_id, analysis in data.items()}
            except Exception:
                pass
        return {}

    def _save_analysis(self):
        """Save video analysis to disk."""
        try:
            data = {analysis_id: asdict(analysis) for analysis_id, analysis in self.analysis.items()}
            with open(self.analysis_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[VideoStreaming] Failed to save analysis: {e}")

    def add_camera_stream(self, camera_id: str, name: str, stream_url: str,
                          quality: StreamQuality = StreamQuality.HIGH) -> CameraStream:
        """
        Add a camera stream.
        
        Args:
            camera_id: Camera ID
            name: Camera name
            stream_url: RTSP/HTTP stream URL
            quality: Stream quality
            
        Returns:
            CameraStream
        """
        stream_id = f"stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Set resolution based on quality
        quality_settings = {
            StreamQuality.LOW: {'width': 640, 'height': 480, 'bitrate': 1000},
            StreamQuality.MEDIUM: {'width': 1280, 'height': 720, 'bitrate': 2500},
            StreamQuality.HIGH: {'width': 1920, 'height': 1080, 'bitrate': 5000},
            StreamQuality.ULTRA: {'width': 3840, 'height': 2160, 'bitrate': 15000}
        }
        
        settings = quality_settings.get(quality, quality_settings[StreamQuality.HIGH])
        
        stream = CameraStream(
            stream_id=stream_id,
            camera_id=camera_id,
            name=name,
            stream_url=stream_url,
            state=StreamState.IDLE,
            quality=quality,
            fps=30,
            bitrate=settings['bitrate'],
            width=settings['width'],
            height=settings['height'],
            is_recording=False,
            last_frame_time=datetime.now().isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        self.streams[stream_id] = stream
        self._save_streams()
        
        return stream

    def start_stream(self, stream_id: str) -> Tuple[bool, str]:
        """
        Start a video stream.
        
        Args:
            stream_id: Stream ID
            
        Returns:
            (success, message)
        """
        if stream_id not in self.streams:
            return False, "Stream not found"
        
        stream = self.streams[stream_id]
        
        # In production, this would start actual streaming
        stream.state = StreamState.STREAMING
        stream.last_frame_time = datetime.now().isoformat()
        self._save_streams()
        
        return True, f"Stream '{stream.name}' started"

    def stop_stream(self, stream_id: str) -> Tuple[bool, str]:
        """
        Stop a video stream.
        
        Args:
            stream_id: Stream ID
            
        Returns:
            (success, message)
        """
        if stream_id not in self.streams:
            return False, "Stream not found"
        
        stream = self.streams[stream_id]
        stream.state = StreamState.IDLE
        self._save_streams()
        
        return True, f"Stream '{stream.name}' stopped"

    def pause_stream(self, stream_id: str) -> Tuple[bool, str]:
        """Pause a video stream."""
        if stream_id not in self.streams:
            return False, "Stream not found"
        
        self.streams[stream_id].state = StreamState.PAUSED
        self._save_streams()
        
        return True, "Stream paused"

    def resume_stream(self, stream_id: str) -> Tuple[bool, str]:
        """Resume a paused video stream."""
        if stream_id not in self.streams:
            return False, "Stream not found"
        
        self.streams[stream_id].state = StreamState.STREAMING
        self._save_streams()
        
        return True, "Stream resumed"

    def set_stream_quality(self, stream_id: str, quality: StreamQuality) -> bool:
        """Change stream quality."""
        if stream_id not in self.streams:
            return False
        
        stream = self.streams[stream_id]
        stream.quality = quality
        
        # Update resolution
        quality_settings = {
            StreamQuality.LOW: {'width': 640, 'height': 480, 'bitrate': 1000},
            StreamQuality.MEDIUM: {'width': 1280, 'height': 720, 'bitrate': 2500},
            StreamQuality.HIGH: {'width': 1920, 'height': 1080, 'bitrate': 5000},
            StreamQuality.ULTRA: {'width': 3840, 'height': 2160, 'bitrate': 15000}
        }
        
        settings = quality_settings.get(quality, quality_settings[StreamQuality.HIGH])
        stream.width = settings['width']
        stream.height = settings['height']
        stream.bitrate = settings['bitrate']
        
        self._save_streams()
        return True

    def start_recording(self, stream_id: str) -> Tuple[bool, str]:
        """Start recording a stream."""
        if stream_id not in self.streams:
            return False, "Stream not found"
        
        self.streams[stream_id].is_recording = True
        self._save_streams()
        
        return True, "Recording started"

    def stop_recording(self, stream_id: str) -> Tuple[bool, str]:
        """Stop recording a stream."""
        if stream_id not in self.streams:
            return False, "Stream not found"
        
        self.streams[stream_id].is_recording = False
        self._save_streams()
        
        return True, "Recording stopped"

    def analyze_frame(self, stream_id: str, analysis_type: str) -> Optional[VideoAnalysis]:
        """
        Analyze a video frame.
        
        Args:
            stream_id: Stream ID
            analysis_type: Type of analysis (motion, object, etc.)
            
        Returns:
            VideoAnalysis
        """
        if stream_id not in self.streams:
            return None
        
        stream = self.streams[stream_id]
        
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # In production, this would perform actual analysis
        # For now, return placeholder
        analysis = VideoAnalysis(
            analysis_id=analysis_id,
            stream_id=stream_id,
            analysis_type=analysis_type,
            results={'detected': False},
            confidence=0.0,
            timestamp=datetime.now().isoformat()
        )
        
        self.analysis[analysis_id] = analysis
        self._save_analysis()
        
        return analysis

    def get_stream(self, stream_id: str) -> Optional[CameraStream]:
        """Get a stream by ID."""
        return self.streams.get(stream_id)

    def get_all_streams(self) -> List[CameraStream]:
        """Get all camera streams."""
        return list(self.streams.values())

    def get_active_streams(self) -> List[CameraStream]:
        """Get all currently streaming cameras."""
        return [s for s in self.streams.values() if s.state == StreamState.STREAMING]

    def remove_stream(self, stream_id: str) -> bool:
        """Remove a camera stream."""
        if stream_id not in self.streams:
            return False
        
        del self.streams[stream_id]
        self._save_streams()
        
        return True

    def get_stream_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        total_streams = len(self.streams)
        active_streams = len(self.get_active_streams())
        recording_streams = sum(1 for s in self.streams.values() if s.is_recording)
        
        # Count by quality
        by_quality = {}
        for stream in self.streams.values():
            quality = stream.quality.value
            by_quality[quality] = by_quality.get(quality, 0) + 1
        
        return {
            'total_streams': total_streams,
            'active_streams': active_streams,
            'recording_streams': recording_streams,
            'by_quality': by_quality
        }

    def export_stream_config(self, stream_id: str, export_path: str) -> Tuple[bool, str]:
        """Export stream configuration."""
        if stream_id not in self.streams:
            return False, "Stream not found"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.streams[stream_id]), f, indent=2)
            return True, f"Stream config exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
