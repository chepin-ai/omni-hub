"""
OMNI-HUB v134 Plugin Bridge
Registers, activates, and tracks plugin state for the OMNI-HUB ecosystem.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from datetime import datetime

from core.event_bus import get_bus, Topics


class PluginBridge:
    """Bridge for registering and managing plugins in OMNI-HUB."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._active: set = set()
        self._activation_history: List[Dict[str, Any]] = []
        self._bus = get_bus()

    def register(self, name: str, capabilities: List[str]) -> Dict[str, Any]:
        """Register a plugin with its capabilities."""
        try:
            if name in self._plugins:
                return {
                    "success": False,
                    "error": f"Plugin '{name}' already registered",
                    "plugin": name,
                }
            self._plugins[name] = {
                "name": name,
                "capabilities": capabilities,
                "registered_at": datetime.now().isoformat(),
                "state": "registered",
            }
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {"component": "plugin_bridge", "action": "register", "plugin": name},
                source="plugin_bridge",
            )
            return {
                "success": True,
                "plugin": name,
                "capabilities": capabilities,
                "state": "registered",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "plugin": name}

    def activate(self, name: str) -> Dict[str, Any]:
        """Activate a registered plugin."""
        try:
            if name not in self._plugins:
                return {
                    "success": False,
                    "error": f"Plugin '{name}' not registered",
                    "plugin": name,
                }
            if name in self._active:
                return {
                    "success": False,
                    "error": f"Plugin '{name}' already active",
                    "plugin": name,
                }
            self._active.add(name)
            self._plugins[name]["state"] = "active"
            self._activation_history.append({
                "plugin": name,
                "action": "activate",
                "timestamp": datetime.now().isoformat(),
            })
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {"component": "plugin_bridge", "action": "activate", "plugin": name},
                source="plugin_bridge",
            )
            return {
                "success": True,
                "plugin": name,
                "state": "active",
                "active_count": len(self._active),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "plugin": name}

    def deactivate(self, name: str) -> Dict[str, Any]:
        """Deactivate an active plugin."""
        try:
            if name not in self._plugins:
                return {
                    "success": False,
                    "error": f"Plugin '{name}' not registered",
                    "plugin": name,
                }
            if name not in self._active:
                return {
                    "success": False,
                    "error": f"Plugin '{name}' not active",
                    "plugin": name,
                }
            self._active.discard(name)
            self._plugins[name]["state"] = "registered"
            self._activation_history.append({
                "plugin": name,
                "action": "deactivate",
                "timestamp": datetime.now().isoformat(),
            })
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {"component": "plugin_bridge", "action": "deactivate", "plugin": name},
                source="plugin_bridge",
            )
            return {
                "success": True,
                "plugin": name,
                "state": "registered",
                "active_count": len(self._active),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "plugin": name}

    def list_active(self) -> List[str]:
        """Return a list of currently active plugin names."""
        return sorted(list(self._active))

    def list_registered(self) -> List[str]:
        """Return a list of all registered plugin names."""
        return sorted(list(self._plugins.keys()))

    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific plugin."""
        return self._plugins.get(name)

    def get_status(self) -> Dict[str, Any]:
        """Return current plugin bridge status."""
        return {
            "registered_count": len(self._plugins),
            "active_count": len(self._active),
            "registered": self.list_registered(),
            "active": self.list_active(),
            "activation_history_count": len(self._activation_history),
        }


# Global singleton
_module: Optional[PluginBridge] = None


def get_plugin_bridge() -> PluginBridge:
    """Get the global PluginBridge singleton."""
    global _module
    if _module is None:
        _module = PluginBridge()
    return _module


def reset_plugin_bridge() -> None:
    """Reset the global singleton (for testing)."""
    global _module
    _module = PluginBridge()


# Pre-defined simulated plugins
SIMULATED_PLUGINS = {
    "deep_research": ["research", "analysis", "summarization"],
    "web_search": ["search", "fetch", "extract"],
    "image_gen": ["generate_image", "edit_image", "style_transfer"],
    "video_gen": ["generate_video", "edit_video", "transcode"],
    "speech": ["tts", "stt", "voice_clone"],
    "financial_data": ["stock_quote", "crypto_price", "market_news"],
    "legal_data": ["case_lookup", "statute_search", "contract_analysis"],
}


def load_simulated_plugins(bridge: PluginBridge = None) -> PluginBridge:
    """Load all simulated plugins into the bridge."""
    bridge = bridge or get_plugin_bridge()
    for name, capabilities in SIMULATED_PLUGINS.items():
        bridge.register(name, capabilities)
    return bridge


if __name__ == "__main__":
    print("[OMNI-HUB v134] Plugin Bridge Demo")
    pb = PluginBridge()
    load_simulated_plugins(pb)
    print(f"Registered: {pb.list_registered()}")
    for name in ["deep_research", "web_search", "image_gen"]:
        pb.activate(name)
    print(f"Active: {pb.list_active()}")
    print(f"Status: {pb.get_status()}")
