"""
OMNI-HUB Metacognitive Monitor v43
Self-monitoring of cognitive processes.

The system watches itself thinking — observing its own
patterns, biases, and blind spots.

Philosophy: 候即违规 — A mind that cannot see itself is blind.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class CognitiveObservation:
    process: str
    metric: str
    value: float
    threshold: float
    status: str
    timestamp: str


class BiasDetector:
    """Detects cognitive biases in system behavior."""

    def detect_action_bias(self, action_history: List[str]) -> Dict[str, Any]:
        """Detect if certain actions are over/under-used."""
        counts = defaultdict(int)
        for action in action_history:
            counts[action] += 1
        total = len(action_history)
        if total == 0:
            return {"bias_detected": False}

        expected = total / len(counts) if counts else 0
        max_action = max(counts.keys(), key=lambda a: counts[a]) if counts else ""
        min_action = min(counts.keys(), key=lambda a: counts[a]) if counts else ""

        bias_score = (counts[max_action] - expected) / max(expected, 1) if expected > 0 else 0

        return {
            "bias_detected": bias_score > 0.5,
            "bias_score": bias_score,
            "overused": max_action if bias_score > 0.5 else None,
            "underused": min_action if bias_score > 0.5 else None,
            "distribution": dict(counts),
        }

    def detect_phase_stagnation(self, phase_history: List[str]) -> Dict[str, Any]:
        """Detect if system is stuck in one phase."""
        if len(phase_history) < 10:
            return {"stagnant": False}

        recent = phase_history[-20:]
        unique = len(set(recent))
        if unique == 1:
            return {"stagnant": True, "stuck_in": recent[-1], "cycles": len(recent)}
        return {"stagnant": False, "unique_phases": unique}

    def detect_phi_oscillation(self, phi_history):
        """Detect if phi is oscillating unstably."""
        if len(phi_history) < 10:
            return {"oscillating": False, "stability": 1.0}
        recent = phi_history[-10:]
        oscillating = len(set(round(p, 2) for p in recent)) > 5
        stability = 1.0 - (max(recent) - min(recent))
        return {"oscillating": oscillating, "stability": stability}


class MetacognitiveMonitor:
    """
    Monitors the system's own cognitive processes.
    """

    PROCESSES = [
        "self_drive", "tool_call", "reflect", "integrate",
        "self_modify", "predict", "plan", "heal", "evolve",
        "resonate", "align", "search", "dream",
    ]

    def __init__(self):
        self.bias_detector = BiasDetector()
        self.observations: List[CognitiveObservation] = []
        self.process_counts: Dict[str, int] = defaultdict(int)
        self.alert_count = 0

    def observe_cycle(self, cycle: int, state: Dict[str, Any], action: str) -> List[CognitiveObservation]:
        """Observe a single cycle and record metrics."""
        observations = []
        self.process_counts[action] += 1

        # Monitor phi stability
        phi = state.get('phi', 0.5)
        if phi < 0.3:
            observations.append(CognitiveObservation(
                process="consciousness", metric="phi", value=phi,
                threshold=0.3, status="critical", timestamp=datetime.now().isoformat(),
            ))
            self.alert_count += 1

        # Monitor energy
        energy = state.get('energy', 0.0)
        if energy < 100:
            observations.append(CognitiveObservation(
                process="vitality", metric="energy", value=energy,
                threshold=100.0, status="warning", timestamp=datetime.now().isoformat(),
            ))

        # Monitor line coherence
        coherence = state.get('line_coherence', 0.0)
        if coherence < 0.5:
            observations.append(CognitiveObservation(
                process="lines", metric="coherence", value=coherence,
                threshold=0.5, status="warning", timestamp=datetime.now().isoformat(),
            ))

        # Monitor alignment
        align_report = state.get('alignment_report')
        if align_report and align_report.get('score', 1.0) < 0.8:
            observations.append(CognitiveObservation(
                process="alignment", metric="score", value=align_report['score'],
                threshold=0.8, status="warning", timestamp=datetime.now().isoformat(),
            ))

        self.observations.extend(observations)
        return observations

    def analyze_biases(self, action_history: List[str], phase_history: List[str], phi_history: List[float]) -> Dict[str, Any]:
        """Run full bias analysis."""
        return {
            "action_bias": self.bias_detector.detect_action_bias(action_history),
            "phase_stagnation": self.bias_detector.detect_phase_stagnation(phase_history),
            "phi_stability": self.bias_detector.detect_phi_oscillation(phi_history),
            "total_alerts": self.alert_count,
        }

    def get_metacognitive_report(self) -> Dict[str, Any]:
        """Generate comprehensive metacognitive report."""
        total_obs = len(self.observations)
        critical = sum(1 for o in self.observations if o.status == "critical")
        warnings = sum(1 for o in self.observations if o.status == "warning")

        # Process coverage
        covered = len(self.process_counts)
        coverage = covered / len(self.PROCESSES)

        return {
            "total_observations": total_obs,
            "critical_alerts": critical,
            "warnings": warnings,
            "process_coverage": coverage,
            "uncovered_processes": [p for p in self.PROCESSES if p not in self.process_counts],
            "most_active_process": max(self.process_counts.keys(), key=lambda k: self.process_counts[k]) if self.process_counts else None,
            "alert_rate": critical / max(total_obs, 1),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "observations": len(self.observations),
            "alerts": self.alert_count,
            "processes_monitored": len(self.process_counts),
            "report": self.get_metacognitive_report(),
        }


_meta_engine = None

def get_metacognitive_monitor():
    global _meta_engine
    if _meta_engine is None:
        _meta_engine = MetacognitiveMonitor()
    return _meta_engine
