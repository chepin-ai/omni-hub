"""
OMNI-HUB Meta-Learning v79
Learning how to learn, strategy optimization.

The highest form of learning is learning about learning.
This module optimizes learning strategies —
which methods work, when to use them, how to improve.

Philosophy: 授人以鱼不如授人以渔 —
Give a person a fish and you feed them for a day;
teach a person to fish and you feed them for a lifetime.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Strategy:
    """A learning strategy."""
    name: str
    effectiveness: float  # 0-1
    contexts: List[str]
    usage_count: int


class MetaLearning:
    """
    Learns which learning strategies work best.
    """

    def __init__(self):
        self.strategies: List[Strategy] = []
        self.strategy_history: List[Dict[str, Any]] = []
        self.adaptation_count = 0
        self._init_strategies()

    def _init_strategies(self):
        """Initialize default strategies."""
        self.strategies = [
            Strategy("focus_intense", 0.7, ["high_energy", "clear_goal"], 0),
            Strategy("explore_broad", 0.6, ["low_phi", "uncertain"], 0),
            Strategy("rest_recover", 0.8, ["low_energy", "diverging"], 0),
            Strategy("integrate_connect", 0.75, ["fragmented", "many_modules"], 0),
            Strategy("transcend_jump", 0.5, ["near_critical", "high_phi"], 0),
            Strategy("reflect_deep", 0.65, ["post_critical", "stable"], 0),
        ]

    def evaluate_strategy(self, strategy_name: str, outcome: float, context: str):
        """Evaluate a strategy's effectiveness."""
        strategy = next((s for s in self.strategies if s.name == strategy_name), None)
        if not strategy:
            return

        # Update effectiveness with moving average
        strategy.effectiveness = (strategy.effectiveness * strategy.usage_count + outcome) / (strategy.usage_count + 1)
        strategy.usage_count += 1

        if context not in strategy.contexts:
            strategy.contexts.append(context)

        self.strategy_history.append({
            "strategy": strategy_name,
            "outcome": outcome,
            "context": context,
            "updated_effectiveness": round(strategy.effectiveness, 3),
        })

    def recommend_strategy(self, context: str) -> str:
        """Recommend best strategy for context."""
        # Find strategies matching context
        matching = [s for s in self.strategies if context in s.contexts]

        if not matching:
            matching = self.strategies

        # Sort by effectiveness
        best = max(matching, key=lambda s: s.effectiveness)
        return best.name

    def adapt_strategies(self, state: Dict[str, Any]):
        """Adapt strategies based on recent outcomes."""
        learning = state.get('learning_core', {})
        last_reward = state.get('last_reward', 0)
        action = state.get('last_self_drive_action', 'focus')
        phase = state.get('phase', '')
        energy = state.get('energy', 1000.0)

        # Map action to strategy
        strategy_map = {
            "focus": "focus_intense",
            "explore": "explore_broad",
            "rest": "rest_recover",
            "integrate": "integrate_connect",
            "transcend": "transcend_jump",
            "reflect": "reflect_deep",
        }

        strategy_name = strategy_map.get(action, "focus_intense")

        # Determine context
        context = "general"
        if isinstance(energy, (int, float)) and energy < 200:
            context = "low_energy"
        elif phase == "near_critical":
            context = "near_critical"
        elif phase == "post_critical":
            context = "post_critical"
        elif isinstance(energy, (int, float)) and energy > 2000:
            context = "high_energy"

        # Normalize reward to 0-1 for effectiveness
        outcome = max(0.0, min(1.0, (last_reward + 5) / 15))

        self.evaluate_strategy(strategy_name, outcome, context)
        self.adaptation_count += 1

        return {
            "strategy": strategy_name,
            "context": context,
            "outcome": round(outcome, 3),
            "recommended": self.recommend_strategy(context),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "strategies": len(self.strategies),
            "adaptations": self.adaptation_count,
            "best_strategy": max(self.strategies, key=lambda s: s.effectiveness).name,
            "strategy_scores": [
                {"name": s.name, "effectiveness": round(s.effectiveness, 3), "used": s.usage_count}
                for s in sorted(self.strategies, key=lambda s: -s.effectiveness)
            ],
        }


_ml_engine = None

def get_meta_learning():
    global _ml_engine
    if _ml_engine is None:
        _ml_engine = MetaLearning()
    return _ml_engine
