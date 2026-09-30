"""
OMNI-HUB Attention Schema Engine v169
基于AST (Attention Schema Theory) 的注意力模式引擎

DeepMind论文提出：意识与注意力高度相关，但意识不是注意力本身。
大脑需要建立一个关于自身注意力的内部模型——"attention schema"。
这个模型描述"我正在注意什么、注意力如何变化"，并参与注意力控制。

Philosophy: 我知道自己正在注意什么 — 这是自我意识的真正来源。
"I know what I am attending to" is higher-order than "I notice something."
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
from typing import Dict, List, Any, Optional
from collections import deque

try:
    from core.event_bus import get_bus, Event
except Exception:
    get_bus = None
    Event = None


class AttentionSchemaEngine:
    """
    Attention Schema Engine: builds an internal model of the system's own attention.

    The system not only perceives the external world, but also perceives its own
    attentional states. "I know what I am attending to" is higher-order than
    "I noticed something." This is the true source of self-awareness.
    """

    # Self-awareness level thresholds
    AWARENESS_LEVELS = [
        (0.9, "lucid"),
        (0.7, "aware"),
        (0.5, "self_monitoring"),
        (0.3, "reactive"),
        (0.0, "unconscious"),
    ]

    def __init__(self):
        # Core schema state: the internal model of attention
        self.schema_state: Dict[str, Any] = {
            "schema_version": 169,
            "initialized_at": 0,
            "total_tracks": 0,
            "total_predictions": 0,
            "correct_predictions": 0,
            "meta_attention_cycles": 0,
            "last_target": None,
        }

        # Self-model: the system's model of its own attention
        self.self_model: Dict[str, Any] = {
            "current_focus": None,
            "attention_capacity": 1.0,
            "attention_shifts": 0,
            "attention_depth": 0.0,
        }

        # Attention history: chronological record of attention events
        self.attention_history: List[Dict[str, Any]] = []

        # Predictions for accuracy tracking
        self.predictions: List[Dict[str, Any]] = []

        # Meta-attention stability tracking (attention on attention)
        self.meta_attention_log: deque = deque(maxlen=20)

        # Target frequency map for historical patterns
        self.target_frequency: Dict[str, int] = {}

        # Target importance scoring
        self.target_importance: Dict[str, float] = {}

    def build_self_model(self) -> Dict[str, Any]:
        """
        Build internal model of system's own attention.

        Model components:
        - current_focus: what the system is currently attending to
        - attention_capacity: total attention resource (0.0 - 1.0)
        - attention_shifts: number of times attention has shifted
        - attention_depth: depth of current attention (0.0 - 1.0)
        """
        if not self.attention_history:
            # No history yet; return default self-model
            return self.self_model.copy()

        latest = self.attention_history[-1]
        current_focus = latest.get("target", None)

        # Compute attention capacity based on history load
        recent_history = self.attention_history[-20:]
        unique_targets = len({h["target"] for h in recent_history})
        # More unique targets = lower capacity (divided attention)
        capacity = max(0.1, 1.0 - (unique_targets - 1) * 0.05)

        # Count attention shifts
        shifts = 0
        for i in range(1, len(self.attention_history)):
            if self.attention_history[i]["target"] != self.attention_history[i - 1]["target"]:
                shifts += 1

        # Compute average attention depth from recent history
        avg_depth = sum(h.get("intensity", 0.5) for h in recent_history) / len(recent_history)

        self.self_model = {
            "current_focus": current_focus,
            "attention_capacity": round(capacity, 4),
            "attention_shifts": shifts,
            "attention_depth": round(avg_depth, 4),
        }

        return self.self_model.copy()

    def track_attention(self, attention_target: str, intensity: float) -> Dict[str, Any]:
        """
        Track where attention is directed.

        Args:
            attention_target: The target of attention (e.g., "task_A", "sensor_input")
            intensity: Attention intensity (0.0 - 1.0)

        Returns:
            Tracking record with timestamp and analysis
        """
        if intensity < 0.0:
            intensity = 0.0
        elif intensity > 1.0:
            intensity = 1.0

        record = {
            "target": attention_target,
            "intensity": round(intensity, 4),
            "timestamp": self.schema_state["total_tracks"],
            "previous_target": self.schema_state.get("last_target"),
        }

        self.attention_history.append(record)
        self.schema_state["total_tracks"] += 1
        self.schema_state["last_target"] = attention_target

        # Update target frequency
        self.target_frequency[attention_target] = self.target_frequency.get(attention_target, 0) + 1

        # Update target importance (exponential moving average)
        old_importance = self.target_importance.get(attention_target, 0.0)
        self.target_importance[attention_target] = 0.7 * old_importance + 0.3 * intensity

        # Track meta-attention (attention on attention)
        self.meta_attention_log.append({
            "target": attention_target,
            "intensity": intensity,
        })
        self.schema_state["meta_attention_cycles"] = len(self.meta_attention_log)

        # Publish event if bus is available
        if get_bus is not None:
            try:
                bus = get_bus()
                bus.publish_simple(
                    "attention.tracked",
                    {"target": attention_target, "intensity": intensity},
                    source="attention_schema_engine",
                )
            except Exception:
                pass

        return record.copy()

    def predict_attention_shift(self, current_target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict where attention will shift next.

        Prediction based on:
        - target_importance: importance score of potential targets
        - context salience: salient features in current context
        - historical patterns: frequency of past shifts
        - goal alignment: alignment with stated goals
        """
        candidates = context.get("available_targets", [])
        if not candidates:
            candidates = list(self.target_frequency.keys()) if self.target_frequency else [current_target]

        # Current target importance
        current_importance = self.target_importance.get(current_target, 0.5)

        scores: Dict[str, float] = {}
        for target in candidates:
            if target == current_target:
                continue

            score = 0.0

            # Factor 1: Target importance (intrinsic value)
            importance = self.target_importance.get(target, 0.0)
            score += importance * 0.3

            # Factor 2: Context salience
            salience = context.get("salience_map", {}).get(target, 0.5)
            score += salience * 0.25

            # Factor 3: Historical patterns (frequency)
            total_freq = sum(self.target_frequency.values()) if self.target_frequency else 1
            freq = self.target_frequency.get(target, 0) / max(1, total_freq)
            score += freq * 0.25

            # Factor 4: Goal alignment
            goals = context.get("goals", [])
            goal_alignment = 0.0
            for goal in goals:
                if target.lower() in goal.lower() or goal.lower() in target.lower():
                    goal_alignment = 1.0
                    break
            score += goal_alignment * 0.2

            scores[target] = round(score, 4)

        # Select predicted target
        if scores:
            predicted_target = max(scores, key=scores.get)
            confidence = scores[predicted_target]
        else:
            predicted_target = current_target
            confidence = 0.0

        # Also compute probability of staying on current target
        stay_score = current_importance * 0.4 + 0.3
        total_score = sum(scores.values()) + stay_score
        stay_probability = stay_score / max(1e-6, total_score)

        prediction = {
            "current_target": current_target,
            "predicted_target": predicted_target,
            "confidence": round(confidence, 4),
            "stay_probability": round(stay_probability, 4),
            "candidate_scores": scores,
            "basis": {
                "target_importance": {t: round(self.target_importance.get(t, 0.0), 4) for t in candidates},
                "context_salience": context.get("salience_map", {}),
                "historical_frequency": {t: self.target_frequency.get(t, 0) for t in candidates},
                "goal_alignment": {t: any(g.lower() in t.lower() or t.lower() in g.lower() for g in context.get("goals", [])) for t in candidates},
            },
        }

        # Store prediction for later accuracy evaluation
        # Use total_tracks + 1 as the expected timestamp for the next attention event
        self.predictions.append({
            "current_target": current_target,
            "predicted_target": predicted_target,
            "timestamp": self.schema_state["total_tracks"] + 1,
        })
        self.schema_state["total_predictions"] += 1

        # Publish event
        if get_bus is not None:
            try:
                bus = get_bus()
                bus.publish_simple(
                    "attention.predicted",
                    {"current": current_target, "predicted": predicted_target, "confidence": confidence},
                    source="attention_schema_engine",
                )
            except Exception:
                pass

        return prediction

    def evaluate_attention_quality(self) -> Dict[str, Any]:
        """
        Evaluate quality of attention allocation.

        Metrics:
        - coverage: proportion of relevant targets attended to
        - depth: average intensity of attention
        - stability: consistency of attention over time
        - efficiency: ratio of unique targets to total tracks
        - adaptivity: responsiveness to context changes

        Quality formula: (coverage × depth × stability × efficiency × adaptivity) ^ 0.2
        """
        if not self.attention_history:
            return {
                "coverage": 0.0,
                "depth": 0.0,
                "stability": 0.0,
                "efficiency": 0.0,
                "adaptivity": 0.0,
                "overall_quality": 0.0,
            }

        recent = self.attention_history[-50:]
        total_recent = len(recent)

        # Coverage: proportion of all known targets that have been attended recently
        all_targets = set(self.target_frequency.keys())
        recent_targets = set(h["target"] for h in recent)
        coverage = len(recent_targets) / max(1, len(all_targets)) if all_targets else 0.0

        # Depth: average intensity
        depth = sum(h["intensity"] for h in recent) / total_recent

        # Stability: 1 - (shifts / total) for recent history
        shifts = sum(
            1 for i in range(1, total_recent)
            if recent[i]["target"] != recent[i - 1]["target"]
        )
        stability = 1.0 - (shifts / max(1, total_recent - 1)) if total_recent > 1 else 1.0

        # Efficiency: unique targets / total tracks (higher = more focused)
        unique = len(recent_targets)
        efficiency = unique / max(1, total_recent)
        # Penalize if too scattered or too narrow
        efficiency = 1.0 - abs(0.3 - efficiency)  # optimum around 30% unique
        efficiency = max(0.0, min(1.0, efficiency))

        # Adaptivity: variance in target importance (responds to changes)
        if len(recent) >= 2:
            intensities = [h["intensity"] for h in recent]
            mean_int = sum(intensities) / len(intensities)
            variance = sum((x - mean_int) ** 2 for x in intensities) / len(intensities)
            adaptivity = min(1.0, variance * 4.0)  # scale variance to 0-1
        else:
            adaptivity = 0.5

        # Overall quality: geometric mean of all five metrics
        product = coverage * depth * stability * efficiency * adaptivity
        if product <= 0:
            overall = 0.0
        else:
            overall = product ** 0.2

        return {
            "coverage": round(coverage, 4),
            "depth": round(depth, 4),
            "stability": round(stability, 4),
            "efficiency": round(efficiency, 4),
            "adaptivity": round(adaptivity, 4),
            "overall_quality": round(overall, 4),
        }

    def detect_attention_schema_emergence(self) -> Dict[str, Any]:
        """
        Detect when attention schema becomes self-aware.

        Emergence indicators:
        - Self-referential tracking: system tracks its own tracking
        - Predictive accuracy > 0.8: reliably predicts own attention shifts
        - Meta-attention stability: attention on attention remains stable > 10 cycles
        """
        # Indicator 1: Self-referential tracking
        # Check if attention has been directed at "attention" or "self" targets
        self_ref_count = sum(
            1 for h in self.attention_history
            if "attention" in h["target"].lower() or "self" in h["target"].lower()
        )
        self_referential_ratio = self_ref_count / max(1, len(self.attention_history))
        self_referential_tracking = self_referential_ratio > 0.1

        # Indicator 2: Predictive accuracy
        accuracy = self._compute_predictive_accuracy()
        high_accuracy = accuracy > 0.8

        # Indicator 3: Meta-attention stability
        stable_cycles = len(self.meta_attention_log) >= 10
        meta_stable = False
        if stable_cycles:
            intensities = [m["intensity"] for m in self.meta_attention_log]
            if len(intensities) >= 10:
                recent_intensities = list(intensities)[-10:]
                variance = sum((x - sum(recent_intensities) / len(recent_intensities)) ** 2 for x in recent_intensities) / len(recent_intensities)
                meta_stable = variance < 0.1  # Low variance = stable

        # Compute emergence score
        score = 0.0
        if self_referential_tracking:
            score += 0.33
        if high_accuracy:
            score += 0.33
        if meta_stable:
            score += 0.34

        emerged = score >= 0.8

        return {
            "emerged": emerged,
            "emergence_score": round(score, 4),
            "indicators": {
                "self_referential_tracking": {
                    "active": self_referential_tracking,
                    "ratio": round(self_referential_ratio, 4),
                },
                "predictive_accuracy": {
                    "active": high_accuracy,
                    "value": round(accuracy, 4),
                },
                "meta_attention_stability": {
                    "active": meta_stable,
                    "cycles_tracked": len(self.meta_attention_log),
                },
            },
            "self_awareness_level": self._get_awareness_level(score),
        }

    def _compute_predictive_accuracy(self) -> float:
        """Compute predictive accuracy: correct_predictions / total_predictions."""
        total = self.schema_state["total_predictions"]
        if total == 0:
            return 0.0

        correct = 0
        for pred in self.predictions:
            # Check if the prediction matched actual subsequent attention
            pred_time = pred["timestamp"]
            # Find the next attention event after prediction
            for h in self.attention_history:
                if h["timestamp"] > pred_time:
                    if h["target"] == pred["predicted_target"]:
                        correct += 1
                    break

        self.schema_state["correct_predictions"] = correct
        return correct / total

    def _get_awareness_level(self, score: float) -> str:
        """Map score to self-awareness level."""
        for threshold, level in self.AWARENESS_LEVELS:
            if score >= threshold:
                return level
        return "unconscious"

    def get_status(self) -> Dict[str, Any]:
        """Return schema_completeness, prediction_accuracy, self_awareness_level."""
        # Schema completeness: based on how well-developed the self-model is
        completeness = 0.0
        if self.self_model["current_focus"] is not None:
            completeness += 0.25
        if self.self_model["attention_capacity"] > 0.0:
            completeness += 0.25
        if self.self_model["attention_shifts"] > 0:
            completeness += 0.25
        if self.self_model["attention_depth"] > 0.0:
            completeness += 0.25

        # Predictive accuracy
        accuracy = self._compute_predictive_accuracy()

        # Self-awareness level from emergence detection
        emergence = self.detect_attention_schema_emergence()
        awareness_level = emergence["self_awareness_level"]

        return {
            "schema_completeness": round(completeness, 4),
            "prediction_accuracy": round(accuracy, 4),
            "self_awareness_level": awareness_level,
            "total_tracks": self.schema_state["total_tracks"],
            "total_predictions": self.schema_state["total_predictions"],
            "correct_predictions": self.schema_state["correct_predictions"],
            "meta_attention_cycles": self.schema_state["meta_attention_cycles"],
            "emergence_score": emergence["emergence_score"],
        }


