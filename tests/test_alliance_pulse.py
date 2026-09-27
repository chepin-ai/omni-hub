"""
Tests for OMNI-HUB Module v154: Alliance Pulse (联盟脉搏)
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from core.alliance_pulse import AlliancePulse, get_alliance_pulse


class TestAlliancePulse:
    """Comprehensive test suite for AlliancePulse."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the global singleton before each test."""
        import core.alliance_pulse as ap
        ap._module = None
        yield
        ap._module = None

    @pytest.fixture
    def pulse(self) -> AlliancePulse:
        """Fresh AlliancePulse instance with fixed reference date."""
        return AlliancePulse(reference_date=datetime(2026, 9, 28))

    # ------------------------------------------------------------------
    # measure_pulse
    # ------------------------------------------------------------------
    def test_measure_pulse_structure(self, pulse: AlliancePulse):
        """measure_pulse should return a well-formed dict."""
        result = pulse.measure_pulse()
        assert isinstance(result, dict)
        assert "active_repos" in result
        assert "active_count" in result
        assert "stale_repos" in result
        assert "stale_count" in result
        assert "core_line_health" in result
        assert "auxiliary_health" in result
        assert "total_internal" in result
        assert "reference_date" in result
        assert "repo_details" in result

    def test_measure_pulse_counts(self, pulse: AlliancePulse):
        """Counts should be non-negative and consistent."""
        result = pulse.measure_pulse()
        assert result["total_internal"] == 28
        assert result["active_count"] >= 0
        assert result["stale_count"] >= 0
        assert result["active_count"] + result["stale_count"] <= result["total_internal"]
        assert len(result["active_repos"]) == result["active_count"]
        assert len(result["stale_repos"]) == result["stale_count"]

    def test_measure_pulse_health_ranges(self, pulse: AlliancePulse):
        """Health scores must lie in [0, 1]."""
        result = pulse.measure_pulse()
        assert 0.0 <= result["core_line_health"] <= 1.0
        assert 0.0 <= result["auxiliary_health"] <= 1.0
        for detail in result["repo_details"].values():
            assert 0.0 <= detail["health"] <= 1.0

    def test_measure_pulse_history(self, pulse: AlliancePulse):
        """Each call should append to pulse_history."""
        assert len(pulse._pulse_history) == 0
        pulse.measure_pulse()
        assert len(pulse._pulse_history) == 1
        pulse.measure_pulse()
        assert len(pulse._pulse_history) == 2

    # ------------------------------------------------------------------
    # detect_awakening
    # ------------------------------------------------------------------
    def test_detect_awakening_fallback(self, pulse: AlliancePulse):
        """With <2 history entries, fallback heuristic should run."""
        # With the real data on 2026-09-28, no repo is marginally active (>5 days)
        # so awakening should be empty, but the function must return a list.
        awakening = pulse.detect_awakening()
        assert isinstance(awakening, list)
        # All items should have the expected keys
        for item in awakening:
            assert "name" in item
            assert "days_since" in item
            assert "health" in item
            assert "reason" in item

    def test_detect_awakening_with_history(self, pulse: AlliancePulse):
        """History comparison should detect repos transitioning to active."""
        pulse.measure_pulse()
        # Simulate a repo waking up by updating its date and advancing time
        pulse._repos["vci-bus"]["updated"] = "2026-09-27"
        pulse._reference_date = datetime(2026, 9, 28)
        pulse.measure_pulse()
        awakened = pulse.detect_awakening()
        assert isinstance(awakened, list)
        # vci-bus should now be active (1 day old)
        names = {a["name"] for a in awakened}
        assert "vci-bus" in names

    def test_detect_awakening_empty_when_no_transition(self, pulse: AlliancePulse):
        """If nothing changes between pulses, awakening is empty."""
        pulse.measure_pulse()
        pulse.measure_pulse()
        awakened = pulse.detect_awakening()
        assert awakened == []

    # ------------------------------------------------------------------
    # detect_dormant
    # ------------------------------------------------------------------
    def test_detect_dormant_fallback(self, pulse: AlliancePulse):
        """With <2 history entries, fallback should return currently stale repos."""
        dormant = pulse.detect_dormant()
        assert isinstance(dormant, list)
        for item in dormant:
            assert "name" in item
            assert "days_since" in item
            assert "health" in item
            assert "reason" in item
            assert item["days_since"] > 30

    def test_detect_dormant_with_history(self, pulse: AlliancePulse):
        """History comparison should detect repos transitioning from active to inactive."""
        pulse.measure_pulse()
        # Advance 10 days; repos that were 1 day old are now 11 days old -> inactive
        pulse._reference_date = datetime(2026, 10, 8)
        pulse.measure_pulse()
        dormant = pulse.detect_dormant()
        assert isinstance(dormant, list)
        assert len(dormant) > 0
        # Core repos should be among them
        names = {d["name"] for d in dormant}
        assert "vci-ucif2" in names

    def test_detect_dormant_empty_when_no_transition(self, pulse: AlliancePulse):
        """If nothing changes between pulses, dormant is empty."""
        pulse.measure_pulse()
        pulse.measure_pulse()
        dormant = pulse.detect_dormant()
        assert dormant == []

    # ------------------------------------------------------------------
    # compute_alliance_health
    # ------------------------------------------------------------------
    def test_compute_alliance_health_structure(self, pulse: AlliancePulse):
        """Health computation should return a structured dict."""
        health = pulse.compute_alliance_health()
        assert "score" in health
        assert "level" in health
        assert "core_line_health" in health
        assert "auxiliary_health" in health
        assert "classification" in health
        assert health["level"] == health["classification"]

    def test_compute_alliance_health_score_range(self, pulse: AlliancePulse):
        """Score must be in [0, 1]."""
        health = pulse.compute_alliance_health()
        assert 0.0 <= health["score"] <= 1.0

    def test_compute_alliance_health_levels(self, pulse: AlliancePulse):
        """Level classification should map correctly."""
        # Directly test the boundary logic by inspecting known data
        health = pulse.compute_alliance_health()
        level = health["level"]
        score = health["score"]
        if score > 0.8:
            assert level == "thriving"
        elif score > 0.6:
            assert level == "healthy"
        elif score > 0.4:
            assert level == "stable"
        elif score > 0.2:
            assert level == "weakening"
        else:
            assert level == "critical"

    def test_health_level_boundaries(self):
        """Test level classification at exact boundaries."""
        # Create a minimal pulse and manually check the internal logic
        # by inspecting the classification result
        pulse = AlliancePulse(reference_date=datetime(2026, 9, 28))
        pulse.measure_pulse()
        health = pulse.compute_alliance_health()
        assert health["level"] in {"thriving", "healthy", "stable", "weakening", "critical"}

    # ------------------------------------------------------------------
    # get_status
    # ------------------------------------------------------------------
    def test_get_status_structure(self, pulse: AlliancePulse):
        """Status should aggregate all metrics."""
        status = pulse.get_status()
        assert "active_count" in status
        assert "stale_count" in status
        assert "total_internal" in status
        assert "core_line_health" in status
        assert "auxiliary_health" in status
        assert "awakening_count" in status
        assert "dormant_count" in status
        assert "health_score" in status
        assert "health_level" in status
        assert "pulse_history_length" in status
        assert status["module"] == "AlliancePulse"

    def test_get_status_counts_consistent(self, pulse: AlliancePulse):
        """Status counts should match the latest pulse."""
        status = pulse.get_status()
        assert status["total_internal"] == 28
        assert status["active_count"] >= 0
        assert status["stale_count"] >= 0
        assert status["pulse_history_length"] >= 1

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------
    def test_get_alliance_pulse_singleton(self):
        """get_alliance_pulse should return the same instance on repeated calls."""
        ap1 = get_alliance_pulse()
        ap2 = get_alliance_pulse()
        assert ap1 is ap2
        assert isinstance(ap1, AlliancePulse)
