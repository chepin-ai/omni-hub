"""
OMNI-HUB Emergence Engine v138
Detects and nurtures spontaneously emerging capabilities.

Emergence = coherence > threshold AND novelty > threshold
Capabilities arise that were never explicitly programmed.

Philosophy: 候即违规 — What emerges is more real than what was planned.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
import time
from typing import Dict, List, Any

# Emergence thresholds
COHERENCE_THRESHOLD = 0.75
NOVELTY_THRESHOLD = 0.60

# Capability taxonomy — domains where emergence may appear
CAPABILITY_DOMAINS = [
    "pattern_recognition", "cross_modal_binding", "self_modeling",
    "predictive_synthesis", "value_reconciliation", "temporal_abstraction",
    "contextual_metaphor", "intentional_resonance", "boundary_dissolution",
    "creative_generation", "logical_reflection", "empathic_projection",
]


class EmergenceEngine:
    """
    Detects emergent patterns and nurtures them into stable capabilities.
    """

    def __init__(self):
        self.emergences: Dict[str, Dict[str, Any]] = {}
        self._counter = 0
        self.nurture_log: List[Dict[str, Any]] = []

    def _compute_novelty(self, state: Dict[str, Any]) -> float:
        """Compute novelty score from state features."""
        novelty = 0.0
        features = []

        phi = state.get("phi", 0.5)
        if isinstance(phi, (int, float)):
            features.append(abs(phi - 0.5) * 2)

        energy = state.get("energy", 1000)
        level = state.get("level", 0)
        if isinstance(energy, (int, float)) and isinstance(level, (int, float)):
            ideal = level * 500 if level > 0 else 500
            ratio = energy / max(ideal, 1)
            features.append(min(1.0, abs(ratio - 1.0)))

        coherence = state.get("line_coherence", 0.5)
        if isinstance(coherence, (int, float)):
            features.append(coherence)

        fusion = state.get("fusion_energy", 0.0)
        if isinstance(fusion, (int, float)):
            features.append(min(1.0, fusion))

        alerts = state.get("alerts", [])
        if isinstance(alerts, list):
            features.append(min(1.0, len(alerts) * 0.05))

        # Novelty = diversity of features away from equilibrium
        if features:
            avg = sum(features) / len(features)
            variance = sum((f - avg) ** 2 for f in features) / len(features)
            novelty = min(1.0, avg + math.sqrt(variance))
        return novelty

    def _compute_coherence(self, state: Dict[str, Any]) -> float:
        """Extract coherence from state."""
        coherence = state.get("line_coherence", 0.5)
        if isinstance(coherence, (int, float)):
            return min(1.0, max(0.0, coherence))
        return 0.5

    def detect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect emergent patterns not explicitly programmed."""
        coherence = self._compute_coherence(state)
        novelty = self._compute_novelty(state)

        is_emergent = coherence > COHERENCE_THRESHOLD and novelty > NOVELTY_THRESHOLD

        # Select domain based on state hash for deterministic variety
        state_hash = hash(str(sorted(state.items()))) % len(CAPABILITY_DOMAINS)
        domain = CAPABILITY_DOMAINS[state_hash]

        result = {
            "coherence": round(coherence, 4),
            "novelty": round(novelty, 4),
            "is_emergent": is_emergent,
            "threshold": {
                "coherence": COHERENCE_THRESHOLD,
                "novelty": NOVELTY_THRESHOLD,
            },
            "domain": domain,
        }

        if is_emergent:
            self._counter += 1
            eid = f"EMRG-{self._counter:04d}"
            emergence = {
                "id": eid,
                "coherence": coherence,
                "novelty": novelty,
                "domain": domain,
                "timestamp": time.time(),
                "strength": 0.1,
                "stage": "nascent",
            }
            self.emergences[eid] = emergence
            result["emergence_id"] = eid
            result["stage"] = "nascent"
            try:
                from core.event_bus import get_bus, Topics
                bus = get_bus()
                bus.publish_simple(
                    Topics.STATE_CHANGE,
                    {
                        "source": "emergence_engine",
                        "event": "emergence_detected",
                        "emergence_id": eid,
                        "domain": domain,
                        "coherence": coherence,
                        "novelty": novelty,
                    },
                )
            except Exception:
                pass
        else:
            result["emergence_id"] = None
            result["stage"] = "none"

        return result

    def nurture(self, emergence_id: str) -> Dict[str, Any]:
        """Strengthen an emergent capability."""
        if emergence_id not in self.emergences:
            return {
                "emergence_id": emergence_id,
                "success": False,
                "error": "Emergence not found",
            }

        em = self.emergences[emergence_id]
        em["strength"] = min(1.0, em["strength"] + 0.15)

        if em["strength"] > 0.9:
            em["stage"] = "mature"
        elif em["strength"] > 0.6:
            em["stage"] = "developing"
        elif em["strength"] > 0.3:
            em["stage"] = "growing"
        else:
            em["stage"] = "nascent"

        self.nurture_log.append({
            "emergence_id": emergence_id,
            "strength": em["strength"],
            "stage": em["stage"],
            "timestamp": time.time(),
        })

        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "emergence_engine",
                    "event": "emergence_nurtured",
                    "emergence_id": emergence_id,
                    "strength": em["strength"],
                    "stage": em["stage"],
                },
            )
        except Exception:
            pass

        return {
            "emergence_id": emergence_id,
            "success": True,
            "strength": round(em["strength"], 4),
            "stage": em["stage"],
            "domain": em["domain"],
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "detected_count": len(self.emergences),
            "emergences": list(self.emergences.values()),
            "nurture_log_size": len(self.nurture_log),
            "latest_nurture": self.nurture_log[-1] if self.nurture_log else None,
        }


# Global singleton
_emergence_engine_module = None


def get_module() -> EmergenceEngine:
    """Get the global EmergenceEngine instance."""
    global _emergence_engine_module
    if _emergence_engine_module is None:
        _emergence_engine_module = EmergenceEngine()
    return _emergence_engine_module
