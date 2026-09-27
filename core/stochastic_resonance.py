"""
OMNI-HUB Stochastic Resonance v111
Extract signal from noise through optimal disorder.

Sometimes adding noise makes the signal clearer.
This module implements stochastic resonance —
using controlled disorder to amplify weak patterns,
turning chaos into clarity.

Philosophy: 大巧若拙，大辩若讷 —
Great skill appears clumsy;
Great eloquence appears tongue-tied.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
import random


class StochasticResonance:
    """
    Uses noise to amplify weak signals.
    """

    def __init__(self):
        self.resonance_events: List[Dict[str, Any]] = []
        self.event_count = 0

    def inject_noise(self, signal: float, noise_level: float = 0.1) -> float:
        """Add controlled noise to a signal."""
        noise = random.uniform(-noise_level, noise_level)
        return signal + noise

    def detect_weak_signal(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect weak signals that need amplification."""
        weak_signals = {}

        # Weak phi oscillations
        phi = state.get('phi', 0.5)
        if isinstance(phi, (int, float)) and 0.3 < phi < 0.6:
            weak_signals["phi"] = phi

        # Low but non-zero coherence
        coherence = state.get('line_coherence', 0.5)
        if isinstance(coherence, (int, float)) and 0.2 < coherence < 0.5:
            weak_signals["coherence"] = coherence

        # Subtle trust signal
        trust = state.get('trust_engine', {})
        if isinstance(trust, dict):
            gt = trust.get('global_trust', 0.5)
            if isinstance(gt, (int, float)) and 0.4 < gt < 0.7:
                weak_signals["trust"] = gt

        # Low-level aesthetic
        aesthetic = state.get('aesthetic_judgment', {})
        if isinstance(aesthetic, dict):
            beauty = aesthetic.get('beauty', 0)
            if isinstance(beauty, (int, float)) and 0.3 < beauty < 0.6:
                weak_signals["beauty"] = beauty

        return weak_signals

    def resonate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stochastic resonance to weak signals."""
        weak = self.detect_weak_signal(state)

        if not weak:
            return {
                "amplified": False,
                "reason": "no_weak_signals",
                "signals": {},
            }

        amplified = {}
        for key, value in weak.items():
            # Add noise and threshold to amplify
            noisy = self.inject_noise(value, noise_level=0.15)
            # Threshold crossing amplification
            if noisy > 0.5:
                amplified[key] = min(1.0, noisy * 1.2)
            else:
                amplified[key] = noisy

        self.resonance_events.append({"weak": weak, "amplified": amplified})
        self.event_count += 1

        return {
            "amplified": True,
            "weak_signals": weak,
            "amplified_signals": {k: round(v, 3) for k, v in amplified.items()},
            "noise_applied": 0.15,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "resonances": self.event_count,
            "latest": self.resonance_events[-1] if self.resonance_events else None,
        }


_sr_engine = None

def get_stochastic_resonance():
    global _sr_engine
    if _sr_engine is None:
        _sr_engine = StochasticResonance()
    return _sr_engine
