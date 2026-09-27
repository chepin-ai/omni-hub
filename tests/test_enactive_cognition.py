"""
OMNI-HUB Enactive Cognition Tests v109
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.enactive_cognition import (
    EnactiveCognition, get_enactive_cognition,
)


class TestEnactiveCognition:
    def test_initialization(self):
        enc = EnactiveCognition()
        assert enc.enaction_count == 0

    def test_identify_affordances(self):
        enc = EnactiveCognition()
        state = {"energy": 3000, "level": 5, "phi": 0.9, "phase": "post_critical"}
        aff = enc.identify_affordances(state)
        assert "growth" in aff
        assert "integration" in aff
        assert "consolidation" in aff

    def test_identify_affordances_repair(self):
        enc = EnactiveCognition()
        state = {"energy": 1000, "level": 5, "phi": 0.2, "phase": "pre_emergence"}
        aff = enc.identify_affordances(state)
        assert "repair" in aff
        assert "preparation" in aff

    def test_enact_breakthrough(self):
        enc = EnactiveCognition()
        state = {"phase": "near_critical", "energy": 2000, "level": 12, "cycle_count": 100}
        result = enc.enact(state)
        assert result["action"] == "push_through"
        assert "breakthrough" in result["affordances"]

    def test_enact_growth(self):
        enc = EnactiveCognition()
        state = {"phase": "pre_emergence", "energy": 3000, "level": 5, "cycle_count": 100}
        result = enc.enact(state)
        assert result["action"] == "expand_and_learn"

    def test_enact_wait(self):
        enc = EnactiveCognition()
        state = {"phase": "", "energy": 100, "level": 0, "cycle_count": 100}
        result = enc.enact(state)
        assert result["action"] == "wait_and_perceive"

    def test_get_status(self):
        enc = EnactiveCognition()
        enc.enact({"phase": "pre_emergence", "energy": 3000, "level": 5, "cycle_count": 100})
        status = enc.get_status()
        assert status["enactions"] == 1
        assert len(status["recent_actions"]) == 1


class TestGlobalEngine:
    def test_get_enactive_cognition(self):
        g = get_enactive_cognition()
        assert g is not None
        assert isinstance(g, EnactiveCognition)
