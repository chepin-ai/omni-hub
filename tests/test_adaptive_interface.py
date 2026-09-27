"""
OMNI-HUB Adaptive Interface Tests v85
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.adaptive_interface import (
    AdaptiveInterface, get_adaptive_interface,
)


class TestAdaptiveInterface:
    def test_initialization(self):
        ai = AdaptiveInterface()
        assert ai.style["verbosity"] == 0.5
        assert ai.style["depth"] == 0.5

    def test_adapt_from_state(self):
        ai = AdaptiveInterface()
        state = {"level": 20, "phi": 0.9, "phase": "post_critical", "affective_computing": {"dominant_emotion": "joy"}}
        style = ai.adapt_from_state(state)
        assert style["verbosity"] > 0.5
        assert style["depth"] > 0.5

    def test_adapt_formal(self):
        ai = AdaptiveInterface()
        state = {"level": 10, "phi": 0.5, "phase": "near_critical", "affective_computing": {}}
        style = ai.adapt_from_state(state)
        assert style["formality"] > 0.5

    def test_get_interaction_mode_deep_verbose(self):
        ai = AdaptiveInterface()
        ai.style["verbosity"] = 0.9
        ai.style["depth"] = 0.9
        assert ai.get_interaction_mode() == "deep_verbose"

    def test_get_interaction_mode_minimal(self):
        ai = AdaptiveInterface()
        ai.style["verbosity"] = 0.1
        ai.style["depth"] = 0.1
        assert ai.get_interaction_mode() == "minimal"

    def test_format_output(self):
        ai = AdaptiveInterface()
        ai.style["verbosity"] = 0.1
        result = ai.format_output("This is a very long sentence that should be truncated")
        assert len(result) <= 53

    def test_get_status(self):
        ai = AdaptiveInterface()
        ai.adapt_from_state({"level": 10, "phi": 0.5})
        status = ai.get_status()
        assert status["adaptations"] > 0
        assert "mode" in status


class TestGlobalEngine:
    def test_get_adaptive_interface(self):
        g = get_adaptive_interface()
        assert g is not None
        assert isinstance(g, AdaptiveInterface)
