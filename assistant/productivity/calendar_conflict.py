"""
Calendar Conflict Resolution
Detects and resolves calendar conflicts with intelligent scheduling suggestions.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time
from enum import Enum


class ConflictSeverity(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    start_time: str
    end_time: str
    location: Optional[str]
    attendees: List[str]
    is_recurring: bool
    priority: str  # 'low', 'medium', 'high'
    flexibility: int  # 0-10, how flexible the event is
    created_at: str


@dataclass
class Conflict:
    conflict_id: str
    event_ids: List[str]
    severity: ConflictSeverity
    overlap_minutes: int
    suggested_resolution: str
    alternative_times: List[Dict[str, str]]
    detected_at: str


class CalendarConflictResolver:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.productivity_dir = os.path.join(self.base_dir, "data", "productivity")
        self.events_file = os.path.join(self.productivity_dir, "calendar_events.json")
        self.conflicts_file = os.path.join(self.productivity_dir, "calendar_conflicts.json")
        
        os.makedirs(self.productivity_dir, exist_ok=True)
        
        # Load data
        self.events = self._load_events()
        self.conflicts = self._load_conflicts()

    def _load_events(self) -> Dict[str, CalendarEvent]:
        """Load calendar events from disk."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {event_id: CalendarEvent(**event) for event_id, event in data.items()}
            except Exception:
                pass
        return {}

    def _save_events(self):
        """Save events to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {event_id: asdict(event) for event_id, event in self.events.items()}
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[CalendarConflict] Failed to save events: {e}")

    def _load_conflicts(self) -> Dict[str, Conflict]:
        """Load conflicts from disk."""
        if os.path.exists(self.conflicts_file):
            try:
                with open(self.conflicts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {conflict_id: Conflict(**conflict) for conflict_id, conflict in data.items()}
            except Exception:
                pass
        return {}

    def _save_conflicts(self):
        """Save conflicts to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {conflict_id: asdict(conflict) for conflict_id, conflict in self.conflicts.items()}
            with open(self.conflicts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[CalendarConflict] Failed to save conflicts: {e}")

    def add_event(self, title: str, start_time: str, end_time: str,
                location: str = None, attendees: List[str] = None,
                is_recurring: bool = False, priority: str = "medium",
                flexibility: int = 5) -> CalendarEvent:
        """
        Add a calendar event.
        
        Args:
            title: Event title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            location: Event location
            attendees: List of attendees
            is_recurring: Whether event is recurring
            priority: Event priority
            flexibility: Flexibility score (0-10)
            
        Returns:
            CalendarEvent
        """
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        event = CalendarEvent(
            event_id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location,
            attendees=attendees or [],
            is_recurring=is_recurring,
            priority=priority,
            flexibility=flexibility,
            created_at=datetime.now().isoformat()
        )
        
        self.events[event_id] = event
        self._save_events()
        
        # Check for conflicts
        self._detect_conflicts()
        
        return event

    def _detect_conflicts(self):
        """Detect conflicts between events."""
        self.conflicts = {}
        
        event_list = list(self.events.values())
        
        for i, event1 in enumerate(event_list):
            for event2 in event_list[i+1:]:
                conflict = self._check_overlap(event1, event2)
                if conflict:
                    self.conflicts[conflict.conflict_id] = conflict
        
        self._save_conflicts()

    def _check_overlap(self, event1: CalendarEvent, event2: CalendarEvent) -> Optional[Conflict]:
        """Check if two events overlap."""
        start1 = datetime.fromisoformat(event1.start_time)
        end1 = datetime.fromisoformat(event1.end_time)
        start2 = datetime.fromisoformat(event2.start_time)
        end2 = datetime.fromisoformat(event2.end_time)
        
        # Check for overlap
        if start1 >= end2 or end1 <= start2:
            return None
        
        # Calculate overlap duration
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
        
        # Determine severity
        if overlap_minutes < 15:
            severity = ConflictSeverity.LOW
        elif overlap_minutes < 30:
            severity = ConflictSeverity.MEDIUM
        else:
            severity = ConflictSeverity.HIGH
        
        # Generate resolution suggestions
        resolution = self._generate_resolution(event1, event2, overlap_minutes)
        
        # Generate alternative times
        alternatives = self._generate_alternatives(event1, event2)
        
        conflict_id = f"conflict_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        return Conflict(
            conflict_id=conflict_id,
            event_ids=[event1.event_id, event2.event_id],
            severity=severity,
            overlap_minutes=int(overlap_minutes),
            suggested_resolution=resolution,
            alternative_times=alternatives,
            detected_at=datetime.now().isoformat()
        )

    def _generate_resolution(self, event1: CalendarEvent, event2: CalendarEvent,
                           overlap_minutes: float) -> str:
        """Generate resolution suggestion."""
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        
        if priority_order[event1.priority] > priority_order[event2.priority]:
            return f"Reschedule '{event2.title}' to accommodate '{event1.title}'"
        elif priority_order[event2.priority] > priority_order[event1.priority]:
            return f"Reschedule '{event1.title}' to accommodate '{event2.title}'"
        else:
            # Same priority, check flexibility
            if event1.flexibility > event2.flexibility:
                return f"Move '{event1.title}' to a different time"
            elif event2.flexibility > event1.flexibility:
                return f"Move '{event2.title}' to a different time"
            else:
                return f"Consider shortening one or both events"

    def _generate_alternatives(self, event1: CalendarEvent, event2: CalendarEvent) -> List[Dict[str, str]]:
        """Generate alternative time suggestions."""
        alternatives = []
        
        start1 = datetime.fromisoformat(event1.start_time)
        start2 = datetime.fromisoformat(event2.start_time)
        
        # Suggest moving event1 before event2
        duration1 = (datetime.fromisoformat(event1.end_time) - start1).total_seconds() / 60
        new_start1 = start2 - timedelta(minutes=duration1 + 30)
        alternatives.append({
            'event': event1.title,
            'suggested_time': new_start1.isoformat(),
            'reason': 'Schedule before conflicting event'
        })
        
        # Suggest moving event1 after event2
        end2 = datetime.fromisoformat(event2.end_time)
        new_start1_after = end2 + timedelta(minutes=30)
        alternatives.append({
            'event': event1.title,
            'suggested_time': new_start1_after.isoformat(),
            'reason': 'Schedule after conflicting event'
        })
        
        # Suggest moving event2 before event1
        duration2 = (datetime.fromisoformat(event2.end_time) - start2).total_seconds() / 60
        new_start2 = start1 - timedelta(minutes=duration2 + 30)
        alternatives.append({
            'event': event2.title,
            'suggested_time': new_start2.isoformat(),
            'reason': 'Schedule before conflicting event'
        })
        
        return alternatives

    def get_conflicts(self, severity: ConflictSeverity = None) -> List[Conflict]:
        """Get conflicts, optionally filtered by severity."""
        conflicts = list(self.conflicts.values())
        
        if severity:
            conflicts = [c for c in conflicts if c.severity == severity]
        
        return conflicts

    def resolve_conflict(self, conflict_id: str, resolution: str) -> Tuple[bool, str]:
        """
        Resolve a conflict by applying a resolution.
        
        Args:
            conflict_id: Conflict ID
            resolution: Resolution to apply
            
        Returns:
            (success, message)
        """
        if conflict_id not in self.conflicts:
            return False, "Conflict not found"
        
        conflict = self.conflicts[conflict_id]
        
        # Remove conflict
        del self.conflicts[conflict_id]
        self._save_conflicts()
        
        return True, f"Conflict resolved: {resolution}"

    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get an event by ID."""
        return self.events.get(event_id)

    def get_events_in_range(self, start_date: str, end_date: str) -> List[CalendarEvent]:
        """Get events within a date range."""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        events_in_range = []
        for event in self.events.values():
            event_start = datetime.fromisoformat(event.start_time)
            if start <= event_start <= end:
                events_in_range.append(event)
        
        return events_in_range

    def suggest_meeting_time(self, duration_minutes: int, preferred_start: str = None,
                           preferred_end: str = None, attendees: List[str] = None) -> List[str]:
        """
        Suggest available meeting times.
        
        Args:
            duration_minutes: Meeting duration
            preferred_start: Preferred start time (ISO format)
            preferred_end: Preferred end time (ISO format)
            attendees: List of attendees
            
        Returns:
            List of suggested time slots
        """
        if not preferred_start:
            preferred_start = datetime.now().replace(hour=9, minute=0).isoformat()
        if not preferred_end:
            preferred_end = (datetime.now() + timedelta(days=1)).replace(hour=17, minute=0).isoformat()
        
        start = datetime.fromisoformat(preferred_start)
        end = datetime.fromisoformat(preferred_end)
        
        # Get events in range
        events = self.get_events_in_range(preferred_start, preferred_end)
        
        # Find available slots
        available_slots = []
        current_time = start
        
        while current_time + timedelta(minutes=duration_minutes) <= end:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with any event
            has_conflict = False
            for event in events:
                event_start = datetime.fromisoformat(event.start_time)
                event_end = datetime.fromisoformat(event.end_time)
                
                if not (slot_end <= event_start or current_time >= event_end):
                    has_conflict = True
                    break
            
            if not has_conflict:
                available_slots.append({
                    'start': current_time.isoformat(),
                    'end': slot_end.isoformat()
                })
            
            # Move to next 30-minute slot
            current_time += timedelta(minutes=30)
        
        return available_slots

    def get_statistics(self) -> Dict[str, Any]:
        """Get calendar statistics."""
        total_events = len(self.events)
        total_conflicts = len(self.conflicts)
        
        # Count by priority
        by_priority = {}
        for event in self.events.values():
            priority = event.priority
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Count by severity
        by_severity = {}
        for conflict in self.conflicts.values():
            severity = conflict.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total_events': total_events,
            'total_conflicts': total_conflicts,
            'by_priority': by_priority,
            'by_severity': by_severity
        }

    def delete_event(self, event_id: str) -> bool:
        """Delete an event."""
        if event_id not in self.events:
            return False
        
        del self.events[event_id]
        self._save_events()
        
        # Re-detect conflicts
        self._detect_conflicts()
        
        return True

    def clear_old_events(self, days: int = 90) -> int:
        """Clear events older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            event_id for event_id, event in self.events.items()
            if datetime.fromisoformat(event.start_time) < cutoff_date
        ]
        
        for event_id in to_remove:
            del self.events[event_id]
        
        if to_remove:
            self._save_events()
            self._detect_conflicts()
        
        return len(to_remove)
