"""
OMNI-HUB Probabilistic Reasoning Tests v62
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.probabilistic_reasoning import (
    Belief, BayesianUpdater, ProbabilisticReasoningEngine, get_probabilistic_reasoning,
)


class TestBayesianUpdater:
    def test_update_positive_evidence(self):
        bu = BayesianUpdater()
        posterior = bu.update(0.5, 0.9, 0.8)
        assert posterior > 0.5

    def test_update_negative_evidence(self):
        bu = BayesianUpdater()
        posterior = bu.update(0.5, 0.1, 0.8)
        assert posterior < 0.5

    def test_update_bounds(self):
        bu = BayesianUpdater()
        posterior = bu.update(0.5, 0.9, 1.0)
        assert 0 < posterior < 1


class TestProbabilisticReasoningEngine:
    def test_initialization(self):
        pr = ProbabilisticReasoningEngine()
        assert len(pr.beliefs) == 0

    def test_register_hypothesis(self):
        pr = ProbabilisticReasoningEngine()
        pr.register_hypothesis("test_hypothesis", 0.5)
        assert "test_hypothesis" in pr.beliefs
        assert pr.beliefs["test_hypothesis"].prior == 0.5

    def test_observe_evidence(self):
        pr = ProbabilisticReasoningEngine()
        pr.observe_evidence("test", likelihood=0.9, strength=0.8)
        belief = pr.get_belief("test")
        assert belief is not None
        assert belief.posterior > 0.5
        assert belief.evidence_count == 1

    def test_infer_from_state_growing(self):
        pr = ProbabilisticReasoningEngine()
        pr.infer_from_state({"level": 5, "phi": 0.6, "energy": 1000.0})
        assert "system_is_growing" in pr.beliefs
        assert pr.beliefs["system_is_growing"].posterior > 0.5

    def test_get_all_beliefs(self):
        pr = ProbabilisticReasoningEngine()
        pr.observe_evidence("a", 0.9, 0.8)
        pr.observe_evidence("b", 0.6, 0.8)
        beliefs = pr.get_all_beliefs()
        assert len(beliefs) == 2
        assert beliefs[0]["hypothesis"] == "a"  # Higher posterior first

    def test_get_status(self):
        pr = ProbabilisticReasoningEngine()
        pr.observe_evidence("test", 0.9, 0.8)
        status = pr.get_status()
        assert "beliefs" in status
        assert "top_beliefs" in status


class TestGlobalEngine:
    def test_get_probabilistic_reasoning(self):
        g = get_probabilistic_reasoning()
        assert g is not None
        assert isinstance(g, ProbabilisticReasoningEngine)
