"""
Music Service Controls
Provides integration with music services (Spotify, Apple Music).
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class MusicService(Enum):
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    YOUTUBE_MUSIC = "youtube_music"
    AMAZON_MUSIC = "amazon_music"


class PlaybackState(Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    BUFFERING = "buffering"


@dataclass
class MusicConfig:
    config_id: str
    service: MusicService
    api_key: str
    access_token: Optional[str]
    refresh_token: Optional[str]
    token_expires_at: Optional[str]
    user_id: str
    created_at: str
    updated_at: str


@dataclass
class Track:
    track_id: str
    name: str
    artist: str
    album: str
    duration_ms: int
    uri: str
    is_playable: bool
    added_at: str


@dataclass
class Playlist:
    playlist_id: str
    name: str
    description: str
    track_count: int
    uri: str
    is_public: bool
    created_at: str


@dataclass
class PlaybackInfo:
    playback_id: str
    config_id: str
    state: PlaybackState
    current_track: Optional[Track]
    volume_percent: int
    is_shuffle: bool
    is_repeat: bool
    position_ms: int
    updated_at: str


class MusicServiceManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.integrations_dir = os.path.join(self.base_dir, "data", "integrations")
        self.music_file = os.path.join(self.integrations_dir, "music_configs.json")
        self.playback_file = os.path.join(self.integrations_dir, "playback_info.json")
        
        os.makedirs(self.integrations_dir, exist_ok=True)
        
        # Load data
        self.configs = self._load_configs()
        self.playback_info = self._load_playback_info()

    def _load_configs(self) -> Dict[str, MusicConfig]:
        """Load music service configurations from disk."""
        if os.path.exists(self.music_file):
            try:
                with open(self.music_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {config_id: MusicConfig(**config) for config_id, config in data.items()}
            except Exception:
                pass
        return {}

    def _save_configs(self):
        """Save music service configurations to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {config_id: asdict(config) for config_id, config in self.configs.items()}
            with open(self.music_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[MusicService] Failed to save configs: {e}")

    def _load_playback_info(self) -> Dict[str, PlaybackInfo]:
        """Load playback information from disk."""
        if os.path.exists(self.playback_file):
            try:
                with open(self.playback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {playback_id: PlaybackInfo(**info) for play_id, info in data.items()}
            except Exception:
                pass
        return {}

    def _save_playback_info(self):
        """Save playback information to disk."""
        try:
            data = {playback_id: asdict(info) for play_id, info in self.playback_info.items()}
            with open(self.playback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[MusicService] Failed to save playback info: {e}")

    def create_config(self, service: MusicService, api_key: str, user_id: str,
                     access_token: str = None, refresh_token: str = None) -> MusicConfig:
        """
        Create music service configuration.
        
        Args:
            service: Music service
            api_key: API key
            user_id: User ID
            access_token: Access token
            refresh_token: Refresh token
            
        Returns:
            MusicConfig
        """
        config_id = f"music_{service.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = MusicConfig(
            config_id=config_id,
            service=service,
            api_key=api_key,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=None,
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.configs[config_id] = config
        self._save_configs()
        
        return config

    def update_tokens(self, config_id: str, access_token: str, refresh_token: str,
                    expires_in: int) -> bool:
        """Update OAuth tokens."""
        if config_id not in self.configs:
            return False
        
        expires_at = datetime.fromtimestamp(datetime.now().timestamp() + expires_in).isoformat()
        
        self.configs[config_id].access_token = access_token
        self.configs[config_id].refresh_token = refresh_token
        self.configs[config_id].token_expires_at = expires_at
        self.configs[config_id].updated_at = datetime.now().isoformat()
        
        self._save_configs()
        return True

    def play_track(self, config_id: str, track_uri: str) -> Tuple[bool, str]:
        """
        Play a specific track.
        
        Args:
            config_id: Configuration ID
            track_uri: Track URI
            
        Returns:
            (success, message)
        """
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        # In production, this would call the music service API
        # Spotify: use spotipy
        # Apple Music: use pyapple-music
        
        # Update playback info
        playback_id = f"playback_{config_id}"
        playback_info = PlaybackInfo(
            playback_id=playback_id,
            config_id=config_id,
            state=PlaybackState.PLAYING,
            current_track=None,
            volume_percent=70,
            is_shuffle=False,
            is_repeat=False,
            position_ms=0,
            updated_at=datetime.now().isoformat()
        )
        
        self.playback_info[playback_id] = playback_info
        self._save_playback_info()
        
        return True, f"Playing track on {self.configs[config_id].service.value}"

    def pause_playback(self, config_id: str) -> Tuple[bool, str]:
        """Pause playback."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        playback_id = f"playback_{config_id}"
        if playback_id in self.playback_info:
            self.playback_info[playback_id].state = PlaybackState.PAUSED
            self.playback_info[playback_id].updated_at = datetime.now().isoformat()
            self._save_playback_info()
        
        return True, "Playback paused"

    def resume_playback(self, config_id: str) -> Tuple[bool, str]:
        """Resume playback."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        playback_id = f"playback_{config_id}"
        if playback_id in self.playback_info:
            self.playback_info[playback_id].state = PlaybackState.PLAYING
            self.playback_info[playback_id].updated_at = datetime.now().isoformat()
            self._save_playback_info()
        
        return True, "Playback resumed"

    def skip_to_next(self, config_id: str) -> Tuple[bool, str]:
        """Skip to next track."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        # In production, this would call the music service API
        return True, "Skipped to next track"

    def skip_to_previous(self, config_id: str) -> Tuple[bool, str]:
        """Skip to previous track."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        # In production, this would call the music service API
        return True, "Skipped to previous track"

    def set_volume(self, config_id: str, volume_percent: int) -> Tuple[bool, str]:
        """
        Set playback volume.
        
        Args:
            config_id: Configuration ID
            volume_percent: Volume (0-100)
            
        Returns:
            (success, message)
        """
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        volume = max(0, min(100, volume_percent))
        
        playback_id = f"playback_{config_id}"
        if playback_id in self.playback_info:
            self.playback_info[playback_id].volume_percent = volume
            self.playback_info[playback_id].updated_at = datetime.now().isoformat()
            self._save_playback_info()
        
        # In production, this would call the music service API
        return True, f"Volume set to {volume}%"

    def toggle_shuffle(self, config_id: str) -> Tuple[bool, str]:
        """Toggle shuffle mode."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        playback_id = f"playback_{config_id}"
        if playback_id in self.playback_info:
            self.playback_info[playback_id].is_shuffle = not self.playback_info[playback_id].is_shuffle
            self.playback_info[playback_id].updated_at = datetime.now().isoformat()
            self._save_playback_info()
        
        # In production, this would call the music service API
        return True, f"Shuffle {'enabled' if self.playback_info[playback_id].is_shuffle else 'disabled'}"

    def toggle_repeat(self, config_id: str) -> Tuple[bool, str]:
        """Toggle repeat mode."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        playback_id = f"playback_{config_id}"
        if playback_id in self.playback_info:
            self.playback_info[playback_id].is_repeat = not self.playback_info[playback_id].is_repeat
            self.playback_info[playback_id].updated_at = datetime.now().isoformat()
            self._save_playback_info()
        
        # In production, this would call the music service API
        return True, f"Repeat {'enabled' if self.playback_info[playback_id].is_repeat else 'disabled'}"

    def search_track(self, config_id: str, query: str) -> List[Track]:
        """
        Search for a track.
        
        Args:
            config_id: Configuration ID
            query: Search query
            
        Returns:
            List of tracks
        """
        if config_id not in self.configs:
            return []
        
        # In production, this would call the music service API
        # For now, return empty list
        return []

    def create_playlist(self, config_id: str, name: str, description: str = "",
                       is_public: bool = False) -> Playlist:
        """
        Create a playlist.
        
        Args:
            config_id: Configuration ID
            name: Playlist name
            description: Playlist description
            is_public: Whether playlist is public
            
        Returns:
            Playlist
        """
        if config_id not in self.configs:
            raise ValueError("Configuration not found")
        
        playlist_id = f"playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        playlist = Playlist(
            playlist_id=playlist_id,
            name=name,
            description=description,
            track_count=0,
            uri=f"{self.configs[config_id].service.value}:playlist:{playlist_id}",
            is_public=is_public,
            created_at=datetime.now().isoformat()
        )
        
        # In production, this would call the music service API
        
        return playlist

    def add_to_playlist(self, config_id: str, playlist_id: str, track_uri: str) -> Tuple[bool, str]:
        """Add a track to a playlist."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        # In production, this would call the music service API
        return True, f"Track added to playlist {playlist_id}"

    def get_playback_info(self, config_id: str) -> Optional[PlaybackInfo]:
        """Get current playback information."""
        playback_id = f"playback_{config_id}"
        return self.playback_info.get(playback_id)

    def get_config(self, config_id: str) -> Optional[MusicConfig]:
        """Get configuration by ID."""
        return self.configs.get(config_id)

    def delete_config(self, config_id: str) -> bool:
        """Delete a configuration."""
        if config_id not in self.configs:
            return False
        
        del self.configs[config_id]
        self._save_configs()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get music service statistics."""
        total_configs = len(self.configs)
        total_playback = len(self.playback_info)
        
        # Count by service
        by_service = {}
        for config in self.configs.values():
            service = config.service.value
            by_service[service] = by_service.get(service, 0) + 1
        
        # Count by playback state
        by_state = {}
        for playback in self.playback_info.values():
            state = playback.state.value
            by_state[state] = by_state.get(state, 0) + 1
        
        return {
            'total_configs': total_configs,
            'total_playback_sessions': total_playback,
            'by_service': by_service,
            'by_playback_state': by_state
        }

    def export_config(self, config_id: str, export_path: str) -> Tuple[bool, str]:
        """Export configuration (without secrets)."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        config = self.configs[config_id]
        
        # Create safe export without secrets
        safe_config = {
            'config_id': config.config_id,
            'service': config.service.value,
            'user_id': config.user_id,
            'created_at': config.created_at,
            'updated_at': config.updated_at
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(safe_config, f, indent=2)
            return True, f"Config exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
