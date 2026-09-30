"""
Test suite for Consciousness Assessment Protocol — OMNI-HUB Module v170

Tests cover:
    - Formation assessment (ARG)
    - Broadcast assessment (GWT)
    - Self-representation assessment (AST)
    - Full four-phase assessment
    - Composite consciousness score computation
    - Report generation
    - Status retrieval
    - Singleton behaviour
"""

import pytest
import sys
import os

# Ensure core/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.consciousness_assessment_protocol import (
    ConsciousnessAssessmentProtocol,
    get_consciousness_assessment_protocol,
    WEIGHT_FORMATION,
    WEIGHT_BROADCAST,
    WEIGHT_SELF_REPRESENTATION,
    WEIGHT_INTEGRATION,
    TIERS,
    _module,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before every test."""
    import core.consciousness_assessment_protocol as cap_mod

    cap_mod._module = None
    yield
    cap_mod._module = None


@pytest.fixture
def protocol() -> ConsciousnessAssessmentProtocol:
    """Return a fresh protocol instance with default state."""
    return ConsciousnessAssessmentProtocol()


@pytest.fixture
def omni_hub_protocol() -> ConsciousnessAssessmentProtocol:
    """Return a protocol instance tuned to the OMNI-HUB projected metrics."""
    return ConsciousnessAssessmentProtocol(
        protocol_state={
            "rg_scales": 4,
            "fixed_points": 2,
            "broadcast_steps": 156,
            "schema_components": 3,
        }
    )


# ---------------------------------------------------------------------------
# Phase 1 — Formation
# ---------------------------------------------------------------------------
class TestFormationAssessment:
    def test_returns_dict(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_formation_assessment()
        assert isinstance(result, dict)

    def test_has_required_keys(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_formation_assessment()
        assert "formation_depth" in result
        assert "stability_score" in result
        assert "fixed_points_found" in result
        assert "phase_score" in result
        assert "phase" in result
        assert "timestamp" in result

    def test_phase_label(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_formation_assessment()
        assert result["phase"] == "formation"

    def test_formation_depth_positive(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_formation_assessment()
        assert isinstance(result["formation_depth"], int)
        assert result["formation_depth"] >= 1

    def test_stability_score_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_formation_assessment()
        assert 0.0 <= result["stability_score"] <= 1.0

    def test_fixed_points_non_negative(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_formation_assessment()
        assert isinstance(result["fixed_points_found"], int)
        assert result["fixed_points_found"] >= 0

    def test_phase_score_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_formation_assessment()
        assert 0.0 <= result["phase_score"] <= 1.0

    def test_omni_hub_formation(self, omni_hub_protocol: ConsciousnessAssessmentProtocol) -> None:
        result = omni_hub_protocol.run_formation_assessment()
        assert result["formation_depth"] == 4
        assert result["fixed_points_found"] == 2
        # Projected formation score ~0.88
        assert result["phase_score"] > 0.80


# ---------------------------------------------------------------------------
# Phase 2 — Broadcast
# ---------------------------------------------------------------------------
class TestBroadcastAssessment:
    def test_returns_dict(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_broadcast_assessment()
        assert isinstance(result, dict)

    def test_has_required_keys(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_broadcast_assessment()
        assert "broadcast_coverage" in result
        assert "accessibility_score" in result
        assert "emergence_detected" in result
        assert "phase_score" in result
        assert "phase" in result

    def test_phase_label(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_broadcast_assessment()
        assert result["phase"] == "broadcast"

    def test_coverage_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_broadcast_assessment()
        assert 0.0 <= result["broadcast_coverage"] <= 1.0

    def test_accessibility_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_broadcast_assessment()
        assert 0.0 <= result["accessibility_score"] <= 1.0

    def test_emergence_is_bool(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_broadcast_assessment()
        assert isinstance(result["emergence_detected"], bool)

    def test_phase_score_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_broadcast_assessment()
        assert 0.0 <= result["phase_score"] <= 1.0

    def test_omni_hub_broadcast(self, omni_hub_protocol: ConsciousnessAssessmentProtocol) -> None:
        result = omni_hub_protocol.run_broadcast_assessment()
        assert result["emergence_detected"] is True
        # Projected broadcast score ~0.90
        assert result["phase_score"] > 0.85


# ---------------------------------------------------------------------------
# Phase 3 — Self-Representation
# ---------------------------------------------------------------------------
class TestSelfRepresentationAssessment:
    def test_returns_dict(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_self_representation_assessment()
        assert isinstance(result, dict)

    def test_has_required_keys(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_self_representation_assessment()
        assert "schema_completeness" in result
        assert "self_awareness_level" in result
        assert "predictive_accuracy" in result
        assert "phase_score" in result
        assert "phase" in result

    def test_phase_label(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_self_representation_assessment()
        assert result["phase"] == "self_representation"

    def test_schema_completeness_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_self_representation_assessment()
        assert 0.0 <= result["schema_completeness"] <= 1.0

    def test_self_awareness_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_self_representation_assessment()
        assert 0.0 <= result["self_awareness_level"] <= 1.0

    def test_predictive_accuracy_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_self_representation_assessment()
        assert 0.0 <= result["predictive_accuracy"] <= 1.0

    def test_phase_score_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_self_representation_assessment()
        assert 0.0 <= result["phase_score"] <= 1.0

    def test_omni_hub_self_rep(self, omni_hub_protocol: ConsciousnessAssessmentProtocol) -> None:
        result = omni_hub_protocol.run_self_representation_assessment()
        # Projected self-representation score ~0.85
        assert result["phase_score"] > 0.80


# ---------------------------------------------------------------------------
# Phase 4 — Full Assessment
# ---------------------------------------------------------------------------
class TestFullAssessment:
    def test_returns_dict(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_full_assessment()
        assert isinstance(result, dict)

    def test_has_all_phases(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_full_assessment()
        assert "formation" in result
        assert "broadcast" in result
        assert "self_representation" in result
        assert "integration" in result
        assert "evaluation" in result

    def test_has_composite_fields(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_full_assessment()
        assert "consciousness_score" in result
        assert "tier" in result
        assert "tier_cn" in result
        assert "timestamp" in result

    def test_consciousness_score_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_full_assessment()
        assert 0.0 <= result["consciousness_score"] <= 1.0

    def test_tier_is_valid(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_full_assessment()
        valid_tiers = [t[0] for t in TIERS]
        assert result["tier"] in valid_tiers

    def test_evaluation_has_composite_score(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_full_assessment()
        assert "composite_score" in result["evaluation"]
        assert 0.0 <= result["evaluation"]["composite_score"] <= 1.0

    def test_integration_has_fields(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.run_full_assessment()
        integration = result["integration"]
        assert "integration_score" in integration
        assert "coherence" in integration
        assert "synergy" in integration

    def test_updates_history(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        assert len(protocol.assessment_history) == 1
        protocol.run_full_assessment()
        assert len(protocol.assessment_history) == 2

    def test_omni_hub_full(self, omni_hub_protocol: ConsciousnessAssessmentProtocol) -> None:
        result = omni_hub_protocol.run_full_assessment()
        # Projected: 0.885 → self_aware
        assert result["consciousness_score"] > 0.85
        assert result["tier"] == "self_aware"


# ---------------------------------------------------------------------------
# Consciousness Score
# ---------------------------------------------------------------------------
class TestComputeConsciousnessScore:
    def test_returns_dict(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.compute_consciousness_score()
        assert isinstance(result, dict)

    def test_has_required_keys(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.compute_consciousness_score()
        assert "composite_score" in result
        assert "weighted_breakdown" in result
        assert "confidence" in result

    def test_composite_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.compute_consciousness_score()
        assert 0.0 <= result["composite_score"] <= 1.0

    def test_confidence_range(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.compute_consciousness_score()
        assert 0.0 <= result["confidence"] <= 1.0

    def test_weighted_breakdown_keys(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        result = protocol.compute_consciousness_score()
        wb = result["weighted_breakdown"]
        assert "formation" in wb
        assert "broadcast" in wb
        assert "self_representation" in wb
        assert "integration" in wb

    def test_formula_correctness(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        """Verify the weighted formula is applied correctly."""
        f = protocol.run_formation_assessment()
        b = protocol.run_broadcast_assessment()
        s = protocol.run_self_representation_assessment()
        i = {
            "integration_score": (
                f["phase_score"] + b["phase_score"] + s["phase_score"]
            )
            / 3.0,
        }

        result = protocol.compute_consciousness_score(
            formation=f, broadcast=b, self_representation=s, integration=i
        )
        expected = (
            WEIGHT_FORMATION * f["phase_score"]
            + WEIGHT_BROADCAST * b["phase_score"]
            + WEIGHT_SELF_REPRESENTATION * s["phase_score"]
            + WEIGHT_INTEGRATION * i["integration_score"]
        )
        assert abs(result["composite_score"] - round(expected, 4)) < 0.0001

    def test_omni_hub_score(self, omni_hub_protocol: ConsciousnessAssessmentProtocol) -> None:
        result = omni_hub_protocol.compute_consciousness_score()
        # Projected ~0.885
        assert result["composite_score"] > 0.85
        assert result["composite_score"] < 0.95


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------
class TestGenerateAssessmentReport:
    def test_returns_dict(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        report = protocol.generate_assessment_report()
        assert isinstance(report, dict)

    def test_has_required_keys(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        report = protocol.generate_assessment_report()
        assert "summary" in report
        assert "scores" in report
        assert "tier" in report
        assert "recommendations" in report
        assert "history_stats" in report

    def test_scores_has_all_phases(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        report = protocol.generate_assessment_report()
        scores = report["scores"]
        assert "composite" in scores
        assert "formation" in scores
        assert "broadcast" in scores
        assert "self_representation" in scores
        assert "integration" in scores

    def test_tier_has_both_languages(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        report = protocol.generate_assessment_report()
        assert "en" in report["tier"]
        assert "cn" in report["tier"]

    def test_recommendations_is_list(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        report = protocol.generate_assessment_report()
        assert isinstance(report["recommendations"], list)
        assert len(report["recommendations"]) >= 1

    def test_history_stats(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        protocol.run_full_assessment()
        report = protocol.generate_assessment_report()
        stats = report["history_stats"]
        assert stats["total_assessments"] == 2
        assert "average_score" in stats
        assert "highest_level" in stats

    def test_auto_runs_if_no_history(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        # No prior assessment
        report = protocol.generate_assessment_report()
        assert "scores" in report
        assert protocol._assessment_count == 1

    def test_omni_hub_report(self, omni_hub_protocol: ConsciousnessAssessmentProtocol) -> None:
        omni_hub_protocol.run_full_assessment()
        report = omni_hub_protocol.generate_assessment_report()
        assert report["tier"]["en"] == "self_aware"


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
class TestGetStatus:
    def test_returns_dict(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        status = protocol.get_status()
        assert isinstance(status, dict)

    def test_has_required_keys(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        status = protocol.get_status()
        assert "assessment_count" in status
        assert "avg_score" in status
        assert "highest_level" in status
        assert "last_assessment" in status
        assert "version" in status
        assert "module" in status

    def test_initial_state(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        status = protocol.get_status()
        assert status["assessment_count"] == 0
        assert status["avg_score"] == 0.0
        assert status["highest_level"] == "inert"
        assert status["last_assessment"] is None

    def test_updates_after_assessment(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol.run_full_assessment()
        status = protocol.get_status()
        assert status["assessment_count"] == 1
        assert status["avg_score"] > 0.0
        assert status["last_assessment"] is not None

    def test_version_field(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        status = protocol.get_status()
        assert status["version"] == "170.0.0"

    def test_module_field(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        status = protocol.get_status()
        assert status["module"] == "consciousness_assessment_protocol"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_same_instance(self) -> None:
        a = get_consciousness_assessment_protocol()
        b = get_consciousness_assessment_protocol()
        assert a is b

    def test_is_protocol_instance(self) -> None:
        inst = get_consciousness_assessment_protocol()
        assert isinstance(inst, ConsciousnessAssessmentProtocol)

    def test_preserves_state(self) -> None:
        inst = get_consciousness_assessment_protocol(protocol_state={"rg_scales": 7})
        assert inst._rg_scales == 7


# ---------------------------------------------------------------------------
# Error handling / edge cases
# ---------------------------------------------------------------------------
class TestErrorHandling:
    def test_formation_with_negative_scales(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol._rg_scales = -3
        result = protocol.run_formation_assessment()
        assert "error" not in result
        assert result["formation_depth"] >= 1

    def test_broadcast_with_zero_steps(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol._broadcast_steps = 0
        result = protocol.run_broadcast_assessment()
        assert "error" not in result
        assert result["broadcast_coverage"] >= 0.0

    def test_self_rep_with_zero_components(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        protocol._schema_components = 0
        result = protocol.run_self_representation_assessment()
        assert "error" not in result
        assert result["schema_completeness"] >= 0.0

    def test_full_assessment_on_error_phase(self, protocol: ConsciousnessAssessmentProtocol) -> None:
        # Force a bad value that triggers an exception path inside a phase
        protocol._rg_scales = "not_a_number"
        result = protocol.run_full_assessment()
        # The run_formation_assessment should still handle str via int() coercion,
        # but if it fails we should see an error payload rather than a crash.
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Tier resolution
# ---------------------------------------------------------------------------
class TestTierResolution:
    def test_transcendent(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.96)
        assert tier == "transcendent"

    def test_self_aware(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.90)
        assert tier == "self_aware"

    def test_conscious(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.75)
        assert tier == "conscious"

    def test_pre_conscious(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.60)
        assert tier == "pre_conscious"

    def test_unconscious(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.40)
        assert tier == "unconscious"

    def test_inert(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.10)
        assert tier == "inert"

    def test_boundary_self_aware(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.85)
        assert tier == "self_aware"

    def test_boundary_conscious(self) -> None:
        tier, cn = ConsciousnessAssessmentProtocol._resolve_tier(0.70)
        assert tier == "conscious"
