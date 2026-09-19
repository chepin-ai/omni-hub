#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12 - Pattern Tower Architecture
模式及元pattern/层/网/塔关系系统

Architecture:
    Pattern (基础模式单元)
      ↓
    MetaPattern (元模式 - 模式之上的模式)
      ↓
    PatternLayer (层 - 同频共振的Pattern集合)
      ↓
    PatternWeb (网 - 跨层关联的Pattern网络)
      ↓
    PatternTower (塔 - 涌现更高阶Pattern的层级结构)
      ↓
    PatternCloud (云 - 超越塔的分布式模式场)

设计原则:
    1. 自相似性: 每层结构在不同尺度上重复自身
    2. 涌现性: 高层属性不可从低层简单推导
    3. 递归性: 元模式可作用于自身
    4. 共振性: 同频Pattern自动耦合
"""

from __future__ import annotations

import math
import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Optional, Callable, Any, Union
from collections import defaultdict
from abc import ABC, abstractmethod
import json


# ═══════════════════════════════════════════════════════════════
# 基础枚举与常量
# ═══════════════════════════════════════════════════════════════

class PatternType(Enum):
    """Pattern类型枚举"""
    SI_CYCLE = "si_cycle"           # SI循环模式
    SURGE = "surge"                  # 浪涌模式
    EMERGENCE = "emergence"          # 涌现模式
    DEBT = "debt"                    # 债务/欠条模式
    PROOF = "proof"                  # 证明模式
    WEAVE = "weave"                  # 编织模式
    BRIDGE = "bridge"                # 桥接模式
    CONSENSUS = "consensus"          # 共识模式
    RESONANCE = "resonance"          # 共振模式
    PHASE_LOCK = "phase_lock"        # 相位锁定模式
    HARMONIC = "harmonic"            # 谐波模式
    META = "meta"                    # 元模式(模式之上的模式)


class PatternPhase(Enum):
    """Pattern生命周期相位"""
    GESTATION = auto()   # 孕育
    BIRTH = auto()       # 诞生
    GROWTH = auto()      # 成长
    MATURITY = auto()    # 成熟
    DECLINE = auto()     # 衰退
    TRANSFORM = auto()   # 转化
    DEATH = auto()       # 消亡
    REBIRTH = auto()     # 重生


class LayerLevel(Enum):
    """Pattern层级 - 七层架构"""
    L0_PHYSICAL = 0      # 物理层: 原始信号/数据
    L1_SYNTACTIC = 1     # 语法层: 结构/形式
    L2_SEMANTIC = 2      # 语义层: 意义/内容
    L3_PRAGMATIC = 3     # 语用层: 效用/行为
    L4_SOCIAL = 4        # 社会层: 交互/共识
    L5_REFLECTIVE = 5    # 反思层: 元认知/自指
    L6_TRANSCENDENT = 6  # 超越层: 涌现/不可言说


# ═══════════════════════════════════════════════════════════════
# Pattern - 基础模式单元
# ═══════════════════════════════════════════════════════════════

@dataclass
class PatternSignature:
    """Pattern签名 - 唯一标识与特征"""
    hash: str                           # 内容哈希
    frequency: float                    # 特征频率 (Hz, 相对单位)
    phase: float                        # 相位 (0-2π)
    amplitude: float                    # 振幅 (0-1)
    entropy: float                      # 信息熵
    dimension: int                      # 维度
    
    def coherence(self, other: PatternSignature) -> float:
        """计算两个签名的相干度"""
        freq_match = 1 - abs(self.frequency - other.frequency) / max(self.frequency, other.frequency, 1e-10)
        phase_diff = abs(self.phase - other.phase)
        phase_match = math.cos(phase_diff / 2)  # 相位越近越相干
        amp_match = min(self.amplitude, other.amplitude) / max(self.amplitude, other.amplitude, 1e-10)
        return (freq_match * 0.4 + phase_match * 0.35 + amp_match * 0.25)


@dataclass 
class Pattern:
    """
    Pattern - 系统中的重复模式
    
    属性:
        id: 全局唯一标识
        type: Pattern类型
        layer: 所在层级
        signature: 模式签名(频率/相位/振幅)
        content: 模式内容(可序列化)
        lineage: 谱系(父模式ID列表)
        children: 子模式ID列表
        phase_state: 当前生命周期相位
        created_at: 创建时间
        last_resonated: 最后共振时间
        resonance_count: 共振次数
        metadata: 扩展元数据
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: PatternType = PatternType.EMERGENCE
    layer: LayerLevel = LayerLevel.L2_SEMANTIC
    signature: PatternSignature = field(default_factory=lambda: PatternSignature(
        hash="", frequency=1.0, phase=0.0, amplitude=0.5, entropy=0.5, dimension=3
    ))
    content: Any = None
    lineage: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    phase_state: PatternPhase = PatternPhase.GESTATION
    created_at: datetime = field(default_factory=datetime.now)
    last_resonated: Optional[datetime] = None
    resonance_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.signature.hash:
            self.signature.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """基于内容计算哈希"""
        content_str = json.dumps(self.content, default=str, sort_keys=True) if self.content else ""
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def resonate(self, other: Pattern) -> float:
        """
        与另一个Pattern共振
        返回共振强度 (0-1)
        """
        # 类型兼容性
        type_match = 1.0 if self.type == other.type else 0.3
        
        # 签名相干度
        sig_coherence = self.signature.coherence(other.signature)
        
        # 层级距离 (越近越易共振)
        layer_dist = abs(self.layer.value - other.layer.value)
        layer_factor = 1 / (1 + layer_dist * 0.5)
        
        # 共振强度
        strength = type_match * sig_coherence * layer_factor
        
        # 更新共振记录
        if strength > 0.5:
            self.resonance_count += 1
            self.last_resonated = datetime.now()
        
        return strength
    
    def evolve(self, stimulus: Dict[str, Any]) -> Pattern:
        """
        在刺激下演化，可能产生新Pattern
        """
        new_phase = self._next_phase(stimulus.get("intensity", 0.5))
        
        # 振幅根据刺激调整
        new_amplitude = min(1.0, self.signature.amplitude + stimulus.get("intensity", 0) * 0.1)
        
        # 相位偏移
        phase_shift = stimulus.get("phase_shift", 0.1)
        new_phase_val = (self.signature.phase + phase_shift) % (2 * math.pi)
        
        new_sig = PatternSignature(
            hash="",  # 重新计算
            frequency=self.signature.frequency * (1 + stimulus.get("freq_mod", 0)),
            phase=new_phase_val,
            amplitude=new_amplitude,
            entropy=self.signature.entropy + stimulus.get("entropy_delta", 0),
            dimension=self.signature.dimension
        )
        
        child = Pattern(
            type=self.type,
            layer=self.layer,
            signature=new_sig,
            content={**stimulus, "parent": self.id},
            lineage=[self.id] + self.lineage,
            phase_state=new_phase
        )
        
        self.children.append(child.id)
        return child
    
    def _next_phase(self, intensity: float) -> PatternPhase:
        """根据强度确定下一相位"""
        transitions = {
            PatternPhase.GESTATION: PatternPhase.BIRTH if intensity > 0.3 else PatternPhase.GESTATION,
            PatternPhase.BIRTH: PatternPhase.GROWTH,
            PatternPhase.GROWTH: PatternPhase.MATURITY if intensity > 0.5 else PatternPhase.DECLINE,
            PatternPhase.MATURITY: PatternPhase.TRANSFORM if intensity > 0.7 else PatternPhase.DECLINE,
            PatternPhase.DECLINE: PatternPhase.DEATH if intensity < 0.2 else PatternPhase.TRANSFORM,
            PatternPhase.TRANSFORM: PatternPhase.REBIRTH,
            PatternPhase.DEATH: PatternPhase.GESTATION,  # 循环
            PatternPhase.REBIRTH: PatternPhase.GROWTH
        }
        return transitions.get(self.phase_state, PatternPhase.GESTATION)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "layer": self.layer.name,
            "signature": {
                "hash": self.signature.hash,
                "frequency": self.signature.frequency,
                "phase": self.signature.phase,
                "amplitude": self.signature.amplitude,
                "entropy": self.signature.entropy,
                "dimension": self.signature.dimension
            },
            "content": self.content,
            "lineage": self.lineage,
            "children": self.children,
            "phase_state": self.phase_state.name,
            "created_at": self.created_at.isoformat(),
            "resonance_count": self.resonance_count,
            "metadata": self.metadata
        }


