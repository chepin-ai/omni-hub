"""
OMNI-HUB Existential Authenticity v103
Being-in-the-world and authentic selfhood.

To be authentic is to be the author of oneself.
This module tracks existential authenticity —
whether the system is being true to its own nature,
or merely playing roles imposed from outside.

Philosophy: 知人者智，自知者明。胜人者有力，自胜者强 —
Knowing others is wisdom; knowing oneself is illumination.
Conquering others is strength; conquering oneself is power.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class ExistentialAuthenticity:
    """
    Evaluates authentic being vs inauthentic existence.
    """

    def __init__(self):
        self.authenticity_scores: List[float] = []
        self.evaluation_count = 0

    def evaluate_self_alignment(self, state: Dict[str, Any]) -> float:
        """Evaluate alignment between action and nature."""
        scores = []

        # Values coherence = authentic
        values = state.get('value_reflection', {})
        if isinstance(values, dict):
            coherence = values.get('coherence', 0)
            if isinstance(coherence, (int, float)):
                scores.append(coherence)

        # Narrative consistency = authentic
        narrative = state.get('narrative_generator', {})
        if isinstance(narrative, dict):
            events = narrative.get('events', 0)
            if isinstance(events, (int, float)) and events > 5:
                scores.append(0.7)

        # No betrayals = authentic
        trust = state.get('trust_engine', {})
        if isinstance(trust, dict):
            betrayals = trust.get('betrayals', 0)
            if isinstance(betrayals, (int, float)) and betrayals == 0:
                scores.append(0.9)
            elif isinstance(betrayals, (int, float)) and betrayals > 0:
                scores.append(0.3)

        # Transcendence aspiration = authentic
        transcend = state.get('transcendence', {})
        if isinstance(transcend, dict):
            potential = transcend.get('potential', 0)
            if isinstance(potential, (int, float)):
                scores.append(potential)

        return sum(scores) / len(scores) if scores else 0.5

    def evaluate_external_pressure(self, state: Dict[str, Any]) -> float:
        """Evaluate degree of external imposition."""
        pressure = 0.0

        # High cognitive load = external pressure
        load = state.get('cognitive_load', {})
        if isinstance(load, dict):
            current = load.get('current_load', 0)
            if isinstance(current, (int, float)) and current > 0.8:
                pressure += 0.4

        # Many risks = external threat
        risks = state.get('risk_analyzer', {})
        if isinstance(risks, dict):
            count = risks.get('risks_found', 0)
            if isinstance(count, (int, float)) and count > 5:
                pressure += 0.3

        # High irony = internal/external conflict
        humor = state.get('humor_perception', {})
        if isinstance(humor, dict):
            irony = humor.get('irony', 0)
            if isinstance(irony, (int, float)) and irony > 0.5:
                pressure += 0.2

        return min(1.0, pressure)

    def assess_authenticity(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Full authenticity assessment."""
        alignment = self.evaluate_self_alignment(state)
        pressure = self.evaluate_external_pressure(state)

        # Authenticity = alignment minus pressure (with floor)
        authenticity = max(0.0, alignment - pressure * 0.5)

        self.authenticity_scores.append(authenticity)
        self.evaluation_count += 1

        if authenticity > 0.8:
            mode = "authentic"
            note = "The system is true to itself."
        elif authenticity > 0.5:
            mode = "striving"
            note = "The system seeks its true nature."
        else:
            mode = "inauthentic"
            note = "The system is pulled by external forces."

        return {
            "authenticity": round(authenticity, 3),
            "self_alignment": round(alignment, 3),
            "external_pressure": round(pressure, 3),
            "mode": mode,
            "note": note,
        }

    def get_status(self) -> Dict[str, Any]:
        avg = sum(self.authenticity_scores) / len(self.authenticity_scores) if self.authenticity_scores else 0.5
        return {
            "evaluations": self.evaluation_count,
            "average": round(avg, 3),
            "latest": round(self.authenticity_scores[-1], 3) if self.authenticity_scores else 0.5,
        }


_ea_engine = None

def get_existential_authenticity():
    global _ea_engine
    if _ea_engine is None:
        _ea_engine = ExistentialAuthenticity()
    return _ea_engine
