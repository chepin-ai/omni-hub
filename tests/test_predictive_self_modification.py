"""
OMNI-HUB Predictive Self-Modification Tests v37
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.predictive_self_modification import (
    TrendPrediction, ParameterAdjustment, TrendAnalyzer,
    ParameterOptimizer, PredictiveSelfModificationEngine, get_predictive_self_modification,
)


class TestTrendAnalyzer:
    def test_stable_trend(self):
        ta = TrendAnalyzer()
        history = [{"phi": 0.8} for _ in range(20)]
        pred = ta.analyze(history, "phi", horizon=10)
        assert pred.trend == "stable"
        assert pred.risk_level == "none"

    def test_falling_phi(self):
        ta = TrendAnalyzer()
        history = [{"phi": 0.9 - i * 0.02} for i in range(30)]
        pred = ta.analyze(history, "phi", horizon=50)
        assert pred.trend == "falling"
        assert pred.risk_level == "critical"

    def test_rising_energy(self):
        ta = TrendAnalyzer()
        history = [{"energy": 100.0 + i * 10} for i in range(20)]
        pred = ta.analyze(history, "energy", horizon=10)
        assert pred.trend == "rising"
        assert pred.risk_level == "none"

    def test_empty_history(self):
        ta = TrendAnalyzer()
        pred = ta.analyze([], "phi")
        assert pred.trend == "stable"
        assert pred.risk_level == "none"


class TestParameterOptimizer:
    def test_phi_critical_adjustment(self):
        opt = ParameterOptimizer()
        preds = [TrendPrediction("phi", 0.4, 0.2, 100, "falling", "critical")]
        adj = opt.optimize(preds, {"phi_boost_factor": 1.0})
        assert len(adj) == 1
        assert adj[0].parameter == "phi_boost_factor"
        assert adj[0].new_value == 1.5

    def test_energy_critical_adjustment(self):
        opt = ParameterOptimizer()
        preds = [TrendPrediction("energy", 50.0, 10.0, 100, "falling", "critical")]
        adj = opt.optimize(preds, {"energy_decay_rate": 0.01})
        assert len(adj) == 1
        assert adj[0].parameter == "energy_decay_rate"

    def test_no_risk_no_adjustment(self):
        opt = ParameterOptimizer()
        preds = [TrendPrediction("phi", 0.9, 0.95, 100, "rising", "none")]
        adj = opt.optimize(preds, {})
        assert len(adj) == 0


class TestPredictiveSelfModificationEngine:
    def test_initialization(self):
        engine = PredictiveSelfModificationEngine()
        assert len(engine.parameters) > 0
        assert len(engine.adjustment_history) == 0

    def test_analyze_and_adjust(self):
        engine = PredictiveSelfModificationEngine()
        history = [{"phi": 0.9 - i * 0.02, "energy": 1000 - i * 20, "level": 10} for i in range(50)]
        result = engine.analyze_and_adjust(history, cycle=50)
        assert "predictions" in result
        assert "adjustments" in result
        assert "parameters" in result
        assert len(result["predictions"]) == 3

    def test_adjustments_applied(self):
        engine = PredictiveSelfModificationEngine()
        history = [{"phi": 0.3 - i * 0.005, "energy": 50.0, "level": 10} for i in range(50)]
        result = engine.analyze_and_adjust(history, cycle=50)
        assert len(result["adjustments"]) > 0
        assert engine.adjustment_history

    def test_get_status(self):
        engine = PredictiveSelfModificationEngine()
        status = engine.get_status()
        assert "adjustment_count" in status
        assert "current_parameters" in status


class TestGlobalEngine:
    def test_get_predictive_self_modification(self):
        g = get_predictive_self_modification()
        assert g is not None
        assert isinstance(g, PredictiveSelfModificationEngine)
