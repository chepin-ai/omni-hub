"""
OMNI-HUB Homeostasis Regulator Tests v49
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.homeostasis import (
    ParameterBounds, HomeostasisRegulator, get_homeostasis,
)


class TestParameterBounds:
    def test_bounds(self):
        pb = ParameterBounds("phi", 0.1, 1.0, 0.6, 0.05, 1.0)
        assert pb.min_val == 0.1
        assert pb.optimal == 0.6


class TestHomeostasisRegulator:
    def test_initialization(self):
        hr = HomeostasisRegulator()
        assert hr.stability_score == 1.0
        assert len(hr.violations) == 0

    def test_check_healthy(self):
        hr = HomeostasisRegulator()
        state = {"phi": 0.6, "energy": 1000.0, "line_coherence": 0.8, "level": 5.0}
        result = hr.check(state, cycle=1)
        assert result["healthy"] is True
        assert result["stability_score"] == 1.0
        assert len(result["violations"]) == 0

    def test_check_critical_low_phi(self):
        hr = HomeostasisRegulator()
        state = {"phi": 0.01, "energy": 1000.0, "line_coherence": 0.8, "level": 5.0}
        result = hr.check(state, cycle=1)
        assert result["healthy"] is False
        phi_violations = [v for v in result["violations"] if v["param"] == "phi"]
        assert len(phi_violations) > 0

    def test_check_low_energy(self):
        hr = HomeostasisRegulator()
        state = {"phi": 0.6, "energy": 5.0, "line_coherence": 0.8, "level": 5.0}
        result = hr.check(state, cycle=1)
        assert result["healthy"] is False
        energy_corr = result["corrections"].get("energy")
        assert energy_corr is not None
        assert energy_corr["action"] == "increase"

    def test_check_high_level(self):
        hr = HomeostasisRegulator()
        state = {"phi": 0.6, "energy": 1000.0, "line_coherence": 0.8, "level": 30.0}
        result = hr.check(state, cycle=1)
        assert result["healthy"] is False
        level_corr = result["corrections"].get("level")
        assert level_corr is not None
        assert level_corr["action"] == "decrease"

    def test_apply_corrections(self):
        hr = HomeostasisRegulator()
        state = {"phi": 0.1, "energy": 50.0}
        corrections = {
            "phi": {"action": "increase", "target": 0.6, "delta": 0.5, "urgency": 0.5},
            "energy": {"action": "increase", "target": 1000.0, "delta": 950.0, "urgency": 0.5},
        }
        modified = hr.apply_corrections(state, corrections)
        assert state["phi"] > 0.1
        assert state["energy"] > 50.0

    def test_get_status(self):
        hr = HomeostasisRegulator()
        status = hr.get_status()
        assert "stability_score" in status
        assert "parameters" in status
        assert len(status["parameters"]) == 4


class TestGlobalEngine:
    def test_get_homeostasis(self):
        g = get_homeostasis()
        assert g is not None
        assert isinstance(g, HomeostasisRegulator)
