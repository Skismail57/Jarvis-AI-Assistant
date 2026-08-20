"""
Meeting Preparation and Summaries
Provides meeting preparation assistance and automatic meeting summaries.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


class MeetingStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Meeting:
    meeting_id: str
    title: str
    start_time: str
    end_time: str
    attendees: List[str]
    agenda: List[str]
    location: str
    notes: str
    status: MeetingStatus
    created_at: str


@dataclass
class MeetingSummary:
    summary_id: str
    meeting_id: str
    key_points: List[str]
    action_items: List[Dict[str, str]]
    decisions: List[str]
    participants: List[str]
    duration_minutes: int
    generated_at: str


class MeetingManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.productivity_dir = os.path.join(self.base_dir, "data", "productivity")
        self.meetings_file = os.path.join(self.productivity_dir, "meetings.json")
        self.summaries_file = os.path.join(self.productivity_dir, "meeting_summaries.json")
        
        os.makedirs(self.productivity_dir, exist_ok=True)
        
        # Load data
        self.meetings = self._load_meetings()
        self.summaries = self._load_summaries()

    def _load_meetings(self) -> Dict[str, Meeting]:
        """Load meetings from disk."""
        if os.path.exists(self.meetings_file):
            try:
                with open(self.meetings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {meeting_id: Meeting(**meeting) for meeting_id, meeting in data.items()}
            except Exception:
                pass
        return {}

    def _save_meetings(self):
        """Save meetings to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {meeting_id: asdict(meeting) for meeting_id, meeting in self.meetings.items()}
            with open(self.meetings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[MeetingManager] Failed to save meetings: {e}")

    def _load_summaries(self) -> Dict[str, MeetingSummary]:
        """Load meeting summaries from disk."""
        if os.path.exists(self.summaries_file):
            try:
                with open(self.summaries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {summary_id: MeetingSummary(**summary) for summary_id, summary in data.items()}
            except Exception:
                pass
        return {}

    def _save_summaries(self):
        """Save meeting summaries to disk."""
        try:
            data = {summary_id: asdict(summary) for summary_id, summary in self.summaries.items()}
            with open(self.summaries_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[MeetingManager] Failed to save summaries: {e}")

    def create_meeting(self, title: str, start_time: str, end_time: str,
                      attendees: List[str], agenda: List[str] = None,
                      location: str = "") -> Meeting:
        """
        Create a new meeting.
        
        Args:
            title: Meeting title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            attendees: List of attendees
            agenda: Meeting agenda items
            location: Meeting location
            
        Returns:
            Meeting
        """
        meeting_id = f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        meeting = Meeting(
            meeting_id=meeting_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            agenda=agenda or [],
            location=location,
            notes="",
            status=MeetingStatus.SCHEDULED,
            created_at=datetime.now().isoformat()
        )
        
        self.meetings[meeting_id] = meeting
        self._save_meetings()
        
        return meeting

    def generate_preparation_notes(self, meeting_id: str) -> Dict[str, Any]:
        """
        Generate preparation notes for a meeting.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Preparation notes
        """
        if meeting_id not in self.meetings:
            return {'error': 'Meeting not found'}
        
        meeting = self.meetings[meeting_id]
        
        preparation = {
            'meeting_id': meeting_id,
            'title': meeting.title,
            'attendees': meeting.attendees,
            'agenda': meeting.agenda,
            'location': meeting.location,
            'preparation_items': [
                f"Review agenda items: {', '.join(meeting.agenda)}",
                f"Prepare materials for {len(meeting.attendees)} attendees",
                f"Check availability for {meeting.location}",
                "Prepare opening remarks",
                "Review previous meeting notes if applicable"
            ],
            'time_until_meeting': self._time_until(meeting.start_time)
        }
        
        return preparation

    def _time_until(self, meeting_time: str) -> str:
        """Calculate time until meeting."""
        meeting_dt = datetime.fromisoformat(meeting_time)
        now = datetime.now()
        
        if meeting_dt < now:
            return "Meeting has passed"
        
        delta = meeting_dt - now
        
        if delta.days > 0:
            return f"{delta.days} days"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hours"
        else:
            minutes = delta.seconds // 60
            return f"{minutes} minutes"

    def start_meeting(self, meeting_id: str) -> bool:
        """Mark a meeting as in progress."""
        if meeting_id not in self.meetings:
            return False
        
        self.meetings[meeting_id].status = MeetingStatus.IN_PROGRESS
        self._save_meetings()
        
        return True

    def end_meeting(self, meeting_id: str, notes: str = "") -> bool:
        """End a meeting and add notes."""
        if meeting_id not in self.meetings:
            return False
        
        self.meetings[meeting_id].status = MeetingStatus.COMPLETED
        self.meetings[meeting_id].notes = notes
        self._save_meetings()
        
        return True

    def generate_summary(self, meeting_id: str, transcript: str = "") -> MeetingSummary:
        """
        Generate a meeting summary.
        
        Args:
            meeting_id: Meeting ID
            transcript: Meeting transcript (optional)
            
        Returns:
            MeetingSummary
        """
        if meeting_id not in self.meetings:
            raise ValueError("Meeting not found")
        
        meeting = self.meetings[meeting_id]
        
        # Calculate duration
        start = datetime.fromisoformat(meeting.start_time)
        end = datetime.fromisoformat(meeting.end_time)
        duration_minutes = int((end - start).total_seconds() / 60)
        
        # In production, this would use NLP to extract key points from transcript
        # For now, generate based on agenda
        key_points = [f"Discussed: {item}" for item in meeting.agenda]
        
        # Generate action items based on agenda
        action_items = [
            {
                'item': f"Follow up on {item}",
                'assigned_to': meeting.attendees[0] if meeting.attendees else "TBD",
                'due_date': (datetime.now() + timedelta(days=7)).isoformat()
            }
            for item in meeting.agenda
        ]
        
        # Decisions (placeholder)
        decisions = ["Agreed on action items", "Next meeting scheduled"]
        
        summary_id = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        summary = MeetingSummary(
            summary_id=summary_id,
            meeting_id=meeting_id,
            key_points=key_points,
            action_items=action_items,
            decisions=decisions,
            participants=meeting.attendees,
            duration_minutes=duration_minutes,
            generated_at=datetime.now().isoformat()
        )
        
        self.summaries[summary_id] = summary
        self._save_summaries()
        
        return summary

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a meeting by ID."""
        return self.meetings.get(meeting_id)

    def get_summary(self, summary_id: str) -> Optional[MeetingSummary]:
        """Get a summary by ID."""
        return self.summaries.get(summary_id)

    def get_meeting_summary(self, meeting_id: str) -> Optional[MeetingSummary]:
        """Get summary for a specific meeting."""
        for summary in self.summaries.values():
            if summary.meeting_id == meeting_id:
                return summary
        return None

    def get_upcoming_meetings(self, days: int = 7) -> List[Meeting]:
        """Get upcoming meetings within specified days."""
        cutoff_date = datetime.now() + timedelta(days=days)
        
        upcoming = [
            meeting for meeting in self.meetings.values()
            if meeting.status == MeetingStatus.SCHEDULED
            and datetime.fromisoformat(meeting.start_time) <= cutoff_date
        ]
        
        upcoming.sort(key=lambda m: m.start_time)
        
        return upcoming

    def get_meetings_for_attendee(self, attendee: str) -> List[Meeting]:
        """Get all meetings for a specific attendee."""
        return [
            meeting for meeting in self.meetings.values()
            if attendee in meeting.attendees
        ]

    def add_agenda_item(self, meeting_id: str, item: str) -> bool:
        """Add an agenda item to a meeting."""
        if meeting_id not in self.meetings:
            return False
        
        self.meetings[meeting_id].agenda.append(item)
        self._save_meetings()
        
        return True

    def update_notes(self, meeting_id: str, notes: str) -> bool:
        """Update meeting notes."""
        if meeting_id not in self.meetings:
            return False
        
        self.meetings[meeting_id].notes = notes
        self._save_meetings()
        
        return True

    def cancel_meeting(self, meeting_id: str) -> bool:
        """Cancel a meeting."""
        if meeting_id not in self.meetings:
            return False
        
        self.meetings[meeting_id].status = MeetingStatus.CANCELLED
        self._save_meetings()
        
        return True

    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting."""
        if meeting_id not in self.meetings:
            return False
        
        del self.meetings[meeting_id]
        self._save_meetings()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get meeting statistics."""
        total_meetings = len(self.meetings)
        total_summaries = len(self.summaries)
        
        # Count by status
        by_status = {}
        for meeting in self.meetings.values():
            status = meeting.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_meetings': total_meetings,
            'total_summaries': total_summaries,
            'by_status': by_status
        }

    def export_meeting_report(self, meeting_id: str, export_path: str) -> Tuple[bool, str]:
        """Export meeting report with summary."""
        if meeting_id not in self.meetings:
            return False, "Meeting not found"
        
        meeting = self.meetings[meeting_id]
        summary = self.get_meeting_summary(meeting_id)
        
        report = {
            'meeting': asdict(meeting),
            'summary': asdict(summary) if summary else None,
            'exported_at': datetime.now().isoformat()
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            return True, f"Report exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
