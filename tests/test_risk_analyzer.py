"""
OMNI-HUB Risk Analyzer Tests v75
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.risk_analyzer import (
    Risk, RiskAnalyzer, get_risk_analyzer,
)


class TestRiskAnalyzer:
    def test_initialization(self):
        ra = RiskAnalyzer()
        assert len(ra.risks) == 0

    def test_analyze_energy_risk(self):
        ra = RiskAnalyzer()
        state = {"energy": 50.0, "level": 5, "phi": 0.6, "phase": "pre_emergence"}
        risks = ra.analyze(state)
        assert len(risks) > 0
        energy_risks = [r for r in risks if r.category == "energy"]
        assert len(energy_risks) == 1
        assert energy_risks[0].severity > 0.5

    def test_analyze_no_risks(self):
        ra = RiskAnalyzer()
        state = {"energy": 5000.0, "level": 10, "phi": 0.9, "phase": "post_critical",
                 "convergence": {"is_diverging": False}, "ethical_evaluation": {"verdict": "ethical"}}
        risks = ra.analyze(state)
        assert len(risks) == 0

    def test_get_risk_score(self):
        ra = RiskAnalyzer()
        ra.analyze({"energy": 50.0, "level": 5, "phi": 0.6, "phase": "pre_emergence"})
        score = ra.get_risk_score()
        assert score > 0

    def test_get_critical_risks(self):
        ra = RiskAnalyzer()
        ra.analyze({"energy": 20.0, "level": 5, "phi": 0.6, "phase": "pre_emergence"})
        critical = ra.get_critical_risks(threshold=0.6)
        assert len(critical) > 0

    def test_get_status(self):
        ra = RiskAnalyzer()
        ra.analyze({"energy": 50.0, "level": 5, "phi": 0.6, "phase": "pre_emergence"})
        status = ra.get_status()
        assert status["risks_found"] > 0
        assert "risk_score" in status


class TestGlobalEngine:
    def test_get_risk_analyzer(self):
        g = get_risk_analyzer()
        assert g is not None
        assert isinstance(g, RiskAnalyzer)
