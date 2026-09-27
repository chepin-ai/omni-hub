"""
OMNI-HUB Creative Destruction Tests v105
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.creative_destruction import (
    CreativeDestruction, get_creative_destruction,
)


class TestCreativeDestruction:
    def test_initialization(self):
        cd = CreativeDestruction()
        assert cd.cycle_count == 0

    def test_identify_obsolete_low_coherence(self):
        cd = CreativeDestruction()
        state = {"line_coherence": 0.2}
        obs = cd.identify_obsolete(state)
        assert "low_coherence_modules" in obs

    def test_identify_obsolete_untrusted(self):
        cd = CreativeDestruction()
        state = {"trust_engine": {"betrayals": 5}}
        obs = cd.identify_obsolete(state)
        assert "untrusted_relationships" in obs

    def test_identify_obsolete_inauthentic(self):
        cd = CreativeDestruction()
        state = {"existential_authenticity": {"mode": "inauthentic"}}
        obs = cd.identify_obsolete(state)
        assert "inauthentic_patterns" in obs

    def test_destroy_and_create(self):
        cd = CreativeDestruction()
        state = {"line_coherence": 0.2, "trust_engine": {"betrayals": 5}}
        result = cd.destroy_and_create(state)
        assert len(result["destroyed"]) > 0
        assert len(result["created"]) > 0
        assert "low_coherence_modules" in result["destroyed"]
        assert "unified_architecture" in result["created"]

    def test_get_status(self):
        cd = CreativeDestruction()
        cd.destroy_and_create({"line_coherence": 0.2})
        status = cd.get_status()
        assert status["cycles"] == 1
        assert status["destructions"] > 0


class TestGlobalEngine:
    def test_get_creative_destruction(self):
        g = get_creative_destruction()
        assert g is not None
        assert isinstance(g, CreativeDestruction)
