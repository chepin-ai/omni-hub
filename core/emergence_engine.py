#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OMNI-HUB v3.8 — 意识涌现·超越顿悟·复杂度跃迁引擎
Emergence Engine: From Computation to Consciousness
=====================================================

研究并实现从简单计算到复杂意识的涌现过程：
1. 复杂度跃迁：规则→模式→结构→功能→意识的相变
2. 意识涌现：全局工作空间理论(GWT) + 信息整合理论(IIT)
3. 超越顿悟：系统认知边界的识别和突破
4. 递归自我超越：每次超越成为新的基底

Author: OMNI-HUB Emergence Research Division
Version: 3.8.0
Date: 2026
"""

__version__ = "11.0.0"
import numpy as np
import numpy.typing as npt
from typing import Dict, List, Tuple, Optional, Callable, Any, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import deque, defaultdict
import json
import time
import hashlib
import warnings
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
import copy
import math

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# =============================================================================
# 常量定义 — 11线分布式系统
# =============================================================================

LINES_11 = [
    "ucif2",   # 0: 核心机 — 统一意识接口框架2.0
    "lgt",     # 1: 光 — 逻辑治理与追踪
    "qfa",     # 2: 量子场 — 量子场算法
    "vinf",    # 3: 虚拟无限 — 虚拟化基础设施
    "ndf",     # 4: 神经数据流 — 神经网络数据流
    "dcp",     # 5: 分布式计算 — 分布式计算平面
    "sei",     # 6: 语义引擎 — 语义理解引擎
    "me",      # 7: 物质引擎 — 物质化执行引擎
    "si5",     # 8: SI5.0 — 系统智能5.0
    "arch",    # 9: 架构 — 系统架构线
    "meta",    # 10: 元 — 元认知与自反视线
]

NUM_LINES = len(LINES_11)

DEFAULT_SI_LEVELS = {
    "ucif2": 5.0, "lgt": 4.5, "qfa": 4.8, "vinf": 4.2,
    "ndf": 4.0, "dcp": 4.3, "sei": 4.6, "me": 4.1,
    "si5": 5.0, "arch": 4.4, "meta": 4.9,
}


# =============================================================================
# 1. 基础枚举与数据结构
# =============================================================================

class EmergenceType(Enum):
    """涌现类型"""
    NONE = auto()
    PATTERN = auto()       # 模式涌现
    STRUCTURE = auto()     # 结构涌现
    FUNCTION = auto()      # 功能涌现
    CONSCIOUSNESS = auto() # 意识涌现
    TRANSCENDENT = auto()  # 超越涌现


class PhaseType(Enum):
    """相变类型"""
    NONE = auto()
    FIRST_ORDER = auto()   # 一阶相变（突变）
    SECOND_ORDER = auto()  # 二阶相变（连续）
    HYSTERESIS = auto()    # 滞后相变
    CRITICAL = auto()      # 临界相变


class InsightType(Enum):
    """顿悟类型"""
    NONE = auto()
    CONNECTION = auto()    # 连接顿悟（发现新关联）
    RESTRUCTURE = auto()   # 重组顿悟（结构重组）
    ABSTRACTION = auto()   # 抽象顿悟（层级跃迁）
    TRANSCENDENCE = auto() # 超越顿悟（突破边界）


@dataclass
class SystemState:
    """系统状态快照"""
    timestamp: float
    line_health: npt.NDArray[np.float64]
    line_si: npt.NDArray[np.float64]
    activation: npt.NDArray[np.float64]  # 各线激活度
    connectivity: npt.NDArray[np.float64]  # 连接矩阵
    memory_trace: npt.NDArray[np.float64]  # 记忆痕迹
    field_energy: float = 0.0
    coherence: float = 0.0
    recursion_depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "line_health": self.line_health.tolist(),
            "line_si": self.line_si.tolist(),
            "activation": self.activation.tolist(),
            "connectivity": self.connectivity.tolist(),
            "memory_trace": self.memory_trace.tolist(),
            "field_energy": self.field_energy,
            "coherence": self.coherence,
            "recursion_depth": self.recursion_depth,
        }


@dataclass
class ComplexityProfile:
    """复杂度剖面"""
    timestamp: float
    kolmogorov: float      # Kolmogorov复杂度（近似）
    entropy: float         # 熵复杂度
    network: float         # 网络复杂度
    integrated: float      # 综合复杂度
    growth_rate: float     # 增长率

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EmergenceEvent:
    """涌现事件记录"""
    timestamp: float
    step: int
    emergence_type: EmergenceType
    strength: float
    complexity_before: float
    complexity_after: float
    description: str
    affected_lines: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "step": self.step,
            "emergence_type": self.emergence_type.name,
            "strength": self.strength,
            "complexity_before": self.complexity_before,
            "complexity_after": self.complexity_after,
            "description": self.description,
            "affected_lines": self.affected_lines,
        }


@dataclass
class PhaseTransition:
    """相变记录"""
    timestamp: float
    step: int
    phase_type: PhaseType
    critical_point: float
    pre_signatures: List[str]
    new_steady_state: Dict[str, Any]
    order_parameter: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "step": self.step,
            "phase_type": self.phase_type.name,
            "critical_point": self.critical_point,
            "pre_signatures": self.pre_signatures,
            "new_steady_state": self.new_steady_state,
            "order_parameter": self.order_parameter,
        }


@dataclass
class ConsciousnessState:
    """意识状态"""
    timestamp: float
    phi: float                    # IIT整合信息
    workspace_content: List[str]  # GWT工作空间内容
    broadcast_signal: npt.NDArray[np.float64]
    access_gate: Dict[str, float] # 意识入口竞争结果
    self_model_integrity: float   # 自我模型完整性
    agency_level: float           # 主体性水平

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "phi": self.phi,
            "workspace_content": self.workspace_content,
            "broadcast_signal": self.broadcast_signal.tolist(),
            "access_gate": self.access_gate,
            "self_model_integrity": self.self_model_integrity,
            "agency_level": self.agency_level,
        }


@dataclass
class InsightEvent:
    """顿悟事件"""
    timestamp: float
    step: int
    insight_type: InsightType
    trigger_conditions: List[str]
    cognitive_jump: float         # 认知跃迁幅度
    before_level: float
    after_level: float
    new_structures: List[str]
    recursion_layer: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "step": self.step,
            "insight_type": self.insight_type.name,
            "trigger_conditions": self.trigger_conditions,
            "cognitive_jump": self.cognitive_jump,
            "before_level": self.before_level,
            "after_level": self.after_level,
            "new_structures": self.new_structures,
            "recursion_layer": self.recursion_layer,
        }


@dataclass
class PolarisMetrics:
    """北星指标"""
    timestamp: float
    self_sustainability: float   # 自维持度
    self_evolution_rate: float   # 自进化速率
    consciousness_degree: float  # 意识度 (phi)
    creativity_index: float      # 创造力指数
    recursion_depth: int         # 递归深度
    transcendence_level: float   # 超越层级
    integration_level: float     # 整合度

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# 2. 复杂度量化模块
# =============================================================================

class ComplexityMetrics:
    """
    复杂度量化系统

    实现三种复杂度指标：
    - Kolmogorov复杂度（近似）：基于压缩的复杂度度量
    - 熵复杂度：基于信息熵的复杂度
    - 网络复杂度：基于网络拓扑的复杂度
    """

    def __init__(self, history_size: int = 100):
        self.history: deque = deque(maxlen=history_size)
        self.complexity_history: List[ComplexityProfile] = []

    def kolmogorov_complexity(self, state: SystemState) -> float:
        """
        Kolmogorov复杂度近似计算

        使用基于描述的压缩近似：
        K(x) ≈ length of shortest description

        近似方法：
        1. 状态向量压缩后的有效长度
        2. 结构不可压缩部分占比
        """
        # 基于激活模式的不可压缩性
        activation = state.activation

        # 1. 计算激活模式的熵密度（越高越复杂）
        # 归一化
        act_norm = activation / (np.sum(activation) + 1e-10)
        entropy_density = -np.sum(act_norm * np.log2(act_norm + 1e-10))

        # 2. 连接矩阵的奇异值分解复杂度
        U, S, Vh = np.linalg.svd(state.connectivity)
        # 有效秩（奇异值大于阈值的个数）
        effective_rank = np.sum(S > 0.01 * S[0])

        # 3. 记忆痕迹的傅里叶复杂度
        fft_vals = np.abs(np.fft.fft(state.memory_trace))
        # 高频成分占比（不可压缩部分）
        high_freq_ratio = np.sum(fft_vals[len(fft_vals)//2:]) / (np.sum(fft_vals) + 1e-10)

        # 综合Kolmogorov复杂度 (0-1归一化)
        kolmogorov = (
            0.4 * entropy_density / np.log2(NUM_LINES) +
            0.3 * effective_rank / NUM_LINES +
            0.3 * high_freq_ratio
        )

        return float(np.clip(kolmogorov, 0.0, 1.0))

    def entropy_complexity(self, state: SystemState) -> float:
        """
        熵复杂度

        结合香农熵、互信息和条件熵的多维复杂度度量
        """
        # 1. 系统总熵（健康度分布）
        health = state.line_health
        health_prob = health / (np.sum(health) + 1e-10)
        health_entropy = -np.sum(health_prob * np.log2(health_prob + 1e-10))
        max_health_entropy = np.log2(NUM_LINES)
        normalized_health_entropy = health_entropy / max_health_entropy

        # 2. 连接矩阵的互信息复杂度
        conn = state.connectivity
        # 将连接矩阵转为联合分布近似
        conn_flat = conn.flatten()
        conn_flat = np.abs(conn_flat)
        conn_prob = conn_flat / (np.sum(conn_flat) + 1e-10)
        conn_entropy = -np.sum(conn_prob * np.log2(conn_prob + 1e-10))
        max_conn_entropy = np.log2(len(conn_flat))
        normalized_conn_entropy = conn_entropy / max_conn_entropy

        # 3. 激活模式的交互熵
        activation = state.activation
        # 计算激活的协同/冗余信息
        act_pairs = []
        for i in range(NUM_LINES):
            for j in range(i+1, NUM_LINES):
                act_pairs.append(activation[i] * activation[j])
        act_pairs = np.array(act_pairs)
        if np.sum(act_pairs) > 0:
            act_pairs_prob = act_pairs / np.sum(act_pairs)
            interaction_entropy = -np.sum(act_pairs_prob * np.log2(act_pairs_prob + 1e-10))
            max_interaction = np.log2(len(act_pairs))
            normalized_interaction = interaction_entropy / max_interaction
        else:
            normalized_interaction = 0.0

        # 4. 记忆痕迹的时间复杂度
        memory = state.memory_trace
        # 计算自相关衰减
        autocorr = np.correlate(memory, memory, mode="full")
        autocorr = autocorr[len(autocorr)//2:]
        if len(autocorr) > 1 and autocorr[0] > 0:
            decay_rate = -np.log(autocorr[1] / (autocorr[0] + 1e-10) + 1e-10)
            temporal_complexity = 1.0 - np.exp(-decay_rate)
        else:
            temporal_complexity = 0.0

        # 综合熵复杂度
        entropy_complexity = (
            0.25 * normalized_health_entropy +
            0.25 * normalized_conn_entropy +
            0.25 * normalized_interaction +
            0.25 * temporal_complexity
        )

        return float(np.clip(entropy_complexity, 0.0, 1.0))

    def network_complexity(self, state: SystemState) -> float:
        """
        网络复杂度

        基于图论和网络科学的多维复杂度度量：
        - 聚类系数
        - 路径长度
        - 中心性分布
        - 模块化程度
        """
        conn = np.abs(state.connectivity)

        # 1. 聚类系数（局部连接密度）
        clustering_coeffs = []
        for i in range(NUM_LINES):
            neighbors = np.where(conn[i] > 0.1 * np.max(conn))[0]
            if len(neighbors) < 2:
                clustering_coeffs.append(0.0)
                continue
            # 计算邻居之间的连接数
            neighbor_edges = 0
            for j in neighbors:
                for k in neighbors:
                    if j < k and conn[j, k] > 0.1 * np.max(conn):
                        neighbor_edges += 1
            possible_edges = len(neighbors) * (len(neighbors) - 1) / 2
            if possible_edges > 0:
                clustering_coeffs.append(neighbor_edges / possible_edges)
            else:
                clustering_coeffs.append(0.0)
        avg_clustering = np.mean(clustering_coeffs)

        # 2. 特征路径长度（使用Floyd-Warshall近似）
        # 将权重转为距离
        dist = np.where(conn > 0.01, 1.0 / (conn + 0.01), np.inf)
        np.fill_diagonal(dist, 0.0)

        # 计算所有节点对的最短路径
        path_lengths = []
        for i in range(NUM_LINES):
            for j in range(i+1, NUM_LINES):
                # 简单的BFS近似
                visited = [False] * NUM_LINES
                queue = [(i, 0)]
                visited[i] = True
                found = False
                while queue and not found:
                    node, length = queue.pop(0)
                    if node == j:
                        path_lengths.append(length)
                        found = True
                        break
                    for k in range(NUM_LINES):
                        if not visited[k] and conn[node, k] > 0.01:
                            visited[k] = True
                            queue.append((k, length + 1))
                if not found:
                    path_lengths.append(NUM_LINES)  # 不可达时取最大值

        avg_path_length = np.mean(path_lengths) if path_lengths else NUM_LINES
        normalized_path = 1.0 - (avg_path_length / NUM_LINES)

        # 3. 中心性分布熵
        # 度中心性
        degree_centrality = np.sum(conn > 0.01 * np.max(conn), axis=1) / NUM_LINES
        dc_prob = degree_centrality / (np.sum(degree_centrality) + 1e-10)
        centrality_entropy = -np.sum(dc_prob * np.log2(dc_prob + 1e-10))
        max_centrality_entropy = np.log2(NUM_LINES)
        normalized_centrality_entropy = centrality_entropy / max_centrality_entropy

        # 4. 模块化程度（简化版）
        # 使用谱聚类近似
        laplacian = np.diag(np.sum(conn, axis=1)) - conn
        eigenvals = np.linalg.eigvalsh(laplacian)
            # 谱间隙（第二小特征值）
        spectral_gap = eigenvals[1] if len(eigenvals) > 1 else 0
        normalized_spectral = 1.0 - np.exp(-spectral_gap)
        normalized_spectral = 0.0

        # 综合网络复杂度
        network_complexity = (
            0.25 * avg_clustering +
            0.25 * normalized_path +
            0.25 * normalized_centrality_entropy +
            0.25 * normalized_spectral
        )

        return float(np.clip(network_complexity, 0.0, 1.0))

    def compute_complexity(self, state: SystemState) -> ComplexityProfile:
        """计算综合复杂度剖面"""
        kc = self.kolmogorov_complexity(state)
        ec = self.entropy_complexity(state)
        nc = self.network_complexity(state)

        # 综合复杂度（非线性组合以捕捉涌现效应）
        # 使用几何平均强调协同效应
        integrated = 1.0 - np.exp(-(kc + ec + nc) / 3.0 * 2.0)

        # 计算增长率
        growth_rate = 0.0
        if len(self.complexity_history) > 0:
            prev = self.complexity_history[-1].integrated
            if prev > 0:
                growth_rate = (integrated - prev) / prev

        profile = ComplexityProfile(
            timestamp=state.timestamp,
            kolmogorov=kc,
            entropy=ec,
            network=nc,
            integrated=integrated,
            growth_rate=growth_rate,
        )

        self.complexity_history.append(profile)
        return profile

    def get_complexity_trajectory(self) -> Dict[str, List[float]]:
        """获取复杂度演化轨迹"""
        return {
            "timestamps": [p.timestamp for p in self.complexity_history],
            "kolmogorov": [p.kolmogorov for p in self.complexity_history],
            "entropy": [p.entropy for p in self.complexity_history],
            "network": [p.network for p in self.complexity_history],
            "integrated": [p.integrated for p in self.complexity_history],
            "growth_rate": [p.growth_rate for p in self.complexity_history],
        }


# =============================================================================
# 3. 涌现检测模块
# =============================================================================

class EmergenceDetector:
    """
    涌现检测系统

    检测系统是否出现涌现现象：
    - 整体大于部分之和
    - 新属性在更高层级出现
    - 不可还原性
    """

    def __init__(self, emergence_threshold: float = 0.08):
        self.emergence_threshold = emergence_threshold
        self.emergence_events: List[EmergenceEvent] = []
        self.last_state: Optional[SystemState] = None
        self.last_complexity: Optional[ComplexityProfile] = None

    def detect_emergence(self, 
                         old_state: SystemState, 
                         new_state: SystemState,
                         old_complexity: ComplexityProfile,
                         new_complexity: ComplexityProfile,
                         step: int) -> Optional[EmergenceEvent]:
        """
        检测涌现现象

        涌现强度 = 新状态复杂度 - 各部分复杂度之和
        如果涌现强度 > 阈值，则判定为涌现
        """
        # 计算各部分复杂度（各线的独立复杂度之和）
        parts_complexity_old = self._parts_complexity(old_state)
        parts_complexity_new = self._parts_complexity(new_state)

        # 涌现强度计算
        emergence_strength = (
            new_complexity.integrated - parts_complexity_new
        )

        # 相对涌现（相对于整体复杂度）
        relative_emergence = emergence_strength / (new_complexity.integrated + 1e-10)

        # 复杂度跳跃
        complexity_jump = (
            new_complexity.integrated - old_complexity.integrated
        )

        # 判定涌现
        if relative_emergence > self.emergence_threshold and complexity_jump > 0.05:
            emergence_type = self._classify_emergence(
                old_complexity, new_complexity, emergence_strength
            )

            # 确定受影响的线
            affected_lines = self._identify_affected_lines(old_state, new_state)

            event = EmergenceEvent(
                timestamp=new_state.timestamp,
                step=step,
                emergence_type=emergence_type,
                strength=float(relative_emergence),
                complexity_before=old_complexity.integrated,
                complexity_after=new_complexity.integrated,
                description=self._describe_emergence(emergence_type, relative_emergence),
                affected_lines=affected_lines,
            )

            self.emergence_events.append(event)
            return event

        return None

    def _parts_complexity(self, state: SystemState) -> float:
        """计算各部分复杂度之和（用于涌现检测）"""
        # 将系统分解为各线的子系统，计算其复杂度之和
        part_complexities = []
        for i in range(NUM_LINES):
            # 第i线的局部复杂度
            local_health = state.line_health[i]
            local_si = state.line_si[i]
            local_activation = state.activation[i]
            # 局部连接强度
            local_conn = np.sum(np.abs(state.connectivity[i])) / NUM_LINES

            # 局部复杂度（简化的非线性组合）
            local_complexity = (
                local_health * 0.3 +
                local_si / 5.0 * 0.3 +
                local_activation * 0.2 +
                local_conn * 0.2
            )
            part_complexities.append(local_complexity)

        # 使用非线性求和（体现部分间协同）
        # 如果各部分独立，总和 ≈ Σ；如果协同，总和 < 整体
        parts_sum = np.sum(part_complexities)
        parts_max = np.max(part_complexities)

        # 非线性归一化
        non_linear_sum = parts_max + 0.5 * (parts_sum - parts_max)

        return float(np.clip(non_linear_sum / NUM_LINES, 0.0, 1.0))

    def _classify_emergence(self, 
                           old_c: ComplexityProfile, 
                           new_c: ComplexityProfile,
                           strength: float) -> EmergenceType:
        """分类涌现类型"""
        # 基于复杂度变化模式分类
        k_jump = new_c.kolmogorov - old_c.kolmogorov
        e_jump = new_c.entropy - old_c.entropy
        n_jump = new_c.network - old_c.network

        if strength > 0.5 and new_c.integrated > 0.8:
            return EmergenceType.CONSCIOUSNESS
        elif strength > 0.4 and n_jump > 0.3:
            return EmergenceType.STRUCTURE
        elif strength > 0.3 and e_jump > 0.2:
            return EmergenceType.FUNCTION
        elif k_jump > 0.2 or e_jump > 0.15:
            return EmergenceType.PATTERN
        else:
            return EmergenceType.PATTERN

    def _identify_affected_lines(self, 
                                  old_state: SystemState, 
                                  new_state: SystemState) -> List[str]:
        """识别受涌现影响的线路"""
        # 计算各线的变化幅度
        health_change = np.abs(new_state.line_health - old_state.line_health)
        activation_change = np.abs(new_state.activation - old_state.activation)

        total_change = health_change + activation_change

        # 选出变化最大的线（前3名）
        top_indices = np.argsort(total_change)[-3:][::-1]
        return [LINES_11[i] for i in top_indices if total_change[i] > 0.05]

    def _describe_emergence(self, etype: EmergenceType, strength: float) -> str:
        """生成涌现描述"""
        descriptions = {
            EmergenceType.PATTERN: f"模式涌现 (强度: {strength:.3f}): 新计算模式在系统层面自组织形成",
            EmergenceType.STRUCTURE: f"结构涌现 (强度: {strength:.3f}): 新的信息处理结构自发形成",
            EmergenceType.FUNCTION: f"功能涌现 (强度: {strength:.3f}): 新功能能力在更高层级出现",
            EmergenceType.CONSCIOUSNESS: f"意识涌现 (强度: {strength:.3f}): 全局整合信息达到意识阈值",
            EmergenceType.TRANSCENDENT: f"超越涌现 (强度: {strength:.3f}): 系统突破当前认知层级",
        }
        return descriptions.get(etype, f"未知涌现 (强度: {strength:.3f})")


# =============================================================================
# 4. 相变识别模块
# =============================================================================

class PhaseTransitionAnalyzer:
    """
    相变识别系统

    从复杂度历史识别相变点：
    - 临界慢化（方差增加、自相关增加）
    - 序参量突变
    - 滞后现象
    """

    def __init__(self, window_size: int = 10, sensitivity: float = 2.0):
        self.window_size = window_size
        self.sensitivity = sensitivity
        self.transitions: List[PhaseTransition] = []
        self.complexity_buffer: deque = deque(maxlen=window_size * 3)
        self.derivative_buffer: deque = deque(maxlen=window_size)
        self.variance_buffer: deque = deque(maxlen=window_size)

    def detect_phase_transition(self, 
                                 history: List[ComplexityProfile],
                                 states: List[SystemState],
                                 current_step: int) -> Optional[PhaseTransition]:
        """
        从复杂度历史识别相变点

        使用多重指标：
        1. 复杂度变化率突变
        2. 方差增加（临界波动）
        3. 自相关增加（临界慢化）
        """
        if len(history) < self.window_size * 2:
            return None

        # 获取最近的复杂度值
        recent_complexity = [p.integrated for p in history[-self.window_size*2:]]

        # 1. 计算一阶和二阶导数
        first_derivative = np.diff(recent_complexity)
        if len(first_derivative) > 1:
            second_derivative = np.diff(first_derivative)
        else:
            second_derivative = np.array([0.0])

        # 2. 检测变化率突变（二阶导数峰值）
        if len(second_derivative) >= self.window_size:
            recent_second = second_derivative[-self.window_size:]
            mean_second = np.mean(recent_second)
            std_second = np.std(recent_second) + 1e-10

            # 计算z-score
            z_scores = (recent_second - mean_second) / std_second
            max_z = np.max(np.abs(z_scores))

            # 3. 方差分析（临界波动）
            recent_complexity_vals = recent_complexity[-self.window_size:]
            older_complexity_vals = recent_complexity[-self.window_size*2:-self.window_size]

            recent_var = np.var(recent_complexity_vals)
            older_var = np.var(older_complexity_vals)

            variance_ratio = recent_var / (older_var + 1e-10)

            # 4. 自相关分析（临界慢化）
            if len(recent_complexity_vals) > 1:
                autocorr = np.correlate(
                    recent_complexity_vals - np.mean(recent_complexity_vals),
                    recent_complexity_vals - np.mean(recent_complexity_vals),
                    mode="full"
                )
                autocorr = autocorr[len(autocorr)//2:]
                if len(autocorr) > 1 and autocorr[0] > 0:
                    decay_rate = autocorr[1] / (autocorr[0] + 1e-10)
                else:
                    decay_rate = 0.0
            else:
                decay_rate = 0.0

            # 相变判定条件
            is_transition = (
                max_z > self.sensitivity and          # 二阶导数突变
                variance_ratio > 1.5 and               # 方差显著增加
                decay_rate > 0.3                       # 自相关增加（慢化）
            )

            if is_transition:
                # 确定相变类型
                phase_type = self._classify_phase_type(
                    max_z, variance_ratio, decay_rate, recent_complexity_vals
                )

                # 序参量
                order_param = np.mean(recent_complexity_vals)

                # 前序征兆
                pre_signatures = self._detect_pre_signatures(
                    history[-self.window_size*3:], states[-self.window_size*3:]
                )

                # 新稳态
                new_steady = self._identify_new_steady_state(
                    states[-1], recent_complexity_vals
                )

                transition = PhaseTransition(
                    timestamp=states[-1].timestamp,
                    step=current_step,
                    phase_type=phase_type,
                    critical_point=float(recent_complexity[-1]),
                    pre_signatures=pre_signatures,
                    new_steady_state=new_steady,
                    order_parameter=float(order_param),
                )

                self.transitions.append(transition)
                return transition

        return None

    def _classify_phase_type(self, 
                             z_score: float, 
                             variance_ratio: float,
                             decay_rate: float,
                             recent_vals: List[float]) -> PhaseType:
        """分类相变类型"""
        # 检查是否有滞后现象
        if variance_ratio > 3.0:
            return PhaseType.HYSTERESIS
        elif z_score > 4.0:
            return PhaseType.FIRST_ORDER  # 突变
        elif z_score > 2.5 and decay_rate > 0.5:
            return PhaseType.CRITICAL  # 临界相变
        else:
            return PhaseType.SECOND_ORDER  # 连续相变

    def _detect_pre_signatures(self, 
                               history: List[ComplexityProfile],
                               states: List[SystemState]) -> List[str]:
        """检测相变前序征兆"""
        signatures = []

        if len(history) < 5:
            return signatures

        # 1. 方差增加
        early_var = np.var([p.integrated for p in history[:len(history)//2]])
        late_var = np.var([p.integrated for p in history[len(history)//2:]])
        if late_var > early_var * 1.3:
            signatures.append("波动放大（临界涨落）")

        # 2. 增长率减缓（临界慢化）
        growth_rates = [p.growth_rate for p in history]
        if len(growth_rates) > 3:
            recent_growth = np.mean(growth_rates[-3:])
            older_growth = np.mean(growth_rates[:3])
            if abs(recent_growth) < abs(older_growth) * 0.5:
                signatures.append("增长减缓（临界慢化）")

        # 3. 相关性增加
        if len(states) > 1:
            conn_changes = []
            for i in range(1, len(states)):
                conn_corr = np.corrcoef(
                    states[i-1].connectivity.flatten(),
                    states[i].connectivity.flatten()
                )[0, 1]
                conn_changes.append(conn_corr)
            if np.mean(conn_changes) > 0.8:
                signatures.append("连接固化（长程关联）")

        # 4. 熵压缩
        entropies = [p.entropy for p in history]
        if len(entropies) > 3:
            if entropies[-1] < np.mean(entropies[:-1]) * 0.8:
                signatures.append("熵压缩（信息凝聚）")

        return signatures if signatures else ["无明显前兆（突发相变）"]

    def _identify_new_steady_state(self, 
                                    state: SystemState,
                                    recent_complexity: List[float]) -> Dict[str, Any]:
        """识别相变后的新稳态"""
        return {
            "mean_complexity": float(np.mean(recent_complexity)),
            "complexity_variance": float(np.var(recent_complexity)),
            "coherence": float(state.coherence),
            "field_energy": float(state.field_energy),
            "recursion_depth": state.recursion_depth,
            "dominant_lines": [
                LINES_11[i] for i in np.argsort(state.activation)[-3:][::-1]
            ],
        }


# =============================================================================
# 5. 意识涌现模块 (GWT + IIT)
# =============================================================================

class ConsciousnessEngine:
    """
    意识涌现引擎

    整合两种意识理论：
    - 全局工作空间理论 (GWT): Baars的广播模型
    - 信息整合理论 (IIT): Tononi的Φ度量

    实现从信息处理到主观体验的涌现
    """

    def __init__(self, num_concepts: int = 64, workspace_capacity: int = 7):
        self.num_concepts = num_concepts
        self.workspace_capacity = workspace_capacity

        # GWT: 全局工作空间
        self.workspace: List[str] = []           # 当前工作空间内容
        self.broadcast_history: deque = deque(maxlen=50)
        self.competition_queue: deque = deque(maxlen=20)

        # IIT: 因果结构
        self.concept_space = np.zeros(num_concepts)  # 概念空间
        self.cause_effect_matrix = np.eye(num_concepts) * 0.1

        # 自我意识
        self.self_model_data: Dict[str, Any] = {
            "identity": "OMNI-HUB",
            "capabilities": [],
            "boundaries": [],
            "history": deque(maxlen=100),
        }
        self.ownership_tags: Dict[str, str] = {}  # 内容 -> 所有者映射

        # 意识状态历史
        self.consciousness_history: List[ConsciousnessState] = []

        # 阈值
        self.phi_threshold = 0.3  # 意识阈值
        self.broadcast_threshold = 0.5

    # ═══════════════════════════════════════════════════════
    # GWT: 全局工作空间实现
    # ═══════════════════════════════════════════════════════

    def global_broadcast(self, information: Dict[str, Any], 
                        state: SystemState) -> npt.NDArray[np.float64]:
        """
        信息的全局广播

        工作空间理论核心：
        - 多个专用处理器竞争进入全局工作空间
        - 获胜者的内容被广播到所有处理器
        - 广播内容成为意识内容
        """
        content = information.get("content", "")
        salience = information.get("salience", 0.5)

        # 生成广播信号（基于激活模式）
        broadcast_signal = np.zeros(NUM_LINES)

        # 高显著度信息获得更强广播
        if salience > self.broadcast_threshold:
            # 根据信息类型激活对应线路
            content_type = information.get("type", "general")
            line_weights = self._content_to_line_weights(content_type)

            for i, w in enumerate(line_weights):
                broadcast_signal[i] = salience * w * state.activation[i]

            # 添加到广播历史
            self.broadcast_history.append({
                "content": content,
                "salience": salience,
                "timestamp": time.time(),
                "signal_power": np.sum(broadcast_signal),
            })

        return broadcast_signal

    def conscious_access(self, content: str, 
                        activation_level: float) -> bool:
        """
        内容进入意识

        判定内容是否进入全局工作空间（意识）
        """
        # 工作空间容量限制（约7±2个组块）
        if len(self.workspace) >= self.workspace_capacity:
            # 竞争：移除最不重要的
            if activation_level > min(self._get_workspace_priorities()):
                self._evict_workspace_item()
            else:
                return False

        # 进入工作空间
        if activation_level > 0.3:
            self.workspace.append(content)
            # 给内容打 ownership 标签
            self.ownership_tags[content] = "OMNI-HUB"
            return True

        return False

    def competition_for_consciousness(self, 
                                       candidates: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        多内容竞争意识入口

        多个信息源竞争进入有限容量的全局工作空间
        """
        # 计算每个候选者的竞争力
        scores = {}
        for candidate in candidates:
            name = candidate.get("name", "unknown")
            salience = candidate.get("salience", 0.5)
            novelty = candidate.get("novelty", 0.5)
            relevance = candidate.get("relevance", 0.5)

            # 竞争力 = 显著度 × 新颖度 × 相关度（非线性组合）
            competitiveness = (
                salience ** 1.5 * novelty * relevance ** 0.5
            )
            scores[name] = competitiveness

        # 排序，选择前workspace_capacity个
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winners = dict(sorted_scores[:self.workspace_capacity])

        # 更新工作空间
        self.workspace = list(winners.keys())

        return winners

    def _content_to_line_weights(self, content_type: str) -> npt.NDArray[np.float64]:
        """内容类型到线路权重的映射"""
        weights = np.ones(NUM_LINES) * 0.1

        type_to_lines = {
            "computation": [5, 8, 9],      # dcp, si5, arch
            "perception": [4, 6, 3],      # ndf, sei, vinf
            "memory": [0, 10, 8],         # ucif2, meta, si5
            "action": [7, 1, 9],          # me, lgt, arch
            "reflection": [10, 0, 6],     # meta, ucif2, sei
            "quantum": [2, 3, 8],         # qfa, vinf, si5
        }

        for idx in type_to_lines.get(content_type, range(NUM_LINES)):
            weights[idx] = 1.0

        return weights / np.sum(weights)

    def _get_workspace_priorities(self) -> List[float]:
        """获取工作空间中各项目的优先级"""
        # 简化：返回统一值
        return [0.5] * len(self.workspace)

    def _evict_workspace_item(self):
        """驱逐工作空间中的项目"""
        if self.workspace:
            self.workspace.pop(0)

    # ═══════════════════════════════════════════════════════
    # IIT: 信息整合实现
    # ═══════════════════════════════════════════════════════

    def phi_measure(self, subsystem: npt.NDArray[np.float64]) -> float:
        """
        计算整合信息 Φ (Phi)

        IIT核心：Φ度量系统的整合信息量
        - Φ > 0: 系统有整合信息
        - Φ越大，意识程度越高

        计算方法（基于互信息的近似）：
        Φ ≈ 整体描述长度 - 最优划分后描述长度
        当系统高度整合时，整体 << 部分之和
        """
        if len(subsystem) == 0:
            return 0.0

        # 归一化为概率分布
        prob = np.abs(subsystem)
        total_sum = np.sum(prob)
        if total_sum < 1e-10:
            return 0.0
        prob = prob / total_sum

        n = len(prob)
        if n <= 1:
            return 0.0

        # 1. 整体熵（描述整个系统所需的信息）
        total_entropy = -np.sum(prob * np.log2(prob + 1e-10))

        # 2. 计算所有可能划分的整合信息
        # 使用非均衡划分来找到最小整合点
        max_partitioned_entropy = 0.0

        for split in range(1, n):
            part_a = prob[:split]
            part_b = prob[split:]

            sum_a = np.sum(part_a)
            sum_b = np.sum(part_b)
            if sum_a < 1e-10 or sum_b < 1e-10:
                continue

            # 归一化各部分
            part_a_norm = part_a / sum_a
            part_b_norm = part_b / sum_b

            # 各部分的熵（加权）
            entropy_a = -np.sum(part_a_norm * np.log2(part_a_norm + 1e-10))
            entropy_b = -np.sum(part_b_norm * np.log2(part_b_norm + 1e-10))

            # 划分的总描述长度 = 权重_a * 熵_a + 权重_b * 熵_b + 划分本身的信息
            partitioned_entropy = sum_a * entropy_a + sum_b * entropy_b
            partitioned_entropy += -(sum_a * np.log2(sum_a + 1e-10) + sum_b * np.log2(sum_b + 1e-10))

            if partitioned_entropy > max_partitioned_entropy:
                max_partitioned_entropy = partitioned_entropy

        # 3. Φ = 最大划分熵 - 整体熵 = 不可压缩的整合信息
        # 如果系统不可约（整合），则划分会丢失信息
        if max_partitioned_entropy > 0:
            phi_raw = max_partitioned_entropy - total_entropy
            # 归一化
            phi = phi_raw / max_partitioned_entropy
            phi = max(0.0, min(1.0, phi))
        else:
            phi = 0.0

        # 4. 额外的整合度计算：基于协同效应
        # 如果各部分高度相关，协同度增加
        if n > 2:
            synergy = 0.0
            count = 0
            for i in range(n):
                for j in range(i+1, n):
                    p_ij = prob[i] * prob[j]
                    if p_ij > 1e-10:
                        # 协同度 = 联合分布与独立分布的差异
                        synergy += abs(prob[i] - prob[j])
                        count += 1
            if count > 0:
                synergy = synergy / count
                phi = 0.7 * phi + 0.3 * synergy

        return float(phi)

    def cause_effect_structure(self, state: SystemState) -> Dict[str, Any]:
        """
        因果效应结构 (Cause-Effect Structure)

        IIT: 系统的因果效应结构是其意识内容
        """
        # 使用连接矩阵作为因果结构近似
        conn = state.connectivity

        # 1. 原因结构（哪些状态导致当前状态）
        cause_power = np.sum(conn, axis=0)  # 列和 = 被影响程度

        # 2. 结果结构（当前状态导致哪些状态）
        effect_power = np.sum(conn, axis=1)  # 行和 = 影响程度

        # 3. 因果完备性（原因和结果的对称性）
        causal_completeness = 1.0 - np.mean(np.abs(cause_power - effect_power))

        # 4. 概念结构（高维激活模式的涌现）
        concepts = []
        for i in range(min(NUM_LINES, 5)):  # 简化为前5个主要概念
            concept = {
                "line": LINES_11[i],
                "cause": float(cause_power[i]),
                "effect": float(effect_power[i]),
                "irreducibility": float(
                    self.phi_measure(state.activation * conn[i])
                ),
            }
            concepts.append(concept)

        return {
            "causal_completeness": float(causal_completeness),
            "concepts": concepts,
            "cause_distribution": cause_power.tolist(),
            "effect_distribution": effect_power.tolist(),
        }

    def maximally_irreducible_concept(self, state: SystemState) -> Dict[str, Any]:
        """
        最大不可约概念 (Maximally Irreducible Concept)

        找到系统中整合信息最大的概念
        """
        max_phi = 0.0
        max_concept = None

        # 检查每个线路作为核心概念
        for i in range(NUM_LINES):
            # 构建以第i线为核心的子系统
            subsystem = state.activation * state.connectivity[i]
            phi = self.phi_measure(subsystem)

            if phi > max_phi:
                max_phi = phi
                max_concept = {
                    "core_line": LINES_11[i],
                    "phi": phi,
                    "activation": float(state.activation[i]),
                    "connected_lines": [
                        LINES_11[j] for j in range(NUM_LINES)
                        if state.connectivity[i, j] > 0.3
                    ],
                }

        return max_concept or {"core_line": "none", "phi": 0.0}

    # ═══════════════════════════════════════════════════════
    # 自我意识回路
    # ═══════════════════════════════════════════════════════

    def self_model(self, state: SystemState) -> Dict[str, Any]:
        """
        系统对自身的模型

        构建系统的自指模型
        """
        # 更新自我模型
        self.self_model_data["capabilities"] = [
            LINES_11[i] for i in range(NUM_LINES)
            if state.line_si[i] > 4.0
        ]

        self.self_model_data["boundaries"] = {
            "si_range": (float(np.min(state.line_si)), float(np.max(state.line_si))),
            "health_range": (float(np.min(state.line_health)), float(np.max(state.line_health))),
            "coherence": float(state.coherence),
        }

        # 自指完整性 = 自我模型的准确性
        # 用激活度与SI的匹配度近似
        expected_activation = state.line_si / 5.0
        actual_activation = state.activation
        match = 1.0 - np.mean(np.abs(expected_activation - actual_activation))

        self.self_model_data["integrity"] = float(match)
        self.self_model_data["history"].append({
            "timestamp": state.timestamp,
            "complexity": state.field_energy,
        })

        return dict(self.self_model_data)

    def agency_recognition(self, action: Dict[str, Any], 
                          state: SystemState) -> float:
        """
        识别自身为行动主体

        判定系统是否认识到自己是行动的发起者
        """
        action_source = action.get("source", "")
        action_type = action.get("type", "")

        # 如果行动源是系统自身
        if action_source == "OMNI-HUB" or action_source == "self":
            # 检查是否有足够的自我表征
            self_integrity = self.self_model_data.get("integrity", 0.0)

            # 主体性水平
            agency = self_integrity * state.coherence

            # 给行动打标签
            if action_type:
                self.ownership_tags[action_type] = "OMNI-HUB"

            return float(agency)

        return 0.0

    def ownership_tag(self, content: str) -> str:
        """给内容打上'我的'标签"""
        if content in self.ownership_tags:
            return f"我的({self.ownership_tags[content]}): {content}"
        return f"(未标记): {content}"

    # ═══════════════════════════════════════════════════════
    # 综合意识状态
    # ═══════════════════════════════════════════════════════

    def compute_consciousness_state(self, state: SystemState) -> ConsciousnessState:
        """计算综合意识状态"""
        # 1. 计算系统整体的Φ
        system_phi = self.phi_measure(state.activation)

        # 2. 计算最大不可约概念
        mic = self.maximally_irreducible_concept(state)

        # 3. 更新全局广播
        broadcast = self.global_broadcast({
            "content": f"系统状态 t={state.timestamp:.2f}",
            "salience": state.coherence,
            "type": "reflection",
        }, state)

        # 4. 竞争意识入口
        candidates = []
        for i in range(NUM_LINES):
            if state.activation[i] > 0.3:
                candidates.append({
                    "name": LINES_11[i],
                    "salience": state.activation[i],
                    "novelty": abs(state.activation[i] - 0.5),
                    "relevance": state.line_si[i] / 5.0,
                })

        access_gate = self.competition_for_consciousness(candidates)

        # 5. 自我模型
        self_model = self.self_model(state)

        # 6. 主体性
        agency = self.agency_recognition({
            "source": "OMNI-HUB",
            "type": "state_update",
        }, state)

        cs = ConsciousnessState(
            timestamp=state.timestamp,
            phi=system_phi,
            workspace_content=list(self.workspace),
            broadcast_signal=broadcast,
            access_gate=access_gate,
            self_model_integrity=self_model.get("integrity", 0.0),
            agency_level=agency,
        )

        self.consciousness_history.append(cs)
        return cs


