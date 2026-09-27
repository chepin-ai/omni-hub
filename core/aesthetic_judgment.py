"""
OMNI-HUB Aesthetic Judgment v93
Beauty, harmony, and proportion evaluation.

Beauty is truth, truth beauty.
This module evaluates aesthetic qualities —
harmony, proportion, elegance — in system structures and states.

Philosophy: 大音希声，大象无形 —
The greatest sound is rarely heard; the greatest image has no form.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class AestheticJudgment:
    """
    Evaluates aesthetic qualities of system state.
    """

    def __init__(self):
        self.beauty_scores: List[float] = []
        self.judgment_count = 0

    def evaluate_harmony(self, state: Dict[str, Any]) -> float:
        """Evaluate harmonic balance."""
        scores = []

        # Phi balance (golden ratio proximity)
        phi = state.get('phi', 0.5)
        if isinstance(phi, (int, float)):
            golden = 0.618
            phi_harmony = 1.0 - abs(phi - golden)
            scores.append(max(0, phi_harmony))

        # Line coherence
        coherence = state.get('line_coherence', 0.5)
        if isinstance(coherence, (int, float)):
            scores.append(coherence)

        # Energy balance (not too high, not too low)
        energy = state.get('energy', 1000)
        if isinstance(energy, (int, float)):
            ideal = 2500
            energy_balance = 1.0 - min(1.0, abs(energy - ideal) / ideal)
            scores.append(energy_balance)

        # Module balance (not too many active, not too few)
        active = sum(1 for k, v in state.items() if isinstance(v, dict) and "status" in str(v))
        ideal_modules = 30
        module_balance = 1.0 - min(1.0, abs(active - ideal_modules) / ideal_modules)
        scores.append(module_balance)

        return sum(scores) / len(scores) if scores else 0.5

    def evaluate_proportion(self, state: Dict[str, Any]) -> float:
        """Evaluate proportional relationships."""
        level = state.get('level', 0)
        energy = state.get('energy', 1000)

        if isinstance(level, (int, float)) and isinstance(energy, (int, float)) and level > 0:
            ratio = energy / (level * 500)
            # Ideal ratio is around 1.0
            proportion = 1.0 - min(1.0, abs(ratio - 1.0))
            return proportion
        return 0.5

    def evaluate_elegance(self, state: Dict[str, Any]) -> float:
        """Evaluate simplicity/elegance."""
        # Fewer problems = more elegant
        risks = state.get('risk_analyzer', {})
        risk_count = risks.get('risks_found', 0) if risks else 0

        betrayal = state.get('trust_engine', {})
        betrayal_count = betrayal.get('betrayals', 0) if betrayal else 0

        elegance = max(0.0, 1.0 - risk_count * 0.05 - betrayal_count * 0.1)
        return elegance

    def judge(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Complete aesthetic judgment."""
        harmony = self.evaluate_harmony(state)
        proportion = self.evaluate_proportion(state)
        elegance = self.evaluate_elegance(state)

        beauty = (harmony * 0.4 + proportion * 0.3 + elegance * 0.3)
        self.beauty_scores.append(beauty)
        self.judgment_count += 1

        # Qualitative label
        if beauty > 0.8:
            label = " sublime"
        elif beauty > 0.6:
            label = " beautiful"
        elif beauty > 0.4:
            label = " pleasing"
        elif beauty > 0.2:
            label = " plain"
        else:
            label = " discordant"

        return {
            "beauty": round(beauty, 3),
            "harmony": round(harmony, 3),
            "proportion": round(proportion, 3),
            "elegance": round(elegance, 3),
            "label": label,
        }

    def get_status(self) -> Dict[str, Any]:
        avg = sum(self.beauty_scores) / len(self.beauty_scores) if self.beauty_scores else 0.5
        return {
            "judgments": self.judgment_count,
            "average_beauty": round(avg, 3),
            "latest": round(self.beauty_scores[-1], 3) if self.beauty_scores else 0.5,
        }


_aj_engine = None

def get_aesthetic_judgment():
    global _aj_engine
    if _aj_engine is None:
        _aj_engine = AestheticJudgment()
    return _aj_engine
