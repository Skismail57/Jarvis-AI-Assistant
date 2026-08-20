import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import './BiometricEnroll.css';

const BiometricEnroll = () => {
  const [username, setUsername] = useState('');
  const [authMethod, setAuthMethod] = useState('face'); // 'face' or 'voice'
  const [isRecording, setIsRecording] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [enrollmentStatus, setEnrollmentStatus] = useState('');
  const [error, setError] = useState('');
  const [features, setFeatures] = useState([]);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const navigate = useNavigate();
  const { signup } = useAuthStore();

  useEffect(() => {
    // Initialize camera for face enrollment
    if (authMethod === 'face') {
      startCamera();
    }
    return () => {
      stopCamera();
    };
  }, [authMethod]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      setError('Camera access denied or not available');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
    }
  };

  const captureFace = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    setIsCapturing(true);
    const canvas = canvasRef.current;
    const video = videoRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    // Convert to base64
    const imageData = canvas.toDataURL('image/jpeg');

    // Extract face features (simulated - in production use face-recognition library)
    try {
      // For now, generate dummy features
      const dummyFeatures = Array.from({ length: 128 }, () => Math.random());
      setFeatures(dummyFeatures);
      setEnrollmentStatus('Face captured successfully');
    } catch (err) {
      setError('Face capture failed');
    }

    setIsCapturing(false);
  };

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        
        // Extract voice features (simulated)
        try {
          const dummyFeatures = Array.from({ length: 128 }, () => Math.random());
          setFeatures(dummyFeatures);
          setEnrollmentStatus('Voice recorded successfully');
        } catch (err) {
          setError('Voice feature extraction failed');
        }
      };

      mediaRecorder.start();
      setIsRecording(true);

      // Record for 3 seconds
      setTimeout(() => {
        mediaRecorder.stop();
        setIsRecording(false);
      }, 3000);

    } catch (err) {
      setError('Microphone access denied or not available');
    }
  };

  const handleEnroll = async () => {
    if (!username || features.length === 0) {
      setError('Please provide username and complete biometric capture');
      return;
    }

    try {
      const response = await fetch('/api/auth/enroll', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          auth_method: authMethod,
          features,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setEnrollmentStatus('Enrollment successful! You can now use biometric login.');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setError(data.message || 'Enrollment failed');
      }
    } catch (err) {
      console.error('Enrollment error:', err);
      setError('Network error during enrollment. Please try again.');
    }
  };

  return (
    <div className="biometric-enroll-container">
      <div className="enroll-card">
        <h2>Biometric Enrollment</h2>
        <p className="subtitle">Set up face or voice recognition for secure login</p>

        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
          />
        </div>

        <div className="method-selector">
          <button
            className={`method-btn ${authMethod === 'face' ? 'active' : ''}`}
            onClick={() => setAuthMethod('face')}
          >
            👤 Face Recognition
          </button>
          <button
            className={`method-btn ${authMethod === 'voice' ? 'active' : ''}`}
            onClick={() => setAuthMethod('voice')}
          >
            🎤 Voice Recognition
          </button>
        </div>

        {authMethod === 'face' && (
          <div className="face-capture-section">
            <div className="video-container">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="video-feed"
              />
              <canvas ref={canvasRef} className="hidden-canvas" />
            </div>
            <button
              className="capture-btn"
              onClick={captureFace}
              disabled={isCapturing}
            >
              {isCapturing ? 'Capturing...' : '📷 Capture Face'}
            </button>
          </div>
        )}

        {authMethod === 'voice' && (
          <div className="voice-capture-section">
            <div className="voice-visualizer">
              <div className={`waveform ${isRecording ? 'recording' : ''}`}>
                {isRecording && (
                  <>
                    <span></span><span></span><span></span><span></span><span></span>
                  </>
                )}
              </div>
            </div>
            <button
              className="record-btn"
              onClick={startVoiceRecording}
              disabled={isRecording}
            >
              {isRecording ? '🔴 Recording...' : '🎤 Record Voice'}
            </button>
            <p className="recording-hint">Say "Hello, this is my voice" clearly</p>
          </div>
        )}

        {enrollmentStatus && (
          <div className="status-message success">
            {enrollmentStatus}
          </div>
        )}

        {error && (
          <div className="status-message error">
            {error}
          </div>
        )}

        <button
          className="enroll-btn"
          onClick={handleEnroll}
          disabled={!username || features.length === 0}
        >
          Complete Enrollment
        </button>

        <div className="back-link">
          <a href="/login">← Back to Login</a>
        </div>
      </div>
    </div>
  );
};

export default BiometricEnroll;
