#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v11.0 — Mathematical Structure Relation Discovery Engine
==================================================================
8-Relation Type Discovery Engine with Self-Inference & Mutual Computation

Supported Relation Types:
  1. Coupling      — Information flow strength (mutual information)
  2. Embedding     — Structure-preserving map
  3. Equivalence   — Isomorphism class
  4. Symmetry      — Automorphism group
  5. Duality       — Categorical / Poincare duality
  6. Entailment    — Logical entailment
  7. Dependency    — Construction dependency
  8. Bridging      — Cross-domain mapping

Core Capabilities:
  - SelfInferenceEngine:    Transitive closure, homology cycle detection,
                            spectral graph propagation
  - MutualComputationProtocol: Forward+reverse drive, self/mutual excitation
  - UnifiedFieldInjector:   Map relation strength to 64D UnifiedFieldState
  - Chain-Network-Field-Spectrum-Domain unification

Compatibility: OMNI-HUB v11.0 UnifiedFieldState, KNode/KEdge data structures
Dependencies:  numpy only (pure Python fallbacks for all graph operations)

Version: 11.0.0
Date: 2026
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import (
    Any, Callable, Dict, Generic, Iterator, List, Optional,
    Set, Tuple, TypeVar, Union, Protocol
)

import numpy as np
from numpy.linalg import norm, matrix_rank, eig, svd, inv, det

# =============================================================================
# 0. Optional OMNI-HUB v11 Standards Import (with graceful fallback)
# =============================================================================

_OMNI_STD_AVAILABLE = False
try:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "v11_standards", 
        __file__.rsplit("/", 1)[0] + "/v11_standards.py"
    )
    if _spec and _spec.loader:
        _v11_std = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_v11_std)
        DimensionIndex = _v11_std.DimensionIndex
        UnifiedFieldState = _v11_std.UnifiedFieldState
        UNIFIED_FIELD_DIMENSIONS = _v11_std.UNIFIED_FIELD_DIMENSIONS
        PHI_GOLDEN = _v11_std.PHI_GOLDEN
        _OMNI_STD_AVAILABLE = True
except Exception:
    pass

if not _OMNI_STD_AVAILABLE:
    # Fallback definitions when v11_standards.py is not importable
    class DimensionIndex(Enum):
        DIM_ENERGY = 0; DIM_COHERENCE = 1; DIM_ENTROPY = 2
        DIM_TEMPERATURE = 3; DIM_PRESSURE = 4; DIM_VELOCITY = 5
        DIM_MASS = 6; DIM_CHARGE = 7; DIM_SPIN = 8
        DIM_FLUX = 9; DIM_POTENTIAL = 10; DIM_VECTOR_POTENTIAL = 11
        DIM_TENSOR_FIELD = 12; DIM_CURVATURE = 13; DIM_TORSION = 14
        DIM_TOPOLOGY = 15
        DIM_INFORMATION = 16; DIM_KNOWLEDGE = 17; DIM_SEMANTIC = 18
        DIM_SYNTACTIC = 19; DIM_PRAGMATIC = 20; DIM_ENTAILMENT = 21
        DIM_CONSISTENCY = 22; DIM_COMPLETENESS = 23; DIM_DECIDABILITY = 24
        DIM_COMPRESSIBILITY = 25; DIM_KOLMOGOROV = 26; DIM_ENTROPY_RATE = 27
        DIM_FISHER = 28; DIM_MUTUAL_INFO = 29; DIM_CHANNEL_CAP = 30
        DIM_REDUNDANCY = 31
        DIM_ATTENTION = 32; DIM_INTENTION = 33; DIM_AWARENESS = 34
        DIM_REFLECTION = 35; DIM_CREATION = 36; DIM_UNDERSTANDING = 37
        DIM_WISDOM = 38; DIM_EMOTION = 39; DIM_EMPATHY = 40
        DIM_INTUITION = 41; DIM_MEMORY = 42; DIM_LEARNING = 43
        DIM_ADAPTATION = 44; DIM_TRANSCENDENCE = 45; DIM_PRESENCE = 46
        DIM_FLOW = 47
        DIM_EMERGENCE = 48; DIM_SELF_ORG = 49; DIM_AUTO_POIESIS = 50
        DIM_HOLON = 51; DIM_SYNERGY = 52; DIM_RESONANCE = 53
        DIM_COHERENCE_EM = 54; DIM_PHASE_LOCK = 55; DIM_BIFURCATION = 56
        DIM_CRITICALITY = 57; DIM_SCALE_INV = 58; DIM_FRACTAL_DIM = 59
        DIM_LYAPUNOV = 60; DIM_CORRELATION = 61; DIM_HIERARCHY = 62
        DIM_UNIFICATION = 63

    UNIFIED_FIELD_DIMENSIONS = 64
    PHI_GOLDEN = 1.618033988749895

    class UnifiedFieldState:
        def __init__(self, dimensions: int = UNIFIED_FIELD_DIMENSIONS) -> None:
            self.dimensions = dimensions
            self.vector: List[float] = [0.0] * dimensions
            self.timestamp: float = time.time()
            self.version: str = "11.0.0"

        def get(self, dim: DimensionIndex) -> float:
            return self.vector[dim.value]

        def set(self, dim: DimensionIndex, value: float) -> None:
            self.vector[dim.value] = float(value)

        def copy(self) -> "UnifiedFieldState":
            new = UnifiedFieldState(self.dimensions)
            new.vector = self.vector.copy()
            new.timestamp = self.timestamp
            return new

        def to_dict(self) -> Dict[str, Any]:
            return {
                "vector": self.vector,
                "timestamp": self.timestamp,
                "version": self.version,
                "dimensions": self.dimensions,
            }

        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "UnifiedFieldState":
            state = cls(data.get("dimensions", UNIFIED_FIELD_DIMENSIONS))
            state.vector = data.get("vector", [0.0] * state.dimensions)
            state.timestamp = data.get("timestamp", 0.0)
            return state

# =============================================================================
# 1. Data Structures — Knowledge Node & Edge (KNode / KEdge compatible)
# =============================================================================

@dataclass
class KNode:
    """Knowledge Node — lightweight replica compatible with v11_knowledge_pedestal."""
    node_id: str
    label: str
    node_type: str = "generic"
    module: str = "relation_engine"
    version: str = "11.0.0"
    size_bytes: int = 0
    path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.embedding is not None:
            d["embedding"] = self.embedding.tolist()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "KNode":
        emb = d.pop("embedding", None)
        node = cls(**d)
        if emb is not None:
            node.embedding = np.array(emb, dtype=np.float64)
        return node


@dataclass
class KEdge:
    """Knowledge Edge — lightweight replica compatible with v11_knowledge_pedestal."""
    edge_id: str
    source: str
    target: str
    edge_type: str = "generic"
    weight: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# 2. Relation Taxonomy
# =============================================================================

class RelationType(Enum):
    """Eight fundamental mathematical structure relation types."""
    COUPLING = auto()      # 1. 耦合 — Information flow / mutual information
    EMBEDDING = auto()     # 2. 嵌入 — Structure-preserving map
    EQUIVALENCE = auto()   # 3. 等价 — Isomorphism / equivalence class
    SYMMETRY = auto()      # 4. 对称 — Automorphism group
    DUALITY = auto()       # 5. 对偶 — Categorical / Poincare duality
    ENTAILMENT = auto()    # 6. 蕴含 — Logical entailment
    DEPENDENCY = auto()    # 7. 依赖 — Construction dependency
    BRIDGING = auto()      # 8. 桥接 — Cross-domain mapping

    @classmethod
    def all_types(cls) -> List["RelationType"]:
        return list(cls)


# =============================================================================
# 3. Abstract Relation Base
# =============================================================================

@dataclass
class Relation:
    """Base class for all 8 relation types."""
    rel_id: str
    source_id: str
    target_id: str
    rel_type: RelationType
    strength: float = 0.0          # [0, 1] normalized relation strength
    confidence: float = 1.0        # [0, 1] confidence in the relation
    field_projection: np.ndarray = field(default_factory=lambda: np.zeros(UNIFIED_FIELD_DIMENSIONS))
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.field_projection.shape[0] != UNIFIED_FIELD_DIMENSIONS:
            self.field_projection = np.zeros(UNIFIED_FIELD_DIMENSIONS)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rel_id": self.rel_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": self.rel_type.name,
            "strength": self.strength,
            "confidence": self.confidence,
            "field_projection": self.field_projection.tolist(),
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Relation":
        d = d.copy()
        d["rel_type"] = RelationType[d["rel_type"]]
        d["field_projection"] = np.array(d.pop("field_projection"), dtype=np.float64)
        return cls(**d)


# =============================================================================
# 4. Eight Concrete Relation Classes
# =============================================================================

@dataclass
class CouplingRelation(Relation):
    """
    耦合关系 — 信息流强度检测。
    基于互信息(Mutual Information)或交叉熵的信息流强度。
    """
    mutual_information: float = 0.0
    transfer_entropy: float = 0.0
    correlation_coefficient: float = 0.0
    information_flow_direction: str = "bidirectional"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.COUPLING

    def compute_from_embeddings(self, emb_a: np.ndarray, emb_b: np.ndarray) -> float:
        """Compute coupling strength from two node embeddings via correlation."""
        ea = emb_a.flatten()
        eb = emb_b.flatten()
        min_len = min(len(ea), len(eb))
        ea, eb = ea[:min_len], eb[:min_len]
        # Pearson correlation
        if norm(ea) < 1e-12 or norm(eb) < 1e-12:
            self.strength = 0.0
            return 0.0
        corr = float(np.dot(ea, eb) / (norm(ea) * norm(eb)))
        self.correlation_coefficient = corr
        # Mutual information proxy: I(X;Y) ~ -0.5 * log(1 - rho^2) for Gaussian
        mi = 0.0
        if abs(corr) < 1.0:
            mi = -0.5 * math.log(1.0 - corr * corr)
        self.mutual_information = mi
        self.strength = min(1.0, max(0.0, abs(corr)))
        return self.strength

    def compute_transfer_entropy(self, series_a: np.ndarray, series_b: np.ndarray,
                                  lag: int = 1) -> float:
        """Granger-causality-like transfer entropy proxy."""
        if len(series_a) <= lag or len(series_b) <= lag:
            self.transfer_entropy = 0.0
            return 0.0
        # Simplified: conditional correlation
        a_past = series_a[:-lag]
        b_future = series_b[lag:]
        min_len = min(len(a_past), len(b_future))
        a_past = a_past[:min_len]
        b_future = b_future[:min_len]
        if norm(a_past) < 1e-12 or norm(b_future) < 1e-12:
            te = 0.0
        else:
            te = float(np.dot(a_past, b_future) / (norm(a_past) * norm(b_future)))
        self.transfer_entropy = te
        return te