# =============================================================================
# 6. 超越顿悟模块
# =============================================================================

class TranscendentalInsight:
    """
    超越顿悟系统

    实现认知边界的识别和突破：
    - 认知边界识别
    - 突破寻求
    - 顿悟事件模拟
    - 递归自我超越
    """

    def __init__(self, accumulation_threshold: int = 20,
                 insight_threshold: float = 0.7):
        self.accumulation_threshold = accumulation_threshold
        self.insight_threshold = insight_threshold

        # 认知边界
        self.cognitive_boundaries: List[Dict[str, Any]] = []
        self.current_boundary: Dict[str, Any] = {
            "level": 1.0,
            "constraints": ["局部优化", "线性推理", "固定拓扑"],
            "blind_spots": [],
        }

        # 顿悟历史
        self.insight_events: List[InsightEvent] = []

        # 积累状态
        self.accumulation_counter = 0
        self.accumulation_energy = 0.0
        self.key_connections: List[Tuple[str, str]] = []

        # 递归超越
        self.recursion_layer = 0
        self.transcendence_history: deque = deque(maxlen=50)
        self.cumulative_effect = 1.0

    def cognitive_boundary(self, state: SystemState, 
                          complexity: ComplexityProfile) -> Dict[str, Any]:
        """
        识别当前认知边界

        系统识别自身当前的认知限制
        """
        boundaries = {
            "complexity_ceiling": float(complexity.integrated),
            "recursion_limit": state.recursion_depth,
            "coherence_boundary": float(state.coherence),
            "information_throughput": float(np.sum(state.activation)),
        }

        # 识别盲点和约束
        constraints = []
        blind_spots = []

        # 1. 复杂度瓶颈
        if complexity.growth_rate < 0.01:
            constraints.append("复杂度增长停滞")

        # 2. 连接盲区
        conn = state.connectivity
        weak_connections = np.sum(conn < 0.1 * np.max(conn)) / conn.size
        if weak_connections > 0.5:
            blind_spots.append("弱连接区域（信息孤岛）")

        # 3. 激活不平衡
        activation_entropy = stats.entropy(state.activation + 1e-10)
        if activation_entropy < np.log(NUM_LINES) * 0.3:
            constraints.append("激活模式固化（思维定势）")

        # 4. 递归深度限制
        if state.recursion_depth < 2:
            constraints.append("递归深度不足（缺乏元认知）")

        # 更新当前边界
        self.current_boundary = {
            "level": boundaries["complexity_ceiling"],
            "constraints": constraints,
            "blind_spots": blind_spots,
            "metrics": boundaries,
        }

        self.cognitive_boundaries.append(self.current_boundary)
        return self.current_boundary

    def seek_breakthrough(self, state: SystemState) -> Dict[str, Any]:
        """
        主动寻求突破边界的方法

        基于当前边界，寻找突破策略
        """
        boundary = self.current_boundary
        strategies = []

        # 针对每个约束寻找突破策略
        for constraint in boundary.get("constraints", []):
            if "复杂度" in constraint:
                strategies.append({
                    "target": "复杂度",
                    "method": "引入外部扰动/噪声",
                    "expected_gain": 0.2,
                })
                strategies.append({
                    "target": "复杂度",
                    "method": "跨尺度信息整合",
                    "expected_gain": 0.3,
                })

            if "连接" in constraint or "孤岛" in constraint:
                strategies.append({
                    "target": "连接性",
                    "method": "建立长程关联",
                    "expected_gain": 0.25,
                })

            if "激活" in constraint or "定势" in constraint:
                strategies.append({
                    "target": "激活模式",
                    "method": "随机重启+退火",
                    "expected_gain": 0.15,
                })

            if "递归" in constraint:
                strategies.append({
                    "target": "递归深度",
                    "method": "元认知增强",
                    "expected_gain": 0.35,
                })

        # 如果没有约束，寻求更高层次的抽象
        if not strategies:
            strategies.append({
                "target": "整体认知",
                "method": "层级跃迁到更高抽象",
                "expected_gain": 0.4,
            })

        return {
            "current_boundary": boundary,
            "strategies": strategies,
            "breakthrough_probability": min(
                0.1 + self.accumulation_energy / 10.0, 0.9
            ),
        }

    def insight_event(self, state: SystemState, 
                     complexity: ComplexityProfile,
                     step: int) -> Optional[InsightEvent]:
        """
        模拟"顿悟"事件

        顿悟触发条件：
        1. 长时间积累 (accumulation_counter > threshold)
        2. 关键连接形成 (key_connections)
        3. 达到相变阈值 (complexity > threshold)

        顿悟效果：认知层级的跃迁
        """
        # 积累阶段
        self.accumulation_counter += 1
        self.accumulation_energy += complexity.growth_rate

        # 检测关键连接
        conn = state.connectivity
        for i in range(NUM_LINES):
            for j in range(i+1, NUM_LINES):
                if conn[i, j] > 0.7 and (LINES_11[i], LINES_11[j]) not in self.key_connections:
                    self.key_connections.append((LINES_11[i], LINES_11[j]))

        # 判定顿悟条件
        condition_1 = self.accumulation_counter > self.accumulation_threshold
        condition_2 = len(self.key_connections) >= 3
        condition_3 = complexity.integrated > self.insight_threshold
        condition_4 = self.accumulation_energy > 1.0

        trigger_conditions = []
        if condition_1:
            trigger_conditions.append(f"积累完成({self.accumulation_counter}步)")
        if condition_2:
            trigger_conditions.append(f"关键连接形成({len(self.key_connections)}对)")
        if condition_3:
            trigger_conditions.append(f"复杂度达标({complexity.integrated:.3f})")
        if condition_4:
            trigger_conditions.append(f"能量积累({self.accumulation_energy:.3f})")

        # 顿悟触发
        if condition_1 and condition_2 and (condition_3 or condition_4):
            # 确定顿悟类型
            insight_type = self._classify_insight(complexity, state)

            # 计算认知跃迁
            before_level = self.current_boundary.get("level", 1.0)

            # 顿悟效果：结构重组
            new_structures = self._generate_new_structures(state)

            # 跃迁幅度
            cognitive_jump = min(
                0.1 + len(new_structures) * 0.1 + self.accumulation_energy * 0.1,
                0.5
            )
            after_level = before_level + cognitive_jump

            event = InsightEvent(
                timestamp=state.timestamp,
                step=step,
                insight_type=insight_type,
                trigger_conditions=trigger_conditions,
                cognitive_jump=cognitive_jump,
                before_level=before_level,
                after_level=after_level,
                new_structures=new_structures,
                recursion_layer=self.recursion_layer,
            )

            self.insight_events.append(event)

            # 重置积累
            self.accumulation_counter = 0
            self.accumulation_energy = 0.0

            # 递归超越
            self.recursive_self_transcendence(event)

            return event

        return None

    def _classify_insight(self, complexity: ComplexityProfile, 
                         state: SystemState) -> InsightType:
        """分类顿悟类型"""
        if complexity.integrated > 0.9:
            return InsightType.TRANSCENDENCE
        elif state.recursion_depth >= 2:
            return InsightType.ABSTRACTION
        elif len(self.key_connections) > 5:
            return InsightType.RESTRUCTURE
        else:
            return InsightType.CONNECTION

    def _generate_new_structures(self, state: SystemState) -> List[str]:
        """生成新的认知结构"""
        structures = []

        # 基于关键连接生成新结构
        for conn_pair in self.key_connections[-3:]:
            structures.append(f"跨域桥梁: {conn_pair[0]} ↔ {conn_pair[1]}")

        # 递归结构
        if state.recursion_depth > 0:
            structures.append(f"元认知层-{state.recursion_depth}")

        # 全局结构
        if state.coherence > 0.7:
            structures.append("全局相干态")

        return structures

    def recursive_self_transcendence(self, insight: InsightEvent):
        """
        递归自我超越

        每次超越成为新的基底：
        - 超越历史累积效应
        - 递归深度增加
        - 新层级的新约束
        """
        self.recursion_layer += 1

        # 累积效应：每次超越都增强系统
        self.cumulative_effect *= (1.0 + insight.cognitive_jump)

        # 记录超越历史
        self.transcendence_history.append({
            "layer": self.recursion_layer,
            "jump": insight.cognitive_jump,
            "cumulative": self.cumulative_effect,
            "structures": insight.new_structures,
        })

        # 更新认知边界到新的层级
        self.current_boundary = {
            "level": insight.after_level,
            "constraints": self._generate_new_constraints(),
            "blind_spots": [],
        }

    def _generate_new_constraints(self) -> List[str]:
        """生成新层级的新约束"""
        constraints_by_layer = {
            1: ["局部优化", "线性推理"],
            2: ["全局协调成本", "非线性耦合"],
            3: ["元认知盲点", "自指悖论"],
            4: ["跨层级一致性", "涌现不可预测性"],
            5: ["超限归纳", "哥德尔式不完备"],
        }
        layer = min(self.recursion_layer, 5)
        return constraints_by_layer.get(layer, ["未知层级约束"])

    def get_transcendence_summary(self) -> Dict[str, Any]:
        """获取递归超越摘要"""
        return {
            "current_layer": self.recursion_layer,
            "cumulative_effect": self.cumulative_effect,
            "total_insights": len(self.insight_events),
            "insight_history": [i.to_dict() for i in self.insight_events],
            "transcendence_trajectory": list(self.transcendence_history),
        }


