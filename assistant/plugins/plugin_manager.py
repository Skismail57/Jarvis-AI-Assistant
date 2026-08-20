import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import re
from ..utils.logger import logger
from ..config import PLUGINS_DIR


class Plugin:
    def __init__(self, name: str, intent_patterns: List[str], handler: Callable, examples: List[str] = None, icon: str = "🧩"):
        self.name = name
        self.intent_patterns = [re.compile(p, re.IGNORECASE) for p in intent_patterns]
        self.handler = handler
        self.examples = examples or []
        self.icon = icon
        self.description = getattr(handler, "__doc__", "") or name

    def matches(self, text: str) -> Optional[re.Match]:
        for pat in self.intent_patterns:
            m = pat.search(text)
            if m:
                return m
        return None


class PluginManager:
    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = Path(plugins_dir or PLUGINS_DIR)
        self.plugins: Dict[str, Plugin] = {}
        self._discovered = False

    def discover(self):
        if self._discovered:
            return
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        init_file = self.plugins_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")
        for pyfile in sorted(self.plugins_dir.glob("*.py")):
            if pyfile.name.startswith("_"):
                continue
            self._load_plugin_file(pyfile)
        self._discovered = True
        logger.info(f"[PluginManager] Discovered {len(self.plugins)} plugins")

    def _load_plugin_file(self, pyfile: Path):
        try:
            spec = importlib.util.spec_from_file_location(f"jarvis_plugin_{pyfile.stem}", str(pyfile))
            if spec is None or spec.loader is None:
                return
            mod = importlib.util.module_from_spec(spec)
            plugins_parent = str(self.plugins_dir.parent)
            if plugins_parent not in sys.path:
                sys.path.insert(0, plugins_parent)
            spec.loader.exec_module(mod)
            plugin_name = getattr(mod, "PLUGIN_NAME", pyfile.stem)
            patterns = getattr(mod, "INTENT_PATTERNS", [])
            handler = getattr(mod, "handle", None)
            examples = getattr(mod, "EXAMPLES", [])
            icon = getattr(mod, "ICON", "🧩")
            if patterns and callable(handler):
                self.plugins[plugin_name] = Plugin(plugin_name, patterns, handler, examples, icon)
                logger.info(f"[PluginManager] Loaded plugin: {plugin_name} ({len(patterns)} patterns)")
        except Exception as e:
            logger.warning(f"[PluginManager] Failed to load {pyfile}: {e}")

    def try_handle(self, text: str, assistant_ref=None) -> Optional[Dict[str, Any]]:
        self.discover()
        for name, plugin in self.plugins.items():
            m = plugin.matches(text)
            if m:
                try:
                    result = plugin.handler(text, match=m, assistant=assistant_ref)
                    if isinstance(result, str):
                        return {"text": result, "intent": f"plugin:{name}", "plugin": name}
                    if isinstance(result, dict) and "text" in result:
                        result.setdefault("intent", f"plugin:{name}")
                        result["plugin"] = name
                        return result
                except Exception as e:
                    logger.warning(f"[PluginManager] Plugin {name} error: {e}")
        return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        self.discover()
        return [
            {
                "name": p.name,
                "icon": p.icon,
                "description": p.description,
                "examples": p.examples,
            }
            for p in self.plugins.values()
        ]

    def register(self, name: str, patterns: List[str], handler: Callable, examples: List[str] = None, icon: str = "🧩"):
        self.plugins[name] = Plugin(name, patterns, handler, examples or [], icon)
