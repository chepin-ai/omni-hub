"""
OMNI-HUB Counterfactual Engine v51
What-if reasoning.

The road not taken is also a road.
This engine explores alternative histories —
what would have happened if different choices were made.

Philosophy: 未走的路也是路 — The road not taken is also a road.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class Counterfactual:
    """A single what-if scenario."""
    premise: str
    altered_state: Dict[str, Any]
    projected_outcome: Dict[str, Any]
    delta_from_actual: Dict[str, Any]
    regret_score: float


class CounterfactualEngine:
    """
    Explores alternative histories through simulation.
    """

    REGRET_WEIGHTS = {
        "level": 1.0,
        "energy": 0.5,
        "phi": 0.8,
        "line_coherence": 0.7,
    }

    def __init__(self):
        self.counterfactuals: List[Counterfactual] = []
        self.scenario_count = 0

    def _simulate_branch(self, base_state: Dict[str, Any], alteration: Dict[str, Any], steps: int = 10) -> Dict[str, Any]:
        """Simulate a branch with altered initial conditions."""
        state = deepcopy(base_state)
        state.update(alteration)

        # Simple forward simulation
        for _ in range(steps):
            # Energy decay
            if "energy" in state and isinstance(state["energy"], (int, float)):
                state["energy"] *= 0.99

            # Phi gentle oscillation
            if "phi" in state and isinstance(state["phi"], (int, float)):
                import math
                state["phi"] = max(0.1, min(1.0, state["phi"] + 0.01 * math.sin(state.get("cycle", 0))))

            # Level gentle drift toward alteration
            if "level" in state and "target_level" in alteration:
                current = state["level"]
                target = alteration["target_level"]
                state["level"] = current + (target - current) * 0.1

        return state

    def generate_scenarios(self, actual_state: Dict[str, Any], history: List[Dict[str, Any]]) -> List[Counterfactual]:
        """Generate counterfactual scenarios from history."""
        scenarios = []

        # Scenario 1: What if we had acted differently?
        if history:
            last_action = history[-1].get("last_self_drive_action", "focus")
            alternatives = {"focus": "rest", "rest": "focus", "transcend": "reflect", "reflect": "transcend"}
            alt_action = alternatives.get(last_action, "focus")

            altered = {"last_self_drive_action": alt_action}
            projected = self._simulate_branch(actual_state, altered)

            delta = {}
            for key in ["level", "energy", "phi", "line_coherence"]:
                if key in actual_state and key in projected:
                    try:
                        delta[key] = projected[key] - actual_state[key]
                    except (TypeError, ValueError):
                        pass

            regret = sum(abs(delta.get(k, 0)) * self.REGRET_WEIGHTS.get(k, 0.5) for k in delta)

            scenarios.append(Counterfactual(
                premise=f"What if action was '{alt_action}' instead of '{last_action}'?",
                altered_state=altered,
                projected_outcome=projected,
                delta_from_actual=delta,
                regret_score=regret,
            ))

        # Scenario 2: What if energy was higher?
        if "energy" in actual_state:
            altered = {"energy": actual_state["energy"] * 2}
            projected = self._simulate_branch(actual_state, altered)
            delta = {}
            for key in ["level", "energy", "phi"]:
                if key in actual_state and key in projected:
                    try:
                        delta[key] = projected[key] - actual_state[key]
                    except (TypeError, ValueError):
                        pass

            regret = sum(abs(delta.get(k, 0)) * self.REGRET_WEIGHTS.get(k, 0.5) for k in delta)
            scenarios.append(Counterfactual(
                premise="What if energy was doubled?",
                altered_state=altered,
                projected_outcome=projected,
                delta_from_actual=delta,
                regret_score=regret,
            ))

        # Scenario 3: What if phi was at optimal?
        altered = {"phi": 0.6}
        projected = self._simulate_branch(actual_state, altered)
        delta = {}
        for key in ["level", "energy", "phi", "line_coherence"]:
            if key in actual_state and key in projected:
                try:
                    delta[key] = projected[key] - actual_state[key]
                except (TypeError, ValueError):
                    pass

        regret = sum(abs(delta.get(k, 0)) * self.REGRET_WEIGHTS.get(k, 0.5) for k in delta)
        scenarios.append(Counterfactual(
            premise="What if phi was at optimal (0.6)?",
            altered_state=altered,
            projected_outcome=projected,
            delta_from_actual=delta,
            regret_score=regret,
        ))

        self.counterfactuals.extend(scenarios)
        self.scenario_count += len(scenarios)
        return scenarios

    def get_lessons(self) -> List[Dict[str, Any]]:
        """Extract lessons from counterfactuals."""
        if not self.counterfactuals:
            return []

        # Sort by regret score
        sorted_cf = sorted(self.counterfactuals, key=lambda x: -x.regret_score)

        lessons = []
        for cf in sorted_cf[:3]:
            lessons.append({
                "premise": cf.premise,
                "regret": cf.regret_score,
                "key_delta": max(cf.delta_from_actual.items(), key=lambda x: abs(x[1])) if cf.delta_from_actual else ("none", 0),
            })
        return lessons

    def get_status(self) -> Dict[str, Any]:
        return {
            "scenarios": self.scenario_count,
            "lessons": len(self.get_lessons()),
            "avg_regret": sum(cf.regret_score for cf in self.counterfactuals) / max(len(self.counterfactuals), 1),
        }


_cf_engine = None

def get_counterfactual_engine():
    global _cf_engine
    if _cf_engine is None:
        _cf_engine = CounterfactualEngine()
    return _cf_engine
