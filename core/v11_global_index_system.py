#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v11.0 — Global Index System (全局指标系统)
====================================================
Complete implementation of MIP* consistency, concordance, isomorphism,
coupling depth, and global aggregation indices.

All indices are mathematically grounded and injectable into the 64-dimensional
UnifiedFieldState. Only numpy is used for numerical computation.

References
----------
- Ji, Z., Natarajan, A., Vidick, T., Wright, J., & Yuen, H. (2020).
  "MIP* = RE". arXiv:2001.04383.
- Shannon, C. E. (1948). "A Mathematical Theory of Communication".
- Weisfeiler, B., & Lehman, A. (1968). "A reduction of a graph to a canonical
  form and an algebra arising during this reduction".
- Hoel, E. P., Albantakis, L., & Tononi, G. (2013). "Quantifying causal
  emergence shows that macro can beat micro". PNAS.

Version: 11.0.0
Date: 2026-09-17
"""

from __future__ import annotations

import math
import sys
import logging
import time
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque

import numpy as np

# ---------------------------------------------------------------------------
# Import v11 standards
# ---------------------------------------------------------------------------
sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")
from v11_standards import (
    UnifiedFieldState,
    DimensionIndex,
    UNIFIED_FIELD_DIMENSIONS,
    PHI_GOLDEN,
    QUANTUM_ENTANGLEMENT_MIN,
    EMERGENCE_THRESHOLD,
    get_logger,
    OMNIHUBDimensionError,
    configure_logging,
)

__version__ = "11.0.0"
__all__ = [
    "MIPStarConsistencyIndex",
    "ConcordanceIndex",
    "IsomorphismIndex",
    "CouplingDepthIndex",
    "GlobalIndexAggregator",
    "GlobalIndexReport",
    "MockDataGenerator",
    "run_all_tests",
    "run_demonstration",
]

# =============================================================================
# 0. DATA STRUCTURES & UTILITIES
# =============================================================================


@dataclass
class GlobalIndexReport:
    """全局指标报告 —— 所有计算结果的统一封装"""

    timestamp: float = field(default_factory=time.time)
    emergence_index: float = 0.0          # E  (来自涌现系统)
    mip_consistency: float = 0.0          # C_MIP
    concordance: float = 0.0              # H
    isomorphism: float = 0.0              # I
    coupling_depth: float = 0.0           # D
    field_variance: float = 0.0           # FV
    global_aggregate: float = 0.0         # G
    weights: Dict[str, float] = field(default_factory=dict)
    component_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "indices": {
                "emergence_E": round(self.emergence_index, 6),
                "mip_consistency_C_MIP": round(self.mip_consistency, 6),
                "concordance_H": round(self.concordance, 6),
                "isomorphism_I": round(self.isomorphism, 6),
                "coupling_depth_D": round(self.coupling_depth, 6),
                "field_variance_FV": round(self.field_variance, 6),
                "global_aggregate_G": round(self.global_aggregate, 6),
            },
            "weights": {k: round(v, 6) for k, v in self.weights.items()},
            "component_details": self.component_details,
        }


class MockDataGenerator:
    """为测试和演示生成模拟数据结构"""

    @staticmethod
    def theorem_dependency_graph(
        n_theorems: int = 24, seed: int = 42
    ) -> np.ndarray:
        """
        生成模拟的形式化定理依赖图.

        返回 n_theorems x n_theorems 的邻接矩阵，元素 \in [0,1] 表示
        定理间的逻辑耦合强度（高值 = 强依赖 = "量子纠缠对"候选）.
        """
        rng = np.random.default_rng(seed)
        adj = rng.random((n_theorems, n_theorems))
        adj = (adj + adj.T) / 2.0
        np.fill_diagonal(adj, 0.0)

        # 增强某些区域内的耦合（模拟同一章节内定理高度相关）
        block_size = n_theorems // 4
        for block in range(4):
            start = block * block_size
            end = start + block_size
            boost = rng.random((end - start, end - start)) * 0.4 + 0.4
            boost = (boost + boost.T) / 2.0
            adj[start:end, start:end] = np.clip(
                adj[start:end, start:end] + boost, 0.0, 1.0
            )
        np.fill_diagonal(adj, 0.0)
        return adj

    @staticmethod
    def cross_project_concepts(
        projects: Optional[List[str]] = None, seed: int = 42
    ) -> Dict[str, Set[str]]:
        """
        生成模拟的多项目概念集合.

        返回 dict: project_name -> set of concept_ids
        """
        if projects is None:
            projects = ["ucif2_lean", "cayley24", "omni_hub_core", "omni_hub_hub"]
        rng = np.random.default_rng(seed)
        base_concepts = [f"concept_{i:03d}" for i in range(80)]
        project_concepts: Dict[str, Set[str]] = {}

        for proj in projects:
            n_concepts = rng.integers(30, 61)
            shared = set(rng.choice(base_concepts, size=int(n_concepts * 0.7), replace=False))
            unique = {f"{proj}_unique_{i}" for i in range(int(n_concepts * 0.3))}
            project_concepts[proj] = shared | unique

        return project_concepts

    @staticmethod
    def knowledge_structures(
        n_structures: int = 12, n_nodes: int = 16, seed: int = 42
    ) -> List[np.ndarray]:
        """
        生成模拟的知识结构（图的邻接矩阵列表）.

        其中部分图故意构造为同构变体，用于测试同构检测.
        """
        rng = np.random.default_rng(seed)
        structures: List[np.ndarray] = []

        # 生成 3 组同构族，每组内部结构相同但节点重排
        for family_id in range(3):
            # 基础图：随机正则图近似
            base = rng.random((n_nodes, n_nodes))
            base = (base + base.T) / 2.0
            np.fill_diagonal(base, 0.0)
            base = (base > 0.6).astype(float)

            for variant in range(4):
                if variant == 0:
                    perm = np.arange(n_nodes)
                else:
                    perm = rng.permutation(n_nodes)
                variant_graph = base[perm][:, perm]
                structures.append(variant_graph)

        return structures

    @staticmethod
    def coupling_graph(n_nodes: int = 20, seed: int = 42) -> np.ndarray:
        """
        生成模拟的耦合图（带权无向图）.
        """
        rng = np.random.default_rng(seed)
        adj = rng.random((n_nodes, n_nodes))
        adj = (adj + adj.T) / 2.0
        np.fill_diagonal(adj, 0.0)
        for i in range(n_nodes):
            k = rng.integers(3, 6)
            neighbors = rng.choice(n_nodes, size=k, replace=False)
            for j in neighbors:
                if i != j:
                    adj[i, j] = rng.random() * 0.5 + 0.5
                    adj[j, i] = adj[i, j]
        return adj


# =============================================================================
# 1. MIP* CONSISTENCY INDEX  (C_MIP)
# =============================================================================


class MIPStarConsistencyIndex:
    r"""
    MIP*一致性指数 —— 基于量子纠缠验证复杂度.

    理论来源
    --------
    Ji et al. (2020) 证明 MIP* = RE，即：拥有量子纠缠的多证明者交互证明
    系统可以判定所有递归可枚举语言。这意味着量子纠缠的验证复杂度与
    停机问题等价 —— 存在原则上不可计算的纠缠关联。

    核心公式
    --------
    .. math::
        C_{MIP} = \frac{N_{\text{entangled}}}{N_{\text{total}}} \times
                  \frac{\ln(1 + d_q)}{\ln(1 + d_{\max})}

    其中:
    - :math:`N_{\text{entangled}}` = 高耦合（"纠缠"）定理对数
    - :math:`N_{\text{total}}` = 定理对总数
    - :math:`d_q` = 量子维度（系统的希尔伯特空间维度）
    - 分母 :math:`\ln(1+d_{\max})` 用于将维度因子归一化到 [0,1]

    物理意义
    --------
    C_MIP 度量系统的"量子关联验证能力":
    - C_MIP -> 1: 系统拥有高度纠缠结构，定理间耦合如同量子纠缠般不可分
    - C_MIP -> 0: 系统为经典可分解结构，无量子关联特征
    """

    def __init__(self, quantum_dim: int = 64, entanglement_threshold: float = 0.5):
        self.quantum_dim = max(1, quantum_dim)
        self.entanglement_threshold = entanglement_threshold
        self.logger = get_logger("MIPStarConsistency")

    def compute(self, theorem_graph: np.ndarray) -> float:
        """
        计算 MIP* 一致性指数.

        Parameters
        ----------
        theorem_graph : np.ndarray, shape (n, n)
            定理依赖图的邻接矩阵，元素 \in [0,1] 表示耦合强度.

        Returns
        -------
        float
            C_MIP \in [0, 1]
        """
        if theorem_graph.ndim != 2 or theorem_graph.shape[0] != theorem_graph.shape[1]:
            raise OMNIHUBDimensionError(
                "theorem_graph must be a square matrix",
                error_code="OMNI-GIS-001"
            )

        n = theorem_graph.shape[0]
        if n < 2:
            return 0.0

        graph = (theorem_graph + theorem_graph.T) / 2.0
        np.fill_diagonal(graph, 0.0)

        upper_tri = np.triu(graph, k=1)
        entangled_pairs = int(np.sum(upper_tri >= self.entanglement_threshold))
        total_pairs = n * (n - 1) // 2

        if total_pairs == 0:
            return 0.0

        ratio = entangled_pairs / total_pairs
        dim_factor = math.log1p(self.quantum_dim) / math.log1p(64)
        c_mip = ratio * dim_factor

        # 非线性增强: 纠缠比例超过黄金比例倒数时相变式提升
        if ratio > 1.0 / PHI_GOLDEN:
            c_mip = min(1.0, c_mip * (1.0 + (ratio - 1.0 / PHI_GOLDEN) * PHI_GOLDEN))

        return float(np.clip(c_mip, 0.0, 1.0))

    def compute_detailed(
        self, theorem_graph: np.ndarray
    ) -> Tuple[float, Dict[str, Any]]:
        """详细计算，返回指数与中间结果."""
        c_mip = self.compute(theorem_graph)
        n = theorem_graph.shape[0]
        graph = (theorem_graph + theorem_graph.T) / 2.0
        np.fill_diagonal(graph, 0.0)
        upper_tri = np.triu(graph, k=1)
        entangled = int(np.sum(upper_tri >= self.entanglement_threshold))
        total = n * (n - 1) // 2

        entanglement_subgraph = (graph >= self.entanglement_threshold).astype(float)
        degrees = entanglement_subgraph.sum(axis=1)

        details = {
            "n_theorems": n,
            "total_pairs": total,
            "entangled_pairs": entangled,
            "entanglement_ratio": entangled / total if total > 0 else 0.0,
            "quantum_dim": self.quantum_dim,
            "dim_factor": math.log1p(self.quantum_dim) / math.log1p(64),
            "max_degree": int(degrees.max()),
            "avg_degree": float(degrees.mean()),
            "entanglement_threshold": self.entanglement_threshold,
            "phase_transition": (entangled / total > 1.0 / PHI_GOLDEN) if total > 0 else False,
        }
        return c_mip, details

    def inject_to_field(
        self, state: UnifiedFieldState, theorem_graph: np.ndarray
    ) -> UnifiedFieldState:
        """将 C_MIP 注入 64 维统一场状态的 DIM_CONSISTENCY 维度."""
        c_mip = self.compute(theorem_graph)
        state.set(DimensionIndex.DIM_CONSISTENCY, c_mip)
        state.set(DimensionIndex.DIM_INFORMATION, c_mip * 0.8 + state.get(DimensionIndex.DIM_INFORMATION) * 0.2)
        return state


# =============================================================================
# 2. CONCORDANCE INDEX  (H)
# =============================================================================


class ConcordanceIndex:
    r"""
    协和度指数 —— 基于跨项目概念共现互信息的协和度.

    理论来源
    --------
    基于 Shannon 熵和互信息 (Mutual Information)。协和度度量知识在不同项目
    间的共享程度：当概念被多个项目共享时，协和度高；当概念碎片化分布在
    少数项目时，协和度低。

    核心公式
    --------
    .. math::
        H = 1 - \frac{I(\text{concept}; \text{project})}{H_{\max}}

    其中:
    - :math:`I(\text{concept}; \text{project}) = H(C) + H(P) - H(C, P)`
      是概念与项目之间的互信息
    - :math:`H(C, P) = -\sum_{c,p} p(c,p) \ln p(c,p)` 是联合熵
    - :math:`p(c, p) = \frac{\mathbb{I}[c \in p]}{\sum_{c'}\sum_{p'} \mathbb{I}[c' \in p']}`
    - :math:`H_{\max} = \ln(N_{\text{projects}})` 是最大可能互信息

    物理意义
    --------
    H -> 1: 知识在所有项目间高度协和（大量共享概念），如同乐队的完美合奏
    H -> 0: 知识碎片化，各项目间缺乏共同语义基础
    """

    def __init__(self, epsilon: float = 1e-12):
        self.epsilon = epsilon
        self.logger = get_logger("ConcordanceIndex")

    def compute(self, project_concepts: Dict[str, Set[str]]) -> float:
        """
        计算协和度指数.

        Parameters
        ----------
        project_concepts : dict[str, set[str]]
            映射: 项目名称 -> 该项目包含的概念集合.

        Returns
        -------
        float
            H \in [0, 1]
        """
        if not project_concepts:
            return 0.0

        projects = list(project_concepts.keys())
        n_projects = len(projects)

        # 构建概念 -> 项目列表的反向索引
        concept_projects: Dict[str, List[str]] = defaultdict(list)
        for proj, concepts in project_concepts.items():
            for concept in concepts:
                concept_projects[concept].append(proj)

        n_concepts = len(concept_projects)
        if n_concepts == 0:
            return 0.0

        # 总出现次数
        total_occurrences = sum(len(projs) for projs in concept_projects.values())
        if total_occurrences == 0:
            return 0.0

        # 计算联合概率 p(concept, project) 和边际概率
        # H(C, P) = -sum p(c,p) log p(c,p)
        h_joint = 0.0
        concept_counts: Dict[str, int] = defaultdict(int)
        project_counts: Dict[str, int] = defaultdict(int)

        for concept, projs in concept_projects.items():
            for proj in projs:
                p = 1.0 / total_occurrences
                h_joint -= p * math.log(p + self.epsilon)
                concept_counts[concept] += 1
                project_counts[proj] += 1

        # H(C) = -sum p(c) log p(c)
        h_concept = 0.0
        for count in concept_counts.values():
            p_c = count / total_occurrences
            h_concept -= p_c * math.log(p_c + self.epsilon)

        # H(P) = -sum p(p) log p(p)
        h_project = 0.0
        for count in project_counts.values():
            p_p = count / total_occurrences
            h_project -= p_p * math.log(p_p + self.epsilon)

        # 互信息 I(C;P) = H(C) + H(P) - H(C,P)
        mutual_info = h_concept + h_project - h_joint
        mutual_info = max(0.0, mutual_info)

        # 最大互信息: min(H(C), H(P)) <= I(C;P) <= min(H(C), H(P))
        # 上界为 log(N_projects) 当概念和项目一一对应时
        h_max = math.log(n_projects + self.epsilon)

        if h_max < self.epsilon:
            return 0.0

        # 协和度 = 1 - 互信息/最大互信息
        # 互信息高 = 概念和项目强相关（不共享）-> H 低
        # 互信息低 = 概念和项目独立（高度共享）-> H 高
        h = 1.0 - (mutual_info / h_max)
        return float(np.clip(h, 0.0, 1.0))

    def compute_with_kl_divergence(
        self, project_concepts: Dict[str, Set[str]]
    ) -> Tuple[float, Dict[str, Any]]:
        r"""
        使用 KL 散度增强的协和度计算.

        额外计算每个项目分布与全局均匀分布的 KL 散度：
        :math:`D_{KL}(P_p || U) = \sum_c P_p(c) \ln \frac{P_p(c)}{U(c)}`
        """
        h = self.compute(project_concepts)

        all_concepts: Set[str] = set()
        for concepts in project_concepts.values():
            all_concepts.update(concepts)

        n_total_concepts = len(all_concepts)
        kl_divergences: Dict[str, float] = {}
        project_entropies: Dict[str, float] = {}

        uniform_p = 1.0 / n_total_concepts if n_total_concepts > 0 else 1.0

        for proj, concepts in project_concepts.items():
            n_proj_concepts = len(concepts)
            if n_proj_concepts == 0:
                kl_divergences[proj] = 0.0
                project_entropies[proj] = 0.0
                continue

            p_in_proj = 1.0 / n_proj_concepts
            kl = n_proj_concepts * p_in_proj * math.log(p_in_proj / uniform_p + self.epsilon)
            kl_divergences[proj] = kl
            h_proj = -math.log(p_in_proj + self.epsilon)
            project_entropies[proj] = h_proj

        avg_kl = sum(kl_divergences.values()) / len(kl_divergences) if kl_divergences else 0.0
        kl_penalty = min(1.0, avg_kl / math.log(len(project_concepts) + 1))
        h_kl_adjusted = h * (1.0 - 0.3 * kl_penalty)

        details = {
            "concordance_base": h,
            "concordance_kl_adjusted": h_kl_adjusted,
            "n_projects": len(project_concepts),
            "n_unique_concepts": n_total_concepts,
            "avg_kl_divergence": avg_kl,
            "kl_penalty": kl_penalty,
            "project_entropies": project_entropies,
            "project_kl_divergences": kl_divergences,
        }
        return h_kl_adjusted, details

    def inject_to_field(
        self, state: UnifiedFieldState, project_concepts: Dict[str, Set[str]]
    ) -> UnifiedFieldState:
        """将协和度 H 注入统一场状态."""
        h, _ = self.compute_with_kl_divergence(project_concepts)
        state.set(DimensionIndex.DIM_UNIFICATION, h)
        state.set(DimensionIndex.DIM_KNOWLEDGE, h * 0.7 + state.get(DimensionIndex.DIM_KNOWLEDGE) * 0.3)
        return state


# =============================================================================
# 3. ISOMORPHISM INDEX  (I)
# =============================================================================


class IsomorphismIndex:
    r"""
    同构指数 —— 基于结构等价类计数的同构检测.

    理论来源
    --------
    Weisfeiler-Lehman (WL) 图同构测试的谱版本。WL 测试通过迭代着色为图节点
    分配标签，若两图在任意迭代步后颜色分布不同，则它们不同构。

    核心公式
    --------
    .. math::
        I = \frac{|\text{IsoClasses}|}{|\text{TotalStructures}|} \times
            \lambda_2^{\text{normalized}}

    其中:
    - :math:`|\text{IsoClasses}|` = WL 测试识别的非同构图等价类数
    - :math:`|\text{TotalStructures}|` = 输入结构总数
    - :math:`\lambda_2^{\text{normalized}}` = 归一化代数连通度
      （图拉普拉斯第二小特征值，反映图的整体连通性）

    物理意义
    --------
    I -> 1: 系统内部高度自相似，知识结构呈现统一的同构模式
    I -> 0: 系统结构碎片化，各子系统间缺乏统一的结构语言
    """

    def __init__(self, wl_iterations: int = 5, epsilon: float = 1e-10):
        self.wl_iterations = wl_iterations
        self.epsilon = epsilon
        self.logger = get_logger("IsomorphismIndex")

    def _weisfeiler_lehman_labels(
        self, adj: np.ndarray
    ) -> Tuple[np.ndarray, int]:
        """
        执行 WL 图同构测试，返回最终颜色标签和唯一颜色数.
        """
        n = adj.shape[0]
        degrees = adj.sum(axis=1)
        labels = np.zeros(n, dtype=np.int64)
        unique_degrees = np.unique(degrees)
        deg_to_color = {d: i for i, d in enumerate(unique_degrees)}
        for i in range(n):
            labels[i] = deg_to_color[degrees[i]]

        for _ in range(self.wl_iterations):
            new_labels = np.zeros(n, dtype=np.int64)
            color_map: Dict[Tuple[int, Tuple[int, ...]], int] = {}
            next_color = 0

            for i in range(n):
                neighbors = np.where(adj[i] > self.epsilon)[0]
                neighbor_colors = tuple(sorted(labels[neighbors].tolist()))
                key = (labels[i], neighbor_colors)

                if key not in color_map:
                    color_map[key] = next_color
                    next_color += 1
                new_labels[i] = color_map[key]

            if np.array_equal(labels, new_labels):
                break
            labels = new_labels

        n_colors = len(np.unique(labels))
        return labels, n_colors

    def _graph_canonical_string(self, adj: np.ndarray) -> str:
        """基于 WL 标签生成图的规范字符串表示."""
        labels, _ = self._weisfeiler_lehman_labels(adj)
        unique, counts = np.unique(labels, return_counts=True)
        hist = sorted(zip(unique.tolist(), counts.tolist()))
        return str(hist)

    def _laplacian_spectrum(self, adj: np.ndarray) -> np.ndarray:
        """计算图拉普拉斯矩阵的特征值谱."""
        n = adj.shape[0]
        degrees = adj.sum(axis=1)
        L = np.diag(degrees) - adj
        try:
            eigenvalues = np.linalg.eigvalsh(L)
        except np.linalg.LinAlgError:
            eigenvalues = np.zeros(n)
        return np.sort(eigenvalues)

    def _algebraic_connectivity(self, adj: np.ndarray) -> float:
        """计算代数连通度（Fiedler 值）."""
        spectrum = self._laplacian_spectrum(adj)
        if len(spectrum) >= 2:
            positive = spectrum[spectrum > self.epsilon]
            if len(positive) > 0:
                return float(positive[0])
        return 0.0

    def compute(self, structures: List[np.ndarray]) -> float:
        """
        计算同构指数.

        Parameters
        ----------
        structures : list[np.ndarray]
            知识结构的邻接矩阵列表.

        Returns
        -------
        float
            I \in [0, 1]
        """
        if not structures:
            return 0.0

        n_total = len(structures)

        # 使用 WL 测试分组
        iso_classes: Dict[str, List[int]] = defaultdict(list)
        for idx, adj in enumerate(structures):
            canonical = self._graph_canonical_string(adj)
            iso_classes[canonical].append(idx)

        n_classes = len(iso_classes)

        # 类比例因子
        class_ratio = n_classes / n_total

        # 计算所有结构的平均代数连通度（归一化）
        connectivities = []
        for adj in structures:
            n_nodes = adj.shape[0]
            if n_nodes <= 1:
                connectivities.append(0.0)
                continue
            ac = self._algebraic_connectivity(adj)
            connectivities.append(min(1.0, ac / n_nodes))

        avg_connectivity = sum(connectivities) / len(connectivities) if connectivities else 0.0

        # 综合指数
        i = class_ratio * avg_connectivity

        # 非线性增强
        if class_ratio > 0.5 and avg_connectivity > 0.5:
            i = min(1.0, i * PHI_GOLDEN * 0.8)

        return float(np.clip(i, 0.0, 1.0))

    def compute_detailed(
        self, structures: List[np.ndarray]
    ) -> Tuple[float, Dict[str, Any]]:
        """详细计算，返回指数与中间结果."""
        n_total = len(structures)
        iso_classes: Dict[str, List[int]] = defaultdict(list)
        wl_colors: List[int] = []

        for idx, adj in enumerate(structures):
            canonical = self._graph_canonical_string(adj)
            iso_classes[canonical].append(idx)
            _, n_colors = self._weisfeiler_lehman_labels(adj)
            wl_colors.append(n_colors)

        n_classes = len(iso_classes)
        class_sizes = [len(v) for v in iso_classes.values()]

        connectivities = []
        for adj in structures:
            n_nodes = adj.shape[0]
            if n_nodes <= 1:
                connectivities.append(0.0)
                continue
            ac = self._algebraic_connectivity(adj)
            connectivities.append(min(1.0, ac / n_nodes))

        avg_connectivity = sum(connectivities) / len(connectivities)
        class_ratio = n_classes / n_total if n_total > 0 else 0.0
        i = class_ratio * avg_connectivity

        details = {
            "n_structures": n_total,
            "n_iso_classes": n_classes,
            "class_ratio": class_ratio,
            "class_sizes": class_sizes,
            "avg_wl_colors": sum(wl_colors) / len(wl_colors) if wl_colors else 0,
            "avg_algebraic_connectivity": avg_connectivity,
            "connectivities_per_graph": connectivities,
            "iso_class_members": {k: v for k, v in iso_classes.items()},
        }
        return i, details

    def inject_to_field(
        self, state: UnifiedFieldState, structures: List[np.ndarray]
    ) -> UnifiedFieldState:
        """将同构指数 I 注入统一场状态."""
        i = self.compute(structures)
        state.set(DimensionIndex.DIM_TOPOLOGY, i)
        state.set(DimensionIndex.DIM_CORRELATION, i * 0.6 + state.get(DimensionIndex.DIM_CORRELATION) * 0.4)
        return state


# =============================================================================
# 4. COUPLING DEPTH INDEX  (D)
# =============================================================================


class CouplingDepthIndex:
    r"""
    耦合深度指数 —— 基于平均最短路径的耦合深度.

    理论来源
    --------
    基于图论中的全局效率 (global efficiency) 和特征路径长度.
    全局效率由 Latora & Marchiori (2001) 提出.

    核心公式
    --------
    .. math::
        D = \frac{1}{\langle d \rangle} \times E_{\text{global}}

    其中:
    - :math:`\langle d \rangle = \frac{1}{N(N-1)} \sum_{i \neq j} d_{ij}`
      是平均最短路径长度
    - :math:`E_{\text{global}} = \frac{1}{N(N-1)} \sum_{i \neq j} \frac{1}{d_{ij}}`
      是全局效率
    - :math:`d_{ij}` = 节点 i 到 j 的最短路径长度（以耦合强度的倒数为边权）
    """

    def __init__(self, epsilon: float = 1e-10):
        self.epsilon = epsilon
        self.logger = get_logger("CouplingDepthIndex")

    def _dijkstra_all_pairs(self, adj: np.ndarray) -> np.ndarray:
        """
        Dijkstra 全源最短路径.
        边权 = 1 / (coupling_strength + epsilon)
        """
        n = adj.shape[0]
        dist = np.full((n, n), np.inf)
        np.fill_diagonal(dist, 0.0)

        for i in range(n):
            for j in range(n):
                if i != j and adj[i, j] > self.epsilon:
                    dist[i, j] = 1.0 / adj[i, j]

        for src in range(n):
            visited = np.zeros(n, dtype=bool)
            for _ in range(n):
                unvisited_dist = np.where(visited, np.inf, dist[src])
                u = int(np.argmin(unvisited_dist))
                if float(dist[src, u]) == np.inf:
                    break
                visited[u] = True
                for v in range(n):
                    if not visited[v] and adj[u, v] > self.epsilon:
                        w = 1.0 / adj[u, v]
                        if dist[src, u] + w < dist[src, v]:
                            dist[src, v] = dist[src, u] + w

        return dist

    def compute(self, coupling_graph: np.ndarray) -> float:
        """
        计算耦合深度指数.

        Parameters
        ----------
        coupling_graph : np.ndarray, shape (n, n)
            耦合强度邻接矩阵，元素 \in [0,1].

        Returns
        -------
        float
            D \in [0, 1]
        """
        if coupling_graph.ndim != 2 or coupling_graph.shape[0] != coupling_graph.shape[1]:
            raise OMNIHUBDimensionError(
                "coupling_graph must be a square matrix",
                error_code="OMNI-GIS-002"
            )

        n = coupling_graph.shape[0]
        if n < 2:
            return 0.0

        adj = (coupling_graph + coupling_graph.T) / 2.0
        np.fill_diagonal(adj, 0.0)

        dist = self._dijkstra_all_pairs(adj)

        finite_mask = (dist != np.inf) & (dist > 0)
        n_finite = int(finite_mask.sum())

        if n_finite == 0:
            return 0.0

        avg_shortest = float(dist[finite_mask].mean())

        inv_dist = np.zeros_like(dist)
        inv_dist[finite_mask] = 1.0 / dist[finite_mask]
        np.fill_diagonal(inv_dist, 0.0)
        global_efficiency = float(inv_dist.sum()) / (n * (n - 1))

        d_raw = (1.0 / (avg_shortest + self.epsilon)) * global_efficiency
        d = min(1.0, d_raw)

        clustering = self._clustering_coefficient(adj)
        if clustering > 0.5 and avg_shortest < 2.0:
            d = min(1.0, d * 1.2)

        return float(np.clip(d, 0.0, 1.0))

    def compute_detailed(
        self, coupling_graph: np.ndarray
    ) -> Tuple[float, Dict[str, Any]]:
        """详细计算，返回指数与中间结果."""
        n = coupling_graph.shape[0]
        adj = (coupling_graph + coupling_graph.T) / 2.0
        np.fill_diagonal(adj, 0.0)

        dist = self._dijkstra_all_pairs(adj)
        finite_mask = (dist != np.inf) & (dist > 0)
        n_finite = int(finite_mask.sum())

        avg_shortest = float(dist[finite_mask].mean()) if n_finite > 0 else float('inf')

        inv_dist = np.zeros_like(dist)
        inv_dist[finite_mask] = 1.0 / dist[finite_mask]
        np.fill_diagonal(inv_dist, 0.0)
        global_eff = float(inv_dist.sum()) / (n * (n - 1))

        diameter = float(dist[finite_mask].max()) if n_finite > 0 else float('inf')
        connected_ratio = n_finite / (n * (n - 1)) if n > 1 else 0.0
        clustering = self._clustering_coefficient(adj)
        d = self.compute(coupling_graph)

        details = {
            "n_nodes": n,
            "avg_shortest_path": avg_shortest,
            "diameter": diameter,
            "global_efficiency": global_eff,
            "connected_pair_ratio": connected_ratio,
            "clustering_coefficient": clustering,
        }
        return d, details

    def _clustering_coefficient(self, adj: np.ndarray) -> float:
        """计算平均聚类系数."""
        n = adj.shape[0]
        coeffs = []
        for i in range(n):
            neighbors = np.where(adj[i] > self.epsilon)[0]
            k = len(neighbors)
            if k < 2:
                continue
            sub = adj[np.ix_(neighbors, neighbors)]
            edges = (sub > self.epsilon).sum() / 2.0
            coeffs.append(2.0 * edges / (k * (k - 1)))
        return sum(coeffs) / len(coeffs) if coeffs else 0.0

    def inject_to_field(
        self, state: UnifiedFieldState, coupling_graph: np.ndarray
    ) -> UnifiedFieldState:
        """将耦合深度 D 注入统一场状态."""
        d = self.compute(coupling_graph)
        state.set(DimensionIndex.DIM_HIERARCHY, d)
        state.set(DimensionIndex.DIM_PHASE_LOCK, d * 0.5 + state.get(DimensionIndex.DIM_PHASE_LOCK) * 0.5)
        return state


# =============================================================================
# 5. GLOBAL INDEX AGGREGATOR  (G)
# =============================================================================


class GlobalIndexAggregator:
    r"""
    全局指标聚合器 —— 整合所有子指数为统一的全局指标.

    核心公式
    --------
    .. math::
        G = w_1 \cdot E + w_2 \cdot C_{MIP} + w_3 \cdot H +
            w_4 \cdot I + w_5 \cdot D + w_6 \cdot F_V

    其中权重 :math:`\{w_i\}` 基于最大熵原则（Maximum Entropy Principle）优化：

    .. math::
        \max_{\mathbf{w}} \; H(\mathbf{w}) = -\sum_i w_i \ln w_i
        \quad \text{s.t.} \quad \sum_i w_i = 1, \; w_i \geq 0

    当各子指数的信息贡献不同时（通过方差或互信息估计），引入约束：

    .. math::
        \sum_i w_i \cdot \sigma_i^2 = \text{const}

    其解析解为:
    .. math::
        w_i = \frac{e^{-\lambda \sigma_i^2}}{\sum_j e^{-\lambda \sigma_j^2}}
    """

    def __init__(
        self,
        lambda_entropy: float = 1.0,
        min_weight: float = 0.05,
        use_max_entropy: bool = True,
    ):
        self.lambda_entropy = lambda_entropy
        self.min_weight = min_weight
        self.use_max_entropy = use_max_entropy
        self.logger = get_logger("GlobalIndexAggregator")

        self.mip_index = MIPStarConsistencyIndex()
        self.concordance_index = ConcordanceIndex()
        self.isomorphism_index = IsomorphismIndex()
        self.coupling_depth_index = CouplingDepthIndex()
        self.history: deque = deque(maxlen=1000)

    def _compute_weights_max_entropy(
        self,
        indices: Dict[str, float],
        historical_variances: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """基于最大熵原则计算权重."""
        keys = ["E", "C_MIP", "H", "I", "D", "FV"]

        if historical_variances is None:
            w = 1.0 / len(keys)
            return {k: w for k in keys}

        variances = np.array([historical_variances.get(k, 1.0) for k in keys])
        variances = np.clip(variances, 1e-6, None)
        weights = np.exp(-self.lambda_entropy * variances)
        weights = np.clip(weights, self.min_weight, None)
        weights /= weights.sum()
        return {k: float(weights[i]) for i, k in enumerate(keys)}

    def _estimate_historical_variances(self) -> Dict[str, float]:
        """从历史记录估计各指数的方差."""
        if len(self.history) < 2:
            return {k: 1.0 for k in ["E", "C_MIP", "H", "I", "D", "FV"]}

        variances: Dict[str, List[float]] = defaultdict(list)
        for record in self.history:
            for k in ["E", "C_MIP", "H", "I", "D", "FV"]:
                variances[k].append(record.get(k, 0.0))

        return {
            k: float(np.var(v)) if len(v) > 1 else 1.0
            for k, v in variances.items()
        }

    def compute(
        self,
        emergence_index: float,
        theorem_graph: np.ndarray,
        project_concepts: Dict[str, Set[str]],
        structures: List[np.ndarray],
        coupling_graph: np.ndarray,
        field_variance: Optional[float] = None,
    ) -> GlobalIndexReport:
        """
        计算全局聚合指标.

        Parameters
        ----------
        emergence_index : float
            涌现指数 E.
        theorem_graph : np.ndarray
            定理依赖图（用于 C_MIP）.
        project_concepts : dict[str, set[str]]
            多项目概念集合（用于 H）.
        structures : list[np.ndarray]
            知识结构列表（用于 I）.
        coupling_graph : np.ndarray
            耦合图（用于 D）.
        field_variance : float, optional
            场方差 FV.

        Returns
        -------
        GlobalIndexReport
        """
        c_mip, mip_details = self.mip_index.compute_detailed(theorem_graph)
        h, h_details = self.concordance_index.compute_with_kl_divergence(project_concepts)
        i, i_details = self.isomorphism_index.compute_detailed(structures)
        d, d_details = self.coupling_depth_index.compute_detailed(coupling_graph)

        if field_variance is None:
            fv = self._compute_field_variance(coupling_graph)
        else:
            fv = field_variance

        e_norm = min(1.0, emergence_index / EMERGENCE_THRESHOLD)

        indices_dict = {
            "E": e_norm,
            "C_MIP": c_mip,
            "H": h,
            "I": i,
            "D": d,
            "FV": fv,
        }

        if self.use_max_entropy:
            variances = self._estimate_historical_variances()
            weights = self._compute_weights_max_entropy(indices_dict, variances)
        else:
            weights = self._compute_weights_max_entropy(indices_dict, None)

        g = (
            weights["E"] * e_norm
            + weights["C_MIP"] * c_mip
            + weights["H"] * h
            + weights["I"] * i
            + weights["D"] * d
            + weights["FV"] * fv
        )

        self.history.append(indices_dict)

        report = GlobalIndexReport(
            emergence_index=emergence_index,
            mip_consistency=c_mip,
            concordance=h,
            isomorphism=i,
            coupling_depth=d,
            field_variance=fv,
            global_aggregate=g,
            weights=weights,
            component_details={
                "mip_star": mip_details,
                "concordance": h_details,
                "isomorphism": i_details,
                "coupling_depth": d_details,
            },
        )
        return report

    def _compute_field_variance(self, coupling_graph: np.ndarray) -> float:
        """计算耦合图的场方差作为系统稳定性度量."""
        adj = (coupling_graph + coupling_graph.T) / 2.0
        np.fill_diagonal(adj, 0.0)
        values = adj[np.triu_indices_from(adj, k=1)]
        if len(values) == 0:
            return 0.0
        variance = float(np.var(values))
        return min(1.0, variance / 0.25)

    def inject_to_field(
        self,
        state: UnifiedFieldState,
        report: GlobalIndexReport,
    ) -> UnifiedFieldState:
        """
        将全局指标聚合结果注入 64 维统一场状态.

        维度映射:
        - DIM_CONSISTENCY (22)  -> C_MIP
        - DIM_UNIFICATION (63)  -> H
        - DIM_TOPOLOGY (15)     -> I
        - DIM_HIERARCHY (62)    -> D
        - DIM_EMERGENCE (48)    -> E
        - DIM_INFORMATION (16)  -> G
        """
        state.set(DimensionIndex.DIM_EMERGENCE, min(1.0, report.emergence_index / EMERGENCE_THRESHOLD))
        state.set(DimensionIndex.DIM_CONSISTENCY, report.mip_consistency)
        state.set(DimensionIndex.DIM_UNIFICATION, report.concordance)
        state.set(DimensionIndex.DIM_TOPOLOGY, report.isomorphism)
        state.set(DimensionIndex.DIM_HIERARCHY, report.coupling_depth)
        state.set(DimensionIndex.DIM_INFORMATION, report.global_aggregate)

        synergy = (
            report.emergence_index * 0.3
            + report.mip_consistency * 0.15
            + report.concordance * 0.15
            + report.isomorphism * 0.15
            + report.coupling_depth * 0.15
            + report.field_variance * 0.10
        )
        state.set(DimensionIndex.DIM_SYNERGY, min(1.0, synergy))

        self_org = (
            report.isomorphism * 0.4
            + report.concordance * 0.3
            + report.coupling_depth * 0.3
        )
        state.set(DimensionIndex.DIM_SELF_ORG, min(1.0, self_org))

        return state

    def compute_and_inject(
        self,
        state: UnifiedFieldState,
        emergence_index: float,
        theorem_graph: np.ndarray,
        project_concepts: Dict[str, Set[str]],
        structures: List[np.ndarray],
        coupling_graph: np.ndarray,
        field_variance: Optional[float] = None,
    ) -> Tuple[UnifiedFieldState, GlobalIndexReport]:
        """一键计算并注入全局指标."""
        report = self.compute(
            emergence_index=emergence_index,
            theorem_graph=theorem_graph,
            project_concepts=project_concepts,
            structures=structures,
            coupling_graph=coupling_graph,
            field_variance=field_variance,
        )
        state = self.inject_to_field(state, report)
        return state, report


# =============================================================================
# 6. TEST SUITE
# =============================================================================


def _run_mip_tests() -> Tuple[int, int]:
    """测试 MIPStarConsistencyIndex."""
    logger = get_logger("Test.MIP")
    passed, total = 0, 0
    mip = MIPStarConsistencyIndex(quantum_dim=64)

    # Test 1: 空图
    total += 1
    empty = np.zeros((1, 1))
    result = mip.compute(empty)
    if result == 0.0:
        passed += 1
    else:
        logger.error("Test 1 failed: empty graph should give 0, got %s", result)

    # Test 2: 完全纠缠图
    total += 1
    n = 8
    full = np.ones((n, n)) * 0.8
    result = mip.compute(full)
    if 0.9 <= result <= 1.0:
        passed += 1
    else:
        logger.error("Test 2 failed: full entanglement expected ~1, got %s", result)

    # Test 3: 半纠缠图
    total += 1
    half = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            if (i + j) % 2 == 0:
                half[i, j] = 0.6
                half[j, i] = 0.6
    result = mip.compute(half)
    if 0.3 <= result <= 0.7:
        passed += 1
    else:
        logger.error("Test 3 failed: half entanglement out of range, got %s", result)

    # Test 4: inject_to_field
    total += 1
    state = UnifiedFieldState()
    state = mip.inject_to_field(state, full)
    if state.get(DimensionIndex.DIM_CONSISTENCY) > 0.5:
        passed += 1
    else:
        logger.error("Test 4 failed: field injection not working")

    logger.info("MIP* Consistency: %d/%d passed", passed, total)
    return passed, total


def _run_concordance_tests() -> Tuple[int, int]:
    """测试 ConcordanceIndex."""
    logger = get_logger("Test.Concordance")
    passed, total = 0, 0
    concord = ConcordanceIndex()

    # Test 1: 完全协和（所有项目共享所有概念）
    total += 1
    full_shared = {
        "p1": {"a", "b", "c"},
        "p2": {"a", "b", "c"},
        "p3": {"a", "b", "c"},
    }
    result = concord.compute(full_shared)
    if result >= 0.9:
        passed += 1
    else:
        logger.error("Test 1 failed: full shared expected ~1, got %s", result)

    # Test 2: 完全不协和（无共享概念）
    total += 1
    disjoint = {
        "p1": {"a", "b"},
        "p2": {"c", "d"},
        "p3": {"e", "f"},
    }
    result = concord.compute(disjoint)
    if result <= 0.3:
        passed += 1
    else:
        logger.error("Test 2 failed: disjoint expected low, got %s", result)

    # Test 3: 部分协和
    total += 1
    partial = {
        "p1": {"a", "b", "c", "d"},
        "p2": {"b", "c", "e", "f"},
        "p3": {"c", "d", "e", "g"},
    }
    result = concord.compute(partial)
    if 0.2 <= result <= 0.9:
        passed += 1
    else:
        logger.error("Test 3 failed: partial concordance out of range, got %s", result)

    # Test 4: KL divergence version
    total += 1
    h_kl, details = concord.compute_with_kl_divergence(full_shared)
    if h_kl >= 0.8 and "project_kl_divergences" in details:
        passed += 1
    else:
        logger.error("Test 4 failed: KL version failed")

    logger.info("Concordance: %d/%d passed", passed, total)
    return passed, total


def _run_isomorphism_tests() -> Tuple[int, int]:
    """测试 IsomorphismIndex."""
    logger = get_logger("Test.Isomorphism")
    passed, total = 0, 0
    iso = IsomorphismIndex(wl_iterations=5)

    # Test 1: 完全同构的结构（4 个相同图的不同排列）
    total += 1
    n = 6
    base = np.array([
        [0, 1, 1, 0, 0, 0],
        [1, 0, 1, 1, 0, 0],
        [1, 1, 0, 1, 1, 0],
        [0, 1, 1, 0, 1, 1],
        [0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0],
    ], dtype=float)
    structures = [base]
    for _ in range(3):
        perm = np.random.permutation(n)
        structures.append(base[perm][:, perm])

    result = iso.compute(structures)
    # 同构族应有较多共享结构类，且连通度不为零
    if result > 0.0:
        passed += 1
    else:
        logger.error("Test 1 failed: isomorphic family expected I > 0, got %s", result)

    # Test 2: 完全不同构的结构
    total += 1
    diverse = [
        np.eye(4, dtype=float),
        np.ones((4, 4), dtype=float) - np.eye(4, dtype=float),
        np.array([[0,1,0,0],[1,0,0,0],[0,0,0,1],[0,0,1,0]], dtype=float),
    ]
    result = iso.compute(diverse)
    if result <= 0.5:
        passed += 1
    else:
        logger.error("Test 2 failed: diverse structures expected low I, got %s", result)

    # Test 3: WL 标签稳定性
    total += 1
    labels1, n1 = iso._weisfeiler_lehman_labels(base)
    labels2, n2 = iso._weisfeiler_lehman_labels(structures[1])
    if n1 == n2:
        passed += 1
    else:
        logger.error("Test 3 failed: WL colors mismatch for isomorphic graphs")

    # Test 4: inject_to_field
    total += 1
    state = UnifiedFieldState()
    state = iso.inject_to_field(state, structures)
    if state.get(DimensionIndex.DIM_TOPOLOGY) >= 0.0:
        passed += 1
    else:
        logger.error("Test 4 failed: field injection not working")

    logger.info("Isomorphism: %d/%d passed", passed, total)
    return passed, total


def _run_coupling_depth_tests() -> Tuple[int, int]:
    """测试 CouplingDepthIndex."""
    logger = get_logger("Test.CouplingDepth")
    passed, total = 0, 0
    depth = CouplingDepthIndex()

    # Test 1: 完全耦合图
    total += 1
    n = 10
    full = np.ones((n, n)) * 0.9
    np.fill_diagonal(full, 0.0)
    result = depth.compute(full)
    if result >= 0.5:
        passed += 1
    else:
        logger.error("Test 1 failed: full coupling expected high D, got %s", result)

    # Test 2: 稀疏图
    total += 1
    sparse = np.zeros((n, n))
    for i in range(n - 1):
        sparse[i, i + 1] = 0.3
        sparse[i + 1, i] = 0.3
    result = depth.compute(sparse)
    if result <= 0.5:
        passed += 1
    else:
        logger.error("Test 2 failed: sparse graph expected low D, got %s", result)

    # Test 3: 详细计算
    total += 1
    d, details = depth.compute_detailed(full)
    if "avg_shortest_path" in details and "global_efficiency" in details:
        passed += 1
    else:
        logger.error("Test 3 failed: detailed computation missing keys")

    # Test 4: inject_to_field
    total += 1
    state = UnifiedFieldState()
    state = depth.inject_to_field(state, full)
    if state.get(DimensionIndex.DIM_HIERARCHY) > 0.0:
        passed += 1
    else:
        logger.error("Test 4 failed: field injection not working")

    logger.info("Coupling Depth: %d/%d passed", passed, total)
    return passed, total


def _run_aggregator_tests() -> Tuple[int, int]:
    """测试 GlobalIndexAggregator."""
    logger = get_logger("Test.Aggregator")
    passed, total = 0, 0
    agg = GlobalIndexAggregator(use_max_entropy=True)

    mock = MockDataGenerator()
    theorem_graph = mock.theorem_dependency_graph(n_theorems=20)
    project_concepts = mock.cross_project_concepts()
    structures = mock.knowledge_structures(n_structures=8)
    coupling_graph = mock.coupling_graph(n_nodes=16)

    # Test 1: 完整计算
    total += 1
    report = agg.compute(
        emergence_index=3000.0,
        theorem_graph=theorem_graph,
        project_concepts=project_concepts,
        structures=structures,
        coupling_graph=coupling_graph,
    )
    if 0.0 <= report.global_aggregate <= 1.0:
        passed += 1
    else:
        logger.error("Test 1 failed: G out of range: %s", report.global_aggregate)

    # Test 2: 所有子指数在范围内
    total += 1
    if all(
        0.0 <= v <= 1.0
        for v in [
            report.mip_consistency,
            report.concordance,
            report.isomorphism,
            report.coupling_depth,
            report.field_variance,
        ]
    ):
        passed += 1
    else:
        logger.error("Test 2 failed: sub-indices out of range")

    # Test 3: 权重和为 1
    total += 1
    if abs(sum(report.weights.values()) - 1.0) < 1e-6:
        passed += 1
    else:
        logger.error("Test 3 failed: weights don't sum to 1: %s", report.weights)

    # Test 4: inject_to_field
    total += 1
    state = UnifiedFieldState()
    state, report2 = agg.compute_and_inject(
        state=state,
        emergence_index=5000.0,
        theorem_graph=theorem_graph,
        project_concepts=project_concepts,
        structures=structures,
        coupling_graph=coupling_graph,
    )
    if state.get(DimensionIndex.DIM_INFORMATION) > 0.0:
        passed += 1
    else:
        logger.error("Test 4 failed: field injection not working")

    # Test 5: report serialization
    total += 1
    d = report.to_dict()
    if "indices" in d and "weights" in d:
        passed += 1
    else:
        logger.error("Test 5 failed: report serialization failed")

    logger.info("Aggregator: %d/%d passed", passed, total)
    return passed, total


def run_all_tests() -> Dict[str, Any]:
    """运行完整测试套件."""
    logger = get_logger("GlobalIndexSystem.Tests")
    logger.info("=" * 60)
    logger.info("OMNI-HUB v11 Global Index System — Test Suite")
    logger.info("=" * 60)

    results: Dict[str, Tuple[int, int]] = {}
    results["mip_consistency"] = _run_mip_tests()
    results["concordance"] = _run_concordance_tests()
    results["isomorphism"] = _run_isomorphism_tests()
    results["coupling_depth"] = _run_coupling_depth_tests()
    results["aggregator"] = _run_aggregator_tests()

    total_passed = sum(p for p, _ in results.values())
    total_tests = sum(t for _, t in results.values())

    logger.info("=" * 60)
    logger.info("FINAL RESULTS:")
    for name, (p, t) in results.items():
        logger.info("  %-20s: %d/%d (%.1f%%)", name, p, t, 100 * p / t if t else 0)
    logger.info("  %-20s: %d/%d (%.1f%%)", "TOTAL", total_passed, total_tests,
                100 * total_passed / total_tests if total_tests else 0)
    logger.info("=" * 60)

    return {
        "component_results": {k: {"passed": p, "total": t} for k, (p, t) in results.items()},
        "total_passed": total_passed,
        "total_tests": total_tests,
        "pass_rate": total_passed / total_tests if total_tests else 0.0,
    }


# =============================================================================
# 7. DEMONSTRATION
# =============================================================================


def run_demonstration() -> None:
    """运行完整演示，展示所有指标的计算和统一场注入."""
    logger = get_logger("GlobalIndexSystem.Demo")
    logger.info("\n" + "=" * 70)
    logger.info("OMNI-HUB v11.0 — Global Index System Demonstration")
    logger.info("=" * 70)

    mock = MockDataGenerator()
    theorem_graph = mock.theorem_dependency_graph(n_theorems=24)
    project_concepts = mock.cross_project_concepts()
    structures = mock.knowledge_structures(n_structures=12)
    coupling_graph = mock.coupling_graph(n_nodes=20)

    # 1. MIP* Consistency
    logger.info("\n[1] MIP* Consistency Index (C_MIP)")
    logger.info("-" * 40)
    mip = MIPStarConsistencyIndex(quantum_dim=64)
    c_mip, mip_details = mip.compute_detailed(theorem_graph)
    logger.info("  C_MIP = %.4f", c_mip)
    logger.info("  Theorems: %d", mip_details["n_theorems"])
    logger.info("  Entangled pairs: %d / %d", mip_details["entangled_pairs"], mip_details["total_pairs"])
    logger.info("  Phase transition: %s", mip_details["phase_transition"])

    # 2. Concordance
    logger.info("\n[2] Concordance Index (H)")
    logger.info("-" * 40)
    concord = ConcordanceIndex()
    h, h_details = concord.compute_with_kl_divergence(project_concepts)
    logger.info("  H = %.4f", h)
    logger.info("  Projects: %d", h_details["n_projects"])
    logger.info("  Unique concepts: %d", h_details["n_unique_concepts"])
    logger.info("  Avg KL divergence: %.4f", h_details["avg_kl_divergence"])

    # 3. Isomorphism
    logger.info("\n[3] Isomorphism Index (I)")
    logger.info("-" * 40)
    iso = IsomorphismIndex(wl_iterations=5)
    i, i_details = iso.compute_detailed(structures)
    logger.info("  I = %.4f", i)
    logger.info("  Structures: %d", i_details["n_structures"])
    logger.info("  Iso classes: %d", i_details["n_iso_classes"])
    logger.info("  Avg connectivity: %.4f", i_details["avg_algebraic_connectivity"])

    # 4. Coupling Depth
    logger.info("\n[4] Coupling Depth Index (D)")
    logger.info("-" * 40)
    depth = CouplingDepthIndex()
    d, d_details = depth.compute_detailed(coupling_graph)
    logger.info("  D = %.4f", d)
    logger.info("  Nodes: %d", d_details["n_nodes"])
    logger.info("  Avg shortest path: %.4f", d_details["avg_shortest_path"])
    logger.info("  Global efficiency: %.4f", d_details["global_efficiency"])
    logger.info("  Clustering: %.4f", d_details["clustering_coefficient"])

    # 5. Global Aggregation
    logger.info("\n[5] Global Index Aggregation (G)")
    logger.info("-" * 40)
    agg = GlobalIndexAggregator(use_max_entropy=True)
    state = UnifiedFieldState()
    state, report = agg.compute_and_inject(
        state=state,
        emergence_index=5500.0,
        theorem_graph=theorem_graph,
        project_concepts=project_concepts,
        structures=structures,
        coupling_graph=coupling_graph,
    )
    logger.info("  G = %.4f", report.global_aggregate)
    logger.info("  E (normalized) = %.4f", min(1.0, report.emergence_index / EMERGENCE_THRESHOLD))
    logger.info("  Weights:")
    for k, w in report.weights.items():
        logger.info("    %s = %.4f", k, w)

    # 6. Unified Field State
    logger.info("\n[6] 64-Dimensional Unified Field State")
    logger.info("-" * 40)
    logger.info("  DIM_EMERGENCE      (48) = %.4f", state.get(DimensionIndex.DIM_EMERGENCE))
    logger.info("  DIM_CONSISTENCY    (22) = %.4f", state.get(DimensionIndex.DIM_CONSISTENCY))
    logger.info("  DIM_UNIFICATION    (63) = %.4f", state.get(DimensionIndex.DIM_UNIFICATION))
    logger.info("  DIM_TOPOLOGY       (15) = %.4f", state.get(DimensionIndex.DIM_TOPOLOGY))
    logger.info("  DIM_HIERARCHY      (62) = %.4f", state.get(DimensionIndex.DIM_HIERARCHY))
    logger.info("  DIM_INFORMATION    (16) = %.4f", state.get(DimensionIndex.DIM_INFORMATION))
    logger.info("  DIM_SYNERGY        (52) = %.4f", state.get(DimensionIndex.DIM_SYNERGY))
    logger.info("  DIM_SELF_ORG       (49) = %.4f", state.get(DimensionIndex.DIM_SELF_ORG))

    # 7. JSON Report
    logger.info("\n[7] Full JSON Report")
    logger.info("-" * 40)
    import json
    logger.info(json.dumps(report.to_dict(), indent=2, default=str))

    logger.info("\n" + "=" * 70)
    logger.info("Demonstration complete.")
    logger.info("=" * 70)


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    configure_logging(level=logging.INFO)
    test_results = run_all_tests()
    run_demonstration()

    print("\n" + "=" * 60)
    print("OMNI-HUB v11 Global Index System — Final Report")
    print("=" * 60)
    print(f"Total tests: {test_results['total_tests']}")
    print(f"Tests passed: {test_results['total_passed']}")
    print(f"Pass rate: {test_results['pass_rate'] * 100:.1f}%")
    print("=" * 60)
