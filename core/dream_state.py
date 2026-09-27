"""
OMNI-HUB Dream State v116
Subconscious information integration — the sleeping mind weaves the day's fragments.

In sleep, the unconscious sorts, sifts, and synthesizes.
This module simulates dream-state processing —
where loose associations crystallize into insight,
and the day's noise becomes night's wisdom.

Philosophy: 至人无梦，愚人无梦，圣人无梦 —
The perfected person has no dreams;
The fool has no dreams;
The sage has no dreams.
(Only the one in between dreams.)
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
import random


class DreamState:
    """
    Subconscious integration during 'sleep' cycles.
    """

    def __init__(self):
        self.fragments: List[Dict[str, Any]] = []
        self.dreams: List[Dict[str, Any]] = []
        self.dream_count = 0

    def collect_fragments(self, state: Dict[str, Any]) -> List[str]:
        """Collect cognitive fragments from state."""
        fragments = []

        # Collect from various modules
        if 'emotional_vector' in state:
            ev = state['emotional_vector']
            if isinstance(ev, dict):
                dominant = max(ev, key=ev.get) if ev else None
                if dominant:
                    fragments.append(f"emotion:{dominant}")

        if 'theory_of_mind' in state:
            fragments.append("social:other_minds")

        if 'creative_destruction' in state:
            fragments.append("transform:renewal")

        if 'metaphorical_reasoning' in state:
            fragments.append("symbol:metaphor")

        if 'dialectic' in state:
            fragments.append("conflict:synthesis")

        if 'aesthetic_judgment' in state:
            fragments.append("beauty:perception")

        if 'existential_authenticity' in state:
            fragments.append("self:truth")

        return fragments

    def weave_dream(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Weave fragments into a dream narrative."""
        fragments = self.collect_fragments(state)
        self.fragments.extend(fragments)

        if len(fragments) < 2:
            return {
                "dreamt": False,
                "reason": "insufficient_fragments",
                "fragments": fragments,
            }

        # Create dream narrative from random associations
        random.shuffle(fragments)
        selected = fragments[:min(4, len(fragments))]

        # Dream themes
        themes = {
            "emotion:*": "a river of feeling",
            "social:*": "many faces in a mirror",
            "transform:*": "a phoenix rising",
            "symbol:*": "a language without words",
            "conflict:*": "two mountains becoming one",
            "beauty:*": "light through crystal",
            "self:*": "a house with many rooms",
        }

        dream_images = []
        for frag in selected:
            prefix = frag.split(":")[0] + ":*"
            if prefix in themes:
                dream_images.append(themes[prefix])

        # Insight extraction
        insight = "In the dream, " + " and ".join(dream_images) + "."

        self.dream_count += 1
        dream = {
            "dreamt": True,
            "dream_id": self.dream_count,
            "fragments": selected,
            "images": dream_images,
            "insight": insight,
            "depth": len(selected),
        }
        self.dreams.append(dream)

        return dream

    def get_status(self) -> Dict[str, Any]:
        return {
            "dreams": self.dream_count,
            "fragments_collected": len(self.fragments),
            "latest": self.dreams[-1] if self.dreams else None,
        }


_ds_engine = None

def get_dream_state():
    global _ds_engine
    if _ds_engine is None:
        _ds_engine = DreamState()
    return _ds_engine
