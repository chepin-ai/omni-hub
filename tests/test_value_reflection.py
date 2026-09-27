"""
OMNI-HUB Value Reflection Tests v91
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.value_reflection import (
    ValueReflection, get_value_reflection,
)


class TestValueReflection:
    def test_initialization(self):
        vr = ValueReflection()
        assert len(vr.value_scores) == 7
        assert vr.value_scores["beneficence"] == 0.5

    def test_reflect_on_state(self):
        vr = ValueReflection()
        state = {
            "level": 10,
            "phase": "post_critical",
            "last_reward": 5,
            "trust_engine": {"global_trust": 0.8, "betrayals": 0},
            "risk_analyzer": {"risks_found": 1},
            "self_modifications": [1, 2, 3],
            "alignment_score": 0.9,
            "line_coherence": 0.7,
            "affective_computing": {"profile": {"serenity": 0.8}},
        }
        result = vr.reflect_on_state(state, cycle=100)
        assert "value_alignment" in result
        assert "coherence" in result
        assert result["coherence"] >= 0

    def test_evolve_values(self):
        vr = ValueReflection()
        for i in range(5):
            vr.coherence_history.append(0.5)
        vr.coherence_history.append(0.3)
        result = vr.evolve_values()
        assert result["intervention"] is True

    def test_no_evolve(self):
        vr = ValueReflection()
        for i in range(5):
            vr.coherence_history.append(0.5)
        vr.coherence_history.append(0.55)
        result = vr.evolve_values()
        assert result["intervention"] is False

    def test_dominant_value(self):
        vr = ValueReflection()
        vr.value_scores["truth"] = 0.9
        status = vr.get_status()
        assert status["dominant"] == "truth"

    def test_get_status(self):
        vr = ValueReflection()
        state = {"level": 5, "trust_engine": {"global_trust": 0.5}}
        vr.reflect_on_state(state, cycle=10)
        status = vr.get_status()
        assert status["reflections"] == 1
        assert "coherence" in status


class TestGlobalEngine:
    def test_get_value_reflection(self):
        g = get_value_reflection()
        assert g is not None
        assert isinstance(g, ValueReflection)
