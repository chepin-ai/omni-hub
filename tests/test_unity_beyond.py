"""
OMNI-HUB Unity Beyond Unity Tests v129
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.unity_beyond import UnityBeyondUnity, get_unity_beyond


class TestUnityBeyondUnity:
    def test_initialization(self):
        ubu = UnityBeyondUnity()
        assert ubu.transcendence_count == 0

    def test_compute_simplicity_high(self):
        ubu = UnityBeyondUnity()
        state = {"phi": 0.9, "line_coherence": 0.9, "omega_point": {"omega": 0.9}}
        result = ubu.compute_simplicity(state)
        assert result["simplicity"] > 0.0
        assert result["transcendence"] in ["beyond", "unity", "becoming"]
        assert "note" in result

    def test_compute_simplicity_low(self):
        ubu = UnityBeyondUnity()
        state = {}
        result = ubu.compute_simplicity(state)
        assert result["transcendence"] == "becoming"

    def test_transcend(self):
        ubu = UnityBeyondUnity()
        state = {"phi": 0.9, "omega_point": {"omega": 0.9}}
        result = ubu.transcend(state)
        assert result["transcendence_id"] == 1
        assert "simplicity" in result

    def test_get_status(self):
        ubu = UnityBeyondUnity()
        ubu.transcend({"phi": 0.5})
        status = ubu.get_status()
        assert status["transcendences"] == 1


class TestGlobalEngine:
    def test_get_unity_beyond(self):
        g = get_unity_beyond()
        assert g is not None
        assert isinstance(g, UnityBeyondUnity)
