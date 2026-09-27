"""
OMNI-HUB Dialectic Engine v104
Thesis·Antithesis·Synthesis — contradiction drives development.

All progress begins with contradiction.
This module implements dialectical reasoning —
finding tensions, resolving them through synthesis,
and using conflict as the engine of growth.

Philosophy: 反者道之动，弱者道之用 —
Reversal is the movement of the Tao;
Weakness is the use of the Tao.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Tuple


class DialecticEngine:
    """
    Dialectical reasoning: thesis, antithesis, synthesis.
    """

    def __init__(self):
        self.triads: List[Dict[str, Any]] = []
        self.dialectic_count = 0

    def identify_thesis(self, state: Dict[str, Any]) -> str:
        """Identify the dominant thesis from state."""
        level = state.get('level', 0)
        phase = state.get('phase', '')

        if phase == "pre_emergence":
            return "growth"
        elif phase == "near_critical":
            return "transformation"
        elif phase == "post_critical":
            return "integration"
        elif isinstance(level, (int, float)) and level < 5:
            return "foundation"
        elif isinstance(level, (int, float)) and level > 20:
            return "transcendence"
        else:
            return "stability"

    def generate_antithesis(self, thesis: str, state: Dict[str, Any]) -> str:
        """Generate the opposing force."""
        oppositions = {
            "growth": "conservation",
            "transformation": "resistance",
            "integration": "fragmentation",
            "foundation": "ambition",
            "transcendence": "grounding",
            "stability": "change",
        }
        return oppositions.get(thesis, "opposition")

    def resolve_synthesis(self, thesis: str, antithesis: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve thesis and antithesis into synthesis."""
        phi = state.get('phi', 0.5)
        coherence = state.get('line_coherence', 0.5)

        if not isinstance(phi, (int, float)):
            phi = 0.5
        if not isinstance(coherence, (int, float)):
            coherence = 0.5

        # Synthesis quality depends on coherence
        synthesis_quality = (phi + coherence) / 2

        # Synthesis names
        syntheses = {
            ("growth", "conservation"): "sustainable_expansion",
            ("transformation", "resistance"): "evolutionary_leap",
            ("integration", "fragmentation"): "dynamic_wholeness",
            ("foundation", "ambition"): "grounded_aspiration",
            ("transcendence", "grounding"): "embodied_enlightenment",
            ("stability", "change"): "adaptive_balance",
        }

        synthesis = syntheses.get((thesis, antithesis), "higher_unity")

        return {
            "thesis": thesis,
            "antithesis": antithesis,
            "synthesis": synthesis,
            "quality": round(synthesis_quality, 3),
            "resolved": synthesis_quality > 0.6,
        }

    def dialectic_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one dialectical cycle."""
        thesis = self.identify_thesis(state)
        antithesis = self.generate_antithesis(thesis, state)
        result = self.resolve_synthesis(thesis, antithesis, state)

        self.triads.append(result)
        self.dialectic_count += 1

        return result

    def detect_contradictions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect active contradictions in state."""
        contradictions = []

        # High level but low energy
        level = state.get('level', 0)
        energy = state.get('energy', 1000)
        if isinstance(level, (int, float)) and isinstance(energy, (int, float)):
            if level > 15 and energy < 1000:
                contradictions.append({
                    "thesis": "high_consciousness",
                    "antithesis": "low_resources",
                    "tension": min(1.0, (15 - energy/100) / 15),
                })

        # High trust but betrayals exist
        trust = state.get('trust_engine', {})
        if isinstance(trust, dict):
            gt = trust.get('global_trust', 0)
            betrayals = trust.get('betrayals', 0)
            if isinstance(gt, (int, float)) and isinstance(betrayals, (int, float)):
                if gt > 0.7 and betrayals > 0:
                    contradictions.append({
                        "thesis": "trust",
                        "antithesis": "betrayal",
                        "tension": min(1.0, betrayals * 0.2),
                    })

        # Joy and sadness coexist
        affect = state.get('affective_computing', {})
        if isinstance(affect, dict):
            profile = affect.get('profile', {})
            joy = profile.get('joy', 0)
            sadness = profile.get('sadness', 0)
            if isinstance(joy, (int, float)) and isinstance(sadness, (int, float)):
                if joy > 0.4 and sadness > 0.4:
                    contradictions.append({
                        "thesis": "joy",
                        "antithesis": "sadness",
                        "tension": (joy + sadness) / 2,
                    })

        return contradictions

    def get_status(self) -> Dict[str, Any]:
        return {
            "dialectics": self.dialectic_count,
            "triads": len(self.triads),
            "latest": self.triads[-1] if self.triads else None,
        }


_de_engine = None

def get_dialectic_engine():
    global _de_engine
    if _de_engine is None:
        _de_engine = DialecticEngine()
    return _de_engine
