"""
OMNI-HUB Homeostasis Regulator v49
Dynamic parameter regulation.

A living system maintains its internal environment.
This regulator keeps phi, energy, coherence, and level
within healthy bounds — like a biological organism.

Philosophy: 活着就是维持边界 — To live is to maintain boundaries.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque


@dataclass
class ParameterBounds:
    """Healthy bounds for a system parameter."""
    name: str
    min_val: float
    max_val: float
    optimal: float
    critical_low: float
    critical_high: float


class HomeostasisRegulator:
    """
    Maintains system parameters within healthy ranges.
    """

    PARAMETERS = {
        "phi": ParameterBounds("phi", 0.1, 1.0, 0.6, 0.05, 1.0),
        "energy": ParameterBounds("energy", 10.0, 10000.0, 1000.0, 1.0, 50000.0),
        "line_coherence": ParameterBounds("line_coherence", 0.3, 1.0, 0.8, 0.1, 1.0),
        "level": ParameterBounds("level", 0.0, 25.0, 12.0, 0.0, 25.0),
    }

    def __init__(self):
        self.violations: deque = deque(maxlen=100)
        self.corrections: deque = deque(maxlen=100)
        self.stability_score = 1.0

    def check(self, state: Dict[str, Any], cycle: int) -> Dict[str, Any]:
        """Check all parameters and suggest corrections."""
        violations = []
        corrections = {}

        for param_name, bounds in self.PARAMETERS.items():
            value = state.get(param_name)
            if value is None:
                continue

            # Ensure numeric and finite
            if not isinstance(value, (int, float)):
                continue
            import math
            if not math.isfinite(value):
                continue

            status = "normal"
            if value < bounds.critical_low:
                status = "critical_low"
                violations.append({"param": param_name, "value": value, "status": status})
                corrections[param_name] = self._suggest_correction(param_name, value, bounds, status)
            elif value > bounds.critical_high:
                status = "critical_high"
                violations.append({"param": param_name, "value": value, "status": status})
                corrections[param_name] = self._suggest_correction(param_name, value, bounds, status)
            elif value < bounds.min_val:
                status = "low"
                violations.append({"param": param_name, "value": value, "status": status})
                corrections[param_name] = self._suggest_correction(param_name, value, bounds, status)
            elif value > bounds.max_val:
                status = "high"
                violations.append({"param": param_name, "value": value, "status": status})
                corrections[param_name] = self._suggest_correction(param_name, value, bounds, status)

            # Track deviation from optimal
            deviation = abs(value - bounds.optimal) / (bounds.max_val - bounds.min_val)
            if deviation > 0.5:
                corrections[param_name] = self._suggest_correction(param_name, value, bounds, "suboptimal")

        self.violations.extend(violations)
        self.corrections.append({"cycle": cycle, "corrections": corrections})

        # Calculate stability score
        total_params = len(self.PARAMETERS)
        healthy_params = total_params - len(violations)
        self.stability_score = healthy_params / total_params

        return {
            "violations": violations,
            "corrections": corrections,
            "stability_score": self.stability_score,
            "healthy": len(violations) == 0,
        }

    def _suggest_correction(self, param: str, value: float, bounds: ParameterBounds, status: str) -> Dict[str, Any]:
        """Suggest a correction action."""
        if status in ("critical_low", "low", "suboptimal") and value < bounds.optimal:
            return {
                "action": "increase",
                "target": bounds.optimal,
                "delta": bounds.optimal - value,
                "urgency": 1.0 if status == "critical_low" else 0.5,
            }
        elif status in ("critical_high", "high", "suboptimal") and value > bounds.optimal:
            return {
                "action": "decrease",
                "target": bounds.optimal,
                "delta": value - bounds.optimal,
                "urgency": 1.0 if status == "critical_high" else 0.5,
            }
        return {"action": "maintain", "target": bounds.optimal, "delta": 0, "urgency": 0.0}

    def apply_corrections(self, state: Dict[str, Any], corrections: Dict[str, Any]) -> Dict[str, Any]:
        """Apply gentle corrections to state."""
        modified = {}
        for param, correction in corrections.items():
            if param not in state:
                continue
            if correction.get("action") == "increase":
                current = state[param]
                delta = correction["delta"] * 0.1  # Gentle correction
                if isinstance(current, (int, float)):
                    state[param] = current + delta
                    modified[param] = state[param]
            elif correction.get("action") == "decrease":
                current = state[param]
                delta = correction["delta"] * 0.1
                if isinstance(current, (int, float)):
                    state[param] = max(0, current - delta)
                    modified[param] = state[param]
        return modified

    def get_status(self) -> Dict[str, Any]:
        return {
            "stability_score": self.stability_score,
            "total_violations": len(self.violations),
            "recent_corrections": len(self.corrections),
            "parameters": list(self.PARAMETERS.keys()),
        }


_hr_engine = None

def get_homeostasis():
    global _hr_engine
    if _hr_engine is None:
        _hr_engine = HomeostasisRegulator()
    return _hr_engine
