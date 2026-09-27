"""
OMNI-HUB Intuition Tests v117
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.intuition import Intuition, get_intuition


class TestIntuition:
    def test_initialization(self):
        intu = Intuition()
        assert intu.hunch_count == 0

    def test_compress_patterns(self):
        intu = Intuition()
        state = {"energy": 4000, "level": 5, "phi": 0.8, "line_coherence": 0.9, "trust_engine": {"global_trust": 0.9, "betrayals": 0}, "alerts": []}
        compressed = intu.compress_patterns(state)
        assert "trust_gut" in compressed
        assert "energy_feel" in compressed
        assert "danger_sense" in compressed
        assert "opportunity_sense" in compressed

    def test_hunch(self):
        intu = Intuition()
        state = {"energy": 4000, "level": 5, "phi": 0.8, "line_coherence": 0.9, "trust_engine": {"global_trust": 0.9, "betrayals": 0}, "alerts": []}
        result = intu.hunch(state)
        assert result["hunch"] is True
        assert "message" in result
        assert "source" in result

    def test_hunch_no_patterns(self):
        intu = Intuition()
        state = {}
        result = intu.hunch(state)
        assert result["hunch"] is False

    def test_get_status(self):
        intu = Intuition()
        intu.hunch({"energy": 4000, "level": 5, "trust_engine": {"global_trust": 0.9}, "alerts": []})
        status = intu.get_status()
        assert status["hunches"] == 1


class TestGlobalEngine:
    def test_get_intuition(self):
        g = get_intuition()
        assert g is not None
        assert isinstance(g, Intuition)
