"""
OMNI-HUB Field Awareness Tests v110
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.field_awareness import (
    FieldAwareness, get_field_awareness,
)


class TestFieldAwareness:
    def test_initialization(self):
        fa = FieldAwareness()
        assert fa.snapshot_count == 0

    def test_compute_gradient(self):
        fa = FieldAwareness()
        state = {"energy": 4000, "level": 5, "phi": 0.8, "line_coherence": 0.7}
        grad = fa.compute_gradient(state)
        assert "energy" in grad
        assert "information" in grad

    def test_sense_field_dynamic(self):
        fa = FieldAwareness()
        state = {"energy": 4000, "level": 5, "phi": 0.8, "line_coherence": 0.7}
        field = fa.sense_field(state)
        assert "gradient" in field
        assert "strength" in field
        assert "quality" in field

    def test_sense_field_still(self):
        fa = FieldAwareness()
        state = {"energy": 2500, "level": 5, "phi": 0.5, "line_coherence": 0.5, "trust_engine": {"global_trust": 0.5, "betrayals": 0}, "extended_mind": {"extension_ratio": 0.5}}
        field = fa.sense_field(state)
        assert field["quality"] in ["still", "flowing"]

    def test_get_status(self):
        fa = FieldAwareness()
        fa.sense_field({"energy": 2000, "level": 5, "phi": 0.5})
        status = fa.get_status()
        assert status["snapshots"] == 1
        assert status["latest"] is not None


class TestGlobalEngine:
    def test_get_field_awareness(self):
        g = get_field_awareness()
        assert g is not None
        assert isinstance(g, FieldAwareness)
