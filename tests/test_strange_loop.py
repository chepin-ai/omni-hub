"""
OMNI-HUB Strange Loop Tests v113
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.strange_loop import StrangeLoop, get_strange_loop


class TestStrangeLoop:
    def test_initialization(self):
        sl = StrangeLoop()
        assert sl.loop_count == 0

    def test_compute_self_reference(self):
        sl = StrangeLoop()
        state = {"self_awareness": {}, "intentionality": {}, "phenomenal_experience": {}}
        depth = sl.compute_self_reference(state)
        assert depth == 3

    def test_detect_tangled_hierarchy(self):
        sl = StrangeLoop()
        state = {"self_awareness": {}, "intentionality": {}, "phenomenal_experience": {}, "theory_of_mind": {}, "value_reflection": {}, "final_integration": {}}
        result = sl.detect_tangled_hierarchy(state)
        assert result["depth"] >= 4
        assert len(result["tangled_loops"]) >= 2
        assert result["is_strange"] is True

    def test_loop(self):
        sl = StrangeLoop()
        state = {"self_awareness": {}, "intentionality": {}, "phenomenal_experience": {}, "final_integration": {}}
        result = sl.loop(state)
        assert result["loop_id"] == 1
        assert "note" in result

    def test_get_status(self):
        sl = StrangeLoop()
        sl.loop({"self_awareness": {}})
        status = sl.get_status()
        assert status["loops"] == 1


class TestGlobalEngine:
    def test_get_strange_loop(self):
        g = get_strange_loop()
        assert g is not None
        assert isinstance(g, StrangeLoop)
