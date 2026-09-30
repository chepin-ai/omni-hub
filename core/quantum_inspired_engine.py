"""
OMNI-HUB v173: Quantum-Inspired Engine (量子启发引擎)

Research Basis: Caltech IQIM exponential memory advantage (April 2026)
+ quantum tensor networks + QPSO + quantum kernel methods.

Key Insight: quantum-inspired algorithms on classical hardware can capture
long-range correlations with fewer parameters.

This is NOT simulating a quantum computer, but using quantum mechanical
mathematical principles to enhance classical AI systems.
"""

import math
import random
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ADVANTAGE_LEVELS = [
    "classical_better",
    "equivalent",
    "quantum_speedup",      # > 2x
    "quantum_advantage",    # > 10x
    "quantum_supremacy",    # > 100x
]

FEATURE_MAPS = ["zz", "z", "rbf_quantum"]


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------
_module: Optional["QuantumInspiredEngine"] = None


def get_quantum_inspired_engine() -> "QuantumInspiredEngine":
    """Return the global singleton QuantumInspiredEngine instance."""
    global _module
    if _module is None:
        _module = QuantumInspiredEngine()
    return _module


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _normalize(amplitudes: List[float]) -> List[float]:
    """L2-normalize a list of amplitudes (quantum-style)."""
    norm = math.sqrt(sum(abs(a) ** 2 for a in amplitudes))
    if norm == 0:
        return [1.0 / len(amplitudes)] * len(amplitudes)
    return [a / norm for a in amplitudes]


def _feature_map_zz(x: List[float], reps: int = 2) -> List[float]:
    """ZZFeatureMap analog: ZZ interaction + single-qubit rotations."""
    mapped = []
    for r in range(reps):
        for xi in x:
            mapped.append(math.sin((r + 1) * xi))
            mapped.append(math.cos((r + 1) * xi))
        for i in range(len(x)):
            for j in range(i + 1, len(x)):
                mapped.append(
                    math.cos((r + 1) * (math.pi - x[i]) * (math.pi - x[j]))
                )
    return mapped


def _feature_map_z(x: List[float], reps: int = 2) -> List[float]:
    """ZFeatureMap analog: single-qubit Z rotations."""
    mapped = []
    for r in range(reps):
        for xi in x:
            mapped.append(math.cos((r + 1) * xi))
            mapped.append(math.sin((r + 1) * xi))
    return mapped


def _feature_map_rbf_quantum(x: List[float], gamma: float = 1.0) -> List[float]:
    """RBF-inspired quantum feature map."""
    return [math.exp(-gamma * (xi ** 2)) for xi in x]


def _svd_2d(matrix: List[List[float]]) -> Tuple[List[float], List[List[float]], List[List[float]]]:
    """Simple 2D SVD via power iteration for MPS decomposition."""
    # Flatten to numpy-like but pure-python
    # For robustness in tests we use a simple SVD approximation
    m = len(matrix)
    n = len(matrix[0]) if m > 0 else 0
    if m == 0 or n == 0:
        return [], [[]], [[]]

    # Compute A^T A eigenvalues / vectors via power iteration
    ata = [[sum(matrix[i][k] * matrix[j][k] for k in range(n))
            for j in range(m)] for i in range(m)]

    # Eigenvalues (singular values squared)
    # Use simple diagonal dominance approximation for robustness
    singular_values = []
    u_approx = []
    v_approx = []

    max_rank = min(m, n)
    remaining = [row[:] for row in matrix]

    for _ in range(max_rank):
        # Power iteration on remaining matrix
        vec = [random.random() for _ in range(m)]
        for _ in range(20):
            # Multiply by A A^T  ->  new_vec[i] = sum_k remaining[i][k] * sum_j remaining[j][k] * vec[j]
            new_vec: List[float] = [0.0] * m
            for i in range(m):
                s = 0.0
                for k in range(n):
                    s += remaining[i][k] * sum(remaining[j][k] * vec[j] for j in range(m))
                new_vec[i] = s
            norm = math.sqrt(sum(vv ** 2 for vv in new_vec)) or 1.0
            vec = [vv / norm for vv in new_vec]

        # Compute singular value
        av = [sum(remaining[i][k] * vec[i] for i in range(m)) for k in range(n)]
        sigma = math.sqrt(sum(vv ** 2 for vv in av))
        if sigma < 1e-10:
            break
        singular_values.append(sigma)

        # Right singular vector
        v_vec = [a / sigma for a in av]
        v_approx.append(v_vec)
        u_approx.append(vec)

        # Deflate
        for i in range(m):
            for k in range(n):
                remaining[i][k] -= sigma * vec[i] * v_vec[k]

    if not singular_values:
        return [0.0], [[1.0] + [0.0] * (m - 1)], [[1.0] + [0.0] * (n - 1)]

    # Build U and V^T
    u_mat = [[u_approx[j][i] for j in range(len(u_approx))] for i in range(m)]
    vt_mat = v_approx  # already shape rank x n
    return singular_values, u_mat, vt_mat


