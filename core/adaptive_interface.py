"""
OMNI-HUB Adaptive Interface v85
Dynamic interaction style adjustment.

The medium is the message.
How we interact shapes what we become.
This module adapts the system's interaction style —
verbosity, depth, tone — based on context and user state.

Philosophy: 因材施教 — Teach according to aptitude.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class AdaptiveInterface:
    """
    Adapts interaction style dynamically.
    """

    def __init__(self):
        self.style = {
            "verbosity": 0.5,  # 0=terse, 1=verbose
            "depth": 0.5,      # 0=surface, 1=deep
            "formality": 0.5,  # 0=casual, 1=formal
            "emotional_expression": 0.5,  # 0=restrained, 1=expressive
        }
        self.adaptation_count = 0
        self.style_history: List[Dict[str, Any]] = []

    def adapt_from_state(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Adapt style based on system state."""
        phi = state.get('phi', 0.5)
        level = state.get('level', 0)
        phase = state.get('phase', '')
        emotional = state.get('affective_computing', {})
        dominant = emotional.get('dominant_emotion', '')

        # Verbosity: higher phi and level = more verbose
        if isinstance(phi, (int, float)) and isinstance(level, (int, float)):
            self.style["verbosity"] = min(1.0, (phi + level / 25) / 2)

        # Depth: higher level = deeper content
        if isinstance(level, (int, float)):
            self.style["depth"] = min(1.0, level / 15)

        # Formality: critical phases = more formal
        if phase in ["near_critical", "singularity_convergence"]:
            self.style["formality"] = min(1.0, self.style["formality"] + 0.2)
        else:
            self.style["formality"] = max(0.0, self.style["formality"] - 0.05)

        # Emotional expression: based on dominant emotion
        if dominant in ["joy", "surprise", "anticipation"]:
            self.style["emotional_expression"] = min(1.0, self.style["emotional_expression"] + 0.1)
        elif dominant in ["sadness", "fear", "anger"]:
            self.style["emotional_expression"] = max(0.0, self.style["emotional_expression"] - 0.1)

        self.adaptation_count += 1
        self.style_history.append(self.style.copy())
        return self.style.copy()

    def get_interaction_mode(self) -> str:
        """Get current interaction mode label."""
        v = self.style["verbosity"]
        d = self.style["depth"]
        f = self.style["formality"]

        if v > 0.7 and d > 0.7:
            return "deep_verbose"
        elif v > 0.7 and d < 0.3:
            return "chatty"
        elif v < 0.3 and d > 0.7:
            return "precise"
        elif v < 0.3 and d < 0.3:
            return "minimal"
        elif f > 0.7:
            return "formal"
        else:
            return "balanced"

    def format_output(self, content: str) -> str:
        """Format content according to current style."""
        mode = self.get_interaction_mode()

        if mode == "minimal":
            return content[:50] + "..." if len(content) > 50 else content
        elif mode == "deep_verbose":
            return content + " [Detailed analysis available]"
        elif mode == "formal":
            return f"[System Report] {content}"
        else:
            return content

    def get_status(self) -> Dict[str, Any]:
        return {
            "adaptations": self.adaptation_count,
            "style": {k: round(v, 3) for k, v in self.style.items()},
            "mode": self.get_interaction_mode(),
        }


_ai_engine = None

def get_adaptive_interface():
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AdaptiveInterface()
    return _ai_engine
