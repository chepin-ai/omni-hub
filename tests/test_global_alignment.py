"""
OMNI-HUB Global Alignment Tests v35
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.global_alignment import (
    AlignmentCheck, ModuleHealth, CrossModuleVerifier,
    LineModuleAligner, GlobalAlignmentEngine, get_alignment_engine,
)


class TestAlignmentCheck:
    def test_creation(self):
        ac = AlignmentCheck("test", "a", "b", True, 1.0, "ok")
        assert ac.aligned is True
        assert ac.score == 1.0


class TestCrossModuleVerifier:
    def test_verify_all(self):
        v = CrossModuleVerifier()
        results = v.verify_all()
        assert len(results) > 0
        # Most should be aligned
        aligned = sum(1 for r in results if r.aligned)
        assert aligned >= len(results) * 0.8

    def test_verify_pair_exists(self):
        v = CrossModuleVerifier()
        from pathlib import Path
        r = v._verify_pair(Path('/mnt/agents/output/OMNI-HUB'), "orchestrator", "event_bus")
        assert r.aligned is True

    def test_verify_pair_missing(self):
        v = CrossModuleVerifier()
        from pathlib import Path
        r = v._verify_pair(Path('/mnt/agents/output/OMNI-HUB'), "nonexistent_xyz", "also_missing")
        assert r.aligned is False


class TestLineModuleAligner:
    def test_check_alignment(self):
        la = LineModuleAligner()
        result = la.check_line_module_alignment()
        assert "all_aligned" in result
        assert "lines" in result
        assert "aligned_count" in result
        # Most lines should be aligned
        assert result["aligned_count"] >= 9

    def test_all_lines_present(self):
        la = LineModuleAligner()
        result = la.check_line_module_alignment()
        assert len(result["lines"]) == 11
        for line in ["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl", "qlv", "cisvr", "qtlv", "usrm", "cfts"]:
            assert line in result["lines"]


class TestGlobalAlignmentEngine:
    def test_initialization(self):
        engine = GlobalAlignmentEngine()
        assert len(engine.alignment_history) == 0

    def test_run_alignment(self):
        engine = GlobalAlignmentEngine()
        result = engine.run_alignment_check()
        assert "status" in result
        assert "overall_score" in result
        assert "cross_module" in result
        assert "line_module" in result
        assert result["overall_score"] > 0.5

    def test_status_aligned(self):
        engine = GlobalAlignmentEngine()
        result = engine.run_alignment_check()
        # Should be aligned since all modules exist
        assert result["status"] in ("aligned", "partial")

    def test_cross_module_high_score(self):
        engine = GlobalAlignmentEngine()
        result = engine.run_alignment_check()
        assert result["cross_module"]["score"] >= 0.8

    def test_line_module_all_aligned(self):
        engine = GlobalAlignmentEngine()
        result = engine.run_alignment_check()
        assert result["line_module"]["aligned_count"] == 11

    def test_history_tracking(self):
        engine = GlobalAlignmentEngine()
        engine.run_alignment_check()
        assert len(engine.alignment_history) == 1

    def test_get_status(self):
        engine = GlobalAlignmentEngine()
        status = engine.get_status()
        assert "history_size" in status


class TestGlobalEngine:
    def test_get_alignment_engine(self):
        g = get_alignment_engine()
        assert g is not None
        assert isinstance(g, GlobalAlignmentEngine)
