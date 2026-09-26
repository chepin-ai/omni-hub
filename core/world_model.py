"""
OMNI-HUB World Model v55
Internal environment simulation.

Prediction is the foundation of perception.
This module builds an internal model of the environment —
predicting future states before they arrive.

Philosophy: 预测是感知的基础 — Prediction is the foundation of perception.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from copy import deepcopy
import math


@dataclass
class StatePrediction:
    """A predicted future state."""
    steps_ahead: int
    predicted_state: Dict[str, float]
    confidence: float
    basis: str


class TransitionLearner:
    """Learns state transition patterns from history."""

    def __init__(self):
        self.transitions: Dict[str, List[Tuple[float, float]]] = {}

    def learn(self, history: List[Dict[str, Any]], var: str):
        """Learn transitions for a variable."""
        pairs = []
        for i in range(len(history) - 1):
            s1 = history[i].get('state', history[i])
            s2 = history[i+1].get('state', history[i+1])
            v1 = s1.get(var)
            v2 = s2.get(var)
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                pairs.append((v1, v2))
        self.transitions[var] = pairs

    def predict(self, var: str, current: float, steps: int = 1) -> Optional[float]:
        """Predict next value based on learned transitions."""
        pairs = self.transitions.get(var, [])
        if len(pairs) < 5:
            return None

        # Find similar starting points and average their deltas
        deltas = []
        for v1, v2 in pairs:
            if abs(v1 - current) < 0.1:
                deltas.append(v2 - v1)

        if not deltas:
            # Fallback: use average delta
            deltas = [v2 - v1 for v1, v2 in pairs]

        avg_delta = sum(deltas) / len(deltas)
        return current + avg_delta * steps


class WorldModel:
    """
    Internal model of the environment for prediction.
    """

    PREDICTABLE_VARS = ["level", "energy", "phi", "line_coherence"]

    def __init__(self):
        self.learner = TransitionLearner()
        self.predictions: List[StatePrediction] = []
        self.prediction_accuracy = 0.5
        self.total_predictions = 0
        self.correct_predictions = 0

    def learn_from_history(self, history: List[Dict[str, Any]]):
        """Learn transition patterns from history."""
        for var in self.PREDICTABLE_VARS:
            self.learner.learn(history, var)

    def predict(self, current_state: Dict[str, Any], steps_ahead: int = 5) -> StatePrediction:
        """Predict future state."""
        predicted = {}
        confidences = []

        for var in self.PREDICTABLE_VARS:
            current = current_state.get(var)
            if not isinstance(current, (int, float)):
                continue

            pred = self.learner.predict(var, current, steps=steps_ahead)
            if pred is not None:
                predicted[var] = pred
                # Confidence based on number of training samples
                pairs = self.learner.transitions.get(var, [])
                conf = min(0.9, len(pairs) / 50.0)
                confidences.append(conf)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.3

        prediction = StatePrediction(
            steps_ahead=steps_ahead,
            predicted_state=predicted,
            confidence=avg_confidence,
            basis="transition_learning",
        )
        self.predictions.append(prediction)
        self.total_predictions += 1
        return prediction

    def verify(self, predicted: StatePrediction, actual_state: Dict[str, Any]):
        """Verify prediction against actual state."""
        matches = 0
        total = 0

        for var, pred_val in predicted.predicted_state.items():
            actual = actual_state.get(var)
            if isinstance(actual, (int, float)) and isinstance(pred_val, (int, float)):
                total += 1
                if abs(actual - pred_val) / max(abs(actual), 1e-10) < 0.2:
                    matches += 1

        if total > 0:
            accuracy = matches / total
            self.correct_predictions += accuracy
            self.prediction_accuracy = self.correct_predictions / self.total_predictions

    def get_trajectory(self, current_state: Dict[str, Any], steps: int = 5) -> List[Dict[str, float]]:
        """Get predicted trajectory over multiple steps."""
        trajectory = []
        state = {k: v for k, v in current_state.items() if isinstance(v, (int, float))}

        for step in range(1, steps + 1):
            pred = self.predict(current_state, steps_ahead=step)
            trajectory.append(pred.predicted_state)

        return trajectory

    def get_status(self) -> Dict[str, Any]:
        return {
            "predictions": self.total_predictions,
            "accuracy": round(self.prediction_accuracy, 3),
            "learned_vars": len(self.learner.transitions),
            "trajectory_available": self.total_predictions > 0,
        }


_wm_engine = None

def get_world_model():
    global _wm_engine
    if _wm_engine is None:
        _wm_engine = WorldModel()
    return _wm_engine
