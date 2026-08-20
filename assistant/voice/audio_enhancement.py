"""
Audio Enhancement System
Provides noise cancellation and echo removal for improved audio quality.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import numpy as np


class NoiseType(Enum):
    WHITE_NOISE = "white_noise"
    PINK_NOISE = "pink_noise"
    BACKGROUND = "background"
    ELECTRICAL = "electrical"
    WIND = "wind"


@dataclass
class NoiseProfile:
    profile_id: str
    noise_type: NoiseType
    frequency_profile: List[float]
    amplitude_profile: List[float]
    sample_duration: float
    created_at: str


class AudioEnhancer:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.enhancement_dir = os.path.join(self.base_dir, "data", "audio_enhancement")
        self.profiles_file = os.path.join(self.enhancement_dir, "noise_profiles.json")
        
        os.makedirs(self.enhancement_dir, exist_ok=True)
        
        # Load noise profiles
        self.noise_profiles = self._load_profiles()
        
        # Enhancement settings
        self.noise_reduction_level = 0.7
        self.echo_removal_enabled = True
        self.normalization_enabled = True

    def _load_profiles(self) -> Dict[str, NoiseProfile]:
        """Load noise profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {profile_id: NoiseProfile(**profile) for profile_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save noise profiles to disk."""
        try:
            data = {profile_id: asdict(profile) for profile_id, profile in self.noise_profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AudioEnhancer] Failed to save profiles: {e}")

    def reduce_noise(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Reduce background noise from audio.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate
            
        Returns:
            Cleaned audio data
        """
        try:
            import librosa
            
            # Use spectral subtraction
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise from first 0.5 seconds
            noise_frames = int(0.5 * sample_rate / 512)
            noise_magnitude = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
            
            # Subtract noise
            clean_magnitude = magnitude - (noise_magnitude * self.noise_reduction_level)
            clean_magnitude = np.maximum(clean_magnitude, 0.01 * magnitude)
            
            # Reconstruct
            clean_stft = clean_magnitude * np.exp(1j * phase)
            clean_audio = librosa.istft(clean_stft)
            
            return clean_audio
            
        except ImportError:
            # Fallback: simple moving average filter
            return self._simple_noise_filter(audio_data)

    def _simple_noise_filter(self, audio_data: np.ndarray) -> np.ndarray:
        """Simple noise filter as fallback."""
        # Moving average filter
        window_size = 5
        kernel = np.ones(window_size) / window_size
        filtered = np.convolve(audio_data, kernel, mode='same')
        
        # Mix with original based on reduction level
        mixed = audio_data * (1 - self.noise_reduction_level) + filtered * self.noise_reduction_level
        
        return mixed

    def remove_echo(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Remove echo from audio.
        
        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            
        Returns:
            Echo-reduced audio
        """
        if not self.echo_removal_enabled:
            return audio_data
        
        try:
            import librosa
            
            # Simple echo cancellation using adaptive filter
            delay_samples = int(0.1 * sample_rate)  # 100ms delay
            decay_factor = 0.5
            
            # Create echo template
            echo_template = np.zeros(len(audio_data))
            echo_template[delay_samples:] = audio_data[:-delay_samples] * decay_factor
            
            # Subtract echo
            clean_audio = audio_data - echo_template
            
            return clean_audio
            
        except ImportError:
            # Fallback: simple high-pass filter to reduce echo
            return self._high_pass_filter(audio_data, sample_rate)

    def _high_pass_filter(self, audio_data: np.ndarray, sample_rate: int, cutoff: int = 100) -> np.ndarray:
        """Simple high-pass filter."""
        from scipy import signal
        
        nyquist = sample_rate / 2
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(4, normal_cutoff, btype='high', analog=False)
        
        filtered = signal.filtfilt(b, a, audio_data)
        return filtered

    def normalize_audio(self, audio_data: np.ndarray, target_level: float = 0.8) -> np.ndarray:
        """
        Normalize audio to target level.
        
        Args:
            audio_data: Audio data
            target_level: Target RMS level
            
        Returns:
            Normalized audio
        """
        if not self.normalization_enabled:
            return audio_data
        
        # Calculate current RMS
        current_rms = np.sqrt(np.mean(audio_data ** 2))
        
        if current_rms == 0:
            return audio_data
        
        # Calculate gain
        gain = target_level / current_rms
        
        # Apply gain with clipping
        normalized = audio_data * gain
        normalized = np.clip(normalized, -1.0, 1.0)
        
        return normalized

    def enhance_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Apply full enhancement pipeline.
        
        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            
        Returns:
            Enhanced audio
        """
        # Apply enhancements in sequence
        enhanced = audio_data.copy()
        
        # 1. Noise reduction
        enhanced = self.reduce_noise(enhanced, sample_rate)
        
        # 2. Echo removal
        enhanced = self.remove_echo(enhanced, sample_rate)
        
        # 3. Normalization
        enhanced = self.normalize_audio(enhanced)
        
        return enhanced

    def detect_noise_type(self, audio_data: np.ndarray, sample_rate: int = 16000) -> NoiseType:
        """
        Detect type of noise in audio.
        
        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            
        Returns:
            Detected noise type
        """
        try:
            import librosa
            
            # Analyze frequency spectrum
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            
            # Average magnitude across time
            avg_magnitude = np.mean(magnitude, axis=1)
            
            # Analyze frequency distribution
            freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)
            
            # Check for different noise patterns
            low_freq_energy = np.sum(avg_magnitude[:10])
            mid_freq_energy = np.sum(avg_magnitude[10:50])
            high_freq_energy = np.sum(avg_magnitude[50:])
            
            total_energy = low_freq_energy + mid_freq_energy + high_freq_energy
            
            if total_energy == 0:
                return NoiseType.WHITE_NOISE
            
            low_ratio = low_freq_energy / total_energy
            high_ratio = high_freq_energy / total_energy
            
            if low_ratio > 0.6:
                return NoiseType.WIND
            elif high_ratio > 0.5:
                return NoiseType.ELECTRICAL
            else:
                return NoiseType.BACKGROUND
                
        except ImportError:
            return NoiseType.WHITE_NOISE

    def create_noise_profile(self, audio_data: np.ndarray, noise_type: NoiseType,
                            sample_rate: int = 16000) -> NoiseProfile:
        """
        Create a noise profile from audio sample.
        
        Args:
            audio_data: Audio data containing noise
            noise_type: Type of noise
            sample_rate: Sample rate
            
        Returns:
            NoiseProfile
        """
        try:
            import librosa
            
            # Analyze frequency spectrum
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            
            # Frequency profile (average magnitude per frequency bin)
            frequency_profile = np.mean(magnitude, axis=1).tolist()
            
            # Amplitude profile over time
            amplitude_profile = np.mean(magnitude, axis=0).tolist()
            
            profile_id = f"noise_{noise_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            profile = NoiseProfile(
                profile_id=profile_id,
                noise_type=noise_type,
                frequency_profile=frequency_profile,
                amplitude_profile=amplitude_profile,
                sample_duration=len(audio_data) / sample_rate,
                created_at=datetime.now().isoformat()
            )
            
            self.noise_profiles[profile_id] = profile
            self._save_profiles()
            
            return profile
            
        except ImportError:
            # Fallback: create simple profile
            profile_id = f"noise_{noise_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            profile = NoiseProfile(
                profile_id=profile_id,
                noise_type=noise_type,
                frequency_profile=[],
                amplitude_profile=[],
                sample_duration=len(audio_data) / sample_rate,
                created_at=datetime.now().isoformat()
            )
            
            self.noise_profiles[profile_id] = profile
            self._save_profiles()
            
            return profile

    def set_noise_reduction_level(self, level: float):
        """Set noise reduction level (0.0 to 1.0)."""
        self.noise_reduction_level = max(0.0, min(1.0, level))

    def enable_echo_removal(self, enabled: bool):
        """Enable or disable echo removal."""
        self.echo_removal_enabled = enabled

    def enable_normalization(self, enabled: bool):
        """Enable or disable normalization."""
        self.normalization_enabled = enabled

    def get_statistics(self) -> Dict[str, Any]:
        """Get enhancement statistics."""
        return {
            'noise_profiles': len(self.noise_profiles),
            'noise_reduction_level': self.noise_reduction_level,
            'echo_removal_enabled': self.echo_removal_enabled,
            'normalization_enabled': self.normalization_enabled
        }
