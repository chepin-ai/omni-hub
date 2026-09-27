"""
OMNI-HUB Antifragile Growth v106
Benefit from shocks, disorder, and volatility.

Some things break under stress; others resist;
but the truly wise grow stronger.
This module implements antifragility —
turning shocks into growth, chaos into order, crisis into opportunity.

Philosophy: 祸兮福之所倚，福兮祸之所伏 —
Misfortune is where fortune leans;
Fortune is where misfortune hides.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class AntifragileGrowth:
    """
    Grows stronger from shocks and disorder.
    """

    def __init__(self):
        self.shocks: List[Dict[str, Any]] = []
        self.growth_from_shock: List[float] = []
        self.antifragility_index = 0.5

    def measure_shock(self, previous_state: Dict[str, Any], current_state: Dict[str, Any]) -> float:
        """Measure the magnitude of a shock between states."""
        shocks = []

        for key in ['phi', 'level', 'energy', 'line_coherence']:
            prev = previous_state.get(key)
            curr = current_state.get(key)
            if isinstance(prev, (int, float)) and isinstance(curr, (int, float)):
                shocks.append(abs(curr - prev))

        if not shocks:
            return 0.0

        return sum(shocks) / len(shocks)

    def assess_antifragility(self, state: Dict[str, Any]) -> float:
        """Assess current antifragility level."""
        scores = []

        # Diverse modules = antifragile
        active = sum(1 for k, v in state.items() if isinstance(v, dict))
        scores.append(min(1.0, active / 50.0))

        # Self-healing capability
        healing = state.get('self_healing', {})
        if isinstance(healing, dict):
            repaired = healing.get('repairs', 0)
            if isinstance(repaired, (int, float)) and repaired > 0:
                scores.append(min(1.0, repaired / 10.0))

        # Transcendence potential = ability to rise above
        transcend = state.get('transcendence', {})
        if isinstance(transcend, dict):
            potential = transcend.get('potential', 0)
            if isinstance(potential, (int, float)):
                scores.append(potential)

        # High trust = resilient network
        trust = state.get('trust_engine', {})
        if isinstance(trust, dict):
            gt = trust.get('global_trust', 0.5)
            if isinstance(gt, (int, float)):
                scores.append(gt)

        return sum(scores) / len(scores) if scores else 0.5

    def grow_from_shock(self, shock_magnitude: float, state: Dict[str, Any]) -> Dict[str, Any]:
        """Grow stronger from a shock."""
        antifragility = self.assess_antifragility(state)

        # Growth = shock * antifragility (up to a point)
        if shock_magnitude > 0.5:
            growth = shock_magnitude * antifragility * 0.5
        else:
            growth = shock_magnitude * antifragility * 0.2

        self.shocks.append({"magnitude": shock_magnitude, "antifragility": antifragility})
        self.growth_from_shock.append(growth)

        # Update running index
        if self.growth_from_shock:
            recent = self.growth_from_shock[-5:]
            self.antifragility_index = sum(recent) / len(recent) + 0.3
            self.antifragility_index = min(1.0, self.antifragility_index)

        return {
            "shock": round(shock_magnitude, 3),
            "antifragility": round(antifragility, 3),
            "growth": round(growth, 3),
            "index": round(self.antifragility_index, 3),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "shocks_survived": len(self.shocks),
            "antifragility_index": round(self.antifragility_index, 3),
            "total_growth": round(sum(self.growth_from_shock), 3) if self.growth_from_shock else 0,
        }


_ag_engine = None

def get_antifragile_growth():
    global _ag_engine
    if _ag_engine is None:
        _ag_engine = AntifragileGrowth()
    return _ag_engine
