"""
Tests for OMNI-HUB Module v144: QI Engine (质量智能引擎)
"""

import pytest
import sys
import os

# Ensure core module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.qi_engine import QIEngine, get_qi_engine, DIMENSIONS, _module


class TestQIEngineMeasurement:
    """Tests for the measure_dimension method."""

    def test_measure_dimension_basic(self):
        engine = QIEngine()
        result = engine.measure_dimension("code_health", 0.85)
        assert result["dimension"] == "code_health"
        assert result["score"] == 0.85
        assert result["weight"] == 1.0
        assert result["alert"] is None

    def test_measure_dimension_with_weight(self):
        engine = QIEngine()
        result = engine.measure_dimension("test_coverage", 0.9, weight=2.0)
        assert result["score"] == 0.9
        assert result["weight"] == 2.0

    def test_measure_dimension_clamps_high(self):
        engine = QIEngine()
        result = engine.measure_dimension("performance", 1.5)
        assert result["score"] == 1.0

    def test_measure_dimension_clamps_low(self):
        engine = QIEngine()
        result = engine.measure_dimension("security", -0.3)
        assert result["score"] == 0.0

    def test_measure_dimension_critical_alert(self):
        engine = QIEngine()
        result = engine.measure_dimension("reliability", 0.4)
        assert result["alert"] is not None
        assert result["alert"]["level"] == "critical"

    def test_measure_dimension_warning_alert(self):
        engine = QIEngine()
        result = engine.measure_dimension("maintainability", 0.6)
        assert result["alert"] is not None
        assert result["alert"]["level"] == "warning"

    def test_measure_dimension_healthy_no_alert(self):
        engine = QIEngine()
        result = engine.measure_dimension("code_health", 0.8)
        assert result["alert"] is None

    def test_measure_dimension_unknown_dimension(self):
        engine = QIEngine()
        result = engine.measure_dimension("custom_dim", 0.75)
        assert result["dimension"] == "custom_dim"
        assert "custom_dim" in engine.quality_scores


class TestQIEngineIndexComputation:
    """Tests for compute_quality_index method."""

    def test_compute_quality_index_all_healthy(self):
        engine = QIEngine()
        for dim in DIMENSIONS:
            engine.measure_dimension(dim, 0.9)
        result = engine.compute_quality_index()
        assert result["overall_index"] == pytest.approx(0.9, abs=0.01)
        assert result["level"] == "healthy"

    def test_compute_quality_index_mixed(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 1.0)
        engine.measure_dimension("test_coverage", 0.0)
        # Only two dimensions have measurements
        result = engine.compute_quality_index()
        # (1.0 + 0.0 + 0 + 0 + 0 + 0) / 6 = 0.166...
        assert result["overall_index"] == pytest.approx(0.1667, abs=0.01)
        assert result["level"] == "critical"

    def test_compute_quality_index_weighted(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 0.5, weight=1.0)
        engine.measure_dimension("code_health", 1.0, weight=3.0)
        result = engine.compute_quality_index()
        # code_health avg = (0.5*1 + 1.0*3) / 4 = 3.5/4 = 0.875
        # others = 0, so overall = 0.875 / 6 = 0.1458
        assert result["dimension_scores"]["code_health"] == pytest.approx(0.875, abs=0.01)

    def test_compute_quality_index_empty(self):
        engine = QIEngine()
        result = engine.compute_quality_index()
        assert result["overall_index"] == 0.0
        assert result["level"] == "critical"

    def test_compute_quality_index_warning_level(self):
        engine = QIEngine()
        for dim in DIMENSIONS:
            engine.measure_dimension(dim, 0.6)
        result = engine.compute_quality_index()
        assert result["overall_index"] == pytest.approx(0.6, abs=0.01)
        assert result["level"] == "warning"


