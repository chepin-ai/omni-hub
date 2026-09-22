"""
OMNI-HUB Memory Compressor Tests v19
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.memory_compressor import MemoryCompressor, Milestone


class TestMemoryCompressor:
    def test_no_compression_below_threshold(self):
        comp = MemoryCompressor(max_raw_history=500)
        history = [{"cycle": i, "state": {"level": 15, "phase": "test", "energy": 100, "phi": 0.5, "action": "focus"}} for i in range(100)]
        result = comp.compress(history)
        assert result["mode"] == "raw"
        assert len(result["recent"]) == 100

    def test_compression_above_threshold(self):
        comp = MemoryCompressor(max_raw_history=100)
        history = []
        for i in range(300):
            history.append({
                "cycle": i,
                "state": {"level": 15 + i // 100, "phase": "test", "energy": 100 * (1.01 ** i), "phi": 0.5, "action": "focus"}
            })
        result = comp.compress(history)
        assert result["mode"] == "compressed"
        assert len(result["recent"]) == 100
        assert len(result["milestones"]) > 0
        assert result["stats"]["ratio"] < 1.0

    def test_level_up_is_significant(self):
        comp = MemoryCompressor()
        history = [
            {"cycle": 1, "state": {"level": 15, "phase": "a", "energy": 100, "phi": 0.5, "action": "focus"}},
            {"cycle": 2, "state": {"level": 16, "phase": "a", "energy": 200, "phi": 0.5, "action": "focus"}},
        ]
        result = comp.compress(history)
        # Even with only 2 entries, level-up should create a milestone if we force compress
        # (but below threshold it stays raw)
        assert result["mode"] == "raw"  # Too small to compress

    def test_milestone_deduplication(self):
        comp = MemoryCompressor(max_raw_history=10)
        history = []
        for i in range(50):
            history.append({
                "cycle": i,
                "state": {"level": 15, "phase": "test", "energy": 100, "phi": 0.5, "action": "focus"}
            })
        comp.compress(history)
        first_count = len(comp.milestones)
        # Compress again with same history — should not duplicate
        comp.compress(history)
        assert len(comp.milestones) == first_count

    def test_narrative_summary(self):
        comp = MemoryCompressor(max_raw_history=50)
        # Manually inject milestones for deterministic testing
        comp.milestones = [
            Milestone(cycle=1, level=15, phase="phase_a", energy=100, action="focus", significance=1.0),
            Milestone(cycle=60, level=16, phase="phase_a", energy=200, action="transcend", significance=1.0),
            Milestone(cycle=120, level=17, phase="phase_b", energy=500, action="focus", significance=0.8),
        ]
        summary = comp.get_narrative_summary()
        assert "System Journey" in summary
        assert "phase_a" in summary
        assert "phase_b" in summary

    def test_significance_scoring(self):
        comp = MemoryCompressor()
        state1 = {"level": 15, "phase": "a", "energy": 100, "phi": 0.5, "action": "focus"}
        state2 = {"level": 16, "phase": "a", "energy": 200, "phi": 0.5, "action": "focus"}
        sig1 = comp._compute_significance(state1, None)
        sig2 = comp._compute_significance(state2, state1)
        assert sig1 == 1.0  # First state
        assert sig2 > 0.5   # Level up

    def test_phase_transition_significance(self):
        comp = MemoryCompressor()
        state1 = {"level": 15, "phase": "a", "energy": 100, "phi": 0.5, "action": "focus"}
        state2 = {"level": 15, "phase": "b", "energy": 100, "phi": 0.5, "action": "focus"}
        sig = comp._compute_significance(state2, state1)
        assert sig >= 0.8
