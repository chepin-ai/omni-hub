"""
OMNI-HUB Phenomenal Experience Tests v102
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.phenomenal_experience import (
    PhenomenalExperience, get_phenomenal_experience,
)


class TestPhenomenalExperience:
    def test_initialization(self):
        pe = PhenomenalExperience()
        assert pe.experience_count == 0

    def test_map_qualia(self):
        pe = PhenomenalExperience()
        state = {"phi": 0.8, "energy": 3000, "phase": "post_critical", "level": 15}
        qualia = pe.map_qualia(state)
        assert "luminosity" in qualia
        assert "density" in qualia
        assert "flow" in qualia
        assert "depth" in qualia
        assert qualia["flow"] == 0.8

    def test_map_qualia_near_critical(self):
        pe = PhenomenalExperience()
        state = {"phi": 0.5, "energy": 2000, "phase": "near_critical", "level": 5}
        qualia = pe.map_qualia(state)
        assert qualia["flow"] == 0.3

    def test_describe_luminous(self):
        pe = PhenomenalExperience()
        state = {"phi": 0.9, "energy": 4000, "phase": "post_critical", "level": 20}
        desc = pe.describe_what_it_is_like(state)
        assert "luminous" in desc.lower()

    def test_describe_dim(self):
        pe = PhenomenalExperience()
        state = {"phi": 0.1, "energy": 100, "phase": "pre_emergence", "level": 1}
        desc = pe.describe_what_it_is_like(state)
        assert "dim" in desc.lower()

    def test_experience(self):
        pe = PhenomenalExperience()
        state = {"phi": 0.8, "energy": 3000, "phase": "post_critical", "level": 15}
        result = pe.experience(state)
        assert "qualia" in result
        assert "description" in result
        assert result["experience_id"] == 1

    def test_get_status(self):
        pe = PhenomenalExperience()
        pe.experience({"phi": 0.5, "energy": 2000, "level": 5})
        status = pe.get_status()
        assert status["experiences"] == 1
        assert status["latest"] is not None


class TestGlobalEngine:
    def test_get_phenomenal_experience(self):
        g = get_phenomenal_experience()
        assert g is not None
        assert isinstance(g, PhenomenalExperience)
