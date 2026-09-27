"""
Tests for OMNI-HUB Module v142: BI Engine (商业智能引擎)
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.bi_engine import BIEngine, get_bi_engine, _module


class TestBIEngine:
    """Test suite for BIEngine class."""

    def setup_method(self):
        """Reset singleton before each test."""
        global _module
        import core.bi_engine as bi_module
        bi_module._module = None

    def test_init(self):
        """Test BIEngine initialization."""
        engine = BIEngine()
        status = engine.get_status()
        assert status["module"] == "BIEngine"
        assert status["version"] == "v142"
        assert status["metric_count"] == 0
        assert status["report_count"] == 0
        assert status["trend_direction"] == "unknown"
        assert status["status"] == "active"

    def test_collect_metric_valid_category(self):
        """Test collecting metric with valid category."""
        engine = BIEngine()
        result = engine.collect_metric("revenue", 100000.0, "financial")
        assert result["status"] == "collected"
        assert result["metric"]["name"] == "revenue"
        assert result["metric"]["value"] == 100000.0
        assert result["metric"]["category"] == "financial"
        assert result["total_metrics"] == 1

    def test_collect_metric_invalid_category(self):
        """Test collecting metric with invalid category raises ValueError."""
        engine = BIEngine()
        with pytest.raises(ValueError, match="Invalid category"):
            engine.collect_metric("revenue", 100000.0, "invalid_category")

    def test_collect_metric_all_categories(self):
        """Test collecting metrics for all valid categories."""
        engine = BIEngine()
        categories = ["market", "financial", "operational", "customer", "product"]
        for i, cat in enumerate(categories):
            result = engine.collect_metric(f"metric_{cat}", float(i * 10), cat)
            assert result["status"] == "collected"
        assert engine._metric_count == 5

    def test_analyze_trends_no_data(self):
        """Test trend analysis with no metrics."""
        engine = BIEngine()
        trends = engine.analyze_trends()
        assert trends["status"] == "no_data"
        assert trends["overall_direction"] == "unknown"
        assert trends["trends"] == {}

    def test_analyze_trends_growth(self):
        """Test trend analysis detects growth."""
        engine = BIEngine()
        # Older values - low
        engine.collect_metric("revenue", 100.0, "financial")
        engine.collect_metric("revenue", 110.0, "financial")
        # Recent values - high
        engine.collect_metric("revenue", 200.0, "financial")
        engine.collect_metric("revenue", 220.0, "financial")
        trends = engine.analyze_trends()
        assert trends["status"] == "analyzed"
        assert trends["overall_direction"] == "growth"
        assert "financial" in trends["trends"]
        assert trends["trends"]["financial"]["direction"] == "growth"

    def test_analyze_trends_decline(self):
        """Test trend analysis detects decline."""
        engine = BIEngine()
        # Older values - high
        engine.collect_metric("profit", 500.0, "financial")
        engine.collect_metric("profit", 550.0, "financial")
        # Recent values - low
        engine.collect_metric("profit", 200.0, "financial")
        engine.collect_metric("profit", 220.0, "financial")
        trends = engine.analyze_trends()
        assert trends["status"] == "analyzed"
        assert trends["overall_direction"] == "decline"
        assert trends["trends"]["financial"]["direction"] == "decline"

    def test_analyze_trends_stable(self):
        """Test trend analysis detects stable."""
        engine = BIEngine()
        # Values staying roughly the same
        engine.collect_metric("cost", 100.0, "operational")
        engine.collect_metric("cost", 102.0, "operational")
        engine.collect_metric("cost", 101.0, "operational")
        engine.collect_metric("cost", 103.0, "operational")
        trends = engine.analyze_trends()
        assert trends["status"] == "analyzed"
        assert trends["trends"]["operational"]["direction"] == "stable"

    def test_generate_report_no_data(self):
        """Test report generation with no data."""
        engine = BIEngine()
        report = engine.generate_report()
        assert report["status"] == "no_data"
        assert "Collect business metrics" in report["recommendations"][0]
        assert engine._report_count == 1

    def test_generate_report_with_data(self):
        """Test report generation with metrics."""
        engine = BIEngine()
        engine.collect_metric("revenue", 1000.0, "financial")
        engine.collect_metric("users", 5000.0, "customer")
        report = engine.generate_report()
        assert report["status"] == "generated"
        assert report["metric_count"] == 2
        assert "financial" in report["kpis"]
        assert "customer" in report["kpis"]
        assert len(report["recommendations"]) > 0
        assert engine._report_count == 1

    def test_detect_opportunity_no_data(self):
        """Test opportunity detection with no data."""
        engine = BIEngine()
        opp = engine.detect_opportunity()
        assert opp["status"] == "no_data"
        assert opp["opportunities"] == []

    def test_detect_opportunity_high_growth_low_saturation(self):
        """Test opportunity detection finds high growth + low saturation."""
        engine = BIEngine()
        # Low initial value
        engine.collect_metric("market_share", 10.0, "market")
        engine.collect_metric("market_share", 12.0, "market")
        # High recent value -> strong growth
        engine.collect_metric("market_share", 50.0, "market")
        engine.collect_metric("market_share", 55.0, "market")
        opp = engine.detect_opportunity()
        assert opp["status"] == "analyzed"
        assert len(opp["opportunities"]) > 0
        top = opp["top_opportunity"]
        assert top is not None
        assert top["category"] == "market"
        assert top["signal"] == "high_growth_low_saturation"
        assert top["score"] > 50

    def test_detect_opportunity_declining(self):
        """Test opportunity detection for declining market."""
        engine = BIEngine()
        engine.collect_metric("sales", 1000.0, "product")
        engine.collect_metric("sales", 900.0, "product")
        engine.collect_metric("sales", 400.0, "product")
        engine.collect_metric("sales", 350.0, "product")
        opp = engine.detect_opportunity()
        assert opp["status"] == "analyzed"
        market_opp = next(
            (o for o in opp["opportunities"] if o["category"] == "product"), None
        )
        assert market_opp is not None
        assert market_opp["signal"] == "declining_market"
        assert market_opp["score"] < 20

    def test_get_status(self):
        """Test get_status returns expected structure."""
        engine = BIEngine()
        engine.collect_metric("m1", 10.0, "financial")
        engine.collect_metric("m2", 20.0, "market")
        engine.generate_report()
        status = engine.get_status()
        assert status["metric_count"] == 2
        assert status["report_count"] == 1
        assert status["module"] == "BIEngine"
        assert status["version"] == "v142"

    def test_singleton(self):
        """Test get_bi_engine returns same instance."""
        import core.bi_engine as bi_module
        bi_module._module = None
        engine1 = get_bi_engine()
        engine2 = get_bi_engine()
        assert engine1 is engine2

    def test_report_multiple_times(self):
        """Test generating multiple reports increments count."""
        engine = BIEngine()
        engine.collect_metric("x", 1.0, "operational")
        engine.generate_report()
        engine.generate_report()
        assert engine._report_count == 2

    def test_trend_multiple_categories(self):
        """Test trend analysis with multiple categories."""
        engine = BIEngine()
        # Financial - growth
        engine.collect_metric("revenue", 100.0, "financial")
        engine.collect_metric("revenue", 200.0, "financial")
        # Market - decline
        engine.collect_metric("share", 80.0, "market")
        engine.collect_metric("share", 40.0, "market")
        trends = engine.analyze_trends()
        assert trends["status"] == "analyzed"
        assert "financial" in trends["trends"]
        assert "market" in trends["trends"]

    def test_metric_has_timestamp(self):
        """Test collected metric has timestamp."""
        engine = BIEngine()
        result = engine.collect_metric("test", 42.0, "product")
        assert "timestamp" in result["metric"]
        assert result["metric"]["timestamp"] is not None

    def test_metric_has_id(self):
        """Test collected metric has incrementing ID."""
        engine = BIEngine()
        r1 = engine.collect_metric("a", 1.0, "customer")
        r2 = engine.collect_metric("b", 2.0, "customer")
        assert r1["metric"]["id"] == 1
        assert r2["metric"]["id"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
