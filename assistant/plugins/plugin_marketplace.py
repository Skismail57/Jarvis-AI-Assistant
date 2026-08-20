"""
Plugin Marketplace System
Provides a centralized marketplace for discovering, installing, and managing plugins.
"""

import os
import json
import hashlib
import shutil
import subprocess
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from pathlib import Path


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: str
    repository: str
    dependencies: List[str]
    jarvis_version: str
    categories: List[str]
    icon: str
    tags: List[str]
    install_count: int
    rating: float
    last_updated: str


@dataclass
class PluginReview:
    plugin_name: str
    user: str
    rating: int
    comment: str
    date: str


@dataclass
class InstalledPlugin:
    manifest: PluginManifest
    install_path: str
    installed_at: str
    enabled: bool
    config: Dict[str, Any] = None


class PluginMarketplace:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.marketplace_dir = os.path.join(self.base_dir, "data", "marketplace")
        self.registry_file = os.path.join(self.marketplace_dir, "registry.json")
        self.installed_file = os.path.join(self.marketplace_dir, "installed.json")
        self.reviews_file = os.path.join(self.marketplace_dir, "reviews.json")
        
        os.makedirs(self.marketplace_dir, exist_ok=True)
        
        self.registry = self._load_registry()
        self.installed_plugins = self._load_installed()
        self.reviews = self._load_reviews()
        
        # Built-in registry (would be fetched from remote server in production)
        self._initialize_builtin_registry()

    def _load_registry(self) -> Dict[str, PluginManifest]:
        """Load plugin registry from disk."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {name: PluginManifest(**manifest) for name, manifest in data.items()}
            except Exception:
                pass
        return {}

    def _save_registry(self):
        """Save plugin registry to disk."""
        try:
            data = {name: asdict(manifest) for name, manifest in self.registry.items()}
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PluginMarketplace] Failed to save registry: {e}")

    def _load_installed(self) -> Dict[str, InstalledPlugin]:
        """Load installed plugins from disk."""
        if os.path.exists(self.installed_file):
            try:
                with open(self.installed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {name: InstalledPlugin(**plugin) for name, plugin in data.items()}
            except Exception:
                pass
        return {}

    def _save_installed(self):
        """Save installed plugins to disk."""
        try:
            data = {name: asdict(plugin) for name, plugin in self.installed_plugins.items()}
            with open(self.installed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PluginMarketplace] Failed to save installed plugins: {e}")

    def _load_reviews(self) -> Dict[str, List[PluginReview]]:
        """Load plugin reviews from disk."""
        if os.path.exists(self.reviews_file):
            try:
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {name: [PluginReview(**review) for review in reviews] 
                       for name, reviews in data.items()}
            except Exception:
                pass
        return {}

    def _save_reviews(self):
        """Save plugin reviews to disk."""
        try:
            data = {name: [asdict(review) for review in reviews] 
                   for name, reviews in self.reviews.items()}
            with open(self.reviews_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PluginMarketplace] Failed to save reviews: {e}")

    def _initialize_builtin_registry(self):
        """Initialize built-in plugin registry."""
        if not self.registry:
            builtin_plugins = {
                "weather_extended": PluginManifest(
                    name="weather_extended",
                    version="1.0.0",
                    description="Extended weather capabilities with forecasts, alerts, and historical data",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/weather_extended",
                    repository="https://github.com/jarvis/weather_extended",
                    dependencies=["requests>=2.31.0"],
                    jarvis_version=">=1.0.0",
                    categories=["productivity", "utilities"],
                    icon="🌤️",
                    tags=["weather", "forecast", "alerts"],
                    install_count=1250,
                    rating=4.5,
                    last_updated="2024-01-15"
                ),
                "smart_home_hub": PluginManifest(
                    name="smart_home_hub",
                    version="2.1.0",
                    description="Comprehensive smart home integration with support for 100+ device types",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/smart_home_hub",
                    repository="https://github.com/jarvis/smart_home_hub",
                    dependencies=["homeassistant>=2023.0.0", "requests>=2.31.0"],
                    jarvis_version=">=1.0.0",
                    categories=["smarthome", "automation"],
                    icon="🏠",
                    tags=["home-automation", "iot", "devices"],
                    install_count=890,
                    rating=4.8,
                    last_updated="2024-01-20"
                ),
                "calendar_pro": PluginManifest(
                    name="calendar_pro",
                    version="1.5.0",
                    description="Advanced calendar management with conflict resolution and smart scheduling",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/calendar_pro",
                    repository="https://github.com/jarvis/calendar_pro",
                    dependencies=["google-api-python-client>=2.100.0"],
                    jarvis_version=">=1.0.0",
                    categories=["productivity", "calendar"],
                    icon="📅",
                    tags=["calendar", "scheduling", "meetings"],
                    install_count=2100,
                    rating=4.7,
                    last_updated="2024-01-18"
                ),
                "code_assistant": PluginManifest(
                    name="code_assistant",
                    version="1.2.0",
                    description="AI-powered code generation, debugging, and refactoring assistant",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/code_assistant",
                    repository="https://github.com/jarvis/code_assistant",
                    dependencies=["openai>=1.30.0"],
                    jarvis_version=">=1.0.0",
                    categories=["development", "ai"],
                    icon="💻",
                    tags=["coding", "programming", "development"],
                    install_count=3400,
                    rating=4.9,
                    last_updated="2024-01-22"
                ),
                "finance_tracker": PluginManifest(
                    name="finance_tracker",
                    version="1.0.0",
                    description="Personal finance tracking with expense categorization and budget management",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/finance_tracker",
                    repository="https://github.com/jarvis/finance_tracker",
                    dependencies=["pandas>=2.0.0", "matplotlib>=3.7.0"],
                    jarvis_version=">=1.0.0",
                    categories=["productivity", "finance"],
                    icon="💰",
                    tags=["finance", "budget", "expenses"],
                    install_count=780,
                    rating=4.3,
                    last_updated="2024-01-10"
                ),
                "music_controller": PluginManifest(
                    name="music_controller",
                    version="1.3.0",
                    description="Universal music control for Spotify, Apple Music, and local libraries",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/music_controller",
                    repository="https://github.com/jarvis/music_controller",
                    dependencies=["spotipy>=2.23.0"],
                    jarvis_version=">=1.0.0",
                    categories=["entertainment", "music"],
                    icon="🎵",
                    tags=["music", "spotify", "audio"],
                    install_count=1560,
                    rating=4.6,
                    last_updated="2024-01-16"
                ),
                "fitness_tracker": PluginManifest(
                    name="fitness_tracker",
                    version="1.0.0",
                    description="Workout tracking, nutrition logging, and health metrics integration",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/fitness_tracker",
                    repository="https://github.com/jarvis/fitness_tracker",
                    dependencies=["requests>=2.31.0"],
                    jarvis_version=">=1.0.0",
                    categories=["health", "fitness"],
                    icon="💪",
                    tags=["fitness", "health", "workout"],
                    install_count=620,
                    rating=4.2,
                    last_updated="2024-01-12"
                ),
                "news_reader": PluginManifest(
                    name="news_reader",
                    version="1.1.0",
                    description="Personalized news aggregation with topic filtering and summarization",
                    author="JARVIS Team",
                    license="MIT",
                    homepage="https://github.com/jarvis/news_reader",
                    repository="https://github.com/jarvis/news_reader",
                    dependencies=["feedparser>=6.0.10", "newspaper3k>=0.2.8"],
                    jarvis_version=">=1.0.0",
                    categories=["information", "news"],
                    icon="📰",
                    tags=["news", "rss", "information"],
                    install_count=980,
                    rating=4.4,
                    last_updated="2024-01-14"
                )
            }
            
            self.registry = builtin_plugins
            self._save_registry()

    def search_plugins(self, query: str, category: str = None, 
                      tags: List[str] = None, sort_by: str = "rating") -> List[PluginManifest]:
        """
        Search for plugins in the marketplace.
        
        Args:
            query: Search query
            category: Filter by category
            tags: Filter by tags
            sort_by: Sort method ['rating', 'install_count', 'name', 'updated']
        """
        results = []
        
        for manifest in self.registry.values():
            # Text search
            if query:
                query_lower = query.lower()
                text_match = (query_lower in manifest.name.lower() or
                            query_lower in manifest.description.lower() or
                            query_lower in manifest.author.lower())
                if not text_match:
                    continue
            
            # Category filter
            if category and category not in manifest.categories:
                continue
            
            # Tags filter
            if tags and not any(tag in manifest.tags for tag in tags):
                continue
            
            results.append(manifest)
        
        # Sort results
        if sort_by == "rating":
            results.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "install_count":
            results.sort(key=lambda x: x.install_count, reverse=True)
        elif sort_by == "name":
            results.sort(key=lambda x: x.name)
        elif sort_by == "updated":
            results.sort(key=lambda x: x.last_updated, reverse=True)
        
        return results

    def get_plugin_details(self, plugin_name: str) -> Optional[PluginManifest]:
        """Get detailed information about a plugin."""
        return self.registry.get(plugin_name)

    def get_plugin_reviews(self, plugin_name: str) -> List[PluginReview]:
        """Get reviews for a plugin."""
        return self.reviews.get(plugin_name, [])

    def add_review(self, plugin_name: str, user: str, rating: int, 
                  comment: str) -> bool:
        """Add a review for a plugin."""
        if plugin_name not in self.registry:
            return False
        
        if not (1 <= rating <= 5):
            return False
        
        review = PluginReview(
            plugin_name=plugin_name,
            user=user,
            rating=rating,
            comment=comment,
            date=datetime.now().isoformat()
        )
        
        if plugin_name not in self.reviews:
            self.reviews[plugin_name] = []
        
        self.reviews[plugin_name].append(review)
        
        # Update plugin rating
        self._update_plugin_rating(plugin_name)
        
        self._save_reviews()
        return True

    def _update_plugin_rating(self, plugin_name: str):
        """Update plugin rating based on reviews."""
        if plugin_name not in self.reviews or not self.reviews[plugin_name]:
            return
        
        reviews = self.reviews[plugin_name]
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        
        if plugin_name in self.registry:
            self.registry[plugin_name].rating = round(avg_rating, 1)
            self._save_registry()

    def install_plugin(self, plugin_name: str, version: str = None) -> Tuple[bool, str]:
        """
        Install a plugin from the marketplace.
        
        Args:
            plugin_name: Name of the plugin to install
            version: Specific version to install (default: latest)
            
        Returns:
            (success, message)
        """
        if plugin_name not in self.registry:
            return False, f"Plugin '{plugin_name}' not found in marketplace"
        
        if plugin_name in self.installed_plugins:
            return False, f"Plugin '{plugin_name}' is already installed"
        
        manifest = self.registry[plugin_name]
        
        try:
            # Create plugin directory
            plugins_dir = os.path.join(self.base_dir, "plugins")
            plugin_dir = os.path.join(plugins_dir, plugin_name)
            os.makedirs(plugin_dir, exist_ok=True)
            
            # Install dependencies
            if manifest.dependencies:
                print(f"[PluginMarketplace] Installing dependencies for {plugin_name}...")
                for dep in manifest.dependencies:
                    try:
                        subprocess.run(
                            ["pip", "install", dep],
                            check=True,
                            capture_output=True,
                            text=True
                        )
                        print(f"[PluginMarketplace] Installed {dep}")
                    except subprocess.CalledProcessError as e:
                        return False, f"Failed to install dependency {dep}: {e.stderr}"
            
            # Create plugin template file
            plugin_file = os.path.join(plugin_dir, f"{plugin_name}.py")
            self._create_plugin_template(plugin_file, manifest)
            
            # Create config file
            config_file = os.path.join(plugin_dir, "config.json")
            with open(config_file, 'w') as f:
                json.dump({"enabled": True, "settings": {}}, f, indent=2)
            
            # Register as installed
            installed_plugin = InstalledPlugin(
                manifest=manifest,
                install_path=plugin_dir,
                installed_at=datetime.now().isoformat(),
                enabled=True,
                config={"enabled": True, "settings": {}}
            )
            
            self.installed_plugins[plugin_name] = installed_plugin
            self._save_installed()
            
            # Update install count
            manifest.install_count += 1
            self._save_registry()
            
            return True, f"Plugin '{plugin_name}' installed successfully"
            
        except Exception as e:
            return False, f"Installation failed: {str(e)}"

    def _create_plugin_template(self, plugin_file: str, manifest: PluginManifest):
        """Create a template plugin file."""
        template = f'''"""
{manifest.name} - {manifest.description}
Author: {manifest.author}
Version: {manifest.version}
License: {manifest.license}
"""

PLUGIN_NAME = "{manifest.name}"
ICON = "{manifest.icon}"
INTENT_PATTERNS = [
    # Add your intent patterns here
    r"example pattern",
]
EXAMPLES = [
    # Add example phrases here
    "example command",
]

def handle(text, match=None, assistant=None):
    """Main handler function for the plugin."""
    # Your plugin logic here
    return {{
        "text": "Response from {manifest.name}",
        "intent": "{manifest.name}",
        "data": {{}}
    }}

def on_install(assistant=None):
    """Called when plugin is installed."""
    pass

def on_uninstall(assistant=None):
    """Called when plugin is uninstalled."""
    pass

def on_enable(assistant=None):
    """Called when plugin is enabled."""
    pass

def on_disable(assistant=None):
    """Called when plugin is disabled."""
    pass
'''
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(template)

    def uninstall_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """Uninstall a plugin."""
        if plugin_name not in self.installed_plugins:
            return False, f"Plugin '{plugin_name}' is not installed"
        
        try:
            installed = self.installed_plugins[plugin_name]
            
            # Remove plugin directory
            if os.path.exists(installed.install_path):
                shutil.rmtree(installed.install_path)
            
            # Remove from installed list
            del self.installed_plugins[plugin_name]
            self._save_installed()
            
            return True, f"Plugin '{plugin_name}' uninstalled successfully"
            
        except Exception as e:
            return False, f"Uninstallation failed: {str(e)}"

    def enable_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """Enable an installed plugin."""
        if plugin_name not in self.installed_plugins:
            return False, f"Plugin '{plugin_name}' is not installed"
        
        self.installed_plugins[plugin_name].enabled = True
        self._save_installed()
        
        return True, f"Plugin '{plugin_name}' enabled"

    def disable_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """Disable an installed plugin."""
        if plugin_name not in self.installed_plugins:
            return False, f"Plugin '{plugin_name}' is not installed"
        
        self.installed_plugins[plugin_name].enabled = False
        self._save_installed()
        
        return True, f"Plugin '{plugin_name}' disabled"

    def update_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """Update a plugin to the latest version."""
        if plugin_name not in self.installed_plugins:
            return False, f"Plugin '{plugin_name}' is not installed"
        
        if plugin_name not in self.registry:
            return False, f"Plugin '{plugin_name}' not found in marketplace"
        
        installed = self.installed_plugins[plugin_name]
        latest = self.registry[plugin_name]
        
        if installed.manifest.version == latest.version:
            return True, f"Plugin '{plugin_name}' is already up to date"
        
        # Uninstall and reinstall
        self.uninstall_plugin(plugin_name)
        return self.install_plugin(plugin_name)

    def get_installed_plugins(self) -> List[InstalledPlugin]:
        """Get list of installed plugins."""
        return list(self.installed_plugins.values())

    def get_categories(self) -> List[str]:
        """Get all available plugin categories."""
        categories = set()
        for manifest in self.registry.values():
            categories.update(manifest.categories)
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """Get all available plugin tags."""
        tags = set()
        for manifest in self.registry.values():
            tags.update(manifest.tags)
        return sorted(list(tags))

    def get_statistics(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        total_plugins = len(self.registry)
        installed_count = len(self.installed_plugins)
        total_installs = sum(m.install_count for m in self.registry.values())
        avg_rating = sum(m.rating for m in self.registry.values()) / total_plugins if total_plugins > 0 else 0
        
        return {
            "total_plugins": total_plugins,
            "installed_plugins": installed_count,
            "total_installs": total_installs,
            "average_rating": round(avg_rating, 2),
            "categories": len(self.get_categories()),
            "tags": len(self.get_tags())
        }

    def sync_registry(self, remote_url: str = None) -> Tuple[bool, str]:
        """
        Sync plugin registry with remote server.
        
        Args:
            remote_url: URL of remote registry (default: official JARVIS registry)
        """
        if remote_url is None:
            remote_url = "https://api.jarvis.ai/plugins/registry"
        
        try:
            response = requests.get(remote_url, timeout=10)
            response.raise_for_status()
            
            remote_registry = response.json()
            
            # Merge registries
            for name, manifest_data in remote_registry.items():
                if name not in self.registry:
                    self.registry[name] = PluginManifest(**manifest_data)
                else:
                    # Update if remote version is newer
                    from packaging import version as pkg_version
                    local_ver = pkg_version.parse(self.registry[name].version)
                    remote_ver = pkg_version.parse(manifest_data['version'])
                    
                    if remote_ver > local_ver:
                        self.registry[name] = PluginManifest(**manifest_data)
            
            self._save_registry()
            return True, f"Registry synced successfully. {len(remote_registry)} plugins available"
            
        except Exception as e:
            return False, f"Registry sync failed: {str(e)}"

    def submit_plugin(self, plugin_path: str, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Submit a new plugin to the marketplace.
        
        Args:
            plugin_path: Path to plugin directory or file
            metadata: Plugin metadata
        """
        try:
            # Validate plugin structure
            if not os.path.exists(plugin_path):
                return False, "Plugin path does not exist"
            
            # Create manifest
            manifest = PluginManifest(
                name=metadata.get('name', 'unknown'),
                version=metadata.get('version', '1.0.0'),
                description=metadata.get('description', ''),
                author=metadata.get('author', 'unknown'),
                license=metadata.get('license', 'MIT'),
                homepage=metadata.get('homepage', ''),
                repository=metadata.get('repository', ''),
                dependencies=metadata.get('dependencies', []),
                jarvis_version=metadata.get('jarvis_version', '>=1.0.0'),
                categories=metadata.get('categories', []),
                icon=metadata.get('icon', '🔌'),
                tags=metadata.get('tags', []),
                install_count=0,
                rating=0.0,
                last_updated=datetime.now().strftime('%Y-%m-%d')
            )
            
            # Add to registry
            self.registry[manifest.name] = manifest
            self._save_registry()
            
            return True, f"Plugin '{manifest.name}' submitted to marketplace"
            
        except Exception as e:
            return False, f"Submission failed: {str(e)}"

    def export_plugin(self, plugin_name: str, output_path: str) -> Tuple[bool, str]:
        """Export an installed plugin as a distributable package."""
        if plugin_name not in self.installed_plugins:
            return False, f"Plugin '{plugin_name}' is not installed"
        
        try:
            import zipfile
            
            installed = self.installed_plugins[plugin_name]
            output_file = os.path.join(output_path, f"{plugin_name}.jarvis")
            
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(installed.install_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, installed.install_path)
                        zipf.write(file_path, arcname)
            
            return True, f"Plugin exported to {output_file}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def import_plugin(self, package_path: str) -> Tuple[bool, str]:
        """Import a plugin from a distributable package."""
        try:
            import zipfile
            
            if not os.path.exists(package_path):
                return False, "Package file does not exist"
            
            with zipfile.ZipFile(package_path, 'r') as zipf:
                # Extract manifest
                manifest_data = None
                for file in zipf.namelist():
                    if file.endswith('manifest.json'):
                        manifest_data = json.loads(zipf.read(file).decode('utf-8'))
                        break
                
                if not manifest_data:
                    return False, "Invalid plugin package (no manifest)"
                
                # Extract plugin
                plugin_name = manifest_data.get('name')
                plugin_dir = os.path.join(self.base_dir, "plugins", plugin_name)
                
                if os.path.exists(plugin_dir):
                    return False, f"Plugin '{plugin_name}' already exists"
                
                zipf.extractall(plugin_dir)
                
                # Register as installed
                manifest = PluginManifest(**manifest_data)
                installed_plugin = InstalledPlugin(
                    manifest=manifest,
                    install_path=plugin_dir,
                    installed_at=datetime.now().isoformat(),
                    enabled=True
                )
                
                self.installed_plugins[plugin_name] = installed_plugin
                self._save_installed()
                
                return True, f"Plugin '{plugin_name}' imported successfully"
            
        except Exception as e:
            return False, f"Import failed: {str(e)}"
