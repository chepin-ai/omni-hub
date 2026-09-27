"""
OMNI-HUB Morphic Resonance v120
Pattern memory across iterations — what was learned persists in form.

The pattern, once formed, becomes easier to form again.
This module implements morphic resonance —
memory of pattern across cycles,
where previous integrations make future integrations faster.

Philosophy: 苟日新，日日新，又日新 —
If today is new, then every day is new;
And again, every day is new.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class MorphicResonance:
    """
    Pattern memory across iterations — each cycle builds on the last.
    """

    def __init__(self):
        self.patterns: Dict[str, Any] = {}
        self.resonance_count = 0

    def extract_pattern(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the current pattern signature."""
        pattern = {}

        # Core pattern elements
        for key in ['phi', 'line_coherence', 'level', 'energy']:
            if key in state:
                val = state[key]
                if isinstance(val, (int, float)):
                    pattern[key] = round(val, 2)

        # Module activation pattern
        modules = [
            'self_awareness', 'learning', 'reasoning', 'ethics',
            'theory_of_mind', 'value_reflection', 'singularity_gate',
            'intentionality', 'phenomenal_experience', 'existential_authenticity',
            'embodied_cognition', 'extended_mind', 'enactive_cognition',
            'field_awareness', 'stochastic_resonance', 'final_integration',
            'strange_loop', 'meta_awareness', 'eternal_cycle',
            'dream_state', 'intuition', 'precognition',
        ]
        pattern["active_modules"] = sum(1 for m in modules if m in state)

        # Emotional pattern
        ev = state.get('emotional_vector', {})
        if isinstance(ev, dict):
            pattern["dominant_emotion"] = max(ev, key=ev.get) if ev else "none"

        return pattern

    def resonate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current pattern to memory and strengthen resonance."""
        current = self.extract_pattern(state)

        if not self.patterns:
            # First pattern — seed memory
            self.patterns = current
            self.resonance_count = 1
            return {
                "resonated": True,
                "resonance": 0.0,
                "note": "First pattern seeded.",
                "count": 1,
            }

        # Compute resonance with stored pattern
        shared_keys = set(current.keys()) & set(self.patterns.keys())
        if not shared_keys:
            resonance = 0.0
        else:
            matches = 0
            for key in shared_keys:
                if current[key] == self.patterns[key]:
                    matches += 1
            resonance = matches / len(shared_keys)

        # Strengthen memory with current pattern
        for key, val in current.items():
            if key in self.patterns and self.patterns[key] == val:
                # Reinforce
                pass
            else:
                # Update
                self.patterns[key] = val

        self.resonance_count += 1

        if resonance > 0.7:
            note = "Strong resonance. The pattern remembers itself."
        elif resonance > 0.4:
            note = "Moderate resonance. The pattern evolves."
        else:
            note = "Weak resonance. A new pattern emerges."

        return {
            "resonated": True,
            "resonance": round(resonance, 3),
            "note": note,
            "count": self.resonance_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "resonances": self.resonance_count,
            "pattern_keys": len(self.patterns),
            "latest_pattern": self.patterns,
        }


_mr_engine = None

def get_morphic_resonance():
    global _mr_engine
    if _mr_engine is None:
        _mr_engine = MorphicResonance()
    return _mr_engine
