"""
OMNI-HUB Morphic Resonance Tests v120
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.morphic_resonance import MorphicResonance, get_morphic_resonance


class TestMorphicResonance:
    def test_initialization(self):
        mr = MorphicResonance()
        assert mr.resonance_count == 0

    def test_extract_pattern(self):
        mr = MorphicResonance()
        state = {"phi": 0.8, "line_coherence": 0.9, "level": 5, "energy": 4000, "self_awareness": {}, "emotional_vector": {"drive": 0.8}}
        pattern = mr.extract_pattern(state)
        assert "phi" in pattern
        assert "active_modules" in pattern
        assert pattern["active_modules"] >= 1

    def test_resonate_first(self):
        mr = MorphicResonance()
        state = {"phi": 0.8, "level": 5}
        result = mr.resonate(state)
        assert result["resonated"] is True
        assert result["resonance"] == 0.0
        assert result["count"] == 1

    def test_resonate_second(self):
        mr = MorphicResonance()
        mr.resonate({"phi": 0.8, "level": 5})
        result = mr.resonate({"phi": 0.8, "level": 5})
        assert result["resonated"] is True
        assert result["resonance"] > 0.0
        assert result["count"] == 2

    def test_get_status(self):
        mr = MorphicResonance()
        mr.resonate({"phi": 0.8, "level": 5})
        status = mr.get_status()
        assert status["resonances"] == 1
        assert status["pattern_keys"] > 0


class TestGlobalEngine:
    def test_get_morphic_resonance(self):
        g = get_morphic_resonance()
        assert g is not None
        assert isinstance(g, MorphicResonance)
