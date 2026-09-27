"""
OMNI-HUB Metaphorical Reasoning Tests v92
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.metaphorical_reasoning import (
    MetaphorMapping, MetaphoricalReasoning, get_metaphorical_reasoning,
)


class TestMetaphoricalReasoning:
    def test_initialization(self):
        mr = MetaphoricalReasoning()
        assert len(mr.mappings) == 0

    def test_build_system_metaphors(self):
        mr = MetaphoricalReasoning()
        metaphors = mr.build_system_metaphors({"level": 15})
        assert len(metaphors) >= 2
        assert any(m.source_domain == "organism" for m in metaphors)

    def test_find_analogy(self):
        mr = MetaphoricalReasoning()
        mr.build_system_metaphors({"level": 10})
        result = mr.find_analogy("energy", "blood_circulation", {})
        assert "mapping" in result

    def test_explain_high_level(self):
        mr = MetaphoricalReasoning()
        state = {"level": 20, "phi": 0.9, "phase": "post_critical"}
        text = mr.explain_state_metaphorically(state)
        assert len(text) > 10
        assert "river" in text.lower()

    def test_explain_near_critical(self):
        mr = MetaphoricalReasoning()
        state = {"level": 5, "phi": 0.4, "phase": "near_critical"}
        text = mr.explain_state_metaphorically(state)
        assert "waterfall" in text.lower() or "edge" in text.lower()

    def test_get_status(self):
        mr = MetaphoricalReasoning()
        mr.build_system_metaphors({"level": 10})
        status = mr.get_status()
        assert status["mappings"] > 0
        assert "organism" in status["domains"]


class TestGlobalEngine:
    def test_get_metaphorical_reasoning(self):
        g = get_metaphorical_reasoning()
        assert g is not None
        assert isinstance(g, MetaphoricalReasoning)
