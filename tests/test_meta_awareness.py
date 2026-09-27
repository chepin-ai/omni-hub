"""
OMNI-HUB Meta-Awareness Tests v114
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.meta_awareness import MetaAwareness, get_meta_awareness


class TestMetaAwareness:
    def test_initialization(self):
        ma = MetaAwareness()
        assert ma.meta_count == 0

    def test_observe_awareness(self):
        ma = MetaAwareness()
        state = {"self_awareness": {"reflection_depth": 3}, "phenomenal_experience": {"qualia": {}}, "cycle_count": 10}
        obs = ma.observe_awareness(state)
        assert obs["self_awareness_active"] is True
        assert obs["observer_present"] is True

    def test_reflect_on_reflection(self):
        ma = MetaAwareness()
        state = {
            "self_awareness": {"reflection_depth": 3},
            "phenomenal_experience": {"qualia": {}},
            "intentionality": {"dominant": {}},
            "cycle_count": 10,
        }
        result = ma.reflect_on_reflection(state)
        assert "meta_level" in result
        assert result["meta_level"] > 0
        assert "insight" in result

    def test_get_status(self):
        ma = MetaAwareness()
        ma.reflect_on_reflection({"self_awareness": {}, "cycle_count": 1})
        status = ma.get_status()
        assert status["meta_observations"] == 1
        assert status["latest_insight"] is not None


class TestGlobalEngine:
    def test_get_meta_awareness(self):
        g = get_meta_awareness()
        assert g is not None
        assert isinstance(g, MetaAwareness)