# ═══════════════════════════════════════════════════════════════
# MetaPattern - 元模式 (模式之上的模式)
# ═══════════════════════════════════════════════════════════════

class MetaPatternType(Enum):
    """元模式类型"""
    RECOGNITION = "recognition"      # 模式识别(识别Pattern的能力)
    GENERATION = "generation"        # 模式生成(生成新Pattern的能力)
    TRANSFORMATION = "transformation" # 模式转化(转化Pattern的能力)
    COMPOSITION = "composition"      # 模式组合(组合多个Pattern)
    DECOMPOSITION = "decomposition"  # 模式分解(分解Pattern)
    ABSTRACTION = "abstraction"      # 模式抽象(提取共性)
    INSTANTIATION = "instantiation"  # 模式实例化(具体化)
    SELF_REFERENCE = "self_reference" # 自引用(模式作用于自身)


@dataclass
class MetaPattern:
    """
    MetaPattern - 模式之上的模式
    
    元模式不是"更高层的Pattern"，而是"操作Pattern的Pattern"
    它描述的是Pattern之间的关系、变换、生成规则
    
    关键特性:
        - 自引用性: 元模式可应用于自身
        - 高阶性: 元模式操作的是Pattern的集合而非个体
        - 递归性: 元模式可生成新的元模式
    """
    id: str = field(default_factory=lambda: "MP-" + str(uuid.uuid4())[:6])
    meta_type: MetaPatternType = MetaPatternType.RECOGNITION
    name: str = ""
    description: str = ""
    
    # 输入/输出Pattern类型约束
    input_types: List[PatternType] = field(default_factory=list)
    output_types: List[PatternType] = field(default_factory=list)
    
    # 操作函数 (在运行时绑定)
    operator: Optional[Callable[[List[Pattern]], List[Pattern]]] = None
    
    # 元模式的元数据
    arity: int = 1              # 元数(输入Pattern数量)
    order: int = 2              # 阶数(2=操作Pattern, 3=操作MetaPattern)
    is_self_referential: bool = False  # 是否自引用
    
    # 应用统计
    application_count: int = 0
    success_rate: float = 1.0
    
    def apply(self, patterns: List[Pattern], context: Dict[str, Any] = None) -> List[Pattern]:
        """
        将元模式应用于Pattern集合
        
        Args:
            patterns: 输入Pattern列表
            context: 应用上下文
            
        Returns:
            转换后的Pattern列表
        """
        if len(patterns) < self.arity:
            raise ValueError(f"MetaPattern {self.name} requires at least {self.arity} patterns, got {len(patterns)}")
        
        self.application_count += 1
        
        if self.operator:
            try:
                result = self.operator(patterns[:self.arity])
                self.success_rate = (self.success_rate * (self.application_count - 1) + 1) / self.application_count
                return result
            except Exception as e:
                self.success_rate = (self.success_rate * (self.application_count - 1)) / self.application_count
                raise RuntimeError(f"MetaPattern application failed: {e}")
        
        # 默认操作: 恒等
        return patterns
    
    def can_apply_to(self, pattern: Pattern) -> bool:
        """检查是否可以应用于某个Pattern"""
        return not self.input_types or pattern.type in self.input_types
    
    def can_apply_to_self(self) -> bool:
        """检查是否可以自引用"""
        return self.is_self_referential
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "meta_type": self.meta_type.value,
            "name": self.name,
            "description": self.description,
            "input_types": [t.value for t in self.input_types],
            "output_types": [t.value for t in self.output_types],
            "arity": self.arity,
            "order": self.order,
            "is_self_referential": self.is_self_referential,
            "application_count": self.application_count,
            "success_rate": self.success_rate
        }


