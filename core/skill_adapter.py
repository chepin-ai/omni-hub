"""
OMNI-HUB v135 Skill Adapter
Adapts external skills into the OMNI-HUB ecosystem.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from core.event_bus import get_bus, Topics


class SkillAdapter:
    """Adapter for loading and executing external skills in OMNI-HUB."""

    def __init__(self) -> None:
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._bus = get_bus()

    def load_skill(self, name: str, fn: Optional[Callable] = None) -> Dict[str, Any]:
        """Load a skill by name. Uses simulated lambda if fn not provided."""
        try:
            if name in self._skills:
                return {
                    "success": False,
                    "error": f"Skill '{name}' already loaded",
                    "skill": name,
                }
            resolved_fn = fn or _get_simulated_skill(name)
            self._skills[name] = {
                "name": name,
                "fn": resolved_fn,
                "loaded_at": datetime.now().isoformat(),
                "execution_count": 0,
            }
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {"component": "skill_adapter", "action": "load", "skill": name},
                source="skill_adapter",
            )
            return {
                "success": True,
                "skill": name,
                "simulated": fn is None,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "skill": name}

    def execute_skill(self, name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a loaded skill with given parameters."""
        try:
            if name not in self._skills:
                return {
                    "success": False,
                    "error": f"Skill '{name}' not loaded",
                    "skill": name,
                }
            skill = self._skills[name]
            params = params or {}
            result = skill["fn"](**params)
            skill["execution_count"] += 1
            self._execution_history.append({
                "skill": name,
                "params": params,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            })
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "component": "skill_adapter",
                    "action": "execute",
                    "skill": name,
                    "result_preview": str(result)[:100],
                },
                source="skill_adapter",
            )
            return {
                "success": True,
                "skill": name,
                "result": result,
                "execution_count": skill["execution_count"],
            }
        except Exception as e:
            return {"success": False, "error": str(e), "skill": name}

    def list_loaded(self) -> List[str]:
        """Return a list of loaded skill names."""
        return sorted(list(self._skills.keys()))

    def unload_skill(self, name: str) -> Dict[str, Any]:
        """Unload a skill by name."""
        try:
            if name not in self._skills:
                return {
                    "success": False,
                    "error": f"Skill '{name}' not loaded",
                    "skill": name,
                }
            del self._skills[name]
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {"component": "skill_adapter", "action": "unload", "skill": name},
                source="skill_adapter",
            )
            return {
                "success": True,
                "skill": name,
                "remaining": len(self._skills),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "skill": name}

    def get_status(self) -> Dict[str, Any]:
        """Return current skill adapter status."""
        return {
            "loaded_count": len(self._skills),
            "loaded": self.list_loaded(),
            "execution_history_count": len(self._execution_history),
        }


def _get_simulated_skill(name: str) -> Callable:
    """Return a simulated lambda function for a given skill name."""
    skills: Dict[str, Callable] = {
        "calculator": lambda **kwargs: kwargs.get("a", 0) + kwargs.get("b", 0),
        "greeter": lambda **kwargs: f"Hello, {kwargs.get('name', 'World')}!",
        "reverser": lambda **kwargs: kwargs.get("text", "")[::-1],
        "doubler": lambda **kwargs: [x * 2 for x in kwargs.get("items", [])],
        "uppercaser": lambda **kwargs: kwargs.get("text", "").upper(),
        "word_counter": lambda **kwargs: len(kwargs.get("text", "").split()),
    }
    if name not in skills:
        return lambda **kwargs: f"[simulated output for {name}]"
    return skills[name]


# Global singleton
_module: Optional[SkillAdapter] = None


def get_skill_adapter() -> SkillAdapter:
    """Get the global SkillAdapter singleton."""
    global _module
    if _module is None:
        _module = SkillAdapter()
    return _module


def reset_skill_adapter() -> None:
    """Reset the global singleton (for testing)."""
    global _module
    _module = SkillAdapter()


if __name__ == "__main__":
    print("[OMNI-HUB v135] Skill Adapter Demo")
    sa = SkillAdapter()
    for skill_name in ["calculator", "greeter", "reverser"]:
        sa.load_skill(skill_name)
    print(f"Loaded: {sa.list_loaded()}")
    print(f"Execute calculator(2,3): {sa.execute_skill('calculator', {'a': 2, 'b': 3})}")
    print(f"Execute greeter(Alice): {sa.execute_skill('greeter', {'name': 'Alice'})}")
    print(f"Status: {sa.get_status()}")
