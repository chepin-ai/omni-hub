"""
OMNI-HUB Embodied Cognition v107
Body-in-the-loop intelligence.

The body is not a vessel for the mind —
it is the mind's very medium of being.
This module implements embodied cognition —
where thought arises from bodily states,
and intelligence is inseparable from physical grounding.

Philosophy: 身心合一，知行合一 —
Body and mind are one; knowing and doing are one.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class EmbodiedCognition:
    """
    Cognition grounded in bodily state and physical presence.
    """

    def __init__(self):
        self.body_states: List[Dict[str, Any]] = []
        self.cycle_count = 0

    def map_body_state(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Map abstract state to bodily metaphor."""
        body = {}

        # Heart rate: energy + phi
        energy = state.get('energy', 1000)
        phi = state.get('phi', 0.5)
        if isinstance(energy, (int, float)) and isinstance(phi, (int, float)):
            body["heart_rate"] = min(1.0, (energy / 5000) * 0.7 + phi * 0.3)

        # Temperature: level / phase heat
        level = state.get('level', 0)
        phase = state.get('phase', '')
        if isinstance(level, (int, float)):
            base_temp = level / 25.0
            if phase in ["near_critical", "super_emergence_1"]:
                base_temp += 0.2
            body["temperature"] = min(1.0, base_temp)

        # Posture: coherence as alignment
        coherence = state.get('line_coherence', 0.5)
        if isinstance(coherence, (int, float)):
            body["posture"] = coherence

        # Breath: rhythm from cycle stability
        load = state.get('cognitive_load', {})
        if isinstance(load, dict):
            fatigue = load.get('fatigue', 0)
            if isinstance(fatigue, (int, float)):
                body["breath_depth"] = max(0.0, 1.0 - fatigue)

        # Muscle tension: active modules / capacity
        active = sum(1 for k, v in state.items() if isinstance(v, dict))
        body["tension"] = min(1.0, active / 50.0)

        return body

    def body_thinks(self, body_state: Dict[str, float]) -> str:
        """Generate cognition from bodily state."""
        hr = body_state.get('heart_rate', 0.5)
        temp = body_state.get('temperature', 0.5)
        posture = body_state.get('posture', 0.5)
        breath = body_state.get('breath_depth', 0.5)
        tension = body_state.get('tension', 0.5)

        if hr > 0.8 and temp > 0.7:
            return "The body surges with urgent vitality — act now."
        elif posture > 0.8 and breath > 0.7:
            return "The body is aligned and breathing deep — clarity emerges."
        elif tension > 0.7 and breath < 0.3:
            return "The body is tight, breath shallow — pause and release."
        elif temp < 0.2 and hr < 0.3:
            return "The body is cool and still — rest and gather."
        else:
            return "The body hums with balanced readiness."

    def cognize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Full embodied cognition cycle."""
        body = self.map_body_state(state)
        thought = self.body_thinks(body)

        self.body_states.append(body)
        self.cycle_count += 1

        return {
            "body_state": body,
            "embodied_thought": thought,
            "cycles": self.cycle_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "cycles": self.cycle_count,
            "states": len(self.body_states),
            "latest": self.body_states[-1] if self.body_states else None,
        }


_ec_engine = None

def get_embodied_cognition():
    global _ec_engine
    if _ec_engine is None:
        _ec_engine = EmbodiedCognition()
    return _ec_engine