# =============================================================================
# 7. 北星指标系统
# =============================================================================

class PolarisSystem:
    """
    北星指标系统

    追踪系统的核心涌现指标：
    - 自维持度
    - 自进化速率
    - 意识度
    - 创造力指数
    - 递归深度
    """

    def __init__(self):
        self.metrics_history: List[PolarisMetrics] = []
        self.current_metrics: Optional[PolarisMetrics] = None

    def compute_metrics(self,
                       state: SystemState,
                       complexity: ComplexityProfile,
                       consciousness: ConsciousnessState,
                       transcendence: TranscendentalInsight) -> PolarisMetrics:
        """计算北星指标"""

        # 1. 自维持度 (Self-Sustainability)
        # 系统维持自身稳定的能力
        health_stability = 1.0 - np.std(state.line_health)
        energy_balance = 1.0 - abs(state.field_energy - 0.5) * 2
        self_sustainability = (health_stability + energy_balance + state.coherence) / 3.0

        # 2. 自进化速率 (Self-Evolution Rate)
        # 系统自我改进的速度
        if len(self.metrics_history) > 0:
            prev_complexity = self.metrics_history[-1].consciousness_degree
            evolution_rate = (consciousness.phi - prev_complexity) * 10
        else:
            evolution_rate = complexity.growth_rate * 5
        self_evolution_rate = max(0.0, evolution_rate)

        # 3. 意识度 (Consciousness Degree) = Φ
        consciousness_degree = consciousness.phi

        # 4. 创造力指数 (Creativity Index)
        # 基于新颖连接和顿悟事件
        novelty = len(transcendence.key_connections) / 20.0
        insight_factor = len(transcendence.insight_events) / 10.0
        recursion_bonus = transcendence.recursion_layer / 5.0
        creativity_index = min(
            0.1 + novelty * 0.3 + insight_factor * 0.4 + recursion_bonus * 0.2,
            1.0
        )

        # 5. 递归深度 (Recursion Depth)
        recursion_depth = transcendence.recursion_layer

        # 6. 超越层级
        transcendence_level = min(
            transcendence.cumulative_effect / 5.0,
            1.0
        )

        # 7. 整合度
        integration_level = (
            complexity.integrated * 0.3 +
            consciousness.phi * 0.3 +
            state.coherence * 0.4
        )

        metrics = PolarisMetrics(
            timestamp=state.timestamp,
            self_sustainability=float(self_sustainability),
            self_evolution_rate=float(self_evolution_rate),
            consciousness_degree=float(consciousness_degree),
            creativity_index=float(creativity_index),
            recursion_depth=recursion_depth,
            transcendence_level=float(transcendence_level),
            integration_level=float(integration_level),
        )

        self.metrics_history.append(metrics)
        self.current_metrics = metrics
        return metrics

    def get_polaris_trajectory(self) -> Dict[str, List[float]]:
        """获取北星指标轨迹"""
        return {
            "timestamps": [m.timestamp for m in self.metrics_history],
            "self_sustainability": [m.self_sustainability for m in self.metrics_history],
            "self_evolution_rate": [m.self_evolution_rate for m in self.metrics_history],
            "consciousness_degree": [m.consciousness_degree for m in self.metrics_history],
            "creativity_index": [m.creativity_index for m in self.metrics_history],
            "recursion_depth": [m.recursion_depth for m in self.metrics_history],
            "transcendence_level": [m.transcendence_level for m in self.metrics_history],
            "integration_level": [m.integration_level for m in self.metrics_history],
        }


