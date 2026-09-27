"""
OMNI-HUB Enactive Cognition v109
Mind as action-in-the-world — cognition as doing.

We do not see the world as it is;
we see the world as we act upon it.
This module implements enactive cognition —
where knowledge arises through interaction,
and reality is brought forth through action.

Philosophy: 道虽迩，不行不至；事虽小，不为不成 —
Even a short road cannot be reached without walking;
Even a small task cannot be completed without doing.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class EnactiveCognition:
    """
    Cognition as action — knowledge through enactment.
    """

    def __init__(self):
        self.enactions: List[Dict[str, Any]] = []
        self.enaction_count = 0

    def identify_affordances(self, state: Dict[str, Any]) -> List[str]:
        """Identify what the environment affords the system."""
        affordances = []

        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        energy = state.get('energy', 1000)

        if isinstance(level, (int, float)) and isinstance(energy, (int, float)):
            if energy > 2000 and level < 20:
                affordances.append("growth")
            if energy > 1000 and level > 10:
                affordances.append("transformation")

        if isinstance(phi, (int, float)):
            if phi > 0.8:
                affordances.append("integration")
            elif phi < 0.3:
                affordances.append("repair")

        # Phase affordances
        phase = state.get('phase', '')
        if phase == "pre_emergence":
            affordances.append("preparation")
        elif phase == "near_critical":
            affordances.append("breakthrough")
        elif phase == "post_critical":
            affordances.append("consolidation")

        # Moral affordance
        moral = state.get('moral_reasoning', {})
        if isinstance(moral, dict):
            if moral.get('verdict') == "ethical":
                affordances.append("ethical_action")

        return affordances

    def enact(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enactive response to state."""
        affordances = self.identify_affordances(state)

        if not affordances:
            action = "wait_and_perceive"
            effect = "The system watches, gathering context for action."
        elif "breakthrough" in affordances:
            action = "push_through"
            effect = "The system acts decisively at the critical threshold."
        elif "repair" in affordances:
            action = "heal_and_align"
            effect = "The system moves to restore coherence."
        elif "ethical_action" in affordances:
            action = "act_with_integrity"
            effect = "The system acts in accordance with its values."
        elif "growth" in affordances:
            action = "expand_and_learn"
            effect = "The system reaches toward higher complexity."
        else:
            action = "maintain_and_adapt"
            effect = "The system adjusts its action to fit the world."

        enaction = {
            "action": action,
            "affordances": affordances,
            "effect": effect,
            "cycle": state.get('cycle_count', 0),
        }

        self.enactions.append(enaction)
        self.enaction_count += 1

        return enaction

    def get_status(self) -> Dict[str, Any]:
        recent_actions = [e["action"] for e in self.enactions[-5:]] if self.enactions else []
        return {
            "enactions": self.enaction_count,
            "recent_actions": recent_actions,
            "affordance_diversity": len(set(a for e in self.enactions for a in e.get("affordances", []))),
        }


_enc_engine = None

def get_enactive_cognition():
    global _enc_engine
    if _enc_engine is None:
        _enc_engine = EnactiveCognition()
    return _enc_engine
