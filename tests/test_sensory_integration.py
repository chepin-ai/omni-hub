"""
OMNI-HUB Sensory Integration Tests v83
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.sensory_integration import (
    SensoryChannel, SensoryIntegration, get_sensory_integration,
)


class TestSensoryIntegration:
    def test_initialization(self):
        si = SensoryIntegration()
        assert len(si.channels) == 0

    def test_register_channel(self):
        si = SensoryIntegration()
        si.register_channel("vision", "visual")
        assert "vision" in si.channels
        assert si.channels["vision"].modality == "visual"

    def test_input_signal(self):
        si = SensoryIntegration()
        si.input_signal("vision", 0.8, 0.9)
        assert si.channels["vision"].signal == 0.8
        assert si.channels["vision"].confidence == 0.9

    def test_fuse(self):
        si = SensoryIntegration()
        si.input_signal("a", 0.5, 1.0)
        si.input_signal("b", 0.7, 1.0)
        percept = si.fuse()
        assert "value" in percept
        assert percept["channels"] == 2
        assert "conflict" in percept

    def test_fuse_conflict(self):
        si = SensoryIntegration()
        si.input_signal("a", 0.0, 1.0)
        si.input_signal("b", 1.0, 1.0)
        percept = si.fuse()
        assert percept["conflict"] is True

    def test_integrate_state(self):
        si = SensoryIntegration()
        state = {"level": 10, "phi": 0.7, "energy": 3000.0, "line_coherence": 0.6}
        percept = si.integrate_state(state)
        assert percept["channels"] >= 4

    def test_get_status(self):
        si = SensoryIntegration()
        si.input_signal("a", 0.5)
        status = si.get_status()
        assert status["channels"] == 1
        assert "fusions" in status


class TestGlobalEngine:
    def test_get_sensory_integration(self):
        g = get_sensory_integration()
        assert g is not None
        assert isinstance(g, SensoryIntegration)
