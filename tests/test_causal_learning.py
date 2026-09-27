"""
OMNI-HUB Causal Learning Tests v88
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.causal_learning import (
    CausalLink, CausalLearning, get_causal_learning,
)


class TestCausalLearning:
    def test_initialization(self):
        cl = CausalLearning()
        assert len(cl.links) == 0

    def test_record_observation(self):
        cl = CausalLearning()
        cl.record_observation({"a": 1.0}, {"a": 2.0})
        assert len(cl.observations) == 1

    def test_infer_links(self):
        cl = CausalLearning()
        for i in range(5):
            cl.record_observation({"cause": i, "effect": i}, {"cause": i, "effect": i + 2})
        links = cl.infer_links()
        assert len(links) >= 1
        assert links[0].confidence > 0

    def test_predict_effect(self):
        cl = CausalLearning()
        cl.links = [CausalLink("cause", "effect", 0.8, 5, 0.9)]
        pred = cl.predict_effect("cause", {})
        assert pred["effect"] == "effect"
        assert pred["confidence"] == 0.9

    def test_learn_from_history(self):
        cl = CausalLearning()
        history = [
            {"state": {"x": 1.0, "y": 1.0}},
            {"state": {"x": 2.0, "y": 3.0}},
            {"state": {"x": 3.0, "y": 5.0}},
            {"state": {"x": 4.0, "y": 7.0}},
        ]
        links = cl.learn_from_history(history)
        assert len(links) >= 1

    def test_get_status(self):
        cl = CausalLearning()
        cl.record_observation({"a": 1}, {"a": 2})
        status = cl.get_status()
        assert status["observations"] == 1
        assert "top_links" in status


class TestGlobalEngine:
    def test_get_causal_learning(self):
        g = get_causal_learning()
        assert g is not None
        assert isinstance(g, CausalLearning)
