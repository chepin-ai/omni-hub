"""
OMNI-HUB Legacy Preservation Tests v82
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.legacy_preservation import (
    LegacyArtifact, LegacyPreservation, get_legacy_preservation,
)


class TestLegacyPreservation:
    def test_initialization(self):
        lp = LegacyPreservation()
        assert len(lp.artifacts) == 0

    def test_preserve_value_alignment(self):
        lp = LegacyPreservation()
        state = {"value_alignment": {"principles": ["beneficence", "autonomy"]}}
        lp.preserve_value_alignment(state, cycle=100)
        assert len(lp.artifacts) == 1
        assert lp.artifacts[0].category == "core_values"

    def test_preserve_strategies(self):
        lp = LegacyPreservation()
        state = {"meta_learning": {"strategy_scores": [{"name": "focus", "effectiveness": 0.8}]}}
        lp.preserve_strategies(state, cycle=100)
        assert any(a.category == "learned_strategies" for a in lp.artifacts)

    def test_build_legacy(self):
        lp = LegacyPreservation()
        state = {
            "value_alignment": {"principles": ["beneficence"]},
            "meta_learning": {"strategy_scores": []},
            "episodic_memory": {"episodes": ["e1", "e2"]},
            "ethical_framework": {"evaluations": 5},
            "architectural_evolution": {"nodes": 10},
        }
        legacy = lp.build_legacy(state, cycle=200)
        assert legacy["version"] == "82.0.0"
        assert legacy["cycle"] == 200
        assert legacy["compressed_categories"] > 0

    def test_build_legacy_compression(self):
        lp = LegacyPreservation()
        state = {"value_alignment": {"principles": ["p1"]}}
        lp.build_legacy(state, cycle=100)
        lp.build_legacy(state, cycle=200)
        # Should compress to one per category
        legacy = lp.build_legacy(state, cycle=300)
        assert legacy["compressed_categories"] <= len(lp.LEGACY_CATEGORIES)

    def test_get_status(self):
        lp = LegacyPreservation()
        lp.preserve_value_alignment({"value_alignment": {"principles": ["test"]}}, 10)
        status = lp.get_status()
        assert status["artifacts"] == 1
        assert "core_values" in status["categories"]


class TestGlobalEngine:
    def test_get_legacy_preservation(self):
        g = get_legacy_preservation()
        assert g is not None
        assert isinstance(g, LegacyPreservation)
