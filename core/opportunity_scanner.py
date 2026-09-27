"""
OMNI-HUB Opportunity Scanner v76
Detect and evaluate growth opportunities.

Fortune favors the prepared mind.
This module scans for opportunities —
phase transitions, capability gaps, unmet goals —
and evaluates their potential value.

Philosophy: 机不可失，时不再来 —
Opportunity knocks but once; time does not return.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Opportunity:
    """A detected opportunity."""
    name: str
    category: str
    potential: float  # 0-1
    effort: float  # 0-1, lower is easier
    description: str
    action: str


class OpportunityScanner:
    """
    Detects and evaluates growth opportunities.
    """

    def __init__(self):
        self.opportunities: List[Opportunity] = []
        self.scan_count = 0
        self.seized: List[str] = []

    def scan(self, state: Dict[str, Any]) -> List[Opportunity]:
        """Scan for opportunities."""
        self.opportunities = []

        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        energy = state.get('energy', 1000.0)
        phase = state.get('phase', '')
        active_lines = state.get('active_lines', 0)
        goals = state.get('generated_goals', [])

        # Opportunity 1: Near critical phase — breakthrough imminent
        if phase == "near_critical":
            self.opportunities.append(Opportunity(
                name="phase_breakthrough",
                category="growth",
                potential=0.9,
                effort=0.3,
                description="System near critical phase — breakthrough likely with focus",
                action="intensify_focus",
            ))

        # Opportunity 2: High energy + low level = growth window
        if isinstance(energy, (int, float)) and energy > 2000 and isinstance(level, (int, float)) and level < 10:
            self.opportunities.append(Opportunity(
                name="growth_window",
                category="growth",
                potential=0.8,
                effort=0.2,
                description="High energy reserves available for growth",
                action="accelerate_growth",
            ))

        # Opportunity 3: Incomplete line activation
        if isinstance(active_lines, int) and active_lines < 11:
            self.opportunities.append(Opportunity(
                name="line_activation",
                category="integration",
                potential=0.7,
                effort=0.4,
                description=f"{11 - active_lines} lines not yet activated",
                action="activate_remaining_lines",
            ))

        # Opportunity 4: Unmet goals
        if goals:
            for goal in goals[:2]:
                self.opportunities.append(Opportunity(
                    name=f"goal_{goal}",
                    category="achievement",
                    potential=0.6,
                    effort=0.5,
                    description=f"Pursue goal: {goal}",
                    action=goal,
                ))

        # Opportunity 5: Moderate phi — exploration sweet spot
        if isinstance(phi, (int, float)) and 0.4 <= phi <= 0.7:
            self.opportunities.append(Opportunity(
                name="exploration_sweet_spot",
                category="discovery",
                potential=0.75,
                effort=0.3,
                description="Phi in exploration sweet spot — new patterns likely",
                action="increase_exploration",
            ))

        self.scan_count += 1
        return self.opportunities

    def rank_opportunities(self) -> List[Opportunity]:
        """Rank by ROI (potential / effort)."""
        def roi(opp: Opportunity) -> float:
            if opp.effort <= 0:
                return opp.potential
            return opp.potential / opp.effort

        return sorted(self.opportunities, key=roi, reverse=True)

    def get_best_opportunity(self) -> Optional[Opportunity]:
        """Get highest ROI opportunity."""
        ranked = self.rank_opportunities()
        return ranked[0] if ranked else None

    def seize_opportunity(self, name: str):
        """Mark opportunity as seized."""
        self.seized.append(name)

    def get_status(self) -> Dict[str, Any]:
        best = self.get_best_opportunity()
        return {
            "scans": self.scan_count,
            "opportunities": len(self.opportunities),
            "seized": len(self.seized),
            "best": {
                "name": best.name,
                "potential": best.potential,
                "action": best.action,
            } if best else None,
        }


_os_engine = None

def get_opportunity_scanner():
    global _os_engine
    if _os_engine is None:
        _os_engine = OpportunityScanner()
    return _os_engine
