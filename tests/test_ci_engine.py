"""
Tests for OMNI-HUB Module v143: CI Engine (竞争情报引擎)
"""

import pytest
import time
import sys
import os

# Ensure core module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.ci_engine import (
    CIEngine,
    get_ci_engine,
    _module,
    SIGNAL_WEIGHTS,
    VALID_SIGNAL_TYPES,
    THREAT_HIGH,
    THREAT_MEDIUM,
    MARKET_MOVE_THRESHOLD,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    global _module
    import core.ci_engine as ci_mod
    ci_mod._module = None
    yield
    ci_mod._module = None


@pytest.fixture
def engine():
    """Provide a fresh CIEngine instance."""
    return CIEngine()


class TestCIEngine:
    """Test suite for CIEngine."""

    def test_init(self, engine):
        """Test engine initialization."""
        assert engine.competitors == {}
        assert engine.intel_feeds == []
        assert engine.threat_level == 0.0
        assert engine._initialized_at <= time.time()

    def test_register_competitor_success(self, engine):
        """Test successful competitor registration."""
        result = engine.register_competitor(
            "AlphaCorp", "SaaS", ["pricing", "brand"]
        )
        assert result["success"] is True
        assert result["name"] == "AlphaCorp"
        assert result["domain"] == "SaaS"
        assert result["strengths"] == ["pricing", "brand"]
        assert result["competitor_count"] == 1
        assert "AlphaCorp" in engine.competitors

    def test_register_competitor_invalid_name(self, engine):
        """Test registration with invalid name."""
        result = engine.register_competitor("", "SaaS", ["pricing"])
        assert result["success"] is False
        assert "error" in result

    def test_register_competitor_invalid_domain(self, engine):
        """Test registration with invalid domain."""
        result = engine.register_competitor("AlphaCorp", "", ["pricing"])
        assert result["success"] is False
        assert "error" in result

    def test_register_competitor_invalid_strengths(self, engine):
        """Test registration with non-list strengths."""
        result = engine.register_competitor("AlphaCorp", "SaaS", "pricing")
        assert result["success"] is False
        assert "error" in result

    def test_register_multiple_competitors(self, engine):
        """Test registering multiple competitors."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.register_competitor("BetaInc", "Cloud", ["scale"])
        assert len(engine.competitors) == 2
        assert "AlphaCorp" in engine.competitors
        assert "BetaInc" in engine.competitors

    def test_collect_intel_success(self, engine):
        """Test successful intel collection."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        result = engine.collect_intel(
            "AlphaCorp", "product_launch", {"intensity": 0.9, "details": "New AI feature"}
        )
        assert result["success"] is True
        assert result["competitor"] == "AlphaCorp"
        assert result["intel"]["signal_type"] == "product_launch"
        assert result["intel"]["intensity"] == 0.9
        assert result["intel"]["weight"] == SIGNAL_WEIGHTS["product_launch"]
        assert len(engine.intel_feeds) == 1

    def test_collect_intel_unregistered_competitor(self, engine):
        """Test intel collection for unregistered competitor."""
        result = engine.collect_intel(
            "UnknownCorp", "product_launch", {"intensity": 0.9}
        )
        assert result["success"] is False
        assert "not registered" in result["error"]

    def test_collect_intel_invalid_signal_type(self, engine):
        """Test intel collection with invalid signal type."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        result = engine.collect_intel(
            "AlphaCorp", "invalid_signal", {"intensity": 0.9}
        )
        assert result["success"] is False
        assert "Invalid signal type" in result["error"]
        assert "valid_types" in result

    def test_collect_intel_all_signal_types(self, engine):
        """Test intel collection for all valid signal types."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        for sig_type in VALID_SIGNAL_TYPES:
            result = engine.collect_intel(
                "AlphaCorp", sig_type, {"intensity": 0.5}
            )
            assert result["success"] is True, f"Failed for {sig_type}"
            assert result["intel"]["weight"] == SIGNAL_WEIGHTS[sig_type]

    def test_collect_intel_default_intensity(self, engine):
        """Test intel collection without explicit intensity."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        result = engine.collect_intel(
            "AlphaCorp", "hiring", {"details": "New hires"}
        )
        assert result["success"] is True
        assert result["intel"]["intensity"] == 0.5

    def test_collect_intel_clamps_intensity(self, engine):
        """Test that intensity is clamped to [0, 1]."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        result = engine.collect_intel(
            "AlphaCorp", "funding", {"intensity": 1.5}
        )
        assert result["intel"]["intensity"] == 1.0
        result2 = engine.collect_intel(
            "AlphaCorp", "funding", {"intensity": -0.5}
        )
        assert result2["intel"]["intensity"] == 0.0

    def test_assess_threat_no_signals(self, engine):
        """Test threat assessment with no signals."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        result = engine.assess_threat("AlphaCorp")
        assert result["success"] is True
        assert result["threat_score"] == 0.0
        assert result["threat_level"] == "low"
        assert result["signal_count"] == 0

    def test_assess_threat_with_signals(self, engine):
        """Test threat assessment with signals."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.collect_intel("AlphaCorp", "funding", {"intensity": 0.9})
        result = engine.assess_threat("AlphaCorp")
        assert result["success"] is True
        assert result["threat_score"] > 0.0
        assert result["signal_count"] == 1

    def test_assess_threat_unregistered(self, engine):
        """Test threat assessment for unregistered competitor."""
        result = engine.assess_threat("UnknownCorp")
        assert result["success"] is False
        assert "not registered" in result["error"]

    def test_assess_threat_levels(self, engine):
        """Test threat level categorization."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        # Low threat
        engine.collect_intel("AlphaCorp", "hiring", {"intensity": 0.1})
        result = engine.assess_threat("AlphaCorp")
        assert result["threat_level"] == "low"

        # Reset
        engine.competitors["AlphaCorp"]["signals"] = []

        # High threat
        engine.collect_intel("AlphaCorp", "tech_advance", {"intensity": 1.0})
        result = engine.assess_threat("AlphaCorp")
        assert result["threat_level"] == "high"
        assert result["threat_score"] >= THREAT_HIGH

    def test_detect_market_move_no_competitors(self, engine):
        """Test market move detection with no competitors."""
        result = engine.detect_market_move()
        assert result["success"] is True
        assert result["market_move_detected"] is False

    def test_detect_market_move_not_enough(self, engine):
        """Test market move detection with insufficient activity."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.collect_intel("AlphaCorp", "product_launch", {"intensity": 0.9})
        result = engine.detect_market_move()
        assert result["market_move_detected"] is False
        assert result["active_competitors"] == 1

    def test_detect_market_move_detected(self, engine):
        """Test successful market move detection."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.register_competitor("BetaInc", "Cloud", ["scale"])
        engine.register_competitor("GammaLtd", "AI", ["research"])

        engine.collect_intel("AlphaCorp", "product_launch", {"intensity": 0.9})
        engine.collect_intel("BetaInc", "funding", {"intensity": 0.95})
        engine.collect_intel("GammaLtd", "tech_advance", {"intensity": 0.8})

        result = engine.detect_market_move()
        assert result["success"] is True
        assert result["market_move_detected"] is True
        assert result["active_competitors"] >= MARKET_MOVE_THRESHOLD
        assert len(result["details"]) >= MARKET_MOVE_THRESHOLD

    def test_detect_market_move_low_intensity(self, engine):
        """Test that low intensity signals don't trigger market move."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.register_competitor("BetaInc", "Cloud", ["scale"])

        engine.collect_intel("AlphaCorp", "hiring", {"intensity": 0.3})
        engine.collect_intel("BetaInc", "hiring", {"intensity": 0.2})

        result = engine.detect_market_move()
        assert result["market_move_detected"] is False
        assert result["active_competitors"] == 0

    def test_get_status_empty(self, engine):
        """Test status on empty engine."""
        status = engine.get_status()
        assert status["module"] == "ci_engine"
        assert status["version"] == "143.0.0"
        assert status["competitor_count"] == 0
        assert status["threat_level"] == 0.0
        assert status["latest_intel"] is None
        assert status["intel_feed_count"] == 0
        assert status["uptime"] >= 0
        assert status["competitors"] == []

    def test_get_status_with_data(self, engine):
        """Test status with competitors and intel."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.collect_intel("AlphaCorp", "partnership", {"intensity": 0.8})

        status = engine.get_status()
        assert status["competitor_count"] == 1
        assert status["intel_feed_count"] == 1
        assert status["latest_intel"] is not None
        assert status["latest_intel"]["competitor"] == "AlphaCorp"
        assert status["latest_intel"]["signal_type"] == "partnership"
        assert status["latest_intel"]["intensity"] == 0.8
        assert status["threat_level"] > 0.0
        assert "AlphaCorp" in status["competitors"]

    def test_global_threat_updates(self, engine):
        """Test that global threat level updates correctly."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.register_competitor("BetaInc", "Cloud", ["scale"])

        engine.collect_intel("AlphaCorp", "hiring", {"intensity": 0.2})
        t1 = engine.threat_level

        engine.collect_intel("BetaInc", "tech_advance", {"intensity": 1.0})
        t2 = engine.threat_level

        assert t2 >= t1

    def test_singleton(self):
        """Test global singleton behavior."""
        import core.ci_engine as ci_mod
        ci_mod._module = None
        e1 = get_ci_engine()
        e2 = get_ci_engine()
        assert e1 is e2
        assert isinstance(e1, CIEngine)

    def test_multiple_intel_same_competitor(self, engine):
        """Test collecting multiple intel for same competitor."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        engine.collect_intel("AlphaCorp", "product_launch", {"intensity": 0.8})
        engine.collect_intel("AlphaCorp", "pricing_change", {"intensity": 0.6})
        engine.collect_intel("AlphaCorp", "partnership", {"intensity": 0.7})

        assert len(engine.intel_feeds) == 3
        assert len(engine.competitors["AlphaCorp"]["signals"]) == 3
        result = engine.assess_threat("AlphaCorp")
        assert result["signal_count"] == 3
        assert result["threat_score"] > 0.0

    def test_defensive_programming_data_not_dict(self, engine):
        """Test collect_intel with non-dict data."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        result = engine.collect_intel("AlphaCorp", "hiring", "not a dict")
        assert result["success"] is False
        assert "data must be a dict" in result["error"]

    def test_signal_weights_coverage(self, engine):
        """Test all signal types have weights."""
        for sig_type in VALID_SIGNAL_TYPES:
            assert sig_type in SIGNAL_WEIGHTS
            assert 0.0 < SIGNAL_WEIGHTS[sig_type] <= 1.0

    def test_threat_calculation_weighted_average(self, engine):
        """Test that threat uses weighted average correctly."""
        engine.register_competitor("AlphaCorp", "SaaS", ["pricing"])
        # hiring (weight 0.5) at intensity 1.0 + tech_advance (weight 0.95) at intensity 0.0
        engine.collect_intel("AlphaCorp", "hiring", {"intensity": 1.0})
        engine.collect_intel("AlphaCorp", "tech_advance", {"intensity": 0.0})
        result = engine.assess_threat("AlphaCorp")
        # weighted avg = (0.5*1.0 + 0.95*0.0) / (0.5 + 0.95) = 0.5 / 1.45 ≈ 0.3448
        expected = (0.5 * 1.0 + 0.95 * 0.0) / (0.5 + 0.95)
        assert abs(result["threat_score"] - round(expected, 4)) < 0.001
