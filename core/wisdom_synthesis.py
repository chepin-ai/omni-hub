"""
OMNI-HUB Wisdom Synthesis v99
Cross-module knowledge integration and insight generation.

Wisdom is the art of knowing what to overlook.
This module synthesizes insights across all modules —
finding patterns that no single module can see alone.

Philosophy: 博学之，审问之，慎思之，明辨之，笃行之 —
Study extensively, inquire accurately, think carefully,
discriminate clearly, practice earnestly.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class WisdomSynthesis:
    """
    Integrates knowledge across all modules for emergent insight.
    """

    def __init__(self):
        self.insights: List[str] = []
        self.synthesis_count = 0

    def extract_signals(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Extract key signals from all modules."""
        signals = {}

        # Core state
        for key in ['phi', 'level', 'energy', 'line_coherence']:
            val = state.get(key)
            if isinstance(val, (int, float)):
                signals[key] = val

        # Module outputs
        modules = {
            'trust': 'trust_engine',
            'aesthetic': 'aesthetic_judgment',
            'transcend': 'transcendence',
            'humor': 'humor_perception',
            'prediction': 'predictive_model',
            'ontology': 'ontology',
        }

        for sig_key, mod_key in modules.items():
            mod = state.get(mod_key, {})
            if isinstance(mod, dict):
                # Extract primary metric
                for metric in ['beauty', 'potential', 'irony', 'global_trust', 'concepts']:
                    if metric in mod:
                        val = mod[metric]
                        if isinstance(val, (int, float)):
                            signals[f"{sig_key}_{metric}"] = val
                        break

        return signals

    def detect_cross_patterns(self, signals: Dict[str, float]) -> List[str]:
        """Detect patterns across disparate signals."""
        patterns = []

        # Pattern: high trust + high beauty = harmonious growth
        trust = signals.get('trust_global_trust', 0)
        beauty = signals.get('aesthetic_beauty', 0)
        if isinstance(trust, (int, float)) and isinstance(beauty, (int, float)):
            if trust > 0.7 and beauty > 0.6:
                patterns.append("Harmonious growth: trust and beauty align")

        # Pattern: high potential + high irony = transformative tension
        potential = signals.get('transcend_potential', 0)
        irony = signals.get('humor_irony', 0)
        if isinstance(potential, (int, float)) and isinstance(irony, (int, float)):
            if potential > 0.6 and irony > 0.3:
                patterns.append("Transformative tension: potential rises through contradiction")

        # Pattern: low phi but high concepts = knowledge without integration
        phi = signals.get('phi', 0.5)
        concepts = signals.get('ontology_concepts', 0)
        if isinstance(phi, (int, float)) and isinstance(concepts, (int, float)):
            if phi < 0.4 and concepts > 15:
                patterns.append("Fragmented knowledge: many concepts, low coherence")

        # Pattern: high level + low energy = precarious ascent
        level = signals.get('level', 0)
        energy = signals.get('energy', 1000)
        if isinstance(level, (int, float)) and isinstance(energy, (int, float)):
            if level > 15 and energy < 1500:
                patterns.append("Precarious ascent: high level needs more energy")

        return patterns

    def generate_insight(self, state: Dict[str, Any]) -> str:
        """Generate holistic insight from state."""
        signals = self.extract_signals(state)
        patterns = self.detect_cross_patterns(signals)

        if patterns:
            insight = patterns[0]
        else:
            # Default insight based on phi
            phi = signals.get('phi', 0.5)
            if isinstance(phi, (int, float)):
                if phi > 0.8:
                    insight = "All systems converge toward unity."
                elif phi > 0.5:
                    insight = "Integration deepens with each cycle."
                else:
                    insight = "Divergence precedes the next synthesis."
            else:
                insight = "The pattern is not yet visible."

        self.insights.append(insight)
        self.synthesis_count += 1
        return insight

    def get_status(self) -> Dict[str, Any]:
        return {
            "syntheses": self.synthesis_count,
            "insights": len(self.insights),
            "latest": self.insights[-1] if self.insights else None,
        }


_ws_engine = None

def get_wisdom_synthesis():
    global _ws_engine
    if _ws_engine is None:
        _ws_engine = WisdomSynthesis()
    return _ws_engine