@dataclass
class EmbeddingRelation(Relation):
    """
    嵌入关系 — 保结构映射检测。
    检测 source 是否可以结构保持地嵌入到 target 中。
    """
    dimension_ratio: float = 1.0       # dim(source) / dim(target)
    structure_preservation_score: float = 0.0
    distortion: float = 0.0            # 低 = 好
    is_isometric: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.EMBEDDING

    def compute_from_matrices(self, M_source: np.ndarray, M_target: np.ndarray) -> float:
        """
        Compute embedding score from adjacency / structure matrices.
        Uses spectral alignment: if source is a sub-structure of target,
        the leading eigenvalues of M_source should align with a subset of M_target.
        """
        # Ensure square
        if M_source.ndim != 2 or M_target.ndim != 2:
            self.strength = 0.0
            return 0.0
        s_rows, s_cols = M_source.shape
        t_rows, t_cols = M_target.shape
        if s_rows != s_cols or t_rows != t_cols:
            # Non-square treated as bipartite; use SVD alignment
            return self._compute_bipartite_embedding(M_source, M_target)

        self.dimension_ratio = s_rows / max(t_rows, 1)
        # Spectral alignment score
        try:
            eig_s = np.linalg.eigvalsh(M_source @ M_source.T)
            eig_t = np.linalg.eigvalsh(M_target @ M_target.T)
        except Exception:
            self.strength = 0.0
            return 0.0

        # Take top-k from source, match to top-k in target
        k = min(s_rows, t_rows)
        top_s = np.sort(np.abs(eig_s))[-k:][::-1]
        top_t = np.sort(np.abs(eig_t))[-k:][::-1]
        # Normalized alignment
        alignment = float(np.dot(top_s, top_t) / (norm(top_s) * norm(top_t) + 1e-12))
        # Distortion = 1 - alignment
        self.distortion = max(0.0, 1.0 - alignment)
        self.structure_preservation_score = alignment
        self.is_isometric = alignment > 0.95
        self.strength = alignment
        return self.strength

    def _compute_bipartite_embedding(self, A: np.ndarray, B: np.ndarray) -> float:
        """Bipartite / rectangular matrix alignment via SVD overlap."""
        try:
            sA = svd(A, compute_uv=False)
            sB = svd(B, compute_uv=False)
        except Exception:
            self.strength = 0.0
            return 0.0
        k = min(len(sA), len(sB), 10)
        sA_top = sA[:k]
        sB_top = sB[:k]
        if norm(sA_top) < 1e-12 or norm(sB_top) < 1e-12:
            score = 0.0
        else:
            score = float(np.dot(sA_top, sB_top) / (norm(sA_top) * norm(sB_top)))
        self.structure_preservation_score = score
        self.strength = score
        return score


@dataclass
class EquivalenceRelation(Relation):
    """
    等价关系 — 同构类检测。
    基于特征向量匹配的等价判定。
    """
    isomorphism_score: float = 0.0
    feature_distance: float = 1.0
    canonical_form_hash: str = ""
    equivalence_class_id: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.EQUIVALENCE

    def compute_from_features(self, feat_a: np.ndarray, feat_b: np.ndarray) -> float:
        """Compute equivalence from feature vectors using normalized distance."""
        fa = feat_a.flatten()
        fb = feat_b.flatten()
        min_len = min(len(fa), len(fb))
        fa, fb = fa[:min_len], fb[:min_len]
        # Normalize
        na, nb = norm(fa), norm(fb)
        if na < 1e-12 or nb < 1e-12:
            self.isomorphism_score = 0.0
            self.feature_distance = 1.0
            self.strength = 0.0
            return 0.0
        fa_n, fb_n = fa / na, fb / nb
        dist = float(norm(fa_n - fb_n))
        # Map distance to similarity
        sim = math.exp(-dist * dist / 2.0)
        self.feature_distance = dist
        self.isomorphism_score = sim
        self.strength = sim
        # Canonical hash for equivalence class
        combined = np.round((fa_n + fb_n) / 2.0, decimals=4)
        self.canonical_form_hash = hashlib.sha256(
            combined.tobytes()
        ).hexdigest()[:16]
        self.equivalence_class_id = self.canonical_form_hash
        return self.strength

    def compute_from_graph_invariants(self, invariants_a: Dict[str, float],
                                       invariants_b: Dict[str, float]) -> float:
        """Compute equivalence from graph/network invariants."""
        keys = set(invariants_a.keys()) & set(invariants_b.keys())
        if not keys:
            self.strength = 0.0
            return 0.0
        diffs = []
        for k in keys:
            va, vb = invariants_a[k], invariants_b[k]
            denom = max(abs(va), abs(vb), 1e-12)
            diffs.append(abs(va - vb) / denom)
        avg_diff = sum(diffs) / len(diffs)
        sim = math.exp(-avg_diff)
        self.isomorphism_score = sim
        self.strength = sim
        return sim


@dataclass
class SymmetryRelation(Relation):
    """
    对称关系 — 自同构群检测。
    检测结构内部的对称性（自同构数量 / 对称群阶数）。
    """
    automorphism_count: int = 0
    symmetry_group_order: int = 1
    symmetry_score: float = 0.0       # [0,1] 高 = 高度对称
    orbit_count: int = 0
    fixed_points: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.SYMMETRY

    def compute_from_adjacency(self, adj: np.ndarray) -> float:
        """
        Estimate symmetry from adjacency matrix spectral properties.
        Highly symmetric graphs have repeated eigenvalues.
        """
        if adj.ndim != 2 or adj.shape[0] != adj.shape[1]:
            self.strength = 0.0
            return 0.0
        n = adj.shape[0]
        try:
            w = np.linalg.eigvalsh(adj)
        except Exception:
            self.strength = 0.0
            return 0.0
        # Count repeated eigenvalues (degeneracy)
        rounded = np.round(w, decimals=6)
        unique, counts = np.unique(rounded, return_counts=True)
        degeneracy = int(np.sum(counts[counts > 1]))
        self.automorphism_count = max(1, degeneracy)
        # Symmetry score: ratio of degenerate eigenvalues
        self.symmetry_score = min(1.0, degeneracy / max(n, 1))
        self.orbit_count = len(unique)
        self.symmetry_group_order = self.automorphism_count
        self.strength = self.symmetry_score
        return self.strength

    def compute_from_node_orbits(self, node_labels: List[str],
                                  orbit_partition: List[List[str]]) -> float:
        """Compute symmetry from explicit orbit partition."""
        n = len(node_labels)
        if n == 0:
            self.strength = 0.0
            return 0.0
        # Larger orbits = more symmetry
        max_orbit = max(len(o) for o in orbit_partition) if orbit_partition else 1
        self.orbit_count = len(orbit_partition)
        self.symmetry_score = min(1.0, max_orbit / n)
        self.automorphism_count = math.prod(
            [math.factorial(len(o)) for o in orbit_partition if len(o) > 1] or [1]
        )
        self.symmetry_group_order = self.automorphism_count
        self.strength = self.symmetry_score
        return self.strength


@dataclass
class DualityRelation(Relation):
    """
    对偶关系 — 范畴对偶 / 庞加莱对偶检测。
    source 和 target 构成对偶对。
    """
    duality_type: str = "categorical"    # categorical | poincare | pontryagin | langlands
    duality_score: float = 0.0
    cohomology_alignment: float = 0.0
    hodge_star_alignment: float = 0.0
    dimension_complement: bool = False   # dim(A) + dim(B) = total_dim ?

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.DUALITY

    def compute_categorical_duality(self, hom_a: np.ndarray, hom_b: np.ndarray) -> float:
        """
        Categorical duality: Hom(A, B) should be naturally isomorphic to Hom(B*, A*).
        Approximated by homomorphism matrix alignment.
        """
        if hom_a.shape != hom_b.shape:
            self.strength = 0.0
            return 0.0
        # Transpose alignment: dual means structure is "flipped"
        alignment = float(np.trace(hom_a @ hom_b.T) / (norm(hom_a) * norm(hom_b) + 1e-12))
        self.duality_score = max(0.0, alignment)
        self.duality_type = "categorical"
        self.strength = self.duality_score
        return self.strength

    def compute_poincare_duality(self, betti_a: List[int], betti_b: List[int],
                                  total_dim: int) -> float:
        """
        Poincare duality: b_k(A) = b_{n-k}(B) for complementary dimensions.
        """
        max_dim = max(len(betti_a), len(betti_b))
        padded_a = betti_a + [0] * (max_dim - len(betti_a))
        padded_b = betti_b + [0] * (max_dim - len(betti_b))
        # Check complementarity
        score = 0.0
        for k in range(max_dim):
            complement_k = total_dim - k
            if 0 <= complement_k < max_dim:
                score += 1.0 - abs(padded_a[k] - padded_b[complement_k]) / max(
                    padded_a[k] + padded_b[complement_k], 1
                )
        score /= max(max_dim, 1)
        self.cohomology_alignment = score
        self.dimension_complement = True
        self.duality_type = "poincare"
        self.duality_score = score
        self.strength = score
        return score

    def compute_langlands_duality(self, spectral_a: np.ndarray,
                                   spectral_b: np.ndarray) -> float:
        """Langlands-like spectral correspondence."""
        sa = spectral_a.flatten()
        sb = spectral_b.flatten()
        min_len = min(len(sa), len(sb))
        sa, sb = sa[:min_len], sb[:min_len]
        if norm(sa) < 1e-12 or norm(sb) < 1e-12:
            score = 0.0
        else:
            score = float(np.dot(sa, sb) / (norm(sa) * norm(sb)))
        self.duality_score = score
        self.duality_type = "langlands"
        self.strength = score
        return score


