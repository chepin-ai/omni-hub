"""
Tests for ConsciousnessMetricEngine (OMNI-HUB Module v171)
"""

import math
import pytest
from typing import Any, Dict, List

from core.consciousness_metric_engine import (
    ConsciousnessMetricEngine,
    get_consciousness_metric_engine,
    _clamp,
    _z_score,
    _compute_d_prime,
    _kl_divergence,
    _normalize,
    _causal_density,
    _integration_index,
    _consciousness_state_label,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> ConsciousnessMetricEngine:
    """Fresh engine instance for each test."""
    return ConsciousnessMetricEngine()


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the global singleton before each test."""
    import core.consciousness_metric_engine as mod
    mod._module = None


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_clamp(self) -> None:
        assert _clamp(0.5) == 0.5
        assert _clamp(-1.0) == 0.0
        assert _clamp(2.0) == 1.0
        assert _clamp(0.5, low=0.2, high=0.8) == 0.5
        assert _clamp(0.1, low=0.2, high=0.8) == 0.2
        assert _clamp(0.9, low=0.2, high=0.8) == 0.8

    def test_z_score_symmetry(self) -> None:
        assert abs(_z_score(0.5)) < 0.01
        assert abs(_z_score(0.8413) - 1.0) < 0.05
        assert abs(_z_score(0.1587) + 1.0) < 0.05

    def test_compute_d_prime(self) -> None:
        # Perfect discrimination
        d = _compute_d_prime(100, 0, 0, 100)
        assert d > 3.0
        # Chance performance
        d = _compute_d_prime(50, 50, 50, 50)
        assert abs(d) < 0.1

    def test_kl_divergence(self) -> None:
        p = [0.5, 0.5]
        q = [0.5, 0.5]
        assert _kl_divergence(p, q) == pytest.approx(0.0, abs=1e-6)
        p = [1.0, 0.0]
        q = [0.5, 0.5]
        assert _kl_divergence(p, q) > 0.0

    def test_normalize(self) -> None:
        v = [1.0, 2.0, 3.0]
        n = _normalize(v)
        assert sum(n) == pytest.approx(1.0)
        assert n == pytest.approx([1 / 6, 2 / 6, 3 / 6])

    def test_causal_density(self) -> None:
        m = [[0.0, 0.5], [0.5, 0.0]]
        assert _causal_density(m) == pytest.approx(0.5)
        assert _causal_density([]) == 0.0
        assert _causal_density([[1.0]]) == 0.0

    def test_integration_index(self) -> None:
        m = [[0.0, 0.8, 0.8], [0.8, 0.0, 0.8], [0.8, 0.8, 0.0]]
        idx = _integration_index(m)
        assert 0.0 <= idx <= 1.0
        assert _integration_index([]) == 0.0

    def test_consciousness_state_label(self) -> None:
        assert _consciousness_state_label(0.95) == "lucid"
        assert _consciousness_state_label(0.8) == "aware"
        assert _consciousness_state_label(0.65) == "attentive"
        assert _consciousness_state_label(0.45) == "drowsy"
        assert _consciousness_state_label(0.2) == "unconscious"


# ---------------------------------------------------------------------------
# Engine method tests
# ---------------------------------------------------------------------------

class TestBroadcastScore:
    def test_empty_workspace(self, engine: ConsciousnessMetricEngine) -> None:
        ws: Dict[str, Any] = {"contents": [], "consumers": {}, "broadcast_log": []}
        result = engine.compute_broadcast_score(ws)
        assert result["metric"] == "broadcast_score"
        assert 0.0 <= result["value"] <= 1.0
        assert "factors" in result

    def test_full_workspace(self, engine: ConsciousnessMetricEngine) -> None:
        ws: Dict[str, Any] = {
            "contents": [
                {"id": "a"},
                {"id": "b"},
                {"id": "c"},
                {"id": "d"},
                {"id": "e"},
                {"id": "f"},
            ],
            "consumers": {
                "a": ["c1", "c2", "c3"],
                "b": ["c1", "c2", "c3"],
                "c": ["c1", "c2", "c3"],
                "d": ["c1", "c2", "c3"],
                "e": ["c1", "c2", "c3"],
                "f": ["c1", "c2", "c3"],
            },
            "broadcast_log": ["e1", "e2", "e3", "e4", "e5"],
        }
        result = engine.compute_broadcast_score(ws)
        assert result["value"] > 0.5
        factors = result["factors"]
        assert factors["content_score"] > 0.9
        assert factors["consumer_overlap"] > 0.5


class TestSelectivityIndex:
    def test_no_inputs(self, engine: ConsciousnessMetricEngine) -> None:
        result = engine.compute_selectivity_index([], [])
        assert result["metric"] == "selectivity_index"
        assert result["value"] == 0.0

    def test_ideal_selectivity(self, engine: ConsciousnessMetricEngine) -> None:
        inputs = list(range(10))
        selected = list(range(3))  # 30% selected
        result = engine.compute_selectivity_index(inputs, selected)
        assert result["value"] == pytest.approx(1.0)
        assert result["ratio"] == 0.3

    def test_too_high_selectivity(self, engine: ConsciousnessMetricEngine) -> None:
        inputs = list(range(10))
        selected = list(range(8))  # 80% selected
        result = engine.compute_selectivity_index(inputs, selected)
        assert result["value"] < 1.0
        assert result["ratio"] == 0.8


class TestMetaDPrime:
    def test_too_few_samples(self, engine: ConsciousnessMetricEngine) -> None:
        result = engine.compute_meta_d_prime([0.5, 0.6], [1, 0])
        assert result["metric"] == "meta_d_prime"
        assert result["value"] == 0.0

    def test_perfect_metacognition(self, engine: ConsciousnessMetricEngine) -> None:
        # High confidence when correct, low when incorrect
        confidence = [0.9, 0.8, 0.85, 0.1, 0.15, 0.2, 0.88, 0.12]
        accuracy = [1, 1, 1, 0, 0, 0, 1, 0]
        result = engine.compute_meta_d_prime(confidence, accuracy)
        assert result["meta_d"] > 1.0
        assert result["value"] > 0.3

    def test_chance_metacognition(self, engine: ConsciousnessMetricEngine) -> None:
        # Random confidence
        confidence = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        accuracy = [1, 0, 1, 0, 1, 0, 1, 0]
        result = engine.compute_meta_d_prime(confidence, accuracy)
        assert result["value"] < 0.2


class TestFreeEnergy:
    def test_identical_distributions(self, engine: ConsciousnessMetricEngine) -> None:
        predicted: Dict[str, Any] = {"distribution": [0.25, 0.25, 0.25, 0.25]}
        actual: Dict[str, Any] = {"distribution": [0.25, 0.25, 0.25, 0.25]}
        result = engine.compute_free_energy(predicted, actual)
        assert result["metric"] == "free_energy"
        assert result["kl_divergence"] == pytest.approx(0.0, abs=1e-5)
        assert result["value"] == pytest.approx(1.0, abs=1e-5)

    def test_different_distributions(self, engine: ConsciousnessMetricEngine) -> None:
        predicted: Dict[str, Any] = {"distribution": [0.9, 0.05, 0.03, 0.02]}
        actual: Dict[str, Any] = {"distribution": [0.1, 0.3, 0.3, 0.3]}
        result = engine.compute_free_energy(predicted, actual)
        assert result["kl_divergence"] > 0.5
        assert result["value"] < 1.0

    def test_empty_distributions(self, engine: ConsciousnessMetricEngine) -> None:
        result = engine.compute_free_energy({}, {})
        assert result["value"] == 0.0
        assert result["kl_divergence"] == 0.0


class TestPhiStructure:
    def test_empty_matrix(self, engine: ConsciousnessMetricEngine) -> None:
        result = engine.compute_phi_structure([])
        assert result["metric"] == "phi_structure"
        assert result["value"] == 0.0

    def test_single_node(self, engine: ConsciousnessMetricEngine) -> None:
        result = engine.compute_phi_structure([[1.0]])
        assert result["value"] == 0.0
        assert result["node_count"] == 1

    def test_fully_connected(self, engine: ConsciousnessMetricEngine) -> None:
        m = [
            [0.0, 0.8, 0.8],
            [0.8, 0.0, 0.8],
            [0.8, 0.8, 0.0],
        ]
        result = engine.compute_phi_structure(m)
        assert result["value"] > 0.0
        assert result["causal_density"] == pytest.approx(0.8)
        assert result["integration"] > 0.0

    def test_nonsquare_matrix(self, engine: ConsciousnessMetricEngine) -> None:
        m = [[0.0, 0.5], [0.3, 0.2, 0.1]]
        result = engine.compute_phi_structure(m)
        assert result["value"] == 0.0


class TestSnapshot:
    def test_empty_snapshot(self, engine: ConsciousnessMetricEngine) -> None:
        result = engine.take_consciousness_snapshot()
        assert result["composite_score"] == 0.0
        assert result["state"] == "unconscious"
        assert "timestamp" in result

    def test_full_snapshot(self, engine: ConsciousnessMetricEngine) -> None:
        # Populate current_reading
        engine.current_reading = {
            "broadcast_score": {"value": 0.9},
            "selectivity_index": {"value": 0.8},
            "meta_d_prime": {"value": 0.7},
            "free_energy": {"value": 0.85},
            "phi_structure": {"value": 0.6},
        }
        result = engine.take_consciousness_snapshot()
        assert result["composite_score"] > 0.0
        assert result["state"] in ("lucid", "aware", "attentive", "drowsy", "unconscious")
        assert len(engine.metrics_history) == 1
        assert engine.baseline_established

    def test_baseline_established(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "broadcast_score": {"value": 0.5},
            "selectivity_index": {"value": 0.5},
            "meta_d_prime": {"value": 0.5},
            "free_energy": {"value": 0.5},
            "phi_structure": {"value": 0.5},
        }
        engine.take_consciousness_snapshot()
        assert engine.baseline == {
            "broadcast_score": 0.5,
            "selectivity_index": 0.5,
            "meta_d_prime": 0.5,
            "free_energy": 0.5,
            "phi_structure": 0.5,
        }


class TestAnomalyDetection:
    def test_no_baseline(self, engine: ConsciousnessMetricEngine) -> None:
        result = engine.detect_consciousness_anomaly()
        assert result["anomaly_detected"] is False
        assert result["severity"] == "none"

    def test_broadcast_failure(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "broadcast_score": {"value": 0.1},
        }
        engine.baseline = {"broadcast_score": 0.8}
        engine.baseline_established = True
        result = engine.detect_consciousness_anomaly()
        assert result["anomaly_detected"] is True
        assert any(a["type"] == "broadcast_failure" for a in result["anomalies"])
        assert result["severity"] == "critical"

    def test_phi_collapse(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "phi_structure": {"value": 0.05},
            "broadcast_score": {"value": 0.9},
        }
        engine.baseline = {"phi_structure": 0.8, "broadcast_score": 0.9}
        engine.baseline_established = True
        result = engine.detect_consciousness_anomaly()
        assert result["anomaly_detected"] is True
        assert any(a["type"] == "phi_collapse" for a in result["anomalies"])
        assert any(a["severity"] == "critical" for a in result["anomalies"])

    def test_meta_cognitive_drift(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "meta_d_prime": {"value": 0.1},
            "broadcast_score": {"value": 0.9},
            "phi_structure": {"value": 0.8},
        }
        engine.baseline = {"meta_d_prime": 0.8, "broadcast_score": 0.9, "phi_structure": 0.8}
        engine.baseline_established = True
        result = engine.detect_consciousness_anomaly()
        assert result["anomaly_detected"] is True
        assert any(a["type"] == "meta_cognitive_drift" for a in result["anomalies"])

    def test_integration_degradation(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "phi_structure": {"value": 0.1},
            "broadcast_score": {"value": 0.9},
            "meta_d_prime": {"value": 0.8},
        }
        engine.baseline = {"phi_structure": 0.8, "broadcast_score": 0.9, "meta_d_prime": 0.8}
        engine.baseline_established = True
        result = engine.detect_consciousness_anomaly()
        assert result["anomaly_detected"] is True
        assert any(a["type"] == "integration_degradation" for a in result["anomalies"])

    def test_free_energy_spike(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "free_energy": {"value": 0.1},
            "broadcast_score": {"value": 0.9},
            "phi_structure": {"value": 0.8},
            "meta_d_prime": {"value": 0.8},
        }
        engine.baseline = {
            "free_energy": 0.9,
            "broadcast_score": 0.9,
            "phi_structure": 0.8,
            "meta_d_prime": 0.8,
        }
        engine.baseline_established = True
        result = engine.detect_consciousness_anomaly()
        assert result["anomaly_detected"] is True
        assert any(a["type"] == "free_energy_spike" for a in result["anomalies"])

    def test_anomaly_count_increment(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {"broadcast_score": {"value": 0.1}}
        engine.baseline = {"broadcast_score": 0.8}
        engine.baseline_established = True
        assert engine.anomaly_count == 0
        engine.detect_consciousness_anomaly()
        assert engine.anomaly_count == 1
        engine.detect_consciousness_anomaly()
        assert engine.anomaly_count == 2


class TestStatus:
    def test_empty_status(self, engine: ConsciousnessMetricEngine) -> None:
        status = engine.get_status()
        assert status["trend"] == "stable"
        assert status["anomaly_count"] == 0
        assert status["baseline_established"] is False

    def test_ascending_trend(self, engine: ConsciousnessMetricEngine) -> None:
        for score in [0.3, 0.4, 0.5, 0.6, 0.7]:
            engine.metrics_history.append({"composite_score": score})
        status = engine.get_status()
        assert status["trend"] == "ascending"

    def test_descending_trend(self, engine: ConsciousnessMetricEngine) -> None:
        for score in [0.7, 0.6, 0.5, 0.4, 0.3]:
            engine.metrics_history.append({"composite_score": score})
        status = engine.get_status()
        assert status["trend"] == "descending"

    def test_stable_trend(self, engine: ConsciousnessMetricEngine) -> None:
        for score in [0.5, 0.51, 0.50, 0.52, 0.51]:
            engine.metrics_history.append({"composite_score": score})
        status = engine.get_status()
        assert status["trend"] == "stable"


class TestSingleton:
    def test_singleton_identity(self) -> None:
        a = get_consciousness_metric_engine()
        b = get_consciousness_metric_engine()
        assert a is b

    def test_singleton_is_engine(self) -> None:
        inst = get_consciousness_metric_engine()
        assert isinstance(inst, ConsciousnessMetricEngine)


class TestComputeAll:
    def test_compute_all_integration(self, engine: ConsciousnessMetricEngine) -> None:
        workspace: Dict[str, Any] = {
            "contents": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "consumers": {"a": ["c1"], "b": ["c1", "c2"], "c": ["c1", "c2", "c3"]},
            "broadcast_log": ["e1", "e2"],
        }
        inputs = list(range(10))
        selected = list(range(3))
        confidence = [0.9, 0.8, 0.85, 0.1, 0.15, 0.2, 0.88, 0.12]
        accuracy = [1, 1, 1, 0, 0, 0, 1, 0]
        predicted: Dict[str, Any] = {"distribution": [0.25, 0.25, 0.25, 0.25]}
        actual: Dict[str, Any] = {"distribution": [0.25, 0.25, 0.25, 0.25]}
        causal_matrix = [
            [0.0, 0.6, 0.6],
            [0.6, 0.0, 0.6],
            [0.6, 0.6, 0.0],
        ]

        result = engine.compute_all(
            workspace, inputs, selected,
            confidence, accuracy,
            predicted, actual,
            causal_matrix,
        )
        assert "snapshot" in result
        assert "anomaly" in result
        assert "status" in result
        snap = result["snapshot"]
        assert "composite_score" in snap
        assert "state" in snap
        assert snap["state"] in ("lucid", "aware", "attentive", "drowsy", "unconscious")


class TestConsciousnessStates:
    def test_lucid_state(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "broadcast_score": {"value": 0.95},
            "selectivity_index": {"value": 0.95},
            "meta_d_prime": {"value": 0.95},
            "free_energy": {"value": 0.95},
            "phi_structure": {"value": 0.95},
        }
        snap = engine.take_consciousness_snapshot()
        assert snap["state"] == "lucid"
        assert snap["composite_score"] > 0.9

    def test_unconscious_state(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "broadcast_score": {"value": 0.1},
            "selectivity_index": {"value": 0.1},
            "meta_d_prime": {"value": 0.1},
            "free_energy": {"value": 0.1},
            "phi_structure": {"value": 0.1},
        }
        snap = engine.take_consciousness_snapshot()
        assert snap["state"] == "unconscious"
        assert snap["composite_score"] < 0.4

    def test_drowsy_state(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "broadcast_score": {"value": 0.45},
            "selectivity_index": {"value": 0.45},
            "meta_d_prime": {"value": 0.45},
            "free_energy": {"value": 0.45},
            "phi_structure": {"value": 0.45},
        }
        snap = engine.take_consciousness_snapshot()
        assert snap["state"] == "drowsy"
        assert 0.4 < snap["composite_score"] <= 0.6

    def test_attentive_state(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "broadcast_score": {"value": 0.65},
            "selectivity_index": {"value": 0.65},
            "meta_d_prime": {"value": 0.65},
            "free_energy": {"value": 0.65},
            "phi_structure": {"value": 0.65},
        }
        snap = engine.take_consciousness_snapshot()
        assert snap["state"] == "attentive"
        assert 0.6 < snap["composite_score"] <= 0.75

    def test_aware_state(self, engine: ConsciousnessMetricEngine) -> None:
        engine.current_reading = {
            "broadcast_score": {"value": 0.8},
            "selectivity_index": {"value": 0.8},
            "meta_d_prime": {"value": 0.8},
            "free_energy": {"value": 0.8},
            "phi_structure": {"value": 0.8},
        }
        snap = engine.take_consciousness_snapshot()
        assert snap["state"] == "aware"
        assert 0.75 < snap["composite_score"] <= 0.9
