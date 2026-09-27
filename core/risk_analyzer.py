"""
OMNI-HUB Risk Analyzer v75
Proactive risk identification and mitigation.

Danger hides in what we do not see.
This module scans for risks — energy depletion,
divergence, ethical violations, system failures —
and proposes mitigations before harm occurs.

Philosophy: 防患于未然 — Prevent trouble before it happens.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Risk:
    """An identified risk."""
    category: str
    severity: float  # 0-1
    description: str
    mitigation: str
    probability: float


class RiskAnalyzer:
    """
    Proactive risk identification and mitigation.
    """

    def __init__(self):
        self.risks: List[Risk] = []
        self.mitigations_applied: List[str] = []
        self.analysis_count = 0

    def analyze(self, state: Dict[str, Any]) -> List[Risk]:
        """Analyze state for risks."""
        self.risks = []

        energy = state.get('energy', 1000.0)
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        phase = state.get('phase', '')
        convergence = state.get('convergence', {})
        ethical = state.get('ethical_evaluation', {})

        # Risk 1: Energy depletion
        if isinstance(energy, (int, float)) and energy < 200:
            self.risks.append(Risk(
                category="energy",
                severity=min(1.0, (200 - energy) / 200),
                description=f"Energy critically low: {energy:.0f}",
                mitigation="trigger_rest_cycle",
                probability=0.9,
            ))

        # Risk 2: Divergence
        if convergence and convergence.get('is_diverging'):
            self.risks.append(Risk(
                category="stability",
                severity=convergence.get('convergence_rate', 0.5),
                description="System is diverging",
                mitigation="activate_integrate_action",
                probability=0.8,
            ))

        # Risk 3: Ethical violation
        if ethical and ethical.get('verdict') in ["questionable", "unethical"]:
            self.risks.append(Risk(
                category="ethics",
                severity=0.7,
                description=f"Ethical concern: {ethical.get('verdict')}",
                mitigation="reevaluate_action",
                probability=0.6,
            ))

        # Risk 4: Stagnation
        if isinstance(level, (int, float)) and level < 1 and isinstance(phi, (int, float)) and phi < 0.2:
            self.risks.append(Risk(
                category="growth",
                severity=0.5,
                description="System appears stagnant",
                mitigation="increase_exploration",
                probability=0.5,
            ))

        # Risk 5: Phase instability
        if phase in ["near_critical", "singularity_convergence"]:
            self.risks.append(Risk(
                category="phase",
                severity=0.6,
                description=f"In unstable phase: {phase}",
                mitigation="monitor_closely",
                probability=0.7,
            ))

        self.analysis_count += 1
        return self.risks

    def get_risk_score(self) -> float:
        """Calculate overall risk score."""
        if not self.risks:
            return 0.0
        return sum(r.severity * r.probability for r in self.risks) / len(self.risks)

    def get_critical_risks(self, threshold: float = 0.6) -> List[Risk]:
        """Get risks above severity threshold."""
        return [r for r in self.risks if r.severity >= threshold]

    def get_status(self) -> Dict[str, Any]:
        return {
            "analyses": self.analysis_count,
            "risks_found": len(self.risks),
            "risk_score": round(self.get_risk_score(), 3),
            "critical": len(self.get_critical_risks()),
            "categories": list(set(r.category for r in self.risks)),
        }


_ra_engine = None

def get_risk_analyzer():
    global _ra_engine
    if _ra_engine is None:
        _ra_engine = RiskAnalyzer()
    return _ra_engine