class TestQIEngineDegradation:
    """Tests for detect_degradation method."""

    def test_detect_degradation_no_history(self):
        engine = QIEngine()
        result = engine.detect_degradation()
        assert result["has_degradation"] is False
        assert result["degraded_count"] == 0

    def test_detect_degradation_single_measurement(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 0.8)
        result = engine.detect_degradation()
        assert result["has_degradation"] is False

    def test_detect_degradation_detected(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 1.0)
        engine.measure_dimension("code_health", 0.8)  # 0.8 < 1.0 * 0.9 = 0.9
        result = engine.detect_degradation()
        assert result["has_degradation"] is True
        assert result["degraded_count"] == 1
        assert result["degraded_dimensions"][0]["dimension"] == "code_health"

    def test_detect_degradation_not_detected(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 1.0)
        engine.measure_dimension("code_health", 0.95)  # 0.95 >= 1.0 * 0.9 = 0.9
        result = engine.detect_degradation()
        assert result["has_degradation"] is False

    def test_detect_degradation_multiple_dimensions(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 1.0)
        engine.measure_dimension("test_coverage", 1.0)
        engine.measure_dimension("code_health", 0.5)  # degraded
        engine.measure_dimension("test_coverage", 0.95)  # not degraded
        result = engine.detect_degradation()
        assert result["has_degradation"] is True
        assert result["degraded_count"] == 1
        assert result["degraded_dimensions"][0]["dimension"] == "code_health"

    def test_detect_degradation_with_zero_previous(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 0.0)
        engine.measure_dimension("code_health", 0.0)
        result = engine.detect_degradation()
        # 0.0 < 0.0 * 0.9 = 0.0 is False, so no degradation
        assert result["has_degradation"] is False


class TestQIEngineReportGeneration:
    """Tests for generate_quality_report method."""

    def test_generate_quality_report_structure(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 0.85)
        engine.measure_dimension("test_coverage", 0.75)
        report = engine.generate_quality_report()
        assert "overall_index" in report
        assert "level" in report
        assert "dimension_scores" in report
        assert "degradation" in report
        assert "alerts" in report
        assert "dimensions_tracked" in report
        assert "thresholds" in report

    def test_generate_quality_report_with_alerts(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 0.4)
        engine.measure_dimension("test_coverage", 0.6)
        report = engine.generate_quality_report()
        assert report["alerts"]["critical_count"] == 1
        assert report["alerts"]["warning_count"] == 1
        assert report["alerts"]["total_count"] == 2

    def test_generate_quality_report_no_alerts(self):
        engine = QIEngine()
        for dim in DIMENSIONS:
            engine.measure_dimension(dim, 0.85)
        report = engine.generate_quality_report()
        assert report["alerts"]["total_count"] == 0
        assert report["level"] == "healthy"

    def test_generate_quality_report_with_degradation(self):
        engine = QIEngine()
        engine.measure_dimension("performance", 1.0)
        engine.measure_dimension("performance", 0.5)
        report = engine.generate_quality_report()
        assert report["degradation"]["has_degradation"] is True
        assert report["degradation"]["degraded_count"] == 1


class TestQIEngineStatus:
    """Tests for get_status method."""

    def test_get_status_basic(self):
        engine = QIEngine()
        engine.measure_dimension("code_health", 0.8)
        status = engine.get_status()
        assert "quality_index" in status
        assert "level" in status
        assert "alert_count" in status
        assert "dimensions_tracked" in status
        assert "dimension_names" in status
        assert status["dimensions_tracked"] == len(DIMENSIONS)

    def test_get_status_with_alerts(self):
        engine = QIEngine()
        engine.measure_dimension("security", 0.3)
        status = engine.get_status()
        assert status["alert_count"] == 1
        assert status["level"] == "critical"


class TestQIEngineSingleton:
    """Tests for the global singleton get_qi_engine."""

    def test_singleton_returns_same_instance(self):
        engine1 = get_qi_engine()
        engine2 = get_qi_engine()
        assert engine1 is engine2

    def test_singleton_is_qiengine_instance(self):
        engine = get_qi_engine()
        assert isinstance(engine, QIEngine)

    def test_singleton_state_persists(self):
        engine = get_qi_engine()
        engine.measure_dimension("code_health", 0.99)
        engine2 = get_qi_engine()
        assert "code_health" in engine2.quality_scores
        assert len(engine2.quality_scores["code_health"]) > 0


class TestQIEngineDefensive:
    """Defensive programming tests."""

    def test_measure_dimension_string_score(self):
        engine = QIEngine()
        result = engine.measure_dimension("code_health", "0.75")
        assert result["score"] == 0.75

    def test_measure_dimension_large_weight(self):
        engine = QIEngine()
        result = engine.measure_dimension("code_health", 0.5, weight=1000.0)
        assert result["weight"] == 1000.0

    def test_all_dimensions_tracked(self):
        engine = QIEngine()
        for dim in DIMENSIONS:
            assert dim in engine.quality_scores

    def test_default_thresholds(self):
        engine = QIEngine()
        for dim in DIMENSIONS:
            assert engine.thresholds[dim] == 0.7
