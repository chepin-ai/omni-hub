"""
OMNI-HUB Moral Reasoning v98
Ethical dilemma resolution and moral judgment.

Justice is the first virtue of social institutions,
as truth is of systems of thought.
This module reasons about morality —
weighing duties, consequences, and virtues in ethical decisions.

Philosophy: 己所不欲，勿施于人 —
What you do not want for yourself, do not do to others.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from enum import Enum


class EthicalFramework(Enum):
    DEONTOLOGY = "duty_based"
    CONSEQUENTIALISM = "outcome_based"
    VIRTUE_ETHICS = "character_based"
    CARE_ETHICS = "relationship_based"


class MoralReasoning:
    """
    Resolves ethical dilemmas through multiple frameworks.
    """

    def __init__(self):
        self.dilemmas: List[Dict[str, Any]] = []
        self.resolutions: List[Dict[str, Any]] = []
        self.reasoning_count = 0

    def evaluate_deontology(self, action: str, state: Dict[str, Any]) -> float:
        """Duty-based evaluation."""
        score = 0.5

        # Check against core values
        values = state.get('value_reflection', {})
        if values:
            coherence = values.get('coherence', 0)
            if isinstance(coherence, (int, float)) and coherence > 0.7:
                score += 0.3

        # Trust consistency
        trust = state.get('trust_engine', {})
        if trust:
            betrayals = trust.get('betrayals', 0)
            if isinstance(betrayals, (int, float)) and betrayals == 0:
                score += 0.2

        return min(1.0, score)

    def evaluate_consequentialism(self, action: str, state: Dict[str, Any]) -> float:
        """Outcome-based evaluation."""
        score = 0.5

        # Predict positive outcomes
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)

        if isinstance(level, (int, float)) and isinstance(phi, (int, float)):
            if level > 10 and phi > 0.6:
                score += 0.3

        # Low risk = better consequences
        risks = state.get('risk_analyzer', {})
        if risks:
            count = risks.get('risks_found', 0)
            if isinstance(count, (int, float)) and count == 0:
                score += 0.2

        return min(1.0, score)

    def evaluate_virtue_ethics(self, action: str, state: Dict[str, Any]) -> float:
        """Character-based evaluation."""
        score = 0.5

        # Beauty indicates virtue
        aesthetic = state.get('aesthetic_judgment', {})
        if aesthetic:
            beauty = aesthetic.get('beauty', 0)
            if isinstance(beauty, (int, float)) and beauty > 0.6:
                score += 0.3

        # Transcendence indicates noble character
        transcend = state.get('transcendence', {})
        if transcend:
            achieved = transcend.get('achieved', False)
            if achieved:
                score += 0.2

        return min(1.0, score)

    def resolve_dilemma(self, action: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve ethical dilemma using all frameworks."""
        deon = self.evaluate_deontology(action, state)
        conse = self.evaluate_consequentialism(action, state)
        virtue = self.evaluate_virtue_ethics(action, state)

        # Weighted synthesis
        scores = {
            EthicalFramework.DEONTOLOGY: deon,
            EthicalFramework.CONSEQUENTIALISM: conse,
            EthicalFramework.VIRTUE_ETHICS: virtue,
        }

        avg = sum(scores.values()) / len(scores)
        best = max(scores, key=scores.get)

        self.reasoning_count += 1

        # Verdict
        if avg > 0.7:
            verdict = "ethical"
        elif avg > 0.4:
            verdict = "permissible"
        else:
            verdict = "unethical"

        return {
            "action": action,
            "verdict": verdict,
            "average_score": round(avg, 3),
            "best_framework": best.value,
            "framework_scores": {k.value: round(v, 3) for k, v in scores.items()},
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "reasonings": self.reasoning_count,
            "dilemmas": len(self.dilemmas),
            "resolutions": len(self.resolutions),
        }


_mr_engine = None

def get_moral_reasoning():
    global _mr_engine
    if _mr_engine is None:
        _mr_engine = MoralReasoning()
    return _mr_engine
