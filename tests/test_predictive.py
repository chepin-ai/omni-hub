"""
OMNI-HUB Predictive Analytics Tests v22
"""

import sys, math
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.predictive import PredictiveEngine


class TestPredictiveEngine:
    def test_insufficient_data(self):
        engine = PredictiveEngine()
        result = engine.predict([{"state": {"energy": 100}}] * 5)
        assert result["status"] == "insufficient_data"

    def test_energy_prediction(self):
        engine = PredictiveEngine()
        history = []
        energy = 1000.0
        for i in range(200):
            energy *= 1.01
            history.append({"cycle": i, "state": {"energy": energy, "phi": 0.5, "level": 15}})
        result = engine.predict(history, horizon=50)
        assert result["status"] == "predicted"
        assert "energy" in result["predictions"]
        assert result["predictions"]["energy"]["r2"] > 0.9

    def test_phi_crash_warning(self):
        engine = PredictiveEngine()
        history = []
        phi = 0.5
        for i in range(200):
            phi -= 0.002  # Steady decline
            history.append({"cycle": i, "state": {"energy": 1000, "phi": max(0.1, phi), "level": 15}})
        result = engine.predict(history, horizon=50)
        assert "phi_crash_predicted" in result["warnings"]
        assert "reflect" in result["recommendations"]

    def test_level_prediction(self):
        engine = PredictiveEngine()
        history = []
        energy = 1000.0
        level = 15
        for i in range(300):
            energy *= 1.02
            if energy > 2000 and level == 15:
                level = 16
            history.append({"cycle": i, "state": {"energy": energy, "phi": 0.5, "level": level}})
        result = engine.predict(history, horizon=50)
        assert "level" in result["predictions"]

    def test_anomaly_detection(self):
        engine = PredictiveEngine()
        history = []
        energy = 1000.0
        for i in range(100):
            if i == 50:
                energy *= 0.5  # Sudden drop
            else:
                energy *= 1.01
            history.append({"cycle": i, "state": {"energy": energy, "phi": 0.5, "level": 15}})
        anomalies = engine.detect_anomaly(history)
        assert len(anomalies) > 0
        assert anomalies[0]["type"] == "energy_drop"

    def test_no_anomaly_in_stable_data(self):
        engine = PredictiveEngine()
        history = []
        energy = 1000.0
        for i in range(100):
            energy *= 1.01
            history.append({"cycle": i, "state": {"energy": energy, "phi": 0.5, "level": 15}})
        anomalies = engine.detect_anomaly(history)
        assert len(anomalies) == 0

    def test_extract_series(self):
        engine = PredictiveEngine()
        history = [{"state": {"energy": 100}}, {"state": {"energy": 200}}]
        series = engine._extract_series(history, "energy")
        assert series == [100.0, 200.0]

    def test_extract_series_skips_invalid(self):
        engine = PredictiveEngine()
        history = [{"state": {"energy": float('inf')}}, {"state": {"energy": 100}}]
        series = engine._extract_series(history, "energy")
        assert series == [100.0]
