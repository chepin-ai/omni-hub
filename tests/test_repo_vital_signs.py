"""
Tests for OMNI-HUB Module v157: Repository Vital Signs (仓库生命体征)
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from core.repo_vital_signs import RepoVitalSigns, get_repo_vital_signs


class TestRepoVitalSigns:
    """Comprehensive test suite for RepoVitalSigns."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the global singleton before each test."""
        import core.repo_vital_signs as rvs
        rvs._module = None
        yield
        rvs._module = None

    @pytest.fixture
    def vitals(self) -> RepoVitalSigns:
        """Fresh RepoVitalSigns instance with fixed reference date."""
        return RepoVitalSigns(reference_date=datetime(2026, 9, 28))

    # ------------------------------------------------------------------
    # measure_heartbeat
    # ------------------------------------------------------------------
    def test_measure_heartbeat_structure(self, vitals: RepoVitalSigns):
        """measure_heartbeat should return a well-formed dict."""
        result = vitals.measure_heartbeat("vci-ucif2")
        assert isinstance(result, dict)
        assert "repo" in result
        assert "bpm" in result
        assert "category" in result
        assert "days_since" in result

    def test_measure_heartbeat_today(self, vitals: RepoVitalSigns):
        """Repo updated today should have 120 bpm."""
        vitals._repos["vci-ucif2"]["updated"] = "2026-09-28"
        result = vitals.measure_heartbeat("vci-ucif2")
        assert result["bpm"] == 120
        assert result["category"] == "very_active"
        assert result["days_since"] == 0

    def test_measure_heartbeat_within_7_days(self, vitals: RepoVitalSigns):
        """Repo updated within 7 days should have 80 bpm."""
        # Set a repo to be updated 3 days ago
        vitals._repos["vci-ucif2"]["updated"] = "2026-09-25"
        result = vitals.measure_heartbeat("vci-ucif2")
        assert result["bpm"] == 80
        assert result["category"] == "active"
        assert result["days_since"] == 3

    def test_measure_heartbeat_within_30_days(self, vitals: RepoVitalSigns):
        """Repo updated within 30 days should have 50 bpm."""
        vitals._repos["vci-ucif2"]["updated"] = "2026-09-10"
        result = vitals.measure_heartbeat("vci-ucif2")
        assert result["bpm"] == 50
        assert result["category"] == "moderate"
        assert result["days_since"] == 18

    def test_measure_heartbeat_dormant(self, vitals: RepoVitalSigns):
        """Repo updated >30 days ago should have 20 bpm."""
        vitals._repos["vci-ucif2"]["updated"] = "2026-08-01"
        result = vitals.measure_heartbeat("vci-ucif2")
        assert result["bpm"] == 20
        assert result["category"] == "dormant"

    def test_measure_heartbeat_unknown_repo(self, vitals: RepoVitalSigns):
        """Unknown repo should return default heartbeat."""
        result = vitals.measure_heartbeat("nonexistent-repo")
        assert result["bpm"] == 0
        assert result["category"] == "unknown"

    def test_measure_heartbeat_external_no_date(self, vitals: RepoVitalSigns):
        """External repo without updated date should be dormant."""
        result = vitals.measure_heartbeat("langchain-ai/langchain")
        assert result["bpm"] == 20
        assert result["category"] == "dormant"

    # ------------------------------------------------------------------
    # measure_blood_pressure
    # ------------------------------------------------------------------
    def test_measure_blood_pressure_structure(self, vitals: RepoVitalSigns):
        """measure_blood_pressure should return a well-formed dict."""
        result = vitals.measure_blood_pressure("vci-ucif2")
        assert isinstance(result, dict)
        assert "repo" in result
        assert "systolic" in result
        assert "diastolic" in result
        assert "status" in result
        assert "normalized" in result

    def test_measure_blood_pressure_ranges(self, vitals: RepoVitalSigns):
        """Systolic and diastolic should be within expected ranges."""
        result = vitals.measure_blood_pressure("vci-ucif2")
        assert 0 <= result["systolic"] <= 20
        assert 0 <= result["diastolic"] <= 10
        assert 0.0 <= result["normalized"] <= 1.0

    def test_measure_blood_pressure_status_normal(self, vitals: RepoVitalSigns):
        """Status should be normal when systolic < 10."""
        # Use a deterministic repo name that yields systolic < 10
        # We can check the actual result
        result = vitals.measure_blood_pressure("vci-ucif2")
        if result["systolic"] < 10:
            assert result["status"] == "normal"

    def test_measure_blood_pressure_deterministic(self, vitals: RepoVitalSigns):
        """Blood pressure should be deterministic for the same repo."""
        r1 = vitals.measure_blood_pressure("vci-ucif2")
        r2 = vitals.measure_blood_pressure("vci-ucif2")
        assert r1 == r2

    def test_measure_blood_pressure_unknown_repo(self, vitals: RepoVitalSigns):
        """Unknown repo should return default blood pressure."""
        result = vitals.measure_blood_pressure("nonexistent-repo")
        assert result["systolic"] == 0
        assert result["diastolic"] == 0
        assert result["status"] == "unknown"

    # ------------------------------------------------------------------
    # measure_temperature
    # ------------------------------------------------------------------
    def test_measure_temperature_structure(self, vitals: RepoVitalSigns):
        """measure_temperature should return a well-formed dict."""
        result = vitals.measure_temperature("vci-ucif2")
        assert isinstance(result, dict)
        assert "repo" in result
        assert "celsius" in result
        assert "category" in result
        assert "normalized" in result

    def test_measure_temperature_python_recent(self, vitals: RepoVitalSigns):
        """Python repo updated today should be hot."""
        vitals._repos["vci-ucif2"]["updated"] = "2026-09-28"
        result = vitals.measure_temperature("vci-ucif2")
        assert result["celsius"] >= 38.0
        assert result["category"] == "hot"

    def test_measure_temperature_lean_old(self, vitals: RepoVitalSigns):
        """Lean repo updated long ago should be cold."""
        vitals._repos["grand-synthesis"]["updated"] = "2026-07-01"
        result = vitals.measure_temperature("grand-synthesis")
        assert result["celsius"] <= 25.0
        assert result["category"] == "cold"

    def test_measure_temperature_normalized_range(self, vitals: RepoVitalSigns):
        """Normalized temperature should be in [0, 1]."""
        for name in vitals._repos:
            result = vitals.measure_temperature(name)
            assert 0.0 <= result["normalized"] <= 1.0

    def test_measure_temperature_unknown_repo(self, vitals: RepoVitalSigns):
        """Unknown repo should return default temperature."""
        result = vitals.measure_temperature("nonexistent-repo")
        assert result["celsius"] == 20.0
        assert result["category"] == "unknown"

    # ------------------------------------------------------------------
    # measure_brainwaves
    # ------------------------------------------------------------------
    def test_measure_brainwaves_structure(self, vitals: RepoVitalSigns):
        """measure_brainwaves should return a well-formed dict."""
        result = vitals.measure_brainwaves("vci-ucif2")
        assert isinstance(result, dict)
        assert "repo" in result
        assert "innovation_index" in result
        assert "category" in result
        assert "description" in result

    def test_measure_brainwaves_core_high(self, vitals: RepoVitalSigns):
        """Core VCI lines should have high innovation."""
        result = vitals.measure_brainwaves("vci-ucif2")
        assert result["innovation_index"] == 0.85
        assert result["category"] == "high"

    def test_measure_brainwaves_research_high(self, vitals: RepoVitalSigns):
        """Research role repos should have high innovation."""
        result = vitals.measure_brainwaves("prima-50-research")
        assert result["innovation_index"] == 0.85
        assert result["category"] == "high"

    def test_measure_brainwaves_control_low(self, vitals: RepoVitalSigns):
        """Control role repos should have low innovation."""
        result = vitals.measure_brainwaves("vci-control")
        assert result["innovation_index"] == 0.2
        assert result["category"] == "low"

    def test_measure_brainwaves_unknown_repo(self, vitals: RepoVitalSigns):
        """Unknown repo should return default brainwaves."""
        result = vitals.measure_brainwaves("nonexistent-repo")
        assert result["innovation_index"] == 0.0
        assert result["category"] == "unknown"

    # ------------------------------------------------------------------
    # get_full_vitals
    # ------------------------------------------------------------------
    def test_get_full_vitals_structure(self, vitals: RepoVitalSigns):
        """get_full_vitals should return all vitals combined."""
        result = vitals.get_full_vitals("vci-ucif2")
        assert isinstance(result, dict)
        assert "repo" in result
        assert "heartbeat" in result
        assert "blood_pressure" in result
        assert "temperature" in result
        assert "brainwaves" in result
        assert "overall_health" in result
        assert "health_level" in result

    def test_get_full_vitals_health_range(self, vitals: RepoVitalSigns):
        """Overall health score must be in [0, 1]."""
        for name in vitals._repos:
            result = vitals.get_full_vitals(name)
            assert 0.0 <= result["overall_health"] <= 1.0

    def test_get_full_vitals_health_levels(self, vitals: RepoVitalSigns):
        """Health level should be one of the expected values."""
        valid_levels = {"excellent", "good", "fair", "poor", "critical"}
        for name in vitals._repos:
            result = vitals.get_full_vitals(name)
            assert result["health_level"] in valid_levels

    def test_get_full_vitals_unknown_repo(self, vitals: RepoVitalSigns):
        """Unknown repo should still return a structure."""
        result = vitals.get_full_vitals("nonexistent-repo")
        assert result["overall_health"] == 0.0
        assert result["health_level"] == "critical"

    # ------------------------------------------------------------------
    # measure_respiration
    # ------------------------------------------------------------------
    def test_measure_respiration_structure(self, vitals: RepoVitalSigns):
        """measure_respiration should return a well-formed dict."""
        result = vitals.measure_respiration("vci-ucif2")
        assert isinstance(result, dict)
        assert "repo" in result
        assert "contributor_count" in result
        assert "turnover_rate" in result
        assert "flow_status" in result

    def test_measure_respiration_ranges(self, vitals: RepoVitalSigns):
        """Respiration metrics should be in expected ranges."""
        result = vitals.measure_respiration("vci-ucif2")
        assert 0 <= result["contributor_count"] <= 20
        assert 0.0 <= result["turnover_rate"] <= 1.0
        assert result["flow_status"] in {"steady", "growing", "declining"}

    def test_measure_respiration_unknown_repo(self, vitals: RepoVitalSigns):
        """Unknown repo should return default respiration."""
        result = vitals.measure_respiration("nonexistent-repo")
        assert result["contributor_count"] == 0
        assert result["flow_status"] == "unknown"

    # ------------------------------------------------------------------
    # get_status
    # ------------------------------------------------------------------
    def test_get_status_structure(self, vitals: RepoVitalSigns):
        """get_status should return aggregate metrics."""
        status = vitals.get_status()
        assert isinstance(status, dict)
        assert status["module"] == "RepoVitalSigns"
        assert "monitored_count" in status
        assert "avg_heartbeat" in status
        assert "critical_count" in status
        assert "health_distribution" in status

    def test_get_status_counts(self, vitals: RepoVitalSigns):
        """Status counts should match the number of repos."""
        status = vitals.get_status()
        assert status["monitored_count"] == 33
        assert status["avg_heartbeat"] >= 20.0
        assert status["critical_count"] >= 0
        total_in_dist = sum(status["health_distribution"].values())
        assert total_in_dist == status["monitored_count"]

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------
    def test_get_repo_vital_signs_singleton(self):
        """get_repo_vital_signs should return the same instance on repeated calls."""
        rvs1 = get_repo_vital_signs()
        rvs2 = get_repo_vital_signs()
        assert rvs1 is rvs2
        assert isinstance(rvs1, RepoVitalSigns)

    # ------------------------------------------------------------------
    # Health classification boundaries
    # ------------------------------------------------------------------
    def test_classify_health_boundaries(self, vitals: RepoVitalSigns):
        """Health classification should be correct at boundaries."""
        assert vitals._classify_health(0.95) == "excellent"
        assert vitals._classify_health(0.85) == "good"
        assert vitals._classify_health(0.6) == "fair"
        assert vitals._classify_health(0.4) == "poor"
        assert vitals._classify_health(0.2) == "critical"
        assert vitals._classify_health(0.0) == "critical"
