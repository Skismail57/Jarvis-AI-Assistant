"""
Accessibility Improvements
Provides screen reader optimization, high contrast modes, and accessibility features.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ContrastMode(Enum):
    NORMAL = "normal"
    HIGH = "high"
    INVERTED = "inverted"
    GRAYSCALE = "grayscale"


class FontSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class ScreenReaderMode(Enum):
    OFF = "off"
    BASIC = "basic"
    FULL = "full"


@dataclass
class AccessibilityProfile:
    profile_id: str
    user_id: str
    name: str
    contrast_mode: ContrastMode
    font_size: FontSize
    screen_reader_mode: ScreenReaderMode
    reduce_motion: bool
    high_focus_visibility: bool
    keyboard_navigation: bool
    voice_navigation: bool
    custom_settings: Dict[str, Any]
    created_at: str
    updated_at: str


class AccessibilityManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.ui_dir = os.path.join(self.base_dir, "data", "ui")
        self.profiles_file = os.path.join(self.ui_dir, "accessibility_profiles.json")
        
        os.makedirs(self.ui_dir, exist_ok=True)
        
        # Load profiles
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> Dict[str, AccessibilityProfile]:
        """Load accessibility profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {profile_id: AccessibilityProfile(**profile) for profile_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save profiles to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {profile_id: asdict(profile) for profile_id, profile in self.profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[AccessibilityManager] Failed to save profiles: {e}")

    def create_profile(self, user_id: str, name: str, contrast_mode: ContrastMode = ContrastMode.NORMAL,
                     font_size: FontSize = FontSize.MEDIUM,
                     screen_reader_mode: ScreenReaderMode = ScreenReaderMode.OFF) -> AccessibilityProfile:
        """
        Create an accessibility profile.
        
        Args:
            user_id: User ID
            name: Profile name
            contrast_mode: Contrast mode
            font_size: Font size
            screen_reader_mode: Screen reader mode
            
        Returns:
            AccessibilityProfile
        """
        profile_id = f"accessibility_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        profile = AccessibilityProfile(
            profile_id=profile_id,
            user_id=user_id,
            name=name,
            contrast_mode=contrast_mode,
            font_size=font_size,
            screen_reader_mode=screen_reader_mode,
            reduce_motion=False,
            high_focus_visibility=False,
            keyboard_navigation=True,
            voice_navigation=False,
            custom_settings={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.profiles[profile_id] = profile
        self._save_profiles()
        
        return profile

    def set_contrast_mode(self, profile_id: str, contrast_mode: ContrastMode) -> bool:
        """Set contrast mode for a profile."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].contrast_mode = contrast_mode
        self.profiles[profile_id].updated_at = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def set_font_size(self, profile_id: str, font_size: FontSize) -> bool:
        """Set font size for a profile."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].font_size = font_size
        self.profiles[profile_id].updated_at = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def set_screen_reader_mode(self, profile_id: str, screen_reader_mode: ScreenReaderMode) -> bool:
        """Set screen reader mode for a profile."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].screen_reader_mode = screen_reader_mode
        self.profiles[profile_id].updated_at = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def set_reduce_motion(self, profile_id: str, reduce_motion: bool) -> bool:
        """Set reduce motion preference."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].reduce_motion = reduce_motion
        self.profiles[profile_id].updated_at = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def set_high_focus_visibility(self, profile_id: str, high_focus_visibility: bool) -> bool:
        """Set high focus visibility preference."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].high_focus_visibility = high_focus_visibility
        self.profiles[profile_id].updated_at = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def set_voice_navigation(self, profile_id: str, voice_navigation: bool) -> bool:
        """Set voice navigation preference."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].voice_navigation = voice_navigation
        self.profiles[profile_id].updated_at = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def set_custom_setting(self, profile_id: str, key: str, value: Any) -> bool:
        """Set a custom accessibility setting."""
        if profile_id not in self.profiles:
            return False
        
        self.profiles[profile_id].custom_settings[key] = value
        self.profiles[profile_id].updated_at = datetime.now().isoformat()
        self._save_profiles()
        
        return True

    def get_profile(self, profile_id: str) -> Optional[AccessibilityProfile]:
        """Get an accessibility profile by ID."""
        return self.profiles.get(profile_id)

    def get_user_profile(self, user_id: str) -> Optional[AccessibilityProfile]:
        """Get accessibility profile for a user."""
        for profile in self.profiles.values():
            if profile.user_id == user_id:
                return profile
        return None

    def get_all_profiles(self) -> List[AccessibilityProfile]:
        """Get all accessibility profiles."""
        return list(self.profiles.values())

    def delete_profile(self, profile_id: str) -> bool:
        """Delete an accessibility profile."""
        if profile_id not in self.profiles:
            return False
        
        del self.profiles[profile_id]
        self._save_profiles()
        
        return True

    def generate_screen_reader_text(self, content: str, profile_id: str = None) -> str:
        """
        Generate screen reader friendly text.
        
        Args:
            content: Original content
            profile_id: Optional profile ID for customization
            
        Returns:
            Screen reader optimized text
        """
        # Get profile if provided
        profile = None
        if profile_id:
            profile = self.get_profile(profile_id)
        
        # Basic screen reader optimizations
        optimized = content
        
        # Add aria-labels for complex elements
        optimized = optimized.replace('<button>', '<button aria-label="button">')
        
        # Add proper heading structure
        optimized = optimized.replace('# ', '<h1>')
        optimized = optimized.replace('## ', '<h2>')
        
        # Add alt text placeholders
        optimized = optimized.replace('![](', '![](alt="image")')
        
        # Add pause indicators for long content
        if len(optimized) > 500:
            optimized = optimized[:250] + ' <break time="500ms"/> ' + optimized[250:]
        
        return optimized

    def get_contrast_stylesheet(self, contrast_mode: ContrastMode) -> str:
        """
        Generate CSS for contrast mode.
        
        Args:
            contrast_mode: Contrast mode
            
        Returns:
            CSS stylesheet
        """
        styles = {
            ContrastMode.NORMAL: """
                :root {
                    --bg-color: #ffffff;
                    --text-color: #000000;
                    --accent-color: #007bff;
                }
            """,
            ContrastMode.HIGH: """
                :root {
                    --bg-color: #000000;
                    --text-color: #ffffff;
                    --accent-color: #ffff00;
                }
                * {
                    color: var(--text-color) !important;
                    background-color: var(--bg-color) !important;
                }
            """,
            ContrastMode.INVERTED: """
                :root {
                    filter: invert(1);
                }
            """,
            ContrastMode.GRAYSCALE: """
                :root {
                    filter: grayscale(100%);
                }
            """
        }
        
        return styles.get(contrast_mode, styles[ContrastMode.NORMAL])

    def get_font_size_stylesheet(self, font_size: FontSize) -> str:
        """
        Generate CSS for font size.
        
        Args:
            font_size: Font size
            
        Returns:
            CSS stylesheet
        """
        sizes = {
            FontSize.SMALL: "html { font-size: 14px; }",
            FontSize.MEDIUM: "html { font-size: 16px; }",
            FontSize.LARGE: "html { font-size: 20px; }",
            FontSize.EXTRA_LARGE: "html { font-size: 24px; }"
        }
        
        return sizes.get(font_size, sizes[FontSize.MEDIUM])

    def get_accessibility_stylesheet(self, profile_id: str) -> str:
        """
        Generate complete accessibility stylesheet for a profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Complete CSS stylesheet
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return ""
        
        css = ""
        
        # Add contrast styles
        css += self.get_contrast_stylesheet(profile.contrast_mode)
        
        # Add font size styles
        css += self.get_font_size_stylesheet(profile.font_size)
        
        # Add reduce motion styles
        if profile.reduce_motion:
            css += """
                *, *::before, *::after {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            """
        
        # Add high focus visibility styles
        if profile.high_focus_visibility:
            css += """
                *:focus {
                    outline: 3px solid #ff0000 !important;
                    outline-offset: 2px !important;
                }
            """
        
        return css

    def get_statistics(self) -> Dict[str, Any]:
        """Get accessibility statistics."""
        total_profiles = len(self.profiles)
        
        # Count by contrast mode
        by_contrast = {}
        for profile in self.profiles.values():
            contrast = profile.contrast_mode.value
            by_contrast[contrast] = by_contrast.get(contrast, 0) + 1
        
        # Count by screen reader mode
        by_screen_reader = {}
        for profile in self.profiles.values():
            sr_mode = profile.screen_reader_mode.value
            by_screen_reader[sr_mode] = by_screen_reader.get(sr_mode, 0) + 1
        
        # Count features enabled
        reduce_motion_count = sum(1 for p in self.profiles.values() if p.reduce_motion)
        high_focus_count = sum(1 for p in self.profiles.values() if p.high_focus_visibility)
        voice_nav_count = sum(1 for p in self.profiles.values() if p.voice_navigation)
        
        return {
            'total_profiles': total_profiles,
            'by_contrast_mode': by_contrast,
            'by_screen_reader_mode': by_screen_reader,
            'reduce_motion_enabled': reduce_motion_count,
            'high_focus_visibility_enabled': high_focus_count,
            'voice_navigation_enabled': voice_nav_count
        }

    def export_profile(self, profile_id: str, export_path: str) -> Tuple[bool, str]:
        """Export accessibility profile."""
        if profile_id not in self.profiles:
            return False, "Profile not found"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.profiles[profile_id]), f, indent=2)
            return True, f"Profile exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
