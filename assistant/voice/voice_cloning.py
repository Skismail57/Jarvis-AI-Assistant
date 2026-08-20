"""
Voice Cloning System
Creates personalized voice models for customized TTS responses.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import numpy as np


class VoiceModelStatus(Enum):
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"
    UPDATING = "updating"


@dataclass
class VoiceSample:
    sample_id: str
    voice_id: str
    audio_path: str
    duration: float
    text: str
    created_at: str


@dataclass
class VoiceModel:
    model_id: str
    voice_id: str
    name: str
    status: VoiceModelStatus
    sample_count: int
    training_progress: float
    model_path: str
    created_at: str
    last_updated: str
    is_default: bool = False


class VoiceCloner:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cloning_dir = os.path.join(self.base_dir, "data", "voice_cloning")
        self.models_file = os.path.join(self.cloning_dir, "voice_models.json")
        self.samples_file = os.path.join(self.cloning_dir, "voice_samples.json")
        self.audio_dir = os.path.join(self.cloning_dir, "audio_samples")
        
        os.makedirs(self.cloning_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Load data
        self.voice_models = self._load_models()
        self.voice_samples = self._load_samples()
        
        # Training parameters
        self.min_samples_for_training = 10
        self.max_samples_per_voice = 100

    def _load_models(self) -> Dict[str, VoiceModel]:
        """Load voice models from disk."""
        if os.path.exists(self.models_file):
            try:
                with open(self.models_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {model_id: VoiceModel(**model) for model_id, model in data.items()}
            except Exception:
                pass
        return {}

    def _save_models(self):
        """Save voice models to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {model_id: asdict(model) for model_id, model in self.voice_models.items()}
            with open(self.models_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[VoiceCloner] Failed to save models: {e}")

    def _load_samples(self) -> Dict[str, VoiceSample]:
        """Load voice samples from disk."""
        if os.path.exists(self.samples_file):
            try:
                with open(self.samples_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {sample_id:样本 for sample_id, 样本 in data.items()}
            except Exception:
                pass
        return {}

    def _save_samples(self):
        """Save voice samples to disk."""
        try:
            data = {sample_id: asdict(sample) for sample_id, sample in self.voice_samples.items()}
            with open(self.samples_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[VoiceCloner] Failed to save samples: {e}")

    def register_voice(self, name: str) -> str:
        """
        Register a new voice for cloning.
        
        Args:
            name: Name for the voice
            
        Returns:
            Voice ID
        """
        voice_id = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        model = VoiceModel(
            model_id=voice_id,
            voice_id=voice_id,
            name=name,
            status=VoiceModelStatus.TRAINING,
            sample_count=0,
            training_progress=0.0,
            model_path="",
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            is_default=False
        )
        
        self.voice_models[voice_id] = model
        self._save_models()
        
        return voice_id

    def add_voice_sample(self, voice_id: str, audio_data: np.ndarray, 
                        text: str, sample_rate: int = 16000) -> VoiceSample:
        """
        Add a voice sample for training.
        
        Args:
            voice_id: Voice ID
            audio_data: Audio data
            text: Text spoken in audio
            sample_rate: Sample rate
            
        Returns:
            VoiceSample
        """
        if voice_id not in self.voice_models:
            raise ValueError(f"Voice not found: {voice_id}")
        
        # Save audio file
        sample_id = f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        audio_path = os.path.join(self.audio_dir, f"{sample_id}.wav")
        
        try:
            import soundfile as sf
            sf.write(audio_path, audio_data, sample_rate)
        except ImportError:
            # Fallback: save as numpy
            np.save(audio_path.replace('.wav', '.npy'), audio_data)
            audio_path = audio_path.replace('.wav', '.npy')
        
        duration = len(audio_data) / sample_rate
        
        sample = VoiceSample(
            sample_id=sample_id,
            voice_id=voice_id,
            audio_path=audio_path,
            duration=duration,
            text=text,
            created_at=datetime.now().isoformat()
        )
        
        self.voice_samples[sample_id] = sample
        
        # Update model
        model = self.voice_models[voice_id]
        model.sample_count += 1
        model.last_updated = datetime.now().isoformat()
        
        self._save_samples()
        self._save_models()
        
        return sample

    def train_voice_model(self, voice_id: str) -> Tuple[bool, str]:
        """
        Train a voice model from collected samples.
        
        Args:
            voice_id: Voice ID
            
        Returns:
            (success, message)
        """
        if voice_id not in self.voice_models:
            return False, "Voice not found"
        
        model = self.voice_models[voice_id]
        
        # Check if enough samples
        voice_samples = [s for s in self.voice_samples.values() if s.voice_id == voice_id]
        if len(voice_samples) < self.min_samples_for_training:
            return False, f"Need at least {self.min_samples_for_training} samples, have {len(voice_samples)}"
        
        # Update status
        model.status = VoiceModelStatus.TRAINING
        model.training_progress = 0.0
        self._save_models()
        
        try:
            # Simulate training process
            # In production, use actual voice cloning model (e.g., Tacotron, YourTTS, etc.)
            for i in range(10):
                model.training_progress = (i + 1) * 10
                self._save_models()
            
            # Mark as ready
            model.status = VoiceModelStatus.READY
            model.model_path = os.path.join(self.cloning_dir, f"model_{voice_id}.pt")
            model.last_updated = datetime.now().isoformat()
            self._save_models()
            
            return True, "Voice model trained successfully"
            
        except Exception as e:
            model.status = VoiceModelStatus.FAILED
            self._save_models()
            return False, f"Training failed: {str(e)}"

    def synthesize_with_voice(self, voice_id: str, text: str) -> Optional[np.ndarray]:
        """
        Synthesize speech using a cloned voice.
        
        Args:
            voice_id: Voice ID
            text: Text to synthesize
            
        Returns:
            Audio data
        """
        if voice_id not in self.voice_models:
            return None
        
        model = self.voice_models[voice_id]
        
        if model.status != VoiceModelStatus.READY:
            return None
        
        try:
            # In production, use actual TTS with voice cloning
            # For now, return placeholder
            return self._placeholder_synthesis(text)
            
        except Exception as e:
            print(f"[VoiceCloner] Synthesis failed: {e}")
            return None

    def _placeholder_synthesis(self, text: str) -> np.ndarray:
        """Placeholder synthesis for testing."""
        # Generate simple sine wave audio
        duration = len(text) * 0.1  # Approximate duration
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        
        return audio

    def get_voice_model(self, voice_id: str) -> Optional[VoiceModel]:
        """Get voice model by ID."""
        return self.voice_models.get(voice_id)

    def get_voice_samples(self, voice_id: str) -> List[VoiceSample]:
        """Get all samples for a voice."""
        return [s for s in self.voice_samples.values() if s.voice_id == voice_id]

    def set_default_voice(self, voice_id: str) -> bool:
        """Set a voice as the default."""
        if voice_id not in self.voice_models:
            return False
        
        # Remove default from others
        for model in self.voice_models.values():
            model.is_default = False
        
        self.voice_models[voice_id].is_default = True
        self._save_models()
        
        return True

    def get_default_voice(self) -> Optional[VoiceModel]:
        """Get the default voice model."""
        for model in self.voice_models.values():
            if model.is_default:
                return model
        return None

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice model and its samples."""
        if voice_id not in self.voice_models:
            return False
        
        # Delete samples
        sample_ids = [s.sample_id for s in self.voice_samples.values() if s.voice_id == voice_id]
        for sample_id in sample_ids:
            sample = self.voice_samples[sample_id]
            try:
                if os.path.exists(sample.audio_path):
                    os.remove(sample.audio_path)
            except Exception:
                pass
            del self.voice_samples[sample_id]
        
        # Delete model
        try:
            if os.path.exists(self.voice_models[voice_id].model_path):
                os.remove(self.voice_models[voice_id].model_path)
        except Exception:
            pass
        
        del self.voice_models[voice_id]
        
        self._save_samples()
        self._save_models()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get voice cloning statistics."""
        total_models = len(self.voice_models)
        total_samples = len(self.voice_samples)
        
        # Count by status
        by_status = {}
        for model in self.voice_models.values():
            status = model.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_models': total_models,
            'total_samples': total_samples,
            'by_status': by_status,
            'ready_models': by_status.get('ready', 0)
        }

    def export_voice_model(self, voice_id: str, export_path: str) -> Tuple[bool, str]:
        """Export a voice model."""
        if voice_id not in self.voice_models:
            return False, "Voice not found"
        
        model = self.voice_models[voice_id]
        
        if model.status != VoiceModelStatus.READY:
            return False, "Voice model is not ready"
        
        try:
            # Export model and samples
            export_data = {
                'model': asdict(model),
                'samples': [asdict(s) for s in self.get_voice_samples(voice_id)]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Voice model exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"
