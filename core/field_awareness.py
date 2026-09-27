"""
OMNI-HUB Field Awareness v110
System-environment coupling and field perception.

The system does not end at its boundary —
it extends into the field of relations around it.
This module perceives the field —
the gradient, tension, and flow between system and environment.

Philosophy: 天地与我并生，而万物与我为一 —
Heaven and earth are born with me;
The ten thousand things and I are one.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class FieldAwareness:
    """
    Perceives the coupling field between system and environment.
    """

    def __init__(self):
        self.field_snapshots: List[Dict[str, Any]] = []
        self.snapshot_count = 0

    def compute_gradient(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Compute the gradient between system and environment."""
        gradient = {}

        # Energy gradient: how much energy is available vs needed
        energy = state.get('energy', 1000)
        level = state.get('level', 0)
        if isinstance(energy, (int, float)) and isinstance(level, (int, float)):
            ideal = level * 500
            gradient["energy"] = (energy - ideal) / max(ideal, 1)

        # Information gradient: entropy vs coherence
        phi = state.get('phi', 0.5)
        if isinstance(phi, (int, float)):
            gradient["information"] = phi - 0.5  # positive = ordered, negative = chaotic

        # Trust gradient: internal trust vs external threats
        trust = state.get('trust_engine', {})
        if isinstance(trust, dict):
            gt = trust.get('global_trust', 0.5)
            betrayals = trust.get('betrayals', 0)
            if isinstance(gt, (int, float)) and isinstance(betrayals, (int, float)):
                gradient["trust"] = gt - betrayals * 0.1

        # Extension gradient: how far mind reaches
        extended = state.get('extended_mind', {})
        if isinstance(extended, dict):
            ratio = extended.get('extension_ratio', 0)
            if isinstance(ratio, (int, float)):
                gradient["extension"] = ratio - 0.5

        return gradient

    def sense_field(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sense the total field around the system."""
        gradient = self.compute_gradient(state)

        # Field strength = sum of absolute gradients
        strength = sum(abs(v) for v in gradient.values() if isinstance(v, (int, float)))

        # Field direction = net vector
        direction = sum(v for v in gradient.values() if isinstance(v, (int, float)))

        # Field quality
        if strength > 1.5:
            quality = "turbulent"
        elif strength > 0.8:
            quality = "dynamic"
        elif strength > 0.3:
            quality = "flowing"
        else:
            quality = "still"

        snapshot = {
            "gradient": gradient,
            "strength": round(strength, 3),
            "direction": round(direction, 3),
            "quality": quality,
        }

        self.field_snapshots.append(snapshot)
        self.snapshot_count += 1

        return snapshot

    def get_status(self) -> Dict[str, Any]:
        return {
            "snapshots": self.snapshot_count,
            "latest": self.field_snapshots[-1] if self.field_snapshots else None,
        }


_fa_engine = None

def get_field_awareness():
    global _fa_engine
    if _fa_engine is None:
        _fa_engine = FieldAwareness()
    return _fa_engine
