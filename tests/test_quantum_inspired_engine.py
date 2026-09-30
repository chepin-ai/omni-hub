"""
Tests for OMNI-HUB v173: Quantum-Inspired Engine
"""

import math
import sys
from typing import Dict, List

sys.path.insert(0, "core")

import pytest

from quantum_inspired_engine import (
    QuantumInspiredEngine,
    get_quantum_inspired_engine,
    _normalize,
    _feature_map_zz,
    _feature_map_z,
    _feature_map_rbf_quantum,
    ADVANTAGE_LEVELS,
    FEATURE_MAPS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def engine() -> QuantumInspiredEngine:
    return QuantumInspiredEngine()


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    import quantum_inspired_engine as qie
    qie._module = None
    yield
    qie._module = None


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------
class TestHelpers:
    def test_normalize_basic(self):
        amps = [1.0, 1.0, 1.0]
        norm = _normalize(amps)
        assert len(norm) == 3
        assert abs(sum(a ** 2 for a in norm) - 1.0) < 1e-6

    def test_normalize_zero(self):
        amps = [0.0, 0.0]
        norm = _normalize(amps)
        assert all(abs(a - 0.5) < 1e-6 for a in norm)

    def test_feature_map_zz(self):
        x = [0.1, 0.2]
        mapped = _feature_map_zz(x, reps=2)
        assert len(mapped) > 0
        assert all(isinstance(v, float) for v in mapped)

    def test_feature_map_z(self):
        x = [0.1, 0.2]
        mapped = _feature_map_z(x, reps=2)
        assert len(mapped) > 0
        assert all(isinstance(v, float) for v in mapped)

    def test_feature_map_rbf_quantum(self):
        x = [0.1, 0.2, 0.3]
        mapped = _feature_map_rbf_quantum(x, gamma=1.0)
        assert len(mapped) == 3
        assert all(0.0 < v <= 1.0 for v in mapped)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_returns_same_instance(self):
        a = get_quantum_inspired_engine()
        b = get_quantum_inspired_engine()
        assert a is b

    def test_singleton_is_initialized(self):
        eng = get_quantum_inspired_engine()
        assert isinstance(eng, QuantumInspiredEngine)


# ---------------------------------------------------------------------------
# Superposition
# ---------------------------------------------------------------------------
class TestSuperposition:
    def test_create_superposition_embedding(self, engine: QuantumInspiredEngine):
        base = [
            {"label": "A", "value": 1},
            {"label": "B", "value": 2},
            {"label": "C", "value": 3},
        ]
        amps = [0.5, 0.5, 0.5]
        result = engine.create_superposition_embedding(base, amps)

        assert "state_id" in result
        assert result["created"] is True
        assert len(result["amplitudes"]) == 3
        assert len(result["interference"]) == 3  # C(3,2)
        assert abs(sum(a ** 2 for a in result["amplitudes"]) - 1.0) < 1e-6

    def test_create_superposition_mismatched_lengths(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.create_superposition_embedding([{"a": 1}], [0.5, 0.5])

    def test_create_superposition_empty(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.create_superposition_embedding([], [])

    def test_measure_superposition(self, engine: QuantumInspiredEngine):
        base = [
            {"label": "A", "value": 1},
            {"label": "B", "value": 2},
        ]
        amps = [1.0, 0.0]  # deterministic collapse to A
        state = engine.create_superposition_embedding(base, amps)
        result = engine.measure_superposition(state["state_id"], basis="computational")

        assert result["basis"] == "computational"
        assert result["collapsed_state"]["label"] == "A"
        assert result["probability"] == 1.0

    def test_measure_superposition_unknown_id(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.measure_superposition("nonexistent-id")

    def test_measure_probabilistic(self, engine: QuantumInspiredEngine):
        base = [
            {"label": "A", "value": 1},
            {"label": "B", "value": 2},
        ]
        amps = [1.0 / math.sqrt(2), 1.0 / math.sqrt(2)]
        state = engine.create_superposition_embedding(base, amps)
        # Run many times to verify probabilistic nature
        counts = {"A": 0, "B": 0}
        for _ in range(200):
            result = engine.measure_superposition(state["state_id"])
            counts[result["collapsed_state"]["label"]] += 1
        # Both should appear roughly equally (with tolerance)
        assert counts["A"] > 50
        assert counts["B"] > 50


# ---------------------------------------------------------------------------
# Tensor Network Compression
# ---------------------------------------------------------------------------
class TestTensorCompression:
    def test_apply_tensor_network_compression(self, engine: QuantumInspiredEngine):
        data = [float(i) for i in range(64)]
        result = engine.apply_tensor_network_compression(data, bond_dimension=4)

        assert result["original_size"] == 64
        assert result["bond_dimension"] <= 4
        assert result["compression_ratio"] > 0
        assert result["mse"] >= 0
        assert "tensors" in result
        assert "U" in result["tensors"]
        assert "S" in result["tensors"]
        assert "V_T" in result["tensors"]

    def test_compression_low_bond_dimension(self, engine: QuantumInspiredEngine):
        data = [float(i) for i in range(100)]
        result = engine.apply_tensor_network_compression(data, bond_dimension=2)
        assert result["bond_dimension"] <= 2

    def test_compression_empty_data(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.apply_tensor_network_compression([], bond_dimension=2)

    def test_compression_invalid_bond(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.apply_tensor_network_compression([1.0, 2.0], bond_dimension=0)

    def test_compression_small_data(self, engine: QuantumInspiredEngine):
        data = [1.0, 2.0, 3.0, 4.0]
        result = engine.apply_tensor_network_compression(data, bond_dimension=10)
        assert result["original_size"] == 4


# ---------------------------------------------------------------------------
# Quantum-behaved PSO
# ---------------------------------------------------------------------------
class TestQPSO:
    def test_run_quantum_pso_sphere(self, engine: QuantumInspiredEngine):
        def sphere(x: List[float]) -> float:
            return sum(v ** 2 for v in x)

        result = engine.run_quantum_pso(
            objective_fn=sphere,
            n_particles=20,
            dim=5,
            iterations=50,
            bounds=([-5.0] * 5, [5.0] * 5),
        )

        assert "best_position" in result
        assert "best_fitness" in result
        assert len(result["best_position"]) == 5
        assert result["best_fitness"] >= 0
        # Should be close to optimum at origin
        assert result["best_fitness"] < 1.0
        assert len(result["convergence_history"]) == 51  # iterations + initial

    def test_run_quantum_pso_no_bounds(self, engine: QuantumInspiredEngine):
        def simple(x: List[float]) -> float:
            return (x[0] - 3.0) ** 2

        result = engine.run_quantum_pso(
            objective_fn=simple,
            n_particles=10,
            dim=1,
            iterations=30,
        )
        assert result["best_fitness"] < 1.0

    def test_run_quantum_pso_invalid_params(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.run_quantum_pso(lambda x: 0.0, n_particles=0, dim=2, iterations=10)
        with pytest.raises(ValueError):
            engine.run_quantum_pso(lambda x: 0.0, n_particles=5, dim=0, iterations=10)
        with pytest.raises(ValueError):
            engine.run_quantum_pso(lambda x: 0.0, n_particles=5, dim=2, iterations=0)

    def test_qpso_convergence_improves(self, engine: QuantumInspiredEngine):
        def rastrigin(x: List[float]) -> float:
            A = 10.0
            return A * len(x) + sum(v ** 2 - A * math.cos(2 * math.pi * v) for v in x)

        result = engine.run_quantum_pso(
            objective_fn=rastrigin,
            n_particles=30,
            dim=2,
            iterations=50,
            bounds=([-5.12] * 2, [5.12] * 2),
        )
        # Final should be <= initial
        assert result["convergence_history"][-1] <= result["convergence_history"][0]


# ---------------------------------------------------------------------------
# Quantum Kernel
# ---------------------------------------------------------------------------
class TestQuantumKernel:
    def test_compute_quantum_kernel_zz(self, engine: QuantumInspiredEngine):
        X = [[0.0, 0.0], [1.0, 1.0]]
        Y = [[0.0, 0.0], [1.0, 1.0]]
        K = engine.compute_quantum_kernel(X, Y, feature_map="zz")

        assert len(K) == 2
        assert len(K[0]) == 2
        # Diagonal should be 1 (self-similarity)
        assert abs(K[0][0] - 1.0) < 1e-6
        assert abs(K[1][1] - 1.0) < 1e-6
        # All values in [0, 1]
        for row in K:
            for v in row:
                assert 0.0 <= v <= 1.0

    def test_compute_quantum_kernel_z(self, engine: QuantumInspiredEngine):
        X = [[0.0], [1.0]]
        Y = [[0.0], [1.0]]
        K = engine.compute_quantum_kernel(X, Y, feature_map="z")

        assert len(K) == 2
        assert len(K[0]) == 2
        assert abs(K[0][0] - 1.0) < 1e-6
        assert abs(K[1][1] - 1.0) < 1e-6

    def test_compute_quantum_kernel_rbf(self, engine: QuantumInspiredEngine):
        X = [[0.0, 0.0], [1.0, 1.0]]
        Y = [[0.0, 0.0], [1.0, 1.0]]
        K = engine.compute_quantum_kernel(X, Y, feature_map="rbf_quantum")

        assert len(K) == 2
        assert len(K[0]) == 2
        assert abs(K[0][0] - 1.0) < 1e-6
        assert abs(K[1][1] - 1.0) < 1e-6

    def test_compute_quantum_kernel_invalid_map(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.compute_quantum_kernel([[0.0]], [[0.0]], feature_map="invalid")

    def test_compute_quantum_kernel_empty(self, engine: QuantumInspiredEngine):
        with pytest.raises(ValueError):
            engine.compute_quantum_kernel([], [[0.0]], feature_map="zz")
        with pytest.raises(ValueError):
            engine.compute_quantum_kernel([[0.0]], [], feature_map="zz")

    def test_kernel_computation_count(self, engine: QuantumInspiredEngine):
        assert engine.kernel_computations == 0
        engine.compute_quantum_kernel([[0.0]], [[0.0]], feature_map="zz")
        assert engine.kernel_computations == 1
        engine.compute_quantum_kernel([[0.0]], [[0.0]], feature_map="z")
        assert engine.kernel_computations == 2


# ---------------------------------------------------------------------------
# Quantum Advantage Detection
# ---------------------------------------------------------------------------
class TestQuantumAdvantage:
    def test_detect_quantum_supremacy(self, engine: QuantumInspiredEngine):
        # composite > 100 requires product > 100^4 = 100_000_000
        classical = {"time": 10000.0, "accuracy": 0.5, "params": 100000, "correlation": 0.2}
        quantum = {"time": 1.0, "accuracy": 0.99, "params": 10, "correlation": 0.95}
        result = engine.detect_quantum_advantage(classical, quantum)

        assert result["speedup"] == 10000.0
        assert result["accuracy_gain"] == pytest.approx(1.98)
        assert result["parameter_reduction"] == 10000.0
        assert result["correlation_capture"] == pytest.approx(4.75)
        assert result["advantage_level"] == "quantum_supremacy"

    def test_detect_quantum_advantage(self, engine: QuantumInspiredEngine):
        # composite > 10 requires product > 10_000
        classical = {"time": 500.0, "accuracy": 0.8, "params": 5000, "correlation": 0.4}
        quantum = {"time": 1.0, "accuracy": 0.95, "params": 50, "correlation": 0.8}
        result = engine.detect_quantum_advantage(classical, quantum)

        assert result["advantage_level"] == "quantum_advantage"

    def test_detect_quantum_speedup(self, engine: QuantumInspiredEngine):
        classical = {"time": 10.0, "accuracy": 0.8, "params": 100, "correlation": 0.5}
        quantum = {"time": 1.0, "accuracy": 0.85, "params": 50, "correlation": 0.6}
        result = engine.detect_quantum_advantage(classical, quantum)

        assert result["advantage_level"] == "quantum_speedup"

    def test_detect_equivalent(self, engine: QuantumInspiredEngine):
        classical = {"time": 1.0, "accuracy": 0.8, "params": 100, "correlation": 0.5}
        quantum = {"time": 1.0, "accuracy": 0.8, "params": 100, "correlation": 0.5}
        result = engine.detect_quantum_advantage(classical, quantum)

        assert result["advantage_level"] == "equivalent"

    def test_detect_classical_better(self, engine: QuantumInspiredEngine):
        classical = {"time": 1.0, "accuracy": 0.9, "params": 100, "correlation": 0.8}
        quantum = {"time": 10.0, "accuracy": 0.5, "params": 1000, "correlation": 0.2}
        result = engine.detect_quantum_advantage(classical, quantum)

        assert result["advantage_level"] == "classical_better"

    def test_detect_advantage_levels_in_constants(self):
        for level in ADVANTAGE_LEVELS:
            assert level in [
                "classical_better",
                "equivalent",
                "quantum_speedup",
                "quantum_advantage",
                "quantum_supremacy",
            ]


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
class TestStatus:
    def test_get_status_initial(self, engine: QuantumInspiredEngine):
        status = engine.get_status()
        assert status["superposition_count"] == 0
        assert status["compression_ratio"] == 0.0
        assert status["pso_runs"] == 0
        assert status["kernel_computations"] == 0
        assert status["superposition_states"] == 0
        assert status["tensor_networks"] == 0
        assert status["optimizer_best_fitness"] == float("inf")

    def test_get_status_after_operations(self, engine: QuantumInspiredEngine):
        engine.create_superposition_embedding([{"a": 1}], [1.0])
        engine.apply_tensor_network_compression([1.0, 2.0, 3.0, 4.0], bond_dimension=2)
        engine.run_quantum_pso(lambda x: sum(v ** 2 for v in x), 5, 2, 5)
        engine.compute_quantum_kernel([[0.0]], [[0.0]], feature_map="zz")

        status = engine.get_status()
        assert status["superposition_count"] == 1
        assert status["pso_runs"] == 1
        assert status["kernel_computations"] == 1
        assert status["superposition_states"] == 1
        assert status["tensor_networks"] == 1
        assert status["compression_ratio"] > 0
        assert status["optimizer_best_fitness"] < float("inf")


# ---------------------------------------------------------------------------
# Integration / End-to-End
# ---------------------------------------------------------------------------
class TestIntegration:
    def test_full_pipeline(self):
        """Test the complete quantum-inspired pipeline end-to-end."""
        eng = QuantumInspiredEngine()

        # 1. Create superposition
        states = [
            {"feature": [1.0, 0.0, 0.0]},
            {"feature": [0.0, 1.0, 0.0]},
            {"feature": [0.0, 0.0, 1.0]},
        ]
        superposition = eng.create_superposition_embedding(states, [1.0, 1.0, 1.0])
        assert superposition["state_id"] is not None

        # 2. Measure it
        measurement = eng.measure_superposition(superposition["state_id"])
        assert measurement["collapsed_state"] in states

        # 3. Compress some data
        data = [math.sin(i * 0.1) for i in range(100)]
        compressed = eng.apply_tensor_network_compression(data, bond_dimension=4)
        assert compressed["compression_ratio"] > 0

        # 4. Run QPSO
        def objective(x: List[float]) -> float:
            return (x[0] - 2.0) ** 2 + (x[1] + 1.0) ** 2

        qpso_result = eng.run_quantum_pso(
            objective_fn=objective,
            n_particles=15,
            dim=2,
            iterations=40,
            bounds=([-5.0, -5.0], [5.0, 5.0]),
        )
        assert qpso_result["best_fitness"] < 0.5

        # 5. Compute kernel
        X = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
        K = eng.compute_quantum_kernel(X, X, feature_map="zz")
        assert len(K) == 3
        assert all(abs(K[i][i] - 1.0) < 1e-6 for i in range(3))

        # 6. Detect advantage
        classical = {"time": 100.0, "accuracy": 0.7, "params": 10000, "correlation": 0.4}
        quantum = {"time": 5.0, "accuracy": 0.85, "params": 500, "correlation": 0.75}
        adv = eng.detect_quantum_advantage(classical, quantum)
        assert adv["advantage_level"] in ADVANTAGE_LEVELS

        # 7. Status
        status = eng.get_status()
        assert status["superposition_count"] >= 1
        assert status["pso_runs"] >= 1
        assert status["kernel_computations"] >= 1
