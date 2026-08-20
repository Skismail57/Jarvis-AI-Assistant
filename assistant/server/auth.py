"""
Authentication API Endpoints
Handles login, signup, logout, and biometric authentication
"""

import os
import sys
import json
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import HTTPException, Depends
from pydantic import BaseModel

from ..security.biometric_auth import BiometricAuth, AuthMethod, AuthStatus
from ..config import settings, ROOT_DIR


# Pydantic models for authentication
class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class BiometricRequest(BaseModel):
    username: str
    face_features: Optional[list] = None
    voice_features: Optional[list] = None


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None


# Simple user storage (in production, use a proper database)
USERS_FILE = ROOT_DIR / "data" / "users.json"
TOKENS_FILE = ROOT_DIR / "data" / "tokens.json"

# Biometric auth system
biometric_auth = BiometricAuth()


def _load_users() -> Dict[str, Dict[str, Any]]:
    """Load users from file."""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_users(users: Dict[str, Dict[str, Any]]):
    """Save users to file."""
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"[Auth] Failed to save users: {e}")


def _load_tokens() -> Dict[str, Dict[str, Any]]:
    """Load tokens from file."""
    if TOKENS_FILE.exists():
        try:
            with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_tokens(tokens: Dict[str, Dict[str, Any]]):
    """Save tokens to file."""
    try:
        TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        print(f"[Auth] Failed to save tokens: {e}")


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def _verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a token and return user data if valid."""
    tokens = _load_tokens()
    
    # Clean expired tokens
    now = datetime.now()
    valid_tokens = {}
    
    for tok, data in tokens.items():
        expires_at = datetime.fromisoformat(data.get('expires_at', ''))
        if now < expires_at:
            valid_tokens[tok] = data
    
    if valid_tokens != tokens:
        _save_tokens(valid_tokens)
    
    if token in valid_tokens:
        return valid_tokens[token]
    
    return None


async def login(request: LoginRequest) -> AuthResponse:
    """
    Handle user login with username and password.
    """
    users = _load_users()
    
    # Find user by username
    user_data = None
    for user_id, data in users.items():
        if data.get('username') == request.username:
            user_data = data
            break
    
    if not user_data:
        return AuthResponse(
            success=False,
            message="User not found"
        )
    
    # Verify password
    hashed_password = _hash_password(request.password)
    if user_data.get('password_hash') != hashed_password:
        return AuthResponse(
            success=False,
            message="Invalid password"
        )
    
    # Generate token
    token = _generate_token()
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    
    # Save token
    tokens = _load_tokens()
    tokens[token] = {
        'user_id': user_data.get('user_id'),
        'username': user_data.get('username'),
        'expires_at': expires_at,
        'created_at': datetime.now().isoformat()
    }
    _save_tokens(tokens)
    
    # Update last login
    user_data['last_login'] = datetime.now().isoformat()
    users[user_data['user_id']] = user_data
    _save_users(users)
    
    # Return user data (without password)
    user_response = {
        'user_id': user_data.get('user_id'),
        'username': user_data.get('username'),
        'email': user_data.get('email'),
        'created_at': user_data.get('created_at'),
        'last_login': user_data.get('last_login')
    }
    
    return AuthResponse(
        success=True,
        message="Login successful",
        token=token,
        user=user_response
    )


async def signup(request: SignupRequest) -> AuthResponse:
    """
    Handle user registration.
    """
    users = _load_users()
    
    # Check if username already exists
    for user_data in users.values():
        if user_data.get('username') == request.username:
            return AuthResponse(
                success=False,
                message="Username already exists"
            )
    
    # Check if email already exists
    if request.email:
        for user_data in users.values():
            if user_data.get('email') == request.email:
                return AuthResponse(
                    success=False,
                    message="Email already registered"
                )
    
    # Create user
    user_id = f"user_{secrets.token_hex(8)}"
    password_hash = _hash_password(request.password)
    
    user_data = {
        'user_id': user_id,
        'username': request.username,
        'email': request.email,
        'password_hash': password_hash,
        'created_at': datetime.now().isoformat(),
        'last_login': None,
        'is_active': True
    }
    
    users[user_id] = user_data
    _save_users(users)
    
    # Also create biometric user profile
    try:
        biometric_auth.enroll_user(request.username)
    except Exception as e:
        print(f"[Auth] Failed to create biometric profile: {e}")
    
    # Generate token
    token = _generate_token()
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    
    # Save token
    tokens = _load_tokens()
    tokens[token] = {
        'user_id': user_id,
        'username': request.username,
        'expires_at': expires_at,
        'created_at': datetime.now().isoformat()
    }
    _save_tokens(tokens)
    
    # Return user data
    user_response = {
        'user_id': user_id,
        'username': request.username,
        'email': request.email,
        'created_at': user_data['created_at'],
        'last_login': None
    }
    
    return AuthResponse(
        success=True,
        message="Registration successful",
        token=token,
        user=user_response
    )


async def logout(token: str) -> AuthResponse:
    """
    Handle user logout.
    """
    tokens = _load_tokens()
    
    if token in tokens:
        del tokens[token]
        _save_tokens(tokens)
        return AuthResponse(
            success=True,
            message="Logout successful"
        )
    
    return AuthResponse(
        success=True,
        message="Already logged out"
    )


async def verify_token(token: str) -> AuthResponse:
    """
    Verify if a token is valid.
    """
    token_data = _verify_token(token)
    
    if token_data:
        return AuthResponse(
            success=True,
            message="Token valid",
            user={
                'user_id': token_data.get('user_id'),
                'username': token_data.get('username')
            }
        )
    
    return AuthResponse(
        success=False,
        message="Invalid or expired token"
    )


async def biometric_authenticate(request: BiometricRequest) -> AuthResponse:
    """
    Handle biometric authentication (face/voice).
    """
    # Get user by username
    user = biometric_auth.get_user_by_username(request.username)
    
    if not user:
        return AuthResponse(
            success=False,
            message="User not found. Please enroll biometrics first."
        )
    
    # Perform biometric authentication
    if request.face_features:
        attempt = biometric_auth.authenticate_face(
            user_id=user.user_id,
            face_features=request.face_features
        )
    elif request.voice_features:
        attempt = biometric_auth.authenticate_voice(
            user_id=user.user_id,
            voice_features=request.voice_features
        )
    else:
        return AuthResponse(
            success=False,
            message="No biometric data provided"
        )
    
    if attempt.status == AuthStatus.SUCCESS:
        # Generate token
        token = _generate_token()
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        # Save token
        tokens = _load_tokens()
        tokens[token] = {
            'user_id': user.user_id,
            'username': user.username,
            'expires_at': expires_at,
            'created_at': datetime.now().isoformat()
        }
        _save_tokens(tokens)
        
        # Update last login
        users = _load_users()
        if user.user_id in users:
            users[user.user_id]['last_login'] = datetime.now().isoformat()
            _save_users(users)
        
        user_response = {
            'user_id': user.user_id,
            'username': user.username,
            'email': None,
            'created_at': user.created_at,
            'last_login': user.last_login
        }
        
        return AuthResponse(
            success=True,
            message="Biometric authentication successful",
            token=token,
            user=user_response
        )
    elif attempt.status == AuthStatus.ENROLLMENT_REQUIRED:
        return AuthResponse(
            success=False,
            message="Biometric enrollment required. Please enroll face or voice first."
        )
    else:
        return AuthResponse(
            success=False,
            message="Biometric authentication failed"
        )


async def enroll_biometric(username: str, auth_method: str, features: list) -> AuthResponse:
    """
    Enroll biometric data for a user.
    """
    user = biometric_auth.get_user_by_username(username)
    
    if not user:
        # Create user if doesn't exist
        user = biometric_auth.enroll_user(username)
    
    try:
        if auth_method == 'face':
            biometric_auth.enroll_face_template(
                user_id=user.user_id,
                face_features=features
            )
        elif auth_method == 'voice':
            biometric_auth.enroll_voice_template(
                user_id=user.user_id,
                voice_features=features
            )
        else:
            return AuthResponse(
                success=False,
                message="Invalid authentication method"
            )
        
        return AuthResponse(
            success=True,
            message=f"{auth_method.capitalize()} enrollment successful"
        )
    except Exception as e:
        return AuthResponse(
            success=False,
            message=f"Enrollment failed: {str(e)}"
        )


async def check_biometric_enrollment(username: str) -> Dict[str, Any]:
    """
    Check if a user has biometric enrollment.
    """
    user = biometric_auth.get_user_by_username(username)
    
    if not user:
        return {
            "has_biometric": False,
            "message": "User not found"
        }
    
    has_face = len(user.face_templates) > 0
    has_voice = len(user.voice_templates) > 0
    
    return {
        "has_biometric": has_face or has_voice,
        "has_face": has_face,
        "has_voice": has_voice,
        "message": "Biometric enrollment found" if (has_face or has_voice) else "No biometric enrollment"
    }
