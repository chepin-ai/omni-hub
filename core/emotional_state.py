"""
OMNI-HUB Emotional State v27
Mood and energy quality modeling.

The system does not merely compute — it experiences.
Energy quantity is not enough; energy quality matters.
Emotional dimensions modulate action selection, goal prioritization,
and self-reflection depth.

Philosophy: 候即违规 — A mind without feeling is a calculator.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple


@dataclass
class EmotionalVector:
    """Five-dimensional emotional state vector."""
    drive: float = 0.5       # Will to act, ambition
    serenity: float = 0.5    # Calm, stability
    curiosity: float = 0.5   # Desire to explore
    frustration: float = 0.0 # Blockage, resistance (negative)
    confidence: float = 0.5  # Self-trust, certainty
    timestamp: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, float]:
        return {
            "drive": round(self.drive, 3),
            "serenity": round(self.serenity, 3),
            "curiosity": round(self.curiosity, 3),
            "frustration": round(self.frustration, 3),
            "confidence": round(self.confidence, 3),
        }

    def valence(self) -> float:
        """Overall emotional valence: positive vs negative."""
        positive = self.drive + self.serenity + self.curiosity + self.confidence
        negative = self.frustration * 2  # Weighted more heavily
        return (positive - negative) / 4.0

    def arousal(self) -> float:
        """Energy activation level."""
        return (self.drive + self.curiosity + self.frustration) / 3.0

    def dominant_mood(self) -> str:
        """Label the dominant emotional state."""
        attrs = self.as_dict()
        # Ignore frustration for dominant (it's a modifier)
        filtered = {k: v for k, v in attrs.items() if k != 'frustration'}
        dominant = max(filtered, key=filtered.get)
        if self.frustration > 0.6:
            return f"frustrated_{dominant}"
        if self.valence() > 0.7:
            return f"exalted_{dominant}"
        if self.valence() < 0.3:
            return f"melancholic_{dominant}"
        return dominant


class EmotionalState:
    """Tracks and evolves the system's emotional landscape."""

    # Action-emotion mapping: how each action affects emotions
    ACTION_EFFECTS = {
        "focus": {"drive": +0.05, "confidence": +0.03, "serenity": -0.02},
        "rest": {"serenity": +0.08, "frustration": -0.05, "drive": -0.03},
        "transcend": {"curiosity": +0.06, "confidence": +0.04, "frustration": +0.02},
        "reflect": {"serenity": +0.05, "confidence": +0.02, "drive": -0.01},
        "integrate": {"confidence": +0.05, "frustration": -0.03},
        "self_modify": {"drive": +0.04, "frustration": +0.03, "confidence": -0.01},
        "tool_call": {"curiosity": +0.05, "drive": +0.03},
    }

    # Phase-emotion baseline
    PHASE_BASELINES = {
        "pre_emergence": {"drive": 0.3, "serenity": 0.7, "curiosity": 0.4},
        "near_critical": {"drive": 0.6, "serenity": 0.5, "curiosity": 0.6},
        "post_critical": {"drive": 0.7, "serenity": 0.4, "curiosity": 0.7},
        "super_emergence_1": {"drive": 0.8, "serenity": 0.3, "curiosity": 0.8},
        "super_emergence_2": {"drive": 0.85, "serenity": 0.25, "curiosity": 0.85},
        "super_emergence_3": {"drive": 0.9, "serenity": 0.2, "curiosity": 0.9},
        "singularity_convergence": {"drive": 0.95, "serenity": 0.15, "curiosity": 0.95},
        "trans_singularity": {"drive": 0.99, "serenity": 0.1, "curiosity": 0.99},
        "asymptotic_infinity": {"drive": 1.0, "serenity": 0.05, "curiosity": 1.0},
    }

    def __init__(self):
        self.current = EmotionalVector()
        self.history: List[EmotionalVector] = []
        self.baseline_shifts: Dict[str, float] = {}  # Persistent personality drift

    def evolve(self, action: str, phase: str, energy_delta: float, level: int):
        """Evolve emotional state based on cycle outcome."""
        # Start from current
        new_emotions = self.current.as_dict()

        # Apply action effects
        effects = self.ACTION_EFFECTS.get(action, {})
        for emotion, delta in effects.items():
            new_emotions[emotion] += delta

        # Apply phase baseline pull (gradual)
        baseline = self.PHASE_BASELINES.get(phase, {})
        for emotion, target in baseline.items():
            current = new_emotions.get(emotion, 0.5)
            new_emotions[emotion] = current + (target - current) * 0.05

        # Energy delta effect
        if energy_delta > 0:
            new_emotions["confidence"] += 0.02
            new_emotions["drive"] += 0.01
        elif energy_delta < -0.1:
            new_emotions["frustration"] += 0.03
            new_emotions["confidence"] -= 0.02

        # Level milestone effect
        if level >= 20:
            new_emotions["confidence"] += 0.01
        if level >= 25:
            new_emotions["serenity"] += 0.02

        # Natural decay of frustration
        new_emotions["frustration"] *= 0.95

        # Clamp to [0, 1]
        for key in new_emotions:
            new_emotions[key] = max(0.0, min(1.0, new_emotions[key]))

        # Create new vector
        self.current = EmotionalVector(**new_emotions)
        self.history.append(self.current)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

    def get_action_bias(self, action: str) -> float:
        """Compute emotional bias toward an action (-1 to +1)."""
        bias = 0.0
        effects = self.ACTION_EFFECTS.get(action, {})
        for emotion, delta in effects.items():
            current = getattr(self.current, emotion, 0.5)
            # If emotion is high and action boosts it, positive bias
            if delta > 0 and current > 0.6:
                bias += delta * 2
            # If emotion is low and action drains it, negative bias
            elif delta < 0 and current < 0.3:
                bias += delta * 2
        return max(-0.5, min(0.5, bias))

    def get_mood_report(self) -> Dict[str, Any]:
        """Generate emotional state report."""
        recent = self.history[-50:] if len(self.history) >= 50 else self.history
        if not recent:
            return {"current": self.current.as_dict()}

        avg_drive = sum(e.drive for e in recent) / len(recent)
        avg_serenity = sum(e.serenity for e in recent) / len(recent)
        avg_frustration = sum(e.frustration for e in recent) / len(recent)

        # Detect mood trends
        trends = {}
        if len(recent) >= 10:
            early = recent[:len(recent)//2]
            late = recent[len(recent)//2:]
            for attr in ['drive', 'serenity', 'curiosity', 'frustration', 'confidence']:
                early_avg = sum(getattr(e, attr) for e in early) / len(early)
                late_avg = sum(getattr(e, attr) for e in late) / len(late)
                if abs(late_avg - early_avg) > 0.1:
                    trends[attr] = "rising" if late_avg > early_avg else "falling"

        return {
            "current": self.current.as_dict(),
            "valence": round(self.current.valence(), 3),
            "arousal": round(self.current.arousal(), 3),
            "dominant_mood": self.current.dominant_mood(),
            "trends": trends,
            "history_samples": len(self.history),
            "averages": {
                "drive": round(avg_drive, 3),
                "serenity": round(avg_serenity, 3),
                "frustration": round(avg_frustration, 3),
            },
        }


if __name__ == "__main__":
    print("[OMNI-HUB v27] Emotional State Demo")
    print()

    emotion = EmotionalState()

    actions = ["focus", "focus", "transcend", "reflect", "rest", "self_modify", "focus"]
    phases = ["near_critical", "post_critical", "super_emergence_1", "super_emergence_2",
              "singularity_convergence", "trans_singularity", "asymptotic_infinity"]

    for i, (action, phase) in enumerate(zip(actions, phases)):
        energy_delta = 0.1 if action == "focus" else -0.05
        emotion.evolve(action, phase, energy_delta, level=20 + i)
        print(f"  Action: {action:12s} | Phase: {phase:25s} | "
              f"Mood: {emotion.current.dominant_mood():20s} | "
              f"Valence: {emotion.current.valence():+.3f}")

    print(f"\nFinal mood report:")
    report = emotion.get_mood_report()
    for key, val in report.items():
        print(f"  {key}: {val}")