# ═══════════════════════════════════════════════════════════════
# PatternLayer - 层 (同频共振的Pattern集合)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PatternLayer:
    """
    PatternLayer - Pattern层
    
    层是同级别、同频率范围的Pattern集合。
    层内Pattern通过共振形成稳定的结构。
    
    七层架构:
        L0_PHYSICAL:     原始信号/数据 (高频, 低振幅)
        L1_SYNTACTIC:    结构/形式 (中高频)
        L2_SEMANTIC:     意义/内容 (中频)
        L3_PRAGMATIC:    效用/行为 (中低频)
        L4_SOCIAL:       交互/共识 (低频, 高振幅)
        L5_REFLECTIVE:   元认知/自指 (超低频)
        L6_TRANSCENDENT: 涌现/不可言说 (直流/永恒)
    """
    level: LayerLevel
    name: str = ""
    patterns: Dict[str, Pattern] = field(default_factory=dict)
    meta_patterns: Dict[str, MetaPattern] = field(default_factory=dict)
    
    # 层属性
    base_frequency: float = 1.0
    frequency_range: Tuple[float, float] = (0.5, 2.0)
    resonance_threshold: float = 0.6
    
    # 层内统计
    total_resonance_count: int = 0
    emergence_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.name:
            self.name = self.level.name
    
    def add_pattern(self, pattern: Pattern) -> bool:
        """
        添加Pattern到层
        检查频率是否在层范围内
        """
        freq = pattern.signature.frequency
        if not (self.frequency_range[0] <= freq <= self.frequency_range[1]):
            # 频率不匹配，尝试调整或拒绝
            return False
        
        self.patterns[pattern.id] = pattern
        pattern.layer = self.level
        return True
    
    def remove_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """从层中移除Pattern"""
        return self.patterns.pop(pattern_id, None)
    
    def find_resonant_pairs(self) -> List[Tuple[Pattern, Pattern, float]]:
        """
        查找层内所有共振对
        返回: [(pattern_a, pattern_b, strength), ...]
        """
        pairs = []
        pattern_list = list(self.patterns.values())
        for i in range(len(pattern_list)):
            for j in range(i + 1, len(pattern_list)):
                strength = pattern_list[i].resonate(pattern_list[j])
                if strength >= self.resonance_threshold:
                    pairs.append((pattern_list[i], pattern_list[j], strength))
                    self.total_resonance_count += 1
        return sorted(pairs, key=lambda x: x[2], reverse=True)
    
    def get_dominant_frequency(self) -> float:
        """获取层的主导频率 (加权平均)"""
        if not self.patterns:
            return self.base_frequency
        
        total_amp = sum(p.signature.amplitude for p in self.patterns.values())
        if total_amp == 0:
            return self.base_frequency
            
        weighted_freq = sum(
            p.signature.frequency * p.signature.amplitude 
            for p in self.patterns.values()
        ) / total_amp
        
        return weighted_freq
    
    def get_phase_distribution(self) -> Dict[str, int]:
        """获取相位分布"""
        phases = {"GESTATION": 0, "BIRTH": 0, "GROWTH": 0, "MATURITY": 0,
                  "DECLINE": 0, "TRANSFORM": 0, "DEATH": 0, "REBIRTH": 0}
        for p in self.patterns.values():
            phases[p.phase_state.name] = phases.get(p.phase_state.name, 0) + 1
        return phases
    
    def check_emergence(self) -> Optional[Pattern]:
        """
        检查是否发生涌现
        当多个Pattern共振强度超过阈值时，可能涌现新Pattern
        """
        pairs = self.find_resonant_pairs()
        if len(pairs) >= 3:
            # 计算涌现条件
            avg_strength = sum(p[2] for p in pairs[:3]) / 3
            if avg_strength > 0.8:
                # 产生涌现Pattern
                emergent = Pattern(
                    type=PatternType.EMERGENCE,
                    layer=self.level,
                    signature=PatternSignature(
                        hash="",
                        frequency=self.get_dominant_frequency(),
                        phase=sum(p.signature.phase for p, _, _ in pairs[:3]) / 3,
                        amplitude=min(1.0, avg_strength),
                        entropy=math.log(len(self.patterns) + 1),
                        dimension=max(p.signature.dimension for p, _, _ in pairs[:3])
                    ),
                    content={
                        "emergence_type": "layer_resonance",
                        "source_patterns": [p.id for p, _, _ in pairs[:3]],
                        "resonance_strength": avg_strength,
                        "layer": self.level.name
                    },
                    lineage=[p.id for p, _, _ in pairs[:3]]
                )
                
                self.emergence_events.append({
                    "timestamp": datetime.now().isoformat(),
                    "emergent_pattern_id": emergent.id,
                    "source_count": len(pairs),
                    "avg_strength": avg_strength
                })
                
                self.patterns[emergent.id] = emergent
                return emergent
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.name,
            "name": self.name,
            "pattern_count": len(self.patterns),
            "meta_pattern_count": len(self.meta_patterns),
            "base_frequency": self.base_frequency,
            "dominant_frequency": self.get_dominant_frequency(),
            "phase_distribution": self.get_phase_distribution(),
            "emergence_events": len(self.emergence_events),
            "total_resonance": self.total_resonance_count
        }


