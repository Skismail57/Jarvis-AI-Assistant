#!/usr/bin/env python3
"""
Test script for Biometric Authentication System
Demonstrates face recognition capabilities
"""

import sys
import os

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from assistant.security.biometric_auth import BiometricAuth, AuthMethod, AuthStatus

def test_face_recognition():
    """Test face recognition functionality."""
    print("=" * 70)
    print("  Biometric Authentication System - Face Recognition Test")
    print("=" * 70)
    
    # Initialize biometric auth system
    auth = BiometricAuth()
    print("\n✓ Biometric authentication system initialized")
    
    # Create a test user
    username = "test_user"
    print(f"\n[1] Creating user: {username}")
    user = auth.enroll_user(username)
    print(f"✓ User created: {user.user_id}")
    print(f"  Username: {user.username}")
    print(f"  Created at: {user.created_at}")
    
    # Simulate face enrollment (with dummy features)
    print(f"\n[2] Enrolling face template for {username}")
    # In real usage, this would come from face_recognition library
    # For testing, we'll use dummy feature vectors
    dummy_face_features = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    face_template = auth.enroll_face_template(
        user_id=user.user_id,
        face_features=dummy_face_features,
        confidence_threshold=0.7
    )
    print(f"✓ Face template enrolled: {face_template.template_id}")
    print(f"  Confidence threshold: {face_template.confidence_threshold}")
    
    # Test face authentication
    print(f"\n[3] Testing face authentication")
    # Simulate authentication with matching features
    auth_attempt = auth.authenticate_face(
        user_id=user.user_id,
        face_features=dummy_face_features
    )
    print(f"✓ Authentication attempt: {auth_attempt.attempt_id}")
    print(f"  Status: {auth_attempt.status.value}")
    print(f"  Confidence: {auth_attempt.confidence:.4f}")
    
    # Test with different features (should fail)
    print(f"\n[4] Testing with different face features (should fail)")
    different_features = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]
    failed_attempt = auth.authenticate_face(
        user_id=user.user_id,
        face_features=different_features
    )
    print(f"✓ Authentication attempt: {failed_attempt.attempt_id}")
    print(f"  Status: {failed_attempt.status.value}")
    print(f"  Confidence: {failed_attempt.confidence:.4f}")
    
    # Get user statistics
    print(f"\n[5] Authentication statistics")
    stats = auth.get_authentication_statistics()
    print(f"  Total attempts: {stats['total_attempts']}")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    print(f"  Total users: {stats['total_users']}")
    print(f"  Total templates: {stats['total_templates']}")
    print(f"  By method: {stats['by_method']}")
    print(f"  By status: {stats['by_status']}")
    
    # Get user attempts
    print(f"\n[6] User authentication attempts")
    user_attempts = auth.get_user_attempts(user.user_id)
    for attempt in user_attempts:
        print(f"  - {attempt.timestamp}: {attempt.status.value} (confidence: {attempt.confidence:.4f})")
    
    print("\n" + "=" * 70)
    print("  Face Recognition Test Complete")
    print("=" * 70)
    
    return auth

def test_voice_recognition():
    """Test voice recognition functionality."""
    print("\n" + "=" * 70)
    print("  Biometric Authentication System - Voice Recognition Test")
    print("=" * 70)
    
    # Initialize biometric auth system
    auth = BiometricAuth()
    print("\n✓ Biometric authentication system initialized")
    
    # Create a test user
    username = "voice_user"
    print(f"\n[1] Creating user: {username}")
    user = auth.enroll_user(username)
    print(f"✓ User created: {user.user_id}")
    
    # Simulate voice enrollment (with dummy features)
    print(f"\n[2] Enrolling voice template for {username}")
    # In real usage, this would come from MFCC features from audio
    dummy_voice_features = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.4, 0.3, 0.2, 0.1]
    
    voice_template = auth.enroll_voice_template(
        user_id=user.user_id,
        voice_features=dummy_voice_features,
        confidence_threshold=0.7
    )
    print(f"✓ Voice template enrolled: {voice_template.template_id}")
    
    # Test voice authentication
    print(f"\n[3] Testing voice authentication")
    auth_attempt = auth.authenticate_voice(
        user_id=user.user_id,
        voice_features=dummy_voice_features
    )
    print(f"✓ Authentication attempt: {auth_attempt.attempt_id}")
    print(f"  Status: {auth_attempt.status.value}")
    print(f"  Confidence: {auth_attempt.confidence:.4f}")
    
    print("\n" + "=" * 70)
    print("  Voice Recognition Test Complete")
    print("=" * 70)
    
    return auth

def test_multi_factor():
    """Test multi-factor authentication."""
    print("\n" + "=" * 70)
    print("  Biometric Authentication System - Multi-Factor Test")
    print("=" * 70)
    
    # Initialize biometric auth system
    auth = BiometricAuth()
    print("\n✓ Biometric authentication system initialized")
    
    # Create a test user
    username = "mfa_user"
    print(f"\n[1] Creating user: {username}")
    user = auth.enroll_user(username)
    print(f"✓ User created: {user.user_id}")
    
    # Enroll both voice and face
    print(f"\n[2] Enrolling both voice and face templates")
    voice_features = [0.1, 0.2, 0.3, 0.4, 0.5]
    face_features = [0.6, 0.7, 0.8, 0.9, 1.0]
    
    auth.enroll_voice_template(user.user_id, voice_features)
    auth.enroll_face_template(user.user_id, face_features)
    print("✓ Both templates enrolled")
    
    # Test multi-factor authentication
    print(f"\n[3] Testing multi-factor authentication")
    mfa_attempt = auth.authenticate_multi_factor(
        user_id=user.user_id,
        voice_features=voice_features,
        face_features=face_features
    )
    print(f"✓ MFA attempt: {mfa_attempt.attempt_id}")
    print(f"  Status: {mfa_attempt.status.value}")
    print(f"  Confidence: {mfa_attempt.confidence:.4f}")
    print(f"  Factors used: {mfa_attempt.metadata.get('factors_used', 0)}")
    
    print("\n" + "=" * 70)
    print("  Multi-Factor Authentication Test Complete")
    print("=" * 70)
    
    return auth

def main():
    """Run all biometric authentication tests."""
    print("\n" + "=" * 70)
    print("  JARVIS - Biometric Authentication System Tests")
    print("=" * 70)
    
    try:
        # Test face recognition
        test_face_recognition()
        
        # Test voice recognition
        test_voice_recognition()
        
        # Test multi-factor authentication
        test_multi_factor()
        
        print("\n" + "=" * 70)
        print("  All Biometric Tests Completed Successfully")
        print("=" * 70)
        print("\nNote: This is a simulation with dummy feature vectors.")
        print("For real face recognition, you need:")
        print("  - face-recognition library (pip install face-recognition)")
        print("  - dlib library (for face detection)")
        print("  - Camera access for live face capture")
        print("\nFor real voice recognition, you need:")
        print("  - Audio recording capabilities")
        print("  - MFCC feature extraction from audio")
        print("  - Voice pattern matching algorithms")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
