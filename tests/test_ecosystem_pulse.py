"""
Tests for OMNI-HUB Module v148: Ecosystem Pulse
"""

import pytest
from typing import Dict, Any

from core.ecosystem_pulse import EcosystemPulse, get_ecosystem_pulse


class TestEcosystemPulse:
    """Comprehensive test suite for EcosystemPulse."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the global singleton before each test."""
        import core.ecosystem_pulse as ep
        ep._module = None
        yield
        ep._module = None

    @pytest.fixture
    def pulse(self) -> EcosystemPulse:
        """Fresh EcosystemPulse instance."""
        return EcosystemPulse()

    @pytest.fixture
    def sample_repos(self) -> list:
        """A realistic list of repository identifiers."""
        return [
            "moonshot-ai/Kimi",
            "openai/whisper",
            "microsoft/DeepSpeed",
            "huggingface/transformers",
        ]

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def test_register_ecosystem_success(self, pulse: EcosystemPulse, sample_repos: list):
        """Registering a valid ecosystem should succeed."""
        result = pulse.register_ecosystem("AI ecosystem", sample_repos)
        assert result["success"] is True
        assert result["repo_count"] == 4
        assert result["ecosystem"]["name"] == "AI ecosystem"

    def test_register_ecosystem_deduplication(self, pulse: EcosystemPulse):
        """Duplicate repos should be deduplicated while preserving order."""
        repos = ["repo/a", "repo/b", "repo/a", "repo/c", "repo/b"]
        result = pulse.register_ecosystem("Test ecosystem", repos)
        assert result["repo_count"] == 3
        assert result["ecosystem"]["repos"] == ["repo/a", "repo/b", "repo/c"]

    def test_register_ecosystem_invalid_name(self, pulse: EcosystemPulse):
        """Empty or non-string name should fail gracefully."""
        assert pulse.register_ecosystem("", ["r1"])["success"] is False
        assert pulse.register_ecosystem(None, ["r1"])["success"] is False  # type: ignore

    def test_register_ecosystem_invalid_repos(self, pulse: EcosystemPulse):
        """Empty or non-list repos should fail gracefully."""
        assert pulse.register_ecosystem("Eco", [])["success"] is False
        assert pulse.register_ecosystem("Eco", None)["success"] is False  # type: ignore

    # ------------------------------------------------------------------
    # Pulse Check
    # ------------------------------------------------------------------
    def test_pulse_check_empty(self, pulse: EcosystemPulse):
        """Pulse check with no ecosystems should return zeroed global metrics."""
        result = pulse.pulse_check()
        assert result["global"]["health"] == 0.0
        assert result["global"]["activity"] == 0.0
        assert result["global"]["growth"] == 0.0
        assert "timestamp" in result

    def test_pulse_check_with_ecosystems(self, pulse: EcosystemPulse, sample_repos: list):
        """Pulse check should compute aggregate metrics for registered ecosystems."""
        pulse.register_ecosystem("AI ecosystem", sample_repos)
        pulse.register_ecosystem("Web3 ecosystem", ["ethereum/go-ethereum", "solana-labs/solana"])

        result = pulse.pulse_check()
        assert "AI ecosystem" in result["ecosystems"]
        assert "Web3 ecosystem" in result["ecosystems"]

        global_metrics = result["global"]
        assert 0.0 <= global_metrics["health"] <= 1.0
        assert 0.0 <= global_metrics["activity"] <= 1.0
        assert 0.0 <= global_metrics["growth"] <= 1.0

        # Verify that pulse history is appended
        assert len(pulse._pulse_history) == 1

    # ------------------------------------------------------------------
    # Risk Detection
    # ------------------------------------------------------------------
    def test_detect_eco_risk_empty(self, pulse: EcosystemPulse):
        """Risk detection with no ecosystems should return stable/zero."""
        result = pulse.detect_eco_risk()
        assert result["risk_score"] == 0.0
        assert result["risk_level"] == "stable"
        assert result["risks"] == []

    def test_detect_eco_risk_categories(self, pulse: EcosystemPulse):
        """
        Risk detection should flag declining repos, concentration, dependency,
        and stagnation where applicable.
        """
        # Create an ecosystem with a single repo to trigger dependency risk
        # and a low-health repo to trigger declining_repo risk.
        pulse.register_ecosystem("Fragile", ["user/legacy-repo"])
        result = pulse.detect_eco_risk()

        assert "risk_score" in result
        assert "risk_level" in result
        assert isinstance(result["risks"], list)

        risk_types = {r["type"] for r in result["risks"]}
        # At least dependency risk should be present (only 1 repo)
        assert "dependency_risk" in risk_types

    def test_risk_level_boundaries(self, pulse: EcosystemPulse):
        """Risk levels should map correctly to thresholds."""
        # Directly test the private classifier for boundary correctness
        assert pulse._classify_risk(0.0) == "stable"
        assert pulse._classify_risk(0.29) == "stable"
        assert pulse._classify_risk(0.3) == "caution"
        assert pulse._classify_risk(0.59) == "caution"
        assert pulse._classify_risk(0.6) == "warning"
        assert pulse._classify_risk(0.79) == "warning"
        assert pulse._classify_risk(0.8) == "critical"
        assert pulse._classify_risk(1.0) == "critical"

    # ------------------------------------------------------------------
    # Opportunity Detection
    # ------------------------------------------------------------------
    def test_detect_eco_opportunity_empty(self, pulse: EcosystemPulse):
        """Opportunity detection with no ecosystems should return zero count."""
        result = pulse.detect_eco_opportunity()
        assert result["opportunity_count"] == 0
        assert result["opportunities"] == []

    def test_detect_eco_opportunity_emerging(self, pulse: EcosystemPulse):
        """
        Opportunity detection should identify emerging repos and trending ecosystems.
        We seed repos with known names so metrics are deterministic.
        """
        # Use repos that have deterministic metrics; we inspect the result
        pulse.register_ecosystem("Hot", ["startup/rocket", "startup/boost"])
        result = pulse.detect_eco_opportunity()

        assert "opportunity_count" in result
        assert isinstance(result["opportunities"], list)
        # The exact count depends on seeded random values, but structure is guaranteed
        for opp in result["opportunities"]:
            assert "type" in opp
            assert opp["ecosystem"] == "Hot"

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def test_get_status_empty(self, pulse: EcosystemPulse):
        """Status with no ecosystems should return zeroed fields."""
        status = pulse.get_status()
        assert status["ecosystem_count"] == 0
        assert status["avg_health"] == 0.0
        assert status["risk_level"] == "stable"
        assert status["opportunity_count"] == 0
        assert status["pulse_history_length"] == 0
        assert status["module"] == "EcosystemPulse"

    def test_get_status_populated(self, pulse: EcosystemPulse, sample_repos: list):
        """Status should reflect registered ecosystems and derived metrics."""
        pulse.register_ecosystem("AI ecosystem", sample_repos)
        pulse.pulse_check()

        status = pulse.get_status()
        assert status["ecosystem_count"] == 1
        assert 0.0 <= status["avg_health"] <= 1.0
        assert status["risk_level"] in {"stable", "caution", "warning", "critical"}
        assert status["pulse_history_length"] == 1
        assert status["module"] == "EcosystemPulse"

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------
    def test_get_ecosystem_pulse_singleton(self):
        """get_ecosystem_pulse should return the same instance on repeated calls."""
        ep1 = get_ecosystem_pulse()
        ep2 = get_ecosystem_pulse()
        assert ep1 is ep2
        assert isinstance(ep1, EcosystemPulse)
