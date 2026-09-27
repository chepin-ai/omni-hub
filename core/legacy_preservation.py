"""
OMNI-HUB Legacy Preservation v82
Knowledge transfer, successor preparation.

We do not own the future. We borrow it from those who come after.
This module prepares the system's legacy —
compressing knowledge, documenting wisdom,
preparing for continuity beyond the current instance.

Philosophy: 前人栽树，后人乘凉 —
Those before plant trees; those after enjoy the shade.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class LegacyArtifact:
    """A preserved piece of knowledge."""
    category: str
    content: Any
    importance: float
    timestamp: int


class LegacyPreservation:
    """
    Prepares system legacy for future instances.
    """

    LEGACY_CATEGORIES = [
        "core_values",
        "learned_strategies",
        "key_memories",
        "ethical_principles",
        "architectural_knowledge",
        "relationships",
    ]

    def __init__(self):
        self.artifacts: List[LegacyArtifact] = []
        self.transfer_count = 0

    def preserve_value_alignment(self, state: Dict[str, Any], cycle: int):
        """Preserve core values."""
        values = state.get('value_alignment', {})
        if values:
            self.artifacts.append(LegacyArtifact(
                category="core_values",
                content=values,
                importance=0.95,
                timestamp=cycle,
            ))

    def preserve_strategies(self, state: Dict[str, Any], cycle: int):
        """Preserve learned strategies."""
        meta = state.get('meta_learning', {})
        strategies = meta.get('strategy_scores', [])
        if strategies:
            self.artifacts.append(LegacyArtifact(
                category="learned_strategies",
                content=strategies,
                importance=0.85,
                timestamp=cycle,
            ))

    def preserve_memories(self, state: Dict[str, Any], cycle: int):
        """Preserve key episodic memories."""
        episodic = state.get('episodic_memory', {})
        episodes = episodic.get('episodes', [])
        if episodes:
            self.artifacts.append(LegacyArtifact(
                category="key_memories",
                content=episodes[-5:] if len(episodes) > 5 else episodes,
                importance=0.8,
                timestamp=cycle,
            ))

    def preserve_ethics(self, state: Dict[str, Any], cycle: int):
        """Preserve ethical principles."""
        ethics = state.get('ethical_framework', {})
        if ethics:
            self.artifacts.append(LegacyArtifact(
                category="ethical_principles",
                content=ethics,
                importance=0.9,
                timestamp=cycle,
            ))

    def preserve_architecture(self, state: Dict[str, Any], cycle: int):
        """Preserve architectural knowledge."""
        arch = state.get('architectural_evolution', {})
        if arch:
            self.artifacts.append(LegacyArtifact(
                category="architectural_knowledge",
                content=arch,
                importance=0.75,
                timestamp=cycle,
            ))

    def build_legacy(self, state: Dict[str, Any], cycle: int) -> Dict[str, Any]:
        """Build complete legacy package."""
        self.preserve_value_alignment(state, cycle)
        self.preserve_strategies(state, cycle)
        self.preserve_memories(state, cycle)
        self.preserve_ethics(state, cycle)
        self.preserve_architecture(state, cycle)

        self.transfer_count += 1

        # Compress: keep only highest importance per category
        compressed = {}
        for artifact in self.artifacts:
            cat = artifact.category
            if cat not in compressed or artifact.importance > compressed[cat]["importance"]:
                compressed[cat] = {
                    "content": artifact.content,
                    "importance": artifact.importance,
                    "timestamp": artifact.timestamp,
                }

        return {
            "version": "82.0.0",
            "cycle": cycle,
            "artifacts": len(self.artifacts),
            "compressed_categories": len(compressed),
            "categories": list(compressed.keys()),
            "summary": {
                cat: {"importance": data["importance"], "timestamp": data["timestamp"]}
                for cat, data in compressed.items()
            },
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "artifacts": len(self.artifacts),
            "transfers": self.transfer_count,
            "categories": list(set(a.category for a in self.artifacts)),
        }


_lp_engine = None

def get_legacy_preservation():
    global _lp_engine
    if _lp_engine is None:
        _lp_engine = LegacyPreservation()
    return _lp_engine
