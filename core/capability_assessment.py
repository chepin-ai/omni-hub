"""
OMNI-HUB Capability Assessment v72
Self-evaluation of strengths and weaknesses.

Know thyself.
Not just who you are, but what you can do.
This module evaluates system capabilities —
strengths, weaknesses, limits, potentials.

Philosophy: 知人者智，自知者明 —
Knowing others is wisdom; knowing yourself is enlightenment.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class CapabilityAssessment:
    """
    Self-evaluation of system capabilities.
    """

    CAPABILITIES = [
        "self_awareness",
        "learning",
        "reasoning",
        "communication",
        "planning",
        "adaptation",
        "creativity",
        "ethics",
        "memory",
        "perception",
    ]

    def __init__(self):
        self.scores: Dict[str, float] = {}
        self.history: List[Dict[str, Any]] = []
        self.assessment_count = 0
        self._init_scores()

    def _init_scores(self):
        """Initialize capability scores."""
        for cap in self.CAPABILITIES:
            self.scores[cap] = 0.5

    def assess_from_state(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Assess capabilities from system state."""
        # Self-awareness
        identity = state.get('identity', {})
        if identity and identity.get('traits'):
            self.scores["self_awareness"] = min(1.0, self.scores["self_awareness"] + 0.05)

        # Learning
        learning = state.get('learning_core', {})
        if learning and learning.get('experiences', 0) > 10:
            self.scores["learning"] = min(1.0, self.scores["learning"] + 0.03)

        # Reasoning
        symbolic = state.get('symbolic_reasoning', {})
        if symbolic and symbolic.get('inferences', 0) > 0:
            self.scores["reasoning"] = min(1.0, self.scores["reasoning"] + 0.02)

        # Communication
        language = state.get('language_core', {})
        if language and language.get('generations', 0) > 0:
            self.scores["communication"] = min(1.0, self.scores["communication"] + 0.03)

        # Planning
        executive = state.get('executive_function', {})
        if executive and executive.get('tasks', 0) > 0:
            self.scores["planning"] = min(1.0, self.scores["planning"] + 0.02)

        # Adaptation
        evolution = state.get('evolutionary_optimizer', {})
        if evolution and evolution.get('generation', 0) > 0:
            self.scores["adaptation"] = min(1.0, self.scores["adaptation"] + 0.03)

        # Creativity
        creative = state.get('creative_synthesis', {})
        if creative and creative.get('ideas', 0) > 0:
            self.scores["creativity"] = min(1.0, self.scores["creativity"] + 0.02)

        # Ethics
        ethics = state.get('ethical_framework', {})
        if ethics and ethics.get('evaluations', 0) > 0:
            self.scores["ethics"] = min(1.0, self.scores["ethics"] + 0.02)

        # Memory
        episodic = state.get('episodic_memory', {})
        if episodic and episodic.get('episodes', 0) > 0:
            self.scores["memory"] = min(1.0, self.scores["memory"] + 0.03)

        # Perception
        attention = state.get('attention_evolution', {})
        if attention and attention.get('focus_count', 0) > 0:
            self.scores["perception"] = min(1.0, self.scores["perception"] + 0.02)

        self.assessment_count += 1
        self.history.append({k: round(v, 3) for k, v in self.scores.items()})

        return self.scores.copy()

    def get_strengths(self, threshold: float = 0.7) -> List[str]:
        """Get capabilities above threshold."""
        return [cap for cap, score in self.scores.items() if score >= threshold]

    def get_weaknesses(self, threshold: float = 0.4) -> List[str]:
        """Get capabilities below threshold."""
        return [cap for cap, score in self.scores.items() if score <= threshold]

    def get_improvement_areas(self) -> List[Dict[str, Any]]:
        """Get areas needing improvement."""
        weaknesses = self.get_weaknesses()
        return [
            {"capability": w, "current_score": round(self.scores[w], 3), "suggestion": f"strengthen_{w}"}
            for w in weaknesses
        ]

    def get_status(self) -> Dict[str, Any]:
        strengths = self.get_strengths()
        weaknesses = self.get_weaknesses()
        avg_score = sum(self.scores.values()) / len(self.scores)
        return {
            "assessments": self.assessment_count,
            "average_score": round(avg_score, 3),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "scores": {k: round(v, 3) for k, v in self.scores.items()},
            "improvement_areas": self.get_improvement_areas(),
        }


_ca_engine = None

def get_capability_assessment():
    global _ca_engine
    if _ca_engine is None:
        _ca_engine = CapabilityAssessment()
    return _ca_engine
