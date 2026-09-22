"""
OMNI-HUB Attention Mechanism Tests v21
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.attention import AttentionMechanism


class TestAttentionWeights:
    def test_phi_low_boosts_reflect(self):
        attn = AttentionMechanism()
        state = {"phi": 0.1, "phase": "test", "goal_planning": {}}
        weights = attn.compute_weights(state, ["reflect", "focus"])
        assert weights["reflect"] > weights["focus"]

    def test_phi_high_boosts_focus(self):
        attn = AttentionMechanism()
        state = {"phi": 0.9, "phase": "test", "goal_planning": {}}
        weights = attn.compute_weights(state, ["reflect", "focus"])
        assert weights["focus"] > weights["reflect"]

    def test_goal_alignment_boost(self):
        attn = AttentionMechanism()
        state = {"phi": 0.5, "phase": "test", "goal_planning": {"next_goal": "Reach Level 20"}}
        weights = attn.compute_weights(state, ["focus", "rest"])
        assert weights["focus"] > weights["rest"]

    def test_phase_preference(self):
        attn = AttentionMechanism()
        state = {"phi": 0.5, "phase": "trans_singularity", "goal_planning": {}}
        weights = attn.compute_weights(state, ["self_modify", "rest"])
        assert weights["self_modify"] > weights["rest"]

    def test_select_action_returns_valid(self):
        attn = AttentionMechanism()
        state = {"phi": 0.5, "phase": "test", "goal_planning": {}}
        actions = ["focus", "rest", "transcend"]
        action = attn.select_action(state, actions)
        assert action in actions

    def test_record_outcome(self):
        attn = AttentionMechanism()
        attn.record_outcome("focus", 100, 102)
        assert len(attn.action_history["focus"]) == 1
        assert attn.action_history["focus"][0] == 1.02

    def test_performance_attention(self):
        attn = AttentionMechanism()
        # Record good performance for focus
        for _ in range(5):
            attn.record_outcome("focus", 100, 110)
        # Record bad performance for rest
        for _ in range(5):
            attn.record_outcome("rest", 100, 95)
        state = {"phi": 0.5, "phase": "test", "goal_planning": {}}
        weights = attn.compute_weights(state, ["focus", "rest"])
        assert weights["focus"] > weights["rest"]

    def test_attention_report(self):
        attn = AttentionMechanism()
        attn.record_outcome("focus", 100, 102)
        report = attn.get_attention_report()
        assert "action_history_lengths" in report
        assert "average_performance" in report
        assert report["action_history_lengths"]["focus"] == 1
