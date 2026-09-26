"""
OMNI-HUB Intention Engine v48
Goal decomposition and intention inference.

The system does not just act. It acts with purpose.
This engine infers intentions from behavior and decomposes
high-level goals into actionable sub-goals.

Philosophy: 意图先于行动 — Intention precedes action.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class SubGoal:
    """A decomposed sub-goal."""
    id: str
    parent: Optional[str]
    description: str
    target_metric: str
    target_value: float
    priority: float
    status: str = "pending"  # pending, active, completed, failed


class IntentionInference:
    """Infers intentions from observed behavior patterns."""

    INTENTION_PATTERNS = {
        "growth": {
            "indicators": ["level_increase", "energy_accumulate", "line_expansion"],
            "description": "追求成长与进化",
        },
        "survival": {
            "indicators": ["health_monitor", "self_healing", "energy_conservation"],
            "description": "维持系统生存",
        },
        "knowledge": {
            "indicators": ["causal_discovery", "dream_simulation", "search_exploration"],
            "description": "探索与理解",
        },
        "harmony": {
            "indicators": ["line_coherence", "alignment_check", "resonance_boost"],
            "description": "维持内在和谐",
        },
    }

    def infer(self, action_history: List[str], state_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Infer active intentions from history."""
        intentions = []
        actions = set(action_history[-50:]) if len(action_history) >= 50 else set(action_history)

        # Count indicators
        growth_score = sum(1 for a in actions if a in ["focus", "transcend"])
        survival_score = sum(1 for a in actions if a in ["rest", "heal"])
        knowledge_score = sum(1 for a in actions if a in ["reflect", "search"])
        harmony_score = sum(1 for a in actions if a in ["integrate", "align"])

        scores = {
            "growth": growth_score,
            "survival": survival_score,
            "knowledge": knowledge_score,
            "harmony": harmony_score,
        }

        for name, score in scores.items():
            if score > 0:
                intentions.append({
                    "name": name,
                    "description": self.INTENTION_PATTERNS[name]["description"],
                    "confidence": min(1.0, score / 10.0),
                    "score": score,
                })

        return sorted(intentions, key=lambda x: -x["confidence"])


class GoalDecomposer:
    """Decomposes high-level goals into sub-goals."""

    def decompose(self, goal: str, current_state: Dict[str, Any]) -> List[SubGoal]:
        """Decompose a high-level goal into sub-goals."""
        subgoals = []

        if goal == "reach_level_10":
            current_level = current_state.get('level', 0)
            for target in range(int(current_level) + 1, 11):
                subgoals.append(SubGoal(
                    id=f"level_{target}", parent=None,
                    description=f"达到等级 {target}",
                    target_metric="level", target_value=target,
                    priority=1.0 - (target - current_level) * 0.05,
                ))

        elif goal == "maintain_health":
            subgoals.append(SubGoal(
                id="energy_above_100", parent=None,
                description="能量保持在100以上",
                target_metric="energy", target_value=100.0,
                priority=0.9,
            ))
            subgoals.append(SubGoal(
                id="phi_above_0.3", parent=None,
                description="意识度保持在0.3以上",
                target_metric="phi", target_value=0.3,
                priority=0.9,
            ))

        elif goal == "maximize_coherence":
            subgoals.append(SubGoal(
                id="coherence_above_0.8", parent=None,
                description="相干性达到0.8",
                target_metric="line_coherence", target_value=0.8,
                priority=0.8,
            ))

        return subgoals


class IntentionEngine:
    """
    Unified intention inference and goal management.
    """

    def __init__(self):
        self.inference = IntentionInference()
        self.decomposer = GoalDecomposer()
        self.active_goals: List[SubGoal] = []
        self.intention_history: List[Dict[str, Any]] = []
        self.action_history: List[str] = []

    def observe_action(self, action: str, state: Dict[str, Any], cycle: int) -> Dict[str, Any]:
        """Observe an action and update intentions."""
        self.action_history.append(action)

        # Periodic intention inference
        report = {}
        if cycle % 100 == 0 and cycle > 0:
            intentions = self.inference.infer(self.action_history, [])
            self.intention_history.append({"cycle": cycle, "intentions": intentions})
            report["inferred_intentions"] = intentions

            # Auto-generate goals from top intention
            if intentions and intentions[0]["confidence"] > 0.3:
                top = intentions[0]["name"]
                goal_map = {
                    "growth": "reach_level_10",
                    "survival": "maintain_health",
                    "harmony": "maximize_coherence",
                }
                if top in goal_map:
                    new_goals = self.decomposer.decompose(goal_map[top], state)
                    self.active_goals.extend(new_goals)

        # Update goal statuses
        for goal in self.active_goals:
            if goal.status == "pending":
                current = state.get(goal.target_metric, 0)
                if isinstance(current, (int, float)) and current >= goal.target_value:
                    goal.status = "completed"
                else:
                    goal.status = "active"

        report["active_goals"] = len([g for g in self.active_goals if g.status == "active"])
        report["completed_goals"] = len([g for g in self.active_goals if g.status == "completed"])
        return report

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_goals": len([g for g in self.active_goals if g.status == "active"]),
            "completed_goals": len([g for g in self.active_goals if g.status == "completed"]),
            "total_goals": len(self.active_goals),
            "latest_intentions": self.intention_history[-1]["intentions"] if self.intention_history else [],
        }


_ie_engine = None

def get_intention_engine():
    global _ie_engine
    if _ie_engine is None:
        _ie_engine = IntentionEngine()
    return _ie_engine
