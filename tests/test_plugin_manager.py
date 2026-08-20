import os
import pytest


def test_discover_creates_plugins_dir(tmp_plugins_dir):
    from assistant.plugins.plugin_manager import PluginManager
    pm = PluginManager(plugins_dir=tmp_plugins_dir)
    pm.discover()
    assert os.path.exists(os.path.join(tmp_plugins_dir, "__init__.py"))
    assert pm._discovered is True


def test_discover_only_runs_once(tmp_plugins_dir):
    from assistant.plugins.plugin_manager import PluginManager
    pm = PluginManager(plugins_dir=tmp_plugins_dir)
    pm.discover()
    pm.plugins["dummy"] = "not_real"
    pm.discover()
    assert "dummy" in pm.plugins


def test_list_plugins_returns_list(tmp_plugins_dir):
    from assistant.plugins.plugin_manager import PluginManager
    pm = PluginManager(plugins_dir=tmp_plugins_dir)
    pm.discover()
    result = pm.list_plugins()
    assert isinstance(result, list)
    for item in result:
        assert "name" in item
        assert "icon" in item
        assert "description" in item
        assert "examples" in item


def test_register_basic_plugin(tmp_plugins_dir):
    from assistant.plugins.plugin_manager import PluginManager, Plugin

    pm = PluginManager(plugins_dir=tmp_plugins_dir)
    pm.discover()

    def my_handler(text, **kwargs):
        return f"Handled: {text}"

    patterns = [r"run my plugin", r"execute custom"]
    pm.register(
        name="my_custom_plugin",
        patterns=patterns,
        handler=my_handler,
        examples=["run my plugin now"],
        icon="🚀",
    )

    assert "my_custom_plugin" in pm.plugins
    plugin = pm.plugins["my_custom_plugin"]
    assert isinstance(plugin, Plugin)
    assert plugin.name == "my_custom_plugin"
    assert plugin.icon == "🚀"
    assert plugin.examples == ["run my plugin now"]
    assert len(plugin.intent_patterns) == 2


def test_plugin_matches_pattern():
    from assistant.plugins.plugin_manager import Plugin

    def h(text, **kw):
        return text

    p = Plugin("test", [r"\bhello\b", r"^greet"], h, examples=["hello"])
    assert p.matches("say hello world") is not None
    assert p.matches("greet me please") is not None
    assert p.matches("nothing here") is None


def test_registered_plugin_appears_in_list(tmp_plugins_dir):
    from assistant.plugins.plugin_manager import PluginManager

    pm = PluginManager(plugins_dir=tmp_plugins_dir)
    pm.discover()

    def handler(text, **kw):
        return "ok"

    pm.register("alpha", [r"alpha"], handler)
    names = [p["name"] for p in pm.list_plugins()]
    assert "alpha" in names


def test_try_handle_with_registered_plugin(tmp_plugins_dir):
    from assistant.plugins.plugin_manager import PluginManager
    pm = PluginManager(plugins_dir=tmp_plugins_dir)
    pm.discover()

    def echo_handler(text, **kw):
        return {"text": f"echo:{text}"}

    pm.register("echo_plugin", [r"\becho\b"], echo_handler)
    result = pm.try_handle("echo hello world")
    assert result is not None
    assert result["intent"] == "plugin:echo_plugin"
    assert result["plugin"] == "echo_plugin"
    assert "echo:" in result["text"]
