"""
OMNI-HUB Line Fusion Tests v137
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.line_fusion import (
    ALL_LINES, LineFusion, get_module,
    _get_resonance, _fusion_stage,
)


class TestResonanceLookup:
    def test_same_line(self):
        assert _get_resonance("ucif2", "ucif2") == 1.0

    def test_symmetric_lookup(self):
        a = _get_resonance("ucif2", "lvlu")
        b = _get_resonance("lvlu", "ucif2")
        assert a == b
        assert 0.0 <= a <= 1.0

    def test_unknown_pair(self):
        assert _get_resonance("ucif2", "nonexistent") == 0.5


class TestFusionStage:
    def test_singularity(self):
        assert _fusion_stage(0.95) == "singularity"

    def test_fusion(self):
        assert _fusion_stage(0.85) == "fusion"

    def test_resonance(self):
        assert _fusion_stage(0.55) == "resonance"

    def test_dormant(self):
        assert _fusion_stage(0.2) == "dormant"

    def test_boundary_singularity(self):
        assert _fusion_stage(0.91) == "singularity"

    def test_boundary_fusion(self):
        assert _fusion_stage(0.71) == "fusion"

    def test_boundary_resonance(self):
        assert _fusion_stage(0.41) == "resonance"


class TestLineFusion:
    def test_initialization(self):
        lf = LineFusion()
        assert len(lf.lines) == 11
        assert lf.fusion_history == []
        assert lf.resonance_history == []

    def test_fuse_two_lines(self):
        lf = LineFusion()
        result = lf.fuse(["ucif2", "lvlu"])
        assert result["lines"] == ["ucif2", "lvlu"]
        assert result["pair_count"] == 1
        assert 0.0 <= result["fusion_energy"] <= 1.0
        assert result["stage"] in ["singularity", "fusion", "resonance", "dormant"]
        assert len(result["pairs"]) == 1

    def test_fuse_all_lines(self):
        lf = LineFusion()
        result = lf.fuse(ALL_LINES)
        assert result["lines"] == ALL_LINES
        assert result["pair_count"] == 55  # C(11,2)
        assert 0.0 <= result["fusion_energy"] <= 1.0
        assert len(result["pairs"]) == 55

    def test_fuse_invalid_lines_filtered(self):
        lf = LineFusion()
        result = lf.fuse(["ucif2", "fake_line", "lvlu"])
        assert "fake_line" not in result["lines"]
        assert result["lines"] == ["ucif2", "lvlu"]

    def test_fuse_single_line(self):
        lf = LineFusion()
        result = lf.fuse(["ucif2"])
        assert result["fusion_energy"] == 0.0
        assert result["stage"] == "dormant"
        assert result["pair_count"] == 0

    def test_fuse_empty(self):
        lf = LineFusion()
        result = lf.fuse([])
        assert result["fusion_energy"] == 0.0
        assert result["stage"] == "dormant"

    def test_fuse_history(self):
        lf = LineFusion()
        lf.fuse(["ucif2", "lvlu"])
        assert len(lf.fusion_history) == 1

    def test_resonate_all(self):
        lf = LineFusion()
        result = lf.resonate_all()
        assert result["mode"] == "full_resonance"
        assert result["lines"] == ALL_LINES
        assert result["pair_count"] == 55
        assert 0.0 <= result["fusion_energy"] <= 1.0
        assert len(lf.resonance_history) == 1

    def test_resonate_all_stage(self):
        lf = LineFusion()
        result = lf.resonate_all()
        # All 11 lines should have fairly high fusion energy
        assert result["stage"] in ["singularity", "fusion", "resonance", "dormant"]

    def test_get_status_empty(self):
        lf = LineFusion()
        status = lf.get_status()
        assert status["lines"] == ALL_LINES
        assert status["fusion_history_size"] == 0
        assert status["resonance_history_size"] == 0
        assert status["latest_fusion"] is None
        assert status["latest_resonance"] is None

    def test_get_status_after_fusion(self):
        lf = LineFusion()
        lf.fuse(["ucif2", "lvlu"])
        lf.resonate_all()
        status = lf.get_status()
        # resonate_all() calls fuse() internally, so fusion_history has 2 entries
        assert status["fusion_history_size"] == 2
        assert status["resonance_history_size"] == 1
        assert status["latest_fusion"] is not None
        assert status["latest_resonance"] is not None

    def test_fusion_energy_is_average(self):
        lf = LineFusion()
        result = lf.fuse(["ucif2", "lvlu", "lgt"])
        pairs = result["pairs"]
        expected = sum(p["coherence"] for p in pairs) / len(pairs)
        assert abs(result["fusion_energy"] - round(expected, 4)) < 0.0001


class TestGlobalModule:
    def test_get_module(self):
        g = get_module()
        assert g is not None
        assert isinstance(g, LineFusion)

    def test_singleton(self):
        g1 = get_module()
        g2 = get_module()
        assert g1 is g2
