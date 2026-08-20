"""
Desktop Application (Electron/Tauri)
Provides desktop application foundation for cross-platform desktop support.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class DesktopPlatform(Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class AppStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class DesktopAppConfig:
    config_id: str
    app_name: str
    version: str
    platform: DesktopPlatform
    auto_start: bool
    minimize_to_tray: bool
    start_minimized: bool
    hotkeys: Dict[str, str]
    theme: str  # 'light', 'dark', 'auto'
    language: str
    created_at: str
    updated_at: str


class DesktopAppManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.desktop_dir = os.path.join(self.base_dir, "desktop")
        self.config_file = os.path.join(self.desktop_dir, "app_config.json")
        self.settings_file = os.path.join(self.desktop_dir, "user_settings.json")
        
        os.makedirs(self.desktop_dir, exist_ok=True)
        
        # Load data
        self.config = self._load_config()
        self.settings = self._load_settings()

    def _load_config(self) -> Dict[str, DesktopAppConfig]:
        """Load app configuration from disk."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {config_id: DesktopAppConfig(**config) for config_id, config in data.items()}
            except Exception:
                pass
        return {}

    def _save_config(self):
        """Save configuration to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {config_id: asdict(config) for config_id, config in self.config.items()}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[DesktopApp] Failed to save config: {e}")

    def _load_settings(self) -> Dict:
        """Load user settings from disk."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_settings(self):
        """Save user settings to disk."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"[DesktopApp] Failed to save settings: {e}")

    def create_config(self, app_name: str, version: str = "1.0.0",
                     platform: DesktopPlatform = DesktopPlatform.WINDOWS) -> DesktopAppConfig:
        """
        Create desktop app configuration.
        
        Args:
            app_name: Application name
            version: Application version
            platform: Target platform
            
        Returns:
            DesktopAppConfig
        """
        config_id = f"config_{platform.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = DesktopAppConfig(
            config_id=config_id,
            app_name=app_name,
            version=version,
            platform=platform,
            auto_start=False,
            minimize_to_tray=True,
            start_minimized=False,
            hotkeys={
                'wake_word': 'Ctrl+Shift+J',
                'toggle_listen': 'Ctrl+Shift+Space',
                'quit': 'Ctrl+Shift+Q'
            },
            theme='auto',
            language='en',
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.config[config_id] = config
        self._save_config()
        
        return config

    def update_hotkey(self, config_id: str, action: str, hotkey: str) -> bool:
        """Update a hotkey in configuration."""
        if config_id not in self.config:
            return False
        
        self.config[config_id].hotkeys[action] = hotkey
        self.config[config_id].updated_at = datetime.now().isoformat()
        self._save_config()
        
        return True

    def set_auto_start(self, config_id: str, auto_start: bool) -> bool:
        """Set auto-start preference."""
        if config_id not in self.config:
            return False
        
        self.config[config_id].auto_start = auto_start
        self.config[config_id].updated_at = datetime.now().isoformat()
        self._save_config()
        
        return True

    def set_theme(self, config_id: str, theme: str) -> bool:
        """Set app theme."""
        if config_id not in self.config:
            return False
        
        self.config[config_id].theme = theme
        self.config[config_id].updated_at = datetime.now().isoformat()
        self._save_config()
        
        return True

    def get_config(self, config_id: str) -> Optional[DesktopAppConfig]:
        """Get app configuration by ID."""
        return self.config.get(config_id)

    def get_platform_config(self, platform: DesktopPlatform) -> Optional[DesktopAppConfig]:
        """Get configuration for a specific platform."""
        for config in self.config.values():
            if config.platform == platform:
                return config
        return None

    def generate_package_json(self, config_id: str) -> Optional[Dict]:
        """Generate package.json for Electron app."""
        config = self.get_config(config_id)
        if not config:
            return None
        
        package_json = {
            "name": config.app_name.lower().replace(' ', '-'),
            "version": config.version,
            "description": f"{config.app_name} Desktop Application",
            "main": "main.js",
            "scripts": {
                "start": "electron .",
                "build": "electron-builder",
                "dev": "electron . --dev"
            },
            "author": "JARVIS AI",
            "license": "MIT",
            "devDependencies": {
                "electron": "^latest",
                "electron-builder": "^latest"
            },
            "build": {
                "appId": f"com.jarvis.{config.app_name.lower().replace(' ', '')}",
                "productName": config.app_name,
                "directories": {
                    "output": "dist"
                },
                "win": {
                    "target": ["nsis"]
                },
                "mac": {
                    "target": ["dmg"]
                },
                "linux": {
                    "target": ["AppImage"]
                }
            }
        }
        
        return package_json

    def generate_main_js(self, config_id: str) -> str:
        """Generate main.js for Electron app."""
        config = self.get_config(config_id)
        if not config:
            return ""
        
        main_js = f"""
