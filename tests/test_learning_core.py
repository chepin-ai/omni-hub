"""
OMNI-HUB Learning Core Tests v68
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.learning_core import (
    Experience, LearningCore, get_learning_core,
)


class TestLearningCore:
    def test_initialization(self):
        lc = LearningCore()
        assert lc.experience_count == 0
        assert len(lc.action_values) == 0

    def test_record_experience(self):
        lc = LearningCore()
        lc.record_experience({"level": 1}, "focus", 5.0, {"level": 2})
        assert lc.experience_count == 1
        assert "focus" in lc.action_values

    def test_learn_from_cycle_level_up(self):
        lc = LearningCore()
        prev = {"level": 1, "energy": 1000.0, "phase": "pre_emergence"}
        curr = {"level": 2, "energy": 1000.0, "phase": "pre_emergence"}
        reward = lc.learn_from_cycle(prev, curr, "focus")
        assert reward > 0  # Level up = positive reward

    def test_learn_from_cycle_low_energy(self):
        lc = LearningCore()
        prev = {"level": 1, "energy": 50.0, "phase": "pre_emergence"}
        curr = {"level": 1, "energy": 50.0, "phase": "pre_emergence"}
        reward = lc.learn_from_cycle(prev, curr, "focus")
        assert reward < 0  # Low energy = negative reward

    def test_recommend_action(self):
        lc = LearningCore()
        for i in range(5):
            lc.record_experience({"level": i}, "focus", 5.0, {"level": i + 1})
        action = lc.recommend_action()
        assert action == "focus"

    def test_get_action_values(self):
        lc = LearningCore()
        lc.record_experience({"level": 1}, "focus", 5.0, {"level": 2})
        values = lc.get_action_values()
        assert "focus" in values

    def test_get_status(self):
        lc = LearningCore()
        lc.record_experience({"level": 1}, "focus", 5.0, {"level": 2})
        status = lc.get_status()
        assert status["experiences"] == 1
        assert status["best_action"] == "focus"


class TestGlobalEngine:
    def test_get_learning_core(self):
        g = get_learning_core()
        assert g is not None
        assert isinstance(g, LearningCore)
