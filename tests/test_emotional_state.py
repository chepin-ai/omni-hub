"""
OMNI-HUB Emotional State Tests v27
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.emotional_state import EmotionalVector, EmotionalState


class TestEmotionalVector:
    def test_default_creation(self):
        ev = EmotionalVector()
        assert ev.drive == 0.5
        assert ev.frustration == 0.0
        assert ev.valence() > 0

    def test_valence_positive(self):
        ev = EmotionalVector(drive=0.9, serenity=0.9, curiosity=0.9, confidence=0.9)
        assert ev.valence() > 0.5

    def test_valence_negative(self):
        ev = EmotionalVector(frustration=0.9)
        assert ev.valence() < 0.3

    def test_arousal(self):
        ev = EmotionalVector(drive=0.9, curiosity=0.9, frustration=0.9)
        assert ev.arousal() > 0.5

    def test_dominant_mood(self):
        ev = EmotionalVector(drive=0.9)
        assert ev.dominant_mood() == "drive"

    def test_frustrated_mood(self):
        ev = EmotionalVector(drive=0.9, frustration=0.7)
        assert "frustrated" in ev.dominant_mood()

    def test_as_dict(self):
        ev = EmotionalVector()
        d = ev.as_dict()
        assert "drive" in d
        assert "frustration" in d


class TestEmotionalState:
    def test_initialization(self):
        es = EmotionalState()
        assert es.current.drive == 0.5
        assert len(es.history) == 0

    def test_evolve_creates_history(self):
        es = EmotionalState()
        es.evolve("focus", "near_critical", 0.1, 5)
        assert len(es.history) == 1

    def test_evolve_affects_emotions(self):
        es = EmotionalState()
        initial_drive = es.current.drive
        es.evolve("focus", "near_critical", 0.1, 5)
        assert es.current.drive != initial_drive

    def test_frustration_decay(self):
        es = EmotionalState()
        es.current.frustration = 0.9
        es.evolve("rest", "pre_emergence", 0.0, 0)
        assert es.current.frustration < 0.9

    def test_action_bias(self):
        es = EmotionalState()
        bias = es.get_action_bias("focus")
        assert -0.5 <= bias <= 0.5

    def test_high_drive_bias(self):
        es = EmotionalState()
        es.current.drive = 0.9
        bias = es.get_action_bias("focus")
        assert bias > 0  # High drive favors focus

    def test_mood_report(self):
        es = EmotionalState()
        for _ in range(5):
            es.evolve("focus", "near_critical", 0.1, 10)
        report = es.get_mood_report()
        assert "current" in report
        assert "valence" in report
        assert "dominant_mood" in report
        assert "averages" in report

    def test_clamping(self):
        es = EmotionalState()
        for _ in range(100):
            es.evolve("focus", "asymptotic_infinity", 1.0, 25)
        assert 0.0 <= es.current.drive <= 1.0
        assert 0.0 <= es.current.confidence <= 1.0

    def test_trend_detection(self):
        es = EmotionalState()
        # Declining drive
        for i in range(20):
            es.evolve("rest", "pre_emergence", -0.1, 0)
        report = es.get_mood_report()
        assert "trends" in report
