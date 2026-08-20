"""
Browser Extension Manager
Provides browser extension foundation for web integration.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class BrowserType(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"
    SAFARI = "safari"
    BRAVE = "brave"


class ExtensionPermission(Enum):
    TABS = "tabs"
    STORAGE = "storage"
    ACTIVE_TAB = "activeTab"
    SCRIPTING = "scripting"
    NOTIFICATIONS = "notifications"
    CLIPBOARD_READ = "clipboardRead"
    CLIPBOARD_WRITE = "clipboardWrite"


@dataclass
class ExtensionConfig:
    config_id: str
    name: str
    version: str
    description: str
    browsers: List[BrowserType]
    permissions: List[ExtensionPermission]
    host_permissions: List[str]
    content_scripts: List[Dict[str, Any]]
    background_scripts: List[str]
    popup_enabled: bool
    options_page: bool
    created_at: str
    updated_at: str


class BrowserExtensionManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.extension_dir = os.path.join(self.base_dir, "browser_extension")
        self.config_file = os.path.join(self.extension_dir, "extension_config.json")
        self.manifest_file = os.path.join(self.extension_dir, "manifest.json")
        
        os.makedirs(self.extension_dir, exist_ok=True)
        
        # Load data
        self.configs = self._load_configs()

    def _load_configs(self) -> Dict[str, ExtensionConfig]:
        """Load extension configurations from disk."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {config_id: ExtensionConfig(**config) for config_id, config in data.items()}
            except Exception:
                pass
        return {}

    def _save_configs(self):
        """Save extension configurations to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {config_id: asdict(config) for config_id, config in self.configs.items()}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[BrowserExtension] Failed to save configs: {e}")

    def create_config(self, name: str, version: str = "1.0.0",
                     description: str = "JARVIS AI Assistant Browser Extension") -> ExtensionConfig:
        """
        Create browser extension configuration.
        
        Args:
            name: Extension name
            version: Extension version
            description: Extension description
            
        Returns:
            ExtensionConfig
        """
        config_id = f"ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = ExtensionConfig(
            config_id=config_id,
            name=name,
            version=version,
            description=description,
            browsers=[BrowserType.CHROME, BrowserType.FIREFOX, BrowserType.EDGE],
            permissions=[
                ExtensionPermission.STORAGE,
                ExtensionPermission.ACTIVE_TAB,
                ExtensionPermission.SCRIPTING,
                ExtensionPermission.NOTIFICATIONS
            ],
            host_permissions=["<all_urls>"],
            content_scripts=[
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "css": ["styles.css"],
                    "run_at": "document_idle"
                }
            ],
            background_scripts=["background.js"],
            popup_enabled=True,
            options_page=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.configs[config_id] = config
        self._save_configs()
        
        return config

    def add_permission(self, config_id: str, permission: ExtensionPermission) -> bool:
        """Add a permission to the extension."""
        if config_id not in self.configs:
            return False
        
        if permission not in self.configs[config_id].permissions:
            self.configs[config_id].permissions.append(permission)
            self.configs[config_id].updated_at = datetime.now().isoformat()
            self._save_configs()
        
        return True

    def add_host_permission(self, config_id: str, host: str) -> bool:
        """Add a host permission."""
        if config_id not in self.configs:
            return False
        
        if host not in self.configs[config_id].host_permissions:
            self.configs[config_id].host_permissions.append(host)
            self.configs[config_id].updated_at = datetime.now().isoformat()
            self._save_configs()
        
        return True

    def add_content_script(self, config_id: str, script_config: Dict[str, Any]) -> bool:
        """Add a content script configuration."""
        if config_id not in self.configs:
            return False
        
        self.configs[config_id].content_scripts.append(script_config)
        self.configs[config_id].updated_at = datetime.now().isoformat()
        self._save_configs()
        
        return True

    def generate_manifest_v3(self, config_id: str) -> Optional[Dict]:
        """Generate Manifest V3 for Chrome/Edge."""
        config = self.get_config(config_id)
        if not config:
            return None
        
        manifest = {
            "manifest_version": 3,
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "permissions": [p.value for p in config.permissions],
            "host_permissions": config.host_permissions,
            "background": {
                "service_worker": "background.js"
            },
            "content_scripts": config.content_scripts,
            "action": {
                "default_popup": "popup.html" if config.popup_enabled else None,
                "default_icon": {
                    "16": "icons/icon16.png",
                    "48": "icons/icon48.png",
                    "128": "icons/icon128.png"
                }
            } if config.popup_enabled else None,
            "options_page": "options.html" if config.options_page else None,
            "icons": {
                "16": "icons/icon16.png",
                "48": "icons/icon48.png",
                "128": "icons/icon128.png"
            }
        }
        
        # Remove None values
        manifest = {k: v for k, v in manifest.items() if v is not None}
        
        return manifest

    def generate_manifest_v2(self, config_id: str) -> Optional[Dict]:
        """Generate Manifest V2 for Firefox."""
        config = self.get_config(config_id)
        if not config:
            return None
        
        manifest = {
            "manifest_version": 2,
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "permissions": [p.value for p in config.permissions],
            "content_scripts": config.content_scripts,
            "background": {
                "scripts": config.background_scripts,
                "persistent": False
            },
            "browser_action": {
                "default_popup": "popup.html" if config.popup_enabled else None,
                "default_icon": {
                    "16": "icons/icon16.png",
                    "48": "icons/icon48.png",
                    "128": "icons/icon128.png"
                }
            } if config.popup_enabled else None,
            "options_ui": {
                "page": "options.html",
                "open_in_tab": False
            } if config.options_page else None,
            "icons": {
                "16": "icons/icon16.png",
                "48": "icons/icon48.png",
                "128": "icons/icon128.png"
            }
        }
        
        # Remove None values
        manifest = {k: v for k, v in manifest.items() if v is not None}
        
        return manifest

    def generate_content_script(self, config_id: str) -> str:
        """Generate content script code."""
        content_script = """
