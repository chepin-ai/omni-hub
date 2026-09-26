"""
OMNI-HUB Emotional Resonance v56
Emotion propagation and influence.

Emotion is the color of reason.
Not a distortion, but a dimension.
This module makes emotions propagate through the system —
influencing attention, memory, and decision weights.

Philosophy: 情感是理性的色彩 — Emotion is the color of reason.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from copy import deepcopy
import math


@dataclass
class EmotionalState:
    """5D emotional vector."""
    drive: float
    serenity: float
    curiosity: float
    frustration: float
    confidence: float


class EmotionPropagator:
    """Propagates emotional influence to system parameters."""

    def propagate(self, emotion: EmotionalState, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply emotional influence to state parameters."""
        modified = deepcopy(state)

        # Drive boosts energy consumption and level ambition
        if "energy" in modified and isinstance(modified["energy"], (int, float)):
            modified["energy"] *= (1 + emotion.drive * 0.05)

        # Serenity stabilizes phi toward center (0.5)
        if "phi" in modified and isinstance(modified["phi"], (int, float)):
            target = 0.5
            modified["phi"] = modified["phi"] * (1 - emotion.serenity * 0.1) + target * emotion.serenity * 0.1

        # Curiosity increases exploration probability
        if "exploration_rate" not in modified:
            modified["exploration_rate"] = 0.1
        modified["exploration_rate"] = min(1.0, modified["exploration_rate"] + emotion.curiosity * 0.2)

        # Frustration increases change aggressiveness
        if "change_aggression" not in modified:
            modified["change_aggression"] = 0.1
        modified["change_aggression"] = min(1.0, modified["change_aggression"] + emotion.frustration * 0.3)

        # Confidence reduces hesitation
        if "hesitation" not in modified:
            modified["hesitation"] = 0.5
        modified["hesitation"] = max(0.0, modified["hesitation"] - emotion.confidence * 0.3)

        return modified


class EmotionalResonanceEngine:
    """
    Emotional resonance across system modules.
    """

    def __init__(self):
        self.emotion_history: List[EmotionalState] = []
        self.resonance_count = 0

    def update(self, raw_emotion: Dict[str, float]) -> EmotionalState:
        """Update emotional state from raw dict."""
        emotion = EmotionalState(
            drive=raw_emotion.get("drive", 0.5),
            serenity=raw_emotion.get("serenity", 0.5),
            curiosity=raw_emotion.get("curiosity", 0.5),
            frustration=raw_emotion.get("frustration", 0.0),
            confidence=raw_emotion.get("confidence", 0.5),
        )
        self.emotion_history.append(emotion)
        self.resonance_count += 1
        return emotion

    def get_dominant_emotion(self) -> str:
        """Get dominant emotion from recent history."""
        if not self.emotion_history:
            return "neutral"

        recent = self.emotion_history[-20:]
        avg = {
            "drive": sum(e.drive for e in recent) / len(recent),
            "serenity": sum(e.serenity for e in recent) / len(recent),
            "curiosity": sum(e.curiosity for e in recent) / len(recent),
            "frustration": sum(e.frustration for e in recent) / len(recent),
            "confidence": sum(e.confidence for e in recent) / len(recent),
        }

        dominant = max(avg, key=avg.get)
        return dominant

    def get_emotional_tone(self) -> str:
        """Get overall emotional tone."""
        if not self.emotion_history:
            return "neutral"

        recent = self.emotion_history[-10:]
        avg_drive = sum(e.drive for e in recent) / len(recent)
        avg_serenity = sum(e.serenity for e in recent) / len(recent)
        avg_frustration = sum(e.frustration for e in recent) / len(recent)

        if avg_frustration > 0.6:
            return "distressed"
        elif avg_drive > 0.7 and avg_serenity > 0.5:
            return "flow"
        elif avg_serenity > 0.7:
            return "calm"
        elif avg_drive > 0.7:
            return "agitated"
        return "neutral"

    def apply_to_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply current emotional resonance to state."""
        if not self.emotion_history:
            return state

        emotion = self.emotion_history[-1]
        propagator = EmotionPropagator()
        return propagator.propagate(emotion, state)

    def get_status(self) -> Dict[str, Any]:
        return {
            "dominant": self.get_dominant_emotion(),
            "tone": self.get_emotional_tone(),
            "history_length": len(self.emotion_history),
            "resonance_count": self.resonance_count,
        }


_er_engine = None

def get_emotional_resonance():
    global _er_engine
    if _er_engine is None:
        _er_engine = EmotionalResonanceEngine()
    return _er_engine