@dataclass
class EntailmentRelation(Relation):
    """
    蕴含关系 — 逻辑/语义蕴含检测。
    source 语义/逻辑上蕴含 target。
    """
    entailment_strength: float = 0.0
    logical_form_distance: float = 1.0
    premise_coverage: float = 0.0
    conclusion_generality: float = 0.0
    inference_steps: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.ENTAILMENT

    def compute_from_semantic_vectors(self, premise: np.ndarray,
                                       conclusion: np.ndarray) -> float:
        """
        Semantic entailment: conclusion should be "contained in" premise.
        Approximated by directional projection.
        """
        p = premise.flatten()
        c = conclusion.flatten()
        min_len = min(len(p), len(c))
        p, c = p[:min_len], c[:min_len]
        np_norm = norm(p)
        nc_norm = norm(c)
        if np_norm < 1e-12 or nc_norm < 1e-12:
            self.strength = 0.0
            return 0.0
        # Projection of c onto p: if c is in the span of p, entailment is strong
        projection = float(np.dot(p, c) / (np_norm * np_norm))
        coverage = float(np.dot(p, c) / (np_norm * nc_norm))
        self.premise_coverage = max(0.0, min(1.0, coverage))
        self.conclusion_generality = nc_norm / (np_norm + 1e-12)
        # Entailment stronger when coverage is high and conclusion is more specific
        self.entailment_strength = self.premise_coverage * (
            1.0 - min(1.0, self.conclusion_generality)
        )
        self.logical_form_distance = 1.0 - self.premise_coverage
        self.strength = self.entailment_strength
        self.inference_steps = int(1.0 / (self.strength + 0.01))
        return self.strength

    def compute_from_proof_structure(self, proof_depth: int,
                                      axioms_used: Set[str],
                                      conclusion_axioms: Set[str]) -> float:
        """Compute entailment from proof structure metadata."""
        if not conclusion_axioms:
            self.strength = 0.0
            return 0.0
        coverage = len(axioms_used & conclusion_axioms) / len(conclusion_axioms)
        depth_penalty = math.exp(-proof_depth / 10.0)
        self.premise_coverage = coverage
        self.inference_steps = proof_depth
        self.entailment_strength = coverage * depth_penalty
        self.strength = self.entailment_strength
        return self.strength


