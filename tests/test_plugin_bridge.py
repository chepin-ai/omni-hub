"""
OMNI-HUB v134 Plugin Bridge Tests
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.plugin_bridge import (
    PluginBridge,
    get_plugin_bridge,
    reset_plugin_bridge,
    load_simulated_plugins,
    SIMULATED_PLUGINS,
)
from core.event_bus import Topics


class TestPluginBridgeCreation:
    def test_init_empty(self):
        pb = PluginBridge()
        assert pb.get_status()["registered_count"] == 0
        assert pb.get_status()["active_count"] == 0

    def test_init_empty_lists(self):
        pb = PluginBridge()
        assert pb.list_active() == []
        assert pb.list_registered() == []


class TestPluginRegister:
    def test_register_single(self):
        pb = PluginBridge()
        result = pb.register("test_plugin", ["cap1", "cap2"])
        assert result["success"] is True
        assert result["plugin"] == "test_plugin"
        assert result["state"] == "registered"

    def test_register_duplicate_fails(self):
        pb = PluginBridge()
        pb.register("test_plugin", ["cap1"])
        result = pb.register("test_plugin", ["cap2"])
        assert result["success"] is False
        assert "already registered" in result["error"]

    def test_register_multiple(self):
        pb = PluginBridge()
        pb.register("p1", ["a"])
        pb.register("p2", ["b"])
        assert pb.get_status()["registered_count"] == 2

    def test_list_registered_sorted(self):
        pb = PluginBridge()
        pb.register("z_plugin", ["z"])
        pb.register("a_plugin", ["a"])
        assert pb.list_registered() == ["a_plugin", "z_plugin"]


class TestPluginActivate:
    def test_activate_registered(self):
        pb = PluginBridge()
        pb.register("test", ["cap"])
        result = pb.activate("test")
        assert result["success"] is True
        assert result["state"] == "active"
        assert result["active_count"] == 1

    def test_activate_not_registered_fails(self):
        pb = PluginBridge()
        result = pb.activate("missing")
        assert result["success"] is False
        assert "not registered" in result["error"]

    def test_activate_already_active_fails(self):
        pb = PluginBridge()
        pb.register("test", ["cap"])
        pb.activate("test")
        result = pb.activate("test")
        assert result["success"] is False
        assert "already active" in result["error"]

    def test_list_active_returns_names(self):
        pb = PluginBridge()
        pb.register("p1", ["a"])
        pb.register("p2", ["b"])
        pb.activate("p2")
        pb.activate("p1")
        assert pb.list_active() == ["p1", "p2"]


class TestPluginDeactivate:
    def test_deactivate_active(self):
        pb = PluginBridge()
        pb.register("test", ["cap"])
        pb.activate("test")
        result = pb.deactivate("test")
        assert result["success"] is True
        assert result["state"] == "registered"
        assert result["active_count"] == 0

    def test_deactivate_not_active_fails(self):
        pb = PluginBridge()
        pb.register("test", ["cap"])
        result = pb.deactivate("test")
        assert result["success"] is False
        assert "not active" in result["error"]

    def test_deactivate_not_registered_fails(self):
        pb = PluginBridge()
        result = pb.deactivate("missing")
        assert result["success"] is False
        assert "not registered" in result["error"]


class TestPluginGetStatus:
    def test_status_empty(self):
        pb = PluginBridge()
        status = pb.get_status()
        assert status["registered_count"] == 0
        assert status["active_count"] == 0
        assert status["registered"] == []
        assert status["active"] == []

    def test_status_with_plugins(self):
        pb = PluginBridge()
        pb.register("p1", ["a"])
        pb.register("p2", ["b"])
        pb.activate("p1")
        status = pb.get_status()
        assert status["registered_count"] == 2
        assert status["active_count"] == 1
        assert "p1" in status["active"]
        assert "p2" in status["registered"]

    def test_get_plugin(self):
        pb = PluginBridge()
        pb.register("test", ["cap1", "cap2"])
        plugin = pb.get_plugin("test")
        assert plugin is not None
        assert plugin["name"] == "test"
        assert plugin["capabilities"] == ["cap1", "cap2"]

    def test_get_plugin_missing(self):
        pb = PluginBridge()
        assert pb.get_plugin("missing") is None


class TestSimulatedPlugins:
    def test_all_simulated_registered(self):
        pb = PluginBridge()
        load_simulated_plugins(pb)
        assert pb.get_status()["registered_count"] == len(SIMULATED_PLUGINS)
        for name in SIMULATED_PLUGINS:
            assert name in pb.list_registered()

    def test_simulated_capabilities(self):
        pb = PluginBridge()
        load_simulated_plugins(pb)
        for name, caps in SIMULATED_PLUGINS.items():
            plugin = pb.get_plugin(name)
            assert plugin["capabilities"] == caps

    def test_activate_all_simulated(self):
        pb = PluginBridge()
        load_simulated_plugins(pb)
        for name in SIMULATED_PLUGINS:
            pb.activate(name)
        assert pb.get_status()["active_count"] == len(SIMULATED_PLUGINS)


class TestSingleton:
    def test_singleton_returns_same_instance(self):
        reset_plugin_bridge()
        pb1 = get_plugin_bridge()
        pb2 = get_plugin_bridge()
        assert pb1 is pb2

    def test_singleton_persists_state(self):
        reset_plugin_bridge()
        pb = get_plugin_bridge()
        pb.register("singleton_plugin", ["cap"])
        pb2 = get_plugin_bridge()
        assert "singleton_plugin" in pb2.list_registered()


class TestEventBusIntegration:
    def test_register_publishes_event(self):
        from core.event_bus import reset_bus, get_bus
        reset_bus()
        pb = PluginBridge()
        pb.register("event_test", ["cap"])
        events = get_bus().get_history(Topics.STATE_CHANGE)
        assert any(e.payload.get("plugin") == "event_test" for e in events)
