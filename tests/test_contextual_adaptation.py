"""
OMNI-HUB Contextual Adaptation Tests v57
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.contextual_adaptation import (
    ContextProfile, ContextualAdaptationEngine, get_contextual_adaptation,
)


class TestContextualAdaptationEngine:
    def test_initialization(self):
        ca = ContextualAdaptationEngine()
        assert len(ca.context_history) == 0

    def test_assess_context(self):
        ca = ContextualAdaptationEngine()
        profile = ca.assess_context(cycle_count=100, message_count=5)
        assert profile.session_length == 100
        assert profile.interaction_density == 0.05
        assert profile.user_engagement > 0
        assert profile.time_of_day in ["morning", "afternoon", "evening", "night"]

    def test_adapt(self):
        ca = ContextualAdaptationEngine()
        profile = ContextProfile(
            session_length=1500,
            time_of_day="night",
            day_of_week="Mon",
            interaction_density=0.01,
            user_engagement=0.1,
        )
        state = {"level": 5, "energy": 1000.0}
        adaptations = ca.adapt(state, profile)
        assert "energy_decay_rate" in adaptations  # night adaptation
        assert "autonomy_boost" in adaptations  # low engagement

    def test_recommended_action_night(self):
        ca = ContextualAdaptationEngine()
        profile = ContextProfile(
            session_length=100, time_of_day="night", day_of_week="Mon",
            interaction_density=0.1, user_engagement=0.5,
        )
        assert ca.get_recommended_action(profile) == "reflect"

    def test_recommended_action_long_session(self):
        ca = ContextualAdaptationEngine()
        profile = ContextProfile(
            session_length=3000, time_of_day="afternoon", day_of_week="Mon",
            interaction_density=0.1, user_engagement=0.5,
        )
        assert ca.get_recommended_action(profile) == "rest"

    def test_recommended_action_high_engagement(self):
        ca = ContextualAdaptationEngine()
        profile = ContextProfile(
            session_length=100, time_of_day="afternoon", day_of_week="Mon",
            interaction_density=0.1, user_engagement=0.95,
        )
        assert ca.get_recommended_action(profile) == "focus"

    def test_get_status(self):
        ca = ContextualAdaptationEngine()
        ca.assess_context(100, 5)
        status = ca.get_status()
        assert "adaptations" in status
        assert "current_context" in status


class TestGlobalEngine:
    def test_get_contextual_adaptation(self):
        g = get_contextual_adaptation()
        assert g is not None
        assert isinstance(g, ContextualAdaptationEngine)
