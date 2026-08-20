"""
Collaborative Features
Provides multi-user session support for collaborative interactions.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


class SessionRole(Enum):
    HOST = "host"
    MODERATOR = "moderator"
    PARTICIPANT = "participant"
    OBSERVER = "observer"


class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


@dataclass
class SessionParticipant:
    participant_id: str
    user_id: str
    name: str
    role: SessionRole
    joined_at: str
    last_active: str
    is_online: bool = True


@dataclass
class SessionMessage:
    message_id: str
    session_id: str
    user_id: str
    user_name: str
    content: str
    message_type: str  # 'text', 'system', 'action'
    timestamp: str


@dataclass
class CollaborativeSession:
    session_id: str
    name: str
    description: str
    host_id: str
    participants: List[SessionParticipant]
    status: SessionStatus
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    max_participants: int = 10


class CollaborativeSessionManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.ui_dir = os.path.join(self.base_dir, "data", "ui")
        self.sessions_file = os.path.join(self.ui_dir, "collaborative_sessions.json")
        self.messages_file = os.path.join(self.ui_dir, "session_messages.json")
        
        os.makedirs(self.ui_dir, exist_ok=True)
        
        # Load data
        self.sessions = self._load_sessions()
        self.messages = self._load_messages()

    def _load_sessions(self) -> Dict[str, CollaborativeSession]:
        """Load sessions from disk."""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {session_id: CollaborativeSession(**session) for session_id, session in data.items()}
            except Exception:
                pass
        return {}

    def _save_sessions(self):
        """Save sessions to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {session_id: asdict(session) for session_id, session in self.sessions.items()}
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[CollaborativeSessions] Failed to save sessions: {e}")

    def _load_messages(self) -> Dict[str, SessionMessage]:
        """Load messages from disk."""
        if os.path.exists(self.messages_file):
            try:
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {message_id: SessionMessage(**message) for message_id, message in data.items()}
            except Exception:
                pass
        return {}

    def _save_messages(self):
        """Save messages to disk."""
        try:
            data = {message_id: asdict(message) for message_id, message in self.messages.items()}
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[CollaborativeSessions] Failed to save messages: {e}")

    def create_session(self, name: str, host_id: str, host_name: str,
                      description: str = "", max_participants: int = 10) -> CollaborativeSession:
        """
        Create a new collaborative session.
        
        Args:
            name: Session name
            host_id: Host user ID
            host_name: Host user name
            description: Session description
            max_participants: Maximum participants
            
        Returns:
            CollaborativeSession
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create host participant
        host_participant = SessionParticipant(
            participant_id=f"participant_{host_id}",
            user_id=host_id,
            name=host_name,
            role=SessionRole.HOST,
            joined_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat(),
            is_online=True
        )
        
        session = CollaborativeSession(
            session_id=session_id,
            name=name,
            description=description,
            host_id=host_id,
            participants=[host_participant],
            status=SessionStatus.ACTIVE,
            created_at=datetime.now().isoformat(),
            started_at=datetime.now().isoformat(),
            max_participants=max_participants
        )
        
        self.sessions[session_id] = session
        self._save_sessions()
        
        return session

    def join_session(self, session_id: str, user_id: str, user_name: str,
                   role: SessionRole = SessionRole.PARTICIPANT) -> Tuple[bool, str]:
        """
        Join a collaborative session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            user_name: User name
            role: User role
            
        Returns:
            (success, message)
        """
        if session_id not in self.sessions:
            return False, "Session not found"
        
        session = self.sessions[session_id]
        
        if session.status != SessionStatus.ACTIVE:
            return False, f"Session is {session.status.value}"
        
        if len(session.participants) >= session.max_participants:
            return False, "Session is full"
        
        # Check if user already in session
        for participant in session.participants:
            if participant.user_id == user_id:
                participant.is_online = True
                participant.last_active = datetime.now().isoformat()
                self._save_sessions()
                return True, "Rejoined session"
        
        # Add new participant
        participant = SessionParticipant(
            participant_id=f"participant_{user_id}",
            user_id=user_id,
            name=user_name,
            role=role,
            joined_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat(),
            is_online=True
        )
        
        session.participants.append(participant)
        self._save_sessions()
        
        # Send system message
        self._send_system_message(session_id, f"{user_name} joined the session")
        
        return True, "Joined session successfully"

    def leave_session(self, session_id: str, user_id: str) -> Tuple[bool, str]:
        """Leave a collaborative session."""
        if session_id not in self.sessions:
            return False, "Session not found"
        
        session = self.sessions[session_id]
        
        for i, participant in enumerate(session.participants):
            if participant.user_id == user_id:
                if participant.role == SessionRole.HOST:
                    # Host leaving - end session or transfer host
                    if len(session.participants) > 1:
                        # Transfer host to next participant
                        session.participants[i].role = SessionRole.PARTICIPANT
                        session.participants[0].role = SessionRole.HOST
                        session.host_id = session.participants[0].user_id
                    else:
                        # Last participant - end session
                        session.status = SessionStatus.ENDED
                        session.ended_at = datetime.now().isoformat()
                
                session.participants.pop(i)
                self._save_sessions()
                
                # Send system message
                self._send_system_message(session_id, f"{participant.name} left the session")
                
                return True, "Left session successfully"
        
        return False, "User not in session"

    def send_message(self, session_id: str, user_id: str, user_name: str,
                   content: str, message_type: str = "text") -> SessionMessage:
        """
        Send a message to a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            user_name: User name
            content: Message content
            message_type: Message type
            
        Returns:
            SessionMessage
        """
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        message_id = f"message_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        message = SessionMessage(
            message_id=message_id,
            session_id=session_id,
            user_id=user_id,
            user_name=user_name,
            content=content,
            message_type=message_type,
            timestamp=datetime.now().isoformat()
        )
        
        self.messages[message_id] = message
        self._save_messages()
        
        # Update user last active
        self._update_participant_activity(session_id, user_id)
        
        return message

    def _send_system_message(self, session_id: str, content: str):
        """Send a system message."""
        message_id = f"message_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        message = SessionMessage(
            message_id=message_id,
            session_id=session_id,
            user_id="system",
            user_name="System",
            content=content,
            message_type="system",
            timestamp=datetime.now().isoformat()
        )
        
        self.messages[message_id] = message
        self._save_messages()

    def _update_participant_activity(self, session_id: str, user_id: str):
        """Update participant last active time."""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        for participant in session.participants:
            if participant.user_id == user_id:
                participant.last_active = datetime.now().isoformat()
                participant.is_online = True
                break
        
        self._save_sessions()

    def get_session_messages(self, session_id: str, limit: int = 100) -> List[SessionMessage]:
        """Get messages for a session."""
        messages = [m for m in self.messages.values() if m.session_id == session_id]
        messages.sort(key=lambda x: x.timestamp)
        return messages[-limit:]

    def get_session_participants(self, session_id: str) -> List[SessionParticipant]:
        """Get participants for a session."""
        if session_id not in self.sessions:
            return []
        
        return self.sessions[session_id].participants

    def end_session(self, session_id: str) -> Tuple[bool, str]:
        """End a collaborative session."""
        if session_id not in self.sessions:
            return False, "Session not found"
        
        self.sessions[session_id].status = SessionStatus.ENDED
        self.sessions[session_id].ended_at = datetime.now().isoformat()
        self._save_sessions()
        
        self._send_system_message(session_id, "Session ended")
        
        return True, "Session ended"

    def update_participant_role(self, session_id: str, user_id: str, role: SessionRole) -> bool:
        """Update participant role."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        for participant in session.participants:
            if participant.user_id == user_id:
                participant.role = role
                self._save_sessions()
                return True
        
        return False

    def get_session(self, session_id: str) -> Optional[CollaborativeSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> List[CollaborativeSession]:
        """Get all sessions for a user."""
        user_sessions = []
        for session in self.sessions.values():
            for participant in session.participants:
                if participant.user_id == user_id:
                    user_sessions.append(session)
                    break
        
        return user_sessions

    def get_active_sessions(self) -> List[CollaborativeSession]:
        """Get all active sessions."""
        return [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]

    def mark_offline(self, session_id: str, user_id: str) -> bool:
        """Mark participant as offline."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        for participant in session.participants:
            if participant.user_id == user_id:
                participant.is_online = False
                self._save_sessions()
                return True
        
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get collaborative session statistics."""
        total_sessions = len(self.sessions)
        active_sessions = len(self.get_active_sessions())
        total_messages = len(self.messages)
        
        # Count by status
        by_status = {}
        for session in self.sessions.values():
            status = session.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_messages': total_messages,
            'by_status': by_status
        }

    def clear_old_sessions(self, days: int = 7) -> int:
        """Clear sessions older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            session_id for session_id, session in self.sessions.items()
            if session.ended_at and datetime.fromisoformat(session.ended_at) < cutoff_date
        ]
        
        for session_id in to_remove:
            # Remove messages
            message_ids = [m.message_id for m in self.messages.values() if m.session_id == session_id]
            for message_id in message_ids:
                del self.messages[message_id]
            
            del self.sessions[session_id]
        
        if to_remove:
            self._save_sessions()
            self._save_messages()
        
        return len(to_remove)
