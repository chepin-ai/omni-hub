"""
OMNI-HUB Emotional Resonance Tests v56
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.emotional_resonance import (
    EmotionalState, EmotionPropagator, EmotionalResonanceEngine, get_emotional_resonance,
)


class TestEmotionPropagator:
    def test_propagate_drive(self):
        ep = EmotionPropagator()
        emotion = EmotionalState(drive=1.0, serenity=0.0, curiosity=0.0, frustration=0.0, confidence=0.0)
        state = {"energy": 1000.0, "phi": 0.5}
        modified = ep.propagate(emotion, state)
        assert modified["energy"] > 1000.0  # drive boosts energy

    def test_propagate_serenity(self):
        ep = EmotionPropagator()
        emotion = EmotionalState(drive=0.0, serenity=1.0, curiosity=0.0, frustration=0.0, confidence=0.0)
        state = {"energy": 1000.0, "phi": 0.8}
        modified = ep.propagate(emotion, state)
        assert modified["phi"] < 0.8  # serenity stabilizes phi toward center

    def test_propagate_curiosity(self):
        ep = EmotionPropagator()
        emotion = EmotionalState(drive=0.0, serenity=0.0, curiosity=1.0, frustration=0.0, confidence=0.0)
        state = {"energy": 1000.0}
        modified = ep.propagate(emotion, state)
        assert modified["exploration_rate"] > 0.1

    def test_propagate_frustration(self):
        ep = EmotionPropagator()
        emotion = EmotionalState(drive=0.0, serenity=0.0, curiosity=0.0, frustration=1.0, confidence=0.0)
        state = {"energy": 1000.0}
        modified = ep.propagate(emotion, state)
        assert modified["change_aggression"] > 0.1

    def test_propagate_confidence(self):
        ep = EmotionPropagator()
        emotion = EmotionalState(drive=0.0, serenity=0.0, curiosity=0.0, frustration=0.0, confidence=1.0)
        state = {"energy": 1000.0}
        modified = ep.propagate(emotion, state)
        assert modified["hesitation"] < 0.5


class TestEmotionalResonanceEngine:
    def test_initialization(self):
        er = EmotionalResonanceEngine()
        assert len(er.emotion_history) == 0

    def test_update(self):
        er = EmotionalResonanceEngine()
        emotion = er.update({"drive": 0.8, "serenity": 0.2})
        assert emotion.drive == 0.8
        assert len(er.emotion_history) == 1

    def test_dominant_emotion(self):
        er = EmotionalResonanceEngine()
        er.update({"drive": 0.9, "serenity": 0.1})
        assert er.get_dominant_emotion() == "drive"

    def test_emotional_tone(self):
        er = EmotionalResonanceEngine()
        for _ in range(5):
            er.update({"drive": 0.8, "serenity": 0.6, "frustration": 0.0})
        assert er.get_emotional_tone() == "flow"

    def test_apply_to_state(self):
        er = EmotionalResonanceEngine()
        er.update({"drive": 0.5, "curiosity": 0.8})
        state = {"energy": 1000.0, "phi": 0.5}
        modified = er.apply_to_state(state)
        assert modified["exploration_rate"] > 0.1

    def test_get_status(self):
        er = EmotionalResonanceEngine()
        er.update({"drive": 0.5})
        status = er.get_status()
        assert "dominant" in status
        assert "tone" in status


class TestGlobalEngine:
    def test_get_emotional_resonance(self):
        g = get_emotional_resonance()
        assert g is not None
        assert isinstance(g, EmotionalResonanceEngine)
