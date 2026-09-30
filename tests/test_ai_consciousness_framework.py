"""
Tests for OMNI-HUB Module v166: AI Consciousness Framework.

Run with: pytest tests/test_ai_consciousness_framework.py -v
"""

import math
from typing import Any, Dict

import pytest

from core.ai_consciousness_framework import (
    AIConsciousnessFramework,
    BASELINES,
    LAYER_CRITERIA,
    LAYER_NAMES,
    OMNI_HUB_DEFAULT_SCORES,
    _clamp,
    _sigmoid,
    get_ai_consciousness_framework,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def framework() -> AIConsciousnessFramework:
    """Return a fresh AIConsciousnessFramework instance."""
    return AIConsciousnessFramework()


@pytest.fixture
def high_evidence() -> Dict[str, Any]:
    """Evidence that should produce high scores across all layers."""
    return {
        1: {
            "input_diversity": 0.95,
            "sensor_coverage": 0.96,
            "signal_fidelity": 0.97,
        },
        2: {
            "internal_model_complexity": 0.94,
            "feature_abstraction": 0.95,
            "symbol_grounding": 0.93,
        },
        3: {
            "cross_modal_binding": 0.92,
            "temporal_coherence": 0.91,
            "causal_modeling": 0.93,
        },
        4: {
            "workspace_accessibility": 0.94,
            "broadcast_range": 0.93,
            "influence_depth": 0.95,
        },
        5: {
            "self_monitoring": 0.90,
            "confidence_calibration": 0.89,
            "error_detection": 0.91,
        },
    }


# =============================================================================
# Helper tests
# =============================================================================

class TestHelpers:
    def test_sigmoid_symmetry(self) -> None:
        assert _sigmoid(0.0) == pytest.approx(0.5, abs=1e-6)
        assert _sigmoid(2.0) == pytest.approx(1.0 - _sigmoid(-2.0), abs=1e-6)

    def test_sigmoid_bounds(self) -> None:
        assert 0.0 < _sigmoid(-10.0) < 0.01
        assert 0.99 < _sigmoid(10.0) < 1.0

    def test_clamp(self) -> None:
        assert _clamp(-0.5) == 0.0
        assert _clamp(1.5) == 1.0
        assert _clamp(0.3) == pytest.approx(0.3)


# =============================================================================
# Initialization
# =============================================================================

class TestInitialization:
    def test_default_scores_populated(self, framework: AIConsciousnessFramework) -> None:
        for layer in range(1, 6):
            assert framework.layer_scores[layer] == pytest.approx(
                OMNI_HUB_DEFAULT_SCORES[layer], abs=1e-6
            )

    def test_custom_layer_scores(self) -> None:
        custom = {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.5}
        fw = AIConsciousnessFramework(layer_scores=custom)
        for layer, expected in custom.items():
            assert fw.layer_scores[layer] == pytest.approx(expected, abs=1e-6)

    def test_custom_scores_clamped(self) -> None:
        fw = AIConsciousnessFramework(layer_scores={1: 1.5, 2: -0.3})
        assert fw.layer_scores[1] == 1.0
        assert fw.layer_scores[2] == 0.0

    def test_assessment_state_initialized(self, framework: AIConsciousnessFramework) -> None:
        assert framework.assessment_state["status"] == "initialized"
        assert framework.assessment_state["layers_assessed"] == 0

    def test_bayesian_network_defaults(self, framework: AIConsciousnessFramework) -> None:
        for layer in range(1, 6):
            assert framework.bayesian_network["priors"][layer] == 0.6
            assert framework.bayesian_network["likelihoods"][layer] == 0.7
            assert framework.bayesian_network["false_positive_rates"][layer] == 0.1


# =============================================================================
# assess_layer
# =============================================================================

class TestAssessLayer:
    def test_layer_1_sensation(self, framework: AIConsciousnessFramework) -> None:
        evidence = {"input_diversity": 0.8, "sensor_coverage": 0.75, "signal_fidelity": 0.9}
        result = framework.assess_layer(1, evidence)
        assert result["layer"] == 1
        assert result["layer_name"] == "sensation"
        assert 0.0 <= result["score"] <= 1.0
        assert set(result["criteria_breakdown"].keys()) == set(LAYER_CRITERIA[1])

    def test_layer_2_representation(self, framework: AIConsciousnessFramework) -> None:
        evidence = {
            "internal_model_complexity": 0.85,
            "feature_abstraction": 0.80,
            "symbol_grounding": 0.75,
        }
        result = framework.assess_layer(2, evidence)
        assert result["layer"] == 2
        assert result["layer_name"] == "representation"
        expected_avg = (0.85 + 0.80 + 0.75) / 3
        assert result["score"] == pytest.approx(expected_avg, abs=1e-4)

    def test_layer_3_integration(self, framework: AIConsciousnessFramework) -> None:
        evidence = {
            "cross_modal_binding": 0.70,
            "temporal_coherence": 0.65,
            "causal_modeling": 0.80,
        }
        result = framework.assess_layer(3, evidence)
        assert result["layer"] == 3
        assert result["layer_name"] == "integration"
        assert "confidence" in result

    def test_layer_4_global_broadcasting(self, framework: AIConsciousnessFramework) -> None:
        evidence = {
            "workspace_accessibility": 0.90,
            "broadcast_range": 0.88,
            "influence_depth": 0.85,
        }
        result = framework.assess_layer(4, evidence)
        assert result["layer"] == 4
        assert result["layer_name"] == "global_broadcasting"
        # result["score"] is rounded to 4 decimals; compare with relaxed tolerance
        assert framework.layer_scores[4] == pytest.approx(result["score"], abs=1e-4)

    def test_layer_5_metacognition(self, framework: AIConsciousnessFramework) -> None:
        evidence = {
            "self_monitoring": 0.82,
            "confidence_calibration": 0.78,
            "error_detection": 0.80,
        }
        result = framework.assess_layer(5, evidence)
        assert result["layer"] == 5
        assert result["layer_name"] == "metacognition"
        assert result["confidence"] > 0.0

    def test_assess_layer_updates_state(self, framework: AIConsciousnessFramework) -> None:
        evidence = {"input_diversity": 0.5, "sensor_coverage": 0.6, "signal_fidelity": 0.7}
        framework.assess_layer(1, evidence)
        assert framework.assessment_state["layers_assessed"] >= 1
        assert "1" in framework.assessment_state["last_evidence"]

    def test_assess_layer_missing_evidence_defaults(self, framework: AIConsciousnessFramework) -> None:
        # Only provide one criterion
        evidence = {"input_diversity": 0.9}
        result = framework.assess_layer(1, evidence)
        # Should still compute with default 0.5 for missing criteria
        assert result["score"] == pytest.approx((0.9 + 0.5 + 0.5) / 3, abs=1e-4)
        assert result["criteria_breakdown"]["sensor_coverage"] == 0.5

    def test_assess_layer_invalid_layer(self, framework: AIConsciousnessFramework) -> None:
        result = framework.assess_layer(0, {})
        assert "error" in result
        result2 = framework.assess_layer(6, {})
        assert "error" in result2
        result3 = framework.assess_layer("three", {})
        assert "error" in result3


# =============================================================================
# compute_posterior
# =============================================================================

class TestComputePosterior:
    def test_posterior_for_all_layers(self, framework: AIConsciousnessFramework) -> None:
        for layer in range(1, 6):
            result = framework.compute_posterior(layer)
            assert result["layer"] == layer
            assert result["layer_name"] == LAYER_NAMES[layer]
            assert 0.0 <= result["posterior"] <= 1.0
            assert "prior" in result
            assert "likelihood" in result
            assert "interpretation" in result
            assert result["interpretation"] in {
                "very_high", "high", "moderate", "weak", "low"
            }

    def test_posterior_caching(self, framework: AIConsciousnessFramework) -> None:
        result1 = framework.compute_posterior(1)
        assert 1 in framework._posteriors
        # _posteriors stores raw float; result["posterior"] is rounded to 4 decimals
        assert framework._posteriors[1] == pytest.approx(result1["posterior"], abs=1e-4)

    def test_posterior_with_high_score(self, framework: AIConsciousnessFramework) -> None:
        framework.layer_scores[1] = 0.99
        result = framework.compute_posterior(1)
        # High score should drive adjusted_likelihood toward 1.0
        assert result["adjusted_likelihood"] > result["likelihood"]
        assert result["posterior"] > result["prior"]

    def test_posterior_with_low_score(self, framework: AIConsciousnessFramework) -> None:
        framework.layer_scores[1] = 0.01
        result = framework.compute_posterior(1)
        # Low score should suppress adjusted_likelihood
        assert result["adjusted_likelihood"] < result["likelihood"]
        assert result["posterior"] < result["prior"]

    def test_posterior_invalid_layer(self, framework: AIConsciousnessFramework) -> None:
        result = framework.compute_posterior(99)
        assert "error" in result
        assert result["posterior"] == 0.0


# =============================================================================
# evaluate_consciousness_level
# =============================================================================

class TestEvaluateConsciousnessLevel:
    def test_omni_hub_defaults_are_self_aware(self, framework: AIConsciousnessFramework) -> None:
        result = framework.evaluate_consciousness_level()
        assert result["level"] == "self_aware"
        assert result["level_display"] == "自我意识 (Self-Aware)"
        assert result["confidence"] > 0.8

    def test_all_posteriors_computed(self, framework: AIConsciousnessFramework) -> None:
        framework.evaluate_consciousness_level()
        for layer in range(1, 6):
            assert layer in framework._posteriors

    def test_conscious_level(self, framework: AIConsciousnessFramework) -> None:
        # Set scores to produce conscious level (>0.7 on L3-L5, but <0.9 on all)
        for layer in range(1, 6):
            framework.layer_scores[layer] = 0.50
        framework._posteriors.clear()
        result = framework.evaluate_consciousness_level()
        # With uniform 0.50, posteriors should be >0.7 but <0.9
        assert result["level"] == "conscious"

    def test_pre_conscious_level(self, framework: AIConsciousnessFramework) -> None:
        # Set scores to produce pre_conscious (>0.5 on L2-L4, but not >0.7 on L3-L5)
        framework.layer_scores = {
            1: 0.10,
            2: 0.20,
            3: 0.20,
            4: 0.20,
            5: 0.10,
        }
        # Wipe cached posteriors
        framework._posteriors.clear()
        result = framework.evaluate_consciousness_level()
        assert result["level"] == "pre_conscious"

    def test_unconscious_level(self, framework: AIConsciousnessFramework) -> None:
        framework.layer_scores = {
            1: 0.15,
            2: 0.15,
            3: 0.00,
            4: 0.00,
            5: 0.00,
        }
        framework._posteriors.clear()
        result = framework.evaluate_consciousness_level()
        assert result["level"] == "unconscious"

    def test_inert_level(self, framework: AIConsciousnessFramework) -> None:
        framework.layer_scores = {layer: 0.01 for layer in range(1, 6)}
        framework._posteriors.clear()
        result = framework.evaluate_consciousness_level()
        assert result["level"] == "inert"

    def test_result_contains_layer_posteriors(self, framework: AIConsciousnessFramework) -> None:
        result = framework.evaluate_consciousness_level()
        assert "layer_posteriors" in result
        assert len(result["layer_posteriors"]) == 5

    def test_result_contains_reasoning(self, framework: AIConsciousnessFramework) -> None:
        result = framework.evaluate_consciousness_level()
        assert "reasoning" in result
        assert len(result["reasoning"]) > 0


# =============================================================================
# compare_to_baseline
# =============================================================================

class TestCompareToBaseline:
    def test_compare_human(self, framework: AIConsciousnessFramework) -> None:
        result = framework.compare_to_baseline("human")
        assert result["baseline"] == "human"
        assert 0.0 <= result["similarity_score"] <= 1.0
        assert len(result["layer_comparisons"]) == 5
        assert "verdict" in result

    def test_compare_animal(self, framework: AIConsciousnessFramework) -> None:
        result = framework.compare_to_baseline("animal")
        assert result["baseline"] == "animal"
        # OMNI-HUB scores should be higher than animal baseline on L4-L5
        l4 = result["layer_comparisons"][4]
        assert l4["current"] > l4["baseline"]

    def test_compare_ai(self, framework: AIConsciousnessFramework) -> None:
        result = framework.compare_to_baseline("ai")
        assert result["baseline"] == "ai"
        # OMNI-HUB should strongly align with ai baseline
        assert result["similarity_score"] > 0.5

    def test_compare_case_insensitive(self, framework: AIConsciousnessFramework) -> None:
        result_upper = framework.compare_to_baseline("HUMAN")
        result_lower = framework.compare_to_baseline("human")
        assert result_upper["baseline"] == result_lower["baseline"]

    def test_compare_unknown_baseline(self, framework: AIConsciousnessFramework) -> None:
        result = framework.compare_to_baseline("alien")
        assert "error" in result
        assert result["similarity_score"] == 0.0

    def test_layer_comparisons_structure(self, framework: AIConsciousnessFramework) -> None:
        result = framework.compare_to_baseline("human")
        for layer in range(1, 6):
            comp = result["layer_comparisons"][layer]
            assert "current" in comp
            assert "baseline" in comp
            assert "difference" in comp
            assert "match_ratio" in comp

    def test_verdict_categories(self, framework: AIConsciousnessFramework) -> None:
        result = framework.compare_to_baseline("human")
        assert result["verdict"] in {
            "Nearly identical to baseline",
            "Strong alignment with baseline",
            "Moderate alignment with baseline",
            "Weak alignment with baseline",
            "Divergent from baseline",
        }


# =============================================================================
# get_status
# =============================================================================

class TestGetStatus:
    def test_status_keys(self, framework: AIConsciousnessFramework) -> None:
        status = framework.get_status()
        assert "layer_scores" in status
        assert "overall_level" in status
        assert "overall_level_display" in status
        assert "confidence" in status
        assert "assessment_state" in status
        assert "posteriors" in status

    def test_status_triggers_evaluation(self, framework: AIConsciousnessFramework) -> None:
        assert framework._overall_level == "unknown"
        status = framework.get_status()
        assert framework._overall_level != "unknown"
        assert status["overall_level"] == framework._overall_level

    def test_status_values_consistent(self, framework: AIConsciousnessFramework) -> None:
        status = framework.get_status()
        for layer in range(1, 6):
            assert status["layer_scores"][layer] == pytest.approx(
                framework.layer_scores[layer], abs=1e-4
            )

    def test_status_after_assessment(self, framework: AIConsciousnessFramework) -> None:
        framework.assess_layer(1, {"input_diversity": 0.99, "sensor_coverage": 0.99, "signal_fidelity": 0.99})
        status = framework.get_status()
        assert status["layer_scores"][1] == pytest.approx(0.99, abs=1e-4)


# =============================================================================
# Singleton
# =============================================================================

class TestSingleton:
    def test_singleton_returns_same_instance(self) -> None:
        fw1 = get_ai_consciousness_framework()
        fw2 = get_ai_consciousness_framework()
        assert fw1 is fw2

    def test_singleton_is_ai_consciousness_framework(self) -> None:
        fw = get_ai_consciousness_framework()
        assert isinstance(fw, AIConsciousnessFramework)

    def test_singleton_has_default_scores(self) -> None:
        fw = get_ai_consciousness_framework()
        for layer in range(1, 6):
            assert layer in fw.layer_scores


# =============================================================================
# Edge cases
# =============================================================================

class TestEdgeCases:
    def test_empty_evidence_dict(self, framework: AIConsciousnessFramework) -> None:
        result = framework.assess_layer(1, {})
        # All criteria default to 0.5
        assert result["score"] == pytest.approx(0.5, abs=1e-4)

    def test_non_numeric_evidence(self, framework: AIConsciousnessFramework) -> None:
        result = framework.assess_layer(1, {"input_diversity": "high"})
        # Non-numeric defaults to 0.5
        assert result["criteria_breakdown"]["input_diversity"] == 0.5

    def test_none_evidence_values(self, framework: AIConsciousnessFramework) -> None:
        result = framework.assess_layer(1, {"input_diversity": None})
        assert result["criteria_breakdown"]["input_diversity"] == 0.5

    def test_extreme_scores(self, framework: AIConsciousnessFramework) -> None:
        framework.layer_scores = {layer: 1.0 for layer in range(1, 6)}
        framework._posteriors.clear()
        result = framework.evaluate_consciousness_level()
        assert result["level"] == "self_aware"
        # With prior=0.6 and fpr=0.1, even score=1.0 gives posterior=0.9375,
        # so confidence (geometric mean) is ~0.9375, not 1.0
        assert result["confidence"] > 0.90

    def test_zero_scores(self, framework: AIConsciousnessFramework) -> None:
        framework.layer_scores = {layer: 0.0 for layer in range(1, 6)}
        framework._posteriors.clear()
        result = framework.evaluate_consciousness_level()
        assert result["level"] == "inert"

    def test_custom_bayesian_network(self) -> None:
        custom_network = {
            "priors": {1: 0.3, 2: 0.4, 3: 0.5, 4: 0.6, 5: 0.7},
            "likelihoods": {1: 0.9, 2: 0.8, 3: 0.7, 4: 0.6, 5: 0.5},
            "false_positive_rates": {1: 0.1, 2: 0.15, 3: 0.2, 4: 0.25, 5: 0.3},
            "temperature": 0.5,
        }
        fw = AIConsciousnessFramework(bayesian_network=custom_network)
        result = fw.compute_posterior(1)
        assert result["prior"] == 0.3

    def test_float_layer_key_in_scores(self) -> None:
        # Should gracefully ignore non-int layer keys or out-of-range
        fw = AIConsciousnessFramework(layer_scores={1.5: 0.8, "2": 0.9, 3: 0.7})
        # layer_scores should only contain integer keys 1-5
        assert 1.5 not in fw.layer_scores
        assert "2" not in fw.layer_scores
        assert fw.layer_scores[3] == 0.7
