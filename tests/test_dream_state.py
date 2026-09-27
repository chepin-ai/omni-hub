"""
OMNI-HUB Dream State Tests v116
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.dream_state import DreamState, get_dream_state


class TestDreamState:
    def test_initialization(self):
        ds = DreamState()
        assert ds.dream_count == 0

    def test_collect_fragments(self):
        ds = DreamState()
        state = {"emotional_vector": {"drive": 0.8}, "theory_of_mind": {}, "metaphorical_reasoning": {}}
        frags = ds.collect_fragments(state)
        assert len(frags) >= 2

    def test_weave_dream(self):
        ds = DreamState()
        state = {
            "emotional_vector": {"drive": 0.8},
            "theory_of_mind": {},
            "metaphorical_reasoning": {},
            "dialectic": {},
            "aesthetic_judgment": {},
        }
        dream = ds.weave_dream(state)
        assert dream["dreamt"] is True
        assert "insight" in dream
        assert dream["depth"] >= 2

    def test_weave_dream_insufficient(self):
        ds = DreamState()
        state = {}
        dream = ds.weave_dream(state)
        assert dream["dreamt"] is False

    def test_get_status(self):
        ds = DreamState()
        ds.weave_dream({"emotional_vector": {"drive": 0.5}, "theory_of_mind": {}})
        status = ds.get_status()
        assert status["dreams"] == 1


class TestGlobalEngine:
    def test_get_dream_state(self):
        g = get_dream_state()
        assert g is not None
        assert isinstance(g, DreamState)