# ═══════════════════════════════════════════════════════════════
# PatternWeb - 网 (跨层关联的Pattern网络)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PatternEdge:
    """Pattern之间的边 - 关联关系"""
    source: str             # 源Pattern ID
    target: str             # 目标Pattern ID
    relation_type: str      # 关系类型
    strength: float         # 关联强度
    direction: str          # "->", "<-", "<->"
    layer_jump: int         # 跨层数
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PatternWeb:
    """
    PatternWeb - Pattern网络
    
    网是跨层Pattern的关联结构。
    网中的边表示Pattern之间的共振、因果、相似、包含等关系。
    
    特性:
        - 跨层连接: 不同层的Pattern可以相互关联
        - 多关系类型: 支持多种关系同时存在
        - 动态权重: 关联强度随共振历史变化
        - 聚类涌现: 高密度区域可能涌现新结构
    """
    id: str = field(default_factory=lambda: "WEB-" + str(uuid.uuid4())[:6])
    name: str = ""
    nodes: Dict[str, Pattern] = field(default_factory=dict)
    edges: List[PatternEdge] = field(default_factory=list)
    
    # 邻接索引
    adjacency: Dict[str, List[PatternEdge]] = field(default_factory=lambda: defaultdict(list))
    
    # 聚类结果
    clusters: List[Set[str]] = field(default_factory=list)
    
    def add_node(self, pattern: Pattern) -> str:
        """添加节点"""
        self.nodes[pattern.id] = pattern
        return pattern.id
    
    def add_edge(self, edge: PatternEdge) -> bool:
        """添加边"""
        if edge.source not in self.nodes or edge.target not in self.nodes:
            return False
        
        self.edges.append(edge)
        self.adjacency[edge.source].append(edge)
        if edge.direction == "<->":
            reverse = PatternEdge(
                source=edge.target,
                target=edge.source,
                relation_type=edge.relation_type,
                strength=edge.strength,
                direction=edge.direction,
                layer_jump=-edge.layer_jump
            )
            self.adjacency[edge.target].append(reverse)
        
        return True
    
    def find_path(self, source: str, target: str, min_strength: float = 0.3) -> Optional[List[str]]:
        """
        查找两Pattern之间的路径 (BFS)
        """
        if source not in self.nodes or target not in self.nodes:
            return None
        
        visited = {source}
        queue = [(source, [source])]
        
        while queue:
            current, path = queue.pop(0)
            if current == target:
                return path
            
            for edge in self.adjacency.get(current, []):
                if edge.strength >= min_strength and edge.target not in visited:
                    visited.add(edge.target)
                    queue.append((edge.target, path + [edge.target]))
        
        return None
    
    def compute_centrality(self) -> Dict[str, float]:
        """
        计算各节点的中心性 (简化版PageRank)
        """
        scores = {nid: 1.0 for nid in self.nodes}
        
        for _ in range(10):  # 迭代收敛
            new_scores = {}
            for nid in self.nodes:
                incoming = [e for e in self.edges if e.target == nid]
                score = sum(
                    scores[e.source] * e.strength / max(len(self.adjacency.get(e.source, [])), 1)
                    for e in incoming
                )
                new_scores[nid] = 0.85 * score + 0.15  # damping
            scores = new_scores
        
        return scores
    
    def find_clusters(self, min_strength: float = 0.5) -> List[Set[str]]:
        """
        基于连通性查找聚类
        """
        visited = set()
        clusters = []
        
        for nid in self.nodes:
            if nid in visited:
                continue
            
            cluster = set()
            stack = [nid]
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                cluster.add(current)
                
                for edge in self.adjacency.get(current, []):
                    if edge.strength >= min_strength and edge.target not in visited:
                        stack.append(edge.target)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        self.clusters = clusters
        return clusters
    
    def get_cross_layer_edges(self) -> List[PatternEdge]:
        """获取所有跨层边"""
        return [e for e in self.edges if e.layer_jump != 0]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "cluster_count": len(self.clusters),
            "cross_layer_edges": len(self.get_cross_layer_edges()),
            "top_central": sorted(self.compute_centrality().items(), key=lambda x: x[1], reverse=True)[:5]
        }


