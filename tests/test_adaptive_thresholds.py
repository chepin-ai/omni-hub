"""
OMNI-HUB Adaptive Thresholds Tests v23
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.adaptive_thresholds import AdaptiveThresholds, ParameterAdjustment
from core import constants as C


class TestAdaptiveThresholds:
    def test_track_metric(self):
        tuner = AdaptiveThresholds()
        tuner.track("energy_growth_rate", 1.01)
        assert "energy_growth_rate" in tuner.metrics_history
        assert len(tuner.metrics_history["energy_growth_rate"]) == 1

    def test_trend_computation(self):
        tuner = AdaptiveThresholds()
        for i in range(40):
            tuner.track("test", 1.0 + i * 0.01)
        trend = tuner._compute_trend(tuner.metrics_history["test"])
        assert trend > 0  # Improving

    def test_declining_trend_proposes_adjustment(self):
        tuner = AdaptiveThresholds()
        # Rapid decline
        for i in range(100):
            tuner.track("energy_growth_rate", 1.05 - i * 0.005)
        tuner.last_adjustment_cycle = -1000  # Bypass cooldown
        proposals = tuner.evaluate(cycle=100)
        assert len(proposals) > 0
        assert proposals[0]["param"] == "SELF_DRIVE_PHI_MIN"
        assert proposals[0]["direction"] == -1

    def test_improving_trend_proposes_opposite(self):
        tuner = AdaptiveThresholds()
        for i in range(100):
            tuner.track("energy_growth_rate", 1.0 + i * 0.02)  # Strong improvement
        tuner.last_adjustment_cycle = -1000
        proposals = tuner.evaluate(cycle=100)
        assert len(proposals) > 0
        assert proposals[0]["direction"] == 1

    def test_cooldown_blocks_evaluation(self):
        tuner = AdaptiveThresholds()
        for i in range(100):
            tuner.track("energy_growth_rate", 1.0 - i * 0.01)
        tuner.last_adjustment_cycle = 50
        proposals = tuner.evaluate(cycle=100)
        assert len(proposals) == 0  # Blocked by cooldown

    def test_apply_changes_parameter(self):
        tuner = AdaptiveThresholds()
        original = C.SELF_DRIVE_PHI_MIN
        proposal = {"param": "SELF_DRIVE_PHI_MIN", "direction": -1, "reason": "test"}
        success = tuner.apply(proposal, C)
        assert success
        assert C.SELF_DRIVE_PHI_MIN < original
        # Restore
        C.SELF_DRIVE_PHI_MIN = original

    def test_apply_respects_bounds(self):
        tuner = AdaptiveThresholds()
        C.SELF_DRIVE_PHI_MIN = 0.05  # At minimum
        proposal = {"param": "SELF_DRIVE_PHI_MIN", "direction": -1, "reason": "test"}
        success = tuner.apply(proposal, C)
        assert not success  # Cannot go below min
        C.SELF_DRIVE_PHI_MIN = 0.15  # Restore

    def test_phi_stagnation_proposal(self):
        tuner = AdaptiveThresholds()
        for i in range(100):
            tuner.track("phi_variance", 0.5 - i * 0.01)  # Declining variance
        tuner.last_adjustment_cycle = -1000
        proposals = tuner.evaluate(cycle=100)
        phi_proposals = [p for p in proposals if p["param"] == "SELF_DRIVE_PLATEAU_THRESHOLD"]
        assert len(phi_proposals) > 0
        assert phi_proposals[0]["direction"] == 1

    def test_slow_leveling_proposal(self):
        tuner = AdaptiveThresholds()
        for i in range(5):
            tuner.track("level_up_interval", 400)  # Very slow
        tuner.last_adjustment_cycle = -1000
        proposals = tuner.evaluate(cycle=100)
        level_proposals = [p for p in proposals if p["param"] == "SELF_DRIVE_CHECKPOINT_INTERVAL"]
        assert len(level_proposals) > 0
        assert level_proposals[0]["direction"] == -1

    def test_get_status(self):
        tuner = AdaptiveThresholds()
        status = tuner.get_status()
        assert "total_adjustments" in status
        assert "metrics_tracked" in status
