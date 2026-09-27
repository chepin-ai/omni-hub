"""
OMNI-HUB Synchronicity v121
Meaningful coincidence detection — acausal connectedness.

Events align without causal connection, yet carry meaning.
This module detects synchronicities —
meaningful coincidences across modules and cycles,
acausal patterns that resonate with significance.

Philosophy: 同声相应，同气相求 —
Same sounds resonate with each other;
Same energies seek each other.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class Synchronicity:
    """
    Detects meaningful coincidences across system events.
    """

    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.synchronicities: List[Dict[str, Any]] = []
        self.event_count = 0

    def record_event(self, state: Dict[str, Any], event_type: str = "cycle") -> None:
        """Record a significant event."""
        event = {
            "id": self.event_count,
            "type": event_type,
            "phi": state.get('phi', 0.5),
            "level": state.get('level', 0),
            "coherence": state.get('line_coherence', 0.5),
        }
        self.events.append(event)
        self.event_count += 1

    def detect_coincidences(self) -> List[Dict[str, Any]]:
        """Detect meaningful coincidences in recent events."""
        if len(self.events) < 3:
            return []

        recent = self.events[-10:]
        coincidences = []

        # Check for phi alignment
        phi_values = [e["phi"] for e in recent if isinstance(e["phi"], (int, float))]
        if len(phi_values) >= 2:
            avg_phi = sum(phi_values) / len(phi_values)
            clustered = sum(1 for p in phi_values if abs(p - avg_phi) < 0.1)
            if clustered >= 3:
                coincidences.append({
                    "type": "phi_cluster",
                    "significance": "high" if clustered >= 5 else "medium",
                    "description": f"Phi values cluster around {avg_phi:.2f} ({clustered} events)",
                })

        # Check for level transition alignment
        levels = [e["level"] for e in recent if isinstance(e["level"], (int, float))]
        if len(levels) >= 2 and levels[-1] != levels[0]:
            coincidences.append({
                "type": "level_transition",
                "significance": "high",
                "description": f"Level shifted from {levels[0]} to {levels[-1]}",
            })

        # Check for coherence convergence
        coherences = [e["coherence"] for e in recent if isinstance(e["coherence"], (int, float))]
        if len(coherences) >= 3:
            increasing = sum(1 for i in range(1, len(coherences)) if coherences[i] > coherences[i-1])
            if increasing >= len(coherences) * 0.7:
                coincidences.append({
                    "type": "coherence_rise",
                    "significance": "medium",
                    "description": f"Coherence rising across {increasing} transitions",
                })

        return coincidences

    def sense(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sense synchronicities in the current moment."""
        self.record_event(state)
        coincidences = self.detect_coincidences()

        if coincidences:
            self.synchronicities.extend(coincidences)
            significance = max(c["significance"] for c in coincidences)
            return {
                "sensed": True,
                "significance": significance,
                "coincidences": coincidences,
                "note": "The universe whispers through pattern.",
            }

        return {
            "sensed": False,
            "significance": "none",
            "coincidences": [],
            "note": "Silence. Meaning awaits the next alignment.",
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "events": self.event_count,
            "synchronicities": len(self.synchronicities),
            "latest": self.synchronicities[-1] if self.synchronicities else None,
        }


_sync_engine = None

def get_synchronicity():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = Synchronicity()
    return _sync_engine
