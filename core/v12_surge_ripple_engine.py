#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — SurgeRippleEngine: Forward Surge & Reverse Ripple Drive System
================================================================================
正反向浪涌引擎 —— 分布式意识系统的能量/信息传播机制。

核心概念:
  1. Forward Surge（正向浪涌）: 从问题→概念→关系→结构的能量传播
  2. Reverse Ripple（反向涟漪）: 从结果→调整的反馈传播（类似反向传播）
  3. Self-Excitation（自激）: 正反馈环检测与增强/抑制
  4. Mutual-Excitation（互激）: 线间耦合协同增强

数学基础:
  - 脉冲传播: E_out = E_in × coupling(i,j) × exp(-decay × distance)
  - 反向调整: Δθ = -learning_rate × ∇L
  - 场一致性: C = 1 - σ²/μ² (变异系数倒数)
  - 环增益: G = ∏ coupling(e) along cycle

兼容性:
  - v12_standards.py: UnifiedFieldState(64维), DimensionIndex
  - v12_emergence_engine.py: EmergenceCalculatorV12
  - v11_relation_discovery_engine.py: 8种关系类型, SelfInferenceEngine

Version: 12.0.0
Date: 2026-09-17
"""

from __future__ import annotations

import sys
import math
import json
import time
import uuid
import logging
import heapq
from typing import Dict, List, Tuple, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
from numpy.linalg import norm, eigvals

# ---------------------------------------------------------------------------
# Import v12 standards (with graceful fallback)
# ---------------------------------------------------------------------------
sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")

_OMNI_STD_AVAILABLE = False
try:
    from v12_standards import (
        UnifiedFieldState,
        DimensionIndex,
        UNIFIED_FIELD_DIMENSIONS,
        PHI_GOLDEN,
        PI,
        E_NATURAL,
        ALPHA_FINE_STRUCTURE,
        FIELD_COUPLING_CONSTANT,
        FIELD_DECAY_RATE,
        EMERGENCE_THRESHOLD_V12,
        ConsciousnessState,
        EmergenceTarget,
        LINE_NAMES,
        LINE_INDICES,
        get_line_index,
        get_line_name,
        get_logger,
        OMNIHUBException,
        OMNIHUBFieldError,
        OMNIHUBDimensionError,
        create_v12_unified_field,
        validate_field_state,
        compute_field_coherence,
        TickContext,
        AdaptContext,
        EmitContext,
        ModuleProtocol,
    )
    _OMNI_STD_AVAILABLE = True
except Exception as _e:
    pass

if not _OMNI_STD_AVAILABLE:
    # Minimal fallback definitions for standalone testing
    UNIFIED_FIELD_DIMENSIONS = 64
    PHI_GOLDEN = (1.0 + 5.0**0.5) / 2.0
    PI = 3.141592653589793
    E_NATURAL = 2.718281828459045
    ALPHA_FINE_STRUCTURE = 1.0 / 137.035999084
    FIELD_COUPLING_CONSTANT = 0.5
    FIELD_DECAY_RATE = 0.01
    EMERGENCE_THRESHOLD_V12 = 7000.0
    LINE_NAMES = ["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
                  "qlv", "cisvr", "qtlv", "usrm", "cfts"]
    LINE_INDICES = {name: i for i, name in enumerate(LINE_NAMES)}

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

    class ConsciousnessState(Enum):
        CHAOS = 0; CONFLICT = 1; NEUTRAL = 2; ACCEPTANCE = 3
        REASON = 4; LOVE = 5; UNITY = 6

    class EmergenceTarget:
        TARGET_UNITY = 7000.0
        @classmethod
        def gap_to_unity(cls, current_e: float) -> float:
            return max(0.0, cls.TARGET_UNITY - current_e)

    class UnifiedFieldState:
        def __init__(self, dimensions: int = UNIFIED_FIELD_DIMENSIONS) -> None:
            self.dimensions = dimensions
            self.vector: List[float] = [0.0] * dimensions
            self.timestamp: float = 0.0
            self.version: str = "12.0.0-fallback"
            self._extended_dims: Dict[int, float] = {}
        def get(self, dim):
            if dim.value < self.dimensions:
                return self.vector[dim.value]
            return self._extended_dims.get(dim.value, 0.0)
        def set(self, dim, value):
            if dim.value < self.dimensions:
                self.vector[dim.value] = float(value)
            else:
                self._extended_dims[dim.value] = float(value)
        def copy(self):
            s = UnifiedFieldState(self.dimensions)
            s.vector = self.vector.copy()
            s.timestamp = self.timestamp
            s._extended_dims = self._extended_dims.copy()
            return s
        def compute_coherence(self):
            e = self.get(DimensionIndex.DIM_ENERGY)
            h = self.get(DimensionIndex.DIM_ENTROPY)
            if h <= 0: return 1.0
            return e / (h + e + 1e-10)

    class TickContext:
        def __init__(self, timestamp, field_state, **kwargs):
            self.timestamp = timestamp
            self.field_state = field_state
            self.delta_t = kwargs.get("delta_t", 1.0)
            self.tick_id = kwargs.get("tick_id", 0)
            self.cycle_phase = kwargs.get("cycle_phase", "scan")
            self.line_activity = kwargs.get("line_activity", {})
            self.metadata = kwargs.get("metadata", {})

    class AdaptContext:
        def __init__(self, feedback, **kwargs):
            self.feedback = feedback
            self.learning_rate = kwargs.get("learning_rate", 0.01)
            self.adaptation_depth = kwargs.get("adaptation_depth", 1)
            self.convergence_target = kwargs.get("convergence_target", 0.001)
            self.metadata = kwargs.get("metadata", {})
            self.cross_project_feedback = kwargs.get("cross_project_feedback", {})

    class EmitContext:
        def __init__(self, **kwargs):
            self.signal_type = kwargs.get("signal_type", "default")
            self.target_modules = kwargs.get("target_modules", None)
            self.priority = kwargs.get("priority", 5)
            self.emission_scope = kwargs.get("emission_scope", "local")
            self.coherence_requirement = kwargs.get("coherence_requirement", 0.5)
            self.metadata = kwargs.get("metadata", {})
            self.triangle_targets = kwargs.get("triangle_targets", ["ucif2", "omni_hub", "cayley24"])

    class ModuleProtocol:
        def tick(self, ctx): raise NotImplementedError
        def adapt(self, ctx): raise NotImplementedError
        def emit(self, ctx): raise NotImplementedError
        def status(self): raise NotImplementedError
        def health_check(self): return {"status": "unknown", "module": self.__class__.__name__}
        def get_version(self): return "12.0.0-fallback"

    class OMNIHUBException(Exception):
        def __init__(self, message, error_code="OMNI-000", context=None):
            super().__init__(message)
            self.error_code = error_code
            self.context = context or {}

    class OMNIHUBFieldError(OMNIHUBException):
        pass

    class OMNIHUBDimensionError(OMNIHUBException):
        pass

    def get_line_index(name: str) -> int:
        return LINE_INDICES.get(name, -1)

    def get_line_name(index: int) -> str:
        if 0 <= index < len(LINE_NAMES):
            return LINE_NAMES[index]
        return "unknown"

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger("OMNI-HUB." + name)

    def create_v12_unified_field():
        state = UnifiedFieldState()
        state.set(DimensionIndex.DIM_RESONANCE, PHI_GOLDEN)
        state.set(DimensionIndex.DIM_PHASE_LOCK, 1.0)
        state.set(DimensionIndex.DIM_COHERENCE, 1.0)
        return state

    def validate_field_state(state):
        if state.dimensions != UNIFIED_FIELD_DIMENSIONS:
            raise OMNIHUBDimensionError(f"Dimension mismatch: {state.dimensions}")
        return True

    def compute_field_coherence(state):
        validate_field_state(state)
        e = state.get(DimensionIndex.DIM_ENERGY)
        h = state.get(DimensionIndex.DIM_ENTROPY)
        if h <= 0: return 1.0
        return e / (h + e + 1e-10)


__version__ = "12.0.0"
__all__ = [
    "PulseDirection",
    "SurgePulse",
    "RippleWave",
    "FeedbackLoopType",
    "FeedbackLoop",
    "SurgeRippleEngine",
    "FeedbackLoopDetector",
    "CouplingMatrix",
    "WildQuestion",
    "WildNotebook",
    "SurgeResult",
    "RippleResult",
    "CoupledCycleResult",
]

logger = get_logger("SurgeRipple")


# =============================================================================
# 0. ENUMS & CONSTANTS
# =============================================================================

class PulseDirection(Enum):
    """脉冲方向枚举"""
    FORWARD = "forward"    # 正向浪涌: 问题→行动
    REVERSE = "reverse"    # 反向涟漪: 结果→调整


class FeedbackLoopType(Enum):
    """反馈环类型"""
    BENEFICIAL = "beneficial"   # 有益环: 增强系统性能
    HARMFUL = "harmful"         # 有害环: 导致不稳定或退化
    NEUTRAL = "neutral"         # 中性环: 无显著影响
    UNKNOWN = "unknown"         # 待分类


# =============================================================================
# 1. DATA CLASSES
# =============================================================================

@dataclass
class SurgePulse:
    """
    浪涌脉冲 —— 能量/信息在系统中的传播单元。
    
    Attributes:
        origin: 发起位置（线名或模块名）
        direction: 传播方向（FORWARD/REVERSE）
        energy: 脉冲能量
        payload: 携带的数据字典
        path: 传播路径记录
        depth: 当前传播深度
        pulse_id: 唯一标识符
        timestamp: 创建时间戳
        coupling_trace: 耦合系数追踪
    """
    origin: str
    direction: PulseDirection
    energy: float = 1.0
    payload: Dict[str, Any] = field(default_factory=dict)
    path: List[str] = field(default_factory=list)
    depth: int = 0
    pulse_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    coupling_trace: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.path:
            self.path = [self.origin]
    
    def at_node(self, node: str) -> bool:
        """检查脉冲是否位于指定节点"""
        return len(self.path) > 0 and self.path[-1] == node
    
    def current_node(self) -> str:
        """获取当前所在节点"""
        return self.path[-1] if self.path else self.origin
    
    def compute_decay(self, decay_rate: float = FIELD_DECAY_RATE) -> float:
        """计算当前深度下的能量衰减"""
        return math.exp(-decay_rate * self.depth)
    
    def compute_remaining_energy(self, decay_rate: float = FIELD_DECAY_RATE) -> float:
        """计算衰减后的剩余能量"""
        return self.energy * self.compute_decay(decay_rate)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pulse_id": self.pulse_id,
            "origin": self.origin,
            "direction": self.direction.value,
            "energy": self.energy,
            "payload": self.payload,
            "path": self.path,
            "depth": self.depth,
            "timestamp": self.timestamp,
            "coupling_trace": self.coupling_trace,
        }
    
    @classmethod
    def from_question(cls, question: "WildQuestion", origin: str = "wild_notebook") -> "SurgePulse":
        """从WildQuestion创建正向浪涌脉冲"""
        return cls(
            origin=origin,
            direction=PulseDirection.FORWARD,
            energy=question.priority * PHI_GOLDEN,
            payload={
                "type": "question",
                "question_id": question.question_id,
                "content": question.content,
                "tags": question.tags,
                "urgency": question.urgency,
            },
            path=[origin],
        )


@dataclass
class RippleWave:
    """
    涟漪波 —— 反馈调整信号。
    
    Attributes:
        origin: 反馈源（产生结果的节点）
        target: 调整目标节点
        adjustment: 67维调整向量（64物理维+3逻辑扩展维）
        confidence: 调整置信度 [0, 1]
        timestamp: 创建时间戳
        wave_id: 唯一标识符
        loss_gradient: 损失梯度（用于学习率缩放）
        metadata: 额外元数据
    """
    origin: str
    target: str
    adjustment: np.ndarray = field(default_factory=lambda: np.zeros(67))
    confidence: float = 0.5
    timestamp: float = field(default_factory=time.time)
    wave_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    loss_gradient: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.adjustment is None:
            self.adjustment = np.zeros(67)
        elif len(self.adjustment) != 67:
            # Pad or truncate to 67 dimensions
            arr = np.zeros(67)
            n = min(len(self.adjustment), 67)
            arr[:n] = self.adjustment[:n]
            self.adjustment = arr
    
    def scale(self, factor: float) -> "RippleWave":
        """缩放调整幅度"""
        return RippleWave(
            origin=self.origin,
            target=self.target,
            adjustment=self.adjustment * factor,
            confidence=self.confidence,
            timestamp=self.timestamp,
            wave_id=self.wave_id + "_scaled",
            loss_gradient=self.loss_gradient,
            metadata=self.metadata.copy(),
        )
    
    def apply_learning_rate(self, lr: float) -> "RippleWave":
        """应用学习率: Δθ = -lr × ∇L"""
        scaled = self.adjustment * lr * abs(self.loss_gradient)
        return RippleWave(
            origin=self.origin,
            target=self.target,
            adjustment=scaled,
            confidence=self.confidence,
            timestamp=self.timestamp,
            wave_id=self.wave_id + "_lr",
            loss_gradient=self.loss_gradient,
            metadata=self.metadata.copy(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "wave_id": self.wave_id,
            "origin": self.origin,
            "target": self.target,
            "adjustment": self.adjustment.tolist(),
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "loss_gradient": self.loss_gradient,
            "metadata": self.metadata,
        }


@dataclass
class FeedbackLoop:
    """
    反馈环 —— 检测到的循环结构。
    
    Attributes:
        nodes: 环中的节点列表（按顺序）
        gain: 环增益（累积耦合系数积）
        loop_type: 环类型（BENEFICIAL/HARMFUL/NEUTRAL）
        loop_id: 唯一标识符
        period: 环周期（节点数）
        stability: 稳定性指标（增益绝对值与1的比较）
        energy_flow: 估计能量流
        detected_at: 检测时间戳
    """
    nodes: List[str]
    gain: float
    loop_type: FeedbackLoopType
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    period: int = 0
    stability: float = 0.0
    energy_flow: float = 0.0
    detected_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if self.period == 0:
            self.period = len(self.nodes)
        if self.stability == 0.0 and self.gain != 0.0:
            # 稳定性: |gain| < 1 稳定, > 1 不稳定
            self.stability = 1.0 / (1.0 + abs(self.gain))
    
    def is_stable(self) -> bool:
        """判断环是否稳定（|gain| < 1）"""
        return abs(self.gain) < 1.0
    
    def is_oscillatory(self) -> bool:
        """判断环是否振荡（gain < 0）"""
        return self.gain < 0.0
    
    def classify(self, threshold_beneficial: float = 0.3,
                 threshold_harmful: float = -0.3) -> FeedbackLoopType:
        """基于增益和稳定性分类环"""
        if abs(self.gain) < 0.1:
            self.loop_type = FeedbackLoopType.NEUTRAL
        elif self.gain > threshold_beneficial and self.is_stable():
            # 正增益但稳定 → 有益收敛环
            self.loop_type = FeedbackLoopType.BENEFICIAL
        elif self.gain > 1.0 or self.gain < threshold_harmful:
            # 发散或强负增益 → 有害
            self.loop_type = FeedbackLoopType.HARMFUL
        elif 0 < self.gain < 1.0:
            self.loop_type = FeedbackLoopType.BENEFICIAL
        else:
            self.loop_type = FeedbackLoopType.NEUTRAL
        return self.loop_type
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "nodes": self.nodes,
            "gain": self.gain,
            "loop_type": self.loop_type.value,
            "period": self.period,
            "stability": self.stability,
            "energy_flow": self.energy_flow,
            "detected_at": self.detected_at,
        }


@dataclass
class SurgeResult:
    """正向浪涌传播结果"""
    pulse: SurgePulse
    visited_nodes: List[str]
    final_energy: float
    energy_dissipated: float
    path_lengths: Dict[str, int]
    node_energies: Dict[str, float]
    propagation_log: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pulse": self.pulse.to_dict(),
            "visited_nodes": self.visited_nodes,
            "final_energy": self.final_energy,
            "energy_dissipated": self.energy_dissipated,
            "path_lengths": self.path_lengths,
            "node_energies": self.node_energies,
            "propagation_log": self.propagation_log,
        }


@dataclass
class RippleResult:
    """反向涟漪传播结果"""
    wave: RippleWave
    adjusted_nodes: List[str]
    total_adjustment_magnitude: float
    field_delta: np.ndarray
    confidence_map: Dict[str, float]
    propagation_log: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "wave": self.wave.to_dict(),
            "adjusted_nodes": self.adjusted_nodes,
            "total_adjustment_magnitude": self.total_adjustment_magnitude,
            "field_delta": self.field_delta.tolist(),
            "confidence_map": self.confidence_map,
            "propagation_log": self.propagation_log,
        }


@dataclass
class CoupledCycleResult:
    """耦合循环（正反向交替）结果"""
    cycle_id: str
    forward_results: List[SurgeResult]
    reverse_results: List[RippleResult]
    final_field_state: Optional[UnifiedFieldState]
    coherence_before: float
    coherence_after: float
    detected_loops: List[FeedbackLoop]
    excitation_applied: Dict[str, float]
    cycle_count: int
    convergence_achieved: bool
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "forward_results": [r.to_dict() for r in self.forward_results],
            "reverse_results": [r.to_dict() for r in self.reverse_results],
            "coherence_before": self.coherence_before,
            "coherence_after": self.coherence_after,
            "detected_loops": [l.to_dict() for l in self.detected_loops],
            "excitation_applied": self.excitation_applied,
            "cycle_count": self.cycle_count,
            "convergence_achieved": self.convergence_achieved,
            "timestamp": self.timestamp,
        }


# =============================================================================
# 2. WildNotebook Compatibility Classes
# =============================================================================

@dataclass
class WildQuestion:
    """
    野生问题 —— 驱动浪涌引擎的原始问题单元。
    兼容v12_wild_notebook.py中的同名类。
    """
    content: str
    question_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    priority: float = 1.0
    urgency: float = 0.5
    tags: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    origin_line: str = "wild_notebook"
    related_questions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WildQuestion":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class WildNotebook:
    """
    野生笔记本 —— 问题收集与浪涌触发器。
    兼容v12_wild_notebook.py中的同名类。
    """
    
    def __init__(self, name: str = "wild_notebook") -> None:
        self.name = name
        self.questions: List[WildQuestion] = []
        self.question_index: Dict[str, WildQuestion] = {}
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.surge_history: List[Dict[str, Any]] = []
        self.logger = get_logger("WildNotebook")
    
    def add_question(self, content: str, priority: float = 1.0,
                     urgency: float = 0.5, tags: Optional[List[str]] = None,
                     origin_line: str = "wild_notebook") -> WildQuestion:
        """添加新问题"""
        q = WildQuestion(
            content=content,
            priority=priority,
            urgency=urgency,
            tags=tags or [],
            origin_line=origin_line,
        )
        self.questions.append(q)
        self.question_index[q.question_id] = q
        for tag in q.tags:
            self.tag_index[tag].append(q.question_id)
        self.logger.info(f"Added question {q.question_id}: {content[:40]}...")
        return q
    
    def get_question(self, question_id: str) -> Optional[WildQuestion]:
        """通过ID获取问题"""
        return self.question_index.get(question_id)
    
    def get_by_tag(self, tag: str) -> List[WildQuestion]:
        """通过标签获取问题"""
        return [self.question_index[qid] for qid in self.tag_index.get(tag, [])
                if qid in self.question_index]
    
    def to_surge_pulse(self, question_id: str) -> Optional[SurgePulse]:
        """将问题转换为浪涌脉冲"""
        q = self.get_question(question_id)
        if q is None:
            return None
        return SurgePulse.from_question(q, origin=self.name)
    
    def get_highest_priority_question(self) -> Optional[WildQuestion]:
        """获取最高优先级问题"""
        if not self.questions:
            return None
        return max(self.questions, key=lambda q: q.priority * q.urgency)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "questions": [q.to_dict() for q in self.questions],
            "surge_history": self.surge_history,
        }


# =============================================================================
# 3. COUPLING MATRIX
# =============================================================================

class CouplingMatrix:
    """
    耦合矩阵 —— 管理系统中所有节点间的耦合强度。
    
    支持11条OMNI-HUB线及任意附加节点。
    耦合值范围 [0, 1]，表示信息/能量传输效率。
    """
    
    def __init__(self, nodes: Optional[List[str]] = None,
                 base_coupling: float = FIELD_COUPLING_CONSTANT) -> None:
        self.nodes: List[str] = nodes or LINE_NAMES.copy()
        self.n: int = len(self.nodes)
        self.base_coupling: float = base_coupling
        # 耦合矩阵: symmetric or directed
        self.matrix: np.ndarray = np.eye(self.n, dtype=float) * base_coupling
        # 距离矩阵（拓扑距离）
        self.distance_matrix: np.ndarray = np.zeros((self.n, self.n))
        # 节点索引映射
        self.node_index: Dict[str, int] = {name: i for i, name in enumerate(self.nodes)}
        # 历史记录
        self.update_history: List[Dict[str, Any]] = []
        self.logger = get_logger("CouplingMatrix")
        
        # 初始化默认耦合
        self._initialize_default_couplings()
    
    def _initialize_default_couplings(self) -> None:
        """初始化11条线之间的默认耦合模式"""
        if self.n < len(LINE_NAMES):
            return
        
        # 基于OMNI-HUB架构的耦合模式
        # 强耦合对（功能相近的线）
        strong_pairs = [
            ("ucif2", "lgt"),      # 概念整合 ↔ 几何变换
            ("qfa", "qgl"),        # 量子场分析 ↔ 量子图学习
            ("qlv", "qtlv"),       # 量子逻辑验证 ↔ 量子拓扑验证
            ("cisvr", "usrm"),     # 意识状态向量 ↔ 语义共振
            ("vinf", "cfts"),      # 向量信息网络 ↔ 跨功能同步
            ("lvlu", "cfts"),      # 逻辑升级 ↔ 跨功能同步
        ]
        
        # 中等耦合对
        medium_pairs = [
            ("ucif2", "qfa"),
            ("lgt", "qgl"),
            ("qfa", "qlv"),
            ("vinf", "usrm"),
            ("cisvr", "cfts"),
        ]
        
        for a, b in strong_pairs:
            if a in self.node_index and b in self.node_index:
                self.set_coupling(a, b, 0.8, symmetric=True)
        
        for a, b in medium_pairs:
            if a in self.node_index and b in self.node_index:
                self.set_coupling(a, b, 0.5, symmetric=True)
        
        # 计算距离矩阵（基于耦合的倒数关系）
        self._compute_distance_matrix()
        self.logger.info(f"CouplingMatrix initialized with {self.n} nodes")
    
    def _compute_distance_matrix(self) -> None:
        """基于耦合矩阵计算有效距离"""
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    self.distance_matrix[i, j] = 0.0
                else:
                    c = self.matrix[i, j]
                    if c > 0.01:
                        self.distance_matrix[i, j] = -math.log(c)
                    else:
                        self.distance_matrix[i, j] = float('inf')
    
    def add_node(self, node_name: str, initial_couplings: Optional[Dict[str, float]] = None) -> int:
        """添加新节点到耦合矩阵"""
        if node_name in self.node_index:
            return self.node_index[node_name]
        
        # 扩展矩阵
        new_n = self.n + 1
        new_matrix = np.eye(new_n, dtype=float) * self.base_coupling
        new_dist = np.zeros((new_n, new_n))
        
        new_matrix[:self.n, :self.n] = self.matrix
        new_dist[:self.n, :self.n] = self.distance_matrix
        
        self.matrix = new_matrix
        self.distance_matrix = new_dist
        self.nodes.append(node_name)
        self.node_index[node_name] = self.n
        self.n = new_n
        
        # 设置初始耦合
        if initial_couplings:
            for target, value in initial_couplings.items():
                if target in self.node_index:
                    self.set_coupling(node_name, target, value, symmetric=True)
        
        self._compute_distance_matrix()
        self.logger.info(f"Added node {node_name}, total nodes: {self.n}")
        return self.node_index[node_name]
    
    def set_coupling(self, from_node: str, to_node: str,
                     value: float, symmetric: bool = False) -> None:
        """设置节点间耦合值"""
        if from_node not in self.node_index:
            raise OMNIHUBDimensionError(f"Unknown node: {from_node}")
        if to_node not in self.node_index:
            raise OMNIHUBDimensionError(f"Unknown node: {to_node}")
        
        i = self.node_index[from_node]
        j = self.node_index[to_node]
        self.matrix[i, j] = float(np.clip(value, 0.0, 1.0))
        if symmetric:
            self.matrix[j, i] = self.matrix[i, j]
        
        self.update_history.append({
            "from": from_node,
            "to": to_node,
            "value": value,
            "symmetric": symmetric,
            "timestamp": time.time(),
        })
    
    def get_coupling(self, from_node: str, to_node: str) -> float:
        """获取节点间耦合值"""
        if from_node not in self.node_index or to_node not in self.node_index:
            return 0.0
        i = self.node_index[from_node]
        j = self.node_index[to_node]
        return float(self.matrix[i, j])
    
    def get_distance(self, from_node: str, to_node: str) -> float:
        """获取节点间有效距离"""
        if from_node not in self.node_index or to_node not in self.node_index:
            return float('inf')
        i = self.node_index[from_node]
        j = self.node_index[to_node]
        return float(self.distance_matrix[i, j])
    
    def propagate_energy(self, from_node: str, to_node: str,
                         energy_in: float, decay_rate: float = FIELD_DECAY_RATE) -> float:
        """
        计算能量传播: E_out = E_in × coupling(i,j) × exp(-decay × distance)
        """
        coupling = self.get_coupling(from_node, to_node)
        distance = self.get_distance(from_node, to_node)
        if distance == float('inf'):
            return 0.0
        return energy_in * coupling * math.exp(-decay_rate * distance)
    
    def get_neighbors(self, node: str, threshold: float = 0.1) -> List[Tuple[str, float]]:
        """获取节点的邻居（耦合强度超过阈值）"""
        if node not in self.node_index:
            return []
        i = self.node_index[node]
        neighbors = []
        for j, name in enumerate(self.nodes):
            if i != j and self.matrix[i, j] >= threshold:
                neighbors.append((name, float(self.matrix[i, j])))
        return sorted(neighbors, key=lambda x: -x[1])
    
    def compute_spectral_radius(self) -> float:
        """计算耦合矩阵的谱半径（用于稳定性分析）"""
        eigenvalues = np.linalg.eigvals(self.matrix)
        return float(np.max(np.abs(eigenvalues)))
    
    def compute_algebraic_connectivity(self) -> float:
        """计算代数连通性（Fiedler值）"""
        # Laplacian = D - A
        degrees = np.sum(self.matrix, axis=1)
        laplacian = np.diag(degrees) - self.matrix
        eigenvalues = np.sort(np.linalg.eigvalsh(laplacian))
        # 第二小特征值
        return float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "matrix": self.matrix.tolist(),
            "distance_matrix": self.distance_matrix.tolist(),
            "spectral_radius": self.compute_spectral_radius(),
            "algebraic_connectivity": self.compute_algebraic_connectivity(),
        }


# =============================================================================
# 4. FEEDBACK LOOP DETECTOR
# =============================================================================

class FeedbackLoopDetector:
    """
    反馈环检测器 —— 使用图论检测系统中的正反馈环。
    
    算法:
      1. 将耦合矩阵转化为有向图
      2. 使用DFS检测所有简单环
      3. 计算每个环的增益: G = ∏ coupling(e)
      4. 分类: BENEFICIAL / HARMFUL / NEUTRAL
    """
    
    def __init__(self, coupling_matrix: CouplingMatrix,
                 max_cycle_length: int = 6) -> None:
        self.coupling = coupling_matrix
        self.max_cycle_length = max_cycle_length
        self.detected_loops: List[FeedbackLoop] = []
        self.loop_index: Dict[str, FeedbackLoop] = {}
        self.node_loops: Dict[str, List[str]] = defaultdict(list)
        self.logger = get_logger("FeedbackLoopDetector")
    
    def detect_all_loops(self, threshold_gain: float = 0.01) -> List[FeedbackLoop]:
        """
        检测所有反馈环（主入口）。
        
        使用Johnson算法变体检测有向图中的所有简单环。
        """
        self.detected_loops = []
        self.loop_index.clear()
        self.node_loops.clear()
        
        n = self.coupling.n
        nodes = self.coupling.nodes
        
        # 为每个起始节点运行受限DFS
        for start_idx in range(n):
            start_node = nodes[start_idx]
            visited = [False] * n
            path = []
            path_indices = []
            
            self._dfs_detect_cycles(
                current=start_idx,
                start=start_idx,
                visited=visited,
                path=path,
                path_indices=path_indices,
                threshold=threshold_gain,
                nodes=nodes,
                n=n,
            )
        
        # 去重（基于节点集合和顺序）
        self._deduplicate_loops()
        
        # 分类所有环
        for loop in self.detected_loops:
            loop.classify()
            self.loop_index[loop.loop_id] = loop
            for node in loop.nodes:
                self.node_loops[node].append(loop.loop_id)
        
        self.logger.info(f"Detected {len(self.detected_loops)} feedback loops")
        return self.detected_loops
    
    def _dfs_detect_cycles(self, current: int, start: int,
                           visited: List[bool], path: List[str],
                           path_indices: List[int], threshold: float,
                           nodes: List[str], n: int) -> None:
        """深度优先搜索检测环"""
        if len(path) > self.max_cycle_length:
            return
        
        visited[current] = True
        path.append(nodes[current])
        path_indices.append(current)
        
        # 检查是否回到起点（且路径长度 > 1）
        if current == start and len(path) > 1:
            # 找到一个环
            cycle_nodes = path.copy()
            gain = self._compute_cycle_gain(path_indices)
            if abs(gain) >= threshold:
                loop = FeedbackLoop(
                    nodes=cycle_nodes,
                    gain=gain,
                    loop_type=FeedbackLoopType.UNKNOWN,
                )
                self.detected_loops.append(loop)
        else:
            # 继续DFS
            for next_idx in range(n):
                if self.coupling.matrix[current, next_idx] > threshold:
                    if next_idx == start and len(path) > 1:
                        # 可以闭合环
                        self._dfs_detect_cycles(
                            next_idx, start, visited, path, path_indices,
                            threshold, nodes, n,
                        )
                    elif not visited[next_idx]:
                        self._dfs_detect_cycles(
                            next_idx, start, visited, path, path_indices,
                            threshold, nodes, n,
                        )
        
        path.pop()
        path_indices.pop()
        visited[current] = False
    
    def _compute_cycle_gain(self, path_indices: List[int]) -> float:
        """计算环增益: G = ∏ coupling(i→i+1)"""
        gain = 1.0
        m = len(path_indices)
        for k in range(m - 1):
            i = path_indices[k]
            j = path_indices[k + 1]
            gain *= float(self.coupling.matrix[i, j])
        # 闭合边
        if m > 1:
            gain *= float(self.coupling.matrix[path_indices[-1], path_indices[0]])
        return gain
    
    def _deduplicate_loops(self) -> None:
        """去除重复检测的环"""
        unique = {}
        for loop in self.detected_loops:
            # 标准化表示: 从最小元素开始
            nodes = loop.nodes
            if not nodes:
                continue
            min_idx = min(range(len(nodes)), key=lambda i: nodes[i])
            canonical = tuple(nodes[min_idx:] + nodes[:min_idx])
            # 同时考虑反向
            rev = tuple(reversed(canonical))
            key = min(canonical, rev)
            if key not in unique:
                unique[key] = loop
        
        self.detected_loops = list(unique.values())
    
    def detect_loops_involving(self, node: str) -> List[FeedbackLoop]:
        """检测包含指定节点的所有环"""
        loop_ids = self.node_loops.get(node, [])
        return [self.loop_index[lid] for lid in loop_ids if lid in self.loop_index]
    
    def get_beneficial_loops(self) -> List[FeedbackLoop]:
        """获取所有有益环"""
        return [l for l in self.detected_loops
                if l.loop_type == FeedbackLoopType.BENEFICIAL]
    
    def get_harmful_loops(self) -> List[FeedbackLoop]:
        """获取所有有害环"""
        return [l for l in self.detected_loops
                if l.loop_type == FeedbackLoopType.HARMFUL]
    
    def compute_loop_statistics(self) -> Dict[str, Any]:
        """计算环统计信息"""
        if not self.detected_loops:
            return {"count": 0, "types": {}, "avg_gain": 0.0}
        
        types = defaultdict(int)
        gains = []
        for loop in self.detected_loops:
            types[loop.loop_type.value] += 1
            gains.append(loop.gain)
        
        return {
            "count": len(self.detected_loops),
            "types": dict(types),
            "avg_gain": sum(gains) / len(gains),
            "max_gain": max(gains),
            "min_gain": min(gains),
            "stable_ratio": sum(1 for g in gains if abs(g) < 1.0) / len(gains),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_loops": [l.to_dict() for l in self.detected_loops],
            "statistics": self.compute_loop_statistics(),
            "max_cycle_length": self.max_cycle_length,
        }




# =============================================================================
# 5. SURGE RIPPLE ENGINE (MAIN CLASS)
# =============================================================================

class SurgeRippleEngine:
    """
    OMNI-HUB v12.0 — 正反向浪涌引擎 (主类)
    
    核心功能:
      1. forward_surge: 正向浪涌传播
      2. reverse_ripple: 反向涟漪传播
      3. detect_feedback_loops: 反馈环检测
      4. self_excite: 自激增强
      5. mutual_excite: 互激增强
      6. propagate_field_update: 全场更新传播
      7. run_coupled_cycle: 耦合循环（正反向交替）
      8. measure_field_coherence: 场一致性测量
    
    数学模型:
      - 正向传播: E_out = E_in × coupling(i,j) × exp(-decay × distance)
      - 反向调整: Δθ = -lr × ∇L × confidence
      - 场一致性: C = 1 - σ²/μ²
      - 自激增益: G_loop = ∏ coupling(e)
      - 互激耦合: C_ab = √(coupling(a,b) × coupling(b,a))
    """
    
    def __init__(self,
                 field_state: Optional[UnifiedFieldState] = None,
                 coupling_matrix: Optional[CouplingMatrix] = None,
                 learning_rate: float = 0.01,
                 max_depth: int = 10,
                 decay_rate: float = FIELD_DECAY_RATE) -> None:
        """
        初始化浪涌引擎。
        
        Args:
            field_state: 初始统一场状态（64维）
            coupling_matrix: 初始耦合矩阵
            learning_rate: 反向传播学习率
            max_depth: 最大传播深度
            decay_rate: 能量衰减率
        """
        # 场状态
        self.field_state: UnifiedFieldState = field_state or create_v12_unified_field()
        self.initial_field: UnifiedFieldState = self.field_state.copy()
        
        # 耦合矩阵
        self.coupling: CouplingMatrix = coupling_matrix or CouplingMatrix()
        
        # 超参数
        self.learning_rate: float = learning_rate
        self.max_depth: int = max_depth
        self.decay_rate: float = decay_rate
        
        # 反馈环检测器
        self.loop_detector: FeedbackLoopDetector = FeedbackLoopDetector(self.coupling)
        
        # 脉冲历史
        self.pulse_history: List[SurgePulse] = []
        self.wave_history: List[RippleWave] = []
        self.cycle_results: List[CoupledCycleResult] = []
        
        # 激活记录
        self.node_activation: Dict[str, float] = defaultdict(float)
        self.line_activation: Dict[str, float] = defaultdict(float)
        
        # 统计信息
        self.stats: Dict[str, Any] = {
            "forward_surges": 0,
            "reverse_ripples": 0,
            "loops_detected": 0,
            "self_excitations": 0,
            "mutual_excitations": 0,
            "coupled_cycles": 0,
            "total_energy_transferred": 0.0,
        }
        
        # 性能监控
        self.performance_log: List[Dict[str, Any]] = []
        self.logger = get_logger("SurgeRippleEngine")
        
        # 确保初始场有效
        self._initialize_field()
        self.logger.info("SurgeRippleEngine initialized (v12.0.0)")
    
    def _initialize_field(self) -> None:
        """初始化场状态默认值"""
        try:
            validate_field_state(self.field_state)
        except OMNIHUBDimensionError:
            self.field_state = create_v12_unified_field()
        
        # 设置默认能量
        if self.field_state.get(DimensionIndex.DIM_ENERGY) < 1.0:
            self.field_state.set(DimensionIndex.DIM_ENERGY, 6654.47)
        if self.field_state.get(DimensionIndex.DIM_ENTROPY) < 0.1:
            self.field_state.set(DimensionIndex.DIM_ENTROPY, 1.0)
        if self.field_state.get(DimensionIndex.DIM_COHERENCE) < 0.1:
            self.field_state.set(DimensionIndex.DIM_COHERENCE, 0.618)
    
    # -----------------------------------------------------------------------
    # 5.1 Forward Surge (正向浪涌)
    # -----------------------------------------------------------------------
    
    def forward_surge(self, pulse: SurgePulse,
                      target_nodes: Optional[List[str]] = None,
                      stop_on_convergence: bool = False) -> SurgeResult:
        """
        正向浪涌传播 —— 从问题/需求出发，沿着概念→关系→结构方向传播。
        
        算法:
          1. 从脉冲起点开始BFS/DFS混合传播
          2. 每步能量按 E_out = E_in × coupling × exp(-decay × distance) 衰减
          3. 记录传播路径和节点激活
          4. 更新场状态（能量注入）
        
        Args:
            pulse: 初始浪涌脉冲
            target_nodes: 目标节点列表（可选）
            stop_on_convergence: 是否在收敛时停止
        
        Returns:
            SurgeResult: 传播结果
        """
        self.logger.info(f"Forward surge from {pulse.origin}, energy={pulse.energy:.4f}")
        
        visited: Set[str] = set()
        queue: deque = deque([(pulse.current_node(), pulse.energy, 0)])
        visited.add(pulse.current_node())
        
        node_energies: Dict[str, float] = {pulse.current_node(): pulse.energy}
        path_lengths: Dict[str, int] = {pulse.current_node(): 0}
        propagation_log: List[Dict[str, Any]] = []
        
        current_pulse = pulse
        total_dissipated = 0.0
        
        while queue and current_pulse.depth < self.max_depth:
            current_node, current_energy, current_depth = queue.popleft()
            
            if current_energy < 0.01:
                total_dissipated += current_energy
                continue
            
            # 获取邻居节点
            neighbors = self.coupling.get_neighbors(current_node, threshold=0.05)
            
            for neighbor, coupling_strength in neighbors:
                # BFS: 跳过已访问节点，防止循环
                if neighbor in visited:
                    if stop_on_convergence:
                        return SurgeResult(
                            pulse=current_pulse,
                            visited_nodes=list(visited),
                            final_energy=sum(node_energies.values()),
                            energy_dissipated=total_dissipated,
                            path_lengths=path_lengths,
                            node_energies=node_energies,
                            propagation_log=propagation_log,
                        )
                    continue
                
                # 能量传播公式: E_out = E_in × coupling × exp(-decay × distance)
                distance = self.coupling.get_distance(current_node, neighbor)
                energy_out = current_energy * coupling_strength * math.exp(
                    -self.decay_rate * distance * (current_depth + 1)
                )
                
                if energy_out < 0.001:
                    total_dissipated += energy_out
                    continue
                
                # 记录
                log_entry = {
                    "from": current_node,
                    "to": neighbor,
                    "energy_in": current_energy,
                    "energy_out": energy_out,
                    "coupling": coupling_strength,
                    "distance": distance,
                    "depth": current_depth + 1,
                }
                propagation_log.append(log_entry)
                
                # 更新节点能量
                node_energies[neighbor] = node_energies.get(neighbor, 0.0) + energy_out
                path_lengths[neighbor] = current_depth + 1
                
                # 激活记录
                self.node_activation[neighbor] += energy_out
                if neighbor in LINE_NAMES:
                    self.line_activation[neighbor] += energy_out
                
                # 继续传播
                queue.append((neighbor, energy_out, current_depth + 1))
                visited.add(neighbor)
                
                # 更新脉冲路径（仅记录首次发现的节点）
                if neighbor not in current_pulse.path:
                    current_pulse.path.append(neighbor)
                    current_pulse.coupling_trace.append(coupling_strength)
            
            current_pulse.depth = max(current_pulse.depth, current_depth + 1)
        
        # 更新场状态 —— 将传播能量注入各维度
        self._inject_surge_energy(node_energies, pulse.payload)
        
        # 结果
        final_energy = sum(node_energies.values())
        result = SurgeResult(
            pulse=current_pulse,
            visited_nodes=list(visited),
            final_energy=final_energy,
            energy_dissipated=total_dissipated,
            path_lengths=path_lengths,
            node_energies=node_energies,
            propagation_log=propagation_log,
        )
        
        self.pulse_history.append(current_pulse)
        self.stats["forward_surges"] += 1
        self.stats["total_energy_transferred"] += final_energy
        
        self.logger.info(f"Forward surge complete: visited={len(visited)}, "
                        f"final_energy={final_energy:.4f}")
        return result
    
    def _inject_surge_energy(self, node_energies: Dict[str, float],
                             payload: Dict[str, Any]) -> None:
        """将浪涌能量注入统一场"""
        total_energy = sum(node_energies.values())
        if total_energy < 1e-10:
            return
        
        # 能量注入各维度
        current_energy = self.field_state.get(DimensionIndex.DIM_ENERGY)
        self.field_state.set(DimensionIndex.DIM_ENERGY,
                             current_energy + total_energy * 0.1)
        
        # 根据payload类型注入特定维度
        ptype = payload.get("type", "")
        if ptype == "question":
            # 问题类型 → 增强信息、知识、注意力维度
            self.field_state.set(DimensionIndex.DIM_INFORMATION,
                self.field_state.get(DimensionIndex.DIM_INFORMATION) + total_energy * 0.05)
            self.field_state.set(DimensionIndex.DIM_KNOWLEDGE,
                self.field_state.get(DimensionIndex.DIM_KNOWLEDGE) + total_energy * 0.03)
            self.field_state.set(DimensionIndex.DIM_ATTENTION,
                self.field_state.get(DimensionIndex.DIM_ATTENTION) + total_energy * 0.02)
        elif ptype == "action":
            # 行动类型 → 增强意图、流动维度
            self.field_state.set(DimensionIndex.DIM_INTENTION,
                self.field_state.get(DimensionIndex.DIM_INTENTION) + total_energy * 0.05)
            self.field_state.set(DimensionIndex.DIM_FLOW,
                self.field_state.get(DimensionIndex.DIM_FLOW) + total_energy * 0.03)
        
        # 协同维度增强
        self.field_state.set(DimensionIndex.DIM_SYNERGY,
            self.field_state.get(DimensionIndex.DIM_SYNERGY) + total_energy * 0.01)
        
        # 更新时间戳
        self.field_state.timestamp = time.time()
    
    # -----------------------------------------------------------------------
    # 5.2 Reverse Ripple (反向涟漪)
    # -----------------------------------------------------------------------
    
    def reverse_ripple(self, wave: RippleWave,
                       propagate_depth: int = 3) -> RippleResult:
        """
        反向涟漪传播 —— 从结果出发，反向传播调整信号。
        
        算法:
          1. 从结果节点出发，沿耦合矩阵反向传播
          2. 每步调整按 Δθ = -lr × ∇L × confidence 计算
          3. 传播到前驱节点，衰减 confidence
          4. 更新场状态（反向调整）
        
        Args:
            wave: 初始涟漪波
            propagate_depth: 反向传播深度
        
        Returns:
            RippleResult: 反向传播结果
        """
        self.logger.info(f"Reverse ripple from {wave.origin} to {wave.target}, "
                        f"confidence={wave.confidence:.4f}")
        
        adjusted_nodes: List[str] = [wave.target]
        confidence_map: Dict[str, float] = {wave.target: wave.confidence}
        propagation_log: List[Dict[str, Any]] = []
        
        # 初始调整
        total_adj = np.zeros(67)
        target_idx = self.coupling.node_index.get(wave.target, -1)
        
        if target_idx >= 0:
            # 应用调整向量到目标节点
            adj = wave.apply_learning_rate(self.learning_rate)
            total_adj += adj.adjustment
            
            log_entry = {
                "node": wave.target,
                "adjustment_norm": float(norm(adj.adjustment)),
                "confidence": wave.confidence,
                "depth": 0,
            }
            propagation_log.append(log_entry)
        
        # 反向传播到前驱节点
        current_nodes = {wave.target: wave.confidence}
        
        for depth in range(1, propagate_depth + 1):
            next_nodes: Dict[str, float] = {}
            
            for node, conf in current_nodes.items():
                # 查找前驱（反向耦合 > 阈值）
                node_idx = self.coupling.node_index.get(node, -1)
                if node_idx < 0:
                    continue
                
                for pred_idx, pred_name in enumerate(self.coupling.nodes):
                    if pred_idx == node_idx:
                        continue
                    
                    # 反向耦合强度
                    rev_coupling = self.coupling.matrix[node_idx, pred_idx]
                    if rev_coupling < 0.05:
                        continue
                    
                    # 衰减后的置信度
                    new_conf = conf * rev_coupling * math.exp(-self.decay_rate * depth)
                    if new_conf < 0.01:
                        continue
                    
                    # 计算前驱调整
                    pred_adj = wave.adjustment * rev_coupling * new_conf * self.learning_rate
                    total_adj += pred_adj
                    
                    if pred_name not in adjusted_nodes:
                        adjusted_nodes.append(pred_name)
                    
                    confidence_map[pred_name] = max(
                        confidence_map.get(pred_name, 0.0), new_conf
                    )
                    next_nodes[pred_name] = new_conf
                    
                    propagation_log.append({
                        "from": node,
                        "to": pred_name,
                        "reverse_coupling": float(rev_coupling),
                        "confidence": new_conf,
                        "depth": depth,
                        "adjustment_norm": float(norm(pred_adj)),
                    })
            
            current_nodes = next_nodes
            if not current_nodes:
                break
        
        # 应用全场调整
        self._apply_field_adjustment(total_adj)
        
        result = RippleResult(
            wave=wave,
            adjusted_nodes=adjusted_nodes,
            total_adjustment_magnitude=float(norm(total_adj)),
            field_delta=total_adj,
            confidence_map=confidence_map,
            propagation_log=propagation_log,
        )
        
        self.wave_history.append(wave)
        self.stats["reverse_ripples"] += 1
        
        self.logger.info(f"Reverse ripple complete: adjusted={len(adjusted_nodes)}, "
                        f"total_adj_norm={norm(total_adj):.4f}")
        return result
    
    def _apply_field_adjustment(self, adjustment: np.ndarray) -> None:
        """应用反向调整向量到统一场"""
        if len(adjustment) != 67:
            adj = np.zeros(67)
            n = min(len(adjustment), 67)
            adj[:n] = adjustment[:n]
            adjustment = adj
        
        # 前64维映射到场向量
        for i in range(min(64, len(adjustment))):
            dim = list(DimensionIndex)[i] if i < len(list(DimensionIndex)) else None
            if dim:
                current = self.field_state.get(dim)
                self.field_state.set(dim, current + adjustment[i])
        
        # 后3维为扩展维度（逻辑值）
        if len(adjustment) > 64:
            # 可以编码到DIM_UNIFICATION子空间
            pass
        
        # 确保能量非负
        energy = self.field_state.get(DimensionIndex.DIM_ENERGY)
        if energy < 0:
            self.field_state.set(DimensionIndex.DIM_ENERGY, 0.0)
        
        self.field_state.timestamp = time.time()
    
    # -----------------------------------------------------------------------
    # 5.3 Feedback Loop Detection
    # -----------------------------------------------------------------------
    
    def detect_feedback_loops(self, recompute: bool = False) -> List[FeedbackLoop]:
        """
        检测系统中的所有反馈环。
        
        Args:
            recompute: 是否重新计算（否则使用缓存）
        
        Returns:
            List[FeedbackLoop]: 检测到的反馈环列表
        """
        if not recompute and self.loop_detector.detected_loops:
            return self.loop_detector.detected_loops
        
        loops = self.loop_detector.detect_all_loops(threshold_gain=0.01)
        self.stats["loops_detected"] = len(loops)
        
        self.logger.info(f"Detected {len(loops)} feedback loops")
        return loops
    
    # -----------------------------------------------------------------------
    # 5.4 Self-Excitation (自激)
    # -----------------------------------------------------------------------
    
    def self_excite(self, loop: FeedbackLoop, gain: Optional[float] = None) -> float:
        """
        自激增强 —— 检测并增强有益的正反馈环。
        
        算法:
          1. 如果环是有益的且稳定的，增强其耦合
          2. 如果环是有害的，抑制其耦合
          3. 增益应用: coupling_new = coupling_old × (1 + gain_factor)
        
        Args:
            loop: 目标反馈环
            gain: 增强增益（默认自动计算）
        
        Returns:
            float: 应用的总增强量
        """
        if gain is None:
            # 自动计算增益
            if loop.loop_type == FeedbackLoopType.BENEFICIAL:
                gain = 0.1 * loop.stability  # 稳定的有益环 → 适度增强
            elif loop.loop_type == FeedbackLoopType.HARMFUL:
                gain = -0.2  # 有害环 → 抑制
            else:
                gain = 0.05  # 中性环 → 轻微增强
        
        total_enhancement = 0.0
        nodes = loop.nodes
        
        for i in range(len(nodes)):
            from_node = nodes[i]
            to_node = nodes[(i + 1) % len(nodes)]
            
            current_coupling = self.coupling.get_coupling(from_node, to_node)
            new_coupling = np.clip(current_coupling * (1.0 + gain), 0.0, 1.0)
            
            self.coupling.set_coupling(from_node, to_node, new_coupling,
                                       symmetric=False)
            total_enhancement += abs(new_coupling - current_coupling)
        
        # 更新能量流估计
        loop.energy_flow = loop.gain * (1.0 + gain)
        
        self.stats["self_excitations"] += 1
        self.logger.info(f"Self-excitation applied to loop {loop.loop_id}: "
                        f"type={loop.loop_type.value}, gain={gain:.4f}, "
                        f"enhancement={total_enhancement:.4f}")
        
        return total_enhancement
    
    def auto_excite_all(self, beneficial_gain: float = 0.1,
                        harmful_damping: float = -0.3) -> Dict[str, float]:
        """
        自动处理所有检测到的反馈环。
        
        Args:
            beneficial_gain: 有益环增强系数
            harmful_damping: 有害环抑制系数
        
        Returns:
            Dict: 各环的处理结果
        """
        loops = self.detect_feedback_loops(recompute=True)
        results = {}
        
        for loop in loops:
            if loop.loop_type == FeedbackLoopType.BENEFICIAL:
                enhancement = self.self_excite(loop, gain=beneficial_gain)
                results[loop.loop_id] = enhancement
            elif loop.loop_type == FeedbackLoopType.HARMFUL:
                damping = self.self_excite(loop, gain=harmful_damping)
                results[loop.loop_id] = damping
            else:
                results[loop.loop_id] = 0.0
        
        return results
    
    # -----------------------------------------------------------------------
    # 5.5 Mutual-Excitation (互激)
    # -----------------------------------------------------------------------
    
    def mutual_excite(self, line_a: str, line_b: str,
                      coupling_boost: float = 0.2) -> float:
        """
        互激增强 —— 增强两条线之间的耦合，产生协同效应。
        
        数学: C'_ab = √(C_ab × C_ba) × (1 + boost)
              协同指数 = C'_ab² / (C_aa × C_bb)
        
        Args:
            line_a: 第一条线名称
            line_b: 第二条线名称
            coupling_boost: 耦合增强系数
        
        Returns:
            float: 新的耦合强度
        """
        if line_a not in self.coupling.node_index:
            self.coupling.add_node(line_a)
        if line_b not in self.coupling.node_index:
            self.coupling.add_node(line_b)
        
        c_ab = self.coupling.get_coupling(line_a, line_b)
        c_ba = self.coupling.get_coupling(line_b, line_a)
        
        # 几何平均耦合
        geometric_mean = math.sqrt(c_ab * c_ba) if c_ab * c_ba > 0 else max(c_ab, c_ba)
        
        # 增强
        new_coupling = min(1.0, geometric_mean * (1.0 + coupling_boost))
        
        self.coupling.set_coupling(line_a, line_b, new_coupling, symmetric=True)
        
        # 更新场状态 —— 互激增强共振和协同维度
        current_resonance = self.field_state.get(DimensionIndex.DIM_RESONANCE)
        current_synergy = self.field_state.get(DimensionIndex.DIM_SYNERGY)
        
        self.field_state.set(DimensionIndex.DIM_RESONANCE,
                             current_resonance + new_coupling * 0.1)
        self.field_state.set(DimensionIndex.DIM_SYNERGY,
                             current_synergy + new_coupling * 0.15)
        
        self.stats["mutual_excitations"] += 1
        self.logger.info(f"Mutual excitation: {line_a} ↔ {line_b}, "
                        f"new_coupling={new_coupling:.4f}")
        
        return new_coupling
    
    def find_best_mutual_pairs(self, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """
        查找最佳互激对 —— 基于当前耦合和激活模式。
        
        Returns:
            List[Tuple]: (线A, 线B, 协同潜力)
        """
        pairs = []
        n = len(LINE_NAMES)
        
        for i in range(n):
            for j in range(i + 1, n):
                a = LINE_NAMES[i]
                b = LINE_NAMES[j]
                
                c_ab = self.coupling.get_coupling(a, b)
                c_ba = self.coupling.get_coupling(b, a)
                
                # 协同潜力 = 几何平均 × 激活乘积 × (1 - 当前耦合)
                geo_mean = math.sqrt(c_ab * c_ba) if c_ab * c_ba > 0 else 0.0
                activation_product = (self.line_activation.get(a, 0.0) +
                                      0.1) * (self.line_activation.get(b, 0.0) + 0.1)
                potential = geo_mean * activation_product * (1.1 - max(c_ab, c_ba))
                
                pairs.append((a, b, potential))
        
        pairs.sort(key=lambda x: -x[2])
        return pairs[:top_k]
    
    # -----------------------------------------------------------------------
    # 5.6 Field Update Propagation
    # -----------------------------------------------------------------------
    
    def propagate_field_update(self, update_vector: Optional[np.ndarray] = None,
                               scope: str = "global") -> Dict[str, float]:
        """
        全场更新传播 —— 将场更新传播到所有活跃节点。
        
        Args:
            update_vector: 更新向量（67维）
            scope: 传播范围 (global/line/local)
        
        Returns:
            Dict: 各节点接收到的更新强度
        """
        if update_vector is None:
            # 基于场状态变化自动生成更新向量
            update_vector = self._compute_field_gradient()
        
        if len(update_vector) != 67:
            uv = np.zeros(67)
            n = min(len(update_vector), 67)
            uv[:n] = update_vector[:n]
            update_vector = uv
        
        node_updates: Dict[str, float] = {}
        
        # 基于耦合矩阵传播更新
        for node in self.coupling.nodes:
            node_idx = self.coupling.node_index.get(node, -1)
            if node_idx < 0:
                continue
            
            # 节点接收的更新强度 = 与所有其他节点的耦合加权和
            received = 0.0
            for other in self.coupling.nodes:
                if other == node:
                    continue
                c = self.coupling.get_coupling(other, node)
                received += c * norm(update_vector)
            
            node_updates[node] = received
            
            # 如果是线，更新线激活
            if node in LINE_NAMES:
                self.line_activation[node] += received * 0.1
        
        # 应用到场状态
        total_update = sum(node_updates.values())
        if total_update > 0:
            current_coherence = self.field_state.get(DimensionIndex.DIM_COHERENCE)
            self.field_state.set(DimensionIndex.DIM_COHERENCE,
                                 current_coherence + total_update * 0.01)
        
        self.logger.info(f"Field update propagated: scope={scope}, "
                        f"nodes={len(node_updates)}, total_update={total_update:.4f}")
        return node_updates
    
    def _compute_field_gradient(self) -> np.ndarray:
        """计算场状态梯度（用于反向传播）"""
        gradient = np.zeros(67)
        
        # 能量梯度
        energy = self.field_state.get(DimensionIndex.DIM_ENERGY)
        target_energy = EMERGENCE_THRESHOLD_V12  # 目标能量
        gradient[0] = (target_energy - energy) / max(target_energy, 1.0)
        
        # 熵梯度（希望降低熵）
        entropy = self.field_state.get(DimensionIndex.DIM_ENTROPY)
        gradient[2] = -entropy / 10.0  # 负梯度 = 降低熵
        
        # 相干性梯度
        coherence = self.field_state.get(DimensionIndex.DIM_COHERENCE)
        gradient[1] = (1.0 - coherence) * 0.5
        
        # 涌现维度梯度
        emergence = self.field_state.get(DimensionIndex.DIM_EMERGENCE)
        gradient[48] = (1.0 - emergence) * 0.3
        
        # 协同维度梯度
        synergy = self.field_state.get(DimensionIndex.DIM_SYNERGY)
        gradient[52] = (1.0 - synergy) * 0.3
        
        return gradient
    
    # -----------------------------------------------------------------------
    # 5.7 Question → Surge (从问题发起浪涌)
    # -----------------------------------------------------------------------
    
    def surge_from_question(self, question: Union[str, WildQuestion],
                            origin: str = "wild_notebook") -> SurgeResult:
        """
        从问题发起正向浪涌。
        
        Args:
            question: 问题内容或WildQuestion对象
            origin: 发起源
        
        Returns:
            SurgeResult: 浪涌结果
        """
        if isinstance(question, str):
            q = WildQuestion(content=question, origin_line=origin)
        else:
            q = question
            origin = q.origin_line
        
        pulse = SurgePulse.from_question(q, origin=origin)
        return self.forward_surge(pulse)
    
    # -----------------------------------------------------------------------
    # 5.8 Result → Ripple (从结果发起涟漪)
    # -----------------------------------------------------------------------
    
    def ripple_from_result(self, result_node: str,
                           loss: float = 1.0,
                           target: Optional[str] = None) -> RippleResult:
        """
        从结果节点发起反向涟漪。
        
        Args:
            result_node: 结果节点名称
            loss: 损失值（决定调整方向）
            target: 调整目标节点（默认结果节点自身）
        
        Returns:
            RippleResult: 涟漪结果
        """
        target = target or result_node
        
        # 计算损失梯度
        gradient = self._compute_field_gradient()
        
        # 基于损失缩放
        adjustment = -gradient * loss  # 负梯度方向
        
        # 计算置信度（基于场一致性）
        coherence = self.field_state.compute_coherence()
        confidence = min(1.0, coherence + 0.3)
        
        wave = RippleWave(
            origin=result_node,
            target=target,
            adjustment=adjustment,
            confidence=confidence,
            loss_gradient=loss,
            metadata={"trigger": "result_feedback", "loss": loss},
        )
        
        return self.reverse_ripple(wave)
    
    # -----------------------------------------------------------------------
    # 5.9 Coupled Cycle (耦合循环 —— 正反向交替)
    # -----------------------------------------------------------------------
    
    def run_coupled_cycle(self,
                          questions: Optional[List[Union[str, WildQuestion]]] = None,
                          max_cycles: int = 3,
                          convergence_threshold: float = 0.01) -> CoupledCycleResult:
        """
        运行耦合循环 —— 正向浪涌和反向涟漪交替执行。
        
        算法:
          1. FORWARD: 从问题发起浪涌
          2. REVERSE: 基于浪涌结果发起涟漪
          3. 检测反馈环并处理
          4. 重复直到收敛或达到最大循环数
        
        Args:
            questions: 问题列表
            max_cycles: 最大循环次数
            convergence_threshold: 收敛阈值
        
        Returns:
            CoupledCycleResult: 耦合循环结果
        """
        cycle_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Starting coupled cycle {cycle_id}, max_cycles={max_cycles}")
        
        forward_results: List[SurgeResult] = []
        reverse_results: List[RippleResult] = []
        detected_loops: List[FeedbackLoop] = []
        excitation_applied: Dict[str, float] = {}
        
        coherence_before = self.measure_field_coherence()
        
        # 默认问题
        if questions is None:
            questions = ["How to enhance system coherence?"]
        
        for cycle in range(max_cycles):
            self.logger.info(f"Cycle {cycle + 1}/{max_cycles}")
            
            # === FORWARD PHASE ===
            for q in questions:
                surge_result = self.surge_from_question(q)
                forward_results.append(surge_result)
            
            # === REVERSE PHASE ===
            # 基于浪涌结果计算损失
            loss = self._compute_cycle_loss(forward_results[-1] if forward_results else None)
            
            # 找到能量最高的节点作为反馈源
            if forward_results:
                node_energies = forward_results[-1].node_energies
                if node_energies:
                    result_node = max(node_energies, key=node_energies.get)
                    ripple_result = self.ripple_from_result(result_node, loss=loss)
                    reverse_results.append(ripple_result)
            
            # === FEEDBACK LOOP DETECTION & EXCITATION ===
            loops = self.detect_feedback_loops(recompute=True)
            detected_loops.extend(loops)
            
            for loop in loops:
                enhancement = self.self_excite(loop)
                excitation_applied[loop.loop_id] = enhancement
            
            # === CONVERGENCE CHECK ===
            current_coherence = self.measure_field_coherence()
            delta = abs(current_coherence - coherence_before)
            
            if delta < convergence_threshold and cycle > 0:
                self.logger.info(f"Convergence achieved at cycle {cycle + 1}")
                break
            
            coherence_before = current_coherence
        
        # 最终一致性
        coherence_after = self.measure_field_coherence()
        
        result = CoupledCycleResult(
            cycle_id=cycle_id,
            forward_results=forward_results,
            reverse_results=reverse_results,
            final_field_state=self.field_state.copy(),
            coherence_before=coherence_before,
            coherence_after=coherence_after,
            detected_loops=list({l.loop_id: l for l in detected_loops}.values()),
            excitation_applied=excitation_applied,
            cycle_count=len(forward_results),
            convergence_achieved=(abs(coherence_after - coherence_before) < convergence_threshold),
        )
        
        self.cycle_results.append(result)
        self.stats["coupled_cycles"] += 1
        
        self.logger.info(f"Coupled cycle {cycle_id} complete: "
                        f"coherence {result.coherence_before:.4f} → {result.coherence_after:.4f}")
        return result
    
    def _compute_cycle_loss(self, last_surge: Optional[SurgeResult]) -> float:
        """计算循环损失（基于浪涌结果和场状态）"""
        if last_surge is None:
            return 1.0
        
        # 能量损失: 希望能量更接近目标
        energy = self.field_state.get(DimensionIndex.DIM_ENERGY)
        target = EMERGENCE_THRESHOLD_V12
        energy_loss = abs(target - energy) / target
        
        # 相干损失: 希望相干性更高
        coherence = self.field_state.compute_coherence()
        coherence_loss = 1.0 - coherence
        
        # 传播损失: 希望更多节点被激活
        if last_surge.visited_nodes:
            coverage = len(last_surge.visited_nodes) / len(self.coupling.nodes)
            coverage_loss = 1.0 - coverage
        else:
            coverage_loss = 1.0
        
        # 综合损失
        loss = (energy_loss + coherence_loss + coverage_loss) / 3.0
        return float(np.clip(loss, 0.0, 1.0))
    
    # -----------------------------------------------------------------------
    # 5.10 Field Coherence Measurement
    # -----------------------------------------------------------------------
    
    def measure_field_coherence(self) -> float:
        """
        测量场一致性。
        
        数学: C = 1 - σ²/μ² = 1 - CV²
              其中 CV = σ/μ 为变异系数
        
        Returns:
            float: 场一致性 [0, 1]
        """
        vector = np.array(self.field_state.vector, dtype=float)
        
        if len(vector) == 0:
            return 0.0
        
        mean = np.mean(vector)
        std = np.std(vector)
        
        if abs(mean) < 1e-10:
            return 0.0
        
        cv = std / abs(mean)  # 变异系数
        coherence = 1.0 / (1.0 + cv * cv)  # C = 1 / (1 + CV²)
        
        # 同时更新场状态中的一致性维度
        self.field_state.set(DimensionIndex.DIM_COHERENCE_EM, coherence)
        
        return float(np.clip(coherence, 0.0, 1.0))
    
    def measure_field_diversity(self) -> float:
        """测量场多样性（Shannon熵）"""
        vector = np.array(self.field_state.vector, dtype=float)
        # 归一化
        total = np.sum(np.abs(vector))
        if total < 1e-10:
            return 0.0
        
        probs = np.abs(vector) / total
        probs = probs[probs > 1e-10]  # 避免log(0)
        
        entropy = -np.sum(probs * np.log(probs))
        max_entropy = np.log(len(probs)) if len(probs) > 0 else 1.0
        
        return float(entropy / max_entropy) if max_entropy > 0 else 0.0
    
    def measure_emergence_potential(self) -> float:
        """测量涌现潜力"""
        coherence = self.measure_field_coherence()
        diversity = self.measure_field_diversity()
        energy = self.field_state.get(DimensionIndex.DIM_ENERGY)
        
        # 涌现潜力 = 相干 × 多样 × log(能量)
        if energy > 1.0:
            potential = coherence * diversity * math.log(energy)
        else:
            potential = coherence * diversity * 0.1
        
        return float(np.clip(potential, 0.0, 1.0))
    
    # -----------------------------------------------------------------------
    # 5.11 Integration with v12 Standards
    # -----------------------------------------------------------------------
    
    def tick(self, ctx: TickContext) -> UnifiedFieldState:
        """
        标准Tick接口 —— 兼容ModuleProtocol。
        
        执行一个完整的浪涌-涟漪周期。
        """
        # 基于Tick上下文生成问题
        questions = []
        if ctx.metadata and "questions" in ctx.metadata:
            questions = ctx.metadata["questions"]
        
        if not questions:
            questions = [f"Tick {ctx.tick_id} auto-question"]
        
        # 运行耦合循环
        result = self.run_coupled_cycle(
            questions=questions,
            max_cycles=1,
        )
        
        return self.field_state
    
    def adapt(self, ctx: AdaptContext) -> None:
        """
        标准Adapt接口 —— 兼容ModuleProtocol。
        
        基于反馈调整耦合矩阵。
        """
        feedback = ctx.feedback
        lr = ctx.learning_rate
        
        # 基于反馈场调整耦合
        feedback_vector = np.array(feedback.vector, dtype=float)
        current_vector = np.array(self.field_state.vector, dtype=float)
        
        # 差异向量
        delta = feedback_vector - current_vector
        
        # 调整耦合矩阵（Hebbian-like learning）
        for i, node_a in enumerate(self.coupling.nodes):
            for j, node_b in enumerate(self.coupling.nodes):
                if i == j:
                    continue
                # 耦合增强与两节点状态差异负相关
                coupling_delta = lr * (1.0 - abs(delta[i] - delta[j]) / max(abs(delta[i]) + abs(delta[j]), 1e-10))
                current = self.coupling.matrix[i, j]
                self.coupling.matrix[i, j] = np.clip(current + coupling_delta, 0.0, 1.0)
        
        self.coupling._compute_distance_matrix()
        self.logger.info(f"Adaptation applied: lr={lr}, feedback_norm={norm(delta):.4f}")
    
    def emit(self, ctx: EmitContext) -> Dict[str, Any]:
        """
        标准Emit接口 —— 兼容ModuleProtocol。
        
        发射当前场状态摘要。
        """
        coherence = self.measure_field_coherence()
        emergence_potential = self.measure_emergence_potential()
        
        emission = {
            "type": ctx.signal_type,
            "priority": ctx.priority,
            "scope": ctx.emission_scope,
            "field_coherence": coherence,
            "emergence_potential": emergence_potential,
            "energy": self.field_state.get(DimensionIndex.DIM_ENERGY),
            "timestamp": time.time(),
            "stats": self.stats.copy(),
            "active_lines": dict(self.line_activation),
        }
        
        if ctx.target_modules:
            emission["target_modules"] = ctx.target_modules
        
        return emission
    
    def status(self) -> Dict[str, Any]:
        """返回引擎状态摘要"""
        return {
            "version": __version__,
            "field_coherence": self.measure_field_coherence(),
            "field_energy": self.field_state.get(DimensionIndex.DIM_ENERGY),
            "field_entropy": self.field_state.get(DimensionIndex.DIM_ENTROPY),
            "emergence_potential": self.measure_emergence_potential(),
            "stats": self.stats.copy(),
            "active_lines": dict(self.line_activation),
            "coupling_spectral_radius": self.coupling.compute_spectral_radius(),
            "coupling_algebraic_connectivity": self.coupling.compute_algebraic_connectivity(),
            "detected_loops": len(self.loop_detector.detected_loops),
            "pulse_history_size": len(self.pulse_history),
            "wave_history_size": len(self.wave_history),
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = self.status()
        healthy = (
            status["field_coherence"] > 0.1 and
            status["field_energy"] > 0 and
            status["coupling_spectral_radius"] < 5.0
        )
        return {
            "status": "healthy" if healthy else "degraded",
            "module": self.__class__.__name__,
            "details": status,
        }
    
    # -----------------------------------------------------------------------
    # 5.12 Utility Methods
    # -----------------------------------------------------------------------
    
    def reset_field(self, preserve_coupling: bool = True) -> None:
        """重置场状态"""
        self.field_state = create_v12_unified_field()
        self.node_activation.clear()
        self.line_activation.clear()
        self.pulse_history.clear()
        self.wave_history.clear()
        if not preserve_coupling:
            self.coupling = CouplingMatrix()
            self.loop_detector = FeedbackLoopDetector(self.coupling)
        self.logger.info("Field state reset")
    
    def export_state(self) -> Dict[str, Any]:
        """导出完整状态"""
        return {
            "version": __version__,
            "field_state": self.field_state.to_dict(),
            "coupling_matrix": self.coupling.to_dict(),
            "stats": self.stats,
            "loop_detector": self.loop_detector.to_dict(),
            "status": self.status(),
        }
    
    def import_state(self, data: Dict[str, Any]) -> None:
        """导入完整状态"""
        if "field_state" in data:
            self.field_state = UnifiedFieldState.from_dict(data["field_state"])
        if "coupling_matrix" in data and "nodes" in data["coupling_matrix"]:
            nodes = data["coupling_matrix"]["nodes"]
            self.coupling = CouplingMatrix(nodes=nodes)
            if "matrix" in data["coupling_matrix"]:
                self.coupling.matrix = np.array(data["coupling_matrix"]["matrix"])
            self.coupling._compute_distance_matrix()
            self.loop_detector = FeedbackLoopDetector(self.coupling)
        if "stats" in data:
            self.stats.update(data["stats"])
    
    def get_activation_heatmap(self) -> Dict[str, float]:
        """获取节点激活热力图"""
        return dict(self.node_activation)
    
    def get_line_energy_distribution(self) -> Dict[str, float]:
        """获取线能量分布"""
        return {line: self.line_activation.get(line, 0.0) for line in LINE_NAMES}


# =============================================================================
# 6. CONVENIENCE FUNCTIONS
# =============================================================================

def create_default_engine(field_energy: float = 6654.47,
                          learning_rate: float = 0.01) -> SurgeRippleEngine:
    """创建默认配置的浪涌引擎"""
    field = create_v12_unified_field()
    field.set(DimensionIndex.DIM_ENERGY, field_energy)
    field.set(DimensionIndex.DIM_ENTROPY, 1.0)
    field.set(DimensionIndex.DIM_COHERENCE, 0.618)
    
    coupling = CouplingMatrix()
    engine = SurgeRippleEngine(
        field_state=field,
        coupling_matrix=coupling,
        learning_rate=learning_rate,
    )
    return engine


def run_full_demonstration() -> Dict[str, Any]:
    """运行完整演示"""
    print("=" * 70)
    print("OMNI-HUB v12.0 — SurgeRippleEngine Demonstration")
    print("=" * 70)
    
    # 创建引擎
    engine = create_default_engine()
    print(f"\n[1] Engine created")
    print(f"    Initial energy: {engine.field_state.get(DimensionIndex.DIM_ENERGY):.2f}")
    print(f"    Initial coherence: {engine.measure_field_coherence():.4f}")
    
    # 正向浪涌
    print(f"\n[2] Forward Surge from question...")
    result_surge = engine.surge_from_question(
        "How to achieve UNITY consciousness state?",
        origin="wild_notebook"
    )
    print(f"    Visited nodes: {len(result_surge.visited_nodes)}")
    print(f"    Final energy: {result_surge.final_energy:.4f}")
    print(f"    Path length: {len(result_surge.pulse.path)}")
    
    # 反向涟漪
    print(f"\n[3] Reverse Ripple from result...")
    result_ripple = engine.ripple_from_result(
        result_node=result_surge.pulse.current_node(),
        loss=0.5,
    )
    print(f"    Adjusted nodes: {len(result_ripple.adjusted_nodes)}")
    print(f"    Total adjustment: {result_ripple.total_adjustment_magnitude:.4f}")
    
    # 检测反馈环
    print(f"\n[4] Detecting feedback loops...")
    loops = engine.detect_feedback_loops()
    print(f"    Detected loops: {len(loops)}")
    for loop in loops[:3]:
        print(f"    - Loop {loop.loop_id}: {loop.nodes[:4]}... "
              f"gain={loop.gain:.4f}, type={loop.loop_type.value}")
    
    # 自激
    print(f"\n[5] Applying self-excitation...")
    for loop in loops[:2]:
        enhancement = engine.self_excite(loop)
        print(f"    Loop {loop.loop_id}: enhancement={enhancement:.4f}")
    
    # 互激
    print(f"\n[6] Applying mutual-excitation...")
    for pair in engine.find_best_mutual_pairs(top_k=2):
        a, b, potential = pair
        new_c = engine.mutual_excite(a, b, coupling_boost=0.15)
        print(f"    {a} ↔ {b}: new_coupling={new_c:.4f}, potential={potential:.4f}")
    
    # 耦合循环
    print(f"\n[7] Running coupled cycle...")
    cycle_result = engine.run_coupled_cycle(
        questions=["Enhance coherence", "Reduce entropy"],
        max_cycles=2,
    )
    print(f"    Cycles run: {cycle_result.cycle_count}")
    print(f"    Coherence: {cycle_result.coherence_before:.4f} → {cycle_result.coherence_after:.4f}")
    print(f"    Convergence: {cycle_result.convergence_achieved}")
    
    # 最终状态
    print(f"\n[8] Final status...")
    status = engine.status()
    print(f"    Field coherence: {status['field_coherence']:.4f}")
    print(f"    Emergence potential: {status['emergence_potential']:.4f}")
    print(f"    Total energy: {status['field_energy']:.2f}")
    print(f"    Forward surges: {status['stats']['forward_surges']}")
    print(f"    Reverse ripples: {status['stats']['reverse_ripples']}")
    print(f"    Self-excitations: {status['stats']['self_excitations']}")
    print(f"    Mutual-excitations: {status['stats']['mutual_excitations']}")
    print(f"    Detected loops: {status['detected_loops']}")
    
    print(f"\n[9] Health check...")
    health = engine.health_check()
    print(f"    Status: {health['status']}")
    
    print("\n" + "=" * 70)
    print("Demonstration complete!")
    print("=" * 70)
    
    return {
        "engine": engine,
        "surge_result": result_surge,
        "ripple_result": result_ripple,
        "loops": loops,
        "cycle_result": cycle_result,
        "status": status,
    }


# =============================================================================
# 7. MAIN
# =============================================================================

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )
    
    # 运行演示
    demo_results = run_full_demonstration()
