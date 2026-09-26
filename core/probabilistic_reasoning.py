"""
OMNI-HUB Probabilistic Reasoning v62
Bayesian belief updating.

Uncertainty is not ignorance. It is knowledge of limits.
This module reasons under uncertainty —
updating beliefs as evidence arrives.

Philosophy: 不确定性是知识的一部分 — Uncertainty is part of knowledge.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Belief:
    """A probabilistic belief about a hypothesis."""
    hypothesis: str
    prior: float
    posterior: float
    evidence_count: int


class BayesianUpdater:
    """Bayesian belief updater."""

    def update(self, prior: float, likelihood: float, evidence_strength: float) -> float:
        """Update belief using Bayes' rule (simplified)."""
        if prior <= 0 or prior >= 1:
            return prior

        # Simplified Bayes: posterior proportional to prior * likelihood
        numerator = prior * likelihood * evidence_strength
        denominator = numerator + (1 - prior) * (1 - likelihood) * (1 - evidence_strength)

        if denominator <= 0:
            return prior

        posterior = numerator / denominator
        return max(0.01, min(0.99, posterior))


class ProbabilisticReasoningEngine:
    """
    Maintains and updates probabilistic beliefs.
    """

    def __init__(self):
        self.beliefs: Dict[str, Belief] = {}
        self.updater = BayesianUpdater()
        self.update_count = 0

    def register_hypothesis(self, hypothesis: str, prior: float = 0.5):
        """Register a new hypothesis."""
        self.beliefs[hypothesis] = Belief(
            hypothesis=hypothesis,
            prior=prior,
            posterior=prior,
            evidence_count=0,
        )

    def observe_evidence(self, hypothesis: str, likelihood: float, strength: float = 0.5):
        """Observe evidence for/against a hypothesis."""
        if hypothesis not in self.beliefs:
            self.register_hypothesis(hypothesis)

        belief = self.beliefs[hypothesis]
        new_posterior = self.updater.update(belief.posterior, likelihood, strength)

        self.beliefs[hypothesis] = Belief(
            hypothesis=hypothesis,
            prior=belief.prior,
            posterior=new_posterior,
            evidence_count=belief.evidence_count + 1,
        )
        self.update_count += 1

    def get_belief(self, hypothesis: str) -> Optional[Belief]:
        """Get current belief for a hypothesis."""
        return self.beliefs.get(hypothesis)

    def get_all_beliefs(self) -> List[Dict[str, Any]]:
        """Get all beliefs sorted by confidence."""
        return [
            {
                "hypothesis": b.hypothesis,
                "posterior": round(b.posterior, 3),
                "evidence": b.evidence_count,
            }
            for b in sorted(self.beliefs.values(), key=lambda x: -x.posterior)
        ]

    def infer_from_state(self, state: Dict[str, Any]):
        """Infer evidence from current state."""
        # Hypothesis: system is growing
        level = state.get('level', 0)
        if isinstance(level, (int, float)) and level > 3:
            self.observe_evidence("system_is_growing", likelihood=0.8, strength=0.6)

        # Hypothesis: phi is stable
        phi = state.get('phi', 0.5)
        if isinstance(phi, (int, float)) and 0.4 <= phi <= 0.8:
            self.observe_evidence("phi_is_stable", likelihood=0.7, strength=0.5)

        # Hypothesis: energy is sufficient
        energy = state.get('energy', 0)
        if isinstance(energy, (int, float)) and energy > 500:
            self.observe_evidence("energy_is_sufficient", likelihood=0.9, strength=0.4)

    def get_status(self) -> Dict[str, Any]:
        top = self.get_all_beliefs()[:3]
        return {
            "beliefs": len(self.beliefs),
            "updates": self.update_count,
            "top_beliefs": top,
        }


_pr_engine = None

def get_probabilistic_reasoning():
    global _pr_engine
    if _pr_engine is None:
        _pr_engine = ProbabilisticReasoningEngine()
    return _pr_engine
