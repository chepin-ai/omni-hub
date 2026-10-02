"""OMNI-HUB v191 Tests — PredictiveWorldModel"""

import pytest
from core.predictive_world_model import (
    PredictiveWorldModel, StatePredictor, TrendExtrapolator,
    ScenarioSimulator, UncertaintyQuantifier, PredictionValidator,
    PredictionHorizon, ScenarioType, Prediction,
    get_predictive_world_model
)


class TestStatePredictor:
    def test_predict_next(self):
        sp = StatePredictor()
        val, ci = sp.predict_next([0.5, 0.6, 0.7, 0.8])
        assert 0 <= val <= 1
        assert ci[0] <= ci[1]

    def test_predict(self):
        sp = StatePredictor()
        p = sp.predict("x", [0.5, 0.6], PredictionHorizon.SHORT)
        assert isinstance(p, Prediction)
        assert p.variable == "x"


class TestTrendExtrapolator:
    def test_extrapolate(self):
        te = TrendExtrapolator()
        result = te.extrapolate([0.5, 0.6, 0.7], steps=5)
        assert len(result) == 5
        assert all(0 <= r <= 1 for r in result)


class TestScenarioSimulator:
    def test_simulate_baseline(self):
        ss = ScenarioSimulator()
        scen = ss.simulate({"l1": 0.5, "l2": 0.6}, ScenarioType.BASELINE, steps=5)
        assert scen.scenario_type == ScenarioType.BASELINE
        assert len(scen.trajectory) == 6

    def test_simulate_stress(self):
        ss = ScenarioSimulator()
        scen = ss.simulate({"l1": 0.5}, ScenarioType.STRESS, steps=3)
        assert scen.probability == 0.08

    def test_get_report(self):
        ss = ScenarioSimulator()
        ss.simulate({"l1": 0.5}, ScenarioType.BASELINE)
        r = ss.get_report()
        assert r["scenarios"] == 1


class TestUncertaintyQuantifier:
    def test_quantify(self):
        uq = UncertaintyQuantifier()
        preds = [Prediction("p1", "x", 0.7, PredictionHorizon.SHORT, (0.6, 0.8), 0)]
        r = uq.quantify(preds, {"x": 0.75})
        assert "x" in r

    def test_ensemble_uncertainty(self):
        uq = UncertaintyQuantifier()
        r = uq.ensemble_uncertainty([[0.5, 0.6], [0.7, 0.8]])
        assert r >= 0


class TestPredictionValidator:
    def test_validate(self):
        pv = PredictionValidator()
        preds = [Prediction("p1", "x", 0.7, PredictionHorizon.SHORT, (0.6, 0.8), 0)]
        r = pv.validate(preds, {"x": 0.75})
        assert "x" in r
        assert r["x"].mae == pytest.approx(0.05)

    def test_get_report(self):
        pv = PredictionValidator()
        assert pv.get_report()["validations"] == 0


class TestPredictiveWorldModel:
    def test_init(self):
        pwm = PredictiveWorldModel()
        assert pwm.VERSION == "191.0.0"

    def test_update_history(self):
        pwm = PredictiveWorldModel()
        pwm.update_history("x", 0.5)
        assert "x" in pwm.history

    def test_forecast(self):
        pwm = PredictiveWorldModel()
        pwm.update_history("x", 0.5)
        pwm.update_history("x", 0.6)
        p = pwm.forecast("x")
        assert 0 <= p.predicted_value <= 1

    def test_forecast_all(self):
        pwm = PredictiveWorldModel()
        pwm.update_history("a", 0.5)
        pwm.update_history("b", 0.6)
        preds = pwm.forecast_all(["a", "b"])
        assert len(preds) == 2

    def test_simulate_scenario(self):
        pwm = PredictiveWorldModel()
        pwm.update_history("a", 0.5)
        scen = pwm.simulate_scenario(["a"], ScenarioType.OPTIMISTIC)
        assert scen.scenario_type == ScenarioType.OPTIMISTIC

    def test_run_cycle(self):
        pwm = PredictiveWorldModel()
        r = pwm.run_cycle({"l1": 0.5, "l2": 0.6})
        assert r["cycle"] == 1
        assert "predictions" in r

    def test_get_status(self):
        pwm = PredictiveWorldModel()
        s = pwm.get_status()
        assert s["version"] == "191.0.0"

    def test_singleton(self):
        p1 = get_predictive_world_model()
        p2 = get_predictive_world_model()
        assert p1 is p2

# Total: 24 tests