# ---------------------------------------------------------------------------
# Event bus stub (integration point)
# ---------------------------------------------------------------------------
class _EventBus:
    """Minimal event-bus stub for OMNI-HUB integration."""

    @staticmethod
    def publish(event: str, payload: Dict[str, Any]) -> None:
        try:
            # In production this would dispatch to real event bus
            pass
        except Exception:
            pass


# ---------------------------------------------------------------------------
# QuantumInspiredEngine
# ---------------------------------------------------------------------------
class QuantumInspiredEngine:
    """
    Quantum-Inspired Engine for classical hardware.

    Implements:
      - superposition-state embeddings
      - tensor-network (MPS) compression
      - quantum-behaved PSO (QPSO)
      - quantum-inspired kernel methods
      - quantum-advantage detection
    """

    def __init__(self) -> None:
        self.superposition_states: Dict[str, Dict[str, Any]] = {}
        self.tensor_networks: Dict[str, Dict[str, Any]] = {}
        self.optimizer_state: Dict[str, Any] = {
            "best_fitness": float("inf"),
            "best_position": None,
            "convergence_history": [],
        }
        # Metrics
        self.superposition_count: int = 0
        self.compression_ratio: float = 0.0
        self.pso_runs: int = 0
        self.kernel_computations: int = 0

    # ------------------------------------------------------------------
    # Superposition
    # ------------------------------------------------------------------
    def create_superposition_embedding(
        self,
        base_states: List[Dict[str, Any]],
        amplitudes: List[float],
    ) -> Dict[str, Any]:
        """
        Create a quantum-inspired superposition of classical states.

        Args:
            base_states: List of classical state dicts.
            amplitudes: Corresponding complex / real amplitudes.

        Returns:
            Dict with state_id, normalized amplitudes, interference pattern.
        """
        if len(base_states) != len(amplitudes):
            raise ValueError("base_states and amplitudes must have same length")
        if not base_states:
            raise ValueError("base_states must not be empty")

        norm_amps = _normalize(amplitudes)

        # Interference pattern: pairwise overlap
        n = len(base_states)
        interference = []
        for i in range(n):
            for j in range(i + 1, n):
                # Simplified overlap = product of amplitudes
                overlap = norm_amps[i] * norm_amps[j]
                interference.append({
                    "pair": (i, j),
                    "overlap": overlap,
                    "phase_diff": 0.0,  # real-only for classical hardware
                })

        state_id = str(uuid.uuid4())
        state = {
            "state_id": state_id,
            "base_states": base_states,
            "amplitudes": norm_amps,
            "interference": interference,
            "created": True,
        }
        self.superposition_states[state_id] = state
        self.superposition_count += 1

        try:
            _EventBus.publish("quantum.superposition.created", {
                "state_id": state_id,
                "n_states": n,
            })
        except Exception:
            pass

        return state

    def measure_superposition(self, state_id: str, basis: str = "computational") -> Dict[str, Any]:
        """
        'Measure' a superposition to probabilistically collapse to a classical state.

        Args:
            state_id: Identifier of the superposition.
            basis: Measurement basis (currently only 'computational').

        Returns:
            Dict with collapsed state, measured_basis, probability.
        """
        if state_id not in self.superposition_states:
            raise ValueError(f"Unknown state_id: {state_id}")

        state = self.superposition_states[state_id]
        amplitudes = state["amplitudes"]
        base_states = state["base_states"]

        # Probabilities = |amplitude|^2
        probs = [abs(a) ** 2 for a in amplitudes]

        # Sample
        r = random.random()
        cumulative = 0.0
        chosen_idx = 0
        for idx, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                chosen_idx = idx
                break

        collapsed = base_states[chosen_idx]
        probability = probs[chosen_idx]

        result = {
            "state_id": state_id,
            "basis": basis,
            "collapsed_state": collapsed,
            "probability": probability,
            "amplitude": amplitudes[chosen_idx],
        }

        try:
            _EventBus.publish("quantum.superposition.measured", {
                "state_id": state_id,
                "chosen_idx": chosen_idx,
                "probability": probability,
            })
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Tensor Network (MPS) Compression
    # ------------------------------------------------------------------
    def apply_tensor_network_compression(
        self,
        data: List[float],
        bond_dimension: int,
    ) -> Dict[str, Any]:
        """
        Compress 1D data using Matrix Product State (MPS) approximation.

        Uses SVD-based truncation to the requested bond dimension.

        Args:
            data: 1D list of floats.
            bond_dimension: Max rank (bond dimension) to keep.

        Returns:
            Dict with compressed tensors, original_size, compressed_size, ratio.
        """
        if not data:
            raise ValueError("data must not be empty")
        if bond_dimension < 1:
            raise ValueError("bond_dimension must be >= 1")

        n = len(data)
        original_size = n

        # Reshape to 2 x (n/2) or closest factors for SVD
        d1 = int(math.sqrt(n))
        while d1 > 1 and n % d1 != 0:
            d1 -= 1
        d2 = n // d1

        # Pad if necessary
        padded = data + [0.0] * (d1 * d2 - n)
        matrix = [padded[i * d2:(i + 1) * d2] for i in range(d1)]

        singular_values, u_mat, vt_mat = _svd_2d(matrix)

        # Truncate
        rank = min(bond_dimension, len(singular_values))
        truncated_s = singular_values[:rank]
        truncated_u = [row[:rank] for row in u_mat]
        truncated_vt = vt_mat[:rank]

        # Reconstruct compressed data for validation
        compressed_data = []
        for i in range(d1):
            row = []
            for j in range(d2):
                val = sum(
                    truncated_u[i][k] * truncated_s[k] * truncated_vt[k][j]
                    for k in range(rank)
                )
                row.append(val)
            compressed_data.extend(row)
        compressed_data = compressed_data[:n]

        # Error
        mse = sum((a - b) ** 2 for a, b in zip(data, compressed_data)) / n

        compressed_size = rank * (d1 + d2 + 1)
        ratio = original_size / max(compressed_size, 1)

        result = {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "bond_dimension": rank,
            "compression_ratio": ratio,
            "mse": mse,
            "singular_values": truncated_s,
            "tensors": {
                "U": truncated_u,
                "S": truncated_s,
                "V_T": truncated_vt,
            },
        }

        tn_id = str(uuid.uuid4())
        self.tensor_networks[tn_id] = result
        self.compression_ratio = ratio

        try:
            _EventBus.publish("quantum.tensor.compressed", {
                "tn_id": tn_id,
                "ratio": ratio,
                "mse": mse,
            })
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Quantum-behaved PSO (QPSO)
    # ------------------------------------------------------------------
    def run_quantum_pso(
        self,
        objective_fn: Callable[[List[float]], float],
        n_particles: int,
        dim: int,
        iterations: int,
        bounds: Optional[Tuple[List[float], List[float]]] = None,
    ) -> Dict[str, Any]:
        """
        Run Quantum-behaved Particle Swarm Optimization (QPSO).

        Particles move in a quantum potential well around the mean best position.
        Global convergence is better than classical PSO due to the quantum
        potential well model.

        Args:
            objective_fn: Function to minimize.
            n_particles: Number of particles.
            dim: Dimensionality of search space.
            iterations: Number of iterations.
            bounds: Optional (lower_bounds, upper_bounds) tuple.

        Returns:
            Dict with best_position, best_fitness, convergence_history.
        """
        if n_particles < 1:
            raise ValueError("n_particles must be >= 1")
        if dim < 1:
            raise ValueError("dim must be >= 1")
        if iterations < 1:
            raise ValueError("iterations must be >= 1")

        # Initialize particles randomly
        if bounds is not None:
            lb, ub = bounds
            particles = [
                [lb[d] + random.random() * (ub[d] - lb[d]) for d in range(dim)]
                for _ in range(n_particles)
            ]
        else:
            particles = [
                [random.uniform(-5.0, 5.0) for _ in range(dim)]
                for _ in range(n_particles)
            ]

        # Personal bests
        pbest_positions = [p[:] for p in particles]
        pbest_fitness = [objective_fn(p) for p in particles]

        # Global best
        gbest_idx = min(range(n_particles), key=lambda i: pbest_fitness[i])
        gbest_position = pbest_positions[gbest_idx][:]
        gbest_fitness = pbest_fitness[gbest_idx]

        convergence_history = [gbest_fitness]

        # QPSO parameters
        alpha = 0.6  # contraction-expansion coefficient

        for it in range(iterations):
            # Decay alpha
            alpha_t = alpha - (alpha - 0.4) * it / iterations

            # Mean best (mbest) across all personal bests
            mbest = [
                sum(pbest_positions[i][d] for i in range(n_particles)) / n_particles
                for d in range(dim)
            ]

            for i in range(n_particles):
                for d in range(dim):
                    # Quantum potential well center between pbest and gbest
                    phi = random.random()
                    p = (phi * pbest_positions[i][d] +
                         (1 - phi) * gbest_position[d])

                    # Quantum motion: double-exponential distribution
                    u = random.random()
                    if random.random() > 0.5:
                        particles[i][d] = p + alpha_t * abs(mbest[d] - particles[i][d]) * math.log(1.0 / u)
                    else:
                        particles[i][d] = p - alpha_t * abs(mbest[d] - particles[i][d]) * math.log(1.0 / u)

                # Boundary check
                if bounds is not None:
                    for d in range(dim):
                        particles[i][d] = max(lb[d], min(ub[d], particles[i][d]))

                # Evaluate
                fitness = objective_fn(particles[i])
                if fitness < pbest_fitness[i]:
                    pbest_fitness[i] = fitness
                    pbest_positions[i] = particles[i][:]
                    if fitness < gbest_fitness:
                        gbest_fitness = fitness
                        gbest_position = particles[i][:]

            convergence_history.append(gbest_fitness)

        self.optimizer_state["best_fitness"] = gbest_fitness
        self.optimizer_state["best_position"] = gbest_position[:]
        self.optimizer_state["convergence_history"] = convergence_history[:]
        self.pso_runs += 1

        result = {
            "best_position": gbest_position,
            "best_fitness": gbest_fitness,
            "convergence_history": convergence_history,
            "iterations": iterations,
            "n_particles": n_particles,
        }

        try:
            _EventBus.publish("quantum.qpso.completed", {
                "best_fitness": gbest_fitness,
                "iterations": iterations,
            })
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Quantum Kernel Methods
    # ------------------------------------------------------------------
    def compute_quantum_kernel(
        self,
        X: List[List[float]],
        Y: List[List[float]],
        feature_map: str = "zz",
    ) -> List[List[float]]:
        """
        Compute quantum-inspired kernel matrix K(x_i, y_j).

        Feature maps:
          - zz: ZZFeatureMap analog (entangling interactions)
          - z:  ZFeatureMap analog (single-qubit rotations)
          - rbf_quantum: RBF-inspired quantum feature map

        Kernel is the squared inner product of mapped features.

        Args:
            X: List of data vectors.
            Y: List of data vectors.
            feature_map: One of 'zz', 'z', 'rbf_quantum'.

        Returns:
            Kernel matrix as 2D list.
        """
        if feature_map not in FEATURE_MAPS:
            raise ValueError(f"Unknown feature_map: {feature_map}. Choose from {FEATURE_MAPS}")
        if not X or not Y:
            raise ValueError("X and Y must not be empty")

        if feature_map == "zz":
            mapper = _feature_map_zz
        elif feature_map == "z":
            mapper = _feature_map_z
        else:
            mapper = _feature_map_rbf_quantum

        # Map features
        X_mapped = [mapper(x) for x in X]
        Y_mapped = [mapper(y) for y in Y]

        # Compute kernel = |<phi(x)|phi(y)>|^2
        kernel = []
        for xm in X_mapped:
            row = []
            for ym in Y_mapped:
                # Ensure same dimension by truncating/padding
                min_len = min(len(xm), len(ym))
                dot = sum(xm[k] * ym[k] for k in range(min_len))
                # Normalize
                norm_x = math.sqrt(sum(v ** 2 for v in xm))
                norm_y = math.sqrt(sum(v ** 2 for v in ym))
                if norm_x > 0 and norm_y > 0:
                    sim = (dot / (norm_x * norm_y)) ** 2
                else:
                    sim = 0.0
                row.append(sim)
            kernel.append(row)

        self.kernel_computations += 1

        try:
            _EventBus.publish("quantum.kernel.computed", {
                "feature_map": feature_map,
                "shape": (len(X), len(Y)),
            })
        except Exception:
            pass

        return kernel

    # ------------------------------------------------------------------
    # Quantum Advantage Detection
    # ------------------------------------------------------------------
    def detect_quantum_advantage(
        self,
        classical_result: Dict[str, Any],
        quantum_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Detect whether the quantum-inspired approach outperforms the classical one.

        Metrics:
          - speedup: classical_time / quantum_time
          - accuracy_gain: quantum_accuracy / classical_accuracy
          - parameter_reduction: classical_params / quantum_params
          - correlation_capture: additional correlation metric

        Advantage levels:
          quantum_supremacy (>100x) · quantum_advantage (>10x) ·
          quantum_speedup (>2x) · equivalent · classical_better

        Args:
            classical_result: Dict with keys time, accuracy, params, correlation.
            quantum_result: Dict with keys time, accuracy, params, correlation.

        Returns:
            Dict with advantage metrics and overall level.
        """
        def _get(key: str, default: float = 1.0) -> Tuple[float, float]:
            c = classical_result.get(key, default)
            q = quantum_result.get(key, default)
            return float(c), float(q)

        c_time, q_time = _get("time", 1.0)
        c_acc, q_acc = _get("accuracy", 1.0)
        c_params, q_params = _get("params", 1.0)
        c_corr, q_corr = _get("correlation", 1.0)

        speedup = c_time / max(q_time, 1e-12)
        accuracy_gain = q_acc / max(c_acc, 1e-12)
        parameter_reduction = c_params / max(q_params, 1e-12)
        correlation_capture = q_corr / max(c_corr, 1e-12)

        # Composite score: geometric mean of all metrics
        composite = (speedup * accuracy_gain * parameter_reduction * correlation_capture) ** 0.25

        if composite > 100:
            level = "quantum_supremacy"
        elif composite > 10:
            level = "quantum_advantage"
        elif composite > 2:
            level = "quantum_speedup"
        elif composite >= 0.5:
            level = "equivalent"
        else:
            level = "classical_better"

        result = {
            "speedup": speedup,
            "accuracy_gain": accuracy_gain,
            "parameter_reduction": parameter_reduction,
            "correlation_capture": correlation_capture,
            "composite_score": composite,
            "advantage_level": level,
        }

        try:
            _EventBus.publish("quantum.advantage.detected", {
                "level": level,
                "composite_score": composite,
            })
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """Return current engine status."""
        return {
            "superposition_count": self.superposition_count,
            "compression_ratio": self.compression_ratio,
            "pso_runs": self.pso_runs,
            "kernel_computations": self.kernel_computations,
            "superposition_states": len(self.superposition_states),
            "tensor_networks": len(self.tensor_networks),
            "optimizer_best_fitness": self.optimizer_state.get("best_fitness"),
        }