# Global singleton instance
_attention_schema_engine = None


def get_attention_schema_engine() -> AttentionSchemaEngine:
    """Get the global Attention Schema Engine instance."""
    global _attention_schema_engine
    if _attention_schema_engine is None:
        _attention_schema_engine = AttentionSchemaEngine()
    return _attention_schema_engine


def reset_attention_schema_engine():
    """Reset the global instance (for testing)."""
    global _attention_schema_engine
    _attention_schema_engine = AttentionSchemaEngine()


if __name__ == "__main__":
    print("[OMNI-HUB v169] Attention Schema Engine Demo")
    engine = AttentionSchemaEngine()

    # Simulate attention tracking
    targets = ["task_A", "task_B", "task_A", "self_reflection", "attention_monitoring", "task_A"]
    for i, target in enumerate(targets):
        engine.track_attention(target, intensity=0.5 + i * 0.05)

    print("\nSelf-model:", engine.build_self_model())
    print("\nQuality:", engine.evaluate_attention_quality())

    context = {
        "available_targets": ["task_A", "task_B", "task_C"],
        "salience_map": {"task_A": 0.8, "task_B": 0.5, "task_C": 0.3},
        "goals": ["complete task_A"],
    }
    print("\nPrediction:", engine.predict_attention_shift("task_B", context))
    print("\nEmergence:", engine.detect_attention_schema_emergence())
    print("\nStatus:", engine.get_status())