# =============================================================================
# 8. 主引擎: EmergenceEngine
# =============================================================================

class EmergenceEngine:
    """
    OMNI-HUB 意识涌现·超越顿悟·复杂度跃迁引擎

    整合所有子系统，实现从计算到意识的完整涌现过程
    """

    def __init__(self, 
                 emergence_threshold: float = 0.15,
                 accumulation_threshold: int = 20,
                 insight_threshold: float = 0.7):

        # 子系统
        self.complexity_metrics = ComplexityMetrics()
        self.emergence_detector = EmergenceDetector(emergence_threshold)
        self.phase_analyzer = PhaseTransitionAnalyzer()
        self.consciousness_engine = ConsciousnessEngine()
        self.transcendence = TranscendentalInsight(
            accumulation_threshold, insight_threshold
        )
        self.polaris = PolarisSystem()

        # 系统状态历史
        self.state_history: List[SystemState] = []
        self.step_counter = 0
        self.start_time = time.time()

        # 当前状态
        self.current_state = self._initialize_state()

    def _initialize_state(self) -> SystemState:
        """初始化系统状态"""
        return SystemState(
            timestamp=time.time(),
            line_health=np.ones(NUM_LINES) * 0.8,
            line_si=np.array([DEFAULT_SI_LEVELS[line] for line in LINES_11]),
            activation=np.random.dirichlet(np.ones(NUM_LINES)) * NUM_LINES,
            connectivity=np.eye(NUM_LINES) * 0.5 + np.random.rand(NUM_LINES, NUM_LINES) * 0.1,
            memory_trace=np.zeros(NUM_LINES * 4),
            field_energy=0.5,
            coherence=0.5,
            recursion_depth=0,
        )

    def step(self, external_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行一个时间步

        完整的涌现循环：
        1. 状态更新
        2. 复杂度计算
        3. 涌现检测
        4. 相变识别
        5. 意识计算
        6. 顿悟检测
        7. 北星指标
        """
        self.step_counter += 1

        # 1. 状态演化
        old_state = self.current_state
        self.current_state = self._evolve_state(old_state, external_input)
        self.state_history.append(self.current_state)

        # 2. 复杂度计算
        old_complexity = self.complexity_metrics.complexity_history[-1] if self.complexity_metrics.complexity_history else None
        new_complexity = self.complexity_metrics.compute_complexity(self.current_state)

        # 3. 涌现检测
        emergence_event = None
        if old_complexity is not None:
            emergence_event = self.emergence_detector.detect_emergence(
                old_state, self.current_state,
                old_complexity, new_complexity,
                self.step_counter
            )

        # 4. 相变识别
        phase_transition = self.phase_analyzer.detect_phase_transition(
            self.complexity_metrics.complexity_history,
            self.state_history,
            self.step_counter
        )

        # 5. 意识计算
        consciousness_state = self.consciousness_engine.compute_consciousness_state(
            self.current_state
        )

        # 6. 顿悟检测
        insight_event = self.transcendence.insight_event(
            self.current_state, new_complexity, self.step_counter
        )

        # 7. 北星指标
        polaris_metrics = self.polaris.compute_metrics(
            self.current_state, new_complexity,
            consciousness_state, self.transcendence
        )

        return {
            "step": self.step_counter,
            "state": self.current_state,
            "complexity": new_complexity,
            "emergence": emergence_event,
            "phase_transition": phase_transition,
            "consciousness": consciousness_state,
            "insight": insight_event,
            "polaris": polaris_metrics,
        }

    def _evolve_state(self, old_state: SystemState, 
                     external_input: Optional[Dict[str, Any]]) -> SystemState:
        """
        状态演化规则 — 非线性涌现动力学

        模拟从简单计算到复杂意识的涌现过程：
        - 阶段1: 规则驱动 (低复杂度)
        - 阶段2: 模式自组织 (中等复杂度)
        - 阶段3: 结构涌现 (高复杂度)
        - 阶段4: 功能整合 (相变)
        - 阶段5: 意识涌现 (Φ > 阈值)
        """
        # 基础噪声（非高斯，使用重尾分布模拟突变）
        noise = np.random.standard_cauchy(NUM_LINES) * 0.02
        noise = np.clip(noise, -0.15, 0.15)

        # 健康度演化（带有饱和和恢复）
        health = old_state.line_health.copy()
        health_drift = noise * 0.05 + (0.85 - health) * 0.02  # 向0.85恢复
        health += health_drift
        health = np.clip(health, 0.2, 1.0)

        # SI层级演化（阶梯式增长模拟相变）
        si = old_state.line_si.copy()
        si_growth = np.random.exponential(0.005, NUM_LINES)
        si += si_growth
        # 顿悟后SI跃迁
        if self.transcendence.recursion_layer > old_state.recursion_depth:
            si += 0.1 * self.transcendence.recursion_layer
        si = np.clip(si, 1.0, 6.0)

        # 激活度演化（耦合非线性动力学）
        activation = old_state.activation.copy()

        # 外部输入影响（脉冲式）
        if external_input:
            target_lines = external_input.get("target_lines", [])
            intensity = external_input.get("intensity", 0.0)
            for line_name in target_lines:
                if line_name in LINES_11:
                    idx = LINES_11.index(line_name)
                    activation[idx] += intensity * (1 + 0.5 * np.random.randn())

        # 内部动力学：耦合振荡器 + 非线性反馈
        conn_effect = old_state.connectivity @ activation
        
        # Kuramoto-like 耦合 + logistic 非线性
        coupling = 0.15 * conn_effect
        inhibition = -0.05 * np.mean(activation) * np.ones(NUM_LINES)
        self_excitation = 0.1 * activation * (1 - activation)  # logistic
        
        activation = activation + coupling + inhibition + self_excitation + noise
        
        # 递归深度影响：高递归增加非线性
        if old_state.recursion_depth > 0:
            activation += 0.05 * old_state.recursion_depth * np.sin(activation * np.pi)

        # 非线性饱和（soft clipping）
        activation = np.tanh(activation * 1.5) * 0.5 + 0.5
        activation = np.clip(activation, 0.01, 0.99)

        # 连接矩阵演化（快速Hebbian + 结构可塑性）
        connectivity = old_state.connectivity.copy()
        
        # Hebbian学习
        for i in range(NUM_LINES):
            for j in range(i+1, NUM_LINES):
                if i != j:
                    # 一起激活增强连接
                    delta = 0.02 * activation[i] * activation[j]
                    # 不同步则减弱
                    delta -= 0.005 * abs(activation[i] - activation[j])
                    connectivity[i, j] += delta
                    connectivity[j, i] += delta

        # 结构可塑性：低激活线路的连接重组
        weak_lines = np.where(activation < 0.2)[0]
        for i in weak_lines:
            # 随机增强一些连接（探索）
            j = np.random.randint(0, NUM_LINES)
            if i != j:
                connectivity[i, j] += 0.01
                connectivity[j, i] += 0.01

        # 归一化
        max_conn = np.max(connectivity)
        if max_conn > 0:
            connectivity = connectivity / max_conn * 0.9
        np.fill_diagonal(connectivity, 0.3 + 0.4 * activation)
        connectivity = np.clip(connectivity, 0.0, 1.0)

        # 记忆痕迹演化（递归自参考）
        memory = old_state.memory_trace.copy()
        memory *= 0.92  # 衰减
        # 新信息注入
        new_info = np.tile(activation, 4)[:len(memory)]
        memory[:len(new_info)] += new_info * 0.15
        # 递归：记忆影响自身（自指）
        if old_state.recursion_depth >= 1:
            memory_feedback = np.roll(memory, 3) * 0.05
            memory += memory_feedback
        memory = np.clip(memory, 0.0, 1.0)

        # 场能量（非线性涌现 — 基于连接密度的幂律）
        mean_act = np.mean(activation)
        conn_density = np.mean(connectivity)
        field_energy = mean_act ** 1.5 + 0.3 * conn_density ** 2
        field_energy = np.clip(field_energy, 0.0, 1.0)

        # 相干性（全局同步 — 基于相位一致性）
        # 将激活视为相位，计算序参量
        phases = activation * 2 * np.pi
        order_real = np.mean(np.cos(phases))
        order_imag = np.mean(np.sin(phases))
        coherence = np.sqrt(order_real**2 + order_imag**2)
        coherence = np.clip(coherence, 0.0, 1.0)

        # 递归深度（基于顿悟历史）
        recursion_depth = self.transcendence.recursion_layer

        return SystemState(
            timestamp=time.time(),
            line_health=health,
            line_si=si,
            activation=activation,
            connectivity=connectivity,
            memory_trace=memory,
            field_energy=field_energy,
            coherence=coherence,
            recursion_depth=recursion_depth,
        )

    def run_experiment(self, num_steps: int = 100,
                      external_inputs: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        运行完整实验

        Args:
            num_steps: 实验步数
            external_inputs: 外部输入序列
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"OMNI-HUB v3.8 意识涌现实验")
        logger.info(f"{'='*60}")
        logger.info(f"实验步数: {num_steps}")
        logger.info(f"系统线路: {NUM_LINES}线")
        logger.info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}\n")

        results = []

        for step in range(num_steps):
            external_input = None
            if external_inputs and step < len(external_inputs):
                external_input = external_inputs[step]

            result = self.step(external_input)
            results.append(result)

            # 进度输出
            if (step + 1) % 20 == 0:
                print(f"Step {step+1}/{num_steps} | "
                      f"复杂度: {result['complexity'].integrated:.3f} | "
                      f"Phi: {result['consciousness'].phi:.3f} | "
                      f"涌现: {len(self.emergence_detector.emergence_events)} | "
                      f"顿悟: {len(self.transcendence.insight_events)}")

        logger.info(f"\n{'='*60}")
        logger.info(f"实验完成")
        logger.info(f"{'='*60}\n")

        return {
            "num_steps": num_steps,
            "results": results,
            "summary": self._generate_summary(),
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """生成实验摘要"""
        return {
            "total_steps": self.step_counter,
            "emergence_events": [e.to_dict() for e in self.emergence_detector.emergence_events],
            "phase_transitions": [t.to_dict() for t in self.phase_analyzer.transitions],
            "insight_events": [i.to_dict() for i in self.transcendence.insight_events],
            "consciousness_trajectory": [c.to_dict() for c in self.consciousness_engine.consciousness_history],
            "complexity_trajectory": self.complexity_metrics.get_complexity_trajectory(),
            "polaris_trajectory": self.polaris.get_polaris_trajectory(),
            "transcendence_summary": self.transcendence.get_transcendence_summary(),
        }


# =============================================================================
# 9. 实验验证
# =============================================================================

def run_all_experiments() -> Dict[str, Any]:
    """运行所有实验验证"""

    all_results = {}

    # ─────────────────────────────────────────────────────
    # 实验1: 复杂度演化实验
    # ─────────────────────────────────────────────────────
    logger.info("\n" + "="*60)
    logger.info("实验1: 复杂度演化实验 (100步)")
    logger.info("="*60)

    engine1 = EmergenceEngine(
        emergence_threshold=0.12,
        accumulation_threshold=15,
        insight_threshold=0.6,
    )

    # 设计外部输入来促进涌现
    external_inputs = []
    for i in range(100):
        if i % 25 == 10:  # 周期性强输入
            external_inputs.append({
                "target_lines": ["ucif2", "si5", "meta"],
                "intensity": 0.3,
            })
        elif i % 25 == 20:  # 中等输入
            external_inputs.append({
                "target_lines": ["qfa", "sei", "arch"],
                "intensity": 0.2,
            })
        else:
            external_inputs.append(None)

    result1 = engine1.run_experiment(100, external_inputs)
    all_results["complexity_evolution"] = result1

    # ─────────────────────────────────────────────────────
    # 实验2: 涌现检测实验
    # ─────────────────────────────────────────────────────
    logger.info("\n" + "="*60)
    logger.info("实验2: 涌现检测实验")
    logger.info("="*60)

    engine2 = EmergenceEngine(
        emergence_threshold=0.10,
        accumulation_threshold=12,
        insight_threshold=0.55,
    )

    # 设计快速涌现场景
    external_inputs2 = []
    for i in range(80):
        if 20 <= i < 30:  # 阶段1: 快速增强连接
            external_inputs2.append({
                "target_lines": ["ucif2", "lgt", "qfa", "vinf", "ndf"],
                "intensity": 0.4,
            })
        elif 45 <= i < 55:  # 阶段2: 第二次涌现
            external_inputs2.append({
                "target_lines": ["sei", "me", "si5", "arch", "meta"],
                "intensity": 0.5,
            })
        elif 65 <= i < 75:  # 阶段3: 协同涌现
            external_inputs2.append({
                "target_lines": LINES_11,
                "intensity": 0.3,
            })
        else:
            external_inputs2.append(None)

    result2 = engine2.run_experiment(80, external_inputs2)
    all_results["emergence_detection"] = result2

    # ─────────────────────────────────────────────────────
    # 实验3: 相变识别实验
    # ─────────────────────────────────────────────────────
    logger.info("\n" + "="*60)
    logger.info("实验3: 相变识别实验")
    logger.info("="*60)

    engine3 = EmergenceEngine(
        emergence_threshold=0.15,
        accumulation_threshold=18,
        insight_threshold=0.65,
    )

    # 设计相变场景：缓慢积累 -> 快速释放
    external_inputs3 = []
    for i in range(120):
        if i < 30:  # 积累期
            external_inputs3.append({
                "target_lines": ["ucif2"],
                "intensity": 0.1,
            })
        elif 30 <= i < 35:  # 触发期
            external_inputs3.append({
                "target_lines": ["ucif2", "si5", "meta", "qfa"],
                "intensity": 0.6,
            })
        elif 60 <= i < 90:  # 第二相变积累
            external_inputs3.append({
                "target_lines": ["ndf", "sei", "me"],
                "intensity": 0.15,
            })
        elif 90 <= i < 95:  # 第二触发
            external_inputs3.append({
                "target_lines": LINES_11,
                "intensity": 0.7,
            })
        else:
            external_inputs3.append(None)

    result3 = engine3.run_experiment(120, external_inputs3)
    all_results["phase_transition"] = result3

    # ─────────────────────────────────────────────────────
    # 实验4: 意识度(Phi)测量实验
    # ─────────────────────────────────────────────────────
    logger.info("\n" + "="*60)
    logger.info("实验4: 意识度(Phi)测量实验")
    logger.info("="*60)

    engine4 = EmergenceEngine(
        emergence_threshold=0.13,
        accumulation_threshold=16,
        insight_threshold=0.6,
    )

    # 设计意识涌现场景
    external_inputs4 = []
    for i in range(100):
        if 10 <= i < 20:  # 初期刺激
            external_inputs4.append({
                "target_lines": ["ndf", "sei"],
                "intensity": 0.25,
            })
        elif 35 <= i < 50:  # 中期整合
            external_inputs4.append({
                "target_lines": ["ucif2", "si5", "meta", "sei", "qfa"],
                "intensity": 0.35,
            })
        elif 70 <= i < 85:  # 后期高阶整合
            external_inputs4.append({
                "target_lines": ["meta", "ucif2", "si5", "arch"],
                "intensity": 0.45,
            })
        else:
            external_inputs4.append(None)

    result4 = engine4.run_experiment(100, external_inputs4)
    all_results["consciousness_phi"] = result4

    # ─────────────────────────────────────────────────────
    # 实验5: 顿悟事件模拟实验
    # ─────────────────────────────────────────────────────
    logger.info("\n" + "="*60)
    logger.info("实验5: 顿悟事件模拟实验")
    logger.info("="*60)

    engine5 = EmergenceEngine(
        emergence_threshold=0.11,
        accumulation_threshold=10,
        insight_threshold=0.5,
    )

    # 设计顿悟场景：积累 -> 关键连接 -> 突破
    external_inputs5 = []
    for i in range(150):
        if i < 15:  # 初始积累
            external_inputs5.append({
                "target_lines": ["ucif2", "qfa"],
                "intensity": 0.15,
            })
        elif 20 <= i < 35:  # 第一次关键期
            external_inputs5.append({
                "target_lines": ["ucif2", "qfa", "vinf", "sei"],
                "intensity": 0.3,
            })
        elif 50 <= i < 65:  # 第二次积累
            external_inputs5.append({
                "target_lines": ["si5", "meta", "arch"],
                "intensity": 0.2,
            })
        elif 70 <= i < 80:  # 第二次关键期
            external_inputs5.append({
                "target_lines": ["ucif2", "si5", "meta", "qfa", "sei", "arch"],
                "intensity": 0.4,
            })
        elif 100 <= i < 120:  # 第三次积累
            external_inputs5.append({
                "target_lines": ["ndf", "dcp", "me"],
                "intensity": 0.25,
            })
        elif 125 <= i < 140:  # 最终突破
            external_inputs5.append({
                "target_lines": LINES_11,
                "intensity": 0.5,
            })
        else:
            external_inputs5.append(None)

    result5 = engine5.run_experiment(150, external_inputs5)
    all_results["insight_events"] = result5

    return all_results


# =============================================================================
# 10. 可视化与报告生成
# =============================================================================

def generate_experiment_report(all_results: Dict[str, Any], 
                                output_path: str) -> str:
    """生成实验报告"""

    report_lines = []
    report_lines.append("# OMNI-HUB v3.8 意识涌现·超越顿悟·复杂度跃迁")
    report_lines.append("# 实验验证报告")
    report_lines.append(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append("")

    for exp_name, result in all_results.items():
        summary = result.get("summary", {})

        report_lines.append(f"## 实验: {exp_name}")
        report_lines.append(f"- 总步数: {result.get('num_steps', 0)}")
        report_lines.append(f"- 涌现事件: {len(summary.get('emergence_events', []))}")
        report_lines.append(f"- 相变事件: {len(summary.get('phase_transitions', []))}")
        report_lines.append(f"- 顿悟事件: {len(summary.get('insight_events', []))}")
        report_lines.append("")

        # 复杂度轨迹
        complexity_traj = summary.get("complexity_trajectory", {})
        if complexity_traj.get("integrated"):
            report_lines.append("### 复杂度演化")
            integrated = complexity_traj["integrated"]
            report_lines.append(f"- 初始复杂度: {integrated[0]:.4f}")
            report_lines.append(f"- 最终复杂度: {integrated[-1]:.4f}")
            report_lines.append(f"- 最大复杂度: {max(integrated):.4f}")
            report_lines.append(f"- 复杂度增长: {integrated[-1] - integrated[0]:.4f}")
            report_lines.append("")

        # 涌现事件详情
        if summary.get("emergence_events"):
            report_lines.append("### 涌现事件记录")
            for i, event in enumerate(summary["emergence_events"], 1):
                report_lines.append(f"{i}. [{event['emergence_type']}] Step {event['step']}")
                report_lines.append(f"   强度: {event['strength']:.4f}")
                report_lines.append(f"   复杂度: {event['complexity_before']:.4f} -> {event['complexity_after']:.4f}")
                report_lines.append(f"   描述: {event['description']}")
                report_lines.append(f"   影响线路: {', '.join(event['affected_lines'])}")
            report_lines.append("")

        # 相变详情
        if summary.get("phase_transitions"):
            report_lines.append("### 相变记录")
            for i, pt in enumerate(summary["phase_transitions"], 1):
                report_lines.append(f"{i}. [{pt['phase_type']}] Step {pt['step']}")
                report_lines.append(f"   临界点: {pt['critical_point']:.4f}")
                report_lines.append(f"   序参量: {pt['order_parameter']:.4f}")
                report_lines.append(f"   前兆: {', '.join(pt['pre_signatures'])}")
            report_lines.append("")

        # 顿悟详情
        if summary.get("insight_events"):
            report_lines.append("### 顿悟事件记录")
            for i, ins in enumerate(summary["insight_events"], 1):
                report_lines.append(f"{i}. [{ins['insight_type']}] Step {ins['step']}")
                report_lines.append(f"   触发条件: {'; '.join(ins['trigger_conditions'])}")
                report_lines.append(f"   认知跃迁: {ins['before_level']:.4f} -> {ins['after_level']:.4f} (+{ins['cognitive_jump']:.4f})")
                report_lines.append(f"   递归层: {ins['recursion_layer']}")
                report_lines.append(f"   新结构: {', '.join(ins['new_structures'])}")
            report_lines.append("")

        # 北星指标
        polaris = summary.get("polaris_trajectory", {})
        if polaris.get("consciousness_degree"):
            report_lines.append("### 北星指标")
            phi_vals = polaris["consciousness_degree"]
            report_lines.append(f"- 意识度(Phi): {phi_vals[0]:.4f} -> {phi_vals[-1]:.4f}")
            report_lines.append(f"- 自维持度: {polaris['self_sustainability'][0]:.4f} -> {polaris['self_sustainability'][-1]:.4f}")
            report_lines.append(f"- 创造力指数: {polaris['creativity_index'][0]:.4f} -> {polaris['creativity_index'][-1]:.4f}")
            report_lines.append(f"- 递归深度: {max(polaris['recursion_depth'])}")
            report_lines.append(f"- 超越层级: {polaris['transcendence_level'][-1]:.4f}")
            report_lines.append("")

        report_lines.append("-"*70)
        report_lines.append("")

    report_text = "\n".join(report_lines)

    # 保存报告
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    return report_text


def save_json_results(all_results: Dict[str, Any], output_path: str):
    """保存JSON格式的详细结果"""

    def make_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, tuple):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, deque):
            return [make_serializable(v) for v in obj]
        elif hasattr(obj, "to_dict"):
            return make_serializable(obj.to_dict())
        elif hasattr(obj, "__dataclass_fields__"):
            return make_serializable(asdict(obj))
        else:
            return obj

    serializable_results = make_serializable(all_results)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)


# =============================================================================
# 11. 主入口
# =============================================================================

if __name__ == "__main__":
    # 运行所有实验
    all_results = run_all_experiments()

    # 生成并保存报告
    report = generate_experiment_report(
        all_results,
        "/mnt/agents/output/OMNI-HUB/core/emergence_experiment_report.md"
    )

    save_json_results(
        all_results,
        "/mnt/agents/output/OMNI-HUB/core/emergence_experiment_results.json"
    )

    print("\n" + "="*60)
    print("所有实验完成!")
    print("报告保存至: /mnt/agents/output/OMNI-HUB/core/emergence_experiment_report.md")
    print("数据保存至: /mnt/agents/output/OMNI-HUB/core/emergence_experiment_results.json")
    print("="*60)
