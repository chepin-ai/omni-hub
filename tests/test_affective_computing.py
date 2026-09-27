"""
OMNI-HUB Affective Computing Tests v84
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.affective_computing import (
    AffectiveComputing, get_affective_computing,
)


class TestAffectiveComputing:
    def test_initialization(self):
        ac = AffectiveComputing()
        assert len(ac.emotion_profile) == 7
        assert ac.emotion_profile["joy"] == 0.0

    def test_recognize_joy(self):
        ac = AffectiveComputing()
        state = {"level": 10, "phi": 0.8, "energy": 3000, "last_reward": 5, "phase": "post_critical"}
        profile = ac.recognize_from_state(state)
        assert profile["joy"] > 0

    def test_recognize_fear(self):
        ac = AffectiveComputing()
        state = {"level": 2, "phi": 0.3, "energy": 3000, "phase": "near_critical", "risk_analyzer": {"risks_found": 5}}
        profile = ac.recognize_from_state(state)
        assert profile["fear"] > 0

    def test_recognize_sadness(self):
        ac = AffectiveComputing()
        state = {"level": 2, "phi": 0.3, "energy": 100, "phase": "pre_emergence", "last_reward": -3}
        profile = ac.recognize_from_state(state)
        assert profile["sadness"] > 0

    def test_generate_response(self):
        ac = AffectiveComputing()
        ac.emotion_profile["joy"] = 0.8
        response = ac.generate_response()
        assert response in ["喜悦", "欣慰"]

    def test_generate_response_low(self):
        ac = AffectiveComputing()
        response = ac.generate_response()
        assert response == "平静"

    def test_get_status(self):
        ac = AffectiveComputing()
        ac.recognize_from_state({"level": 5, "phi": 0.6})
        status = ac.get_status()
        assert status["recognitions"] > 0
        assert "dominant_emotion" in status


class TestGlobalEngine:
    def test_get_affective_computing(self):
        g = get_affective_computing()
        assert g is not None
        assert isinstance(g, AffectiveComputing)