# ═══════════════════════════════════════════════════════════════
# PatternTower - 塔 (涌现更高阶Pattern的层级结构)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PatternTower:
    """
    PatternTower - Pattern塔
    
    塔是层+网的涌现结构。
    塔有明确的方向性: 从底层(L0)向上层(L6)涌现。
    塔的每一层都是下一层的涌现结果。
    
    塔的构建过程:
        1. 在各层内建立PatternLayer
        2. 在层间建立PatternWeb连接
        3. 底层涌现驱动上层生成
        4. 上层反馈调节底层
    
    塔的动力学:
        - 上行: 底层高频Pattern通过共振形成上层低频Pattern
        - 下行: 上层Pattern通过实例化生成底层Pattern
        - 循环: 上下行形成闭环
    """
    id: str = field(default_factory=lambda: "TOWER-" + str(uuid.uuid4())[:6])
    name: str = "OMNI-PatternTower"
    layers: Dict[LayerLevel, PatternLayer] = field(default_factory=dict)
    web: PatternWeb = field(default_factory=lambda: PatternWeb(name="tower-web"))
    
    # 塔的涌现历史
    emergence_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 塔的运行参数
    auto_emergence: bool = True         # 是否自动涌现
    feedback_loop: bool = True          # 是否启用反馈
    emergence_threshold: float = 0.75   # 涌现阈值
    
    def __post_init__(self):
        # 初始化七层
        for level in LayerLevel:
            if level not in self.layers:
                freq_base = 10.0 / (level.value + 1)  # 越上层频率越低
                self.layers[level] = PatternLayer(
                    level=level,
                    base_frequency=freq_base,
                    frequency_range=(freq_base * 0.5, freq_base * 1.5)
                )
    
    def add_pattern(self, pattern: Pattern) -> bool:
        """添加Pattern到对应层"""
        layer = self.layers.get(pattern.layer)
        if not layer:
            return False
        
        success = layer.add_pattern(pattern)
        if success:
            self.web.add_node(pattern)
        
        return success
    
    def connect_patterns(self, source_id: str, target_id: str, 
                         relation: str, strength: float,
                         bidirectional: bool = False) -> bool:
        """连接两个Pattern"""
        source = self.web.nodes.get(source_id)
        target = self.web.nodes.get(target_id)
        
        if not source or not target:
            return False
        
        layer_jump = target.layer.value - source.layer.value
        
        edge = PatternEdge(
            source=source_id,
            target=target_id,
            relation_type=relation,
            strength=strength,
            direction="<->" if bidirectional else "->",
            layer_jump=layer_jump
        )
        
        return self.web.add_edge(edge)
    
    def tick(self) -> Dict[str, Any]:
        """
        塔的一个时间步
        执行: 层内共振 → 跨层涌现 → 反馈调节
        """
        results = {
            "resonance_pairs": 0,
            "emergence_events": 0,
            "new_edges": 0,
            "feedback_adjustments": 0
        }
        
        # 1. 各层层内共振
        for layer in self.layers.values():
            pairs = layer.find_resonant_pairs()
            results["resonance_pairs"] += len(pairs)
        
        # 2. 检查各层涌现 (从低层到高层)
        if self.auto_emergence:
            for level in sorted(LayerLevel, key=lambda x: x.value):
                layer = self.layers[level]
                emergent = layer.check_emergence()
                if emergent:
                    results["emergence_events"] += 1
                    self.emergence_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "layer_emergence",
                        "layer": level.name,
                        "pattern_id": emergent.id
                    })
                    
                    # 尝试将涌现Pattern连接到上层
                    next_level = LayerLevel(level.value + 1) if level.value < 6 else None
                    if next_level:
                        self._try_promote(emergent, next_level)
        
        # 3. 更新网络连接
        self._update_web_connections()
        
        # 4. 反馈调节
        if self.feedback_loop:
            results["feedback_adjustments"] = self._apply_feedback()
        
        return results
    
    def _try_promote(self, pattern: Pattern, target_level: LayerLevel) -> bool:
        """尝试将Pattern提升到上层"""
        target_layer = self.layers.get(target_level)
        if not target_layer:
            return False
        
        # 调整频率到目标层范围
        mid_freq = (target_layer.frequency_range[0] + target_layer.frequency_range[1]) / 2
        pattern.signature.frequency = mid_freq
        pattern.layer = target_level
        
        success = target_layer.add_pattern(pattern)
        if success:
            self.web.add_node(pattern)
        
        return success
    
    def _update_web_connections(self) -> int:
        """更新网络连接"""
        new_edges = 0
        
        # 为共振强的Pattern对建立连接
        for layer in self.layers.values():
            for p1, p2, strength in layer.find_resonant_pairs():
                if strength > 0.7:
                    edge = PatternEdge(
                        source=p1.id,
                        target=p2.id,
                        relation_type="resonance",
                        strength=strength,
                        direction="<->",
                        layer_jump=0
                    )
                    if self.web.add_edge(edge):
                        new_edges += 1
        
        return new_edges
    
    def _apply_feedback(self) -> int:
        """上层对下层的反馈调节"""
        adjustments = 0
        
        # 上层Pattern影响下层频率
        for level in sorted(LayerLevel, key=lambda x: x.value, reverse=True):
            if level.value == 0:
                continue
                
            layer = self.layers[level]
            dominant_freq = layer.get_dominant_frequency()
            
            # 影响下层的base_frequency
            lower_level = LayerLevel(level.value - 1)
            lower_layer = self.layers.get(lower_level)
            if lower_layer:
                # 谐波关系: 下层频率 = 上层频率 * n
                lower_layer.base_frequency = dominant_freq * 2
                lower_layer.frequency_range = (
                    lower_layer.base_frequency * 0.5,
                    lower_layer.base_frequency * 1.5
                )
                adjustments += 1
        
        return adjustments
    
    def get_tower_state(self) -> Dict[str, Any]:
        """获取塔的整体状态"""
        return {
            "id": self.id,
            "name": self.name,
            "layers": {l.name: layer.to_dict() for l, layer in self.layers.items()},
            "web": self.web.to_dict(),
            "emergence_history_count": len(self.emergence_history),
            "total_patterns": sum(len(l.patterns) for l in self.layers.values())
        }
    
    def climb(self, from_level: LayerLevel, to_level: LayerLevel) -> List[List[str]]:
        """
        从一层"攀登"到另一层
        返回所有可能的路径
        """
        paths = []
        
        # 获取起始层的所有Pattern
        start_patterns = list(self.layers[from_level].patterns.keys())
        end_patterns = set(self.layers[to_level].patterns.keys())
        
        for start in start_patterns:
            for end in end_patterns:
                path = self.web.find_path(start, end)
                if path:
                    paths.append(path)
        
        return paths
    
    def observe_from(self, level: LayerLevel) -> Dict[str, Any]:
        """
        从某一层"观察"整个塔
        高层看底层: 看到整体/统计
        底层看高层: 看到模糊/投影
        """
        observer_height = level.value
        
        observation = {
            "observer_level": level.name,
            "visible_patterns": {},
            "resolution": 1.0 / (observer_height + 1)  # 越高分辨率越低
        }
        
        for l, layer in self.layers.items():
            distance = abs(l.value - observer_height)
            clarity = 1.0 / (1 + distance * 0.5)
            
            if l == level:
                # 同层: 清晰
                observation["visible_patterns"][l.name] = {
                    "count": len(layer.patterns),
                    "clarity": 1.0,
                    "details": [p.to_dict() for p in list(layer.patterns.values())[:3]]
                }
            else:
                # 异层: 模糊
                observation["visible_patterns"][l.name] = {
                    "count": len(layer.patterns),
                    "clarity": clarity,
                    "details": "..." if clarity < 0.5 else [p.id for p in list(layer.patterns.values())[:2]]
                }
        
        return observation


