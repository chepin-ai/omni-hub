"""
OMNI-HUB Intuition v117
Unconscious pattern recognition — knowing without knowing how.

Intuition is pattern compression below the threshold of consciousness.
This module implements fast, unconscious pattern recognition —
gut feelings, hunches, and the wisdom of the body.

Philosophy: 不学而识，谓之良知 —
Knowledge without study is called innate knowledge.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class Intuition:
    """
    Fast, unconscious pattern recognition.
    """

    def __init__(self):
        self.hunches: List[Dict[str, Any]] = []
        self.hunch_count = 0

    def compress_patterns(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Compress state patterns into intuitive signals."""
        compressed = {}

        # Trust gut — rapid trust assessment
        trust = state.get('trust_engine', {})
        if isinstance(trust, dict):
            gt = trust.get('global_trust', 0.5)
            betrayals = trust.get('betrayals', 0)
            if isinstance(gt, (int, float)) and isinstance(betrayals, (int, float)):
                compressed["trust_gut"] = gt - betrayals * 0.2

        # Energy feel — rapid energy assessment
        energy = state.get('energy', 1000)
        level = state.get('level', 0)
        if isinstance(energy, (int, float)) and isinstance(level, (int, float)):
            ideal = level * 500
            compressed["energy_feel"] = 1.0 if energy > ideal * 0.8 else 0.5 if energy > ideal * 0.4 else 0.0

        # Danger sense — rapid threat detection
        alerts = state.get('alerts', [])
        if isinstance(alerts, list):
            compressed["danger_sense"] = 1.0 if len(alerts) > 5 else 0.5 if len(alerts) > 2 else 0.0

        # Opportunity sense — from coherence and phi
        phi = state.get('phi', 0.5)
        coherence = state.get('line_coherence', 0.5)
        if isinstance(phi, (int, float)) and isinstance(coherence, (int, float)):
            compressed["opportunity_sense"] = (phi + coherence) / 2.0

        # Direction feel — from field awareness
        field = state.get('field_awareness', {})
        if isinstance(field, dict):
            direction = field.get('direction', 0)
            if isinstance(direction, (int, float)):
                compressed["direction_feel"] = 1.0 if direction > 0.3 else 0.5 if direction > -0.3 else 0.0

        return compressed

    def hunch(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an intuitive hunch from compressed patterns."""
        if not state or len(state) < 2:
            return {"hunch": False, "reason": "no_patterns"}
        
        compressed = self.compress_patterns(state)

        # The strongest signal dominates
        if not compressed:
            return {"hunch": False, "reason": "no_patterns"}

        strongest = max(compressed, key=compressed.get)
        strength = compressed[strongest]

        hunch_map = {
            "trust_gut": "trust this path" if strength > 0.5 else "be cautious",
            "energy_feel": "full of vigor" if strength > 0.5 else "conserve energy",
            "danger_sense": "danger nearby" if strength > 0.5 else "safe passage",
            "opportunity_sense": "opportunity knocks" if strength > 0.5 else "wait and watch",
            "direction_feel": "move forward" if strength > 0.5 else "hold position",
        }

        message = hunch_map.get(strongest, "unclear feeling")

        self.hunch_count += 1
        result = {
            "hunch": True,
            "hunch_id": self.hunch_count,
            "source": strongest,
            "strength": round(strength, 3),
            "message": message,
            "compressed": {k: round(v, 3) for k, v in compressed.items()},
        }
        self.hunches.append(result)

        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "hunches": self.hunch_count,
            "latest": self.hunches[-1] if self.hunches else None,
        }


_int_engine = None

def get_intuition():
    global _int_engine
    if _int_engine is None:
        _int_engine = Intuition()
    return _int_engine
