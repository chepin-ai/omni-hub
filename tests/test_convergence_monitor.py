"""
OMNI-HUB Convergence Monitor Tests v61
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.convergence_monitor import (
    ConvergenceSnapshot, ConvergenceMonitor, get_convergence_monitor,
)


class TestConvergenceMonitor:
    def test_initialization(self):
        cm = ConvergenceMonitor()
        assert len(cm.history) == 0

    def test_record(self):
        cm = ConvergenceMonitor()
        cm.record({"level": 5, "phi": 0.7, "energy": 1000.0}, cycle=1)
        assert len(cm.history) == 1

    def test_analyze_insufficient_data(self):
        cm = ConvergenceMonitor()
        result = cm.analyze()
        assert result["status"] == "insufficient_data"

    def test_analyze_rising_trend(self):
        cm = ConvergenceMonitor()
        for i in range(20):
            cm.record({"level": float(i), "phi": 0.5, "energy": 1000.0}, cycle=i)
        result = cm.analyze()
        assert result["trend"] == "rising"
        assert result["is_diverging"] is False

    def test_analyze_stable_trend(self):
        cm = ConvergenceMonitor()
        for i in range(20):
            cm.record({"level": 5.0, "phi": 0.5, "energy": 1000.0}, cycle=i)
        result = cm.analyze()
        assert result["trend"] == "stable"

    def test_singularity_prediction(self):
        cm = ConvergenceMonitor()
        for i in range(20):
            cm.record({"level": float(i) * 0.1, "phi": 0.5, "energy": 1000.0}, cycle=i)
        result = cm.analyze()
        assert result["cycles_to_singularity"] > 0

    def test_get_status(self):
        cm = ConvergenceMonitor()
        status = cm.get_status()
        assert "snapshots" in status
        assert "divergence_alerts" in status


class TestGlobalEngine:
    def test_get_convergence_monitor(self):
        g = get_convergence_monitor()
        assert g is not None
        assert isinstance(g, ConvergenceMonitor)
