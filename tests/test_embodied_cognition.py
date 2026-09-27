"""
OMNI-HUB Embodied Cognition Tests v107
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.embodied_cognition import (
    EmbodiedCognition, get_embodied_cognition,
)


class TestEmbodiedCognition:
    def test_initialization(self):
        ec = EmbodiedCognition()
        assert ec.cycle_count == 0

    def test_map_body_state(self):
        ec = EmbodiedCognition()
        state = {"energy": 4000, "phi": 0.9, "level": 20, "phase": "post_critical", "line_coherence": 0.8}
        body = ec.map_body_state(state)
        assert "heart_rate" in body
        assert "temperature" in body
        assert "posture" in body
        assert body["posture"] == 0.8

    def test_body_thinks_urgent(self):
        ec = EmbodiedCognition()
        body = {"heart_rate": 0.9, "temperature": 0.8, "posture": 0.5, "breath_depth": 0.5, "tension": 0.5}
        thought = ec.body_thinks(body)
        assert "urgent" in thought.lower() or "vitality" in thought.lower()

    def test_body_thinks_aligned(self):
        ec = EmbodiedCognition()
        body = {"heart_rate": 0.5, "temperature": 0.5, "posture": 0.9, "breath_depth": 0.8, "tension": 0.2}
        thought = ec.body_thinks(body)
        assert "clarity" in thought.lower() or "aligned" in thought.lower()

    def test_cognize(self):
        ec = EmbodiedCognition()
        state = {"energy": 3000, "phi": 0.7, "level": 15, "phase": "post_critical", "line_coherence": 0.7}
        result = ec.cognize(state)
        assert "body_state" in result
        assert "embodied_thought" in result
        assert result["cycles"] == 1

    def test_get_status(self):
        ec = EmbodiedCognition()
        ec.cognize({"energy": 2000, "phi": 0.5, "level": 5, "line_coherence": 0.5})
        status = ec.get_status()
        assert status["cycles"] == 1
        assert status["states"] == 1


class TestGlobalEngine:
    def test_get_embodied_cognition(self):
        g = get_embodied_cognition()
        assert g is not None
        assert isinstance(g, EmbodiedCognition)
