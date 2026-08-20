"""
Biometric Authentication System
Provides voice and face recognition for secure user authentication.
"""

import os
import json
import pickle
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class AuthMethod(Enum):
    VOICE = "voice"
    FACE = "face"
    MULTI_FACTOR = "multi_factor"


class AuthStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ENROLLMENT_REQUIRED = "enrollment_required"
    LOCKED = "locked"
    EXPIRED = "expired"


@dataclass
class BiometricTemplate:
    template_id: str
    user_id: str
    auth_method: AuthMethod
    template_data: bytes
    created_at: str
    last_used: str
    confidence_threshold: float = 0.7
    is_active: bool = True


@dataclass
class AuthAttempt:
    attempt_id: str
    user_id: str
    auth_method: AuthMethod
    status: AuthStatus
    confidence: float
    timestamp: str
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class UserProfile:
    user_id: str
    username: str
    voice_templates: List[str]
    face_templates: List[str]
    created_at: str
    last_login: str
    failed_attempts: int = 0
    is_locked: bool = False
    lock_until: Optional[str] = None
    mfa_enabled: bool = False


class BiometricAuth:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.auth_dir = os.path.join(self.base_dir, "data", "biometric_auth")
        self.templates_file = os.path.join(self.auth_dir, "templates.json")
        self.users_file = os.path.join(self.auth_dir, "users.json")
        self.attempts_file = os.path.join(self.auth_dir, "attempts.json")
        
        os.makedirs(self.auth_dir, exist_ok=True)
        
        # Load data
        self.templates = self._load_templates()
        self.users = self._load_users()
        self.attempts = self._load_attempts()
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.session_duration_minutes = 60
        
        # Active sessions
        self.active_sessions = {}

    def _load_templates(self) -> Dict[str, BiometricTemplate]:
        """Load biometric templates from disk."""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {template_id: BiometricTemplate(**template) for template_id, template in data.items()}
            except Exception:
                pass
        return {}

    def _save_templates(self):
        """Save biometric templates to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {template_id: asdict(template) for template_id, template in self.templates.items()}
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[BiometricAuth] Failed to save templates: {e}")

    def _load_users(self) -> Dict[str, UserProfile]:
        """Load user profiles from disk."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {user_id: UserProfile(**user) for user_id, user in data.items()}
            except Exception:
                pass
        return {}

    def _save_users(self):
        """Save user profiles to disk."""
        try:
            data = {user_id: asdict(user) for user_id, user in self.users.items()}
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[BiometricAuth] Failed to save users: {e}")

    def _load_attempts(self) -> Dict[str, AuthAttempt]:
        """Load authentication attempts from disk."""
        if os.path.exists(self.attempts_file):
            try:
                with open(self.attempts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {attempt_id: AuthAttempt(**attempt) for attempt_id, attempt in data.items()}
            except Exception:
                pass
        return {}

    def _save_attempts(self):
        """Save authentication attempts to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {attempt_id: asdict(attempt) for attempt_id, attempt in self.attempts.items()}
            with open(self.attempts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[BiometricAuth] Failed to save attempts: {e}")

    def enroll_user(self, username: str) -> UserProfile:
        """
        Create a new user profile.
        
        Args:
            username: Username for the new user
            
        Returns:
            Created UserProfile
        """
        user_id = f"user_{hashlib.md5(username.encode()).hexdigest()[:16]}"
        
        profile = UserProfile(
            user_id=user_id,
            username=username,
            voice_templates=[],
            face_templates=[],
            created_at=datetime.now().isoformat(),
            last_login=datetime.now().isoformat()
        )
        
        self.users[user_id] = profile
        self._save_users()
        
        return profile

    def enroll_voice_template(self, user_id: str, voice_features: List[float],
                             confidence_threshold: float = 0.7) -> BiometricTemplate:
        """
        Enroll a voice biometric template for a user.
        
        Args:
            user_id: User ID
            voice_features: Voice feature vector (from MFCC or similar)
            confidence_threshold: Minimum confidence for matching
            
        Returns:
            Created BiometricTemplate
        """
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")
        
        template_id = f"voice_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Serialize features
        template_data = pickle.dumps(voice_features)
        
        template = BiometricTemplate(
            template_id=template_id,
            user_id=user_id,
            auth_method=AuthMethod.VOICE,
            template_data=template_data,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            confidence_threshold=confidence_threshold
        )
        
        self.templates[template_id] = template
        self.users[user_id].voice_templates.append(template_id)
        self._save_templates()
        self._save_users()
        
        return template

    def enroll_face_template(self, user_id: str, face_features: List[float],
                           confidence_threshold: float = 0.7) -> BiometricTemplate:
        """
        Enroll a face biometric template for a user.
        
        Args:
            user_id: User ID
            face_features: Face feature vector (from face_recognition or similar)
            confidence_threshold: Minimum confidence for matching
            
        Returns:
            Created BiometricTemplate
        """
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")
        
        template_id = f"face_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Serialize features
        template_data = pickle.dumps(face_features)
        
        template = BiometricTemplate(
            template_id=template_id,
            user_id=user_id,
            auth_method=AuthMethod.FACE,
            template_data=template_data,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            confidence_threshold=confidence_threshold
        )
        
        self.templates[template_id] = template
        self.users[user_id].face_templates.append(template_id)
        self._save_templates()
        self._save_users()
        
        return template

    def authenticate_voice(self, user_id: str, voice_features: List[float],
                         ip_address: str = None, device_info: str = None) -> AuthAttempt:
        """
        Authenticate a user using voice biometrics.
        
        Args:
            user_id: User ID to authenticate
            voice_features: Voice feature vector to match
            ip_address: IP address of the attempt
            device_info: Device information
            
        Returns:
            AuthAttempt with authentication result
        """
        attempt_id = f"attempt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Check if user exists and is not locked
        if user_id not in self.users:
            attempt = AuthAttempt(
                attempt_id=attempt_id,
                user_id=user_id,
                auth_method=AuthMethod.VOICE,
                status=AuthStatus.ENROLLMENT_REQUIRED,
                confidence=0.0,
                timestamp=datetime.now().isoformat(),
                ip_address=ip_address,
                device_info=device_info
            )
            self.attempts[attempt_id] = attempt
            self._save_attempts()
            return attempt
        
        user = self.users[user_id]
        
        # Check if account is locked
        if user.is_locked:
            if user.lock_until:
                lock_until = datetime.fromisoformat(user.lock_until)
                if datetime.now() < lock_until:
                    attempt = AuthAttempt(
                        attempt_id=attempt_id,
                        user_id=user_id,
                        auth_method=AuthMethod.VOICE,
                        status=AuthStatus.LOCKED,
                        confidence=0.0,
                        timestamp=datetime.now().isoformat(),
                        ip_address=ip_address,
                        device_info=device_info,
                        metadata={'lock_until': user.lock_until}
                    )
                    self.attempts[attempt_id] = attempt
                    self._save_attempts()
                    return attempt
                else:
                    # Lock expired
                    user.is_locked = False
                    user.lock_until = None
                    user.failed_attempts = 0
                    self._save_users()
        
        # Match against voice templates
        best_match = None
        best_confidence = 0.0
        
        for template_id in user.voice_templates:
            if template_id in self.templates:
                template = self.templates[template_id]
                if not template.is_active:
                    continue
                
                stored_features = pickle.loads(template.template_data)
                confidence = self._calculate_similarity(voice_features, stored_features)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = template
        
        # Determine authentication result
        if best_match and best_confidence >= best_match.confidence_threshold:
            status = AuthStatus.SUCCESS
            user.failed_attempts = 0
            user.last_login = datetime.now().isoformat()
            self._save_users()
            
            # Create session
            session_id = self._create_session(user_id)
        else:
            status = AuthStatus.FAILED
            user.failed_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_attempts >= self.max_failed_attempts:
                user.is_locked = True
                user.lock_until = (datetime.now() + 
                                 timedelta(minutes=self.lockout_duration_minutes)).isoformat()
            
            self._save_users()
            session_id = None
        
        attempt = AuthAttempt(
            attempt_id=attempt_id,
            user_id=user_id,
            auth_method=AuthMethod.VOICE,
            status=status,
            confidence=best_confidence,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            device_info=device_info,
            metadata={'session_id': session_id} if session_id else None
        )
        
        self.attempts[attempt_id] = attempt
        self._save_attempts()
        
        return attempt

    def authenticate_face(self, user_id: str, face_features: List[float],
                        ip_address: str = None, device_info: str = None) -> AuthAttempt:
        """
        Authenticate a user using face biometrics.
        
        Args:
            user_id: User ID to authenticate
            face_features: Face feature vector to match
            ip_address: IP address of the attempt
            device_info: Device information
            
        Returns:
            AuthAttempt with authentication result
        """
        attempt_id = f"attempt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Check if user exists and is not locked
        if user_id not in self.users:
            attempt = AuthAttempt(
                attempt_id=attempt_id,
                user_id=user_id,
                auth_method=AuthMethod.FACE,
                status=AuthStatus.ENROLLMENT_REQUIRED,
                confidence=0.0,
                timestamp=datetime.now().isoformat(),
                ip_address=ip_address,
                device_info=device_info
            )
            self.attempts[attempt_id] = attempt
            self._save_attempts()
            return attempt
        
        user = self.users[user_id]
        
        # Check if account is locked
        if user.is_locked:
            if user.lock_until:
                lock_until = datetime.fromisoformat(user.lock_until)
                if datetime.now() < lock_until:
                    attempt = AuthAttempt(
                        attempt_id=attempt_id,
                        user_id=user_id,
                        auth_method=AuthMethod.FACE,
                        status=AuthStatus.LOCKED,
                        confidence=0.0,
                        timestamp=datetime.now().isoformat(),
                        ip_address=ip_address,
                        device_info=device_info,
                        metadata={'lock_until': user.lock_until}
                    )
                    self.attempts[attempt_id] = attempt
                    self._save_attempts()
                    return attempt
                else:
                    # Lock expired
                    user.is_locked = False
                    user.lock_until = None
                    user.failed_attempts = 0
                    self._save_users()
        
        # Match against face templates
        best_match = None
        best_confidence = 0.0
        
        for template_id in user.face_templates:
            if template_id in self.templates:
                template = self.templates[template_id]
                if not template.is_active:
                    continue
                
                stored_features = pickle.loads(template.template_data)
                confidence = self._calculate_similarity(face_features, stored_features)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = template
        
        # Determine authentication result
        if best_match and best_confidence >= best_match.confidence_threshold:
            status = AuthStatus.SUCCESS
            user.failed_attempts = 0
            user.last_login = datetime.now().isoformat()
            self._save_users()
            
            # Create session
            session_id = self._create_session(user_id)
        else:
            status = AuthStatus.FAILED
            user.failed_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_attempts >= self.max_failed_attempts:
                user.is_locked = True
                user.lock_until = (datetime.now() + 
                                 timedelta(minutes=self.lockout_duration_minutes)).isoformat()
            
            self._save_users()
            session_id = None
        
        attempt = AuthAttempt(
            attempt_id=attempt_id,
            user_id=user_id,
            auth_method=AuthMethod.FACE,
            status=status,
            confidence=best_confidence,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            device_info=device_info,
            metadata={'session_id': session_id} if session_id else None
        )
        
        self.attempts[attempt_id] = attempt
        self._save_attempts()
        
        return attempt

    def authenticate_multi_factor(self, user_id: str, voice_features: List[float] = None,
                                face_features: List[float] = None,
                                ip_address: str = None, device_info: str = None) -> AuthAttempt:
        """
        Authenticate using multi-factor biometrics.
        
        Args:
            user_id: User ID to authenticate
            voice_features: Voice feature vector (optional)
            face_features: Face feature vector (optional)
            ip_address: IP address of the attempt
            device_info: Device information
            
        Returns:
            AuthAttempt with authentication result
        """
        attempt_id = f"attempt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        if user_id not in self.users:
            attempt = AuthAttempt(
                attempt_id=attempt_id,
                user_id=user_id,
                auth_method=AuthMethod.MULTI_FACTOR,
                status=AuthStatus.ENROLLMENT_REQUIRED,
                confidence=0.0,
                timestamp=datetime.now().isoformat(),
                ip_address=ip_address,
                device_info=device_info
            )
            self.attempts[attempt_id] = attempt
            self._save_attempts()
            return attempt
        
        user = self.users[user_id]
        
        # Check if account is locked
        if user.is_locked:
            if user.lock_until:
                lock_until = datetime.fromisoformat(user.lock_until)
                if datetime.now() < lock_until:
                    attempt = AuthAttempt(
                        attempt_id=attempt_id,
                        user_id=user_id,
                        auth_method=AuthMethod.MULTI_FACTOR,
                        status=AuthStatus.LOCKED,
                        confidence=0.0,
                        timestamp=datetime.now().isoformat(),
                        ip_address=ip_address,
                        device_info=device_info,
                        metadata={'lock_until': user.lock_until}
                    )
                    self.attempts[attempt_id] = attempt
                    self._save_attempts()
                    return attempt
        
        # Authenticate each factor
        voice_confidence = 0.0
        face_confidence = 0.0
        
        if voice_features:
            voice_attempt = self.authenticate_voice(user_id, voice_features, ip_address, device_info)
            voice_confidence = voice_attempt.confidence
        
        if face_features:
            face_attempt = self.authenticate_face(user_id, face_features, ip_address, device_info)
            face_confidence = face_attempt.confidence
        
        # Combine results
        factors_used = 0
        total_confidence = 0.0
        
        if voice_features:
            factors_used += 1
            total_confidence += voice_confidence
        
        if face_features:
            factors_used += 1
            total_confidence += face_confidence
        
        avg_confidence = total_confidence / factors_used if factors_used > 0 else 0.0
        
        # Require at least one factor and minimum confidence
        if factors_used > 0 and avg_confidence >= 0.7:
            status = AuthStatus.SUCCESS
            user.failed_attempts = 0
            user.last_login = datetime.now().isoformat()
            self._save_users()
            
            session_id = self._create_session(user_id)
        else:
            status = AuthStatus.FAILED
            user.failed_attempts += 1
            
            if user.failed_attempts >= self.max_failed_attempts:
                user.is_locked = True
                user.lock_until = (datetime.now() + 
                                 timedelta(minutes=self.lockout_duration_minutes)).isoformat()
            
            self._save_users()
            session_id = None
        
        attempt = AuthAttempt(
            attempt_id=attempt_id,
            user_id=user_id,
            auth_method=AuthMethod.MULTI_FACTOR,
            status=status,
            confidence=avg_confidence,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            device_info=device_info,
            metadata={
                'session_id': session_id,
                'voice_confidence': voice_confidence,
                'face_confidence': face_confidence,
                'factors_used': factors_used
            }
        )
        
        self.attempts[attempt_id] = attempt
        self._save_attempts()
        
        return attempt

    def _calculate_similarity(self, features1: List[float], features2: List[float]) -> float:
        """Calculate similarity between two feature vectors using cosine similarity."""
        try:
            import numpy as np
            
            vec1 = np.array(features1)
            vec2 = np.array(features2)
            
            # Ensure same length
            if len(vec1) != len(vec2):
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
            return float(similarity)
            
        except Exception as e:
            print(f"[BiometricAuth] Failed to calculate similarity: {e}")
            return 0.0

    def _create_session(self, user_id: str) -> str:
        """Create an authentication session."""
        session_id = f"session_{hashlib.md5(f"{user_id}{datetime.now().isoformat()}".encode()).hexdigest()}"
        
        expires_at = datetime.now() + timedelta(minutes=self.session_duration_minutes)
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        return session_id

    def validate_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an active session.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            (is_valid, user_id)
        """
        if session_id not in self.active_sessions:
            return False, None
        
        session = self.active_sessions[session_id]
        expires_at = datetime.fromisoformat(session['expires_at'])
        
        if datetime.now() > expires_at:
            del self.active_sessions[session_id]
            return False, None
        
        return True, session['user_id']

    def revoke_session(self, session_id: str) -> bool:
        """Revoke an active session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def revoke_all_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user."""
        revoked = 0
        sessions_to_remove = []
        
        for session_id, session in self.active_sessions.items():
            if session['user_id'] == user_id:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            revoked += 1
        
        return revoked

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get a user profile by ID."""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[UserProfile]:
        """Get a user profile by username."""
        username_lower = username.lower()
        
        for user in self.users.values():
            if user.username.lower() == username_lower:
                return user
        
        return None

    def remove_template(self, template_id: str) -> bool:
        """Remove a biometric template."""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        user_id = template.user_id
        
        # Remove from user's template list
        if user_id in self.users:
            if template.auth_method == AuthMethod.VOICE:
                self.users[user_id].voice_templates = [
                    tid for tid in self.users[user_id].voice_templates if tid != template_id
                ]
            else:
                self.users[user_id].face_templates = [
                    tid for tid in self.users[user_id].face_templates if tid != template_id
                ]
            self._save_users()
        
        del self.templates[template_id]
        self._save_templates()
        
        return True

    def disable_user(self, user_id: str) -> bool:
        """Disable a user account."""
        if user_id not in self.users:
            return False
        
        # Deactivate all templates
        for template_id in self.users[user_id].voice_templates + self.users[user_id].face_templates:
            if template_id in self.templates:
                self.templates[template_id].is_active = False
        
        self._save_templates()
        return True

    def enable_user(self, user_id: str) -> bool:
        """Enable a user account."""
        if user_id not in self.users:
            return False
        
        # Activate all templates
        for template_id in self.users[user_id].voice_templates + self.users[user_id].face_templates:
            if template_id in self.templates:
                self.templates[template_id].is_active = True
        
        self._save_templates()
        return True

    def unlock_account(self, user_id: str) -> bool:
        """Unlock a locked account."""
        if user_id not in self.users:
            return False
        
        self.users[user_id].is_locked = False
        self.users[user_id].lock_until = None
        self.users[user_id].failed_attempts = 0
        self._save_users()
        
        return True

    def get_authentication_statistics(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        total_attempts = len(self.attempts)
        
        if total_attempts == 0:
            return {
                'total_attempts': 0,
                'success_rate': 0.0,
                'by_method': {},
                'by_status': {}
            }
        
        # Count by method
        by_method = defaultdict(int)
        for attempt in self.attempts.values():
            by_method[attempt.auth_method.value] += 1
        
        # Count by status
        by_status = defaultdict(int)
        for attempt in self.attempts.values():
            by_status[attempt.status.value] += 1
        
        # Calculate success rate
        successful = by_status.get('success', 0)
        success_rate = successful / total_attempts
        
        return {
            'total_attempts': total_attempts,
            'success_rate': round(success_rate, 4),
            'by_method': dict(by_method),
            'by_status': dict(by_status),
            'total_users': len(self.users),
            'total_templates': len(self.templates),
            'active_sessions': len(self.active_sessions)
        }

    def get_user_attempts(self, user_id: str, limit: int = 50) -> List[AuthAttempt]:
        """Get authentication attempts for a specific user."""
        user_attempts = [
            attempt for attempt in self.attempts.values()
            if attempt.user_id == user_id
        ]
        
        # Sort by timestamp (newest first)
        user_attempts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return user_attempts[:limit]

    def clear_old_attempts(self, days: int = 30) -> int:
        """Clear authentication attempts older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        removed = 0
        for attempt_id, attempt in list(self.attempts.items()):
            attempt_date = datetime.fromisoformat(attempt.timestamp)
            if attempt_date < cutoff_date:
                del self.attempts[attempt_id]
                removed += 1
        
        if removed > 0:
            self._save_attempts()
        
        return removed

    def export_auth_data(self, export_path: str) -> Tuple[bool, str]:
        """Export authentication data (without sensitive template data)."""
        try:
            export_data = {
                'users': {user_id: asdict(user) for user_id, user in self.users.items()},
                'attempts': {attempt_id: asdict(attempt) for attempt_id, attempt 
                            in self.attempts.items()},
                'statistics': self.get_authentication_statistics(),
                'exported_at': datetime.now().isoformat(),
                'note': 'Template data not included for security'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Authentication data exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"
