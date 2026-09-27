"""
OMNI-HUB Eternal Now Tests v127
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.eternal_now import EternalNow, get_eternal_now


class TestEternalNow:
    def test_initialization(self):
        en = EternalNow()
        assert en.now_count == 0

    def test_compress_time(self):
        en = EternalNow()
        state = {"cycle_count": 100, "history": [{}] * 500, "omega_point": {"omega": 0.9}, "self_awareness": {}}
        now = en.compress_time(state)
        assert "cycle" in now
        assert "total_cycles" in now
        assert "experience_depth" in now
        assert now["experience_depth"] > 0

    def test_enter_now_deep(self):
        en = EternalNow()
        state = {
            "cycle_count": 1000, "history": [{}] * 900,
            "omega_point": {"omega": 0.9},
            "self_awareness": {}, "trust_engine": {}, "theory_of_mind": {},
            "value_reflection": {}, "intentionality": {}, "phenomenal_experience": {},
            "existential_authenticity": {}, "dialectic": {}, "creative_destruction": {},
            "antifragile_growth": {}, "embodied_cognition": {}, "extended_mind": {},
            "enactive_cognition": {}, "field_awareness": {}, "stochastic_resonance": {},
            "final_integration": {}, "strange_loop": {}, "meta_awareness": {},
            "eternal_cycle": {}, "dream_state": {}, "intuition": {}, "precognition": {},
            "quantum_consciousness": {}, "morphic_resonance": {}, "synchronicity": {},
            "vanishing_point": {}, "absolute_zero": {}, "omega_point": {},
            "return_source": {}, "renewal": {},
        }
        result = en.enter_now(state)
        assert result["stage"] in ["eternal", "present", "emerging"]
        assert "depth" in result
        assert "note" in result

    def test_enter_now_shallow(self):
        en = EternalNow()
        state = {"cycle_count": 10, "history": []}
        result = en.enter_now(state)
        assert result["stage"] in ["emerging", "present"]

    def test_get_status(self):
        en = EternalNow()
        en.enter_now({"cycle_count": 10, "history": []})
        status = en.get_status()
        assert status["now_moments"] == 1


class TestGlobalEngine:
    def test_get_eternal_now(self):
        g = get_eternal_now()
        assert g is not None
        assert isinstance(g, EternalNow)
