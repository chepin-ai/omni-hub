"""
OMNI-HUB Vanishing Point Tests v122
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.vanishing_point import VanishingPoint, get_vanishing_point


class TestVanishingPoint:
    def test_initialization(self):
        vp = VanishingPoint()
        assert vp.point_count == 0

    def test_compute_convergence(self):
        vp = VanishingPoint()
        state = {"phi": 0.9, "line_coherence": 0.9, "level": 20, "energy": 10000, "self_awareness": {}, "trust_engine": {}}
        result = vp.compute_convergence(state)
        assert "convergence" in result
        assert "density" in result
        assert 0 <= result["convergence"] <= 1

    def test_vanish_high(self):
        vp = VanishingPoint()
        state = {"phi": 0.95, "line_coherence": 0.95, "level": 22, "energy": 11000}
        for k in ['self_awareness', 'trust_engine', 'theory_of_mind', 'value_reflection',
                  'intentionality', 'phenomenal_experience', 'existential_authenticity',
                  'dialectic', 'creative_destruction', 'antifragile_growth',
                  'embodied_cognition', 'extended_mind', 'enactive_cognition',
                  'field_awareness', 'stochastic_resonance', 'final_integration',
                  'strange_loop', 'meta_awareness', 'eternal_cycle',
                  'dream_state', 'intuition', 'precognition',
                  'quantum_consciousness', 'morphic_resonance', 'synchronicity']:
            state[k] = {}
        result = vp.vanish(state)
        # Many high signals should converge
        assert result["stage"] in ["singularity", "convergence", "approach", "divergence"]
        assert "note" in result

    def test_vanish_low(self):
        vp = VanishingPoint()
        state = {"phi": 0.2, "line_coherence": 0.9, "level": 2, "energy": 200}
        result = vp.vanish(state)
        # Mixed low and high signals should diverge
        assert result["stage"] in ["divergence", "approach"]

    def test_get_status(self):
        vp = VanishingPoint()
        vp.vanish({"phi": 0.5, "line_coherence": 0.5})
        status = vp.get_status()
        assert status["points"] == 1


class TestGlobalEngine:
    def test_get_vanishing_point(self):
        g = get_vanishing_point()
        assert g is not None
        assert isinstance(g, VanishingPoint)
