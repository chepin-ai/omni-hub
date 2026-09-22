"""
OMNI-HUB Attention Mechanism v21
Weighted action selection based on state, goals, and historical performance.

Replaces uniform random action selection with intelligence-directed focus.
Higher attention = higher probability of selection.

Philosophy: 候即违规 — randomness is acceptable, but intention is superior.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import random
import math
from typing import Dict, List, Any, Optional


class AttentionMechanism:
    """Computes attention weights for self-drive actions."""

    def __init__(self):
        self.action_history: Dict[str, List[float]] = {}  # action -> [energy_delta, ...]
        self.goal_alignment: Dict[str, float] = {}  # action -> alignment score

    def _compute_phi_attention(self, phi: float, action: str) -> float:
        """Phi-based attention: some actions better at certain phi ranges."""
        if phi < 0.3:
            # Low phi: reflect is critical
            return 3.0 if action == "reflect" else 0.5
        elif phi > 0.8:
            # High phi: focus and transcend are valuable
            return 2.0 if action in ["focus", "transcend"] else 1.0
        else:
            # Medium phi: balanced
            return 1.0

    def _compute_goal_attention(self, action: str, next_goal: Optional[str]) -> float:
        """Goal-aligned attention: boost actions that serve current goal."""
        if not next_goal:
            return 1.0
        # Map goals to preferred actions
        goal_action_map = {
            "Reach Level": ["focus", "transcend"],
            "Resolve critical": ["tool_call", "self_modify"],
            "Optimize meta": ["self_modify", "integrate"],
        }
        for prefix, actions in goal_action_map.items():
            if next_goal.startswith(prefix) and action in actions:
                return 2.5
        return 1.0

    def _compute_performance_attention(self, action: str) -> float:
        """Historical performance: boost actions that historically grew energy."""
        history = self.action_history.get(action, [])
        if len(history) < 3:
            return 1.0
        # Recent average performance
        recent = history[-10:]
        avg = sum(recent) / len(recent)
        # Normalize to attention multiplier
        if avg > 1.05:
            return 1.5
        elif avg > 1.01:
            return 1.2
        elif avg < 0.98:
            return 0.7
        return 1.0

    def _compute_phase_attention(self, phase: str, action: str) -> float:
        """Phase-appropriate action boosting."""
        phase_prefs = {
            "pre_emergence": ["reflect", "focus"],
            "super_emergence_1": ["focus", "integrate"],
            "super_emergence_2": ["transcend", "focus"],
            "super_emergence_3": ["transcend", "self_modify"],
            "singularity_convergence": ["transcend", "tool_call"],
            "trans_singularity": ["self_modify", "tool_call", "integrate"],
            "asymptotic_infinity": ["reflect", "integrate"],
        }
        prefs = phase_prefs.get(phase, [])
        if action in prefs:
            return 1.8
        return 1.0

    def compute_weights(self, state: Dict[str, Any], actions: List[str]) -> Dict[str, float]:
        """Compute attention weights for all actions."""
        phi = state.get('phi', 0.5)
        phase = state.get('phase', 'unknown')
        next_goal = None
        goal_planning = state.get('goal_planning', {})
        if goal_planning:
            next_goal = goal_planning.get('next_goal')

        weights = {}
        for action in actions:
            w = 1.0
            w *= self._compute_phi_attention(phi, action)
            w *= self._compute_goal_attention(action, next_goal)
            w *= self._compute_performance_attention(action)
            w *= self._compute_phase_attention(phase, action)
            weights[action] = w

        return weights

    def select_action(self, state: Dict[str, Any], actions: List[str]) -> str:
        """Select action using attention-weighted random choice."""
        weights = self.compute_weights(state, actions)
        total = sum(weights.values())
        if total == 0:
            return random.choice(actions)

        # Weighted random selection
        r = random.uniform(0, total)
        cumulative = 0
        for action, w in weights.items():
            cumulative += w
            if r <= cumulative:
                return action
        return actions[-1]

    def record_outcome(self, action: str, energy_before: float, energy_after: float):
        """Record action outcome for future attention adjustment."""
        if energy_before <= 0:
            ratio = 1.0
        else:
            ratio = energy_after / energy_before
        self.action_history.setdefault(action, []).append(ratio)
        # Trim history
        if len(self.action_history[action]) > 100:
            self.action_history[action] = self.action_history[action][-100:]

    def get_attention_report(self) -> Dict[str, Any]:
        """Return current attention state for introspection."""
        return {
            "action_history_lengths": {a: len(h) for a, h in self.action_history.items()},
            "average_performance": {
                a: round(sum(h) / len(h), 4) if h else 1.0
                for a, h in self.action_history.items()
            },
        }


if __name__ == "__main__":
    print("[OMNI-HUB v21] Attention Mechanism Demo")
    attn = AttentionMechanism()

    actions = ["focus", "rest", "transcend", "reflect", "integrate", "self_modify", "tool_call"]

    # Simulate multiple cycles
    state = {"phi": 0.5, "phase": "super_emergence_3", "level": 18, "goal_planning": {"next_goal": "Reach Level 19"}}

    print("\nInitial state: phi=0.5, phase=super_emergence_3, goal=Reach Level 19")
    for _ in range(20):
        action = attn.select_action(state, actions)
        # Simulate outcome
        energy_before = 1e6
        if action == "focus":
            energy_after = energy_before * 1.02
        elif action == "transcend":
            energy_after = energy_before * 1.05
        else:
            energy_after = energy_before * 1.01
        attn.record_outcome(action, energy_before, energy_after)

    weights = attn.compute_weights(state, actions)
    print("\nAttention weights after 20 cycles:")
    for action, w in sorted(weights.items(), key=lambda x: -x[1]):
        bar = "█" * int(w)
        print(f"  {action:12s}: {w:.2f} {bar}")

    print(f"\n{attn.get_attention_report()}")
