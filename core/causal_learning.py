"""
OMNI-HUB Causal Learning v88
Causal model building from observations.

Correlation is not causation — but causation leaves footprints.
This module builds causal models from observed state transitions,
learning which actions lead to which effects.

Philosophy: 种瓜得瓜，种豆得豆 —
Plant melons, harvest melons; plant beans, harvest beans.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class CausalLink:
    """A hypothesized causal link."""
    cause: str
    effect: str
    strength: float
    observations: int
    confidence: float


class CausalLearning:
    """
    Learns causal models from observations.
    """

    def __init__(self):
        self.links: List[CausalLink] = []
        self.observations: List[Dict[str, Any]] = []
        self.learning_count = 0

    def record_observation(self, before: Dict[str, Any], after: Dict[str, Any], action: str = ""):
        """Record a state transition observation."""
        self.observations.append({
            "before": before,
            "after": after,
            "action": action,
        })

    def infer_links(self) -> List[CausalLink]:
        """Infer causal links from observations."""
        if len(self.observations) < 3:
            return []

        # Check for co-occurrence patterns
        candidates: Dict[Tuple[str, str], List[float]] = {}

        for obs in self.observations:
            before = obs["before"]
            after = obs["after"]

            # Compare before and after for changes
            for key in set(before.keys()) | set(after.keys()):
                b_val = before.get(key)
                a_val = after.get(key)

                if isinstance(b_val, (int, float)) and isinstance(a_val, (int, float)):
                    if abs(a_val - b_val) > 0.01:  # significant change
                        effect_key = key

                        # Look for potential causes in before state
                        for cause_key in before:
                            c_val = before.get(cause_key)
                            if isinstance(c_val, (int, float)) and cause_key != effect_key:
                                pair = (cause_key, effect_key)
                                if pair not in candidates:
                                    candidates[pair] = []
                                candidates[pair].append(1.0 if a_val > b_val else -1.0)

        # Build links from consistent patterns
        links = []
        for (cause, effect), changes in candidates.items():
            if len(changes) >= 2:
                consistency = abs(sum(changes)) / len(changes)
                strength = min(1.0, len(changes) / 10.0)
                confidence = consistency * strength

                links.append(CausalLink(
                    cause=cause,
                    effect=effect,
                    strength=round(strength, 3),
                    observations=len(changes),
                    confidence=round(confidence, 3),
                ))

        self.links = sorted(links, key=lambda l: -l.confidence)[:20]
        return self.links

    def predict_effect(self, cause: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Predict effect given cause and state."""
        relevant = [l for l in self.links if l.cause == cause]

        if not relevant:
            return {"predicted_change": 0, "confidence": 0}

        top = relevant[0]
        return {
            "effect": top.effect,
            "predicted_direction": "increase" if top.strength > 0.5 else "decrease",
            "confidence": top.confidence,
        }

    def learn_from_history(self, history: List[Dict[str, Any]]):
        """Learn causal links from full history."""
        if len(history) < 2:
            return []

        for i in range(1, min(len(history), 50)):
            before = history[i-1].get('state', history[i-1])
            after = history[i].get('state', history[i])
            self.record_observation(before, after)

        self.learning_count += 1
        return self.infer_links()

    def get_status(self) -> Dict[str, Any]:
        return {
            "observations": len(self.observations),
            "links": len(self.links),
            "learning_ops": self.learning_count,
            "top_links": [
                {"cause": l.cause, "effect": l.effect, "confidence": l.confidence}
                for l in self.links[:5]
            ],
        }


_cl_engine = None

def get_causal_learning():
    global _cl_engine
    if _cl_engine is None:
        _cl_engine = CausalLearning()
    return _cl_engine
