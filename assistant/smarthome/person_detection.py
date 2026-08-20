"""
Person Detection and Recognition
Provides person detection and recognition capabilities for smart home security.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np


class DetectionConfidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PersonProfile:
    profile_id: str
    name: str
    face_features: List[float]
    is_authorized: bool
    access_level: str  # 'full', 'limited', 'guest'
    created_at: str
    last_seen: str


@dataclass
class DetectionEvent:
    event_id: str
    camera_id: str
    person_id: Optional[str]
    confidence: float
    bounding_box: List[int]  # [x, y, width, height]
    timestamp: str
    is_recognized: bool
    snapshot_path: Optional[str]


class PersonDetectionManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.smarthome_dir = os.path.join(self.base_dir, "data", "smarthome")
        self.profiles_file = os.path.join(self.smarthome_dir, "person_profiles.json")
        self.events_file = os.path.join(self.smarthome_dir, "detection_events.json")
        self.snapshots_dir = os.path.join(self.smarthome_dir, "snapshots")
        
        os.makedirs(self.smarthome_dir, exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)
        
        # Load data
        self.profiles = self._load_profiles()
        self.events = self._load_events()
        
        # Detection threshold
        self.recognition_threshold = 0.7

    def _load_profiles(self) -> Dict[str, PersonProfile]:
        """Load person profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {profile_id: PersonProfile(**profile) for profile_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save person profiles to disk."""
        try:
            data = {profile_id: asdict(profile) for profile_id, profile in self.profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PersonDetection] Failed to save profiles: {e}")

    def _load_events(self) -> Dict[str, DetectionEvent]:
        """Load detection events from disk."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {event_id: DetectionEvent(**event) for event_id, event in data.items()}
            except Exception:
                pass
        return {}

    def _save_events(self):
        """Save detection events to disk."""
        try:
            data = {event_id: asdict(event) for event_id, event in self.events.items()}
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PersonDetection] Failed to save events: {e}")

    def register_person(self, name: str, face_features: List[float],
                       is_authorized: bool = True, access_level: str = "full") -> PersonProfile:
        """
        Register a new person profile.
        
        Args:
            name: Person's name
            face_features: Face feature vector
            is_authorized: Whether person is authorized
            access_level: Access level
            
        Returns:
            PersonProfile
        """
        profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        profile = PersonProfile(
            profile_id=profile_id,
            name=name,
            face_features=face_features,
            is_authorized=is_authorized,
            access_level=access_level,
            created_at=datetime.now().isoformat(),
            last_seen=datetime.now().isoformat()
        )
        
        self.profiles[profile_id] = profile
        self._save_profiles()
        
        return profile

    def detect_person(self, camera_id: str, face_features: List[float],
                    bounding_box: List[int] = None) -> DetectionEvent:
        """
        Detect and recognize a person.
        
        Args:
            camera_id: Camera ID
            face_features: Face feature vector
            bounding_box: Bounding box coordinates
            
        Returns:
            DetectionEvent
        """
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Try to recognize person
        person_id = None
        confidence = 0.0
        is_recognized = False
        
        for profile_id, profile in self.profiles.items():
            similarity = self._compare_features(face_features, profile.face_features)
            if similarity > confidence:
                confidence = similarity
                person_id = profile_id
        
        if confidence >= self.recognition_threshold:
            is_recognized = True
            
            # Update last seen
            if person_id and person_id in self.profiles:
                self.profiles[person_id].last_seen = datetime.now().isoformat()
                self._save_profiles()
        
        event = DetectionEvent(
            event_id=event_id,
            camera_id=camera_id,
            person_id=person_id,
            confidence=confidence,
            bounding_box=bounding_box or [0, 0, 0, 0],
            timestamp=datetime.now().isoformat(),
            is_recognized=is_recognized,
            snapshot_path=None
        )
        
        self.events[event_id] = event
        self._save_events()
        
        return event

    def _compare_features(self, features1: List[float], features2: List[float]) -> float:
        """Compare two face feature vectors."""
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
            print(f"[PersonDetection] Feature comparison failed: {e}")
            return 0.0

    def get_person_profile(self, profile_id: str) -> Optional[PersonProfile]:
        """Get a person profile by ID."""
        return self.profiles.get(profile_id)

    def get_person_by_name(self, name: str) -> Optional[PersonProfile]:
        """Get a person profile by name."""
        for profile in self.profiles.values():
            if profile.name.lower() == name.lower():
                return profile
        return None

    def update_person_features(self, profile_id: str, face_features: List[float]) -> bool:
        """Update face features for a person."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].face_features = face_features
        self.profiles[profile_id].last_seen = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def set_authorization(self, profile_id: str, is_authorized: bool) -> bool:
        """Set authorization status for a person."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].is_authorized = is_authorized
        self._save_profiles()
        
        return True

    def set_access_level(self, profile_id: str, access_level: str) -> bool:
        """Set access level for a person."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].access_level = access_level
        self._save_profiles()
        
        return True

    def get_detection_events(self, camera_id: str = None, person_id: str = None,
                           limit: int = 100) -> List[DetectionEvent]:
        """
        Get detection events with filters.
        
        Args:
            camera_id: Filter by camera ID
            person_id: Filter by person ID
            limit: Maximum results
            
        Returns:
            List of DetectionEvents
        """
        events = list(self.events.values())
        
        if camera_id:
            events = [e for e in events if e.camera_id == camera_id]
        
        if person_id:
            events = [e for e in events if e.person_id == person_id]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return events[:limit]

    def get_person_activity(self, profile_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get activity summary for a person.
        
        Args:
            profile_id: Person profile ID
            days: Number of days to analyze
            
        Returns:
            Activity summary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        person_events = [
            event for event in self.events.values()
            if event.person_id == profile_id and datetime.fromisoformat(event.timestamp) >= cutoff_date
        ]
        
        # Count by camera
        camera_counts = {}
        for event in person_events:
            camera_counts[event.camera_id] = camera_counts.get(event.camera_id, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(e.confidence for e in person_events) / len(person_events) if person_events else 0
        
        return {
            'profile_id': profile_id,
            'period_days': days,
            'total_detections': len(person_events),
            'by_camera': camera_counts,
            'average_confidence': round(avg_confidence, 2)
        }

    def get_authorized_persons(self) -> List[PersonProfile]:
        """Get all authorized persons."""
        return [p for p in self.profiles.values() if p.is_authorized]

    def get_unauthorized_detections(self, hours: int = 24) -> List[DetectionEvent]:
        """Get detections of unauthorized persons."""
        cutoff_date = datetime.now() - timedelta(hours=hours)
        
        unauthorized_events = [
            event for event in self.events.values()
            if not event.is_recognized and datetime.fromisoformat(event.timestamp) >= cutoff_date
        ]
        
        unauthorized_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return unauthorized_events

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a person profile."""
        if profile_id not in self.profiles:
            return False
        
        del self.profiles[profile_id]
        self._save_profiles()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get person detection statistics."""
        total_profiles = len(self.profiles)
        total_events = len(self.events)
        
        authorized_count = sum(1 for p in self.profiles.values() if p.is_authorized)
        
        # Count by access level
        by_access_level = {}
        for profile in self.profiles.values():
            level = profile.access_level
            by_access_level[level] = by_access_level.get(level, 0) + 1
        
        # Recent events
        recent_events = len([e for e in self.events.values() 
                           if datetime.fromisoformat(e.timestamp) >= datetime.now() - timedelta(hours=24)])
        
        return {
            'total_profiles': total_profiles,
            'authorized_count': authorized_count,
            'by_access_level': by_access_level,
            'total_events': total_events,
            'recent_events_24h': recent_events
        }

    def clear_old_events(self, days: int = 30) -> int:
        """Clear detection events older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            event_id for event_id, event in self.events.items()
            if datetime.fromisoformat(event.timestamp) < cutoff_date
        ]
        
        for event_id in to_remove:
            del self.events[event_id]
        
        if to_remove:
            self._save_events()
        
        return len(to_remove)

    def export_profiles(self, export_path: str) -> Tuple[bool, str]:
        """Export person profiles."""
        try:
            export_data = {
                'profiles': {profile_id: asdict(profile) for profile_id, profile in self.profiles.items()},
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Profiles exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
