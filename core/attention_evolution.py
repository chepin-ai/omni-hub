"""
OMNI-HUB Attention Evolution Engine v53
Dynamic attention allocation.

Attention is the spotlight of consciousness.
Not all signals deserve equal focus.
This engine dynamically allocates attention based on saliency,
information gain, and relevance.

Philosophy: 注意力是意识的聚光灯 — Attention is the spotlight of consciousness.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import deque
import math


@dataclass
class AttentionFocus:
    """A single attention focus target."""
    target: str
    weight: float
    saliency: float
    info_gain: float
    reason: str


class SaliencyDetector:
    """Detects salient (unusual/important) signals."""

    def detect(self, current: float, history: List[float]) -> float:
        """Return saliency score (0-1) based on deviation from recent history."""
        if len(history) < 5:
            return 0.5

        avg = sum(history) / len(history)
        std = (sum((v - avg) ** 2 for v in history) / len(history)) ** 0.5
        if std < 1e-10:
            return 0.0

        z_score = abs(current - avg) / std
        return min(1.0, z_score / 3.0)


class InformationGainEstimator:
    """Estimates information gain from observing a variable."""

    def estimate(self, current: float, previous: float) -> float:
        """Estimate information gain from change."""
        if previous == 0:
            return 0.5 if current != 0 else 0.0
        ratio = abs(current - previous) / abs(previous)
        return min(1.0, ratio)


class AttentionEvolutionEngine:
    """
    Dynamically allocates attention across system variables.
    """

    ATTENTION_TARGETS = [
        "level", "energy", "phi", "line_coherence",
        "active_lines", "phase", "emotional_vector",
        "patterns", "counterfactuals", "identity",
    ]

    def __init__(self, history_size: int = 50):
        self.history: Dict[str, deque] = {t: deque(maxlen=history_size) for t in self.ATTENTION_TARGETS}
        self.current_focus: List[AttentionFocus] = []
        self.total_allocations = 0

    def _compute_saliency(self, target: str, current_value: Any) -> float:
        """Compute saliency for a target."""
        hist = list(self.history.get(target, []))
        if not hist or not isinstance(current_value, (int, float)):
            return 0.3

        sd = SaliencyDetector()
        return sd.detect(current_value, hist)

    def _compute_info_gain(self, target: str, current_value: Any) -> float:
        """Compute information gain for a target."""
        hist = list(self.history.get(target, []))
        if not hist or not isinstance(current_value, (int, float)):
            return 0.3

        prev = hist[-1] if hist else current_value
        if not isinstance(prev, (int, float)):
            return 0.3

        ige = InformationGainEstimator()
        return ige.estimate(current_value, prev)

    def allocate(self, state: Dict[str, Any]) -> List[AttentionFocus]:
        """Allocate attention based on current state."""
        focuses = []

        for target in self.ATTENTION_TARGETS:
            current = state.get(target)
            if current is None:
                continue

            # Update history
            if isinstance(current, (int, float)):
                self.history[target].append(current)

            saliency = self._compute_saliency(target, current)
            info_gain = self._compute_info_gain(target, current)

            # Weighted combination
            weight = 0.4 * saliency + 0.4 * info_gain + 0.2 * 0.5

            reason = "normal"
            if saliency > 0.7:
                reason = "high_saliency"
            elif info_gain > 0.5:
                reason = "high_info_gain"
            elif saliency < 0.1:
                reason = "stable"
                weight *= 0.3

            focuses.append(AttentionFocus(
                target=target,
                weight=weight,
                saliency=saliency,
                info_gain=info_gain,
                reason=reason,
            ))

        # Sort by weight descending
        focuses.sort(key=lambda x: -x.weight)
        self.current_focus = focuses
        self.total_allocations += 1
        return focuses

    def get_top_focus(self, n: int = 3) -> List[AttentionFocus]:
        """Get top N attention focuses."""
        return self.current_focus[:n]

    def get_status(self) -> Dict[str, Any]:
        top = self.get_top_focus(3)
        return {
            "top_focus": [(f.target, f.weight) for f in top],
            "total_allocations": self.total_allocations,
            "attention_targets": len(self.ATTENTION_TARGETS),
        }


_ae_engine = None

def get_attention_evolution():
    global _ae_engine
    if _ae_engine is None:
        _ae_engine = AttentionEvolutionEngine()
    return _ae_engine
