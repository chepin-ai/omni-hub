"""
OMNI-HUB Metacognitive Monitor Tests v43
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.metacognitive_monitor import (
    CognitiveObservation, BiasDetector, MetacognitiveMonitor, get_metacognitive_monitor,
)


class TestBiasDetector:
    def test_no_bias(self):
        bd = BiasDetector()
        actions = ["focus", "rest", "transcend", "reflect"] * 10
        result = bd.detect_action_bias(actions)
        assert result["bias_detected"] is False

    def test_bias_detected(self):
        bd = BiasDetector()
        actions = ["focus"] * 90 + ["rest"] * 10
        result = bd.detect_action_bias(actions)
        assert result["bias_detected"] is True
        assert result["overused"] == "focus"

    def test_phase_stagnation(self):
        bd = BiasDetector()
        phases = ["pre_emergence"] * 25
        result = bd.detect_phase_stagnation(phases)
        assert result["stagnant"] is True

    def test_no_stagnation(self):
        bd = BiasDetector()
        phases = ["pre_emergence", "post_critical"] * 10
        result = bd.detect_phase_stagnation(phases)
        assert result["stagnant"] is False

    def test_phi_oscillation(self):
        bd = BiasDetector()
        phi = [0.5 + i * 0.05 for i in range(10)]
        result = bd.detect_phi_oscillation(phi)
        assert "oscillating" in result
        assert "stability" in result


class TestMetacognitiveMonitor:
    def test_initialization(self):
        mm = MetacognitiveMonitor()
        assert len(mm.observations) == 0
        assert mm.alert_count == 0

    def test_observe_cycle_critical_phi(self):
        mm = MetacognitiveMonitor()
        obs = mm.observe_cycle(1, {"phi": 0.1, "energy": 1000.0}, "focus")
        assert len(obs) >= 1
        assert any(o.status == "critical" for o in obs)
        assert mm.alert_count >= 1

    def test_observe_cycle_warning_energy(self):
        mm = MetacognitiveMonitor()
        obs = mm.observe_cycle(1, {"phi": 0.8, "energy": 50.0}, "focus")
        assert any(o.status == "warning" for o in obs)

    def test_analyze_biases(self):
        mm = MetacognitiveMonitor()
        actions = ["focus"] * 50 + ["rest"] * 10
        phases = ["pre_emergence"] * 20
        phi = [0.5] * 20
        result = mm.analyze_biases(actions, phases, phi)
        assert "action_bias" in result
        assert "phase_stagnation" in result
        assert "phi_stability" in result

    def test_get_metacognitive_report(self):
        mm = MetacognitiveMonitor()
        mm.observe_cycle(1, {"phi": 0.1, "energy": 1000.0}, "focus")
        report = mm.get_metacognitive_report()
        assert "total_observations" in report
        assert "critical_alerts" in report
        assert "process_coverage" in report

    def test_get_status(self):
        mm = MetacognitiveMonitor()
        status = mm.get_status()
        assert "observations" in status
        assert "alerts" in status


class TestGlobalEngine:
    def test_get_metacognitive_monitor(self):
        g = get_metacognitive_monitor()
        assert g is not None
        assert isinstance(g, MetacognitiveMonitor)
