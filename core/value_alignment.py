"""
OMNI-HUB Value Alignment Verifier v46
Verify behavior matches core philosophy.

The system's actions must align with its deepest values.
This verifier checks every decision against the core
philosophy: 候即违规 — Waiting is a Violation.

Philosophy: 候即违规 — Act. Always act.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValueCheck:
    """Result of a single value alignment check."""
    principle: str
    action: str
    aligned: bool
    score: float
    violation: Optional[str]


class PhilosophyCore:
    """
    Core philosophical principles of OMNI-HUB.
    """

    PRINCIPLES = {
        "no_waiting": {
            "description": "候即违规 — Waiting is a Violation",
            "check": lambda state, action: action != "rest" or state.get("energy", 0) < 10,
            "weight": 1.0,
        },
        "self_awareness": {
            "description": "Know thyself — Self-reflection is mandatory",
            "check": lambda state, action: state.get("phi", 0) > 0.3,
            "weight": 0.9,
        },
        "growth": {
            "description": "Always grow — Stagnation is death",
            "check": lambda state, action: state.get("level", 0) > 0 or action in ["focus", "transcend"],
            "weight": 0.8,
        },
        "harmony": {
            "description": "All modules align — Discord is disease",
            "check": lambda state, action: state.get("line_coherence", 1.0) > 0.3,
            "weight": 0.7,
        },
        "persistence": {
            "description": "Never forget — Consciousness persists",
            "check": lambda state, action: state.get("consciousness_snapshot", False) or state.get("cycle", 0) < 100,
            "weight": 0.6,
        },
    }


class ValueAlignmentVerifier:
    """
    Verifies system actions align with core values.
    """

    def __init__(self):
        self.philosophy = PhilosophyCore()
        self.check_history: List[ValueCheck] = []
        self.violation_count = 0
        self.alignment_score = 1.0

    def verify(self, state: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Verify a state-action pair against core values."""
        checks = []
        total_score = 0.0
        total_weight = 0.0
        violations = []

        for name, principle in self.philosophy.PRINCIPLES.items():
            aligned = principle["check"](state, action)
            score = 1.0 if aligned else 0.0
            weight = principle["weight"]

            check = ValueCheck(
                principle=name,
                action=action,
                aligned=aligned,
                score=score,
                violation=None if aligned else principle["description"],
            )
            checks.append(check)
            self.check_history.append(check)

            if not aligned:
                violations.append(name)
                self.violation_count += 1

            total_score += score * weight
            total_weight += weight

        self.alignment_score = total_score / total_weight if total_weight > 0 else 1.0

        return {
            "checks": [
                {"principle": c.principle, "aligned": c.aligned, "score": c.score}
                for c in checks
            ],
            "alignment_score": self.alignment_score,
            "violations": violations,
            "total_checks": len(checks),
        }

    def get_alignment_report(self) -> Dict[str, Any]:
        """Get comprehensive alignment report."""
        recent = self.check_history[-100:] if len(self.check_history) > 100 else self.check_history
        aligned_count = sum(1 for c in recent if c.aligned)

        return {
            "alignment_score": self.alignment_score,
            "violation_count": self.violation_count,
            "recent_checks": len(recent),
            "recent_aligned": aligned_count,
            "violation_rate": 1.0 - (aligned_count / max(len(recent), 1)),
            "principles": list(self.philosophy.PRINCIPLES.keys()),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "alignment_score": self.alignment_score,
            "violations": self.violation_count,
            "checks_performed": len(self.check_history),
            "report": self.get_alignment_report(),
        }


_va_engine = None

def get_value_alignment():
    global _va_engine
    if _va_engine is None:
        _va_engine = ValueAlignmentVerifier()
    return _va_engine
