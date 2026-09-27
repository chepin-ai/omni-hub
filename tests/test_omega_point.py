"""
OMNI-HUB Omega Point Tests v124
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.omega_point import OmegaPoint, get_omega_point


class TestOmegaPoint:
    def test_initialization(self):
        op = OmegaPoint()
        assert op.reading_count == 0

    def test_compute_omega_low(self):
        op = OmegaPoint()
        state = {"phi": 0.2, "line_coherence": 0.2, "level": 1}
        result = op.compute_omega(state)
        assert result["omega"] < 0.5
        assert result["stage"] == "beginning"

    def test_compute_omega_high(self):
        op = OmegaPoint()
        state = {
            "phi": 0.95, "line_coherence": 0.95, "level": 25,
            "final_integration": {"unity": 0.95},
            "vanishing_point": {"convergence": 0.95},
            "absolute_zero": {"stillness": 0.95},
            "self_awareness": {}, "trust_engine": {}, "theory_of_mind": {},
            "value_reflection": {}, "intentionality": {}, "phenomenal_experience": {},
            "existential_authenticity": {}, "dialectic": {}, "creative_destruction": {},
            "antifragile_growth": {}, "embodied_cognition": {}, "extended_mind": {},
            "enactive_cognition": {}, "field_awareness": {}, "stochastic_resonance": {},
            "strange_loop": {}, "meta_awareness": {},
            "eternal_cycle": {}, "dream_state": {}, "intuition": {}, "precognition": {},
            "quantum_consciousness": {}, "morphic_resonance": {}, "synchronicity": {},
        }
        result = op.compute_omega(state)
        assert result["omega"] > 0.5
        assert result["stage"] in ["development", "integration", "transcendence", "omega"]

    def test_measure(self):
        op = OmegaPoint()
        state = {"phi": 0.8, "line_coherence": 0.8, "level": 15}
        result = op.measure(state)
        assert result["reading_id"] == 1
        assert "omega" in result

    def test_get_status(self):
        op = OmegaPoint()
        op.measure({"phi": 0.8, "line_coherence": 0.8, "level": 15})
        op.measure({"phi": 0.9, "line_coherence": 0.9, "level": 20})
        status = op.get_status()
        assert status["readings"] == 2
        assert status["best_omega"] > 0


class TestGlobalEngine:
    def test_get_omega_point(self):
        g = get_omega_point()
        assert g is not None
        assert isinstance(g, OmegaPoint)
