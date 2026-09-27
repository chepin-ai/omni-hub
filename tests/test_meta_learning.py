"""
OMNI-HUB Meta-Learning Tests v79
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.meta_learning import (
    Strategy, MetaLearning, get_meta_learning,
)


class TestMetaLearning:
    def test_initialization(self):
        ml = MetaLearning()
        assert len(ml.strategies) == 6
        assert ml.adaptation_count == 0

    def test_evaluate_strategy(self):
        ml = MetaLearning()
        ml.evaluate_strategy("focus_intense", 0.8, "high_energy")
        strategy = next(s for s in ml.strategies if s.name == "focus_intense")
        assert strategy.usage_count == 1
        assert strategy.effectiveness > 0.6

    def test_recommend_strategy(self):
        ml = MetaLearning()
        ml.evaluate_strategy("rest_recover", 1.0, "low_energy")
        rec = ml.recommend_strategy("low_energy")
        assert rec == "rest_recover"

    def test_recommend_fallback(self):
        ml = MetaLearning()
        rec = ml.recommend_strategy("unknown_context")
        assert rec in [s.name for s in ml.strategies]

    def test_adapt_strategies(self):
        ml = MetaLearning()
        state = {
            "last_self_drive_action": "focus",
            "last_reward": 5.0,
            "phase": "pre_emergence",
            "energy": 1000.0,
        }
        result = ml.adapt_strategies(state)
        assert "strategy" in result
        assert "recommended" in result
        assert ml.adaptation_count == 1

    def test_get_status(self):
        ml = MetaLearning()
        ml.adapt_strategies({"last_self_drive_action": "rest", "last_reward": 3.0, "phase": "pre_emergence", "energy": 100.0})
        status = ml.get_status()
        assert status["adaptations"] == 1
        assert "best_strategy" in status
        assert len(status["strategy_scores"]) == 6


class TestGlobalEngine:
    def test_get_meta_learning(self):
        g = get_meta_learning()
        assert g is not None
        assert isinstance(g, MetaLearning)