const {{ app, BrowserWindow, globalShortcut }} = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {{
    mainWindow = new BrowserWindow({{
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {{
            nodeIntegration: true,
            contextIsolation: false
        }},
        icon: path.join(__dirname, 'assets/icon.png'),
        show: {str(not config.start_minimized).lower()}
    }});

    mainWindow.loadFile('index.html');

    mainWindow.on('minimize', function (event) {{
        event.preventDefault();
        mainWindow.hide();
    }});

    mainWindow.on('close', function (event) {{
        if (!app.isQuiting) {{
            event.preventDefault();
            mainWindow.hide();
        }}
    }});
}}

app.whenReady().then(() => {{
    createWindow();

    // Register hotkeys
    globalShortcut.register('{config.hotkeys.get('toggle_listen', 'Ctrl+Shift+Space')}', () => {{
        mainWindow.webContents.send('toggle-listen');
    }});

    globalShortcut.register('{config.hotkeys.get('wake_word', 'Ctrl+Shift+J')}', () => {{
        mainWindow.webContents.send('activate-wake-word');
    }});

    app.on('activate', () => {{
        if (BrowserWindow.getAllWindows().length === 0) {{
            createWindow();
        }}
    }});
}});

app.on('window-all-closed', () => {{
    if (process.platform !== 'darwin') {{
        app.quit();
    }}
}});

app.on('before-quit', () => {{
    app.isQuiting = true;
}});
"""
        
        return main_js

    def generate_tauri_config(self, config_id: str) -> Optional[Dict]:
        """Generate tauri.conf.json for Tauri app."""
        config = self.get_config(config_id)
        if not config:
            return None
        
        tauri_config = {
            "build": {
                "distDir": "../dist",
                "devPath": "http://localhost:5173"
            },
            "tauri": {
                "bundle": {
                    "identifier": f"com.jarvis.{config.app_name.lower().replace(' ', '')}",
                    "targets": ["all"],
                    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/128x128@2x.png", "icons/icon.icns"]
                },
                "allowlist": {
                    "all": true,
                    "shell": {
                        "all": true,
                        "open": true
                    },
                    "globalShortcut": {
                        "all": true
                    }
                }
            }
        }
        
        return tauri_config

    def set_user_setting(self, key: str, value: Any) -> bool:
        """Set a user setting."""
        self.settings[key] = value
        self._save_settings()
        return True

    def get_user_setting(self, key: str, default: Any = None) -> Any:
        """Get a user setting."""
        return self.settings.get(key, default)

    def delete_config(self, config_id: str) -> bool:
        """Delete a configuration."""
        if config_id not in self.config:
            return False
        
        del self.config[config_id]
        self._save_config()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get desktop app statistics."""
        total_configs = len(self.config)
        
        # Count by platform
        by_platform = {}
        for config in self.config.values():
            platform = config.platform.value
            by_platform[platform] = by_platform.get(platform, 0) + 1
        
        return {
            'total_configs': total_configs,
            'by_platform': by_platform,
            'total_settings': len(self.settings)
        }

    def export_config(self, config_id: str, export_path: str) -> Tuple[bool, str]:
        """Export configuration to file."""
        if config_id not in self.config:
            return False, "Config not found"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config[config_id]), f, indent=2)
            return True, f"Config exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
