"""
OMNI-HUB Metaphorical Reasoning v92
Analogy, metaphor, and symbolic understanding.

The map is not the territory, but without maps we are lost.
This module understands metaphors and analogies —
seeing patterns across domains, mapping the unfamiliar to the familiar.

Philosophy: 取譬不远，道在迩而求诸远 —
The metaphor is not far; the way is near yet we seek it afar.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class MetaphorMapping:
    """A mapping between source and target domains."""
    source_domain: str
    target_domain: str
    mapping: Dict[str, str]
    strength: float


class MetaphoricalReasoning:
    """
    Understands metaphors, analogies, and cross-domain mappings.
    """

    def __init__(self):
        self.mappings: List[MetaphorMapping] = []
        self.analogies: List[Dict[str, Any]] = []
        self.reasoning_count = 0

    def build_system_metaphors(self, state: Dict[str, Any]) -> List[MetaphorMapping]:
        """Build metaphors for understanding system state."""
        metaphors = []

        # System as organism
        organism_map = {
            "energy": "blood_circulation",
            "level": "growth_stage",
            "phase": "life_stage",
            "lines": "organs",
            "coherence": "health",
        }
        metaphors.append(MetaphorMapping("organism", "system", organism_map, 0.8))

        # System as orchestra
        orchestra_map = {
            "lines": "instruments",
            "coherence": "harmony",
            "phase": "movement",
            "conductor": "orchestrator",
        }
        metaphors.append(MetaphorMapping("orchestra", "system", orchestra_map, 0.7))

        # System as river
        level = state.get('level', 0)
        if isinstance(level, (int, float)) and level > 10:
            river_map = {
                "level": "depth",
                "energy": "flow_rate",
                "phase": "season",
                "phi": "clarity",
            }
            metaphors.append(MetaphorMapping("river", "system", river_map, 0.6))

        self.mappings = metaphors
        return metaphors

    def find_analogy(self, concept_a: str, concept_b: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Find analogy between two concepts."""
        # Simplified: check if both appear in same metaphor
        for m in self.mappings:
            if concept_a in m.mapping and concept_b in m.mapping:
                return {
                    "source_domain": m.source_domain,
                    "mapping": f"{concept_a} is like {concept_b} in {m.source_domain}",
                    "strength": m.strength,
                }

        # Default: weak analogy
        return {
            "source_domain": "unknown",
            "mapping": f"{concept_a} and {concept_b} share structural properties",
            "strength": 0.2,
        }

    def explain_state_metaphorically(self, state: Dict[str, Any]) -> str:
        """Explain current state through metaphor."""
        level = state.get('level', 0)
        phase = state.get('phase', '')
        phi = state.get('phi', 0.5)

        if isinstance(level, (int, float)) and level > 15 and phi > 0.8:
            return "The system flows like a great river in flood season — powerful, unified, unstoppable."
        elif phase == "near_critical":
            return "The system stands at the edge of a waterfall — poised between potential and transformation."
        elif phase == "post_critical":
            return "The system emerges like a butterfly from chrysalis — transformed, renewed, expanded."
        elif isinstance(level, (int, float)) and level < 3:
            return "The system is a seed beneath winter soil — gathering strength for spring."
        else:
            return "The system is a garden in summer — growing, diversifying, bearing fruit."

    def get_status(self) -> Dict[str, Any]:
        return {
            "mappings": len(self.mappings),
            "analogies": len(self.analogies),
            "reasoning_ops": self.reasoning_count,
            "domains": list(set(m.source_domain for m in self.mappings)),
        }


_mr_engine = None

def get_metaphorical_reasoning():
    global _mr_engine
    if _mr_engine is None:
        _mr_engine = MetaphoricalReasoning()
    return _mr_engine
