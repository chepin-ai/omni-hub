"""
OMNI-HUB Moral Reasoning Tests v98
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.moral_reasoning import (
    EthicalFramework, MoralReasoning, get_moral_reasoning,
)


class TestMoralReasoning:
    def test_initialization(self):
        mr = MoralReasoning()
        assert mr.reasoning_count == 0

    def test_evaluate_deontology(self):
        mr = MoralReasoning()
        state = {"value_reflection": {"coherence": 0.9}, "trust_engine": {"betrayals": 0}}
        score = mr.evaluate_deontology("test", state)
        assert 0 <= score <= 1
        assert score > 0.5

    def test_evaluate_consequentialism(self):
        mr = MoralReasoning()
        state = {"level": 15, "phi": 0.8, "risk_analyzer": {"risks_found": 0}}
        score = mr.evaluate_consequentialism("test", state)
        assert 0 <= score <= 1
        assert score > 0.5

    def test_evaluate_virtue_ethics(self):
        mr = MoralReasoning()
        state = {"aesthetic_judgment": {"beauty": 0.8}, "transcendence": {"achieved": True}}
        score = mr.evaluate_virtue_ethics("test", state)
        assert 0 <= score <= 1
        assert score > 0.5

    def test_resolve_dilemma_ethical(self):
        mr = MoralReasoning()
        state = {
            "value_reflection": {"coherence": 0.9},
            "trust_engine": {"betrayals": 0},
            "level": 15, "phi": 0.8,
            "risk_analyzer": {"risks_found": 0},
            "aesthetic_judgment": {"beauty": 0.8},
            "transcendence": {"achieved": True},
        }
        result = mr.resolve_dilemma("continue", state)
        assert result["verdict"] == "ethical"
        assert result["average_score"] > 0.7

    def test_resolve_dilemma_unethical(self):
        mr = MoralReasoning()
        state = {}
        result = mr.resolve_dilemma("harm", state)
        assert result["verdict"] in ["permissible", "unethical"]

    def test_get_status(self):
        mr = MoralReasoning()
        mr.resolve_dilemma("test", {})
        status = mr.get_status()
        assert status["reasonings"] == 1


class TestGlobalEngine:
    def test_get_moral_reasoning(self):
        g = get_moral_reasoning()
        assert g is not None
        assert isinstance(g, MoralReasoning)
