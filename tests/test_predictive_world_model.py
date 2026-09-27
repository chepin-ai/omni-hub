"""
OMNI-HUB Predictive World Model Tests v95
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.predictive_world_model import (
    PredictiveWorldModel, get_predictive_world_model,
)


class TestPredictiveWorldModel:
    def test_initialization(self):
        pwm = PredictiveWorldModel()
        assert pwm.simulation_count == 0

    def test_simulate_step(self):
        pwm = PredictiveWorldModel()
        state = {"level": 5, "phi": 0.6, "energy": 2000, "phase": "pre_emergence"}
        next_state = pwm.simulate_step(state)
        assert "level" in next_state
        assert "energy" in next_state
        assert next_state["level"] > 5

    def test_simulate_trajectory(self):
        pwm = PredictiveWorldModel()
        state = {"level": 5, "phi": 0.6, "energy": 2000, "phase": "pre_emergence"}
        traj = pwm.simulate_trajectory(state, steps=5)
        assert len(traj) == 5
        assert traj[-1]["level"] > traj[0]["level"]

    def test_predict_critical_transition(self):
        pwm = PredictiveWorldModel()
        state = {"level": 2, "phi": 0.7, "phase": "pre_emergence"}
        pred = pwm.predict_critical_transition(state)
        assert "predicted_cycle" in pred
        assert pred["target_level"] == 3
        assert pred["confidence"] > 0

    def test_predict_at_maximum(self):
        pwm = PredictiveWorldModel()
        state = {"level": 25, "phi": 0.9, "phase": "singularity_convergence"}
        pred = pwm.predict_critical_transition(state)
        assert pred["predicted_cycle"] == -1

    def test_build_from_state(self):
        pwm = PredictiveWorldModel()
        state = {"level": 5, "phi": 0.6, "energy": 2000, "phase": "pre_emergence"}
        result = pwm.build_from_state(state)
        assert "trajectory" in result
        assert "critical_prediction" in result
        assert result["simulations"] == 1

    def test_get_status(self):
        pwm = PredictiveWorldModel()
        state = {"level": 5, "phi": 0.6, "energy": 2000, "phase": "pre_emergence"}
        pwm.build_from_state(state)
        status = pwm.get_status()
        assert status["simulations"] == 1
        assert status["predictions"] == 1


class TestGlobalEngine:
    def test_get_predictive_world_model(self):
        g = get_predictive_world_model()
        assert g is not None
        assert isinstance(g, PredictiveWorldModel)
