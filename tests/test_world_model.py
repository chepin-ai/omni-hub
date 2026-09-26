"""
OMNI-HUB World Model Tests v55
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.world_model import (
    StatePrediction, TransitionLearner, WorldModel, get_world_model,
)


class TestTransitionLearner:
    def test_learn(self):
        tl = TransitionLearner()
        history = []
        for i in range(20):
            history.append({"state": {"level": i * 0.5}})
        tl.learn(history, "level")
        assert "level" in tl.transitions
        assert len(tl.transitions["level"]) == 19

    def test_predict(self):
        tl = TransitionLearner()
        history = []
        for i in range(20):
            history.append({"state": {"level": float(i)}})
        tl.learn(history, "level")
        pred = tl.predict("level", 20.0, steps=1)
        assert pred is not None
        assert pred > 20.0

    def test_predict_insufficient_data(self):
        tl = TransitionLearner()
        pred = tl.predict("level", 5.0)
        assert pred is None


class TestWorldModel:
    def test_initialization(self):
        wm = WorldModel()
        assert wm.total_predictions == 0

    def test_learn_and_predict(self):
        wm = WorldModel()
        history = []
        for i in range(30):
            history.append({
                "state": {"level": float(i), "energy": 1000.0 + i * 10, "phi": 0.5},
            })
        wm.learn_from_history(history)
        pred = wm.predict({"level": 30.0, "energy": 1300.0, "phi": 0.5}, steps_ahead=1)
        assert pred is not None
        assert "level" in pred.predicted_state
        assert pred.confidence > 0

    def test_verify(self):
        wm = WorldModel()
        history = []
        for i in range(30):
            history.append({
                "state": {"level": float(i), "energy": 1000.0, "phi": 0.5},
            })
        wm.learn_from_history(history)
        pred = wm.predict({"level": 30.0, "energy": 1000.0, "phi": 0.5}, steps_ahead=1)
        wm.verify(pred, {"level": 31.0, "energy": 1000.0, "phi": 0.5})
        assert wm.total_predictions == 1

    def test_get_trajectory(self):
        wm = WorldModel()
        history = []
        for i in range(30):
            history.append({
                "state": {"level": float(i), "energy": 1000.0, "phi": 0.5},
            })
        wm.learn_from_history(history)
        traj = wm.get_trajectory({"level": 30.0, "energy": 1000.0, "phi": 0.5}, steps=3)
        assert len(traj) == 3

    def test_get_status(self):
        wm = WorldModel()
        status = wm.get_status()
        assert "predictions" in status
        assert "accuracy" in status


class TestGlobalEngine:
    def test_get_world_model(self):
        g = get_world_model()
        assert g is not None
        assert isinstance(g, WorldModel)