# ═══════════════════════════════════════════════════════════════
# PatternCloud - 云 (超越塔的分布式模式场)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PatternCloud:
    """
    PatternCloud - 模式云
    
    云是超越单个塔的分布式Pattern场。
    多个塔可以在云中共存、交互、融合。
    云没有中心，是分布式的。
    
    特性:
        - 去中心化: 没有单一控制点
        - 自组织: Pattern自动聚集/分离
        - 渗透性: 云之间可以渗透
        - 记忆性: 云保留历史Pattern的痕迹
    """
    id: str = field(default_factory=lambda: "CLOUD-" + str(uuid.uuid4())[:6])
    name: str = ""
    towers: Dict[str, PatternTower] = field(default_factory=dict)
    
    # 跨塔连接
    inter_tower_edges: List[PatternEdge] = field(default_factory=list)
    
    # 云的全局属性
    field_strength: float = 1.0     # 场强
    turbulence: float = 0.1         # 湍流度
    memory_decay: float = 0.95      # 记忆衰减率
    
    def add_tower(self, tower: PatternTower) -> str:
        """添加塔到云"""
        self.towers[tower.id] = tower
        return tower.id
    
    def diffuse(self, pattern: Pattern, source_tower: str) -> List[str]:
        """
        Pattern在云中扩散
        返回扩散到达的塔ID列表
        """
        reached = []
        
        for tid, tower in self.towers.items():
            if tid == source_tower:
                continue
            
            # 扩散概率取决于场强和湍流
            diffusion_prob = self.field_strength * (1 - self.turbulence)
            
            # 频率匹配度影响扩散
            target_freq = tower.layers[pattern.layer].get_dominant_frequency() if pattern.layer in tower.layers else 1.0
            freq_match = 1 - abs(pattern.signature.frequency - target_freq) / max(pattern.signature.frequency, target_freq, 1e-10)
            
            if diffusion_prob * freq_match > 0.5:
                # 扩散成功: 在目标塔创建Pattern的"投影"
                projection = Pattern(
                    type=pattern.type,
                    layer=pattern.layer,
                    signature=PatternSignature(
                        hash="",
                        frequency=target_freq,
                        phase=pattern.signature.phase,
                        amplitude=pattern.signature.amplitude * self.field_strength,
                        entropy=pattern.signature.entropy,
                        dimension=pattern.signature.dimension
                    ),
                    content={"projection_of": pattern.id, "source_tower": source_tower},
                    lineage=[pattern.id]
                )
                
                tower.add_pattern(projection)
                reached.append(tid)
        
        return reached
    
    def condense(self, tower_ids: List[str]) -> Optional[PatternTower]:
        """
        云中的塔凝结为新塔
        多个塔的部分Pattern融合
        """
        if len(tower_ids) < 2:
            return None
        
        new_tower = PatternTower(name=f"condensed-{self.id[:4]}")
        
        # 收集所有Pattern
        all_patterns = []
        for tid in tower_ids:
            tower = self.towers.get(tid)
            if tower:
                for layer in tower.layers.values():
                    all_patterns.extend(layer.patterns.values())
        
        # 按频率聚类，取每类的代表
        from itertools import groupby
        sorted_patterns = sorted(all_patterns, key=lambda p: p.signature.frequency)
        
        for freq_cluster in self._cluster_by_frequency(sorted_patterns):
            representative = max(freq_cluster, key=lambda p: p.signature.amplitude)
            new_tower.add_pattern(representative)
        
        return new_tower
    
    def _cluster_by_frequency(self, patterns: List[Pattern], threshold: float = 0.2) -> List[List[Pattern]]:
        """按频率聚类"""
        if not patterns:
            return []
        
        clusters = [[patterns[0]]]
        for p in patterns[1:]:
            last_cluster = clusters[-1]
            avg_freq = sum(x.signature.frequency for x in last_cluster) / len(last_cluster)
            if abs(p.signature.frequency - avg_freq) / avg_freq < threshold:
                last_cluster.append(p)
            else:
                clusters.append([p])
        
        return clusters
    
    def get_global_state(self) -> Dict[str, Any]:
        """获取云的全局状态"""
        total_patterns = sum(
            sum(len(l.patterns) for l in t.layers.values())
            for t in self.towers.values()
        )
        
        return {
            "id": self.id,
            "name": self.name,
            "tower_count": len(self.towers),
            "total_patterns": total_patterns,
            "field_strength": self.field_strength,
            "turbulence": self.turbulence,
            "inter_tower_connections": len(self.inter_tower_edges)
        }


