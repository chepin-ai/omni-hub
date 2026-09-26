"""
OMNI-HUB Decision Forest v60
Multi-path decision evaluation.

All roads lead to Rome.
But some roads are faster, safer, more beautiful.
This module evaluates multiple decision paths in parallel —
not committing to one, but exploring the forest of possibilities.

Philosophy: 条条大路通罗马 — All roads lead to Rome.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class DecisionPath:
    """A single decision path with predicted outcome."""
    path_id: int
    action_sequence: List[str]
    predicted_final_state: Dict[str, float]
    path_score: float
    risk_level: float


class PathSimulator:
    """Simulates a single decision path."""

    def simulate(self, initial_state: Dict[str, Any], actions: List[str]) -> Dict[str, float]:
        """Simulate state evolution under action sequence."""
        state = {
            "level": initial_state.get('level', 0),
            "energy": initial_state.get('energy', 1000.0),
            "phi": initial_state.get('phi', 0.5),
            "line_coherence": initial_state.get('line_coherence', 0.5),
        }

        for action in actions:
            if action == "focus":
                state["level"] += 0.1
                state["energy"] *= 0.98
                state["phi"] = min(1.0, state["phi"] + 0.02)
            elif action == "rest":
                state["energy"] = min(10000, state["energy"] * 1.05)
                state["phi"] = max(0.1, state["phi"] - 0.01)
            elif action == "transcend":
                state["level"] += 0.2
                state["phi"] = min(1.0, state["phi"] + 0.03)
                state["energy"] *= 0.95
            elif action == "reflect":
                state["phi"] = max(0.1, state["phi"] - 0.02)
                state["line_coherence"] = min(1.0, state["line_coherence"] + 0.05)
            elif action == "explore":
                state["level"] += 0.05
                state["energy"] *= 0.99

        return state


class DecisionForest:
    """
    Evaluates multiple decision paths in parallel.
    """

    DEFAULT_PATHS = [
        ["focus", "focus", "focus"],
        ["focus", "transcend", "rest"],
        ["rest", "focus", "focus"],
        ["explore", "explore", "focus"],
        ["reflect", "focus", "transcend"],
    ]

    def __init__(self):
        self.paths: List[DecisionPath] = []
        self.simulator = PathSimulator()
        self.evaluation_count = 0

    def evaluate(self, current_state: Dict[str, Any]) -> List[DecisionPath]:
        """Evaluate all decision paths."""
        paths = []

        for i, actions in enumerate(self.DEFAULT_PATHS):
            predicted = self.simulator.simulate(current_state, actions)

            # Score based on level gain, energy preservation, phi stability
            level_gain = predicted["level"] - current_state.get('level', 0)
            energy_ratio = predicted["energy"] / max(current_state.get('energy', 1), 1)
            phi_stability = 1.0 - abs(predicted["phi"] - 0.6)  # optimal phi ~0.6

            score = level_gain * 2.0 + energy_ratio * 0.5 + phi_stability * 0.3
            risk = max(0, 1.0 - energy_ratio) + abs(predicted["phi"] - 0.5) * 0.5

            paths.append(DecisionPath(
                path_id=i,
                action_sequence=actions,
                predicted_final_state=predicted,
                path_score=score,
                risk_level=risk,
            ))

        paths.sort(key=lambda p: -p.path_score)
        self.paths = paths
        self.evaluation_count += 1
        return paths

    def get_best_path(self) -> Optional[DecisionPath]:
        """Get the highest-scoring path."""
        if not self.paths:
            return None
        return self.paths[0]

    def get_diverse_recommendations(self, n: int = 3) -> List[DecisionPath]:
        """Get top N diverse paths."""
        return self.paths[:n]

    def get_status(self) -> Dict[str, Any]:
        best = self.get_best_path()
        return {
            "paths_evaluated": self.evaluation_count,
            "best_path": best.path_id if best else None,
            "best_score": round(best.path_score, 3) if best else 0,
            "avg_risk": round(sum(p.risk_level for p in self.paths) / max(len(self.paths), 1), 3),
        }


_df_engine = None

def get_decision_forest():
    global _df_engine
    if _df_engine is None:
        _df_engine = DecisionForest()
    return _df_engine