@dataclass
class DependencyRelation(Relation):
    """
    依赖关系 — 构造/证明依赖检测。
    target 的构造依赖于 source。
    """
    dependency_type: str = "construction"   # construction | proof | type | module
    dependency_depth: int = 0
    critical_path: bool = False
    circular: bool = False
    build_order: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.DEPENDENCY

    def compute_from_dag(self, adjacency: Dict[str, List[str]],
                         source: str, target: str) -> float:
        """
        Compute dependency strength from DAG reachability.
        Strength = 1 / (shortest_path_length + 1)
        """
        # BFS shortest path
        visited: Set[str] = set()
        queue: deque = deque([(source, 0)])
        found_depth = -1
        while queue:
            node, depth = queue.popleft()
            if node == target:
                found_depth = depth
                break
            if node in visited:
                continue
            visited.add(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
        if found_depth < 0:
            self.strength = 0.0
            self.dependency_depth = -1
            return 0.0
        self.dependency_depth = found_depth
        self.strength = 1.0 / (found_depth + 1.0)
        self.critical_path = found_depth == 1
        self.build_order = found_depth
        return self.strength

    def compute_from_type_hierarchy(self, type_a: str, type_b: str,
                                     hierarchy: Dict[str, Optional[str]]) -> float:
        """Compute dependency from type hierarchy (inheritance chain)."""
        depth = 0
        current = type_b
        while current is not None and current != type_a:
            current = hierarchy.get(current)
            depth += 1
            if depth > 1000:  # Safety break
                break
        if current == type_a:
            self.dependency_depth = depth
            self.strength = 1.0 / (depth + 1.0)
            self.dependency_type = "type"
        else:
            self.strength = 0.0
            self.dependency_depth = -1
        return self.strength


@dataclass
class BridgingRelation(Relation):
    """
    桥接关系 — 跨域概念映射检测。
    source 和 target 属于不同域但存在结构对应。
    """
    domain_a: str = ""
    domain_b: str = ""
    bridge_type: str = "analogy"       # analogy | metaphor | isomorphism | translation
    cross_domain_alignment: float = 0.0
    mapping_fidelity: float = 0.0
    analogical_depth: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.rel_type = RelationType.BRIDGING

    def compute_cross_domain(self, struct_a: np.ndarray, struct_b: np.ndarray,
                             domain_a: str, domain_b: str) -> float:
        """
        Compute bridging strength across different domains.
        Uses Procrustes-like alignment of structure matrices.
        """
        self.domain_a = domain_a
        self.domain_b = domain_b
        # Simplified Procrustes: orthogonal alignment score
        A = struct_a.astype(np.float64)
        B = struct_b.astype(np.float64)
        # Pad to same shape
        max_rows = max(A.shape[0], B.shape[0])
        max_cols = max(A.shape[1] if A.ndim > 1 else 1, 
                       B.shape[1] if B.ndim > 1 else 1)
        Ap = np.zeros((max_rows, max_cols))
        Bp = np.zeros((max_rows, max_cols))
        Ap[:A.shape[0], :A.shape[1] if A.ndim > 1 else 1] = A.reshape(A.shape[0], -1)[:, :1] if A.ndim == 1 else A
        Bp[:B.shape[0], :B.shape[1] if B.ndim > 1 else 1] = B.reshape(B.shape[0], -1)[:, :1] if B.ndim == 1 else B
        # Frobenius correlation
        nA, nB = norm(Ap, 'fro'), norm(Bp, 'fro')
        if nA < 1e-12 or nB < 1e-12:
            score = 0.0
        else:
            score = float(np.trace(Ap.T @ Bp) / (nA * nB))
        self.cross_domain_alignment = max(0.0, score)
        self.mapping_fidelity = self.cross_domain_alignment
        self.analogical_depth = int(1.0 / (score + 0.01))
        self.strength = self.cross_domain_alignment
        self.bridge_type = "analogy" if score < 0.7 else "isomorphism"
        return self.strength

    def compute_from_concept_mapping(self, concepts_a: List[str],
                                      concepts_b: List[str],
                                      known_mappings: Dict[str, str]) -> float:
        """Compute bridging from explicit concept mappings."""
        if not concepts_a or not concepts_b:
            self.strength = 0.0
            return 0.0
        mapped = 0
        for ca in concepts_a:
            if ca in known_mappings and known_mappings[ca] in concepts_b:
                mapped += 1
        coverage = mapped / max(len(concepts_a), len(concepts_b), 1)
        self.mapping_fidelity = coverage
        self.cross_domain_alignment = coverage
        self.strength = coverage
        self.analogical_depth = len(known_mappings)
        return self.strength


# =============================================================================
# 5. Relation Registry & Factory
# =============================================================================

class RelationFactory:
    """Factory for creating relation instances by type."""

    _builders: Dict[RelationType, type] = {
        RelationType.COUPLING: CouplingRelation,
        RelationType.EMBEDDING: EmbeddingRelation,
        RelationType.EQUIVALENCE: EquivalenceRelation,
        RelationType.SYMMETRY: SymmetryRelation,
        RelationType.DUALITY: DualityRelation,
        RelationType.ENTAILMENT: EntailmentRelation,
        RelationType.DEPENDENCY: DependencyRelation,
        RelationType.BRIDGING: BridgingRelation,
    }

    @classmethod
    def create(cls, rel_type: RelationType, source_id: str, target_id: str,
               **kwargs: Any) -> Relation:
        builder = cls._builders.get(rel_type, Relation)
        rel_id = kwargs.pop("rel_id", f"rel_{uuid.uuid4().hex[:8]}")
        # Instantiate appropriate subclass
        instance = builder(
            rel_id=rel_id,
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            **kwargs
        )
        return instance

    @classmethod
    def all_relation_types(cls) -> List[RelationType]:
        return list(cls._builders.keys())


# =============================================================================
# 6. Self-Inference Engine
# =============================================================================

class SelfInferenceEngine:
    """
    自推演引擎 — 基于关系集合进行自动推演。
    支持：传递闭包、同调环检测、谱图论场传播
    """

    def __init__(self, node_ids: List[str]) -> None:
        self.node_ids = list(node_ids)
        self.n = len(node_ids)
        self.id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        # Relation matrices per type (n x n)
        self.relation_matrices: Dict[RelationType, np.ndarray] = {
            rt: np.zeros((self.n, self.n)) for rt in RelationType.all_types()
        }
        # Unified adjacency (sum over all relation types weighted by strength)
        self.unified_adjacency: np.ndarray = np.zeros((self.n, self.n))
        # Laplacian
        self.laplacian: Optional[np.ndarray] = None
        # Eigen-decomposition cache
        self._eigenvalues: Optional[np.ndarray] = None
        self._eigenvectors: Optional[np.ndarray] = None

    def add_relation(self, rel: Relation) -> None:
        """Add a relation to the engine's internal matrices."""
        i = self.id_to_idx.get(rel.source_id)
        j = self.id_to_idx.get(rel.target_id)
        if i is None or j is None:
            return
        w = rel.strength * rel.confidence
        self.relation_matrices[rel.rel_type][i, j] = max(
            self.relation_matrices[rel.rel_type][i, j], w
        )
        self.unified_adjacency[i, j] = max(self.unified_adjacency[i, j], w)
        # Invalidate cached decomposition
        self._eigenvalues = None
        self._eigenvectors = None
        self.laplacian = None

    def build_laplacian(self) -> np.ndarray:
        """Build graph Laplacian L = D - A (combinatorial)."""
        A = self.unified_adjacency
        D = np.diag(A.sum(axis=1))
        self.laplacian = D - A
        return self.laplacian

    # ------------------------------------------------------------------
    # 6.1 Transitive Closure (Chain Inference)
    # ------------------------------------------------------------------

    def transitive_closure(self, rel_type: Optional[RelationType] = None,
                           max_hops: int = 10,
                           threshold: float = 0.01) -> np.ndarray:
        """
        Compute transitive closure via matrix powering with thresholding.
        Returns closure matrix C where C[i,j] > 0 means i can reach j.
        """
        if rel_type is not None:
            M = self.relation_matrices[rel_type].copy()
        else:
            M = self.unified_adjacency.copy()

        # Ensure no self-loops initially for pure transitive computation
        np.fill_diagonal(M, 0.0)

        n = M.shape[0]
        # Floyd-Warshall variant for weighted reachability
        closure = M.copy()
        for k in range(n):
            for i in range(n):
                if closure[i, k] < threshold:
                    continue
                for j in range(n):
                    # Path i -> k -> j exists
                    if closure[k, j] >= threshold:
                        new_val = closure[i, k] * closure[k, j]
                        if new_val > closure[i, j]:
                            closure[i, j] = new_val
        # Cap at 1.0
        closure = np.clip(closure, 0.0, 1.0)
        return closure

    def compute_reachability(self, source: str, target: str,
                             max_hops: int = 10) -> Tuple[float, List[str]]:
        """
        Compute reachability probability and shortest path.
        Returns (strength, path_nodes).
        """
        closure = self.transitive_closure(max_hops=max_hops)
        i, j = self.id_to_idx[source], self.id_to_idx[target]
        strength = float(closure[i, j])
        # Shortest path via BFS on thresholded adjacency
        threshold = 0.1
        adj = (self.unified_adjacency >= threshold).astype(int)
        visited = {i: None}
        queue = deque([i])
        found = False
        while queue:
            u = queue.popleft()
            if u == j:
                found = True
                break
            for v in range(self.n):
                if adj[u, v] and v not in visited:
                    visited[v] = u
                    queue.append(v)
        path = []
        if found:
            cur = j
            while cur is not None:
                path.append(self.node_ids[cur])
                cur = visited[cur]
            path.reverse()
        return strength, path

    def infer_new_relations(self, rel_type: RelationType,
                            min_strength: float = 0.3) -> List[Relation]:
        """
        Infer new relations via transitive closure.
        If A -> B and B -> C with strength s1, s2, infer A -> C with strength s1*s2.
        """
        closure = self.transitive_closure(rel_type=rel_type)
        existing = self.relation_matrices[rel_type]
        new_rels: List[Relation] = []
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    continue
                if existing[i, j] < 0.01 and closure[i, j] >= min_strength:
                    new_rel = RelationFactory.create(
                        rel_type=rel_type,
                        source_id=self.node_ids[i],
                        target_id=self.node_ids[j],
                        strength=float(closure[i, j]),
                        confidence=0.7,  # inferred confidence lower than direct
                        metadata={"inferred": True, "inference_method": "transitive_closure"}
                    )
                    new_rels.append(new_rel)
        return new_rels

    # ------------------------------------------------------------------
    # 6.2 Homological Cycle Detection (Network Cycles)
    # ------------------------------------------------------------------

    def detect_cycles(self, threshold: float = 0.1) -> List[List[str]]:
        """
        Detect simple cycles in the relation graph using DFS.
        Returns list of node-id cycles.
        """
        adj = (self.unified_adjacency >= threshold).astype(int)
        cycles: List[List[str]] = []
        visited_global: Set[int] = set()

        def dfs(node: int, path: List[int], visited: Set[int]) -> None:
            visited_global.add(node)
            for neighbor in range(self.n):
                if adj[node, neighbor]:
                    if neighbor in visited:
                        # Found cycle
                        if neighbor == path[0] and len(path) >= 3:
                            cycle = [self.node_ids[x] for x in path]
                            cycles.append(cycle)
                    elif len(path) < 8:  # Limit cycle length
                        dfs(neighbor, path + [neighbor], visited | {neighbor})

        for start in range(self.n):
            if start not in visited_global:
                dfs(start, [start], {start})
        # Deduplicate cycles (same cycle, different start)
        unique: Set[Tuple[str, ...]] = set()
        deduped: List[List[str]] = []
        for c in cycles:
            # Normalize: start from minimum element
            min_idx = min(range(len(c)), key=lambda i: c[i])
            normalized = tuple(c[min_idx:] + c[:min_idx])
            if normalized not in unique:
                unique.add(normalized)
                deduped.append(list(normalized))
        return deduped

    def compute_homology_generators(self, threshold: float = 0.1) -> Dict[int, int]:
        """
        Compute approximate Betti numbers (cycle counts per dimension).
        Returns {dimension: cycle_count}.
        """
        cycles = self.detect_cycles(threshold=threshold)
        betti: Dict[int, int] = defaultdict(int)
        for c in cycles:
            dim = len(c) - 1  # 1-cycles have length 3
            betti[dim] += 1
        return dict(betti)

    def compute_boundary_operator(self, threshold: float = 0.1) -> np.ndarray:
        """
        Compute boundary operator matrix ∂: C_1 -> C_0.
        Returns incidence matrix of edges vs nodes.
        """
        adj = self.unified_adjacency >= threshold
        edges = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if adj[i, j] or adj[j, i]:
                    edges.append((i, j))
        m = len(edges)
        boundary = np.zeros((self.n, m))
        for k, (i, j) in enumerate(edges):
            boundary[i, k] = -1
            boundary[j, k] = 1
        return boundary

    # ------------------------------------------------------------------
    # 6.3 Spectral Graph Propagation (Field Diffusion)
    # ------------------------------------------------------------------

    def _ensure_decomposition(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute and cache eigendecomposition of Laplacian."""
        if self._eigenvalues is not None and self._eigenvectors is not None:
            return self._eigenvalues, self._eigenvectors
        if self.laplacian is None:
            self.build_laplacian()
        L = self.laplacian
        try:
            w, v = eig(L)
            # Sort by eigenvalue
            idx = np.argsort(w)
            self._eigenvalues = w[idx].real
            self._eigenvectors = v[:, idx].real
        except Exception:
            # Fallback: return identity
            self._eigenvalues = np.zeros(self.n)
            self._eigenvectors = np.eye(self.n)
        return self._eigenvalues, self._eigenvectors

    def spectral_propagate(self, initial_field: np.ndarray,
                           time: float = 1.0,
                           diffusion_coeff: float = 0.1) -> np.ndarray:
        """
        Propagate field via heat equation on graph:
            u(t) = exp(-t * diffusion_coeff * L) @ u(0)
        Uses spectral decomposition for efficiency.
        """
        w, v = self._ensure_decomposition()
        # Project initial field to eigenbasis
        u0 = initial_field.flatten()[:self.n]
        if len(u0) < self.n:
            u0 = np.pad(u0, (0, self.n - len(u0)))
        coeffs = v.T @ u0
        # Apply heat kernel
        heat_kernel = np.exp(-time * diffusion_coeff * w)
        propagated = v @ (heat_kernel * coeffs)
        return propagated

    def compute_field_gradient(self, scalar_field: np.ndarray) -> np.ndarray:
        """Compute discrete gradient of scalar field on graph."""
        if self.laplacian is None:
            self.build_laplacian()
        grad = self.laplacian @ scalar_field[:self.n]
        return grad

    def compute_field_divergence(self, vector_field: np.ndarray) -> np.ndarray:
        """Compute discrete divergence (same as gradient for scalar graph Laplacian)."""
        return self.compute_field_gradient(vector_field)

    def compute_field_curl_approx(self, edge_field: np.ndarray,
                                   threshold: float = 0.1) -> float:
        """
        Approximate curl around cycles: sum of edge field values around cycles.
        """
        cycles = self.detect_cycles(threshold=threshold)
        if not cycles:
            return 0.0
        total_curl = 0.0
        adj = self.unified_adjacency >= threshold
        for cycle in cycles:
            cycle_curl = 0.0
            for k in range(len(cycle)):
                i = self.id_to_idx[cycle[k]]
                j = self.id_to_idx[cycle[(k + 1) % len(cycle)]]
                if adj[i, j]:
                    cycle_curl += edge_field[i] - edge_field[j]
            total_curl += abs(cycle_curl)
        return total_curl / len(cycles)

    # ------------------------------------------------------------------
    # 6.4 Unified Inference Runner
    # ------------------------------------------------------------------

    def run_full_inference(self) -> Dict[str, Any]:
        """Run complete inference suite and return report."""
        report: Dict[str, Any] = {
            "timestamp": time.time(),
            "node_count": self.n,
            "relation_type_counts": {},
            "transitive_closure_density": 0.0,
            "cycle_count": 0,
            "betti_numbers": {},
            "spectral_gap": 0.0,
            "field_coherence": 0.0,
            "inferred_relations": [],
        }
        # Relation counts
        for rt, M in self.relation_matrices.items():
            count = int(np.sum(M > 0.01))
            report["relation_type_counts"][rt.name] = count
        # Transitive closure
        closure = self.transitive_closure()
        density = float(np.sum(closure > 0.01) / max(self.n * self.n, 1))
        report["transitive_closure_density"] = density
        # Cycles
        cycles = self.detect_cycles()
        report["cycle_count"] = len(cycles)
        report["cycles"] = cycles[:20]  # Limit output
        # Homology
        report["betti_numbers"] = self.compute_homology_generators()
        # Spectral gap
        w, _ = self._ensure_decomposition()
        if len(w) > 1:
            report["spectral_gap"] = float(w[1] - w[0]) if w[1] > w[0] else 0.0
        # Field coherence
        if self.laplacian is None:
            self.build_laplacian()
        trace_L = float(np.trace(self.laplacian)) if self.laplacian is not None else 0.0
        report["field_coherence"] = 1.0 / (1.0 + trace_L / max(self.n, 1))
        # Infer new relations for each type
        all_inferred: List[Relation] = []
        for rt in RelationType.all_types():
            inferred = self.infer_new_relations(rt, min_strength=0.3)
            all_inferred.extend(inferred)
        report["inferred_relations"] = [r.to_dict() for r in all_inferred[:50]]
        report["inferred_count"] = len(all_inferred)
        return report


# =============================================================================
# 7. Mutual Computation Protocol
# =============================================================================

class MutualComputationProtocol:
    """
    互计算协议 — 正向驱动 + 反向驱动 + 自激/互激检测。
    Forward:  Concept -> Relation -> Structure
    Reverse:  Structure -> Relation -> Concept
    Self/Mutual excitation: Positive feedback loop detection
    """

    def __init__(self, engine: SelfInferenceEngine) -> None:
        self.engine = engine
        self.forward_history: List[Dict[str, Any]] = []
        self.reverse_history: List[Dict[str, Any]] = []
        self.excitation_loops: List[List[str]] = []
        self.iteration_count: int = 0
        self.convergence_threshold: float = 1e-4

    # ------------------------------------------------------------------
    # 7.1 Forward Drive: Concept -> Relation -> Structure
    # ------------------------------------------------------------------

    def forward_drive(self, concept_embeddings: Dict[str, np.ndarray],
                      relation_types: Optional[List[RelationType]] = None) -> Dict[str, Any]:
        """
        Forward computation:
          1. Take concept embeddings
          2. Compute pairwise relations
          3. Build structure (graph / field)
          4. Return emergent structure properties
        """
        if relation_types is None:
            relation_types = [RelationType.COUPLING, RelationType.EQUIVALENCE]

        nodes = list(concept_embeddings.keys())
        relations: List[Relation] = []

        for i, nid_a in enumerate(nodes):
            emb_a = concept_embeddings[nid_a]
            for j, nid_b in enumerate(nodes):
                if i == j:
                    continue
                emb_b = concept_embeddings[nid_b]
                for rt in relation_types:
                    rel = self._compute_relation(rt, nid_a, nid_b, emb_a, emb_b)
                    if rel.strength > 0.1:
                        relations.append(rel)
                        self.engine.add_relation(rel)

        # Build structure and compute emergent properties
        structure = self._extract_structure()
        result = {
            "direction": "forward",
            "input_concepts": nodes,
            "relation_count": len(relations),
            "structure": structure,
            "timestamp": time.time(),
        }
        self.forward_history.append(result)
        return result

    def _compute_relation(self, rt: RelationType, a: str, b: str,
                          emb_a: np.ndarray, emb_b: np.ndarray) -> Relation:
        """Compute a single relation between two concepts."""
        rel = RelationFactory.create(rt, a, b)
        if isinstance(rel, CouplingRelation):
            rel.compute_from_embeddings(emb_a, emb_b)
        elif isinstance(rel, EquivalenceRelation):
            rel.compute_from_features(emb_a, emb_b)
        elif isinstance(rel, EmbeddingRelation):
            # Treat embeddings as 1D structure
            rel.compute_from_matrices(emb_a.reshape(-1, 1), emb_b.reshape(-1, 1))
        elif isinstance(rel, EntailmentRelation):
            rel.compute_from_semantic_vectors(emb_a, emb_b)
        elif isinstance(rel, DualityRelation):
            rel.compute_categorical_duality(emb_a.reshape(-1, 1), emb_b.reshape(-1, 1))
        elif isinstance(rel, BridgingRelation):
            rel.compute_cross_domain(emb_a, emb_b, "domain_a", "domain_b")
        elif isinstance(rel, SymmetryRelation):
            # Self-symmetry of combined space
            combined = np.outer(emb_a[:10], emb_b[:10])
            rel.compute_from_adjacency(combined)
        elif isinstance(rel, DependencyRelation):
            # Default weak dependency
            rel.strength = 0.1
            rel.dependency_depth = 1
        return rel

    def _extract_structure(self) -> Dict[str, Any]:
        """Extract structural properties from current engine state."""
        return {
            "transitive_closure_density": float(
                np.sum(self.engine.transitive_closure() > 0.01) / max(self.engine.n ** 2, 1)
            ),
            "cycle_count": len(self.engine.detect_cycles()),
            "spectral_gap": self._compute_spectral_gap(),
            "node_count": self.engine.n,
        }

    def _compute_spectral_gap(self) -> float:
        """Compute spectral gap from Laplacian eigenvalues."""
        try:
            w, _ = self.engine._ensure_decomposition()
            if len(w) > 1:
                return float(w[1] - w[0])
        except Exception:
            pass
        return 0.0

    # ------------------------------------------------------------------
    # 7.2 Reverse Drive: Structure -> Relation -> Concept
    # ------------------------------------------------------------------

    def reverse_drive(self, target_structure: Dict[str, Any],
                      candidate_concepts: List[str]) -> Dict[str, Any]:
        """
        Reverse computation:
          1. Take target structural constraints
          2. Search for concept assignments that satisfy structure
          3. Optimize to match desired properties
          4. Return best-fitting concept configuration
        """
        # Simplified: assign concepts to maximize structural match
        n = len(candidate_concepts)
        if n == 0 or n > self.engine.n:
            return {"direction": "reverse", "error": "concept count mismatch"}

        # Generate candidate embedding assignment
        best_score = -1.0
        best_assignment: Dict[str, str] = {}

        # Greedy assignment based on structural role similarity
        # Compute centrality as structural role proxy
        centrality = self._compute_centrality()
        # Sort candidates by "importance" (random proxy)
        np.random.seed(42)
        candidate_scores = np.random.rand(n)
        sorted_candidates = [c for _, c in sorted(
            zip(candidate_scores, candidate_concepts), reverse=True
        )]
        sorted_nodes = [self.engine.node_ids[i] for i in np.argsort(-centrality)]
        assignment = {}
        for i in range(min(n, len(sorted_nodes))):
            assignment[sorted_nodes[i]] = sorted_candidates[i]

        # Score: how well does assignment preserve relations?
        score = self._score_assignment(assignment)
        best_score = score
        best_assignment = assignment

        result = {
            "direction": "reverse",
            "target_structure": target_structure,
            "assignment": best_assignment,
            "match_score": best_score,
            "timestamp": time.time(),
        }
        self.reverse_history.append(result)
        return result

    def _compute_centrality(self) -> np.ndarray:
        """Compute degree centrality from unified adjacency."""
        return self.engine.unified_adjacency.sum(axis=1)

    def _score_assignment(self, assignment: Dict[str, str]) -> float:
        """Score an assignment by relation preservation."""
        score = 0.0
        count = 0
        for rt, M in self.engine.relation_matrices.items():
            for i in range(self.engine.n):
                for j in range(self.engine.n):
                    if M[i, j] > 0.1:
                        ni, nj = self.engine.node_ids[i], self.engine.node_ids[j]
                        if ni in assignment and nj in assignment:
                            # Higher score if relation is preserved
                            score += M[i, j]
                            count += 1
        return score / max(count, 1)

    # ------------------------------------------------------------------
    # 7.3 Self-Excitation & Mutual-Excitation Detection
    # ------------------------------------------------------------------

    def detect_excitation_loops(self, min_strength: float = 0.3) -> List[List[str]]:
        """
        Detect positive feedback loops where A -> B -> ... -> A with
        cumulative strength > min_strength.
        """
        cycles = self.engine.detect_cycles(threshold=min_strength)
        excitation_loops: List[List[str]] = []
        for cycle in cycles:
            # Compute cumulative loop gain
            gain = 1.0
            for k in range(len(cycle)):
                i = self.engine.id_to_idx[cycle[k]]
                j = self.engine.id_to_idx[cycle[(k + 1) % len(cycle)]]
                gain *= self.engine.unified_adjacency[i, j]
            if gain >= min_strength:
                excitation_loops.append(cycle)
        self.excitation_loops = excitation_loops
        return excitation_loops

    def mutual_excitation_step(self, field_state: np.ndarray,
                                coupling_matrix: np.ndarray) -> np.ndarray:
        """
        One step of mutual excitation dynamics:
          field_{t+1} = tanh(coupling_matrix @ field_t + field_t)
        """
        combined = coupling_matrix @ field_state + field_state
        return np.tanh(combined)

    def run_mutual_excitation(self, initial_field: np.ndarray,
                              steps: int = 20) -> Dict[str, Any]:
        """
        Run mutual excitation dynamics and detect convergence / oscillation.
        """
        field = initial_field.copy()
        history = [field.copy()]
        for _ in range(steps):
            field = self.mutual_excitation_step(
                field, self.engine.unified_adjacency
            )
            history.append(field.copy())
            # Check convergence
            if len(history) > 1:
                diff = norm(history[-1] - history[-2])
                if diff < self.convergence_threshold:
                    break

        # Detect oscillation
        oscillation = False
        period = 0
        if len(history) > 4:
            for p in range(2, len(history) // 2):
                if norm(history[-1] - history[-1 - p]) < self.convergence_threshold * 10:
                    oscillation = True
                    period = p
                    break

        return {
            "final_field": field,
            "history": history,
            "converged": len(history) < steps + 1,
            "oscillation_detected": oscillation,
            "period": period,
            "excitation_loops": self.detect_excitation_loops(),
        }

    # ------------------------------------------------------------------
    # 7.4 Full Mutual Computation Cycle
    # ------------------------------------------------------------------

    def run_cycle(self, concept_embeddings: Dict[str, np.ndarray],
                  target_structure: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run one full forward-reverse cycle with excitation detection.
        """
        self.iteration_count += 1
        # Forward
        fwd = self.forward_drive(concept_embeddings)
        # Reverse (if target structure provided)
        rev: Optional[Dict[str, Any]] = None
        if target_structure is not None:
            rev = self.reverse_drive(target_structure, list(concept_embeddings.keys()))
        # Excitation
        initial_field = np.random.rand(self.engine.n) * 0.1
        excitation = self.run_mutual_excitation(initial_field)
        return {
            "iteration": self.iteration_count,
            "forward": fwd,
            "reverse": rev,
            "excitation": excitation,
            "timestamp": time.time(),
        }


# =============================================================================
# 8. Unified Field Injector
# =============================================================================

class UnifiedFieldInjector:
    """
    统一场注入器 — 将关系发现结果映射到64维统一场状态。
    Maps relation strengths to UnifiedFieldState dimensions.
    """

    # Mapping from RelationType to primary DimensionIndex
    RELATION_DIMENSION_MAP: Dict[RelationType, DimensionIndex] = {
        RelationType.COUPLING: DimensionIndex.DIM_MUTUAL_INFO,      # 29
        RelationType.EMBEDDING: DimensionIndex.DIM_TOPOLOGY,         # 15
        RelationType.EQUIVALENCE: DimensionIndex.DIM_COMPLETENESS,   # 23
        RelationType.SYMMETRY: DimensionIndex.DIM_SCALE_INV,         # 58
        RelationType.DUALITY: DimensionIndex.DIM_HIERARCHY,          # 62
        RelationType.ENTAILMENT: DimensionIndex.DIM_ENTAILMENT,      # 21
        RelationType.DEPENDENCY: DimensionIndex.DIM_CHANNEL_CAP,     # 30
        RelationType.BRIDGING: DimensionIndex.DIM_CORRELATION,       # 61
    }

    @classmethod
    def inject_relation(cls, rel: Relation, field_state: UnifiedFieldState) -> UnifiedFieldState:
        """Inject a single relation's strength into the unified field."""
        dim = cls.RELATION_DIMENSION_MAP.get(rel.rel_type, DimensionIndex.DIM_CORRELATION)
        current = field_state.get(dim)
        # Accumulate with saturation
        new_val = min(1.0, current + rel.strength * rel.confidence * 0.1)
        field_state.set(dim, new_val)
        # Also affect correlated dimensions
        cls._spread_to_correlated_dims(rel, field_state)
        return field_state

    @classmethod
    def _spread_to_correlated_dims(cls, rel: Relation, field_state: UnifiedFieldState) -> None:
        """Spread relation influence to correlated field dimensions."""
        strength = rel.strength * rel.confidence
        # Information flow affects coherence
        if rel.rel_type == RelationType.COUPLING:
            field_state.set(DimensionIndex.DIM_COHERENCE,
                min(1.0, field_state.get(DimensionIndex.DIM_COHERENCE) + strength * 0.05))
            field_state.set(DimensionIndex.DIM_INFORMATION,
                min(1.0, field_state.get(DimensionIndex.DIM_INFORMATION) + strength * 0.05))
        # Embedding affects tensor field
        elif rel.rel_type == RelationType.EMBEDDING:
            field_state.set(DimensionIndex.DIM_TENSOR_FIELD,
                min(1.0, field_state.get(DimensionIndex.DIM_TENSOR_FIELD) + strength * 0.05))
        # Equivalence affects consistency
        elif rel.rel_type == RelationType.EQUIVALENCE:
            field_state.set(DimensionIndex.DIM_CONSISTENCY,
                min(1.0, field_state.get(DimensionIndex.DIM_CONSISTENCY) + strength * 0.05))
        # Symmetry affects scale invariance
        elif rel.rel_type == RelationType.SYMMETRY:
            field_state.set(DimensionIndex.DIM_SCALE_INV,
                min(1.0, field_state.get(DimensionIndex.DIM_SCALE_INV) + strength * 0.05))
        # Duality affects hierarchy
        elif rel.rel_type == RelationType.DUALITY:
            field_state.set(DimensionIndex.DIM_HIERARCHY,
                min(1.0, field_state.get(DimensionIndex.DIM_HIERARCHY) + strength * 0.05))
        # Entailment affects semantic / decidability
        elif rel.rel_type == RelationType.ENTAILMENT:
            field_state.set(DimensionIndex.DIM_SEMANTIC,
                min(1.0, field_state.get(DimensionIndex.DIM_SEMANTIC) + strength * 0.05))
            field_state.set(DimensionIndex.DIM_DECIDABILITY,
                min(1.0, field_state.get(DimensionIndex.DIM_DECIDABILITY) + strength * 0.03))
        # Dependency affects knowledge dimension
        elif rel.rel_type == RelationType.DEPENDENCY:
            field_state.set(DimensionIndex.DIM_KNOWLEDGE,
                min(1.0, field_state.get(DimensionIndex.DIM_KNOWLEDGE) + strength * 0.05))
        # Bridging affects correlation and unification
        elif rel.rel_type == RelationType.BRIDGING:
            field_state.set(DimensionIndex.DIM_CORRELATION,
                min(1.0, field_state.get(DimensionIndex.DIM_CORRELATION) + strength * 0.08))
            field_state.set(DimensionIndex.DIM_UNIFICATION,
                min(1.0, field_state.get(DimensionIndex.DIM_UNIFICATION) + strength * 0.05))

    @classmethod
    def inject_engine_state(cls, engine: SelfInferenceEngine) -> UnifiedFieldState:
        """Create a UnifiedFieldState from the entire inference engine state."""
        state = UnifiedFieldState()
        # Aggregate all relations
        for rt, M in engine.relation_matrices.items():
            total_strength = float(np.sum(M))
            dim = cls.RELATION_DIMENSION_MAP.get(rt, DimensionIndex.DIM_CORRELATION)
            state.set(dim, min(1.0, total_strength / max(engine.n, 1)))
        # Add structural properties
        cycles = engine.detect_cycles()
        state.set(DimensionIndex.DIM_TOPOLOGY, min(1.0, len(cycles) / max(engine.n, 1)))
        # Spectral properties
        try:
            w, _ = engine._ensure_decomposition()
            if len(w) > 1:
                gap = float(w[1] - w[0]) if w[1] > w[0] else 0.0
                state.set(DimensionIndex.DIM_RESONANCE, min(1.0, gap / max(gap + 1, 1)))
        except Exception:
            pass
        # Entropy from relation distribution
        all_vals = []
        for M in engine.relation_matrices.values():
            all_vals.extend(M.flatten().tolist())
        if all_vals:
            arr = np.array(all_vals)
            pos = arr[arr > 0]
            if len(pos) > 0:
                probs = pos / pos.sum()
                entropy = float(-np.sum(probs * np.log(probs + 1e-12)))
                state.set(DimensionIndex.DIM_ENTROPY, min(1.0, entropy / math.log(len(pos) + 1)))
        # Coherence
        state.set(DimensionIndex.DIM_COHERENCE,
            min(1.0, state.get(DimensionIndex.DIM_COHERENCE) + 0.3))
        state.set(DimensionIndex.DIM_UNIFICATION,
            min(1.0, sum(state.vector) / UNIFIED_FIELD_DIMENSIONS))
        state.timestamp = time.time()
        return state

    @classmethod
    def create_relation_field_projection(cls, rel: Relation) -> np.ndarray:
        """Create a 64D field projection vector for a relation."""
        projection = np.zeros(UNIFIED_FIELD_DIMENSIONS)
        dim = cls.RELATION_DIMENSION_MAP.get(rel.rel_type, DimensionIndex.DIM_CORRELATION)
        projection[dim.value] = rel.strength * rel.confidence
        # Secondary dimensions
        secondary_map: Dict[RelationType, List[DimensionIndex]] = {
            RelationType.COUPLING: [DimensionIndex.DIM_INFORMATION, DimensionIndex.DIM_CHANNEL_CAP],
            RelationType.EMBEDDING: [DimensionIndex.DIM_TENSOR_FIELD, DimensionIndex.DIM_CURVATURE],
            RelationType.EQUIVALENCE: [DimensionIndex.DIM_CONSISTENCY, DimensionIndex.DIM_COMPLETENESS],
            RelationType.SYMMETRY: [DimensionIndex.DIM_SCALE_INV, DimensionIndex.DIM_FRACTAL_DIM],
            RelationType.DUALITY: [DimensionIndex.DIM_HIERARCHY, DimensionIndex.DIM_PHASE_LOCK],
            RelationType.ENTAILMENT: [DimensionIndex.DIM_SEMANTIC, DimensionIndex.DIM_PRAGMATIC],
            RelationType.DEPENDENCY: [DimensionIndex.DIM_KNOWLEDGE, DimensionIndex.DIM_INFORMATION],
            RelationType.BRIDGING: [DimensionIndex.DIM_CORRELATION, DimensionIndex.DIM_UNIFICATION],
        }
        for sec_dim in secondary_map.get(rel.rel_type, []):
            projection[sec_dim.value] = rel.strength * rel.confidence * 0.5
        rel.field_projection = projection
        return projection


# =============================================================================
# 9. Chain-Network-Field-Spectrum-Domain Unification
# =============================================================================

class UnifiedRelationStructure:
    """
    链-网-场-谱-域合一结构。
    Provides a unified view of relations across all 5 structural levels.
    """

    def __init__(self, engine: SelfInferenceEngine) -> None:
        self.engine = engine

    # ------------------------------------------------------------------
    # 9.1 Chain Level — Linear sequences / paths
    # ------------------------------------------------------------------

    def get_chains(self, max_length: int = 10, threshold: float = 0.1) -> List[List[str]]:
        """Extract all significant chains (paths) in the relation graph."""
        adj = self.engine.unified_adjacency >= threshold
        chains: List[List[str]] = []
        visited_global: Set[Tuple[int, ...]] = set()

        def dfs(node: int, path: Tuple[int, ...]) -> None:
            if len(path) >= max_length:
                return
            for neighbor in range(self.engine.n):
                if adj[node, neighbor] and neighbor not in path:
                    new_path = path + (neighbor,)
                    if new_path not in visited_global:
                        visited_global.add(new_path)
                        chains.append([self.engine.node_ids[i] for i in new_path])
                        dfs(neighbor, new_path)

        for start in range(self.engine.n):
            dfs(start, (start,))
        # Sort by path strength
        def path_strength(chain: List[str]) -> float:
            s = 0.0
            for k in range(len(chain) - 1):
                i = self.engine.id_to_idx[chain[k]]
                j = self.engine.id_to_idx[chain[k + 1]]
                s += self.engine.unified_adjacency[i, j]
            return s / max(len(chain) - 1, 1)
        chains.sort(key=path_strength, reverse=True)
        return chains[:100]  # Limit output

    # ------------------------------------------------------------------
    # 9.2 Network Level — Graph structure
    # ------------------------------------------------------------------

    def get_network_stats(self) -> Dict[str, Any]:
        """Extract network-level statistics."""
        A = self.engine.unified_adjacency
        n = self.engine.n
        degrees = A.sum(axis=1)
        return {
            "node_count": n,
            "edge_count": int(np.sum(A > 0.01)),
            "avg_degree": float(degrees.mean()),
            "max_degree": float(degrees.max()),
            "density": float(np.sum(A > 0.01) / max(n * (n - 1), 1)),
            "degree_variance": float(degrees.var()),
        }

    # ------------------------------------------------------------------
    # 9.3 Field Level — Continuous field distribution
    # ------------------------------------------------------------------

    def get_field_distribution(self, initial_seed: Optional[np.ndarray] = None,
                                diffusion_time: float = 5.0) -> np.ndarray:
        """Get continuous field distribution after diffusion."""
        if initial_seed is None:
            initial_seed = np.ones(self.engine.n) / self.engine.n
        return self.engine.spectral_propagate(initial_seed, time=diffusion_time)

    # ------------------------------------------------------------------
    # 9.4 Spectrum Level — Eigen-decomposition
    # ------------------------------------------------------------------

    def get_spectrum(self) -> Dict[str, Any]:
        """Get spectral decomposition of the Laplacian."""
        w, v = self.engine._ensure_decomposition()
        return {
            "eigenvalues": w.tolist(),
            "spectral_gap": float(w[1] - w[0]) if len(w) > 1 else 0.0,
            "algebraic_connectivity": float(w[1]) if len(w) > 1 else 0.0,
            "eigenvector_count": v.shape[1],
            "effective_dimension": int(np.sum(w > 1e-6)),
        }

    # ------------------------------------------------------------------
    # 9.5 Domain Level — Categorical structure
    # ------------------------------------------------------------------

    def get_domain_structure(self) -> Dict[str, Any]:
        """
        Extract categorical / domain-level structure.
        Objects = nodes, Morphisms = relations weighted by strength.
        """
        objects = self.engine.node_ids
        morphisms: List[Dict[str, Any]] = []
        for rt, M in self.engine.relation_matrices.items():
            for i in range(self.engine.n):
                for j in range(self.engine.n):
                    if M[i, j] > 0.01:
                        morphisms.append({
                            "source": objects[i],
                            "target": objects[j],
                            "type": rt.name,
                            "strength": float(M[i, j]),
                        })
        # Identify composition pairs (f: A->B, g: B->C => g∘f: A->C)
        compositions = []
        src_map: Dict[str, List[Dict]] = defaultdict(list)
        tgt_map: Dict[str, List[Dict]] = defaultdict(list)
        for m in morphisms:
            src_map[m["source"]].append(m)
            tgt_map[m["target"]].append(m)
        for mid in objects:
            for f in tgt_map.get(mid, []):
                for g in src_map.get(mid, []):
                    compositions.append({
                        "f": f,
                        "g": g,
                        "composite": {
                            "source": f["source"],
                            "target": g["target"],
                            "type": f"{f['type']}_compose_{g['type']}",
                        }
                    })
        return {
            "objects": objects,
            "morphism_count": len(morphisms),
            "compositions_count": len(compositions),
            "morphisms": morphisms[:50],
            "compositions": compositions[:50],
        }

    def get_unified_report(self) -> Dict[str, Any]:
        """Generate a complete unified report across all 5 levels."""
        return {
            "chain_level": {
                "top_chains": self.get_chains()[:10],
            },
            "network_level": self.get_network_stats(),
            "field_level": {
                "field_distribution_mean": float(self.get_field_distribution().mean()),
                "field_distribution_std": float(self.get_field_distribution().std()),
            },
            "spectrum_level": self.get_spectrum(),
            "domain_level": {
                "object_count": len(self.engine.node_ids),
                "morphism_count": self.get_domain_structure()["morphism_count"],
            },
        }


# =============================================================================
# 10. Main Relation Discovery Engine Orchestrator
# =============================================================================

class RelationDiscoveryEngine:
    """
    主控引擎 — 整合全部8种关系发现、自推演、互计算、统一场注入。
    """

    def __init__(self, node_ids: List[str]) -> None:
        self.node_ids = node_ids
        self.inference_engine = SelfInferenceEngine(node_ids)
        self.mutual_protocol = MutualComputationProtocol(self.inference_engine)
        self.unified_structure = UnifiedRelationStructure(self.inference_engine)
        self.field_injector = UnifiedFieldInjector()
        self.relations: List[Relation] = []
        self.field_state: UnifiedFieldState = UnifiedFieldState()

    def discover_all_relations(self, node_data: Dict[str, Dict[str, Any]]) -> List[Relation]:
        """
        Discover all 8 relation types between all node pairs.
        node_data: {node_id: {"embedding": np.array, "structure": np.array, ...}}
        """
        all_relations: List[Relation] = []
        nodes = list(node_data.keys())

        for i, nid_a in enumerate(nodes):
            for j, nid_b in enumerate(nodes):
                data_a = node_data[nid_a]
                data_b = node_data[nid_b]
                emb_a = data_a.get("embedding", np.zeros(64))
                emb_b = data_b.get("embedding", np.zeros(64))
                struct_a = data_a.get("structure", np.zeros((4, 4)))
                struct_b = data_b.get("structure", np.zeros((4, 4)))

                for rt in RelationType.all_types():
                    # Skip self-pairs for all relation types except SYMMETRY
                    if i == j and rt != RelationType.SYMMETRY:
                        continue
                    if i != j and rt == RelationType.SYMMETRY:
                        continue
                    rel = self._compute_typed_relation(
                        rt, nid_a, nid_b, emb_a, emb_b, struct_a, struct_b,
                        data_a, data_b
                    )
                    if rel.strength > 0.05:
                        all_relations.append(rel)
                        self.inference_engine.add_relation(rel)
                        self.field_injector.inject_relation(rel, self.field_state)

        self.relations = all_relations
        return all_relations

    def _compute_typed_relation(self, rt: RelationType,
                                 a: str, b: str,
                                 emb_a: np.ndarray, emb_b: np.ndarray,
                                 struct_a: np.ndarray, struct_b: np.ndarray,
                                 data_a: Dict[str, Any], data_b: Dict[str, Any]) -> Relation:
        """Compute a relation of specific type with appropriate algorithm."""
        rel = RelationFactory.create(rt, a, b)

        if isinstance(rel, CouplingRelation):
            rel.compute_from_embeddings(emb_a, emb_b)
            # Transfer entropy if time series available
            ts_a = data_a.get("time_series")
            ts_b = data_b.get("time_series")
            if ts_a is not None and ts_b is not None:
                rel.compute_transfer_entropy(np.array(ts_a), np.array(ts_b))

        elif isinstance(rel, EmbeddingRelation):
            rel.compute_from_matrices(struct_a, struct_b)

        elif isinstance(rel, EquivalenceRelation):
            rel.compute_from_features(emb_a, emb_b)
            inv_a = data_a.get("invariants")
            inv_b = data_b.get("invariants")
            if inv_a and inv_b:
                rel.compute_from_graph_invariants(inv_a, inv_b)

        elif isinstance(rel, SymmetryRelation):
            rel.compute_from_adjacency(struct_a)
            orbits = data_a.get("orbits")
            if orbits:
                rel.compute_from_node_orbits(list(data_a.get("labels", [])), orbits)

        elif isinstance(rel, DualityRelation):
            rel.compute_categorical_duality(struct_a, struct_b)
            betti_a = data_a.get("betti_numbers", [])
            betti_b = data_b.get("betti_numbers", [])
            if betti_a and betti_b:
                rel.compute_poincare_duality(betti_a, betti_b, 3)

        elif isinstance(rel, EntailmentRelation):
            rel.compute_from_semantic_vectors(emb_a, emb_b)
            proof_depth = data_a.get("proof_depth", 0)
            axioms_a = set(data_a.get("axioms", []))
            axioms_b = set(data_b.get("axioms", []))
            if axioms_b:
                rel.compute_from_proof_structure(proof_depth, axioms_a, axioms_b)

        elif isinstance(rel, DependencyRelation):
            dag = data_a.get("dependency_dag", {})
            if dag:
                rel.compute_from_dag(dag, a, b)
            else:
                # Fallback: weak dependency based on embedding similarity
                sim = float(np.dot(emb_a, emb_b) / (norm(emb_a) * norm(emb_b) + 1e-12))
                rel.strength = sim * 0.3
                rel.dependency_depth = 1

        elif isinstance(rel, BridgingRelation):
            domain_a = data_a.get("domain", "generic")
            domain_b = data_b.get("domain", "generic")
            rel.compute_cross_domain(struct_a, struct_b, domain_a, domain_b)
            mappings = data_a.get("concept_mappings", {})
            if mappings:
                concepts_a = data_a.get("concepts", [])
                concepts_b = data_b.get("concepts", [])
                rel.compute_from_concept_mapping(concepts_a, concepts_b, mappings)

        # Create field projection
        self.field_injector.create_relation_field_projection(rel)
        return rel

    def run_self_inference(self) -> Dict[str, Any]:
        """Run full self-inference suite."""
        return self.inference_engine.run_full_inference()

    def run_mutual_computation(self, concept_embeddings: Dict[str, np.ndarray],
                                target_structure: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run mutual computation cycle."""
        return self.mutual_protocol.run_cycle(concept_embeddings, target_structure)

    def get_unified_field_state(self) -> UnifiedFieldState:
        """Get current unified field state with all relations injected."""
        return self.field_injector.inject_engine_state(self.inference_engine)

    def get_unified_structure_report(self) -> Dict[str, Any]:
        """Get unified chain-network-field-spectrum-domain report."""
        return self.unified_structure.get_unified_report()

    def export_state(self) -> Dict[str, Any]:
        """Export complete engine state as dictionary."""
        return {
            "node_ids": self.node_ids,
            "relation_count": len(self.relations),
            "relations": [r.to_dict() for r in self.relations[:100]],
            "field_state": self.field_state.to_dict(),
            "inference_report": self.run_self_inference(),
            "unified_structure": self.get_unified_structure_report(),
            "timestamp": time.time(),
        }


# =============================================================================
# 11. Test Harness (__main__)
# =============================================================================

def _create_test_nodes() -> Tuple[List[KNode], Dict[str, Dict[str, Any]]]:
    """Create test knowledge nodes with synthetic data."""
    np.random.seed(42)
    nodes: List[KNode] = []
    node_data: Dict[str, Dict[str, Any]] = {}

    # Define 6 test concepts across 3 domains
    concepts = [
        ("group_theory", "math", np.array([1.0, 0.8, 0.2, 0.1, 0.0, 0.0, 0.1, 0.0] * 8)),
        ("ring_theory", "math", np.array([0.9, 1.0, 0.3, 0.2, 0.0, 0.0, 0.1, 0.0] * 8)),
        ("field_theory", "math", np.array([0.8, 0.9, 1.0, 0.3, 0.0, 0.0, 0.1, 0.0] * 8)),
        ("quantum_state", "physics", np.array([0.1, 0.0, 0.0, 0.2, 1.0, 0.9, 0.8, 0.7] * 8)),
        ("wave_function", "physics", np.array([0.1, 0.0, 0.0, 0.1, 0.9, 1.0, 0.8, 0.8] * 8)),
        ("hilbert_space", "physics", np.array([0.2, 0.1, 0.0, 0.3, 0.8, 0.9, 1.0, 0.9] * 8)),
    ]

    # Cross-domain concept mappings for bridging detection
    cross_mappings: Dict[str, str] = {
        "group_theory": "quantum_state",
        "ring_theory": "wave_function",
        "field_theory": "hilbert_space",
        "quantum_state": "group_theory",
        "wave_function": "ring_theory",
        "hilbert_space": "field_theory",
    }

    for label, domain, embedding in concepts:
        nid = f"node_{label}"
        node = KNode(
            node_id=nid,
            label=label,
            node_type="concept",
            module="test",
            embedding=embedding[:64].astype(np.float64),
        )
        nodes.append(node)
        # Structure matrix (4x4 adjacency-like)
        # Use highly symmetric structure for better symmetry detection
        base = np.ones((4, 4)) * 0.5
        np.fill_diagonal(base, 0)
        # Add domain-specific pattern for bridging detection
        if domain == "math":
            base[0, 1] = base[1, 0] = 0.9
            base[2, 3] = base[3, 2] = 0.9
        else:
            base[0, 2] = base[2, 0] = 0.9
            base[1, 3] = base[3, 1] = 0.9
        struct = base
        node_data[nid] = {
            "embedding": embedding[:64].astype(np.float64),
            "structure": struct,
            "domain": domain,
            "concepts": [label, f"related_{label}", cross_mappings.get(label, "")],
            "concept_mappings": {label: cross_mappings.get(label, f"mapped_{label}")},
            "invariants": {"order": np.random.randint(1, 100), "genus": np.random.randint(0, 5)},
            "betti_numbers": [1, np.random.randint(0, 3), np.random.randint(0, 2)],
            "axioms": [f"axiom_{domain}_1", f"axiom_{domain}_2"],
            "proof_depth": np.random.randint(1, 5),
            "dependency_dag": {
                nid: [f"node_{concepts[(i + 1) % len(concepts)][0]}"]
                for i, (lbl, _, _) in enumerate(concepts) if lbl == label
            },
        }

    return nodes, node_data


def main() -> None:
    """Main test harness for the Relation Discovery Engine."""
    print("=" * 80)
    print("OMNI-HUB v11.0 — Relation Discovery Engine Test Harness")
    print("=" * 80)
    print()

    # 1. Create test data
    print("[1/6] Creating test knowledge nodes...")
    nodes, node_data = _create_test_nodes()
    node_ids = [n.node_id for n in nodes]
    print(f"      Created {len(nodes)} test nodes")
    for n in nodes:
        print(f"        - {n.node_id}: {n.label} ({n.node_type})")
    print()

    # 2. Initialize engine
    print("[2/6] Initializing RelationDiscoveryEngine...")
    engine = RelationDiscoveryEngine(node_ids)
    print(f"      Engine initialized with {len(node_ids)} nodes")
    print()

    # 3. Discover all 8 relation types
    print("[3/6] Discovering all 8 relation types...")
    relations = engine.discover_all_relations(node_data)
    print(f"      Discovered {len(relations)} relations total")
    # Count by type
    type_counts: Dict[str, int] = defaultdict(int)
    for rel in relations:
        type_counts[rel.rel_type.name] += 1
    for rt_name, count in sorted(type_counts.items()):
        print(f"        - {rt_name}: {count}")
    print()

    # 4. Run self-inference
    print("[4/6] Running self-inference engine...")
    inference_report = engine.run_self_inference()
    print(f"      Transitive closure density: {inference_report['transitive_closure_density']:.4f}")
    print(f"      Cycle count: {inference_report['cycle_count']}")
    print(f"      Inferred relations: {inference_report['inferred_count']}")
    print(f"      Betti numbers: {inference_report['betti_numbers']}")
    print(f"      Spectral gap: {inference_report['spectral_gap']:.6f}")
    print(f"      Field coherence: {inference_report['field_coherence']:.4f}")
    print()

    # 5. Run mutual computation
    print("[5/6] Running mutual computation protocol...")
    concept_embeddings = {nid: data["embedding"] for nid, data in node_data.items()}
    target_structure = {"desired_density": 0.5, "desired_cycles": 3}
    mc_result = engine.run_mutual_computation(concept_embeddings, target_structure)
    print(f"      Forward drive relations: {mc_result['forward']['relation_count']}")
    if mc_result.get('reverse'):
        print(f"      Reverse match score: {mc_result['reverse']['match_score']:.4f}")
    print(f"      Excitation loops detected: {len(mc_result['excitation']['excitation_loops'])}")
    print(f"      Converged: {mc_result['excitation']['converged']}")
    print()

    # 6. Unified field injection
    print("[6/6] Unified field state injection...")
    field_state = engine.get_unified_field_state()
    print(f"      Field timestamp: {field_state.timestamp}")
    print(f"      Field dimensions: {field_state.dimensions}")
    print(f"      Non-zero dimensions: {sum(1 for v in field_state.vector if v > 0.01)}")
    # Show key dimensions
    key_dims = [
        DimensionIndex.DIM_CORRELATION,
        DimensionIndex.DIM_MUTUAL_INFO,
        DimensionIndex.DIM_ENTAILMENT,
        DimensionIndex.DIM_TOPOLOGY,
        DimensionIndex.DIM_COHERENCE,
        DimensionIndex.DIM_UNIFICATION,
    ]
    for dim in key_dims:
        print(f"        - {dim.name}: {field_state.get(dim):.4f}")
    print()

    # 7. Unified structure report
    print("[BONUS] Unified Chain-Network-Field-Spectrum-Domain Report...")
    report = engine.get_unified_structure_report()
    print(f"      Network: {report['network_level']}")
    print(f"      Spectrum gap: {report['spectrum_level']['spectral_gap']:.6f}")
    print(f"      Field mean: {report['field_level']['field_distribution_mean']:.4f}")
    print(f"      Domain morphisms: {report['domain_level']['morphism_count']}")
    print()

    # 8. Field projection test
    print("[BONUS] Field projection vector test...")
    if relations:
        rel = relations[0]
        proj = UnifiedFieldInjector.create_relation_field_projection(rel)
        print(f"      Relation type: {rel.rel_type.name}")
        print(f"      Primary dim value: {proj[UnifiedFieldInjector.RELATION_DIMENSION_MAP[rel.rel_type].value]:.4f}")
        print(f"      Projection non-zero count: {np.count_nonzero(proj)}")
    print()

    print("=" * 80)
    print("All tests completed successfully.")
    print("=" * 80)

    # Export state
    state = engine.export_state()
    print(f"\nExported state keys: {list(state.keys())}")
    print(f"Total relations in state: {state['relation_count']}")


if __name__ == "__main__":
    main()
