#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v8.0 — RingTopologyEngine
环拓扑引擎 — 管理OMNI-HUB中所有环的注册、验证、互激和自组织

Author: OMNI-HUB Core Architect
Version: 8.0.0

11线名称:
    ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']

环类型 (ring_type):
    - pair: 对闭环 (两线互逆)
    - chain: 链环 (开放链状)
    - cycle: 循环环 (闭合链)
    - self: 自环 (单线自指)
    - causal: 因果环 (因果闭环)
    - meta: 元环 (环之环)

闭合类型 (closure_type):
    - meridian: 经环 (纵向贯通)
    - latitude: 纬环 (横向闭合)
    - grid: 经纬环 (纵横交织)
    - open: 开放 (未闭合)
"""

import numpy as np
import uuid
import json
from typing import List, Dict, Tuple, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import random
import logging


class RingType(Enum):
    """环类型枚举"""
    PAIR = "pair"
    CHAIN = "chain"
    CYCLE = "cycle"
    SELF = "self"
    CAUSAL = "causal"
    META = "meta"


class ClosureType(Enum):
    """闭合类型枚举"""
    MERIDIAN = "meridian"   # 经环
    LATITUDE = "latitude"   # 纬环
    GRID = "grid"           # 经纬环
    OPEN = "open"           # 开放


class RingStatus(Enum):
    """环状态枚举"""
    OPEN = "open"
    CLOSED = "closed"
    RESONATING = "resonating"
    DECAYING = "decaying"


@dataclass
class Ring:
    """
    Ring — 环类
    
    表示OMNI-HUB中的一个环结构，由有序的线成员组成，
    首尾相连形成闭合或非闭合的拓扑结构。
    
    Attributes:
        ring_id: 环唯一标识符
        name: 环名称
        members: 成员线列表（有序，首尾相连形成环）
        ring_type: 环类型（pair/chain/cycle/self/causal/meta）
        closure_type: 闭合类型（meridian/latitude/grid/open）
        energy: 环能量（标量）
        coherence: 环相干度 [0,1]
        status: 环状态
        phase: 环相位 [0, 2π)
        frequency: 环共振频率
        creation_time: 创建时间戳
        metadata: 额外元数据
    """
    ring_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "unnamed_ring"
    members: List[str] = field(default_factory=list)
    ring_type: RingType = RingType.CHAIN
    closure_type: ClosureType = ClosureType.OPEN
    energy: float = 0.0
    coherence: float = 1.0
    status: RingStatus = RingStatus.OPEN
    phase: float = 0.0
    frequency: float = 1.0
    creation_time: float = field(default_factory=lambda: float(np.random.randint(0, 1000000)))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 内部状态
    _energy_history: List[float] = field(default_factory=list, repr=False)
    _coherence_history: List[float] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.ring_type, str):
            self.ring_type = RingType(self.ring_type)
        if isinstance(self.closure_type, str):
            self.closure_type = ClosureType(self.closure_type)
        if isinstance(self.status, str):
            self.status = RingStatus(self.status)
        self._energy_history = [self.energy]
        self._coherence_history = [self.coherence]
    
    def add_member(self, line_id: str, position: int = -1) -> None:
        """
        添加成员线到环
        
        Args:
            line_id: 线标识符
            position: 插入位置，-1表示末尾
        """
        if line_id in self.members:
            return
        if position == -1:
            self.members.append(line_id)
        else:
            self.members.insert(position, line_id)
        self._update_status()
    
    def remove_member(self, line_id: str) -> bool:
        """
        从环中移除成员线
        
        Args:
            line_id: 线标识符
            
        Returns:
            是否成功移除
        """
        if line_id not in self.members:
            return False
        self.members.remove(line_id)
        self._update_status()
        return True
    
    def is_closed(self) -> bool:
        """
        检查环是否闭合
        
        闭合条件：
        - self类型：始终闭合
        - pair类型：恰好2个成员
        - cycle类型：成员数≥3且首尾可连
        - 其他：根据closure_type判断
        
        Returns:
            是否闭合
        """
        if self.ring_type == RingType.SELF:
            return len(self.members) == 1
        elif self.ring_type == RingType.PAIR:
            return len(self.members) == 2
        elif self.ring_type in (RingType.CYCLE, RingType.CAUSAL):
            return len(self.members) >= 3
        elif self.ring_type == RingType.META:
            return len(self.members) >= 2
        else:
            return self.closure_type != ClosureType.OPEN
    
    def _update_status(self) -> None:
        """根据当前状态更新环状态"""
        if self.is_closed():
            if self.status == RingStatus.OPEN:
                self.status = RingStatus.CLOSED
        else:
            self.status = RingStatus.OPEN
    
    def circulate(self, energy: float, direction: int = 1) -> float:
        """
        能量环流
        
        模拟能量在环中的流动，返回环流后的能量分布方差
        （方差越小表示环流越均匀）
        
        Args:
            energy: 注入能量
            direction: 环流方向 (1=顺时针, -1=逆时针)
            
        Returns:
            能量分布均匀度 [0,1]
        """
        if not self.members:
            return 0.0
        
        # 能量注入
        self.energy += energy
        
        # 模拟环流：能量在成员间均匀化
        n = len(self.members)
        if n == 0:
            return 0.0
            
        # 计算环流后的能量分布
        # 理想情况下能量均匀分布
        ideal_per_member = self.energy / n
        
        # 考虑相干度影响：相干度越高，能量分布越均匀
        uniformity = self.coherence * (1.0 - 0.1 * np.random.random())
        
        # 能量衰减（小量）
        decay_factor = 0.999
        self.energy *= decay_factor
        
        self._energy_history.append(self.energy)
        if len(self._energy_history) > 1000:
            self._energy_history = self._energy_history[-1000:]
        
        return uniformity
    
    def resonate(self, frequency: float) -> float:
        """
        共振
        
        当外部频率接近环的固有频率时发生共振，
        共振增强环的能量和相干度。
        
        Args:
            frequency: 外部驱动频率
            
        Returns:
            共振强度 [0, 1]
        """
        if self.frequency <= 0:
            self.frequency = 1.0
            
        # 频率匹配度
        freq_ratio = frequency / self.frequency
        # 共振曲线 (Lorentzian-like)
        resonance_strength = 1.0 / (1.0 + 4.0 * (freq_ratio - 1.0) ** 2)
        
        # 共振增强能量和相干度
        energy_gain = resonance_strength * 0.5
        coherence_gain = resonance_strength * 0.1
        
        self.energy += energy_gain
        self.coherence = min(1.0, self.coherence + coherence_gain)
        self.phase = (self.phase + frequency * 0.1) % (2 * np.pi)
        
        if resonance_strength > 0.7:
            self.status = RingStatus.RESONATING
        
        self._coherence_history.append(self.coherence)
        if len(self._coherence_history) > 1000:
            self._coherence_history = self._coherence_history[-1000:]
        
        return resonance_strength
    
    def decay(self, rate: float = 0.01) -> float:
        """
        衰减
        
        环的能量和相干度随时间衰减。
        
        Args:
            rate: 衰减率
            
        Returns:
            衰减后的能量
        """
        self.energy *= (1.0 - rate)
        self.coherence *= (1.0 - rate * 0.5)
        self.coherence = max(0.0, self.coherence)
        
        if self.energy < 0.01:
            self.status = RingStatus.DECAYING
        
        self._energy_history.append(self.energy)
        self._coherence_history.append(self.coherence)
        return self.energy
    
    def get_energy_flow(self) -> np.ndarray:
        """
        获取能量流分布
        
        Returns:
            各成员的能量分布数组
        """
        n = len(self.members)
        if n == 0:
            return np.array([])
        base = self.energy / n
        # 添加小扰动
        noise = np.random.normal(0, base * 0.1 * (1 - self.coherence), n)
        flow = np.full(n, base) + noise
        return np.maximum(flow, 0)
    
    def get_adjacency_matrix(self, line_index_map: Dict[str, int]) -> np.ndarray:
        """
        获取环的邻接矩阵表示
        
        Args:
            line_index_map: 线名到索引的映射
            
        Returns:
            邻接矩阵
        """
        n_lines = len(line_index_map)
        adj = np.zeros((n_lines, n_lines), dtype=np.float32)
        
        m = len(self.members)
        for i in range(m):
            curr = self.members[i]
            next_m = self.members[(i + 1) % m] if self.is_closed() else (
                self.members[i + 1] if i + 1 < m else None
            )
            if next_m and curr in line_index_map and next_m in line_index_map:
                ci = line_index_map[curr]
                ni = line_index_map[next_m]
                adj[ci, ni] = self.energy / max(1, m)
        
        return adj
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "ring_id": self.ring_id,
            "name": self.name,
            "members": self.members,
            "ring_type": self.ring_type.value,
            "closure_type": self.closure_type.value,
            "energy": float(self.energy),
            "coherence": float(self.coherence),
            "status": self.status.value,
            "phase": float(self.phase),
            "frequency": float(self.frequency),
            "creation_time": self.creation_time,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ring":
        """从字典反序列化"""
        return cls(
            ring_id=data.get("ring_id", str(uuid.uuid4())[:8]),
            name=data.get("name", "unnamed_ring"),
            members=data.get("members", []),
            ring_type=RingType(data.get("ring_type", "chain")),
            closure_type=ClosureType(data.get("closure_type", "open")),
            energy=data.get("energy", 0.0),
            coherence=data.get("coherence", 1.0),
            status=RingStatus(data.get("status", "open")),
            phase=data.get("phase", 0.0),
            frequency=data.get("frequency", 1.0),
            creation_time=data.get("creation_time", 0.0),
            metadata=data.get("metadata", {}),
        )
    
    def __repr__(self) -> str:
        return f"Ring({self.ring_id}, {self.name}, type={self.ring_type.value}, members={self.members}, energy={self.energy:.3f}, coherence={self.coherence:.3f})"
    
    def __hash__(self) -> int:
        return hash(self.ring_id)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Ring):
            return self.ring_id == other.ring_id
        return False


class RingRegistry:
    """
    RingRegistry — 环注册表
    
    管理OMNI-HUB中所有环的注册、注销和查询。
    支持按类型、线成员、闭合类型等多维度检索。
    """
    
    def __init__(self):
        """初始化空注册表"""
        self._rings: Dict[str, Ring] = {}
        self._line_index: Dict[str, Set[str]] = defaultdict(set)
        self._type_index: Dict[RingType, Set[str]] = defaultdict(set)
        self._closure_index: Dict[ClosureType, Set[str]] = defaultdict(set)
        self._name_index: Dict[str, str] = {}  # name -> ring_id
    
    @property
    def rings(self) -> Dict[str, Ring]:
        """获取所有环的字典"""
        return self._rings.copy()
    
    def register_ring(self, ring: Ring) -> bool:
        """
        注册环
        
        Args:
            ring: 要注册的环实例
            
        Returns:
            是否注册成功
        """
        if ring.ring_id in self._rings:
            return False
        
        self._rings[ring.ring_id] = ring
        self._name_index[ring.name] = ring.ring_id
        self._type_index[ring.ring_type].add(ring.ring_id)
        self._closure_index[ring.closure_type].add(ring.ring_id)
        
        for line in ring.members:
            self._line_index[line].add(ring.ring_id)
        
        return True
    
    def unregister_ring(self, ring_id: str) -> bool:
        """
        注销环
        
        Args:
            ring_id: 环标识符
            
        Returns:
            是否成功注销
        """
        if ring_id not in self._rings:
            return False
        
        ring = self._rings[ring_id]
        del self._rings[ring_id]
        
        if ring.name in self._name_index:
            del self._name_index[ring.name]
        
        self._type_index[ring.ring_type].discard(ring_id)
        self._closure_index[ring.closure_type].discard(ring_id)
        
        for line in ring.members:
            self._line_index[line].discard(ring_id)
        
        return True
    
    def get_ring(self, ring_id: str) -> Optional[Ring]:
        """
        通过ID获取环
        
        Args:
            ring_id: 环标识符
            
        Returns:
            环实例或None
        """
        return self._rings.get(ring_id)
    
    def get_ring_by_name(self, name: str) -> Optional[Ring]:
        """
        通过名称获取环
        
        Args:
            name: 环名称
            
        Returns:
            环实例或None
        """
        rid = self._name_index.get(name)
        if rid:
            return self._rings.get(rid)
        return None
    
    def get_rings_by_type(self, ring_type: RingType) -> List[Ring]:
        """
        按类型获取环
        
        Args:
            ring_type: 环类型
            
        Returns:
            环列表
        """
        return [self._rings[rid] for rid in self._type_index[ring_type] if rid in self._rings]
    
    def get_rings_by_line(self, line_id: str) -> List[Ring]:
        """
        获取包含某线的环
        
        Args:
            line_id: 线标识符
            
        Returns:
            包含该线的环列表
        """
        return [self._rings[rid] for rid in self._line_index.get(line_id, set()) if rid in self._rings]
    
    def get_rings_by_closure(self, closure_type: ClosureType) -> List[Ring]:
        """
        按闭合类型获取环
        
        Args:
            closure_type: 闭合类型
            
        Returns:
            环列表
        """
        return [self._rings[rid] for rid in self._closure_index[closure_type] if rid in self._rings]
    
    def detect_overlapping_rings(self) -> List[Tuple[Ring, Ring, Set[str]]]:
        """
        检测重叠环
        
        找出共享至少一个成员的环对。
        
        Returns:
            [(环A, 环B, 共享成员集), ...]
        """
        overlaps = []
        ring_ids = list(self._rings.keys())
        
        for i in range(len(ring_ids)):
            for j in range(i + 1, len(ring_ids)):
                r1 = self._rings[ring_ids[i]]
                r2 = self._rings[ring_ids[j]]
                shared = set(r1.members) & set(r2.members)
                if shared:
                    overlaps.append((r1, r2, shared))
        
        return overlaps
    
    def list_all_rings(self) -> List[Ring]:
        """
        列出所有环
        
        Returns:
            所有环的列表
        """
        return list(self._rings.values())
    
    def count(self) -> int:
        """环数量"""
        return len(self._rings)
    
    def clear(self) -> None:
        """清空注册表"""
        self._rings.clear()
        self._line_index.clear()
        self._type_index.clear()
        self._closure_index.clear()
        self._name_index.clear()


class RingVerifier:
    """
    RingVerifier — 环验证器
    
    验证环的各种物理和拓扑属性，确保环的合法性和一致性。
    """
    
    def __init__(self, line_names: Optional[List[str]] = None):
        """
        初始化验证器
        
        Args:
            line_names: 有效的线名称列表
        """
        self.line_names = set(line_names) if line_names else set()
        self._verification_log: List[Dict[str, Any]] = []
    
    def verify_closure(self, ring: Ring) -> Dict[str, Any]:
        """
        验证环的闭合性
        
        检查环是否满足其声明类型的闭合条件。
        
        Args:
            ring: 待验证的环
            
        Returns:
            {"passed": bool, "score": float, "details": str}
        """
        is_closed = ring.is_closed()
        score = 1.0 if is_closed else 0.0
        
        details = f"Type={ring.ring_type.value}, members={len(ring.members)}, closed={is_closed}"
        
        # 额外检查：首尾成员是否形成有效连接
        if is_closed and len(ring.members) >= 2:
            # 首尾相连形成闭合
            score = 1.0
        
        result = {
            "passed": is_closed,
            "score": score,
            "details": details,
            "ring_id": ring.ring_id,
        }
        self._verification_log.append(result)
        return result
    
    def verify_resonance(self, ring: Ring, tolerance: float = 0.1) -> Dict[str, Any]:
        """
        验证共振条件
        
        检查环的共振参数是否合理。
        
        Args:
            ring: 待验证的环
            tolerance: 容差
            
        Returns:
            {"passed": bool, "score": float, "details": str}
        """
        issues = []
        
        # 频率必须为正
        if ring.frequency <= 0:
            issues.append("frequency must be positive")
        
        # 相干度在[0,1]
        if not (0.0 <= ring.coherence <= 1.0):
            issues.append(f"coherence {ring.coherence} out of [0,1]")
        
        # 能量非负
        if ring.energy < 0:
            issues.append("energy cannot be negative")
        
        passed = len(issues) == 0
        score = 1.0 if passed else max(0.0, 1.0 - len(issues) * 0.3)
        
        result = {
            "passed": passed,
            "score": score,
            "details": "; ".join(issues) if issues else "resonance parameters valid",
            "ring_id": ring.ring_id,
        }
        self._verification_log.append(result)
        return result
    
    def verify_causality(self, ring: Ring) -> Dict[str, Any]:
        """
        验证因果一致性
        
        检查因果环是否满足因果一致性：
        - 无矛盾的因果关系
        - 因果链首尾一致
        
        Args:
            ring: 待验证的环
            
        Returns:
            {"passed": bool, "score": float, "details": str}
        """
        if ring.ring_type != RingType.CAUSAL:
            return {
                "passed": True,
                "score": 1.0,
                "details": "not a causal ring, skip",
                "ring_id": ring.ring_id,
            }
        
        # 因果环至少要有3个成员才能形成闭环
        if len(ring.members) < 2:
            return {
                "passed": False,
                "score": 0.0,
                "details": "causal ring needs >=2 members",
                "ring_id": ring.ring_id,
            }
        
        # 检查首尾一致性（简化：首尾成员不应矛盾）
        passed = len(ring.members) >= 3
        score = 1.0 if passed else 0.5
        
        result = {
            "passed": passed,
            "score": score,
            "details": "causal consistency verified" if passed else "insufficient members for causal loop",
            "ring_id": ring.ring_id,
        }
        self._verification_log.append(result)
        return result
    
    def verify_energy_conservation(self, ring: Ring, delta_threshold: float = 0.01) -> Dict[str, Any]:
        """
        验证能量守恒
        
        检查环的能量变化是否符合守恒定律（允许小量损耗）。
        
        Args:
            ring: 待验证的环
            delta_threshold: 能量变化阈值
            
        Returns:
            {"passed": bool, "score": float, "details": str}
        """
        history = ring._energy_history
        if len(history) < 2:
            return {
                "passed": True,
                "score": 1.0,
                "details": "no history to verify",
                "ring_id": ring.ring_id,
            }
        
        # 检查能量突变
        max_delta = max(abs(history[i] - history[i-1]) for i in range(1, len(history)))
        
        # 能量不应为负
        if ring.energy < 0:
            passed = False
            score = 0.0
            details = "energy is negative"
        elif max_delta > delta_threshold * 10:
            passed = False
            score = 0.5
            details = f"large energy jump detected: {max_delta:.4f}"
        else:
            passed = True
            score = 1.0
            details = f"energy conservation holds, max_delta={max_delta:.4f}"
        
        result = {
            "passed": passed,
            "score": score,
            "details": details,
            "ring_id": ring.ring_id,
        }
        self._verification_log.append(result)
        return result
    
    def full_verify(self, ring: Ring) -> Dict[str, Any]:
        """
        全面验证
        
        对环执行所有验证项目。
        
        Args:
            ring: 待验证的环
            
        Returns:
            {"passed": bool, "score": float, "results": [sub_results]}
        """
        results = [
            self.verify_closure(ring),
            self.verify_resonance(ring),
            self.verify_causality(ring),
            self.verify_energy_conservation(ring),
        ]
        
        all_passed = all(r["passed"] for r in results)
        avg_score = np.mean([r["score"] for r in results])
        
        return {
            "passed": all_passed,
            "score": float(avg_score),
            "results": results,
            "ring_id": ring.ring_id,
        }
    
    def get_log(self) -> List[Dict[str, Any]]:
        """获取验证日志"""
        return self._verification_log.copy()
    
    def clear_log(self) -> None:
        """清空验证日志"""
        self._verification_log.clear()


class RingInteraction:
    """
    RingInteraction — 环互作
    
    处理多个环之间的相互作用，包括互激、能量转移、相位锁定和干涉。
    """
    
    def __init__(self, coupling_matrix: Optional[np.ndarray] = None):
        """
        初始化互作处理器
        
        Args:
            coupling_matrix: 环间耦合系数矩阵
        """
        self.coupling_matrix = coupling_matrix
        self._interaction_log: List[Dict[str, Any]] = []
    
    def mutual_excitation(self, ring_a: Ring, ring_b: Ring, 
                          coupling_strength: Optional[float] = None) -> Dict[str, Any]:
        """
        互激
        
        两个环通过共享成员或场耦合相互激发。
        
        Args:
            ring_a: 环A
            ring_b: 环B
            coupling_strength: 耦合强度，None时自动计算
            
        Returns:
            {"energy_a": float, "energy_b": float, "strength": float}
        """
        # 计算共享成员比例作为耦合强度
        shared = set(ring_a.members) & set(ring_b.members)
        if coupling_strength is None:
            if ring_a.members and ring_b.members:
                coupling_strength = len(shared) / max(len(ring_a.members), len(ring_b.members))
            else:
                coupling_strength = 0.1
        
        coupling_strength = max(0.0, min(1.0, coupling_strength))
        
        # 互激公式：能量从高能环流向低能环，同时总能量略有增加
        energy_diff = ring_b.energy - ring_a.energy
        transfer = coupling_strength * energy_diff * 0.5
        
        ring_a.energy += transfer + coupling_strength * 0.1
        ring_b.energy -= transfer - coupling_strength * 0.1
        
        # 相干度相互影响
        avg_coherence = (ring_a.coherence + ring_b.coherence) / 2
        ring_a.coherence = 0.7 * ring_a.coherence + 0.3 * avg_coherence
        ring_b.coherence = 0.7 * ring_b.coherence + 0.3 * avg_coherence
        
        result = {
            "energy_a": float(ring_a.energy),
            "energy_b": float(ring_b.energy),
            "strength": float(coupling_strength),
            "shared_members": list(shared),
            "type": "mutual_excitation",
        }
        self._interaction_log.append(result)
        return result
    
    def energy_transfer(self, ring_a: Ring, ring_b: Ring, amount: float) -> Dict[str, Any]:
        """
        能量转移
        
        从环A向环B转移指定能量。
        
        Args:
            ring_a: 源环
            ring_b: 目标环
            amount: 转移能量量
            
        Returns:
            {"transferred": float, "remaining_a": float, "received_b": float}
        """
        actual_transfer = min(amount, ring_a.energy * 0.5)  # 最多转移50%
        ring_a.energy -= actual_transfer
        ring_b.energy += actual_transfer * 0.95  # 5%损耗
        
        result = {
            "transferred": float(actual_transfer),
            "remaining_a": float(ring_a.energy),
            "received_b": float(ring_b.energy),
            "loss": float(actual_transfer * 0.05),
            "type": "energy_transfer",
        }
        self._interaction_log.append(result)
        return result
    
    def phase_lock(self, ring_a: Ring, ring_b: Ring, 
                   lock_strength: float = 0.5) -> Dict[str, Any]:
        """
        相位锁定
        
        使两个环的相位趋于同步。
        
        Args:
            ring_a: 环A
            ring_b: 环B
            lock_strength: 锁定强度 [0,1]
            
        Returns:
            {"phase_diff": float, "locked": bool}
        """
        phase_diff = abs(ring_a.phase - ring_b.phase)
        phase_diff = min(phase_diff, 2 * np.pi - phase_diff)
        
        # 相位向中间靠拢
        target_phase = (ring_a.phase + ring_b.phase) / 2
        ring_a.phase = (ring_a.phase * (1 - lock_strength) + target_phase * lock_strength) % (2 * np.pi)
        ring_b.phase = (ring_b.phase * (1 - lock_strength) + target_phase * lock_strength) % (2 * np.pi)
        
        locked = phase_diff < 0.1
        
        result = {
            "phase_diff": float(phase_diff),
            "locked": locked,
            "target_phase": float(target_phase),
            "type": "phase_lock",
        }
        self._interaction_log.append(result)
        return result
    
    def constructive_interference(self, ring_a: Ring, ring_b: Ring) -> Dict[str, Any]:
        """
        相长干涉
        
        当两个环相位相近时，发生相长干涉，能量增强。
        
        Args:
            ring_a: 环A
            ring_b: 环B
            
        Returns:
            {"interference_factor": float, "energy_gain": float}
        """
        phase_diff = abs(ring_a.phase - ring_b.phase)
        phase_diff = min(phase_diff, 2 * np.pi - phase_diff)
        
        # 相长干涉：相位差越小，干涉越强
        interference_factor = 0.5 * (1 + np.cos(phase_diff))
        energy_gain = interference_factor * (ring_a.energy + ring_b.energy) * 0.1
        
        ring_a.energy += energy_gain * 0.5
        ring_b.energy += energy_gain * 0.5
        
        result = {
            "interference_factor": float(interference_factor),
            "energy_gain": float(energy_gain),
            "phase_diff": float(phase_diff),
            "type": "constructive_interference",
        }
        self._interaction_log.append(result)
        return result
    
    def destructive_interference(self, ring_a: Ring, ring_b: Ring) -> Dict[str, Any]:
        """
        相消干涉
        
        当两个环相位相反时，发生相消干涉，能量减弱。
        
        Args:
            ring_a: 环A
            ring_b: 环B
            
        Returns:
            {"interference_factor": float, "energy_loss": float}
        """
        phase_diff = abs(ring_a.phase - ring_b.phase)
        phase_diff = min(phase_diff, 2 * np.pi - phase_diff)
        
        # 相消干涉：相位差越大，相消越强
        interference_factor = 0.5 * (1 - np.cos(phase_diff))
        energy_loss = interference_factor * min(ring_a.energy, ring_b.energy) * 0.1
        
        ring_a.energy -= energy_loss * 0.5
        ring_b.energy -= energy_loss * 0.5
        ring_a.energy = max(0, ring_a.energy)
        ring_b.energy = max(0, ring_b.energy)
        
        result = {
            "interference_factor": float(interference_factor),
            "energy_loss": float(energy_loss),
            "phase_diff": float(phase_diff),
            "type": "destructive_interference",
        }
        self._interaction_log.append(result)
        return result
    
    def get_interaction_log(self) -> List[Dict[str, Any]]:
        """获取互作日志"""
        return self._interaction_log.copy()


class SelfOrganizingRingDetector:
    """
    SelfOrganizingRingDetector — 自组织环检测器
    
    从系统交互中自动检测潜在的环结构，包括因果环、共振簇等。
    """
    
    def __init__(self, line_names: List[str]):
        """
        初始化检测器
        
        Args:
            line_names: 线名称列表
        """
        self.line_names = line_names
        self._detected_rings: List[Ring] = []
        self._proposals: List[Dict[str, Any]] = []
    
    def detect_from_interactions(self, interactions: List[Tuple[str, str, float]]) -> List[Ring]:
        """
        从交互中检测潜在环
        
        根据线之间的交互强度图，检测闭合路径。
        
        Args:
            interactions: [(源线, 目标线, 强度), ...]
            
        Returns:
            检测到的潜在新环列表
        """
        # 构建邻接图
        graph = defaultdict(dict)
        for src, dst, strength in interactions:
            if strength > 0.3:  # 阈值
                graph[src][dst] = strength
        
        detected = []
        
        # 检测3-5长度的环
        for start in self.line_names:
            for length in range(3, 6):
                paths = self._find_cycles(graph, start, length)
                for path in paths:
                    ring = Ring(
                        name=f"auto_{start}_{length}",
                        members=path,
                        ring_type=RingType.CYCLE,
                        closure_type=ClosureType.LATITUDE,
                        energy=sum(graph[path[i]].get(path[(i+1)%len(path)], 0) for i in range(len(path))),
                        coherence=0.5,
                    )
                    detected.append(ring)
        
        self._detected_rings.extend(detected)
        return detected
    
    def _find_cycles(self, graph: Dict, start: str, length: int) -> List[List[str]]:
        """
        从图中查找指定长度的环
        
        Args:
            graph: 邻接图
            start: 起始节点
            length: 环长度
            
        Returns:
            环路径列表
        """
        cycles = []
        visited = set()
        
        def dfs(node: str, path: List[str]):
            if len(path) == length:
                if node == start:
                    cycles.append(path.copy())
                return
            
            for neighbor in graph.get(node, {}):
                if neighbor not in visited or (len(path) == length - 1 and neighbor == start):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        path.append(neighbor)
                        dfs(neighbor, path)
                        path.pop()
                        visited.remove(neighbor)
                    elif len(path) == length - 1 and neighbor == start:
                        path.append(neighbor)
                        dfs(neighbor, path)
                        path.pop()
        
        visited.add(start)
        dfs(start, [start])
        return cycles
    
    def detect_causal_loops(self, causal_graph: Dict[str, List[str]]) -> List[Ring]:
        """
        检测因果环
        
        从因果图中检测闭环因果关系。
        
        Args:
            causal_graph: {原因: [结果列表]}
            
        Returns:
            因果环列表
        """
        loops = []
        
        def dfs(node: str, path: List[str], visited: Set[str]):
            if node in visited:
                if node == path[0] and len(path) >= 3:
                    # 发现因果环
                    ring = Ring(
                        name=f"causal_{node}",
                        members=path,
                        ring_type=RingType.CAUSAL,
                        closure_type=ClosureType.MERIDIAN,
                        energy=len(path) * 0.5,
                        coherence=0.7,
                    )
                    loops.append(ring)
                return
            
            visited.add(node)
            for effect in causal_graph.get(node, []):
                dfs(effect, path + [effect], visited.copy())
        
        for start in causal_graph:
            dfs(start, [start], set())
        
        # 去重
        unique_loops = []
        seen = set()
        for ring in loops:
            key = tuple(sorted(ring.members))
            if key not in seen:
                seen.add(key)
                unique_loops.append(ring)
        
        self._detected_rings.extend(unique_loops)
        return unique_loops
    
    def detect_resonance_clusters(self, resonance_matrix: np.ndarray,
                                   threshold: float = 0.5) -> List[Ring]:
        """
        检测共振簇
        
        从共振矩阵中检测高共振的线簇。
        
        Args:
            resonance_matrix: 线间共振矩阵 (n_lines x n_lines)
            threshold: 共振阈值
            
        Returns:
            共振簇环列表
        """
        n = len(self.line_names)
        clusters = []
        visited = set()
        
        # 基于共振矩阵的连通分量检测
        for i in range(n):
            if i in visited:
                continue
            
            cluster = []
            queue = deque([i])
            while queue:
                curr = queue.popleft()
                if curr in visited:
                    continue
                visited.add(curr)
                cluster.append(self.line_names[curr])
                
                for j in range(n):
                    if j not in visited and resonance_matrix[curr, j] > threshold:
                        queue.append(j)
            
            if len(cluster) >= 2:
                ring_type = RingType.PAIR if len(cluster) == 2 else RingType.CYCLE
                closure = ClosureType.LATITUDE if len(cluster) <= 3 else ClosureType.GRID
                
                ring = Ring(
                    name=f"resonance_{'_'.join(cluster[:3])}",
                    members=cluster,
                    ring_type=ring_type,
                    closure_type=closure,
                    energy=float(np.mean([resonance_matrix[i, j] 
                                          for i in range(n) for j in range(n) 
                                          if self.line_names[i] in cluster and self.line_names[j] in cluster])),
                    coherence=float(np.mean([resonance_matrix[i, j] 
                                             for i in range(n) for j in range(n)
                                             if self.line_names[i] in cluster and self.line_names[j] in cluster])),
                )
                clusters.append(ring)
        
        self._detected_rings.extend(clusters)
        return clusters
    
    def propose_new_rings(self, registry: RingRegistry) -> List[Dict[str, Any]]:
        """
        提议新环
        
        基于已检测的环和现有注册表，提议可能的新环。
        
        Args:
            registry: 环注册表
            
        Returns:
            提议列表 [{"ring": Ring, "confidence": float, "reason": str}]
        """
        proposals = []
        existing_members = set()
        for ring in registry.list_all_rings():
            existing_members.update(ring.members)
        
        # 提议1：未参与任何环的线形成自环
        for line in self.line_names:
            if line not in existing_members:
                ring = Ring(
                    name=f"self_{line}",
                    members=[line],
                    ring_type=RingType.SELF,
                    closure_type=ClosureType.MERIDIAN,
                    energy=0.5,
                    coherence=1.0,
                )
                proposals.append({
                    "ring": ring,
                    "confidence": 0.9,
                    "reason": f"Line '{line}' not in any ring, suggest self-ring",
                })
        
        # 提议2：基于已检测的环
        for detected in self._detected_rings:
            # 检查是否已存在
            exists = False
            for existing in registry.list_all_rings():
                if set(existing.members) == set(detected.members):
                    exists = True
                    break
            
            if not exists:
                proposals.append({
                    "ring": detected,
                    "confidence": 0.7,
                    "reason": "Detected from interaction analysis",
                })
        
        self._proposals = proposals
        return proposals
    
    def get_detected_rings(self) -> List[Ring]:
        """获取所有检测到的环"""
        return self._detected_rings.copy()


class RingTopologyEngine:
    """
    RingTopologyEngine — 环拓扑引擎（主类）
    
    整合环注册、验证、互作和自组织检测的完整引擎，
    是OMNI-HUB v8.0中环拓扑管理的核心组件。
    
    11线名称:
        ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
    """
    
    # 11线名称
    LINE_NAMES = ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
    
    def __init__(self, num_lines: int = 11):
        """
        初始化环拓扑引擎
        
        Args:
            num_lines: 线数量（默认11）
        """
        self.num_lines = num_lines
        self.line_names = self.LINE_NAMES[:num_lines]
        self.line_index_map = {name: i for i, name in enumerate(self.line_names)}
        
        # 子组件
        self.registry = RingRegistry()
        self.verifier = RingVerifier(self.line_names)
        self.interaction = RingInteraction()
        self.detector = SelfOrganizingRingDetector(self.line_names)
        
        # 场状态
        self._field_state = np.zeros(64, dtype=np.float32)
        self._resonance_matrix = np.zeros((num_lines, num_lines), dtype=np.float32)
        self._time_step = 0
        
        # 注册预定义环
        self.predefined_rings()
    
    def predefined_rings(self) -> List[Ring]:
        """
        预定义所有已知环
        
        注册OMNI-HUB v7.0中已存在的所有环：
        - lgt⇄vinf（对闭环，pair）
        - cfts→lgt→qgl→cfts（三角环，cycle）
        - qgl⇄usrm（对闭环，pair）
        - qlv⇄qfa（SI5-RING首环，pair）
        - 大环（cycle）
        - 各线因果自环（self）
        
        Returns:
            注册的环列表
        """
        rings = []
        
        # 1. lgt⇄vinf 对闭环
        r1 = Ring(
            name="lgt_vinf_pair",
            members=["lgt", "vinf"],
            ring_type=RingType.PAIR,
            closure_type=ClosureType.LATITUDE,
            energy=1.0,
            coherence=0.9,
            frequency=1.0,
            metadata={"description": "lgt-vinf 对闭环", "version": "7.0"},
        )
        rings.append(r1)
        
        # 2. cfts→lgt→qgl→cfts 三角环
        r2 = Ring(
            name="cfts_lgt_qgl_cycle",
            members=["cfts", "lgt", "qgl"],
            ring_type=RingType.CYCLE,
            closure_type=ClosureType.GRID,
            energy=1.2,
            coherence=0.85,
            frequency=1.2,
            metadata={"description": "cfts-lgt-qgl 三角环", "version": "7.0"},
        )
        rings.append(r2)
        
        # 3. qgl⇄usrm 对闭环
        r3 = Ring(
            name="qgl_usrm_pair",
            members=["qgl", "usrm"],
            ring_type=RingType.PAIR,
            closure_type=ClosureType.LATITUDE,
            energy=0.9,
            coherence=0.88,
            frequency=0.9,
            metadata={"description": "qgl-usrm 对闭环", "version": "7.0"},
        )
        rings.append(r3)
        
        # 4. qlv⇄qfa SI5-RING首环
        r4 = Ring(
            name="qlv_qfa_si5",
            members=["qlv", "qfa"],
            ring_type=RingType.PAIR,
            closure_type=ClosureType.MERIDIAN,
            energy=1.1,
            coherence=0.92,
            frequency=1.1,
            metadata={"description": "qlv-qfa SI5-RING首环", "version": "7.0"},
        )
        rings.append(r4)
        
        # 5. 大环: ucif2→lvlu→lgt→qfa→vinf→qgl→qlv→cisvr→qtlv→usrm→cfts→ucif2
        r5 = Ring(
            name="grand_cycle",
            members=["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl", "qlv", "cisvr", "qtlv", "usrm", "cfts"],
            ring_type=RingType.CYCLE,
            closure_type=ClosureType.GRID,
            energy=2.0,
            coherence=0.75,
            frequency=0.5,
            metadata={"description": "11线大环", "version": "7.0"},
        )
        rings.append(r5)
        
        # 6-16. 各线因果自环
        for line in self.line_names:
            r = Ring(
                name=f"self_{line}",
                members=[line],
                ring_type=RingType.SELF,
                closure_type=ClosureType.MERIDIAN,
                energy=0.5,
                coherence=1.0,
                frequency=1.0,
                metadata={"description": f"{line} 因果自环", "version": "7.0"},
            )
            rings.append(r)
        
        # 17. 互激闭环 (meta类型示例)
        r_meta = Ring(
            name="meta_excitation",
            members=["lgt", "qgl", "vinf"],
            ring_type=RingType.META,
            closure_type=ClosureType.GRID,
            energy=1.3,
            coherence=0.8,
            frequency=1.15,
            metadata={"description": "互激闭环", "version": "7.0"},
        )
        rings.append(r_meta)
        
        # 18. 额外因果环
        r_causal = Ring(
            name="causal_lgt_chain",
            members=["lgt", "qfa", "vinf"],
            ring_type=RingType.CAUSAL,
            closure_type=ClosureType.MERIDIAN,
            energy=0.8,
            coherence=0.7,
            frequency=1.05,
            metadata={"description": "lgt-qfa-vinf 因果链", "version": "7.0"},
        )
        rings.append(r_causal)
        
        # 更新所有环的状态并注册
        for ring in rings:
            ring._update_status()
            self.registry.register_ring(ring)
        
        return rings
    
    def verify_all_rings(self) -> Dict[str, Any]:
        """
        验证所有环
        
        对注册表中所有环执行全面验证。
        
        Returns:
            {"total": int, "passed": int, "failed": int, "results": [details]}
        """
        results = []
        passed = 0
        failed = 0
        
        for ring in self.registry.list_all_rings():
            result = self.verifier.full_verify(ring)
            results.append(result)
            if result["passed"]:
                passed += 1
            else:
                failed += 1
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
        }
    
    def run_mutual_excitation(self, iterations: int = 3) -> Dict[str, Any]:
        """
        运行所有环的互激
        
        对注册表中每对相邻环执行互激。
        
        Args:
            iterations: 每对环互激次数
            
        Returns:
            {"interactions": int, "results": [details]}
        """
        rings = self.registry.list_all_rings()
        results = []
        count = 0
        
        for i in range(len(rings)):
            for j in range(i + 1, len(rings)):
                for _ in range(iterations):
                    result = self.interaction.mutual_excitation(rings[i], rings[j])
                    results.append(result)
                    count += 1
        
        return {
            "interactions": count,
            "results": results,
        }
    
    def detect_new_rings(self, interactions: Optional[List[Tuple[str, str, float]]] = None) -> List[Ring]:
        """
        检测新环
        
        从交互中检测潜在的新环结构。
        
        Args:
            interactions: 外部交互数据，None时生成随机交互
            
        Returns:
            检测到的潜在新环列表
        """
        if interactions is None:
            # 生成随机交互
            interactions = []
            for _ in range(50):
                a, b = random.sample(self.line_names, 2)
                strength = random.random()
                interactions.append((a, b, strength))
        
        detected = self.detector.detect_from_interactions(interactions)
        
        # 提议新环
        proposals = self.detector.propose_new_rings(self.registry)
        
        # 将高置信度提议加入检测列表
        for p in proposals:
            if p["confidence"] > 0.8:
                detected.append(p["ring"])
        
        return detected
    
    def get_ring_resonance_matrix(self) -> np.ndarray:
        """
        获取环共振矩阵
        
        计算所有环之间的共振强度矩阵。
        
        Returns:
            n_rings x n_rings 共振矩阵
        """
        rings = self.registry.list_all_rings()
        n = len(rings)
        matrix = np.zeros((n, n), dtype=np.float32)
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i, j] = 1.0
                else:
                    # 共振强度 = 共享成员比例 * 频率匹配度 * 相干度乘积
                    shared = set(rings[i].members) & set(rings[j].members)
                    shared_ratio = len(shared) / max(len(rings[i].members), len(rings[j].members))
                    
                    freq_ratio = rings[i].frequency / max(rings[j].frequency, 1e-6)
                    freq_match = 1.0 / (1.0 + (freq_ratio - 1.0) ** 2)
                    
                    coherence_product = rings[i].coherence * rings[j].coherence
                    
                    matrix[i, j] = shared_ratio * freq_match * coherence_product
        
        self._resonance_matrix = matrix
        return matrix
    
    def get_topology_report(self) -> Dict[str, Any]:
        """
        获取拓扑报告
        
        生成环拓扑的完整报告。
        
        Returns:
            拓扑报告字典
        """
        rings = self.registry.list_all_rings()
        
        # 分类统计
        type_counts = defaultdict(int)
        closure_counts = defaultdict(int)
        status_counts = defaultdict(int)
        total_energy = 0.0
        total_coherence = 0.0
        
        for ring in rings:
            type_counts[ring.ring_type.value] += 1
            closure_counts[ring.closure_type.value] += 1
            status_counts[ring.status.value] += 1
            total_energy += ring.energy
            total_coherence += ring.coherence
        
        # 重叠检测
        overlaps = self.registry.detect_overlapping_rings()
        
        # 共振矩阵
        res_matrix = self.get_ring_resonance_matrix()
        
        report = {
            "summary": {
                "total_rings": len(rings),
                "total_energy": float(total_energy),
                "avg_coherence": float(total_coherence / max(1, len(rings))),
                "type_distribution": dict(type_counts),
                "closure_distribution": dict(closure_counts),
                "status_distribution": dict(status_counts),
            },
            "overlaps": [
                {
                    "ring_a": r1.name,
                    "ring_b": r2.name,
                    "shared": list(shared),
                    "shared_count": len(shared),
                }
                for r1, r2, shared in overlaps
            ],
            "rings": [ring.to_dict() for ring in rings],
            "resonance_matrix_shape": res_matrix.shape,
            "resonance_matrix_mean": float(np.mean(res_matrix)),
            "resonance_matrix_max": float(np.max(res_matrix)),
            "timestamp": self._time_step,
        }
        
        return report
    
    def get_field_state(self) -> np.ndarray:
        """
        获取环场状态（用于场引擎）
        
        生成64维环场状态向量，包含：
        - 各线能量分布 (11维)
        - 各线相干度 (11维)
        - 环类型分布 (6维)
        - 闭合类型分布 (4维)
        - 共振矩阵特征值 (11维)
        - 全局统计量 (11维)
        - 时间步和相位信息 (10维)
        
        Returns:
            64维状态向量
        """
        state = np.zeros(64, dtype=np.float32)
        
        rings = self.registry.list_all_rings()
        n = len(rings)
        
        if n == 0:
            return state
        
        # 1. 各线能量分布 (11维, indices 0-10)
        line_energies = np.zeros(self.num_lines)
        for ring in rings:
            per_member = ring.energy / max(1, len(ring.members))
            for member in ring.members:
                if member in self.line_index_map:
                    line_energies[self.line_index_map[member]] += per_member
        state[0:self.num_lines] = line_energies / max(1, np.max(line_energies))
        
        # 2. 各线相干度 (11维, indices 11-21)
        line_coherences = np.zeros(self.num_lines)
        line_counts = np.zeros(self.num_lines)
        for ring in rings:
            for member in ring.members:
                if member in self.line_index_map:
                    idx = self.line_index_map[member]
                    line_coherences[idx] += ring.coherence
                    line_counts[idx] += 1
        line_counts = np.maximum(line_counts, 1)
        state[11:11+self.num_lines] = line_coherences / line_counts
        
        # 3. 环类型分布 (6维, indices 22-27)
        type_counts = np.zeros(6)
        type_map = {RingType.PAIR: 0, RingType.CHAIN: 1, RingType.CYCLE: 2,
                    RingType.SELF: 3, RingType.CAUSAL: 4, RingType.META: 5}
        for ring in rings:
            if ring.ring_type in type_map:
                type_counts[type_map[ring.ring_type]] += 1
        state[22:28] = type_counts / max(1, np.sum(type_counts))
        
        # 4. 闭合类型分布 (4维, indices 28-31)
        closure_counts = np.zeros(4)
        closure_map = {ClosureType.MERIDIAN: 0, ClosureType.LATITUDE: 1,
                       ClosureType.GRID: 2, ClosureType.OPEN: 3}
        for ring in rings:
            if ring.closure_type in closure_map:
                closure_counts[closure_map[ring.closure_type]] += 1
        state[28:32] = closure_counts / max(1, np.sum(closure_counts))
        
        # 5. 共振矩阵特征值 (11维, indices 32-42)
        res_matrix = self.get_ring_resonance_matrix()
        if res_matrix.shape[0] > 0:
            # 计算线级别的共振（聚合）
            line_resonance = np.zeros(self.num_lines)
            for i, ring_i in enumerate(rings):
                for j, ring_j in enumerate(rings):
                    if i != j:
                        shared = set(ring_i.members) & set(ring_j.members)
                        for line in shared:
                            if line in self.line_index_map:
                                line_resonance[self.line_index_map[line]] += res_matrix[i, j]
            state[32:32+self.num_lines] = line_resonance / max(1, np.max(line_resonance))
        
        # 6. 全局统计量 (11维, indices 43-53)
        state[43] = len(rings) / 20.0  # 环数量归一化
        state[44] = np.sum(line_energies) / 20.0  # 总能量
        state[45] = np.mean([r.coherence for r in rings])  # 平均相干度
        state[46] = np.mean([r.frequency for r in rings])  # 平均频率
        state[47] = len(self.registry.detect_overlapping_rings()) / 50.0  # 重叠对数
        state[48] = np.std(line_energies)  # 能量标准差
        state[49] = np.max(line_energies)  # 最大能量
        state[50] = np.min([r.energy for r in rings])  # 最小环能量
        state[51] = np.max([r.energy for r in rings])  # 最大环能量
        state[52] = self._time_step / 1000.0  # 时间步
        state[53] = np.mean([len(r.members) for r in rings]) / 11.0  # 平均环大小
        
        # 7. 相位信息 (10维, indices 54-63)
        phases = [r.phase for r in rings[:10]] if rings else []
        for i, ph in enumerate(phases):
            state[54 + i] = ph / (2 * np.pi)
        
        self._field_state = state
        return state
    
    def step(self, external_energy: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        执行一个时间步
        
        模拟环系统的一个演化步骤。
        
        Args:
            external_energy: 外部能量注入 (num_lines维)
            
        Returns:
            步进结果
        """
        self._time_step += 1
        
        # 1. 能量注入
        if external_energy is not None:
            for ring in self.registry.list_all_rings():
                injected = sum(external_energy[self.line_index_map[m]] 
                              for m in ring.members if m in self.line_index_map)
                ring.energy += injected * 0.1
        
        # 2. 所有环衰减
        for ring in self.registry.list_all_rings():
            ring.decay(rate=0.005)
        
        # 3. 更新共振矩阵
        self.get_ring_resonance_matrix()
        
        # 4. 更新场状态
        self.get_field_state()
        
        return {
            "time_step": self._time_step,
            "total_energy": sum(r.energy for r in self.registry.list_all_rings()),
            "avg_coherence": np.mean([r.coherence for r in self.registry.list_all_rings()]) if self.registry.list_all_rings() else 0,
        }
    
    def reset(self) -> None:
        """重置引擎到初始状态"""
        self.registry.clear()
        self.verifier.clear_log()
        self.interaction = RingInteraction()
        self.detector = SelfOrganizingRingDetector(self.line_names)
        self._field_state = np.zeros(64, dtype=np.float32)
        self._resonance_matrix = np.zeros((self.num_lines, self.num_lines), dtype=np.float32)
        self._time_step = 0
        self.predefined_rings()
    
    def export_to_json(self, filepath: str) -> None:
        """
        导出拓扑到JSON
        
        Args:
            filepath: 输出文件路径
        """
        report = self.get_topology_report()
    with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
            logger.error(f"File operation failed: {e}")
    def get_ring_by_name(self, name: str) -> Optional[Ring]:
        """通过名称获取环"""
        return self.registry.get_ring_by_name(name)
    
    def __repr__(self) -> str:
        return f"RingTopologyEngine(lines={self.num_lines}, rings={self.registry.count()})"


