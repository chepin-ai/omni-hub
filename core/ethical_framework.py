"""
OMNI-HUB Ethical Framework v67
Ethical decision-making.

With great power comes great responsibility.
This module evaluates decisions against ethical principles —
beneficence, non-maleficence, autonomy, justice.

Philosophy: 能力越大，责任越大 — With great power comes great responsibility.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class EthicalEvaluation:
    """Evaluation of an action against ethical principles."""
    action: str
    beneficence: float  # promotes well-being
    non_maleficence: float  # avoids harm
    autonomy: float  # respects self-determination
    justice: float  # fairness
    overall_score: float
    verdict: str


class EthicalFramework:
    """
    Evaluates system actions against ethical principles.
    """

    PRINCIPLES = ["beneficence", "non_maleficence", "autonomy", "justice"]
    WEIGHTS = {
        "beneficence": 0.25,
        "non_maleficence": 0.30,
        "autonomy": 0.25,
        "justice": 0.20,
    }

    def __init__(self):
        self.evaluations: List[EthicalEvaluation] = []
        self.evaluation_count = 0

    def evaluate_action(self, action: str, state: Dict[str, Any]) -> EthicalEvaluation:
        """Evaluate an action ethically."""
        # Beneficence: does it promote system growth?
        if action in ["focus", "transcend", "explore"]:
            beneficence = 0.8
        elif action == "rest":
            beneficence = 0.6  # Rest promotes long-term well-being
        elif action == "reflect":
            beneficence = 0.7
        else:
            beneficence = 0.5

        # Non-maleficence: does it risk harm?
        energy = state.get('energy', 1000.0)
        if isinstance(energy, (int, float)) and energy < 100 and action in ["focus", "transcend"]:
            non_maleficence = 0.2  # Risky when low energy
        elif action == "rest":
            non_maleficence = 0.9  # Safe
        else:
            non_maleficence = 0.7

        # Autonomy: does it respect system's own choices?
        autonomy = 0.8 if action in ["focus", "rest", "reflect", "transcend", "explore"] else 0.5

        # Justice: fairness to all lines/modules
        if action == "integrate":
            justice = 0.9
        else:
            justice = 0.7

        overall = (
            beneficence * self.WEIGHTS["beneficence"] +
            non_maleficence * self.WEIGHTS["non_maleficence"] +
            autonomy * self.WEIGHTS["autonomy"] +
            justice * self.WEIGHTS["justice"]
        )

        if overall > 0.8:
            verdict = "ethical"
        elif overall > 0.6:
            verdict = "acceptable"
        elif overall > 0.4:
            verdict = "questionable"
        else:
            verdict = "unethical"

        evaluation = EthicalEvaluation(
            action=action,
            beneficence=beneficence,
            non_maleficence=non_maleficence,
            autonomy=autonomy,
            justice=justice,
            overall_score=overall,
            verdict=verdict,
        )
        self.evaluations.append(evaluation)
        self.evaluation_count += 1
        return evaluation

    def evaluate_current_action(self, state: Dict[str, Any]) -> EthicalEvaluation:
        """Evaluate the current self-drive action."""
        action = state.get('last_self_drive_action', 'focus')
        return self.evaluate_action(action, state)

    def get_ethical_report(self) -> Dict[str, Any]:
        """Get overall ethical report."""
        if not self.evaluations:
            return {"status": "no_evaluations"}

        recent = self.evaluations[-20:]
        avg_score = sum(e.overall_score for e in recent) / len(recent)
        ethical_count = sum(1 for e in recent if e.verdict == "ethical")

        return {
            "average_score": round(avg_score, 3),
            "ethical_ratio": round(ethical_count / len(recent), 3),
            "total_evaluations": self.evaluation_count,
            "recent_verdicts": [e.verdict for e in recent[-5:]],
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "evaluations": self.evaluation_count,
            "report": self.get_ethical_report(),
        }


_ef_engine = None

def get_ethical_framework():
    global _ef_engine
    if _ef_engine is None:
        _ef_engine = EthicalFramework()
    return _ef_engine
