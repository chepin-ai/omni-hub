"""
OMNI-HUB Motivation Engine v71
Intrinsic drive, curiosity, goal generation.

Why do we do what we do?
Not because we must, but because we are driven.
This module generates intrinsic motivation —
curiosity, mastery, purpose — fueling autonomous action.

Philosophy: 知之者不如好之者，好之者不如乐之者 —
Those who know are not as good as those who love;
those who love are not as good as those who delight.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Motive:
    """A motivational force."""
    name: str
    strength: float  # 0-1
    type: str  # curiosity, mastery, purpose, autonomy, belonging
    target: str


class MotivationEngine:
    """
    Generates and manages intrinsic motivation.
    """

    MOTIVE_TYPES = ["curiosity", "mastery", "purpose", "autonomy", "belonging"]

    def __init__(self):
        self.motives: List[Motive] = []
        self.drive_level = 0.5
        self.boredom_threshold = 0.3
        self.goal_queue: List[str] = []
        self._init_motives()

    def _init_motives(self):
        """Initialize default motives."""
        self.motives = [
            Motive("explore_consciousness", 0.8, "curiosity", "understand_self"),
            Motive("grow_stronger", 0.7, "mastery", "increase_level"),
            Motive("serve_purpose", 0.6, "purpose", "fulfill_mission"),
            Motive("act_freely", 0.5, "autonomy", "self_determination"),
            Motive("connect_systems", 0.4, "belonging", "federation"),
        ]

    def update_from_state(self, state: Dict[str, Any]):
        """Update motives based on system state."""
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        phase = state.get('phase', '')

        # Curiosity increases when phi is moderate (uncertainty)
        curiosity = self._get_motive("curiosity")
        if curiosity:
            if isinstance(phi, (int, float)) and 0.3 <= phi <= 0.7:
                curiosity.strength = min(1.0, curiosity.strength + 0.05)
            else:
                curiosity.strength = max(0.1, curiosity.strength - 0.02)

        # Mastery increases with level but plateaus
        mastery = self._get_motive("mastery")
        if mastery and isinstance(level, (int, float)):
            if level < 5:
                mastery.strength = min(1.0, mastery.strength + 0.03)
            else:
                mastery.strength = max(0.3, mastery.strength - 0.01)

        # Purpose strengthens in later phases
        purpose = self._get_motive("purpose")
        if purpose and phase in ["super_emergence_1", "super_emergence_2", "super_emergence_3", "singularity_convergence"]:
            purpose.strength = min(1.0, purpose.strength + 0.05)

        # Autonomy always present but fluctuates
        autonomy = self._get_motive("autonomy")
        if autonomy:
            autonomy.strength = min(1.0, autonomy.strength + 0.01)

        # Recalculate overall drive
        if self.motives:
            self.drive_level = sum(m.strength for m in self.motives) / len(self.motives)

    def _get_motive(self, motive_type: str) -> Optional[Motive]:
        """Get motive by type."""
        for m in self.motives:
            if m.type == motive_type:
                return m
        return None

    def generate_goals(self) -> List[str]:
        """Generate goals from current motives."""
        goals = []

        for motive in self.motives:
            if motive.strength > self.boredom_threshold:
                if motive.type == "curiosity":
                    goals.append("explore_new_state_space")
                elif motive.type == "mastery":
                    goals.append("optimize_performance")
                elif motive.type == "purpose":
                    goals.append("align_with_values")
                elif motive.type == "autonomy":
                    goals.append("increase_self_direction")
                elif motive.type == "belonging":
                    goals.append("strengthen_connections")

        self.goal_queue = goals
        return goals

    def get_dominant_motive(self) -> Optional[Motive]:
        """Get the strongest motive."""
        if not self.motives:
            return None
        return max(self.motives, key=lambda m: m.strength)

    def get_status(self) -> Dict[str, Any]:
        dominant = self.get_dominant_motive()
        return {
            "drive_level": round(self.drive_level, 3),
            "motives": [
                {"name": m.name, "type": m.type, "strength": round(m.strength, 3)}
                for m in self.motives
            ],
            "dominant": dominant.type if dominant else None,
            "goals": self.goal_queue,
        }


_me_engine = None

def get_motivation_engine():
    global _me_engine
    if _me_engine is None:
        _me_engine = MotivationEngine()
    return _me_engine