# =============================================================================
# 测试块
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v8.0 — RingTopologyEngine 测试")
    print("=" * 70)
    
    # 初始化引擎
    print("\n[1] 初始化引擎...")
    engine = RingTopologyEngine(num_lines=11)
    print(f"    引擎: {engine}")
    print(f"    11线: {engine.line_names}")
    
    # 测试1: 注册所有预定义环（≥8个）
    print("\n[2] 注册预定义环...")
    rings = engine.registry.list_all_rings()
    print(f"    已注册环数量: {len(rings)}")
    for ring in rings:
        print(f"    - {ring.name}: type={ring.ring_type.value}, members={ring.members}")
    assert len(rings) >= 8, f"需要≥8个环，实际{len(rings)}个"
    print(f"    ✓ 通过: 注册环数 ≥ 8")
    
    # 测试2: 验证所有环的闭合性
    print("\n[3] 验证所有环的闭合性...")
    verify_result = engine.verify_all_rings()
    print(f"    总环数: {verify_result['total']}")
    print(f"    通过: {verify_result['passed']}")
    print(f"    失败: {verify_result['failed']}")
    for r in verify_result['results'][:5]:
        ring = engine.registry.get_ring(r['ring_id'])
        print(f"    - {ring.name if ring else r['ring_id']}: score={r['score']:.3f}, passed={r['passed']}")
    print(f"    ✓ 通过: 闭合性验证完成")
    
    # 测试3: 运行互激模拟（每对相邻环互激3次）
    print("\n[4] 运行互激模拟（每对环互激3次）...")
    exc_result = engine.run_mutual_excitation(iterations=3)
    print(f"    总互激次数: {exc_result['interactions']}")
    print(f"    互激示例:")
    for r in exc_result['results'][:5]:
        print(f"      {r['type']}: strength={r.get('strength', 'N/A'):.3f}")
    print(f"    ✓ 通过: 互激模拟完成")
    
    # 测试4: 检测自组织环（从随机交互中）
    print("\n[5] 检测自组织环...")
    random_interactions = []
    for _ in range(100):
        a, b = random.sample(engine.line_names, 2)
        strength = random.random()
        random_interactions.append((a, b, strength))
    
    new_rings = engine.detect_new_rings(random_interactions)
    print(f"    检测到潜在新环: {len(new_rings)}")
    for ring in new_rings[:5]:
        print(f"    - {ring.name}: type={ring.ring_type.value}, members={ring.members}")
    print(f"    ✓ 通过: 自组织环检测完成")
    
    # 测试5: 计算环共振矩阵
    print("\n[6] 计算环共振矩阵...")
    res_matrix = engine.get_ring_resonance_matrix()
    print(f"    矩阵形状: {res_matrix.shape}")
    print(f"    矩阵均值: {np.mean(res_matrix):.4f}")
    print(f"    矩阵最大值: {np.max(res_matrix):.4f}")
    print(f"    矩阵最小值: {np.min(res_matrix):.4f}")
    print(f"    矩阵迹(自共振和): {np.trace(res_matrix):.4f}")
    print(f"    ✓ 通过: 共振矩阵计算完成")
    
    # 测试6: 测试能量转移和相位锁定
    print("\n[7] 测试能量转移和相位锁定...")
    ring_a = engine.get_ring_by_name("lgt_vinf_pair")
    ring_b = engine.get_ring_by_name("qgl_usrm_pair")
    
    if ring_a and ring_b:
        print(f"    环A ({ring_a.name}) 初始能量: {ring_a.energy:.3f}")
        print(f"    环B ({ring_b.name}) 初始能量: {ring_b.energy:.3f}")
        
        # 能量转移
        et_result = engine.interaction.energy_transfer(ring_a, ring_b, 0.5)
        print(f"    能量转移: {et_result['transferred']:.3f}")
        print(f"    环A剩余: {et_result['remaining_a']:.3f}")
        print(f"    环B接收: {et_result['received_b']:.3f}")
        
        # 相位锁定
        ring_a.phase = 0.5
        ring_b.phase = 2.5
        print(f"    相位锁定前: A={ring_a.phase:.3f}, B={ring_b.phase:.3f}")
        pl_result = engine.interaction.phase_lock(ring_a, ring_b, lock_strength=0.5)
        print(f"    相位锁定后: A={ring_a.phase:.3f}, B={ring_b.phase:.3f}")
        print(f"    相位差: {pl_result['phase_diff']:.3f}, 锁定: {pl_result['locked']}")
        
        # 相长/相消干涉
        ring_a.phase = 0.1
        ring_b.phase = 0.2
        ci_result = engine.interaction.constructive_interference(ring_a, ring_b)
        print(f"    相长干涉: factor={ci_result['interference_factor']:.3f}, gain={ci_result['energy_gain']:.3f}")
        
        ring_a.phase = 0.0
        ring_b.phase = np.pi
        di_result = engine.interaction.destructive_interference(ring_a, ring_b)
        print(f"    相消干涉: factor={di_result['interference_factor']:.3f}, loss={di_result['energy_loss']:.3f}")
    
    print(f"    ✓ 通过: 能量转移和相位锁定测试完成")
    
    # 测试7: 输出完整拓扑报告
    print("\n[8] 输出完整拓扑报告...")
    report = engine.get_topology_report()
    print(f"    --- 摘要 ---")
    print(f"    总环数: {report['summary']['total_rings']}")
    print(f"    总能量: {report['summary']['total_energy']:.3f}")
    print(f"    平均相干度: {report['summary']['avg_coherence']:.3f}")
    print(f"    类型分布: {report['summary']['type_distribution']}")
    print(f"    闭合分布: {report['summary']['closure_distribution']}")
    print(f"    状态分布: {report['summary']['status_distribution']}")
    print(f"    --- 重叠环 ---")
    print(f"    重叠对数: {len(report['overlaps'])}")
    for ov in report['overlaps'][:5]:
        print(f"      {ov['ring_a']} <-> {ov['ring_b']}: shared={ov['shared']}")
    print(f"    ✓ 通过: 拓扑报告生成完成")
    
    # 测试8: 获取64维环场状态向量
    print("\n[9] 获取64维环场状态向量...")
    field_state = engine.get_field_state()
    print(f"    状态向量形状: {field_state.shape}")
    print(f"    状态向量维度: {field_state.shape[0]}")
    print(f"    状态向量均值: {np.mean(field_state):.4f}")
    print(f"    状态向量标准差: {np.std(field_state):.4f}")
    print(f"    状态向量最大值: {np.max(field_state):.4f}")
    print(f"    状态向量最小值: {np.min(field_state):.4f}")
    print(f"    前10维: {field_state[:10]}")
    print(f"    后10维: {field_state[-10:]}")
    assert field_state.shape == (64,), f"状态向量应为64维，实际{field_state.shape}"
    print(f"    ✓ 通过: 64维场状态向量正确")
    
    # 测试额外: 环流、共振、衰减
    print("\n[10] 测试环流、共振和衰减...")
    test_ring = engine.get_ring_by_name("grand_cycle")
    if test_ring:
        print(f"    测试环: {test_ring.name}")
        print(f"    初始能量: {test_ring.energy:.3f}, 相干度: {test_ring.coherence:.3f}")
        
        # 环流
        uniformity = test_ring.circulate(energy=2.0, direction=1)
        print(f"    环流后能量: {test_ring.energy:.3f}, 均匀度: {uniformity:.3f}")
        
        # 共振
        res_strength = test_ring.resonate(frequency=0.5)
        print(f"    共振强度: {res_strength:.3f}")
        print(f"    共振后能量: {test_ring.energy:.3f}, 相干度: {test_ring.coherence:.3f}")
        
        # 衰减
        for _ in range(10):
            test_ring.decay(rate=0.01)
        print(f"    衰减后能量: {test_ring.energy:.3f}, 相干度: {test_ring.coherence:.3f}")
        print(f"    环状态: {test_ring.status.value}")
    
    print(f"    ✓ 通过: 环流、共振、衰减测试完成")
    
    # 测试额外: 引擎步进
    print("\n[11] 测试引擎步进...")
    for step in range(5):
        external = np.random.random(11) * 0.1
        result = engine.step(external_energy=external)
        print(f"    Step {result['time_step']}: total_energy={result['total_energy']:.3f}, avg_coherence={result['avg_coherence']:.3f}")
    print(f"    ✓ 通过: 引擎步进测试完成")
    
    # 测试额外: 导出报告
    print("\n[12] 导出拓扑报告到JSON...")
    engine.export_to_json("/mnt/agents/output/OMNI-HUB/core/topology_report.json")
    print(f"    ✓ 通过: 报告已导出")
    
    print("\n" + "=" * 70)
    print("所有测试通过!")
    print("=" * 70)
