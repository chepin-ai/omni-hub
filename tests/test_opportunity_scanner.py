"""
OMNI-HUB Opportunity Scanner Tests v76
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.opportunity_scanner import (
    Opportunity, OpportunityScanner, get_opportunity_scanner,
)


class TestOpportunityScanner:
    def test_initialization(self):
        os = OpportunityScanner()
        assert os.scan_count == 0

    def test_scan_near_critical(self):
        os = OpportunityScanner()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0, "phase": "near_critical", "active_lines": 11}
        opps = os.scan(state)
        assert len(opps) > 0
        names = [o.name for o in opps]
        assert "phase_breakthrough" in names

    def test_scan_high_energy(self):
        os = OpportunityScanner()
        state = {"level": 3, "phi": 0.6, "energy": 3000.0, "phase": "pre_emergence", "active_lines": 11}
        opps = os.scan(state)
        names = [o.name for o in opps]
        assert "growth_window" in names

    def test_scan_incomplete_lines(self):
        os = OpportunityScanner()
        state = {"level": 3, "phi": 0.6, "energy": 1000.0, "phase": "pre_emergence", "active_lines": 8}
        opps = os.scan(state)
        names = [o.name for o in opps]
        assert "line_activation" in names

    def test_rank_opportunities(self):
        os = OpportunityScanner()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0, "phase": "near_critical", "active_lines": 11}
        os.scan(state)
        ranked = os.rank_opportunities()
        assert len(ranked) > 0
        # Highest ROI first
        if len(ranked) > 1:
            roi_first = ranked[0].potential / max(0.01, ranked[0].effort)
            roi_second = ranked[1].potential / max(0.01, ranked[1].effort)
            assert roi_first >= roi_second

    def test_get_best_opportunity(self):
        os = OpportunityScanner()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0, "phase": "near_critical", "active_lines": 11}
        os.scan(state)
        best = os.get_best_opportunity()
        assert best is not None
        assert best.potential > 0

    def test_get_status(self):
        os = OpportunityScanner()
        os.scan({"level": 5, "phi": 0.6, "energy": 1000.0, "phase": "near_critical", "active_lines": 11})
        status = os.get_status()
        assert status["scans"] == 1
        assert status["opportunities"] > 0
        assert status["best"] is not None


class TestGlobalEngine:
    def test_get_opportunity_scanner(self):
        g = get_opportunity_scanner()
        assert g is not None
        assert isinstance(g, OpportunityScanner)
