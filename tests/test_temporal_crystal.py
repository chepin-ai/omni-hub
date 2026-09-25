"""
OMNI-HUB Temporal Crystal Tests v44
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
import math
from core.temporal_crystal import (
    OscillationMode, TemporalCrystal, TemporalCrystalEngine, get_temporal_crystal,
)


class TestTemporalCrystal:
    def test_initialization(self):
        tc = TemporalCrystal()
        assert len(tc.modes) == 4

    def test_oscillate(self):
        tc = TemporalCrystal()
        result = tc.oscillate(0)
        assert "phi_pulse" in result
        assert "energy_breath" in result

    def test_oscillation_values(self):
        tc = TemporalCrystal()
        result = tc.oscillate(0)
        for v in result.values():
            assert -1.0 <= v <= 1.0

    def test_periodicity(self):
        tc = TemporalCrystal()
        r1 = tc.oscillate(0)
        r2 = tc.oscillate(100)
        # At period boundary, values should be similar
        assert abs(r1["phi_pulse"] - r2["phi_pulse"]) < 0.1

    def test_energy_harvested(self):
        tc = TemporalCrystal()
        initial = tc.energy_harvested
        tc.oscillate(0)
        assert tc.energy_harvested > initial

    def test_rhythm(self):
        tc = TemporalCrystal()
        rhythm = tc.get_rhythm()
        assert "modes" in rhythm
        assert "frequencies" in rhythm


class TestTemporalCrystalEngine:
    def test_initialization(self):
        engine = TemporalCrystalEngine()
        assert engine.crystal.oscillation_count == 0

    def test_pulse(self):
        engine = TemporalCrystalEngine()
        state = {"phi": 0.5, "energy": 100.0}
        result = engine.pulse(0, state)
        assert "oscillations" in result
        assert "modifications" in result

    def test_phi_modification(self):
        engine = TemporalCrystalEngine()
        state = {"phi": 0.5, "energy": 100.0}
        result = engine.pulse(0, state)
        mod = result["modifications"]
        assert "phi" in mod
        assert 0.0 <= mod["phi"] <= 1.0

    def test_energy_modification(self):
        engine = TemporalCrystalEngine()
        state = {"phi": 0.5, "energy": 100.0}
        result = engine.pulse(0, state)
        mod = result["modifications"]
        assert "energy" in mod
        assert mod["energy"] > 0

    def test_get_status(self):
        engine = TemporalCrystalEngine()
        status = engine.get_status()
        assert "crystal" in status


class TestGlobalEngine:
    def test_get_temporal_crystal(self):
        g = get_temporal_crystal()
        assert g is not None
        assert isinstance(g, TemporalCrystalEngine)
