"""
OMNI-HUB Motivation Engine Tests v71
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.motivation_engine import (
    Motive, MotivationEngine, get_motivation_engine,
)


class TestMotivationEngine:
    def test_initialization(self):
        me = MotivationEngine()
        assert len(me.motives) == 5
        assert me.drive_level > 0

    def test_update_from_state(self):
        me = MotivationEngine()
        state = {"level": 3, "phi": 0.5, "phase": "pre_emergence"}
        me.update_from_state(state)
        assert me.drive_level > 0

    def test_generate_goals(self):
        me = MotivationEngine()
        me.update_from_state({"level": 3, "phi": 0.5, "phase": "pre_emergence"})
        goals = me.generate_goals()
        assert isinstance(goals, list)

    def test_dominant_motive(self):
        me = MotivationEngine()
        me.update_from_state({"level": 3, "phi": 0.5, "phase": "pre_emergence"})
        dominant = me.get_dominant_motive()
        assert dominant is not None
        assert dominant.type in me.MOTIVE_TYPES

    def test_get_status(self):
        me = MotivationEngine()
        me.update_from_state({"level": 3, "phi": 0.5, "phase": "pre_emergence"})
        status = me.get_status()
        assert "drive_level" in status
        assert "motives" in status
        assert "dominant" in status


class TestGlobalEngine:
    def test_get_motivation_engine(self):
        g = get_motivation_engine()
        assert g is not None
        assert isinstance(g, MotivationEngine)