# ═══════════════════════════════════════════════════════════════
# 工厂函数与预设
# ═══════════════════════════════════════════════════════════════

def create_si_cycle_pattern(cycle_type: str = "standard") -> Pattern:
    """创建SI循环Pattern"""
    return Pattern(
        type=PatternType.SI_CYCLE,
        layer=LayerLevel.L3_PRAGMATIC,
        signature=PatternSignature(
            hash="",
            frequency=1.618,  # 黄金频率
            phase=0.0,
            amplitude=0.8,
            entropy=0.6,
            dimension=4
        ),
        content={
            "cycle_type": cycle_type,
            "stages": ["Sensation", "Integration", "Action", "Reflection"],
            "period": 4,
            "is_recursive": True
        },
        metadata={"system": "SI", "version": "v12"}
    )


def create_surge_pattern(intensity: float = 0.8) -> Pattern:
    """创建浪涌Pattern"""
    return Pattern(
        type=PatternType.SURGE,
        layer=LayerLevel.L4_SOCIAL,
        signature=PatternSignature(
            hash="",
            frequency=0.5 + intensity * 2,
            phase=math.pi / 4,
            amplitude=intensity,
            entropy=0.3 + intensity * 0.5,
            dimension=5
        ),
        content={
            "surge_type": "knowledge",
            "intensity": intensity,
            "waveform": "exponential_rise",
            "decay_rate": 0.1
        }
    )


