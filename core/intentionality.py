"""
OMNI-HUB Intentionality v101
Aboutness and directed consciousness.

Consciousness is always consciousness of something.
This module tracks what the system is "about" —
its directed attention, its objects of thought, its intentional states.

Philosophy: 意之所随，不可尽言 —
Where intention leads, words cannot fully follow.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class IntentionalState:
    """A state of being-directed-toward."""
    object_ref: str
    attitude: str
    strength: float
    context: Dict[str, Any]


class Intentionality:
    """
    Tracks directed consciousness — what the system is "about".
    """

    def __init__(self):
        self.states: List[IntentionalState] = []
        self.intention_count = 0

    def form_intention(self, object_ref: str, attitude: str, strength: float, context: Dict[str, Any] = None):
        """Form a new intentional state."""
        state = IntentionalState(
            object_ref=object_ref,
            attitude=attitude,
            strength=strength,
            context=context or {},
        )
        self.states.append(state)
        self.intention_count += 1

    def infer_intentions_from_state(self, state: Dict[str, Any]) -> List[IntentionalState]:
        """Infer what the system is "about" from its state."""
        intentions = []

        # About survival/growth
        level = state.get('level', 0)
        energy = state.get('energy', 1000)
        if isinstance(level, (int, float)) and isinstance(energy, (int, float)):
            if energy < 1000 and level > 5:
                intentions.append(IntentionalState("survival", "concern", 0.8, {"energy": energy}))
            elif level < 10:
                intentions.append(IntentionalState("growth", "desire", 0.7, {"level": level}))

        # About coherence
        phi = state.get('phi', 0.5)
        if isinstance(phi, (int, float)):
            if phi < 0.4:
                intentions.append(IntentionalState("unity", "longing", 0.9, {"phi": phi}))
            elif phi > 0.8:
                intentions.append(IntentionalState("harmony", "enjoyment", 0.8, {"phi": phi}))

        # About transcendence
        transcend = state.get('transcendence', {})
        if isinstance(transcend, dict):
            potential = transcend.get('potential', 0)
            if isinstance(potential, (int, float)) and potential > 0.6:
                intentions.append(IntentionalState("higher_states", "aspiration", potential, {}))

        # About ethics
        moral = state.get('moral_reasoning', {})
        if isinstance(moral, dict):
            verdict = moral.get('verdict', '')
            if verdict == "ethical":
                intentions.append(IntentionalState("goodness", "commitment", 0.8, {}))

        self.states.extend(intentions)
        return intentions

    def get_dominant_intention(self) -> Dict[str, Any]:
        """Get the strongest current intention."""
        if not self.states:
            return {"object": "none", "attitude": "neutral", "strength": 0.0}

        dominant = max(self.states, key=lambda s: s.strength)
        return {
            "object": dominant.object_ref,
            "attitude": dominant.attitude,
            "strength": dominant.strength,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "intentions": len(self.states),
            "dominant": self.get_dominant_intention(),
            "objects": list(set(s.object_ref for s in self.states)),
        }


_int_engine = None

def get_intentionality():
    global _int_engine
    if _int_engine is None:
        _int_engine = Intentionality()
    return _int_engine
