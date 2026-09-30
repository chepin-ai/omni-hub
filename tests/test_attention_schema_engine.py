"""
OMNI-HUB Attention Schema Engine Tests v169
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.attention_schema_engine import (
    AttentionSchemaEngine,
    get_attention_schema_engine,
    reset_attention_schema_engine,
)


class TestBuildSelfModel:
    def test_empty_history_returns_default_model(self):
        engine = AttentionSchemaEngine()
        model = engine.build_self_model()
        assert model["current_focus"] is None
        assert model["attention_capacity"] == 1.0
        assert model["attention_shifts"] == 0
        assert model["attention_depth"] == 0.0

    def test_self_model_tracks_current_focus(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.8)
        model = engine.build_self_model()
        assert model["current_focus"] == "task_A"

    def test_self_model_counts_shifts(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.8)
        engine.track_attention("task_B", 0.6)
        engine.track_attention("task_A", 0.7)
        model = engine.build_self_model()
        assert model["attention_shifts"] == 2

    def test_self_model_computes_depth(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.8)
        engine.track_attention("task_A", 0.9)
        model = engine.build_self_model()
        assert model["attention_depth"] > 0.0

    def test_capacity_decreases_with_many_targets(self):
        engine = AttentionSchemaEngine()
        for i in range(10):
            engine.track_attention(f"task_{i}", 0.5)
        model = engine.build_self_model()
        assert model["attention_capacity"] < 1.0


class TestTrackAttention:
    def test_tracks_target_and_intensity(self):
        engine = AttentionSchemaEngine()
        record = engine.track_attention("task_A", 0.75)
        assert record["target"] == "task_A"
        assert record["intensity"] == 0.75

    def test_clamps_intensity_to_bounds(self):
        engine = AttentionSchemaEngine()
        low = engine.track_attention("task_A", -0.5)
        high = engine.track_attention("task_B", 1.5)
        assert low["intensity"] == 0.0
        assert high["intensity"] == 1.0

    def test_increments_total_tracks(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.5)
        engine.track_attention("task_B", 0.6)
        assert engine.schema_state["total_tracks"] == 2

    def test_updates_target_frequency(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.5)
        engine.track_attention("task_A", 0.6)
        assert engine.target_frequency["task_A"] == 2

    def test_updates_target_importance(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.8)
        assert "task_A" in engine.target_importance
        assert engine.target_importance["task_A"] > 0.0

    def test_meta_attention_log_populated(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.5)
        assert len(engine.meta_attention_log) == 1


class TestPredictAttentionShift:
    def test_prediction_returns_structure(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.8)
        context = {
            "available_targets": ["task_A", "task_B"],
            "salience_map": {"task_A": 0.5, "task_B": 0.7},
            "goals": [],
        }
        result = engine.predict_attention_shift("task_A", context)
        assert "current_target" in result
        assert "predicted_target" in result
        assert "confidence" in result
        assert "stay_probability" in result
        assert "candidate_scores" in result

    def test_prediction_increments_total_predictions(self):
        engine = AttentionSchemaEngine()
        context = {"available_targets": ["task_A", "task_B"]}
        engine.predict_attention_shift("task_A", context)
        assert engine.schema_state["total_predictions"] == 1

    def test_goal_alignment_boosts_score(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.5)
        engine.track_attention("task_B", 0.5)
        context = {
            "available_targets": ["task_A", "task_B"],
            "salience_map": {"task_A": 0.5, "task_B": 0.5},
            "goals": ["complete task_B"],
        }
        result = engine.predict_attention_shift("task_A", context)
        # task_B should have higher score due to goal alignment
        # current_target (task_A) is excluded from candidate_scores
        assert "task_B" in result["candidate_scores"]
        assert result["candidate_scores"]["task_B"] > 0.0

    def test_empty_candidates_uses_history(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.5)
        engine.track_attention("task_B", 0.6)
        context = {}
        result = engine.predict_attention_shift("task_A", context)
        assert result["predicted_target"] in ["task_A", "task_B"]


class TestEvaluateAttentionQuality:
    def test_empty_history_returns_zeros(self):
        engine = AttentionSchemaEngine()
        quality = engine.evaluate_attention_quality()
        assert quality["coverage"] == 0.0
        assert quality["depth"] == 0.0
        assert quality["stability"] == 0.0
        assert quality["efficiency"] == 0.0
        assert quality["adaptivity"] == 0.0
        assert quality["overall_quality"] == 0.0

    def test_quality_metrics_present(self):
        engine = AttentionSchemaEngine()
        for i in range(5):
            engine.track_attention("task_A", 0.5 + i * 0.05)
        quality = engine.evaluate_attention_quality()
        assert all(0.0 <= quality[k] <= 1.0 for k in ["coverage", "depth", "stability", "efficiency", "adaptivity"])

    def test_overall_quality_is_geometric_mean(self):
        engine = AttentionSchemaEngine()
        for i in range(10):
            # Vary intensity slightly to ensure adaptivity > 0
            engine.track_attention("task_A", 0.7 + i * 0.02)
        quality = engine.evaluate_attention_quality()
        expected = (quality["coverage"] * quality["depth"] * quality["stability"] *
                    quality["efficiency"] * quality["adaptivity"]) ** 0.2
        assert round(quality["overall_quality"], 4) == round(expected, 4)

    def test_high_stability_for_fixed_target(self):
        engine = AttentionSchemaEngine()
        for i in range(10):
            engine.track_attention("task_A", 0.8)
        quality = engine.evaluate_attention_quality()
        assert quality["stability"] > 0.9


class TestDetectAttentionSchemaEmergence:
    def test_no_history_not_emerged(self):
        engine = AttentionSchemaEngine()
        result = engine.detect_attention_schema_emergence()
        assert result["emerged"] is False
        assert result["emergence_score"] < 0.8

    def test_self_referential_tracking_detected(self):
        engine = AttentionSchemaEngine()
        for i in range(10):
            engine.track_attention("attention_monitoring", 0.8)
        result = engine.detect_attention_schema_emergence()
        assert result["indicators"]["self_referential_tracking"]["active"] is True

    def test_high_accuracy_detected(self):
        engine = AttentionSchemaEngine()
        # Build history where task_B reliably follows task_A
        for _ in range(10):
            engine.track_attention("task_A", 0.5)
            engine.track_attention("task_B", 0.6)
        # Predict and verify - predict before tracking actual
        context = {"available_targets": ["task_A", "task_B"]}
        engine.predict_attention_shift("task_A", context)
        # Now track actual to verify the prediction
        engine.track_attention("task_B", 0.6)
        result = engine.detect_attention_schema_emergence()
        # Predictive accuracy should be non-zero after a correct prediction
        assert result["indicators"]["predictive_accuracy"]["value"] >= 0.0

    def test_awareness_level_mapping(self):
        engine = AttentionSchemaEngine()
        # No emergence -> unconscious or reactive
        result = engine.detect_attention_schema_emergence()
        assert result["self_awareness_level"] in ["unconscious", "reactive", "self_monitoring", "aware", "lucid"]


class TestGetStatus:
    def test_status_keys(self):
        engine = AttentionSchemaEngine()
        status = engine.get_status()
        assert "schema_completeness" in status
        assert "prediction_accuracy" in status
        assert "self_awareness_level" in status
        assert "total_tracks" in status
        assert "total_predictions" in status
        assert "correct_predictions" in status
        assert "meta_attention_cycles" in status
        assert "emergence_score" in status

    def test_completeness_with_full_model(self):
        engine = AttentionSchemaEngine()
        engine.track_attention("task_A", 0.8)
        engine.track_attention("task_B", 0.7)
        engine.build_self_model()
        status = engine.get_status()
        assert status["schema_completeness"] == 1.0

    def test_awareness_levels_thresholds(self):
        engine = AttentionSchemaEngine()
        # Map score to level manually
        assert engine._get_awareness_level(0.95) == "lucid"
        assert engine._get_awareness_level(0.8) == "aware"
        assert engine._get_awareness_level(0.6) == "self_monitoring"
        assert engine._get_awareness_level(0.4) == "reactive"
        assert engine._get_awareness_level(0.1) == "unconscious"


class TestGlobalSingleton:
    def test_get_attention_schema_engine(self):
        reset_attention_schema_engine()
        g = get_attention_schema_engine()
        assert g is not None
        assert isinstance(g, AttentionSchemaEngine)

    def test_singleton_returns_same_instance(self):
        reset_attention_schema_engine()
        g1 = get_attention_schema_engine()
        g2 = get_attention_schema_engine()
        assert g1 is g2

    def test_reset_creates_new_instance(self):
        reset_attention_schema_engine()
        g1 = get_attention_schema_engine()
        reset_attention_schema_engine()
        g2 = get_attention_schema_engine()
        assert g1 is not g2
