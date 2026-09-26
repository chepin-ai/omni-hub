"""
OMNI-HUB Capability Assessment Tests v72
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.capability_assessment import (
    CapabilityAssessment, get_capability_assessment,
)


class TestCapabilityAssessment:
    def test_initialization(self):
        ca = CapabilityAssessment()
        assert len(ca.scores) == 10
        assert all(v == 0.5 for v in ca.scores.values())

    def test_assess_from_state(self):
        ca = CapabilityAssessment()
        state = {
            "identity": {"traits": ["curious"]},
            "learning_core": {"experiences": 20},
            "symbolic_reasoning": {"inferences": 5},
            "language_core": {"generations": 10},
        }
        scores = ca.assess_from_state(state)
        assert len(scores) == 10
        assert ca.assessment_count == 1

    def test_get_strengths(self):
        ca = CapabilityAssessment()
        ca.scores["self_awareness"] = 0.9
        ca.scores["learning"] = 0.8
        strengths = ca.get_strengths(threshold=0.7)
        assert "self_awareness" in strengths
        assert "learning" in strengths

    def test_get_weaknesses(self):
        ca = CapabilityAssessment()
        ca.scores["creativity"] = 0.2
        weaknesses = ca.get_weaknesses(threshold=0.4)
        assert "creativity" in weaknesses

    def test_get_improvement_areas(self):
        ca = CapabilityAssessment()
        ca.scores["planning"] = 0.3
        areas = ca.get_improvement_areas()
        assert len(areas) > 0
        assert areas[0]["capability"] == "planning"

    def test_get_status(self):
        ca = CapabilityAssessment()
        ca.assess_from_state({})
        status = ca.get_status()
        assert "assessments" in status
        assert "average_score" in status
        assert "strengths" in status
        assert "weaknesses" in status


class TestGlobalEngine:
    def test_get_capability_assessment(self):
        g = get_capability_assessment()
        assert g is not None
        assert isinstance(g, CapabilityAssessment)