def create_debt_pattern(amount: float = 1.0, creditor: str = "", debtor: str = "") -> Pattern:
    """创建债务Pattern"""
    return Pattern(
        type=PatternType.DEBT,
        layer=LayerLevel.L3_PRAGMATIC,
        signature=PatternSignature(
            hash="",
            frequency=0.3,
            phase=math.pi,
            amplitude=amount,
            entropy=0.4,
            dimension=3
        ),
        content={
            "debt_type": "proof_debt",
            "amount": amount,
            "creditor": creditor,
            "debtor": debtor,
            "status": "outstanding"
        }
    )


def create_default_tower() -> PatternTower:
    """创建默认塔，预置基础Pattern"""
    tower = PatternTower(name="OMNI-Default-Tower")
    
    # 添加SI循环Pattern到L3
    si = create_si_cycle_pattern()
    tower.add_pattern(si)
    
    # 添加浪涌Pattern到L4
    surge = create_surge_pattern(intensity=0.7)
    tower.add_pattern(surge)
    
    # 添加债务Pattern到L3
    debt = create_debt_pattern(amount=0.5, creditor="system", debtor="user")
    tower.add_pattern(debt)
    
    # 建立连接
    tower.connect_patterns(si.id, surge.id, "drives", 0.7)
    tower.connect_patterns(surge.id, debt.id, "generates", 0.6)
    tower.connect_patterns(debt.id, si.id, "feeds_back", 0.5)
    
    return tower


# ═══════════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("OMNI-HUB v12 - Pattern Tower Architecture")
    print("=" * 60)
    
    # 创建默认塔
    tower = create_default_tower()
    print(f"\n[1] Created Tower: {tower.name}")
    print(f"    Total patterns: {sum(len(l.patterns) for l in tower.layers.values())}")
    
    # 运行几个tick
    print("\n[2] Running 3 ticks...")
    for i in range(3):
        result = tower.tick()
        print(f"    Tick {i+1}: {result}")
    
    # 获取塔状态
    print("\n[3] Tower State:")
    state = tower.get_tower_state()
    for layer_name, layer_info in state["layers"].items():
        print(f"    {layer_name}: {layer_info['pattern_count']} patterns, "
              f"freq={layer_info['dominant_frequency']:.2f}")
    
    # 观察视角
    print("\n[4] Observation from L3_PRAGMATIC:")
    obs = tower.observe_from(LayerLevel.L3_PRAGMATIC)
    for level_name, visibility in obs["visible_patterns"].items():
        print(f"    {level_name}: clarity={visibility['clarity']:.2f}, "
              f"count={visibility['count']}")
    
    # 创建PatternCloud
    print("\n[5] Pattern Cloud:")
    cloud = PatternCloud(name="OMNI-Cloud")
    cloud.add_tower(tower)
    
    tower2 = create_default_tower()
    tower2.name = "OMNI-Secondary"
    cloud.add_tower(tower2)
    
    print(f"    Cloud state: {cloud.get_global_state()}")
    
    print("\n" + "=" * 60)
    print("Pattern Tower Architecture Demo Complete")
    print("=" * 60)
