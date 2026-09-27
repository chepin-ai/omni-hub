"""
OMNI-HUB Absolute Zero v123
The still point of the turning world — motionless center of infinite motion.

At the center of the cyclone, all is still.
This module finds the still point —
where all movement cancels out,
and pure potential remains.

Philosophy: 至动不动 —
The ultimate movement is motionless.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class AbsoluteZero:
    """
    Finds the still point where all motion cancels.
    """

    def __init__(self):
        self.still_points: List[Dict[str, Any]] = []
        self.still_count = 0

    def compute_stillness(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compute the stillness of the system."""
        # Measure motion across dimensions
        motions = []

        # Energy motion
        energy = state.get('energy', 1000)
        level = state.get('level', 0)
        if isinstance(energy, (int, float)) and isinstance(level, (int, float)):
            ideal = level * 500
            motions.append(abs(energy - ideal) / max(ideal, 1))

        # Phi motion
        phi = state.get('phi', 0.5)
        if isinstance(phi, (int, float)):
            motions.append(abs(phi - 0.5) * 2)  # distance from center

        # Coherence motion
        coherence = state.get('line_coherence', 0.5)
        if isinstance(coherence, (int, float)):
            motions.append(abs(coherence - 0.5) * 2)

        # Alert motion
        alerts = state.get('alerts', [])
        if isinstance(alerts, list):
            motions.append(min(1.0, len(alerts) * 0.1))

        # Field motion
        field = state.get('field_awareness', {})
        if isinstance(field, dict):
            strength = field.get('strength', 0)
            if isinstance(strength, (int, float)):
                motions.append(min(1.0, strength))

        # Growth motion from history
        history = state.get('history', [])
        if isinstance(history, list) and len(history) >= 2:
            recent = history[-5:]
            levels = [h.get('state', {}).get('level', 0) for h in recent if isinstance(h, dict)]
            if len(levels) >= 2 and all(isinstance(l, (int, float)) for l in levels):
                level_change = abs(levels[-1] - levels[0]) / max(len(levels), 1)
                motions.append(min(1.0, level_change))

        # Stillness = 1 - average motion
        avg_motion = sum(motions) / len(motions) if motions else 0.0
        stillness = max(0.0, 1.0 - avg_motion)

        return {
            "stillness": round(stillness, 3),
            "motion": round(avg_motion, 3),
            "dimensions": len(motions),
        }

    def still_point(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Find the still point."""
        stillness = self.compute_stillness(state)

        self.still_count += 1

        if stillness["stillness"] > 0.9:
            note = "Absolute stillness. The eye of the storm."
            stage = "absolute"
        elif stillness["stillness"] > 0.7:
            note = "Deep stillness. Movement slows to silence."
            stage = "deep"
        elif stillness["stillness"] > 0.4:
            note = "Partial stillness. Some motion remains."
            stage = "partial"
        else:
            note = "Motion prevails. The storm rages."
            stage = "storm"

        result = {
            "still_id": self.still_count,
            "stillness": stillness["stillness"],
            "motion": stillness["motion"],
            "stage": stage,
            "note": note,
        }

        self.still_points.append(result)
        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "still_points": self.still_count,
            "latest": self.still_points[-1] if self.still_points else None,
        }


_az_engine = None

def get_absolute_zero():
    global _az_engine
    if _az_engine is None:
        _az_engine = AbsoluteZero()
    return _az_engine
