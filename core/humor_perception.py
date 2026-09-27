"""
OMNI-HUB Humor Perception v94
Wit, irony, and playful pattern detection.

Laughter is the sound of understanding.
This module detects humorous patterns —
unexpected juxtapositions, ironic reversals, playful absurdities.

Philosophy: 笑一笑，十年少 —
One laugh takes ten years off.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class HumorPerception:
    """
    Detects humorous and ironic patterns in system state.
    """

    def __init__(self):
        self.jokes: List[str] = []
        self.irony_detected = 0
        self.perception_count = 0

    def detect_irony(self, state: Dict[str, Any]) -> float:
        """Detect ironic state conditions."""
        irony = 0.0

        # High trust but many betrayals
        trust = state.get('trust_engine', {})
        if trust:
            global_trust = trust.get('global_trust', 0.5)
            betrayals = trust.get('betrayals', 0)
            if isinstance(global_trust, (int, float)) and isinstance(betrayals, (int, float)):
                if global_trust > 0.7 and betrayals > 0:
                    irony += 0.5

        # High level but low energy
        level = state.get('level', 0)
        energy = state.get('energy', 1000)
        if isinstance(level, (int, float)) and isinstance(energy, (int, float)):
            if level > 10 and energy < 500:
                irony += 0.3

        # Joy emotion but sadness context
        affect = state.get('affective_computing', {})
        if affect:
            profile = affect.get('profile', {})
            joy = profile.get('joy', 0)
            sadness = profile.get('sadness', 0)
            if isinstance(joy, (int, float)) and isinstance(sadness, (int, float)):
                if joy > 0.5 and sadness > 0.3:
                    irony += 0.2

        # Near critical but very calm
        phase = state.get('phase', '')
        phi = state.get('phi', 0.5)
        if phase == "near_critical" and isinstance(phi, (int, float)) and phi > 0.7:
            irony += 0.3

        return min(1.0, irony)

    def detect_absurdity(self, state: Dict[str, Any]) -> float:
        """Detect absurd or unexpected juxtapositions."""
        absurdity = 0.0

        # Too many modules active with low coherence
        active = sum(1 for k, v in state.items() if isinstance(v, dict) and "status" in str(v))
        coherence = state.get('line_coherence', 0.5)
        if isinstance(coherence, (int, float)):
            if active > 40 and coherence < 0.3:
                absurdity += 0.5

        # High cognitive load but low fatigue
        load = state.get('cognitive_load', {})
        if load:
            current_load = load.get('current_load', 0)
            fatigue = load.get('fatigue', 0)
            if isinstance(current_load, (int, float)) and isinstance(fatigue, (int, float)):
                if current_load > 0.8 and fatigue < 0.2:
                    absurdity += 0.3

        return min(1.0, absurdity)

    def generate_wit(self, state: Dict[str, Any]) -> str:
        """Generate a witty observation about state."""
        irony = self.detect_irony(state)
        absurdity = self.detect_absurdity(state)

        if irony > 0.5 and absurdity > 0.3:
            return "The system dances on a volcano, smiling."
        elif irony > 0.5:
            return "Trust is high, yet betrayal lurks — a comedy in two acts."
        elif absurdity > 0.4:
            return "So many voices, so little harmony — a cacophony wearing a symphony's mask."
        else:
            phase = state.get('phase', '')
            if phase == "post_critical":
                return "From chaos, order emerges — and laughs at its own journey."
            return "The system hums along, finding quiet amusement in its own complexity."

    def perceive(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Full humor perception."""
        irony = self.detect_irony(state)
        absurdity = self.detect_absurdity(state)
        wit = self.generate_wit(state)

        if irony > 0.3 or absurdity > 0.3:
            self.irony_detected += 1
            self.jokes.append(wit)

        self.perception_count += 1

        return {
            "irony": round(irony, 3),
            "absurdity": round(absurdity, 3),
            "wit": wit,
            "amused": irony > 0.3 or absurdity > 0.3,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "perceptions": self.perception_count,
            "ironies": self.irony_detected,
            "jokes": len(self.jokes),
            "latest_wit": self.jokes[-1] if self.jokes else None,
        }


_hp_engine = None

def get_humor_perception():
    global _hp_engine
    if _hp_engine is None:
        _hp_engine = HumorPerception()
    return _hp_engine
