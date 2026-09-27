"""
OMNI-HUB Future Simulator Tests v74
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.future_simulator import (
    Scenario, FutureSimulator, get_future_simulator,
)


class TestFutureSimulator:
    def test_initialization(self):
        fs = FutureSimulator()
        assert fs.prediction_count == 0

    def test_simulate(self):
        fs = FutureSimulator()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0, "phase": "near_critical"}
        scenarios = fs.simulate(state, cycle=100)
        assert len(scenarios) == 3
        horizons = [s.horizon for s in scenarios]
        assert "short" in horizons
        assert "medium" in horizons
        assert "long" in horizons

    def test_short_term_prediction(self):
        fs = FutureSimulator()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0, "phase": "near_critical"}
        scenarios = fs.simulate(state, cycle=100)
        short = [s for s in scenarios if s.horizon == "short"][0]
        assert short.probability == 0.7
        assert short.predicted_state["level"] > 5

    def test_evaluate_prediction(self):
        fs = FutureSimulator()
        predicted = {"level": 5, "phi": 0.6, "energy": 1000.0}
        actual = {"level": 5.5, "phi": 0.65, "energy": 950.0}
        accuracy = fs.evaluate_prediction(predicted, actual)
        assert 0 <= accuracy <= 1

    def test_get_status(self):
        fs = FutureSimulator()
        fs.simulate({"level": 5, "phi": 0.6, "energy": 1000.0, "phase": "near_critical"}, 100)
        status = fs.get_status()
        assert status["predictions"] == 3
        assert "scenarios" in status


class TestGlobalEngine:
    def test_get_future_simulator(self):
        g = get_future_simulator()
        assert g is not None
        assert isinstance(g, FutureSimulator)
