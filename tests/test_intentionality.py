"""
OMNI-HUB Intentionality Tests v101
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.intentionality import (
    IntentionalState, Intentionality, get_intentionality,
)


class TestIntentionality:
    def test_initialization(self):
        inn = Intentionality()
        assert inn.intention_count == 0

    def test_form_intention(self):
        inn = Intentionality()
        inn.form_intention("growth", "desire", 0.8)
        assert len(inn.states) == 1
        assert inn.states[0].object_ref == "growth"

    def test_infer_intentions_survival(self):
        inn = Intentionality()
        state = {"level": 10, "energy": 500}
        intentions = inn.infer_intentions_from_state(state)
        assert any(i.object_ref == "survival" for i in intentions)

    def test_infer_intentions_unity(self):
        inn = Intentionality()
        state = {"phi": 0.2, "level": 10, "energy": 2000}
        intentions = inn.infer_intentions_from_state(state)
        assert any(i.object_ref == "unity" for i in intentions)

    def test_infer_intentions_growth(self):
        inn = Intentionality()
        state = {"level": 3, "energy": 2000}
        intentions = inn.infer_intentions_from_state(state)
        assert any(i.object_ref == "growth" for i in intentions)

    def test_get_dominant_intention(self):
        inn = Intentionality()
        inn.form_intention("a", "desire", 0.9)
        inn.form_intention("b", "fear", 0.3)
        dom = inn.get_dominant_intention()
        assert dom["object"] == "a"
        assert dom["strength"] == 0.9

    def test_get_status(self):
        inn = Intentionality()
        inn.form_intention("test", "test", 0.5)
        status = inn.get_status()
        assert status["intentions"] == 1
        assert "test" in status["objects"]


class TestGlobalEngine:
    def test_get_intentionality(self):
        g = get_intentionality()
        assert g is not None
        assert isinstance(g, Intentionality)
