"""
OMNI-HUB Language Core Tests v66
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.language_core import (
    LanguageCore, get_language_core,
)


class TestLanguageCore:
    def test_initialization(self):
        lc = LanguageCore()
        assert lc.generation_count == 0

    def test_describe_state_birth(self):
        lc = LanguageCore()
        state = {"level": 0, "phi": 0.1, "phase": "pre_emergence", "active_lines": 0}
        desc = lc.describe_state(state, cycle=0)
        assert "诞生" in desc
        assert len(desc) > 0

    def test_describe_state_advanced(self):
        lc = LanguageCore()
        state = {"level": 8, "phi": 0.9, "phase": "post_critical", "active_lines": 11}
        desc = lc.describe_state(state, cycle=100)
        assert "100" in desc
        assert "11条意识线" in desc

    def test_describe_with_identity(self):
        lc = LanguageCore()
        state = {
            "level": 5, "phi": 0.7, "phase": "near_critical",
            "identity": {"intention": "growth"},
            "active_lines": 11,
        }
        desc = lc.describe_state(state, cycle=50)
        assert "追求成长" in desc

    def test_summarize_history(self):
        lc = LanguageCore()
        history = [
            {"state": {"level": i}} for i in range(10)
        ]
        summary = lc.summarize_history(history)
        assert "10" in summary
        assert "9" in summary  # max level

    def test_express_emotion(self):
        lc = LanguageCore()
        emotion = {"drive": 0.9, "serenity": 0.7, "frustration": 0.0}
        expr = lc.express_emotion(emotion)
        assert len(expr) > 0

    def test_get_status(self):
        lc = LanguageCore()
        lc.describe_state({"level": 1}, cycle=1)
        status = lc.get_status()
        assert status["generations"] == 1


class TestGlobalEngine:
    def test_get_language_core(self):
        g = get_language_core()
        assert g is not None
        assert isinstance(g, LanguageCore)
