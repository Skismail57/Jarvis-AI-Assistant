"""
Custom Wake Word Training System
Allows users to train custom wake words with their own voice samples.
"""

import os
import json
import numpy as np
import pickle
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import queue
import time


@dataclass
class WakeWordModel:
    word: str
    user_id: str
    samples: List[np.ndarray]
    mfcc_features: List[np.ndarray]
    threshold: float
    created_at: str
    accuracy: float = 0.0


@dataclass
class TrainingSession:
    session_id: str
    user_id: str
    target_word: str
    required_samples: int
    collected_samples: int
    status: str  # 'collecting', 'training', 'complete', 'failed'
    progress: float
    error_message: Optional[str] = None


class WakeWordTrainer:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = os.path.join(self.base_dir, "data", "wake_word_models")
        self.training_sessions_dir = os.path.join(self.base_dir, "data", "training_sessions")
        
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.training_sessions_dir, exist_ok=True)
        
        self.current_session: Optional[TrainingSession] = None
        self.audio_queue = queue.Queue()
        self.is_collecting = False
        self.collection_thread = None
        
        # Audio recording setup
        self.sample_rate = 16000
        self.chunk_duration = 2.0  # seconds
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # Try to import audio libraries
        self.pyaudio_available = False
        try:
            import pyaudio
            self.pyaudio = pyaudio
            self.pyaudio_available = True
        except ImportError:
            print("[WakeWordTrainer] PyAudio not available. Install with: pip install pyaudio")

    def start_training_session(self, user_id: str, target_word: str, 
                              required_samples: int = 20) -> TrainingSession:
        """
        Start a new wake word training session.
        
        Args:
            user_id: User identifier
            target_word: The wake word to train
            required_samples: Number of audio samples required for training
        """
        session_id = f"{user_id}_{target_word}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = TrainingSession(
            session_id=session_id,
            user_id=user_id,
            target_word=target_word.lower(),
            required_samples=required_samples,
            collected_samples=0,
            status='collecting',
            progress=0.0
        )
        
        self.current_session = session
        self._save_session(session
        
        print(f"[WakeWordTrainer] Started training session for '{target_word}'")
        print(f"[WakeWordTrainer] Required samples: {required_samples}")
        
        return session

    def collect_audio_sample(self) -> bool:
        """
        Record a single audio sample for the current training session.
        
        Returns:
            True if sample was collected successfully
        """
        if not self.current_session or self.current_session.status != 'collecting':
            print("[WakeWordTrainer] No active training session")
            return False
        
        if not self.pyaudio_available:
            print("[WakeWordTrainer] PyAudio not available")
            return False
        
        try:
            print(f"[WakeWordTrainer] Recording sample {self.current_session.collected_samples + 1}/{self.current_session.required_samples}")
            print("[WakeWordTrainer] Say the wake word now...")
            
            audio_data = self._record_audio(self.chunk_duration)
            
            if audio_data is not None:
                # Save audio sample
                sample_path = self._save_audio_sample(
                    self.current_session.session_id,
                    self.current_session.collected_samples,
                    audio_data
                )
                
                self.current_session.collected_samples += 1
                self.current_session.progress = (self.current_session.collected_samples / 
                                                self.current_session.required_samples) * 100
                
                self._save_session(self.current_session)
                
                print(f"[WakeWordTrainer] Sample {self.current_session.collected_samples}/{self.current_session.required_samples} collected")
                
                if self.current_session.collected_samples >= self.current_session.required_samples:
                    self.current_session.status = 'training'
                    self._save_session(self.current_session)
                    print("[WakeWordTrainer] All samples collected. Ready to train.")
                
                return True
            
        except Exception as e:
            print(f"[WakeWordTrainer] Failed to collect sample: {e}")
            return False
        
        return False

    def _record_audio(self, duration: float) -> Optional[np.ndarray]:
        """Record audio for specified duration."""
        try:
            p = self.pyaudio.PyAudio()
            
            stream = p.open(
                format=self.pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            print(f"[WakeWordTrainer] Recording for {duration} seconds...")
            frames = []
            
            for _ in range(0, int(self.sample_rate / 1024 * duration)):
                data = stream.read(1024)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Convert to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            
            return audio_data
            
        except Exception as e:
            print(f"[WakeWordTrainer] Recording failed: {e}")
            return None

    def _save_audio_sample(self, session_id: str, sample_num: int, 
                         audio_data: np.ndarray) -> str:
        """Save audio sample to disk."""
        session_dir = os.path.join(self.training_sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        sample_path = os.path.join(session_dir, f"sample_{sample_num:03d}.npy")
        np.save(sample_path, audio_data)
        
        return sample_path

    def train_model(self) -> WakeWordModel:
        """
        Train a wake word model from collected samples.
        
        Returns:
            Trained WakeWordModel
        """
        if not self.current_session or self.current_session.status != 'training':
            raise RuntimeError("No training session ready for training")
        
        try:
            self.current_session.status = 'training'
            self._save_session(self.current_session)
            
            print("[WakeWordTrainer] Training wake word model...")
            
            # Load all audio samples
            session_dir = os.path.join(self.training_sessions_dir, self.current_session.session_id)
            samples = []
            
            for i in range(self.current_session.collected_samples):
                sample_path = os.path.join(session_dir, f"sample_{i:03d}.npy")
                if os.path.exists(sample_path):
                    audio_data = np.load(sample_path)
                    samples.append(audio_data)
            
            if len(samples) < 5:
                raise RuntimeError("Need at least 5 samples for training")
            
            # Extract MFCC features from all samples
            mfcc_features = []
            for sample in samples:
                mfcc = self._extract_mfcc(sample)
                if mfcc is not None:
                    mfcc_features.append(mfcc)
            
            if len(mfcc_features) < 5:
                raise RuntimeError("Failed to extract features from samples")
            
            # Calculate model template (average of MFCC features)
            avg_mfcc = np.mean(mfcc_features, axis=0)
            
            # Calculate threshold based on variance
            distances = [np.linalg.norm(mfcc - avg_mfcc) for mfcc in mfcc_features]
            threshold = np.mean(distances) + 2 * np.std(distances)
            
            # Create model
            model = WakeWordModel(
                word=self.current_session.target_word,
                user_id=self.current_session.user_id,
                samples=samples,
                mfcc_features=mfcc_features,
                threshold=float(threshold),
                created_at=datetime.now().isoformat(),
                accuracy=self._estimate_accuracy(mfcc_features, avg_mfcc, threshold)
            )
            
            # Save model
            model_path = self._save_model(model)
            
            self.current_session.status = 'complete'
            self.current_session.progress = 100.0
            self._save_session(self.current_session)
            
            print(f"[WakeWordTrainer] Training complete! Model saved to {model_path}")
            print(f"[WakeWordTrainer] Estimated accuracy: {model.accuracy:.2f}")
            print(f"[WakeWordTrainer] Detection threshold: {threshold:.4f}")
            
            return model
            
        except Exception as e:
            self.current_session.status = 'failed'
            self.current_session.error_message = str(e)
            self._save_session(self.current_session)
            raise RuntimeError(f"Training failed: {e}")

    def _extract_mfcc(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """Extract MFCC features from audio data."""
        try:
            import librosa
            import librosa.feature
            
            # Ensure audio is the right length
            if len(audio_data) < self.sample_rate:
                audio_data = np.pad(audio_data, (0, self.sample_rate - len(audio_data)))
            elif len(audio_data) > self.sample_rate:
                audio_data = audio_data[:self.sample_rate]
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(
                y=audio_data,
                sr=self.sample_rate,
                n_mfcc=13,
                n_fft=512,
                hop_length=256
            )
            
            # Take mean across time
            mfcc_mean = np.mean(mfcc, axis=1)
            
            return mfcc_mean
            
        except ImportError:
            print("[WakeWordTrainer] librosa not available. Install with: pip install librosa")
            return None
        except Exception as e:
            print(f"[WakeWordTrainer] MFCC extraction failed: {e}")
            return None

    def _estimate_accuracy(self, mfcc_features: List[np.ndarray], 
                          avg_mfcc: np.ndarray, threshold: float) -> float:
        """Estimate model accuracy based on training data."""
        distances = [np.linalg.norm(mfcc - avg_mfcc) for mfcc in mfcc_features]
        correct_detections = sum(1 for d in distances if d < threshold)
        accuracy = correct_detections / len(distances)
        return accuracy

    def _save_model(self, model: WakeWordModel) -> str:
        """Save trained model to disk."""
        model_filename = f"{model.user_id}_{model.word}_model.pkl"
        model_path = os.path.join(self.models_dir, model_filename)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        return model_path

    def load_model(self, user_id: str, word: str) -> Optional[WakeWordModel]:
        """Load a trained wake word model."""
        model_filename = f"{user_id}_{word}_model.pkl"
        model_path = os.path.join(self.models_dir, model_filename)
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"[WakeWordTrainer] Failed to load model: {e}")
        
        return None

    def detect_wake_word(self, audio_data: np.ndarray, model: WakeWordModel) -> Tuple[bool, float]:
        """
        Detect if the wake word is present in audio data.
        
        Args:
            audio_data: Audio data to analyze
            model: Trained wake word model
            
        Returns:
            (is_detected, confidence_score)
        """
        try:
            mfcc = self._extract_mfcc(audio_data)
            if mfcc is None:
                return False, 0.0
            
            # Calculate distance from model template
            distance = np.linalg.norm(mfcc - np.mean(model.mfcc_features, axis=0))
            
            # Convert distance to confidence score
            confidence = max(0.0, 1.0 - (distance / model.threshold))
            
            is_detected = distance < model.threshold
            
            return is_detected, confidence
            
        except Exception as e:
            print(f"[WakeWordTrainer] Detection failed: {e}")
            return False, 0.0

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available trained models."""
        models = []
        
        if os.path.exists(self.models_dir):
            for filename in os.listdir(self.models_dir):
                if filename.endswith('_model.pkl'):
                    try:
                        model_path = os.path.join(self.models_dir, filename)
                        with open(model_path, 'rb') as f:
                            model = pickle.load(f)
                        
                        models.append({
                            'word': model.word,
                            'user_id': model.user_id,
                            'created_at': model.created_at,
                            'accuracy': model.accuracy,
                            'samples': len(model.samples)
                        })
                    except Exception:
                        continue
        
        return models

    def delete_model(self, user_id: str, word: str) -> bool:
        """Delete a trained model."""
        model_filename = f"{user_id}_{word}_model.pkl"
        model_path = os.path.join(self.models_dir, model_filename)
        
        if os.path.exists(model_path):
            try:
                os.remove(model_path)
                print(f"[WakeWordTrainer] Deleted model for '{word}'")
                return True
            except Exception as e:
                print(f"[WakeWordTrainer] Failed to delete model: {e}")
        
        return False

    def _save_session(self, session: TrainingSession):
        """Save training session to disk."""
        session_path = os.path.join(self.training_sessions_dir, f"{session.session_id}_session.json")
        
        with open(session_path, 'w') as f:
            json.dump(asdict(session), f, indent=2)

    def load_session(self, session_id: str) -> Optional[TrainingSession]:
        """Load a training session."""
        session_path = os.path.join(self.training_sessions_dir, f"{session_id}_session.json")
        
        if os.path.exists(session_path):
            try:
                with open(session_path, 'r') as f:
                    data = json.load(f)
                return TrainingSession(**data)
            except Exception as e:
                print(f"[WakeWordTrainer] Failed to load session: {e}")
        
        return None

    def get_training_progress(self) -> Optional[Dict[str, Any]]:
        """Get current training session progress."""
        if self.current_session:
            return {
                'session_id': self.current_session.session_id,
                'target_word': self.current_session.target_word,
                'collected_samples': self.current_session.collected_samples,
                'required_samples': self.current_session.required_samples,
                'progress': self.current_session.progress,
                'status': self.current_session.status
            }
        return None

    def cancel_session(self):
        """Cancel the current training session."""
        if self.current_session:
            self.current_session.status = 'failed'
            self.current_session.error_message = 'Cancelled by user'
            self._save_session(self.current_session)
            self.current_session = None
            print("[WakeWordTrainer] Training session cancelled")

    def calibrate_threshold(self, model: WakeWordModel, 
                           negative_samples: List[np.ndarray]) -> float:
        """
        Calibrate detection threshold using negative samples.
        
        Args:
            model: Trained wake word model
            negative_samples: Audio samples without the wake word
            
        Returns:
            Optimized threshold
        """
        if not negative_samples:
            return model.threshold
        
        try:
            # Calculate distances for negative samples
            avg_mfcc = np.mean(model.mfcc_features, axis=0)
            negative_distances = []
            
            for sample in negative_samples:
                mfcc = self._extract_mfcc(sample)
                if mfcc is not None:
                    distance = np.linalg.norm(mfcc - avg_mfcc)
                    negative_distances.append(distance)
            
            if not negative_distances:
                return model.threshold
            
            # Set threshold to be above most negative samples
            negative_threshold = np.percentile(negative_distances, 95)
            
            # Combine with original threshold
            new_threshold = max(model.threshold, negative_threshold * 1.2)
            
            print(f"[WakeWordTrainer] Threshold calibrated: {model.threshold:.4f} -> {new_threshold:.4f}")
            
            return new_threshold
            
        except Exception as e:
            print(f"[WakeWordTrainer] Threshold calibration failed: {e}")
            return model.threshold


class WakeWordDetector:
    """Real-time wake word detector using trained models."""
    
    def __init__(self, model: WakeWordModel):
        self.model = model
        self.trainer = WakeWordTrainer()
        self.sample_rate = 16000
        self.chunk_duration = 2.0
        self.is_running = False
        self.detection_callback = None
        
    def start_detection(self, callback):
        """Start real-time wake word detection."""
        self.detection_callback = callback
        self.is_running = True
        
        if not self.trainer.pyaudio_available:
            print("[WakeWordDetector] PyAudio not available")
            return
        
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            print(f"[WakeWordDetector] Listening for '{self.model.word}'...")
            
            while self.is_running:
                try:
                    # Record audio chunk
                    frames = []
                    for _ in range(0, int(self.sample_rate / 1024 * self.chunk_duration)):
                        data = stream.read(1024)
                        frames.append(data)
                    
                    # Convert to numpy array
                    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    
                    # Detect wake word
                    detected, confidence = self.trainer.detect_wake_word(audio_data, self.model)
                    
                    if detected and confidence > 0.5:
                        print(f"[WakeWordDetector] Wake word detected! Confidence: {confidence:.2f}")
                        if self.detection_callback:
                            self.detection_callback(confidence)
                
                except Exception as e:
                    print(f"[WakeWordDetector] Detection error: {e}")
                    continue
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            print(f"[WakeWordDetector] Failed to start detection: {e}")

    def stop_detection(self):
        """Stop wake word detection."""
        self.is_running = False
        print("[WakeWordDetector] Detection stopped")
