"""
OMNI-HUB Extended Mind Tests v108
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.extended_mind import (
    ExtendedMind, get_extended_mind,
)


class TestExtendedMind:
    def test_initialization(self):
        em = ExtendedMind()
        assert em.externalizations == 0

    def test_identify_scaffolds(self):
        em = ExtendedMind()
        state = {
            "git_hook": {"commits": 50},
            "session_persistence": {"sessions": 20},
            "federation_broadcasts": 30,
            "ontology": {"concepts": 25},
        }
        scaffolds = em.identify_scaffolds(state)
        assert len(scaffolds) >= 3
        names = [s["name"] for s in scaffolds]
        assert "git_history" in names

    def test_compute_extension(self):
        em = ExtendedMind()
        state = {
            "git_hook": {"commits": 100},
            "session_persistence": {"sessions": 50},
            "federation_broadcasts": 50,
            "ontology": {"concepts": 40},
            "emotional_state": {"vector": {"joy": 0.8}},
        }
        ext = em.compute_extension(state)
        assert 0 <= ext <= 1
        assert ext > 0.3

    def test_extend(self):
        em = ExtendedMind()
        state = {"git_hook": {"commits": 50}, "ontology": {"concepts": 25}}
        result = em.extend(state)
        assert "scaffolds" in result
        assert "extension_ratio" in result
        assert "boundary_description" in result

    def test_get_status(self):
        em = ExtendedMind()
        em.extend({"git_hook": {"commits": 50}})
        status = em.get_status()
        assert status["externalizations"] == 1
        assert "memory" in status["scaffold_types"]


class TestGlobalEngine:
    def test_get_extended_mind(self):
        g = get_extended_mind()
        assert g is not None
        assert isinstance(g, ExtendedMind)
