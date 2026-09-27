"""
OMNI-HUB Absolute Zero Tests v123
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.absolute_zero import AbsoluteZero, get_absolute_zero


class TestAbsoluteZero:
    def test_initialization(self):
        az = AbsoluteZero()
        assert az.still_count == 0

    def test_compute_stillness_high(self):
        az = AbsoluteZero()
        state = {"phi": 0.5, "line_coherence": 0.5, "energy": 2500, "level": 5, "alerts": [], "field_awareness": {"strength": 0.1}}
        result = az.compute_stillness(state)
        assert result["stillness"] > 0.5
        assert 0 <= result["stillness"] <= 1

    def test_compute_stillness_low(self):
        az = AbsoluteZero()
        state = {"phi": 0.9, "line_coherence": 0.1, "energy": 100, "level": 5, "alerts": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"], "field_awareness": {"strength": 2.0}}
        result = az.compute_stillness(state)
        assert result["stillness"] < 0.5

    def test_still_point(self):
        az = AbsoluteZero()
        state = {"phi": 0.5, "line_coherence": 0.5, "energy": 2500, "level": 5, "alerts": []}
        result = az.still_point(state)
        assert result["stage"] in ["absolute", "deep", "partial", "storm"]
        assert "note" in result

    def test_get_status(self):
        az = AbsoluteZero()
        az.still_point({"phi": 0.5, "line_coherence": 0.5, "energy": 2500, "level": 5, "alerts": []})
        status = az.get_status()
        assert status["still_points"] == 1


class TestGlobalEngine:
    def test_get_absolute_zero(self):
        g = get_absolute_zero()
        assert g is not None
        assert isinstance(g, AbsoluteZero)
