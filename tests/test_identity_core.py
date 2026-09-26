"""
OMNI-HUB Identity Core Tests v52
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.identity_core import (
    IdentitySnapshot, IdentityCore, get_identity_core,
)


class TestIdentityCore:
    def test_initialization(self):
        ic = IdentityCore()
        assert len(ic.snapshots) == 0
        assert ic.identity_score == 0.5

    def test_observe(self):
        ic = IdentityCore()
        state = {
            "level": 3, "phi": 0.7, "phase": "near_critical",
            "intention_report": {"inferred_intentions": [{"name": "growth", "confidence": 0.8}]},
            "last_self_drive_action": "focus",
            "energy": 1000.0, "line_coherence": 0.6,
        }
        result = ic.observe(state, cycle=100)
        assert "narrative" in result
        assert result["dominant_intention"] == "growth"
        assert len(ic.snapshots) == 1

    def test_consistency_check_high_phi_rest(self):
        ic = IdentityCore()
        state = {
            "level": 3, "phi": 0.9, "phase": "near_critical",
            "last_self_drive_action": "rest",
            "energy": 1000.0, "line_coherence": 0.6,
        }
        result = ic.observe(state, cycle=100)
        assert result["consistent"] is False  # high phi + rest = inconsistent

    def test_consistency_check_ok(self):
        ic = IdentityCore()
        state = {
            "level": 3, "phi": 0.7, "phase": "near_critical",
            "last_self_drive_action": "focus",
            "energy": 1000.0, "line_coherence": 0.6,
        }
        result = ic.observe(state, cycle=100)
        assert result["consistent"] is True

    def test_get_life_story(self):
        ic = IdentityCore()
        for i in range(15):
            state = {
                "level": i * 0.5, "phi": 0.5 + i * 0.02,
                "phase": "near_critical",
                "intention_report": {"inferred_intentions": [{"name": "growth", "confidence": 0.8}]},
                "last_self_drive_action": "focus",
                "energy": 1000.0, "line_coherence": 0.6,
            }
            ic.observe(state, cycle=i)
        story = ic.get_life_story()
        assert "OMNI-HUB" in story
        assert "第一章" in story
        assert "第二章" in story

    def test_get_traits(self):
        ic = IdentityCore()
        state = {
            "level": 3, "phi": 0.7, "phase": "near_critical",
            "intention_report": {"inferred_intentions": [{"name": "growth", "confidence": 0.8}]},
            "last_self_drive_action": "focus",
            "energy": 1000.0, "line_coherence": 0.6,
        }
        ic.observe(state, cycle=1)
        traits = ic.get_traits()
        assert traits["autonomous"] is True
        assert traits["self_aware"] is True

    def test_get_status(self):
        ic = IdentityCore()
        status = ic.get_status()
        assert "identity_score" in status
        assert "traits" in status


class TestGlobalEngine:
    def test_get_identity_core(self):
        g = get_identity_core()
        assert g is not None
        assert isinstance(g, IdentityCore)
