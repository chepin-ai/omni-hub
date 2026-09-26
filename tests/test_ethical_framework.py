"""
OMNI-HUB Ethical Framework Tests v67
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.ethical_framework import (
    EthicalEvaluation, EthicalFramework, get_ethical_framework,
)


class TestEthicalFramework:
    def test_initialization(self):
        ef = EthicalFramework()
        assert len(ef.evaluations) == 0

    def test_evaluate_focus_action(self):
        ef = EthicalFramework()
        state = {"energy": 1000.0}
        eval = ef.evaluate_action("focus", state)
        assert eval.action == "focus"
        assert eval.beneficence > 0.5
        assert eval.non_maleficence > 0.5
        assert eval.overall_score > 0
        assert eval.verdict in ["ethical", "acceptable", "questionable", "unethical"]

    def test_evaluate_rest_action(self):
        ef = EthicalFramework()
        state = {"energy": 1000.0}
        eval = ef.evaluate_action("rest", state)
        assert eval.non_maleficence > 0.8  # rest is safe

    def test_evaluate_risky_action_low_energy(self):
        ef = EthicalFramework()
        state = {"energy": 50.0}
        eval = ef.evaluate_action("focus", state)
        assert eval.non_maleficence < 0.5  # risky when low energy

    def test_evaluate_current_action(self):
        ef = EthicalFramework()
        state = {"last_self_drive_action": "transcend", "energy": 1000.0}
        eval = ef.evaluate_current_action(state)
        assert eval.action == "transcend"

    def test_get_ethical_report(self):
        ef = EthicalFramework()
        for action in ["focus", "rest", "reflect"]:
            ef.evaluate_action(action, {"energy": 1000.0})
        report = ef.get_ethical_report()
        assert "average_score" in report
        assert "ethical_ratio" in report
        assert report["total_evaluations"] == 3

    def test_get_status(self):
        ef = EthicalFramework()
        ef.evaluate_action("focus", {"energy": 1000.0})
        status = ef.get_status()
        assert status["evaluations"] == 1
        assert "report" in status


class TestGlobalEngine:
    def test_get_ethical_framework(self):
        g = get_ethical_framework()
        assert g is not None
        assert isinstance(g, EthicalFramework)