// JARVIS AI Assistant - Content Script

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getText') {
        const selectedText = window.getSelection().toString();
        sendResponse({ text: selectedText });
    } else if (request.action === 'getPageContent') {
        const content = document.body.innerText;
        sendResponse({ content: content });
    } else if (request.action === 'highlightText') {
        highlightText(request.text);
        sendResponse({ success: true });
    }
    return true;
});

// Highlight text on page
function highlightText(text) {
    const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    const nodesToReplace = [];
    let node;
    
    while (node = walker.nextNode()) {
        if (node.nodeValue.includes(text)) {
            nodesToReplace.push(node);
        }
    }
    
    nodesToReplace.forEach(node => {
        const span = document.createElement('span');
        span.style.backgroundColor = 'yellow';
        span.textContent = node.textContent;
        node.parentNode.replaceChild(span, node);
    });
}

// Inject JARVIS button
function injectJarvisButton() {
    if (document.getElementById('jarvis-button')) return;
    
    const button = document.createElement('button');
    button.id = 'jarvis-button';
    button.innerHTML = '🤖 JARVIS';
    button.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 20px;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 50px;
        cursor: pointer;
        font-size: 16px;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    
    button.addEventListener('click', () => {
        const selectedText = window.getSelection().toString();
        chrome.runtime.sendMessage({
            action: 'processText',
            text: selectedText
        });
    });
    
    document.body.appendChild(button);
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectJarvisButton);
} else {
    injectJarvisButton();
}
"""
        return content_script

    def generate_background_script(self, config_id: str) -> str:
        """Generate background script code."""
        background_script = """
// JARVIS AI Assistant - Background Script

// Extension installation
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        chrome.tabs.create({ url: 'options.html' });
    }
});

// Handle keyboard shortcuts
chrome.commands.onCommand.addListener((command) => {
    if (command === 'activate-jarvis') {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'activate' });
        });
    }
});

// Context menu
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: 'jarvis-selection',
        title: 'Ask JARVIS',
        contexts: ['selection']
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'jarvis-selection') {
        chrome.tabs.sendMessage(tab.id, {
            action: 'processText',
            text: info.selectionText
        });
    }
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'processText') {
        // Send to JARVIS backend
        processWithJarvis(request.text).then(response => {
            sendResponse({ response });
        });
        return true;
    }
});

// Process text with JARVIS
async function processWithJarvis(text) {
    // In production, this would call the JARVIS API
    // For now, return a placeholder response
    return {
        summary: 'This is a placeholder response from JARVIS.',
        suggestions: ['Suggestion 1', 'Suggestion 2']
    };
}
"""
        return background_script

    def generate_popup_html(self, config_id: str) -> str:
        """Generate popup HTML."""
        popup_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS AI</title>
    <style>
        body {
            width: 300px;
            padding: 15px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .header {
            text-align: center;
            margin-bottom: 15px;
        }
        .logo {
            font-size: 24px;
        }
        .input-area {
            width: 100%;
            height: 100px;
            margin-bottom: 10px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            resize: none;
        }
        .button {
            width: 100%;
            padding: 10px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .button:hover {
            background: #0056b3;
        }
        .status {
            margin-top: 10px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🤖 JARVIS</div>
    </div>
    <textarea class="input-area" id="input" placeholder="Type your message..."></textarea>
    <button class="button" id="send">Send to JARVIS</button>
    <div class="status" id="status">Ready</div>
    <script src="popup.js"></script>
</body>
</html>
"""
        return popup_html

    def get_config(self, config_id: str) -> Optional[ExtensionConfig]:
        """Get extension configuration by ID."""
        return self.configs.get(config_id)

    def delete_config(self, config_id: str) -> bool:
        """Delete an extension configuration."""
        if config_id not in self.configs:
            return False
        
        del self.configs[config_id]
        self._save_configs()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get extension statistics."""
        total_configs = len(self.configs)
        
        # Count by browser
        by_browser = {}
        for config in self.configs.values():
            for browser in config.browsers:
                by_browser[browser.value] = by_browser.get(browser.value, 0) + 1
        
        return {
            'total_configs': total_configs,
            'by_browser': by_browser
        }

    def export_extension(self, config_id: str, export_dir: str) -> Tuple[bool, str]:
        """Export extension files to directory."""
        config = self.get_config(config_id)
        if not config:
            return False, "Config not found"
        
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate and save manifest
            manifest = self.generate_manifest_v3(config_id)
            with open(os.path.join(export_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Generate and save content script
            content_script = self.generate_content_script(config_id)
            with open(os.path.join(export_dir, 'content.js'), 'w') as f:
                f.write(content_script)
            
            # Generate and save background script
            background_script = self.generate_background_script(config_id)
            with open(os.path.join(export_dir, 'background.js'), 'w') as f:
                f.write(background_script)
            
            # Generate and save popup
            popup_html = self.generate_popup_html(config_id)
            with open(os.path.join(export_dir, 'popup.html'), 'w') as f:
                f.write(popup_html)
            
            return True, f"Extension exported to {export_dir}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
