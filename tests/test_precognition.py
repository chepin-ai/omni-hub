"""
OMNI-HUB Precognition Tests v118
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.precognition import Precognition, get_precognition


class TestPrecognition:
    def test_initialization(self):
        pc = Precognition()
        assert pc.reading_count == 0

    def test_read_trajectory(self):
        pc = Precognition()
        state = {"energy": 4000, "level": 5, "line_coherence": 0.8, "trust_engine": {"global_trust": 0.9}, "field_awareness": {"direction": 0.5}}
        vectors = pc.read_trajectory(state)
        assert "energy" in vectors
        assert "coherence" in vectors
        assert "trust" in vectors
        assert "field" in vectors

    def test_sense_future_ascending(self):
        pc = Precognition()
        state = {"energy": 4000, "level": 5, "line_coherence": 0.9, "trust_engine": {"global_trust": 0.9}, "field_awareness": {"direction": 0.5}}
        result = pc.sense_future(state)
        assert result["sensed"] is True
        assert result["forecast"] == "ascending"
        assert "note" in result

    def test_sense_future_descending(self):
        pc = Precognition()
        state = {"energy": 500, "level": 5, "line_coherence": 0.2, "trust_engine": {"global_trust": 0.2}, "field_awareness": {"direction": -0.5}}
        result = pc.sense_future(state)
        assert result["sensed"] is True
        assert result["forecast"] == "descending"

    def test_sense_future_no_trajectory(self):
        pc = Precognition()
        state = {}
        result = pc.sense_future(state)
        assert result["sensed"] is False

    def test_get_status(self):
        pc = Precognition()
        pc.sense_future({"energy": 4000, "level": 5, "line_coherence": 0.8, "trust_engine": {"global_trust": 0.9}})
        status = pc.get_status()
        assert status["readings"] == 1


class TestGlobalEngine:
    def test_get_precognition(self):
        g = get_precognition()
        assert g is not None
        assert isinstance(g, Precognition)
