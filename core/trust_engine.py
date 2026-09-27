"""
OMNI-HUB Trust Engine v80
Reputation, trust scoring, betrayal detection.

Trust is earned in drops and lost in buckets.
This module maintains trust scores for entities —
systems, agents, data sources — detecting shifts
in reliability and flagging potential betrayal.

Philosophy: 信言不美，美言不信 —
Trustworthy words are not beautiful; beautiful words are not trustworthy.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class TrustRecord:
    """Trust record for an entity."""
    entity: str
    score: float  # 0-1
    interactions: int
    positive: int
    negative: int
    last_updated: int


class TrustEngine:
    """
    Maintains trust scores and detects reliability shifts.
    """

    def __init__(self):
        self.records: Dict[str, TrustRecord] = {}
        self.betrayals: List[Dict[str, Any]] = []
        self.global_trust = 0.5

    def register_entity(self, entity: str, initial_score: float = 0.5):
        """Register a new entity."""
        if entity not in self.records:
            self.records[entity] = TrustRecord(
                entity=entity,
                score=initial_score,
                interactions=0,
                positive=0,
                negative=0,
                last_updated=0,
            )

    def record_interaction(self, entity: str, positive: bool, cycle: int):
        """Record an interaction outcome."""
        if entity not in self.records:
            self.register_entity(entity)

        record = self.records[entity]
        record.interactions += 1

        if positive:
            record.positive += 1
            record.score = min(1.0, record.score + 0.05)
        else:
            record.negative += 1
            record.score = max(0.0, record.score - 0.1)

        record.last_updated = cycle

        # Detect betrayal: sudden drop in trust
        if record.interactions >= 5 and record.score < 0.3:
            self.betrayals.append({
                "entity": entity,
                "score": record.score,
                "cycle": cycle,
                "reason": "trust_dropped_below_threshold",
            })

    def evaluate_system_trust(self, state: Dict[str, Any], cycle: int):
        """Evaluate trust in system components."""
        # Register/check key system components
        components = [
            "self_awareness", "learning", "reasoning", "planning",
            "ethics", "communication", "memory", "perception",
        ]

        assessment = state.get('capability_assessment', {})
        scores = assessment.get('scores', {})

        for comp in components:
            self.register_entity(comp)
            score = scores.get(comp, 0.5)
            if isinstance(score, (int, float)):
                # Treat high capability as positive interaction
                if score > 0.6:
                    self.record_interaction(comp, positive=True, cycle=cycle)
                elif score < 0.3:
                    self.record_interaction(comp, positive=False, cycle=cycle)

        # Calculate global trust
        if self.records:
            self.global_trust = sum(r.score for r in self.records.values()) / len(self.records)

        return self.records

    def get_trusted_entities(self, threshold: float = 0.7) -> List[str]:
        """Get entities above trust threshold."""
        return [e for e, r in self.records.items() if r.score >= threshold]

    def get_untrusted_entities(self, threshold: float = 0.3) -> List[str]:
        """Get entities below trust threshold."""
        return [e for e, r in self.records.items() if r.score <= threshold]

    def get_status(self) -> Dict[str, Any]:
        return {
            "entities": len(self.records),
            "global_trust": round(self.global_trust, 3),
            "trusted": len(self.get_trusted_entities()),
            "untrusted": len(self.get_untrusted_entities()),
            "betrayals": len(self.betrayals),
            "records": [
                {"entity": r.entity, "score": round(r.score, 3), "interactions": r.interactions}
                for r in sorted(self.records.values(), key=lambda x: -x.score)[:5]
            ],
        }


_te_engine = None

def get_trust_engine():
    global _te_engine
    if _te_engine is None:
        _te_engine = TrustEngine()
    return _te_engine
