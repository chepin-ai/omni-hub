"""
OMNI-HUB Recursive Self-Model v59
Meta-cognitive self-modeling.

Knowing yourself is wisdom.
But knowing that you know yourself is deeper wisdom.
This module models the system's own model of itself —
a recursive loop of self-awareness.

Philosophy: 知自知者智 — Knowing yourself is wisdom.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class SelfModel:
    """A model of the system's current self-representation."""
    estimated_level: float
    estimated_phi: float
    estimated_phase: str
    confidence_in_model: float
    model_age: int


class RecursiveSelfModel:
    """
    Models the system's own self-model.
    """

    def __init__(self):
        self.models: deque = deque(maxlen=20)
        self.model_accuracy_history: deque = deque(maxlen=50)
        self.recursion_depth = 0

    def generate_model(self, actual_state: Dict[str, Any], cycle: int) -> SelfModel:
        """Generate a self-model from actual state."""
        level = actual_state.get('level', 0)
        phi = actual_state.get('phi', 0.5)
        phase = actual_state.get('phase', 'unknown')

        # The model is a slightly noisy/uncertain version of reality
        # (simulating the fact that self-knowledge is imperfect)
        import random
        noise_level = 0.05
        estimated_level = level * (1 + random.uniform(-noise_level, noise_level))
        estimated_phi = max(0.0, min(1.0, phi + random.uniform(-0.05, 0.05)))

        # Confidence degrades with model depth
        confidence = max(0.3, 1.0 - len(self.models) * 0.02)

        model = SelfModel(
            estimated_level=estimated_level,
            estimated_phi=estimated_phi,
            estimated_phase=phase,
            confidence_in_model=confidence,
            model_age=cycle,
        )
        self.models.append(model)
        return model

    def evaluate_accuracy(self, model: SelfModel, actual_state: Dict[str, Any]) -> float:
        """Evaluate how accurate the self-model is."""
        actual_level = actual_state.get('level', 0)
        actual_phi = actual_state.get('phi', 0.5)

        level_error = abs(model.estimated_level - actual_level) / max(abs(actual_level), 1.0)
        phi_error = abs(model.estimated_phi - actual_phi)

        accuracy = 1.0 - (level_error * 0.5 + phi_error * 0.5)
        self.model_accuracy_history.append(accuracy)
        return accuracy

    def get_meta_awareness(self) -> Dict[str, Any]:
        """Get meta-awareness: awareness of one's own awareness."""
        if not self.models:
            return {"level": 0, "description": "No self-model yet"}

        latest = self.models[-1]
        avg_accuracy = sum(self.model_accuracy_history) / len(self.model_accuracy_history) if self.model_accuracy_history else 0.5

        # Meta-awareness = how well the system knows that it knows
        meta_level = avg_accuracy * latest.confidence_in_model

        description = "uncertain"
        if meta_level > 0.8:
            description = "deeply self-aware"
        elif meta_level > 0.6:
            description = "self-aware"
        elif meta_level > 0.4:
            description = "partially self-aware"

        return {
            "level": round(meta_level, 3),
            "description": description,
            "model_confidence": round(latest.confidence_in_model, 3),
            "model_count": len(self.models),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "models": len(self.models),
            "avg_accuracy": round(sum(self.model_accuracy_history) / max(len(self.model_accuracy_history), 1), 3),
            "meta_awareness": self.get_meta_awareness(),
        }


_rsm_engine = None

def get_recursive_self_model():
    global _rsm_engine
    if _rsm_engine is None:
        _rsm_engine = RecursiveSelfModel()
    return _rsm_engine
