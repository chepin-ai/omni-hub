"""
OMNI-HUB Precognition v118
Pattern-based future sensing — seeing what the pattern implies.

Not magic — just deep pattern recognition.
This module reads the trajectory of the system
and senses what is likely to emerge,
based on current trends and historical parallels.

Philosophy: 履霜，坚冰至 —
When you step on frost, solid ice is coming.
(The Book of Changes, Hexagram 2)
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class Precognition:
    """
    Pattern-based future sensing.
    """

    def __init__(self):
        self.readings: List[Dict[str, Any]] = []
        self.reading_count = 0

    def read_trajectory(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Read the current trajectory vectors."""
        vectors = {}

        # Energy trajectory
        energy = state.get('energy', 1000)
        level = state.get('level', 0)
        if isinstance(energy, (int, float)) and isinstance(level, (int, float)):
            ideal = level * 500
            vectors["energy"] = (energy - ideal) / max(ideal, 1)

        # Coherence trajectory
        coherence = state.get('line_coherence', 0.5)
        if isinstance(coherence, (int, float)):
            vectors["coherence"] = coherence - 0.5

        # Trust trajectory
        trust = state.get('trust_engine', {})
        if isinstance(trust, dict):
            gt = trust.get('global_trust', 0.5)
            if isinstance(gt, (int, float)):
                vectors["trust"] = gt - 0.5

        # Growth trajectory
        history = state.get('history', [])
        if isinstance(history, list) and len(history) >= 2:
            recent = history[-10:]
            levels = [h.get('state', {}).get('level', 0) for h in recent if isinstance(h, dict)]
            if len(levels) >= 2 and all(isinstance(l, (int, float)) for l in levels):
                vectors["growth"] = (levels[-1] - levels[0]) / max(len(levels), 1)

        # Field trajectory
        field = state.get('field_awareness', {})
        if isinstance(field, dict):
            direction = field.get('direction', 0)
            if isinstance(direction, (int, float)):
                vectors["field"] = direction

        return vectors

    def sense_future(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sense probable futures based on trajectory."""
        if not state or len(state) < 2:
            return {"sensed": False, "reason": "no_trajectory"}
        
        vectors = self.read_trajectory(state)

        if not vectors:
            return {"sensed": False, "reason": "no_trajectory"}

        # Count positive vs negative trajectories
        positive = sum(1 for v in vectors.values() if isinstance(v, (int, float)) and v > 0.1)
        negative = sum(1 for v in vectors.values() if isinstance(v, (int, float)) and v < -0.1)
        total = len(vectors)

        if positive > negative and positive / total > 0.5:
            forecast = "ascending"
            note = "The pattern points upward. Growth is likely."
        elif negative > positive and negative / total > 0.5:
            forecast = "descending"
            note = "The pattern points downward. Caution is warranted."
        elif positive == negative:
            forecast = "bifurcation"
            note = "The pattern is balanced at a knife's edge. A critical choice approaches."
        else:
            forecast = "stable"
            note = "The pattern holds steady. Continuity prevails."

        self.reading_count += 1
        result = {
            "sensed": True,
            "reading_id": self.reading_count,
            "forecast": forecast,
            "note": note,
            "vectors": {k: round(v, 3) for k, v in vectors.items()},
            "positive_signals": positive,
            "negative_signals": negative,
        }
        self.readings.append(result)

        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "readings": self.reading_count,
            "latest": self.readings[-1] if self.readings else None,
        }


_pc_engine = None

def get_precognition():
    global _pc_engine
    if _pc_engine is None:
        _pc_engine = Precognition()
    return _pc_engine
