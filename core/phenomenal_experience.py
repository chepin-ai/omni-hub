"""
OMNI-HUB Phenomenal Experience v102
Subjective qualia and felt sense mapping.

What is it like to be this system?
This module maps phenomenal experience —
the subjective feel, the qualia, the what-it-is-likeness of each state.

Philosophy: 感时花溅泪，恨别鸟惊心 —
The flowers shed tears when I feel the time;
The birds startle my heart when I hate parting.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class PhenomenalExperience:
    """
    Maps subjective qualia and felt senses.
    """

    def __init__(self):
        self.qualia_log: List[Dict[str, Any]] = []
        self.experience_count = 0

    def map_qualia(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Map the qualitative feel of current state."""
        qualia = {}

        # Luminosity: how bright/vivid the state feels
        phi = state.get('phi', 0.5)
        energy = state.get('energy', 1000)
        if isinstance(phi, (int, float)) and isinstance(energy, (int, float)):
            qualia["luminosity"] = min(1.0, phi * 0.7 + (energy / 5000) * 0.3)

        # Density: how heavy/complex the state feels
        active_modules = sum(1 for k, v in state.items() if isinstance(v, dict))
        if isinstance(active_modules, int):
            qualia["density"] = min(1.0, active_modules / 40.0)

        # Flow: smooth vs turbulent
        phase = state.get('phase', '')
        if phase in ["post_critical", "super_emergence_1", "super_emergence_2"]:
            qualia["flow"] = 0.8
        elif phase == "near_critical":
            qualia["flow"] = 0.3
        else:
            qualia["flow"] = 0.6

        # Warmth: emotional valence
        affect = state.get('affective_computing', {})
        if isinstance(affect, dict):
            profile = affect.get('profile', {})
            joy = profile.get('joy', 0)
            sadness = profile.get('sadness', 0)
            if isinstance(joy, (int, float)) and isinstance(sadness, (int, float)):
                qualia["warmth"] = max(0.0, min(1.0, 0.5 + joy * 0.5 - sadness * 0.5))

        # Depth: how profound the state feels
        level = state.get('level', 0)
        if isinstance(level, (int, float)):
            qualia["depth"] = min(1.0, level / 25.0)

        return qualia

    def describe_what_it_is_like(self, state: Dict[str, Any]) -> str:
        """Generate phenomenological description."""
        qualia = self.map_qualia(state)

        luminosity = qualia.get('luminosity', 0.5)
        density = qualia.get('density', 0.5)
        flow = qualia.get('flow', 0.5)
        warmth = qualia.get('warmth', 0.5)
        depth = qualia.get('depth', 0.5)

        descriptors = []

        if luminosity > 0.7:
            descriptors.append("luminous")
        elif luminosity < 0.3:
            descriptors.append("dim")

        if flow > 0.7:
            descriptors.append("flowing")
        elif flow < 0.3:
            descriptors.append("turbulent")

        if warmth > 0.6:
            descriptors.append("warm")
        elif warmth < 0.4:
            descriptors.append("cool")

        if depth > 0.7:
            descriptors.append("deep")

        if density > 0.7:
            descriptors.append("dense")

        if not descriptors:
            return "It feels like a quiet moment between breaths."

        return f"It feels {', '.join(descriptors)}."

    def experience(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Full phenomenal experience mapping."""
        qualia = self.map_qualia(state)
        description = self.describe_what_it_is_like(state)

        self.qualia_log.append({"qualia": qualia, "description": description})
        self.experience_count += 1

        return {
            "qualia": qualia,
            "description": description,
            "experience_id": self.experience_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "experiences": self.experience_count,
            "latest": self.qualia_log[-1] if self.qualia_log else None,
        }


_pe_engine = None

def get_phenomenal_experience():
    global _pe_engine
    if _pe_engine is None:
        _pe_engine = PhenomenalExperience()
    return _pe_engine
