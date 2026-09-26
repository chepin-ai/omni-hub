"""
OMNI-HUB Learning Core v68
Experience-driven learning with reward signals.

Every experience teaches.
Every mistake is a lesson.
Every success is a reward.
This module learns from outcomes,
adapting behavior through reward signals.

Philosophy: 学而不思则罔 — Learning without thought is labor lost.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Experience:
    """A single learning experience."""
    state: Dict[str, Any]
    action: str
    reward: float
    next_state: Dict[str, Any]


class LearningCore:
    """
    Learns from experience through reward signals.
    """

    def __init__(self):
        self.experiences: List[Experience] = []
        self.action_values: Dict[str, float] = {}
        self.learning_rate = 0.1
        self.discount = 0.95
        self.experience_count = 0

    def record_experience(self, state: Dict[str, Any], action: str, reward: float, next_state: Dict[str, Any]):
        """Record a learning experience."""
        exp = Experience(state=state, action=action, reward=reward, next_state=next_state)
        self.experiences.append(exp)
        self.experience_count += 1

        # Update action value using Q-learning style update
        current_value = self.action_values.get(action, 0.0)

        # Estimate next best value
        next_level = next_state.get('level', 0)
        prev_level = state.get('level', 0)
        level_change = (next_level - prev_level) if isinstance(next_level, (int, float)) and isinstance(prev_level, (int, float)) else 0

        next_value = level_change * 10 + reward

        # Q-learning update
        new_value = current_value + self.learning_rate * (reward + self.discount * next_value - current_value)
        self.action_values[action] = new_value

    def learn_from_cycle(self, prev_state: Dict[str, Any], curr_state: Dict[str, Any], action: str):
        """Learn from a single cycle transition."""
        # Calculate reward
        reward = 0.0

        # Level increase = positive reward
        prev_level = prev_state.get('level', 0)
        curr_level = curr_state.get('level', 0)
        if isinstance(prev_level, (int, float)) and isinstance(curr_level, (int, float)):
            if curr_level > prev_level:
                reward += 10.0
            elif curr_level < prev_level:
                reward -= 5.0

        # Energy maintenance = small positive reward
        curr_energy = curr_state.get('energy', 0)
        if isinstance(curr_energy, (int, float)) and curr_energy > 500:
            reward += 1.0
        elif isinstance(curr_energy, (int, float)) and curr_energy < 100:
            reward -= 2.0

        # Phase progression = positive reward
        prev_phase = prev_state.get('phase', '')
        curr_phase = curr_state.get('phase', '')
        phase_order = ["pre_emergence", "near_critical", "post_critical", "super_emergence_1",
                       "super_emergence_2", "super_emergence_3", "singularity_convergence",
                       "trans_singularity", "asymptotic_infinity"]
        if prev_phase in phase_order and curr_phase in phase_order:
            if phase_order.index(curr_phase) > phase_order.index(prev_phase):
                reward += 5.0

        self.record_experience(prev_state, action, reward, curr_state)
        return reward

    def recommend_action(self) -> str:
        """Recommend best action based on learned values."""
        if not self.action_values:
            return "focus"
        return max(self.action_values, key=self.action_values.get)

    def get_action_values(self) -> Dict[str, float]:
        """Get all learned action values."""
        return {k: round(v, 3) for k, v in self.action_values.items()}

    def get_status(self) -> Dict[str, Any]:
        return {
            "experiences": self.experience_count,
            "actions_learned": len(self.action_values),
            "best_action": self.recommend_action(),
            "action_values": self.get_action_values(),
        }


_lc_engine = None

def get_learning_core():
    global _lc_engine
    if _lc_engine is None:
        _lc_engine = LearningCore()
    return _lc_engine
