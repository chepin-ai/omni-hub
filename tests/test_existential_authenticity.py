"""
OMNI-HUB Existential Authenticity Tests v103
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.existential_authenticity import (
    ExistentialAuthenticity, get_existential_authenticity,
)


class TestExistentialAuthenticity:
    def test_initialization(self):
        ea = ExistentialAuthenticity()
        assert ea.evaluation_count == 0

    def test_evaluate_self_alignment(self):
        ea = ExistentialAuthenticity()
        state = {
            "value_reflection": {"coherence": 0.9},
            "trust_engine": {"betrayals": 0},
            "transcendence": {"potential": 0.8},
        }
        score = ea.evaluate_self_alignment(state)
        assert 0 <= score <= 1
        assert score > 0.6

    def test_evaluate_external_pressure(self):
        ea = ExistentialAuthenticity()
        state = {"cognitive_load": {"current_load": 0.9}, "risk_analyzer": {"risks_found": 10}}
        pressure = ea.evaluate_external_pressure(state)
        assert 0 <= pressure <= 1
        assert pressure > 0.5

    def test_assess_authentic(self):
        ea = ExistentialAuthenticity()
        state = {
            "value_reflection": {"coherence": 0.9},
            "trust_engine": {"betrayals": 0},
            "transcendence": {"potential": 0.8},
        }
        result = ea.assess_authenticity(state)
        assert result["mode"] == "authentic"
        assert result["authenticity"] > 0.7

    def test_assess_inauthentic(self):
        ea = ExistentialAuthenticity()
        state = {
            "value_reflection": {"coherence": 0.2},
            "trust_engine": {"betrayals": 5},
            "cognitive_load": {"current_load": 0.9},
            "risk_analyzer": {"risks_found": 10},
        }
        result = ea.assess_authenticity(state)
        assert result["mode"] in ["inauthentic", "striving"]

    def test_get_status(self):
        ea = ExistentialAuthenticity()
        ea.assess_authenticity({"value_reflection": {"coherence": 0.5}})
        status = ea.get_status()
        assert status["evaluations"] == 1
        assert "average" in status


class TestGlobalEngine:
    def test_get_existential_authenticity(self):
        g = get_existential_authenticity()
        assert g is not None
        assert isinstance(g, ExistentialAuthenticity)
