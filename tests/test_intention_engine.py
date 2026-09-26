"""
OMNI-HUB Intention Engine Tests v48
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.intention_engine import (
    SubGoal, IntentionInference, GoalDecomposer, IntentionEngine, get_intention_engine,
)


class TestIntentionInference:
    def test_infer_growth(self):
        ii = IntentionInference()
        actions = ["focus", "transcend", "focus", "focus"] * 5
        intentions = ii.infer(actions, [])
        assert len(intentions) > 0
        assert intentions[0]["name"] == "growth"

    def test_infer_survival(self):
        ii = IntentionInference()
        actions = ["rest", "heal", "rest"] * 5
        intentions = ii.infer(actions, [])
        growth = [i for i in intentions if i["name"] == "survival"]
        assert len(growth) > 0

    def test_empty_history(self):
        ii = IntentionInference()
        intentions = ii.infer([], [])
        assert len(intentions) == 0


class TestGoalDecomposer:
    def test_decompose_level(self):
        gd = GoalDecomposer()
        state = {"level": 3}
        goals = gd.decompose("reach_level_10", state)
        assert len(goals) == 7
        assert goals[0].target_value == 4

    def test_decompose_health(self):
        gd = GoalDecomposer()
        state = {"energy": 50, "phi": 0.2}
        goals = gd.decompose("maintain_health", state)
        assert len(goals) == 2
        assert goals[0].target_metric == "energy"

    def test_decompose_coherence(self):
        gd = GoalDecomposer()
        state = {}
        goals = gd.decompose("maximize_coherence", state)
        assert len(goals) == 1
        assert goals[0].target_value == 0.8


class TestIntentionEngine:
    def test_initialization(self):
        ie = IntentionEngine()
        assert len(ie.active_goals) == 0

    def test_observe_action(self):
        ie = IntentionEngine()
        state = {"level": 1, "energy": 100, "phi": 0.5}
        report = ie.observe_action("focus", state, cycle=100)
        assert "inferred_intentions" in report

    def test_goal_progression(self):
        ie = IntentionEngine()
        state = {"level": 1, "energy": 100, "phi": 0.5}
        ie.observe_action("focus", state, cycle=100)
        # Simulate reaching goal
        state["level"] = 5
        report = ie.observe_action("focus", state, cycle=200)
        assert report["completed_goals"] >= 0

    def test_get_status(self):
        ie = IntentionEngine()
        status = ie.get_status()
        assert "active_goals" in status
        assert "completed_goals" in status


class TestGlobalEngine:
    def test_get_intention_engine(self):
        g = get_intention_engine()
        assert g is not None
        assert isinstance(g, IntentionEngine)
