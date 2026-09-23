"""
OMNI-HUB Self-Healing Engine Tests v31
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.self_healing import (
    HealthMonitor, HealthSnapshot, RepairEngine, ImprovementEngine,
    SelfHealingEngine, RepairAction, ImprovementSuggestion,
)


class TestHealthMonitor:
    def test_record(self):
        hm = HealthMonitor(window_size=10)
        state = {"level": 1, "energy": 1.5, "phi": 0.6, "phase": "near_critical", "action": "focus"}
        snap = hm.record(0, state)
        assert snap.cycle == 0
        assert snap.energy == 1.5
        assert len(hm.history) == 1

    def test_baseline_empty(self):
        hm = HealthMonitor()
        assert hm.compute_baseline() == {}

    def test_baseline_computation(self):
        hm = HealthMonitor()
        for i in range(20):
            hm.record(i, {"level": i // 5, "energy": 1.0 + i * 0.1, "phi": 0.5, "phase": "x", "action": "focus"})
        baseline = hm.compute_baseline()
        assert "avg_energy" in baseline
        assert baseline["energy_trend"] > 0

    def test_anomaly_normal(self):
        hm = HealthMonitor()
        for i in range(20):
            hm.record(i, {"level": 0, "energy": 1.0 + i * 0.1, "phi": 0.5 + i * 0.01, "phase": "x", "action": "focus"})
        snap = hm.record(20, {"level": 1, "energy": 3.0, "phi": 0.7, "phase": "x", "action": "focus"})
        score = hm.get_anomaly_score(snap)
        assert score < 0.3

    def test_anomaly_stagnation(self):
        hm = HealthMonitor()
        for i in range(20):
            hm.record(i, {"level": 0, "energy": 1.0, "phi": 0.5, "phase": "x", "action": "focus"})
        snap = hm.record(20, {"level": 0, "energy": 1.0, "phi": 0.5, "phase": "x", "action": "focus"})
        score = hm.get_anomaly_score(snap)
        assert score >= 0.3  # Stagnation detected

    def test_anomaly_phi_collapse(self):
        hm = HealthMonitor()
        for i in range(20):
            hm.record(i, {"level": 0, "energy": 1.0, "phi": 0.5, "phase": "x", "action": "focus"})
        snap = hm.record(20, {"level": 0, "energy": 1.0, "phi": 0.05, "phase": "x", "action": "focus"})
        score = hm.get_anomaly_score(snap)
        assert score >= 0.3


class TestRepairEngine:
    def test_clear_stale_state(self):
        re = RepairEngine()
        result = re.clear_stale_state()
        assert isinstance(result, RepairAction)
        assert result.success is True

    def test_clear_pycache(self):
        re = RepairEngine()
        result = re.clear_pycache()
        assert isinstance(result, RepairAction)
        assert result.success is True

    def test_recompile_modules(self):
        re = RepairEngine()
        result = re.recompile_modules()
        assert isinstance(result, RepairAction)
        assert result.success is True
        assert "active modules" in result.detail.lower() or "compile" in result.detail.lower()

    def test_reset_emotional_state(self):
        re = RepairEngine()
        result = re.reset_emotional_state()
        assert isinstance(result, RepairAction)
        assert result.success is True

    def test_refresh_imports(self):
        re = RepairEngine()
        result = re.refresh_imports()
        assert isinstance(result, RepairAction)
        assert result.success is True

    def test_run_all(self):
        re = RepairEngine()
        results = re.run_all()
        assert len(results) == 5
        assert all(isinstance(r, RepairAction) for r in results)


class TestImprovementEngine:
    def test_analyze_empty(self):
        ie = ImprovementEngine()
        assert ie.analyze([]) == []

    def test_analyze_stagnation(self):
        ie = ImprovementEngine()
        history = []
        for i in range(60):
            history.append(HealthSnapshot(
                cycle=i, level=5, energy=10.0, phi=0.5,
                phase="x", action="focus"
            ))
        suggestions = ie.analyze(history)
        assert len(suggestions) > 0
        assert any("stagnant" in s.reason for s in suggestions)

    def test_analyze_action_imbalance(self):
        ie = ImprovementEngine()
        history = []
        for i in range(60):
            history.append(HealthSnapshot(
                cycle=i, level=i // 10, energy=1.0 + i * 0.1, phi=0.5,
                phase="x", action="focus"  # All focus
            ))
        suggestions = ie.analyze(history)
        assert any("focus dominates" in s.reason for s in suggestions)

    def test_apply_suggestion(self):
        ie = ImprovementEngine()
        sug = ImprovementSuggestion("test", 1, 2, "reason", 0.8)
        assert ie.apply_suggestion(sug) is True
        assert sug.applied is True


class TestSelfHealingEngine:
    def test_initialization(self):
        engine = SelfHealingEngine()
        assert engine.health_trend == "stable"
        assert len(engine.monitor.history) == 0

    def test_check(self):
        engine = SelfHealingEngine()
        state = {"level": 1, "energy": 1.5, "phi": 0.6, "phase": "near_critical", "action": "focus"}
        report = engine.check(0, state)
        assert report["status"] in ("healthy", "warning", "degraded")
        assert "anomaly_score" in report

    def test_deep_repair(self):
        engine = SelfHealingEngine()
        # Seed some history
        for i in range(10):
            engine.check(i, {"level": 0, "energy": 1.0 + i * 0.1, "phi": 0.5, "phase": "x", "action": "focus"})
        report = engine.deep_repair(10)
        assert report["status"] == "repaired"
        assert len(report["repairs"]) == 5

    def test_get_status(self):
        engine = SelfHealingEngine()
        status = engine.get_status()
        assert "health_trend" in status
        assert "history_size" in status
