#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
OMNI-HUB v3.8 — 毂-轮-脊-鼎-塔-环 六元元结构系统
Meta-Structure: Gu-Wheel-Spine-Ding-Tower-Ring (GWS-DTR)
================================================================================

六元定义:
  毂(Gu)    : 核心自指机 — 元控制中心
  轮(Wheel) : 递归循环 — 迭代引擎
  脊(Spine) : 知识谱系 — 纵向传承链
  鼎(Ding)  : 共识熔炉 — 多源决议合成
  塔(Tower) : 扫描瞭望 — 递归自观测
  环(Ring)  : 闭环契约 — 强制执行契约

与现有系统映射:
  层-圈-环-网-云 ↔ 毂-轮-脊-鼎-塔-环
  经-纬-薪      ↔ 脊-轮-鼎
  张量-链       ↔ 轮-环-塔

Author: OMNI-HUB Meta-Architecture Division
Version: v3.8-SI5.0
================================================================================
"""

__version__ = "11.0.0"
from __future__ import annotations

import hashlib
import json
import math
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# =============================================================================
# SECTION 0: Constants & Global Configuration
# =============================================================================

LINES = ['ucif2', 'lgt', 'qfa', 'usrm', 'vinf', 'qgl', 'qlv', 'lvlu', 'cfts', 'cisvr', 'qtlv']
META_NAMES = ['Gu', 'Wheel', 'Spine', 'Ding', 'Tower', 'Ring']
META_SYMBOLS = {
    'Gu': '毂',
    'Wheel': '轮',
    'Spine': '脊',
    'Ding': '鼎',
    'Tower': '塔',
    'Ring': '环'
}

# 层-圈-环-网-云 ↔ 六元 映射
LEGACY_TO_META = {
    'layer':  'Gu',      # 层 → 毂 (控制中心)
    'circle': 'Ding',    # 圈 → 鼎 (共识圈)
    'ring':   'Ring',    # 环 → 环 (闭环)
    'net':    'Wheel',   # 网 → 轮 (递归网)
    'cloud':  'Tower',   # 云 → 塔 (瞭望云)
}

META_TO_LEGACY = {v: k for k, v in LEGACY_TO_META.items()}
META_TO_LEGACY['Spine'] = 'layer'  # 脊也映射到层(纵向)

# 经-纬-薪 映射
JING_WEI_XIN = {
    'jing': 'Spine',    # 经 → 脊 (纵向传承)
    'wei':  'Wheel',    # 纬 → 轮 (横向循环)
    'xin':  'Ding',     # 薪 → 鼎 (共识燃料)
}

# 张量-链 流转映射
TENSOR_CHAIN_FLOW = {
    'tensor_field': ['Wheel', 'Ring', 'Tower'],   # 张量场流转路径
    'chain_hash':   ['Ring', 'Spine', 'Gu'],      # 链式哈希流转路径
    'contraction':  ['Tower', 'Ding', 'Wheel'],   # 收缩操作流转路径
}


# =============================================================================
# SECTION 1: Core Data Types
# =============================================================================

class MetaState(Enum):
    """六元状态枚举"""
    DORMANT = auto()      # 休眠
    INITIALIZING = auto() # 初始化中
    ACTIVE = auto()       # 活跃
    PROCESSING = auto()   # 处理中
    REINFORCING = auto()  # 自我强化中
    STABILIZING = auto()  # 稳定化
    DEGRADED = auto()     # 降级
    CRITICAL = auto()     # 临界


class MetaRole(Enum):
    """六元在交互中的角色"""
    CONTROLLER = auto()   # 控制器 (Gu)
    ITERATOR = auto()     # 迭代器 (Wheel)
    ARCHIVIST = auto()    # 档案员 (Spine)
    ARBITER = auto()      # 仲裁者 (Ding)
    OBSERVER = auto()     # 观测者 (Tower)
    ENFORCER = auto()     # 执行者 (Ring)


class FlowType(Enum):
    """流类型"""
    INFORMATION = auto()  # 信息流
    ENERGY = auto()       # 能量流
    CONTROL = auto()      # 控制流
    FEEDBACK = auto()     # 反馈流
    RESONANCE = auto()    # 共振流


@dataclass
class MetaPacket:
    """六元间传输的数据包"""
    packet_id: str
    source: str           # 源元名称
    target: str           # 目标元名称
    flow_type: FlowType
    payload: Dict[str, Any]
    timestamp: float
    priority: float = 1.0
    ttl: int = 10         # 生存时间(跳数)
    signature: Optional[str] = None

    def compute_signature(self) -> str:
        data = f"{self.source}:{self.target}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def sign(self):
        self.signature = self.compute_signature()


@dataclass  
class CouplingChannel:
    """耦合通道 — 两个元之间的连接"""
    source: str
    target: str
    weight: float = 0.5           # 耦合权重 [0, 1]
    info_bandwidth: float = 1.0   # 信息带宽
    energy_bandwidth: float = 1.0 # 能量带宽
    latency: float = 0.01         # 延迟(秒)
    reliability: float = 0.95     # 可靠性
    last_activity: float = 0.0
    packet_count: int = 0

    def compute_capacity(self) -> float:
        """计算通道容量 = 带宽 × 可靠性 / (1 + 延迟)"""
        return (self.info_bandwidth * self.reliability) / (1.0 + self.latency)

    def transfer_efficiency(self) -> float:
        """传输效率"""
        return self.weight * self.reliability * math.exp(-self.latency)


@dataclass
class SpinState:
    """Spin状态 — 轮的核心数据结构"""
    spin_id: str
    iteration: int = 0
    depth: int = 0
    max_depth: int = 16
    energy: float = 1.0
    phase: float = 0.0          # 相位 [0, 2π]
    recursion_stack: List[Dict] = field(default_factory=list)
    is_self_referential: bool = False

    def advance(self) -> 'SpinState':
        """推进spin状态"""
        self.iteration += 1
        self.phase = (self.phase + 2 * math.pi / 16) % (2 * math.pi)
        self.energy *= 0.98  # 能量衰减
        return self

    def clone_for_recursion(self) -> 'SpinState':
        """为递归创建副本"""
        return SpinState(
            spin_id=f"{self.spin_id}_r{self.depth+1}",
            iteration=self.iteration,
            depth=self.depth + 1,
            max_depth=self.max_depth,
            energy=self.energy * 0.9,
            phase=self.phase,
            recursion_stack=list(self.recursion_stack),
            is_self_referential=True
        )


@dataclass
class KnowledgeNode:
    """知识节点 — 脊的核心数据结构"""
    node_id: str
    generation: int = 0         # 代际
    content: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    lineage_score: float = 0.0  # 谱系分数
    durability: float = 1.0     # 耐久度

    def spawn_child(self, content: Dict[str, Any]) -> 'KnowledgeNode':
        """产生子代知识节点"""
        child = KnowledgeNode(
            node_id=f"KN-{uuid.uuid4().hex[:8].upper()}",
            generation=self.generation + 1,
            content=content,
            parent_id=self.node_id,
            timestamp=time.time(),
            lineage_score=self.lineage_score * 0.95 + 0.05,
            durability=self.durability * 0.98
        )
        self.children_ids.append(child.node_id)
        return child


@dataclass
class ConsensusShard:
    """共识碎片 — 鼎的核心数据结构"""
    shard_id: str
    source_lines: List[str] = field(default_factory=list)
    vote_data: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    timestamp: float = 0.0
    finalized: bool = False
    hash_digest: Optional[str] = None

    def finalize(self) -> bool:
        """固化共识碎片"""
        if self.finalized:
            return False
        data = json.dumps({
            'source_lines': sorted(self.source_lines),
            'vote_data': self.vote_data,
            'weight': self.weight,
            'timestamp': self.timestamp
        }, sort_keys=True)
        self.hash_digest = hashlib.sha256(data.encode()).hexdigest()[:16]
        self.finalized = True
        return True


@dataclass
class ObservationFrame:
    """观测帧 — 塔的核心数据结构"""
    frame_id: str
    observer_level: int = 0     # 观测层级 (0=自观测, 1=元观测, 2=元元观测...)
    target_meta: str = ''
    metrics: Dict[str, float] = field(default_factory=dict)
    prediction: Optional[Dict] = None
    timestamp: float = 0.0
    confidence: float = 0.0

    def meta_observe(self, target: str) -> 'ObservationFrame':
        """对观测本身进行观测 (元观测)"""
        return ObservationFrame(
            frame_id=f"OF-meta-{uuid.uuid4().hex[:6]}",
            observer_level=self.observer_level + 1,
            target_meta=target,
            metrics={
                'observation_of': self.frame_id,
                'observer_level': self.observer_level,
                'confidence_degradation': self.confidence * 0.9
            },
            timestamp=time.time(),
            confidence=self.confidence * 0.9
        )


@dataclass
class ContractLink:
    """契约链接 — 环的核心数据结构"""
    link_id: str
    contract_type: str        # 'N-MUST', 'M-CODE', 'DELTA-BASE'
    binding: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    violation_count: int = 0
    repair_attempts: int = 0
    created_at: float = 0.0
    last_checked: float = 0.0
    chain_prev: Optional[str] = None
    chain_hash: Optional[str] = None

    def compute_chain_hash(self, prev_hash: Optional[str] = None) -> str:
        data = f"{self.link_id}:{self.contract_type}:{self.created_at}:{prev_hash or '0'*16}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def bind_chain(self, prev_link: Optional['ContractLink'] = None):
        self.chain_prev = prev_link.link_id if prev_link else None
        self.chain_hash = self.compute_chain_hash(prev_link.chain_hash if prev_link else None)


# =============================================================================
# SECTION 2: Six Meta Elements
# =============================================================================

class GuMeta:
    """
    毂(Gu) — 核心自指机 / 元控制中心

    职责:
    - 持有系统全局自描述
    - 协调六元之间的交互
    - 自指循环: Gu描述Gu描述Gu...
    - 全局状态监控与调度
    """

    def __init__(self):
        self.name = 'Gu'
        self.symbol = '毂'
        self.role = MetaRole.CONTROLLER
        self.state = MetaState.INITIALIZING

        # 全局自描述
        self.self_description: Dict[str, Any] = {
            'system': 'OMNI-HUB',
            'version': 'v3.8',
            'si_level': 5.0,
            'meta_structure': 'Gu-Wheel-Spine-Ding-Tower-Ring',
            'self_reference_depth': 0,
        }

        # 六元注册表
        self.meta_registry: Dict[str, Any] = {}

        # 全局状态向量
        self.global_state = np.zeros(6)

        # 自指栈
        self.self_ref_stack: List[Dict] = []
        self.max_self_ref_depth = 8

        # 调度队列
        self.schedule_queue: deque = deque()

        # 活动日志
        self.activity_log: List[Dict] = []

        self._lock = threading.RLock()
        self._initialized_at = time.time()

    def describe_self(self, depth: int = 0) -> Dict[str, Any]:
        """自描述 — 核心自指功能"""
        if depth > self.max_self_ref_depth:
            return {"error": "max_self_reference_depth_reached", "depth": depth}

        desc = {
            "meta": self.name,
            "symbol": self.symbol,
            "role": self.role.name,
            "state": self.state.name,
            "self_description_of": f"Gu_at_depth_{depth}",
            "timestamp": time.time(),
            "registered_metas": list(self.meta_registry.keys()),
            "global_state": self.global_state.tolist(),
        }

        # 自指: Gu描述它自己的描述
        if depth < self.max_self_ref_depth:
            desc["self_ref"] = self.describe_self(depth + 1)

        self.self_ref_stack.append({"depth": depth, "timestamp": time.time()})
        if len(self.self_ref_stack) > 100:
            self.self_ref_stack = self.self_ref_stack[-50:]

        return desc

    def register_meta(self, name: str, meta_ref: Any) -> bool:
        """注册一个元到毂的控制中心"""
        with self._lock:
            self.meta_registry[name] = {
                'ref': meta_ref,
                'registered_at': time.time(),
                'status': 'active'
            }
            self._log_activity('REGISTER', name)
        return True

    def update_global_state(self, meta_states: Dict[str, float]):
        """更新全局状态向量"""
        for i, name in enumerate(META_NAMES):
            if name in meta_states:
                self.global_state[i] = meta_states[name]

    def coordinate(self, packet: MetaPacket) -> MetaPacket:
        """协调六元之间的交互 — 核心调度功能"""
        self._log_activity('COORDINATE', f"{packet.source}->{packet.target}")

        # 根据系统状态调整包的路由
        if packet.target not in self.meta_registry:
            # 目标不在注册表中，重新路由到最活跃的元
            active_meta = self._find_most_active_meta()
            packet.target = active_meta

        # 添加协调标记
        packet.payload['coordinated_by'] = self.name
        packet.payload['coordination_timestamp'] = time.time()

        return packet

    def _find_most_active_meta(self) -> str:
        """找到当前最活跃的元"""
        scores = {}
        for name, reg in self.meta_registry.items():
            if hasattr(reg['ref'], 'activity_score'):
                scores[name] = reg['ref'].activity_score
            else:
                scores[name] = 0.5
        return max(scores, key=scores.get) if scores else 'Wheel'

    def _log_activity(self, event: str, detail: str):
        self.activity_log.append({
            'timestamp': time.time(),
            'event': event,
            'detail': detail
        })

    def get_system_health(self) -> float:
        """计算系统整体健康度"""
        return float(np.mean(self.global_state))

    @property
    def activity_score(self) -> float:
        return 1.0 if self.state == MetaState.ACTIVE else 0.5


class WheelMeta:
    """
    轮(Wheel) — 递归循环 / 迭代引擎

    职责:
    - spin的自指迭代
    - 递归深度管理
    - 循环中的能量流动
    - 收敛检测
    """

    def __init__(self):
        self.name = 'Wheel'
        self.symbol = '轮'
        self.role = MetaRole.ITERATOR
        self.state = MetaState.INITIALIZING

        # 当前spin状态
        self.current_spin: Optional[SpinState] = None

        # spin历史
        self.spin_history: List[SpinState] = []

        # 递归深度限制
        self.max_recursion_depth = 16
        self.convergence_threshold = 1e-6

        # 能量池
        self.energy_pool = 1.0
        self.energy_injections: List[Dict] = []

        # 迭代统计
        self.iteration_count = 0
        self.convergence_count = 0

        # 收敛检测
        self.last_delta = float('inf')
        self.converged = False

        self._lock = threading.RLock()

    def spin(self, initial_state: Optional[Dict] = None) -> SpinState:
        """
        执行一次spin迭代

        spin算法:
        1. 初始化/更新spin状态
        2. 执行自指迭代
        3. 能量流动计算
        4. 收敛检测
        """
        with self._lock:
            if self.current_spin is None:
                self.current_spin = SpinState(
                    spin_id=f"SPIN-{uuid.uuid4().hex[:8].upper()}",
                    max_depth=self.max_recursion_depth,
                    energy=self.energy_pool
                )

            # 推进spin
            self.current_spin.advance()
            self.iteration_count += 1

            # 自指迭代: 如果当前状态满足自指条件
            if self._should_recurse():
                self._perform_recursion()

            # 能量流动
            self._energy_flow()

            # 收敛检测
            self._check_convergence()

            # 保存历史
            spin_copy = SpinState(
                spin_id=self.current_spin.spin_id,
                iteration=self.current_spin.iteration,
                depth=self.current_spin.depth,
                max_depth=self.current_spin.max_depth,
                energy=self.current_spin.energy,
                phase=self.current_spin.phase,
                is_self_referential=self.current_spin.is_self_referential
            )
            self.spin_history.append(spin_copy)
            if len(self.spin_history) > 1000:
                self.spin_history = self.spin_history[-500:]

            return self.current_spin

    def _should_recurse(self) -> bool:
        """判断是否应递归"""
        if self.current_spin.depth >= self.max_recursion_depth:
            return False
        if self.current_spin.energy < 0.1:
            return False
        # 自指条件: 每4次迭代递归一次
        return self.current_spin.iteration % 4 == 0 and self.current_spin.iteration > 0

    def _perform_recursion(self):
        """执行递归调用"""
        new_spin = self.current_spin.clone_for_recursion()
        new_spin.recursion_stack.append({
            'parent_spin': self.current_spin.spin_id,
            'parent_iteration': self.current_spin.iteration,
            'parent_depth': self.current_spin.depth
        })
        self.current_spin = new_spin

    def _energy_flow(self):
        """能量流动计算"""
        # 能量从轮流向其他元
        if self.current_spin:
            energy_decay = 0.02
            self.current_spin.energy = max(0.0, self.current_spin.energy - energy_decay)
            self.energy_pool = self.current_spin.energy

    def _check_convergence(self):
        """收敛检测"""
        if len(self.spin_history) < 2:
            return

        prev = self.spin_history[-1]
        curr = self.current_spin

        delta = abs(curr.energy - prev.energy) + abs(curr.phase - prev.phase) / (2 * math.pi)

        if delta < self.convergence_threshold:
            self.convergence_count += 1
            if self.convergence_count >= 5:
                self.converged = True
        else:
            self.convergence_count = 0
            self.converged = False

        self.last_delta = delta

    def inject_energy(self, amount: float, source: str = 'external'):
        """注入能量"""
        with self._lock:
            self.energy_pool = min(2.0, self.energy_pool + amount)
            if self.current_spin:
                self.current_spin.energy = self.energy_pool
            self.energy_injections.append({
                'amount': amount,
                'source': source,
                'timestamp': time.time()
            })

    def get_cycle_frequency(self) -> float:
        """获取当前循环频率"""
        if not self.spin_history or len(self.spin_history) < 2:
            return 0.0
        times = [s.phase for s in self.spin_history[-10:]]
        if len(times) < 2:
            return 0.0
        # 频率 = 相位变化率
        return abs(times[-1] - times[0]) / (2 * math.pi * len(times))

    @property
    def activity_score(self) -> float:
        return self.energy_pool * (1.0 if self.state == MetaState.ACTIVE else 0.3)


class SpineMeta:
    """
    脊(Spine) — 知识谱系 / 纵向传承链

    职责:
    - 知识的代际传递
    - 经验/教训的纵向累积
    - 从基底到基座的成长路径
    - 知识树的生长与修剪
    """

    def __init__(self):
        self.name = 'Spine'
        self.symbol = '脊'
        self.role = MetaRole.ARCHIVIST
        self.state = MetaState.INITIALIZING

        # 知识树根节点
        self.root_node = KnowledgeNode(
            node_id="ROOT",
            generation=0,
            content={"type": "genesis", "description": "OMNI-HUB knowledge genesis"},
            timestamp=time.time(),
            lineage_score=1.0,
            durability=1.0
        )

        # 知识节点索引
        self.knowledge_index: Dict[str, KnowledgeNode] = {"ROOT": self.root_node}

        # 代际统计
        self.generation_stats: Dict[int, Dict] = {}

        # 谱系深度
        self.max_lineage_depth = 32

        # 成长路径
        self.growth_path: List[str] = ["ROOT"]

        # 经验累积
        self.experience_pool: List[Dict] = []

        # 教训记录
        self.lesson_log: List[Dict] = []

        self._lock = threading.RLock()

    def ingest_knowledge(self, content: Dict[str, Any], 
                         parent_id: Optional[str] = None) -> KnowledgeNode:
        """摄入新知识，创建知识节点"""
        with self._lock:
            parent = self.knowledge_index.get(parent_id or "ROOT")
            if parent is None:
                parent = self.root_node

            child = parent.spawn_child(content)
            self.knowledge_index[child.node_id] = child

            # 更新成长路径
            if child.generation > len(self.growth_path) - 1:
                self.growth_path.append(child.node_id)

            # 更新代际统计
            gen = child.generation
            if gen not in self.generation_stats:
                self.generation_stats[gen] = {"count": 0, "avg_durability": 0.0}
            self.generation_stats[gen]["count"] += 1

            return child

    def query_lineage(self, node_id: str) -> List[KnowledgeNode]:
        """查询知识节点的谱系路径"""
        lineage = []
        current = self.knowledge_index.get(node_id)

        while current is not None:
            lineage.append(current)
            if current.parent_id is None or current.parent_id == current.node_id:
                break
            current = self.knowledge_index.get(current.parent_id)

        return list(reversed(lineage))

    def propagate_downward(self, node_id: str, modifier: float = 1.0) -> List[KnowledgeNode]:
        """向下传播知识 (从父到子)"""
        node = self.knowledge_index.get(node_id)
        if node is None:
            return []

        affected = []
        for child_id in node.children_ids:
            child = self.knowledge_index.get(child_id)
            if child:
                child.durability = min(1.0, child.durability + 0.05 * modifier)
                child.lineage_score = max(child.lineage_score, node.lineage_score * 0.95)
                affected.append(child)

        return affected

    def accumulate_experience(self, event: Dict[str, Any]):
        """累积经验"""
        experience = {
            'timestamp': time.time(),
            'event': event,
            'extracted_lesson': self._extract_lesson(event)
        }
        self.experience_pool.append(experience)
        if len(self.experience_pool) > 1000:
            self.experience_pool = self.experience_pool[-500:]

    def _extract_lesson(self, event: Dict) -> Dict:
        """从事件中提取教训"""
        lesson = {
            'type': event.get('type', 'unknown'),
            'outcome': event.get('outcome', 'neutral'),
            'recommendation': 'continue' if event.get('success', True) else 'adjust'
        }
        self.lesson_log.append(lesson)
        return lesson

    def get_growth_metrics(self) -> Dict:
        """获取成长指标"""
        total_nodes = len(self.knowledge_index)
        max_gen = max(self.generation_stats.keys()) if self.generation_stats else 0
        avg_durability = np.mean([n.durability for n in self.knowledge_index.values()]) if self.knowledge_index else 0.0

        return {
            'total_knowledge_nodes': total_nodes,
            'max_generation': max_gen,
            'avg_durability': float(avg_durability),
            'growth_path_length': len(self.growth_path),
            'experience_count': len(self.experience_pool),
            'lesson_count': len(self.lesson_log)
        }

    @property
    def activity_score(self) -> float:
        return len(self.knowledge_index) / 100.0 + (1.0 if self.state == MetaState.ACTIVE else 0.0)


class DingMeta:
    """
    鼎(Ding) — 共识熔炉 / 多源决议合成

    职责:
    - 多线多仓的决议合成
    - 异见融合
    - 决议的不可逆固化
    - 共识驱动的决策
    """

    def __init__(self):
        self.name = 'Ding'
        self.symbol = '鼎'
        self.role = MetaRole.ARBITER
        self.state = MetaState.INITIALIZING

        # 共识碎片池
        self.shard_pool: Dict[str, ConsensusShard] = {}

        # 已固化的决议
        self.resolutions: List[Dict] = []

        # 异见记录
        self.dissent_log: List[Dict] = []

        # 融合阈值
        self.consensus_threshold = 0.67  # 2/3多数

        # 决议计数
        self.resolution_count = 0
        self.finalization_count = 0

        # 投票权重
        self.line_weights = {line: 1.0 for line in LINES}

        self._lock = threading.RLock()

    def collect_vote(self, line: str, proposal: Dict[str, Any], 
                     vote: Any, weight: Optional[float] = None) -> ConsensusShard:
        """收集投票，创建或更新共识碎片"""
        with self._lock:
            shard_id = f"SHARD-{proposal.get('id', uuid.uuid4().hex[:8])}"

            if shard_id not in self.shard_pool:
                self.shard_pool[shard_id] = ConsensusShard(
                    shard_id=shard_id,
                    source_lines=[],
                    vote_data={},
                    timestamp=time.time()
                )

            shard = self.shard_pool[shard_id]
            shard.source_lines.append(line)
            shard.vote_data[line] = {
                'vote': vote,
                'weight': weight or self.line_weights.get(line, 1.0),
                'timestamp': time.time()
            }

            return shard

    def forge_consensus(self, shard_id: str) -> Optional[Dict]:
        """
        锻造共识 — 将碎片合成为决议

        算法:
        1. 统计加权投票
        2. 检测异见
        3. 如果达到阈值，固化决议
        4. 否则，标记为待协商
        """
        with self._lock:
            shard = self.shard_pool.get(shard_id)
            if shard is None or shard.finalized:
                return None

            # 统计投票
            votes = shard.vote_data
            total_weight = sum(v['weight'] for v in votes.values())

            # 简单多数投票 (假设vote是可哈希的)
            vote_counts = defaultdict(float)
            for line, vdata in votes.items():
                vote_key = str(vdata['vote'])
                vote_counts[vote_key] += vdata['weight']

            if not vote_counts:
                return None

            # 找出最高票
            max_vote = max(vote_counts, key=vote_counts.get)
            max_weight = vote_counts[max_vote]
            consensus_ratio = max_weight / total_weight if total_weight > 0 else 0

            # 检测异见
            dissenters = [line for line, vdata in votes.items() 
                         if str(vdata['vote']) != max_vote]

            if consensus_ratio >= self.consensus_threshold:
                # 达到共识，固化
                shard.finalize()
                self.finalization_count += 1

                resolution = {
                    'resolution_id': f"RES-{self.resolution_count:04d}",
                    'shard_id': shard_id,
                    'consensus_value': max_vote,
                    'consensus_ratio': consensus_ratio,
                    'participating_lines': list(votes.keys()),
                    'dissenters': dissenters,
                    'finalized_at': time.time(),
                    'hash': shard.hash_digest
                }
                self.resolutions.append(resolution)
                self.resolution_count += 1
                return resolution
            else:
                # 未达共识，记录异见
                self.dissent_log.append({
                    'shard_id': shard_id,
                    'consensus_ratio': consensus_ratio,
                    'needed': self.consensus_threshold,
                    'dissenters': dissenters,
                    'timestamp': time.time()
                })
                return {
                    'status': 'pending_consensus',
                    'consensus_ratio': consensus_ratio,
                    'needed': self.consensus_threshold,
                    'dissenters': dissenters
                }

    def fuse_dissent(self, shard_id: str, fusion_strategy: str = 'weighted_average') -> Dict:
        """融合异见"""
        shard = self.shard_pool.get(shard_id)
        if shard is None:
            return {'error': 'shard_not_found'}

        votes = shard.vote_data

        if fusion_strategy == 'weighted_average':
            # 加权平均融合
            total = 0.0
            weight_sum = 0.0
            for line, vdata in votes.items():
                    val = float(vdata['vote'])
                    total += val * vdata['weight']
                    weight_sum += vdata['weight']
            if weight_sum > 0:
                fused = total / weight_sum
                return {
                    'strategy': fusion_strategy,
                    'fused_value': fused,
                    'participants': len(votes)
                }

        return {'strategy': fusion_strategy, 'status': 'fusion_incomplete'}

    def get_consensus_stats(self) -> Dict:
        return {
            'total_shards': len(self.shard_pool),
            'finalized_shards': self.finalization_count,
            'total_resolutions': self.resolution_count,
            'pending_consensus': len(self.shard_pool) - self.finalization_count,
            'dissent_events': len(self.dissent_log)
        }

    @property
    def activity_score(self) -> float:
        return len(self.resolutions) / 10.0 + (1.0 if self.state == MetaState.ACTIVE else 0.0)


class TowerMeta:
    """
    塔(Tower) — 扫描瞭望 / 递归自观测

    职责:
    - OctaveScan的递归升级
    - 自观测的观测（元观测）
    - 前瞻预测
    - 多层级观测栈
    """

    def __init__(self):
        self.name = 'Tower'
        self.symbol = '塔'
        self.role = MetaRole.OBSERVER
        self.state = MetaState.INITIALIZING

        # 观测帧栈 (元观测支持)
        self.observation_stack: List[ObservationFrame] = []
        self.max_observation_level = 4

        # 扫描维度
        self.scan_dimensions = [
            'meta_health', 'coupling_strength', 'spin_stability',
            'knowledge_growth', 'consensus_quality', 'contract_integrity',
            'system_entropy', 'prediction_accuracy'
        ]

        # 扫描历史
        self.scan_history: List[Dict] = []

        # 预测模型
        self.predictions: List[Dict] = []
        self.prediction_accuracy = 0.0

        # 告警阈值
        self.alert_thresholds = {
            'meta_health': 0.5,
            'coupling_strength': 0.3,
            'spin_stability': 0.2,
            'system_entropy': 0.8
        }

        # 告警记录
        self.alerts: List[Dict] = []

        self._lock = threading.RLock()

    def observe(self, target_meta: str, metrics: Dict[str, float],
                level: int = 0) -> ObservationFrame:
        """
        执行观测

        支持元观测: Tower观测Tower观测...
        """
        with self._lock:
            frame = ObservationFrame(
                frame_id=f"OBS-{uuid.uuid4().hex[:8]}",
                observer_level=level,
                target_meta=target_meta,
                metrics=metrics,
                timestamp=time.time(),
                confidence=self._compute_confidence(metrics)
            )

            self.observation_stack.append(frame)
            if len(self.observation_stack) > 500:
                self.observation_stack = self.observation_stack[-250:]

            # 检查告警
            self._check_alerts(frame)

            return frame

    def meta_observe(self, target_level: int = 1) -> ObservationFrame:
        """元观测 — 对观测本身进行观测"""
        if not self.observation_stack:
            return ObservationFrame(
                frame_id=f"META-OBS-empty",
                observer_level=target_level,
                target_meta='Tower',
                metrics={'error': 'no_observations'},
                timestamp=time.time(),
                confidence=0.0
            )

        last_obs = self.observation_stack[-1]
        meta_frame = last_obs.meta_observe('Tower')
        meta_frame.observer_level = target_level

        # 元观测的置信度衰减
        meta_frame.confidence *= (0.8 ** target_level)

        self.observation_stack.append(meta_frame)
        return meta_frame

    def scan_all(self, meta_states: Dict[str, Dict[str, float]]) -> Dict:
        """全维度扫描"""
        scan_result = {
            'timestamp': time.time(),
            'dimensions': {},
            'overall_score': 0.0,
            'alerts': []
        }

        # 扫描每个维度
        for dim in self.scan_dimensions:
            score = self._scan_dimension(dim, meta_states)
            scan_result['dimensions'][dim] = score

            if dim in self.alert_thresholds and score < self.alert_thresholds[dim]:
                scan_result['alerts'].append({
                    'dimension': dim,
                    'score': score,
                    'threshold': self.alert_thresholds[dim]
                })

        scan_result['overall_score'] = float(np.mean(list(scan_result['dimensions'].values())))
        self.scan_history.append(scan_result)

        return scan_result

    def predict(self, horizon: int = 5) -> Dict:
        """前瞻预测"""
        if len(self.scan_history) < 3:
            return {'status': 'insufficient_data', 'predictions': []}

        # 简单线性外推预测
        recent = self.scan_history[-10:]
        predictions = []

        for dim in self.scan_dimensions:
            values = [s['dimensions'].get(dim, 0.5) for s in recent if dim in s.get('dimensions', {})]
            if len(values) >= 2:
                # 线性回归
                x = np.arange(len(values))
                slope, intercept = np.polyfit(x, values, 1)

                future_values = []
                for h in range(1, horizon + 1):
                    pred = slope * (len(values) + h) + intercept
                    future_values.append(max(0.0, min(1.0, pred)))

                predictions.append({
                    'dimension': dim,
                    'current': values[-1],
                    'predicted': future_values,
                    'trend': 'up' if slope > 0.01 else 'down' if slope < -0.01 else 'stable'
                })

        prediction_result = {
            'horizon': horizon,
            'timestamp': time.time(),
            'predictions': predictions
        }
        self.predictions.append(prediction_result)

        return prediction_result

    def _scan_dimension(self, dim: str, meta_states: Dict) -> float:
        """扫描单个维度"""
        if dim == 'meta_health':
            healths = [s.get('health', 0.5) for s in meta_states.values()]
            return float(np.mean(healths)) if healths else 0.5
        elif dim == 'coupling_strength':
            return meta_states.get('_coupling', {}).get('avg_strength', 0.5)
        elif dim == 'spin_stability':
            return 1.0 - abs(meta_states.get('Wheel', {}).get('delta', 0.5))
        elif dim == 'knowledge_growth':
            return min(1.0, meta_states.get('Spine', {}).get('growth_rate', 0) / 100)
        elif dim == 'consensus_quality':
            return meta_states.get('Ding', {}).get('consensus_ratio', 0.5)
        elif dim == 'contract_integrity':
            return meta_states.get('Ring', {}).get('integrity', 1.0)
        elif dim == 'system_entropy':
            return 1.0 - meta_states.get('_global', {}).get('order', 0.5)
        elif dim == 'prediction_accuracy':
            return self.prediction_accuracy
        return 0.5

    def _compute_confidence(self, metrics: Dict) -> float:
        """计算观测置信度"""
        if not metrics:
            return 0.0
        # 基于数据完整性和一致性
        completeness = len(metrics) / len(self.scan_dimensions)
        consistency = 1.0 - np.std(list(metrics.values())) if metrics else 0.0
        return float(np.clip((completeness + consistency) / 2, 0.0, 1.0))

    def _check_alerts(self, frame: ObservationFrame):
        """检查告警条件"""
        for metric, value in frame.metrics.items():
            threshold = self.alert_thresholds.get(metric)
            if threshold is not None and value < threshold:
                self.alerts.append({
                    'timestamp': time.time(),
                    'metric': metric,
                    'value': value,
                    'threshold': threshold,
                    'frame_id': frame.frame_id
                })

    @property
    def activity_score(self) -> float:
        return len(self.observation_stack) / 100.0 + (1.0 if self.state == MetaState.ACTIVE else 0.0)


class RingMeta:
    """
    环(Ring) — 闭环契约 / 强制执行契约

    职责:
    - N-MUST/M-CODE的递归强化
    - 契约的链式绑定
    - 违约自动修复
    - 闭环保证
    """

    def __init__(self):
        self.name = 'Ring'
        self.symbol = '环'
        self.role = MetaRole.ENFORCER
        self.state = MetaState.INITIALIZING

        # 契约链
        self.contract_chain: List[ContractLink] = []

        # 活跃契约
        self.active_contracts: Dict[str, ContractLink] = {}

        # 契约模板
        self.contract_templates = {
            'N-MUST': {
                'must_enable': True,
                'must_track': True,
                'must_verify': True,
                'timeout_sec': 5.0
            },
            'M-CODE': {
                'trigger_required': True,
                'action_enforced': True,
                'verification_mandatory': True
            },
            'DELTA-BASE': {
                'delta_computed': True,
                'target_enforced': True,
                'reached_verified': True
            }
        }

        # 违约记录
        self.violations: List[Dict] = []

        # 修复记录
        self.repairs: List[Dict] = []

        # 自动修复启用
        self.auto_repair = True

        # 链完整性
        self.chain_integrity = 1.0

        self._lock = threading.RLock()

    def forge_contract(self, contract_type: str, 
                       binding: Dict[str, Any]) -> ContractLink:
        """锻造新契约并链接到链上"""
        with self._lock:
            link = ContractLink(
                link_id=f"LINK-{uuid.uuid4().hex[:8].upper()}",
                contract_type=contract_type,
                binding=binding,
                created_at=time.time()
            )

            # 链式绑定
            prev_link = self.contract_chain[-1] if self.contract_chain else None
            link.bind_chain(prev_link)

            self.contract_chain.append(link)
            self.active_contracts[link.link_id] = link

            return link

    def enforce(self, link_id: str, context: Dict[str, Any] = None) -> Dict:
        """执行契约强制"""
        with self._lock:
            link = self.active_contracts.get(link_id)
            if link is None:
                return {'status': 'contract_not_found'}

            link.last_checked = time.time()

            # 验证契约条件
            template = self.contract_templates.get(link.contract_type, {})
            checks = {}
            all_passed = True

            for condition, required in template.items():
                actual = link.binding.get(condition, False)
                passed = (actual == required) if required else True
                checks[condition] = {'required': required, 'actual': actual, 'passed': passed}
                if not passed:
                    all_passed = False

            if not all_passed:
                link.violation_count += 1
                violation = {
                    'link_id': link_id,
                    'timestamp': time.time(),
                    'failed_checks': [c for c, r in checks.items() if not r['passed']],
                    'context': context
                }
                self.violations.append(violation)

                # 自动修复
                if self.auto_repair:
                    repair_result = self._auto_repair(link, checks)
                    return {
                        'status': 'violation_repaired' if repair_result else 'violation',
                        'link_id': link_id,
                        'checks': checks,
                        'repair': repair_result
                    }

                return {'status': 'violation', 'link_id': link_id, 'checks': checks}

            return {'status': 'enforced', 'link_id': link_id, 'checks': checks}

    def _auto_repair(self, link: ContractLink, checks: Dict) -> bool:
        """自动修复违约"""
        link.repair_attempts += 1

        # 修复策略: 补全缺失的绑定
        template = self.contract_templates.get(link.contract_type, {})
        repaired = False

        for condition, required in template.items():
            if not checks[condition]['passed'] and required:
                link.binding[condition] = required
                repaired = True

        self.repairs.append({
            'link_id': link.link_id,
            'timestamp': time.time(),
            'repaired_count': sum(1 for c in checks.values() if c['passed']),
            'success': repaired
        })

        return repaired

    def verify_chain_integrity(self) -> Dict:
        """验证契约链完整性"""
        if not self.contract_chain:
            return {'status': 'empty_chain', 'integrity': 1.0}

        broken_links = 0
        for i, link in enumerate(self.contract_chain):
            if i > 0:
                prev = self.contract_chain[i-1]
                expected_hash = link.compute_chain_hash(prev.chain_hash)
                if link.chain_hash != expected_hash:
                    broken_links += 1

        integrity = 1.0 - (broken_links / len(self.contract_chain))
        self.chain_integrity = integrity

        return {
            'status': 'verified',
            'integrity': integrity,
            'broken_links': broken_links,
            'total_links': len(self.contract_chain)
        }

    def recursive_reinforce(self, depth: int = 3) -> Dict:
        """递归强化所有活跃契约"""
        results = []

        for link_id, link in list(self.active_contracts.items()):
            if not link.is_active:
                continue

            # 基础强化
            result = self.enforce(link_id)

            # 递归强化
            if depth > 0 and result['status'] not in ['enforced']:
                sub_result = self.recursive_reinforce(depth - 1)
                result['recursive_reinforce'] = sub_result

            results.append(result)

        return {
            'depth': depth,
            'reinforced_count': len(results),
            'results': results
        }

    def get_enforcement_stats(self) -> Dict:
        return {
            'total_contracts': len(self.contract_chain),
            'active_contracts': sum(1 for c in self.active_contracts.values() if c.is_active),
            'total_violations': len(self.violations),
            'total_repairs': len(self.repairs),
            'chain_integrity': self.chain_integrity
        }

    @property
    def activity_score(self) -> float:
        return len(self.active_contracts) / 10.0 + (1.0 if self.state == MetaState.ACTIVE else 0.0)



# =============================================================================
# SECTION 3: Coupling Matrix & Interaction Protocol
# =============================================================================

class CouplingMatrix:
    """
    六元耦合矩阵 — 6×6动态耦合权重系统

    矩阵索引: [Gu, Wheel, Spine, Ding, Tower, Ring]

    耦合类型:
    - info: 信息流 (数据、指令、状态)
    - energy: 能量流 (资源、动力、优先级)
    - control: 控制流 (调度、约束、策略)
    - feedback: 反馈流 (结果、状态、健康度)
    - resonance: 共振流 (同步、协同、谐振)

    动态调整: 基于系统状态实时调整耦合权重
    """

    # 基础耦合权重矩阵 (静态)
    BASE_WEIGHTS = np.array([
        # Gu   Wheel  Spine  Ding   Tower  Ring   
        [0.00, 0.85, 0.70, 0.90, 0.75, 0.80],  # Gu (控制其他)
        [0.60, 0.00, 0.55, 0.65, 0.50, 0.70],  # Wheel (迭代驱动)
        [0.45, 0.50, 0.00, 0.60, 0.55, 0.40],  # Spine (传承支撑)
        [0.70, 0.65, 0.60, 0.00, 0.55, 0.75],  # Ding (共识仲裁)
        [0.80, 0.60, 0.65, 0.70, 0.00, 0.65],  # Tower (观测全局)
        [0.75, 0.70, 0.45, 0.80, 0.60, 0.00],  # Ring (契约约束)
    ], dtype=np.float64)

    # 流类型权重分配
    FLOW_TYPE_WEIGHTS = {
        FlowType.INFORMATION: 1.0,
        FlowType.ENERGY: 0.8,
        FlowType.CONTROL: 1.2,
        FlowType.FEEDBACK: 0.9,
        FlowType.RESONANCE: 1.5
    }

    def __init__(self):
        self.names = META_NAMES
        self.n = len(self.names)
        self.index = {name: i for i, name in enumerate(self.names)}

        # 当前动态权重
        self.weights = self.BASE_WEIGHTS.copy()

        # 耦合通道
        self.channels: Dict[Tuple[str, str], CouplingChannel] = {}
        self._init_channels()

        # 动态调整参数
        self.adaptation_rate = 0.05
        self.stability_factor = 0.9

        # 历史记录
        self.history: List[Dict] = []

        self._lock = threading.RLock()

    def _init_channels(self):
        """初始化所有耦合通道"""
        for i, src in enumerate(self.names):
            for j, dst in enumerate(self.names):
                if i != j:
                    self.channels[(src, dst)] = CouplingChannel(
                        source=src,
                        target=dst,
                        weight=self.weights[i, j]
                    )

    def get_weight(self, source: str, target: str) -> float:
        """获取耦合权重"""
        i, j = self.index[source], self.index[target]
        return float(self.weights[i, j])

    def set_weight(self, source: str, target: str, weight: float):
        """设置耦合权重"""
        i, j = self.index[source], self.index[target]
        self.weights[i, j] = np.clip(weight, 0.0, 2.0)

        key = (source, target)
        if key in self.channels:
            self.channels[key].weight = self.weights[i, j]

    def get_channel(self, source: str, target: str) -> Optional[CouplingChannel]:
        """获取耦合通道"""
        return self.channels.get((source, target))

    def compute_transfer(self, source: str, target: str, 
                         flow_type: FlowType,
                         packet: MetaPacket) -> float:
        """
        计算从source到target的传输效率

        传输效率 = 权重 × 流类型系数 × 通道容量 × 优先级衰减
        """
        weight = self.get_weight(source, target)
        flow_coef = self.FLOW_TYPE_WEIGHTS.get(flow_type, 1.0)

        channel = self.get_channel(source, target)
        capacity = channel.compute_capacity() if channel else 0.5

        # 优先级衰减 (高优先级减少衰减)
        priority_factor = 0.5 + 0.5 * packet.priority

        # TTL衰减
        ttl_factor = packet.ttl / 10.0

        efficiency = weight * flow_coef * capacity * priority_factor * ttl_factor
        return float(np.clip(efficiency, 0.0, 2.0))

    def adapt(self, system_state: Dict[str, float]):
        """
        动态调整耦合矩阵

        调整策略:
        1. 根据元的健康度调整输入权重
        2. 根据系统负载调整带宽
        3. 根据历史交互成功率调整可靠性
        """
        with self._lock:
            new_weights = self.weights.copy()

            for i, src in enumerate(self.names):
                src_health = system_state.get(f"{src}_health", 0.5)

                for j, dst in enumerate(self.names):
                    if i == j:
                        continue

                    dst_health = system_state.get(f"{dst}_health", 0.5)

                    # 健康度调整: 健康元之间的耦合增强
                    health_factor = (src_health + dst_health) / 2

                    # 负载调整: 高负载元减少输入
                    dst_load = system_state.get(f"{dst}_load", 0.5)
                    load_factor = 1.0 - 0.3 * dst_load

                    # 交互成功率
                    channel = self.channels.get((src, dst))
                    success_factor = channel.reliability if channel else 0.9

                    # 综合调整
                    adjustment = health_factor * load_factor * success_factor
                    base = self.BASE_WEIGHTS[i, j]

                    new_weights[i, j] = base * adjustment

            # 平滑过渡
            self.weights = (self.stability_factor * self.weights + 
                           (1 - self.stability_factor) * new_weights)

            # 更新通道
            for i, src in enumerate(self.names):
                for j, dst in enumerate(self.names):
                    if i != j:
                        key = (src, dst)
                        if key in self.channels:
                            self.channels[key].weight = self.weights[i, j]

            self._record_state(system_state)

    def _record_state(self, system_state: Dict):
        """记录状态历史"""
        self.history.append({
            'timestamp': time.time(),
            'weights': self.weights.copy(),
            'system_state': system_state.copy()
        })
        if len(self.history) > 100:
            self.history = self.history[-50:]

    def get_dominant_flows(self, top_k: int = 5) -> List[Dict]:
        """获取主导耦合流"""
        flows = []
        for i, src in enumerate(self.names):
            for j, dst in enumerate(self.names):
                if i != j:
                    flows.append({
                        'source': src,
                        'target': dst,
                        'weight': float(self.weights[i, j])
                    })

        flows.sort(key=lambda x: x['weight'], reverse=True)
        return flows[:top_k]

    def get_matrix_summary(self) -> Dict:
        """获取矩阵摘要"""
        return {
            'matrix': self.weights.tolist(),
            'avg_weight': float(np.mean(self.weights[self.weights > 0])),
            'max_weight': float(np.max(self.weights)),
            'min_weight': float(np.min(self.weights[self.weights > 0])),
            'std_weight': float(np.std(self.weights[self.weights > 0])),
            'dominant_flows': self.get_dominant_flows(3)
        }


# =============================================================================
# SECTION 4: Meta Interaction Protocol
# =============================================================================

class MetaProtocol:
    """
    六元交互协议

    定义六元之间的标准化交互模式:
    - 请求-响应 (Request-Response)
    - 发布-订阅 (Publish-Subscribe)
    - 推送-反馈 (Push-Feedback)
    - 共振-同步 (Resonance-Sync)

    协议层负责:
    1. 消息编码/解码
    2. 路由选择
    3. 优先级调度
    4. 错误处理与重试
    """

    def __init__(self, coupling_matrix: CouplingMatrix):
        self.coupling = coupling_matrix
        self.packet_queue: deque = deque()
        self.delivered_packets: List[MetaPacket] = []

        # 协议统计
        self.stats = {
            'sent': 0,
            'delivered': 0,
            'dropped': 0,
            'retried': 0
        }

        # 处理线程
        self._running = False
        self._processor_thread = None

    def send(self, source: str, target: str, 
             flow_type: FlowType,
             payload: Dict[str, Any],
             priority: float = 1.0) -> MetaPacket:
        """发送数据包"""
        packet = MetaPacket(
            packet_id=f"PKT-{uuid.uuid4().hex[:8].upper()}",
            source=source,
            target=target,
            flow_type=flow_type,
            payload=payload,
            timestamp=time.time(),
            priority=priority
        )
        packet.sign()

        self.packet_queue.append(packet)
        self.stats['sent'] += 1

        return packet

    def broadcast(self, source: str, flow_type: FlowType,
                  payload: Dict[str, Any],
                  exclude: Optional[List[str]] = None) -> List[MetaPacket]:
        """广播到所有其他元"""
        packets = []
        exclude = exclude or []

        for target in META_NAMES:
            if target != source and target not in exclude:
                pkt = self.send(source, target, flow_type, payload)
                packets.append(pkt)

        return packets

    def route(self, packet: MetaPacket) -> Tuple[bool, float]:
        """
        路由数据包

        Returns:
            (delivered, efficiency)
        """
        # 检查TTL
        if packet.ttl <= 0:
            self.stats['dropped'] += 1
            return False, 0.0

        packet.ttl -= 1

        # 计算传输效率
        efficiency = self.coupling.compute_transfer(
            packet.source, packet.target, packet.flow_type, packet
        )

        # 基于效率决定交付
        if random.random() < efficiency:
            packet.payload['delivery_efficiency'] = efficiency
            packet.payload['delivered_at'] = time.time()
            self.delivered_packets.append(packet)
            self.stats['delivered'] += 1

            # 更新通道活跃度
            channel = self.coupling.get_channel(packet.source, packet.target)
            if channel:
                channel.last_activity = time.time()
                channel.packet_count += 1

            return True, efficiency
        else:
            # 尝试重传
            if packet.ttl > 0:
                self.packet_queue.append(packet)
                self.stats['retried'] += 1
            else:
                self.stats['dropped'] += 1

            return False, efficiency

    def process_queue(self, max_packets: int = 100) -> List[Tuple[MetaPacket, bool, float]]:
        """处理队列中的数据包"""
        results = []
        count = 0

        while self.packet_queue and count < max_packets:
            packet = self.packet_queue.popleft()
            delivered, efficiency = self.route(packet)
            results.append((packet, delivered, efficiency))
            count += 1

        return results

    def get_protocol_stats(self) -> Dict:
        return {
            **self.stats,
            'queue_length': len(self.packet_queue),
            'delivery_rate': self.stats['delivered'] / max(self.stats['sent'], 1),
            'drop_rate': self.stats['dropped'] / max(self.stats['sent'], 1)
        }


# =============================================================================
# SECTION 5: Self-Reinforcement Mechanism
# =============================================================================

class SelfReinforcementEngine:
    """
    六元自我强化引擎

    强化机制:
    1. 正反馈循环: 高效交互 → 耦合增强 → 更高效
    2. 负反馈阻尼: 过度耦合 → 自动衰减 → 稳定
    3. 共振放大: 同频元 → 协同增强
    4. 自适应平衡: 动态调整 → 全局最优

    强化公式:
        ΔW_ij = α × (E_ij - W_ij) + β × R_ij - γ × O_ij

        其中:
        - E_ij: 实际交互效率
        - W_ij: 当前耦合权重
        - R_ij: 共振因子
        - O_ij: 过载因子
        - α, β, γ: 学习率
    """

    def __init__(self, coupling_matrix: CouplingMatrix):
        self.coupling = coupling_matrix

        # 学习率
        self.alpha = 0.1   # 效率学习率
        self.beta = 0.05   # 共振学习率
        self.gamma = 0.08  # 过载惩罚率

        # 强化历史
        self.reinforcement_log: List[Dict] = []

        # 强化周期计数
        self.cycle_count = 0

    def reinforce(self, interaction_log: List[Dict]) -> Dict:
        """
        执行一次强化周期

        Args:
            interaction_log: 交互日志 [{source, target, efficiency, resonance, overload}]
        """
        adjustments = []

        for entry in interaction_log:
            src = entry['source']
            dst = entry['target']
            efficiency = entry.get('efficiency', 0.5)
            resonance = entry.get('resonance', 0.0)
            overload = entry.get('overload', 0.0)

            current_weight = self.coupling.get_weight(src, dst)

            # 计算调整量
            delta_efficiency = self.alpha * (efficiency - current_weight)
            delta_resonance = self.beta * resonance
            delta_overload = -self.gamma * overload

            total_delta = delta_efficiency + delta_resonance + delta_overload
            new_weight = np.clip(current_weight + total_delta, 0.0, 2.0)

            self.coupling.set_weight(src, dst, new_weight)

            adjustments.append({
                'source': src,
                'target': dst,
                'old_weight': current_weight,
                'new_weight': new_weight,
                'delta': total_delta,
                'components': {
                    'efficiency': delta_efficiency,
                    'resonance': delta_resonance,
                    'overload': delta_overload
                }
            })

        self.cycle_count += 1

        result = {
            'cycle': self.cycle_count,
            'timestamp': time.time(),
            'adjustments': adjustments,
            'total_adjustment': sum(abs(a['delta']) for a in adjustments)
        }
        self.reinforcement_log.append(result)

        return result

    def compute_resonance(self, meta_states: Dict[str, Dict]) -> np.ndarray:
        """
        计算六元共振矩阵

        共振发生在两个元处于相似相位时
        """
        n = len(META_NAMES)
        resonance = np.zeros((n, n))

        phases = {}
        for name in META_NAMES:
            state = meta_states.get(name, {})
            phases[name] = state.get('phase', random.random() * 2 * math.pi)

        for i, src in enumerate(META_NAMES):
            for j, dst in enumerate(META_NAMES):
                if i != j:
                    phase_diff = abs(phases[src] - phases[dst])
                    # 归一化到 [0, π]
                    phase_diff = min(phase_diff, 2 * math.pi - phase_diff)
                    # 相位越接近，共振越强
                    resonance[i, j] = math.cos(phase_diff / 2) ** 2

        return resonance

    def detect_overload(self, meta_states: Dict[str, Dict]) -> np.ndarray:
        """
        检测过载矩阵

        过载 = 输入耦合和 - 处理能力
        """
        n = len(META_NAMES)
        overload = np.zeros((n, n))

        for i, src in enumerate(META_NAMES):
            for j, dst in enumerate(META_NAMES):
                if i != j:
                    dst_load = meta_states.get(dst, {}).get('load', 0.5)
                    dst_capacity = meta_states.get(dst, {}).get('capacity', 1.0)

                    if dst_load > dst_capacity:
                        overload[i, j] = (dst_load - dst_capacity) / dst_capacity

        return overload

    def get_reinforcement_stats(self) -> Dict:
        if not self.reinforcement_log:
            return {'cycles': 0}

        recent = self.reinforcement_log[-10:]
        return {
            'cycles': self.cycle_count,
            'avg_adjustment': sum(r['total_adjustment'] for r in recent) / len(recent),
            'last_cycle': self.reinforcement_log[-1]['cycle']
        }


# =============================================================================
# SECTION 6: Meta Structure Orchestrator
# =============================================================================

class MetaStructureOrchestrator:
    """
    六元结构编排器 — 全局协调中心

    负责:
    1. 六元的生命周期管理
    2. 全局交互编排
    3. 状态同步
    4. 与现有系统的集成
    """

    def __init__(self):
        # 六元实例
        self.gu = GuMeta()
        self.wheel = WheelMeta()
        self.spine = SpineMeta()
        self.ding = DingMeta()
        self.tower = TowerMeta()
        self.ring = RingMeta()

        self.metas: Dict[str, Any] = {
            'Gu': self.gu,
            'Wheel': self.wheel,
            'Spine': self.spine,
            'Ding': self.ding,
            'Tower': self.tower,
            'Ring': self.ring
        }

        # 耦合矩阵
        self.coupling = CouplingMatrix()

        # 交互协议
        self.protocol = MetaProtocol(self.coupling)

        # 强化引擎
        self.reinforcement = SelfReinforcementEngine(self.coupling)

        # 系统节拍
        self.beat_count = 0
        self.beat_interval = 0.1  # 100ms

        # 全局状态
        self.global_metrics: Dict[str, Any] = {}

        # 运行状态
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # 初始化
        self._initialize_metas()

    def _initialize_metas(self):
        """初始化所有元并注册到毂"""
        for name, meta in self.metas.items():
            meta.state = MetaState.INITIALIZING
            # 注册到Gu
            self.gu.register_meta(name, meta)

        # Gu自描述
        self.gu.describe_self()

        # 所有元激活
        for name, meta in self.metas.items():
            meta.state = MetaState.ACTIVE

    def beat(self) -> Dict:
        """
        执行一次系统节拍

        节拍流程:
        1. Wheel spin
        2. Tower scan
        3. 元交互
        4. Ding consensus (如果需要)
        5. Ring enforcement
        6. Spine knowledge update
        7. Gu coordination
        8. Coupling adaptation
        """
        self.beat_count += 1
        beat_result = {
            'beat': self.beat_count,
            'timestamp': time.time(),
            'phases': {}
        }

        # Phase 1: Wheel spin
        spin = self.wheel.spin()
        beat_result['phases']['wheel_spin'] = {
            'iteration': spin.iteration,
            'energy': spin.energy,
            'phase': spin.phase,
            'converged': self.wheel.converged
        }

        # Phase 2: Tower scan
        meta_states = self._collect_meta_states()
        scan = self.tower.scan_all(meta_states)
        beat_result['phases']['tower_scan'] = scan

        # Phase 3: 元交互 (随机触发)
        if self.beat_count % 3 == 0:
            interactions = self._execute_interactions()
            beat_result['phases']['interactions'] = interactions

        # Phase 4: Ding consensus (每10拍)
        if self.beat_count % 10 == 0:
            consensus = self._forge_consensus()
            beat_result['phases']['consensus'] = consensus

        # Phase 5: Ring enforcement
        if self.beat_count % 5 == 0:
            enforcement = self.ring.recursive_reinforce(depth=2)
            beat_result['phases']['enforcement'] = enforcement

        # Phase 6: Spine knowledge
        self.spine.accumulate_experience({
            'beat': self.beat_count,
            'wheel_converged': self.wheel.converged,
            'scan_score': scan.get('overall_score', 0.5)
        })

        # Phase 7: Gu coordination
        self.gu.update_global_state({
            name: meta.activity_score for name, meta in self.metas.items()
        })

        # Phase 8: Coupling adaptation
        system_state = self._build_system_state()
        self.coupling.adapt(system_state)

        # 强化 (每20拍)
        if self.beat_count % 20 == 0:
            interaction_log = self._build_interaction_log()
            reinforcement = self.reinforcement.reinforce(interaction_log)
            beat_result['phases']['reinforcement'] = reinforcement

        self.global_metrics = beat_result
        return beat_result

    def _collect_meta_states(self) -> Dict[str, Dict[str, float]]:
        """收集所有元的状态"""
        states = {}

        # Gu
        states['Gu'] = {
            'health': self.gu.get_system_health(),
            'phase': 0.0,
            'load': 0.3,
            'capacity': 1.0
        }

        # Wheel
        if self.wheel.current_spin:
            states['Wheel'] = {
                'health': self.wheel.energy_pool,
                'phase': self.wheel.current_spin.phase,
                'delta': self.wheel.last_delta,
                'load': 1.0 - self.wheel.energy_pool,
                'capacity': 1.0
            }
        else:
            states['Wheel'] = {'health': 0.5, 'phase': 0.0, 'delta': 0.5, 'load': 0.5, 'capacity': 1.0}

        # Spine
        spine_metrics = self.spine.get_growth_metrics()
        states['Spine'] = {
            'health': spine_metrics.get('avg_durability', 0.5),
            'phase': spine_metrics.get('growth_path_length', 0) * 0.1,
            'growth_rate': spine_metrics.get('total_knowledge_nodes', 0),
            'load': min(1.0, spine_metrics.get('total_knowledge_nodes', 0) / 1000),
            'capacity': 1.0
        }

        # Ding
        ding_stats = self.ding.get_consensus_stats()
        states['Ding'] = {
            'health': 1.0 if ding_stats['total_resolutions'] > 0 else 0.5,
            'phase': 0.0,
            'consensus_ratio': ding_stats.get('finalized_shards', 0) / max(ding_stats.get('total_shards', 1), 1),
            'load': min(1.0, ding_stats.get('pending_consensus', 0) / 10.0),
            'capacity': 1.0
        }

        # Tower
        states['Tower'] = {
            'health': 0.8 if self.tower.observation_stack else 0.5,
            'phase': len(self.tower.observation_stack) * 0.01,
            'load': min(1.0, len(self.tower.observation_stack) / 500),
            'capacity': 1.0
        }

        # Ring
        ring_stats = self.ring.get_enforcement_stats()
        states['Ring'] = {
            'health': ring_stats.get('chain_integrity', 1.0),
            'phase': 0.0,
            'integrity': ring_stats.get('chain_integrity', 1.0),
            'load': min(1.0, ring_stats.get('total_violations', 0) / 10.0),
            'capacity': 1.0
        }

        # 全局耦合状态
        states['_coupling'] = {
            'avg_strength': float(np.mean(self.coupling.weights[self.coupling.weights > 0]))
        }
        states['_global'] = {
            'order': np.mean([s.get('health', 0.5) for s in states.values() if isinstance(s, dict) and 'health' in s])
        }

        return states

    def _execute_interactions(self) -> List[Dict]:
        """执行元间交互"""
        interactions = []

        # 生成一些随机交互
        flow_types = list(FlowType)

        for _ in range(5):
            src, dst = random.sample(META_NAMES, 2)
            flow = random.choice(flow_types)

            payload = {
                'beat': self.beat_count,
                'interaction_id': f"INT-{uuid.uuid4().hex[:6]}"
            }

            packet = self.protocol.send(src, dst, flow, payload)
            delivered, efficiency = self.protocol.route(packet)

            interactions.append({
                'source': src,
                'target': dst,
                'flow_type': flow.name,
                'delivered': delivered,
                'efficiency': efficiency
            })

        return interactions

    def _forge_consensus(self) -> Dict:
        """锻造共识"""
        # 收集投票
        proposal = {'id': f"PROP-{self.beat_count}", 'action': 'beat_advance'}

        for line in LINES[:5]:  # 前5条线投票
            vote = random.choice([True, False, True])  # 2/3概率同意
            self.ding.collect_vote(line, proposal, vote)

        # 尝试锻造共识
        shard_id = f"SHARD-{proposal['id']}"
        result = self.ding.forge_consensus(shard_id)

        return result or {'status': 'no_consensus'}

    def _build_system_state(self) -> Dict[str, float]:
        """构建系统状态用于耦合调整"""
        states = self._collect_meta_states()
        system_state = {}

        for name in META_NAMES:
            s = states.get(name, {})
            system_state[f"{name}_health"] = s.get('health', 0.5)
            system_state[f"{name}_load"] = s.get('load', 0.5)

        return system_state

    def _build_interaction_log(self) -> List[Dict]:
        """构建交互日志用于强化"""
        log = []

        # 从协议获取最近的交互
        recent_packets = self.protocol.delivered_packets[-50:]

        for pkt in recent_packets:
            # 计算效率
            channel = self.coupling.get_channel(pkt.source, pkt.target)
            efficiency = channel.transfer_efficiency() if channel else 0.5

            # 计算共振
            src_phase = 0.0
            dst_phase = 0.0
            if hasattr(self.metas.get(pkt.source), 'current_spin') and self.metas[pkt.source].current_spin:
                src_phase = self.metas[pkt.source].current_spin.phase
            if hasattr(self.metas.get(pkt.target), 'current_spin') and self.metas[pkt.target].current_spin:
                dst_phase = self.metas[pkt.target].current_spin.phase

            phase_diff = abs(src_phase - dst_phase)
            phase_diff = min(phase_diff, 2 * math.pi - phase_diff)
            resonance = math.cos(phase_diff / 2) ** 2

            log.append({
                'source': pkt.source,
                'target': pkt.target,
                'efficiency': efficiency,
                'resonance': resonance,
                'overload': 0.0
            })

        return log

    def run_beats(self, n: int = 100) -> List[Dict]:
        """运行n个节拍"""
        results = []
        for _ in range(n):
            result = self.beat()
            results.append(result)
        return results

    def get_full_state(self) -> Dict:
        """获取完整系统状态"""
        return {
            'metas': {
                name: {
                    'name': meta.name,
                    'symbol': meta.symbol,
                    'role': meta.role.name,
                    'state': meta.state.name,
                    'activity_score': meta.activity_score
                }
                for name, meta in self.metas.items()
            },
            'coupling': self.coupling.get_matrix_summary(),
            'protocol': self.protocol.get_protocol_stats(),
            'reinforcement': self.reinforcement.get_reinforcement_stats(),
            'beat_count': self.beat_count,
            'system_health': self.gu.get_system_health()
        }



# =============================================================================
# SECTION 7: Legacy System Integration
# =============================================================================

class LegacyIntegration:
    """
    与现有层-圈-环-网-云系统的集成适配器

    映射关系:
    层(layer)   ↔ 毂(Gu)    — 控制中心
    圈(circle)  ↔ 鼎(Ding)  — 共识圈
    环(ring)    ↔ 环(Ring)  — 闭环
    网(net)     ↔ 轮(Wheel) — 递归网
    云(cloud)   ↔ 塔(Tower) — 瞭望云
    脊(Spine)   ↔ 层(layer) — 纵向传承(补充映射)

    经-纬-薪映射:
    经(jing) ↔ 脊(Spine) — 纵向传承
    纬(wei)  ↔ 轮(Wheel) — 横向循环
    薪(xin)  ↔ 鼎(Ding)  — 共识燃料

    张量-链流转:
    张量场 ↔ Wheel → Ring → Tower
    链式哈希 ↔ Ring → Spine → Gu
    收缩操作 ↔ Tower → Ding → Wheel
    """

    def __init__(self, orchestrator: MetaStructureOrchestrator):
        self.orchestrator = orchestrator

        # 双向映射表
        self.legacy_to_meta = LEGACY_TO_META.copy()
        self.meta_to_legacy = META_TO_LEGACY.copy()

        # 经-纬-薪映射
        self.jing_wei_xin = JING_WEI_XIN.copy()

        # 张量-链流转
        self.tensor_chain_flow = TENSOR_CHAIN_FLOW.copy()

        # 集成日志
        self.integration_log: List[Dict] = []

    def map_legacy_to_meta(self, legacy_level: str, legacy_node: str) -> Tuple[str, Dict]:
        """将层-圈-环-网-云节点映射到六元"""
        meta_name = self.legacy_to_meta.get(legacy_level, 'Gu')
        meta = self.orchestrator.metas.get(meta_name)

        mapping_info = {
            'legacy_level': legacy_level,
            'legacy_node': legacy_node,
            'mapped_meta': meta_name,
            'meta_symbol': meta.symbol if meta else '?',
            'mapping_type': 'direct'
        }

        self.integration_log.append(mapping_info)
        return meta_name, mapping_info

    def map_meta_to_legacy(self, meta_name: str) -> Tuple[str, Dict]:
        """将六元映射回层-圈-环-网-云"""
        legacy_level = self.meta_to_legacy.get(meta_name, 'layer')

        mapping_info = {
            'meta_name': meta_name,
            'mapped_legacy': legacy_level,
            'mapping_type': 'reverse'
        }

        self.integration_log.append(mapping_info)
        return legacy_level, mapping_info

    def route_tensor_field(self, tensor_data: Dict[str, Any]) -> List[Dict]:
        """
        张量场流转: Wheel → Ring → Tower

        在张量场中，数据先经过轮的迭代处理，
        然后经过环的契约验证，最后到达塔的观测分析。
        """
        flow_path = self.tensor_chain_flow['tensor_field']
        results = []

        current_data = tensor_data.copy()

        for meta_name in flow_path:
            meta = self.orchestrator.metas.get(meta_name)

            # 模拟处理
            processed = self._process_tensor_step(meta_name, current_data)
            results.append({
                'meta': meta_name,
                'input_shape': current_data.get('shape', 'unknown'),
                'output_shape': processed.get('shape', 'unknown'),
                'processing_time': processed.get('time', 0)
            })
            current_data = processed

        return results

    def route_chain_hash(self, chain_data: Dict[str, Any]) -> List[Dict]:
        """
        链式哈希流转: Ring → Spine → Gu

        链式哈希数据先经过环的契约绑定，
        然后存储到脊的知识谱系，最后归档到毂的全局描述。
        """
        flow_path = self.tensor_chain_flow['chain_hash']
        results = []

        current_data = chain_data.copy()

        for meta_name in flow_path:
            meta = self.orchestrator.metas.get(meta_name)

            processed = self._process_chain_step(meta_name, current_data)
            results.append({
                'meta': meta_name,
                'hash_digest': processed.get('hash', 'none'),
                'integrity': processed.get('integrity', 0.0)
            })
            current_data = processed

        return results

    def route_contraction(self, contraction_data: Dict[str, Any]) -> List[Dict]:
        """
        收缩操作流转: Tower → Ding → Wheel

        收缩操作先由塔观测数据模式，
        然后由鼎合成共识，最后由轮执行迭代收缩。
        """
        flow_path = self.tensor_chain_flow['contraction']
        results = []

        current_data = contraction_data.copy()

        for meta_name in flow_path:
            meta = self.orchestrator.metas.get(meta_name)

            processed = self._process_contraction_step(meta_name, current_data)
            results.append({
                'meta': meta_name,
                'contraction_factor': processed.get('factor', 1.0),
                'residual': processed.get('residual', 0.0)
            })
            current_data = processed

        return results

    def resolve_jing_wei_xin(self, jing_data: Dict = None, 
                              wei_data: Dict = None,
                              xin_data: Dict = None) -> Dict:
        """
        解析经-纬-薪在六元中的交互

        经(纵向传承) → 脊
        纬(横向循环) → 轮
        薪(共识燃料) → 鼎

        经-纬-薪的交汇点产生系统动力
        """
        result = {
            'jing': None,
            'wei': None,
            'xin': None,
            'intersection': {}
        }

        # 经 → 脊
        if jing_data:
            jing_node = self.orchestrator.spine.ingest_knowledge(
                content={'type': 'jing', 'data': jing_data}
            )
            result['jing'] = {
                'meta': 'Spine',
                'node_id': jing_node.node_id,
                'generation': jing_node.generation
            }

        # 纬 → 轮
        if wei_data:
            self.orchestrator.wheel.inject_energy(
                amount=wei_data.get('energy', 0.1),
                source='wei'
            )
            result['wei'] = {
                'meta': 'Wheel',
                'energy_injected': wei_data.get('energy', 0.1),
                'current_energy': self.orchestrator.wheel.energy_pool
            }

        # 薪 → 鼎
        if xin_data:
            for line, vote in xin_data.get('votes', {}).items():
                self.orchestrator.ding.collect_vote(
                    line, 
                    {'id': f"xin-{time.time()}"},
                    vote
                )
            result['xin'] = {
                'meta': 'Ding',
                'votes_collected': len(xin_data.get('votes', {}))
            }

        # 计算交汇点
        result['intersection'] = {
            'jing_wei_interaction': 'Spine provides knowledge feed to Wheel spin',
            'wei_xin_interaction': 'Wheel energy fuels Ding consensus',
            'xin_jing_interaction': 'Ding resolutions stored in Spine lineage'
        }

        return result

    def _process_tensor_step(self, meta_name: str, data: Dict) -> Dict:
        """模拟张量处理步骤"""
        if meta_name == 'Wheel':
            return {**data, 'processed_by': 'Wheel', 'shape': data.get('shape', [11, 7, 7]), 'time': 0.01}
        elif meta_name == 'Ring':
            return {**data, 'validated_by': 'Ring', 'integrity': 0.99, 'time': 0.005}
        elif meta_name == 'Tower':
            return {**data, 'observed_by': 'Tower', 'anomaly_score': 0.05, 'time': 0.02}
        return data

    def _process_chain_step(self, meta_name: str, data: Dict) -> Dict:
        """模拟链式哈希处理步骤"""
        if meta_name == 'Ring':
            link = self.orchestrator.ring.forge_contract('M-CODE', data)
            return {**data, 'link_id': link.link_id, 'hash': link.chain_hash, 'integrity': 1.0}
        elif meta_name == 'Spine':
            node = self.orchestrator.spine.ingest_knowledge(
                content={'type': 'chain_record', 'data': data}
            )
            return {**data, 'stored_at': node.node_id, 'generation': node.generation}
        elif meta_name == 'Gu':
            return {**data, 'archived_by': 'Gu', 'global_ref': f"gu-{time.time()}"}
        return data

    def _process_contraction_step(self, meta_name: str, data: Dict) -> Dict:
        """模拟收缩处理步骤"""
        if meta_name == 'Tower':
            return {**data, 'pattern_detected': True, 'factor': 0.8}
        elif meta_name == 'Ding':
            return {**data, 'consensus_reached': True, 'factor': 0.7}
        elif meta_name == 'Wheel':
            return {**data, 'iteration_complete': True, 'residual': 0.02}
        return data

    def get_integration_summary(self) -> Dict:
        return {
            'mappings_executed': len(self.integration_log),
            'legacy_to_meta': self.legacy_to_meta,
            'jing_wei_xin': self.jing_wei_xin,
            'tensor_chain_flows': self.tensor_chain_flow
        }


# =============================================================================
# SECTION 8: Experiment Framework
# =============================================================================

class MetaExperiment:
    """
    六元结构实验框架

    实验套件:
    1. 初始化测试
    2. 六元交互测试
    3. 耦合矩阵动态调整测试
    4. 自我强化测试
    5. 与现有系统集成测试
    """

    def __init__(self):
        self.orchestrator: Optional[MetaStructureOrchestrator] = None
        self.integration: Optional[LegacyIntegration] = None
        self.results: Dict[str, Dict] = {}

    def setup(self):
        """设置实验环境"""
        logger.info("=" * 70)
        logger.info("OMNI-HUB v3.8 — 六元元结构实验初始化")
        logger.info("=" * 70)

        self.orchestrator = MetaStructureOrchestrator()
        self.integration = LegacyIntegration(self.orchestrator)

        logger.info(f"\n[SETUP] 六元编排器已初始化")
        logger.info(f"  - 毂(Gu): {self.orchestrator.gu.symbol} — 元控制中心")
        logger.info(f"  - 轮(Wheel): {self.orchestrator.wheel.symbol} — 迭代引擎")
        logger.info(f"  - 脊(Spine): {self.orchestrator.spine.symbol} — 知识谱系")
        logger.info(f"  - 鼎(Ding): {self.orchestrator.ding.symbol} — 共识熔炉")
        logger.info(f"  - 塔(Tower): {self.orchestrator.tower.symbol} — 扫描瞭望")
        logger.info(f"  - 环(Ring): {self.orchestrator.ring.symbol} — 闭环契约")
        logger.info(f"  - 耦合矩阵: 6x6 动态权重系统")
        logger.info(f"  - 交互协议: 5种流类型")
        logger.info(f"  - 强化引擎: 自适应学习")

    def experiment_1_initialization(self) -> Dict:
        """
        实验1: 六元初始化测试

        验证:
        - 所有元正确实例化
        - 状态为ACTIVE
        - 注册到Gu
        - 自描述正确
        """
        logger.info("\n" + "-" * 70)
        logger.info("[实验1] 六元初始化测试")
        logger.info("-" * 70)

        results = {
            'test_name': '六元初始化',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # 测试1.1: 所有元已实例化
        for name in META_NAMES:
            meta = self.orchestrator.metas.get(name)
            passed = meta is not None
            results['details'].append({
                'test': f"{name} 实例化",
                'passed': passed,
                'detail': f"{name}: {meta.symbol if meta else 'N/A'}"
            })
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1

        # 测试1.2: 所有元状态为ACTIVE
        for name, meta in self.orchestrator.metas.items():
            passed = meta.state == MetaState.ACTIVE
            results['details'].append({
                'test': f"{name} 状态ACTIVE",
                'passed': passed,
                'detail': f"状态: {meta.state.name}"
            })
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1

        # 测试1.3: 注册到Gu
        passed = len(self.orchestrator.gu.meta_registry) == 6
        results['details'].append({
            'test': "Gu注册表完整性",
            'passed': passed,
            'detail': f"注册数: {len(self.orchestrator.gu.meta_registry)}/6"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试1.4: Gu自描述
        desc = self.orchestrator.gu.describe_self(depth=2)
        passed = 'self_ref' in desc and 'registered_metas' in desc
        results['details'].append({
            'test': "Gu自描述",
            'passed': passed,
            'detail': f"自引用深度: {desc.get('self_description_of', 'N/A')}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试1.5: 耦合矩阵初始化
        cm = self.orchestrator.coupling
        passed = cm.weights.shape == (6, 6)
        results['details'].append({
            'test': "耦合矩阵维度",
            'passed': passed,
            'detail': f"形状: {cm.weights.shape}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 打印结果
        for detail in results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            logger.info(f"  [{status}] {detail['test']}: {detail['detail']}")

        logger.info(f"\n  结果: {results['passed']}/{results['passed'] + results['failed']} 通过")

        self.results['experiment_1'] = results
        return results

    def experiment_2_interaction(self) -> Dict:
        """
        实验2: 六元交互测试

        验证:
        - 元间数据包传输
        - 多种流类型支持
        - 广播功能
        - 协议统计
        """
        logger.info("\n" + "-" * 70)
        logger.info("[实验2] 六元交互测试")
        logger.info("-" * 70)

        results = {
            'test_name': '六元交互',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        protocol = self.orchestrator.protocol

        # 测试2.1: 点对点传输
        pkt = protocol.send('Gu', 'Wheel', FlowType.CONTROL, 
                           {'command': 'spin', 'speed': 1.0}, priority=1.5)
        delivered, eff = protocol.route(pkt)
        passed = pkt.signature is not None
        results['details'].append({
            'test': "数据包签名",
            'passed': passed,
            'detail': f"签名: {pkt.signature[:16] if pkt.signature else 'N/A'}..."
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试2.2: 多种流类型
        flow_types = [FlowType.INFORMATION, FlowType.ENERGY, 
                     FlowType.CONTROL, FlowType.FEEDBACK, FlowType.RESONANCE]
        for ft in flow_types:
            pkt = protocol.send('Wheel', 'Spine', ft, {'test': True})
            protocol.route(pkt)

        stats = protocol.get_protocol_stats()
        passed = stats['sent'] >= len(flow_types)
        results['details'].append({
            'test': "多流类型发送",
            'passed': passed,
            'detail': f"已发送: {stats['sent']}, 已交付: {stats['delivered']}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试2.3: 广播
        packets = protocol.broadcast('Gu', FlowType.CONTROL, 
                                     {'broadcast': True}, exclude=['Ring'])
        passed = len(packets) == 4  # 6 - 1(Gu) - 1(exclude) = 4
        results['details'].append({
            'test': "广播功能",
            'passed': passed,
            'detail': f"广播包数: {len(packets)} (预期4)"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试2.4: 队列处理
        processed = protocol.process_queue(max_packets=50)
        passed = len(processed) > 0 or len(protocol.packet_queue) == 0
        results['details'].append({
            'test': "队列处理",
            'passed': passed,
            'detail': f"处理包数: {len(processed)}, 队列剩余: {len(protocol.packet_queue)}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试2.5: 协议统计
        stats = protocol.get_protocol_stats()
        passed = 'delivery_rate' in stats and 'drop_rate' in stats
        results['details'].append({
            'test': "协议统计",
            'passed': passed,
            'detail': f"交付率: {stats.get('delivery_rate', 0):.2%}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        for detail in results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            logger.info(f"  [{status}] {detail['test']}: {detail['detail']}")

        logger.info(f"\n  结果: {results['passed']}/{results['passed'] + results['failed']} 通过")

        self.results['experiment_2'] = results
        return results

    def experiment_3_coupling(self) -> Dict:
        """
        实验3: 耦合矩阵动态调整测试

        验证:
        - 基础权重矩阵正确
        - 动态调整响应系统状态
        - 主导流识别
        - 矩阵稳定性
        """
        logger.info("\n" + "-" * 70)
        logger.info("[实验3] 耦合矩阵动态调整测试")
        logger.info("-" * 70)

        results = {
            'test_name': '耦合矩阵动态调整',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        cm = self.orchestrator.coupling

        # 测试3.1: 基础权重
        base_weight = cm.get_weight('Gu', 'Ding')
        passed = 0.0 < base_weight <= 2.0
        results['details'].append({
            'test': "基础耦合权重",
            'passed': passed,
            'detail': f"Gu→Ding权重: {base_weight:.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试3.2: 通道容量计算
        channel = cm.get_channel('Wheel', 'Ring')
        capacity = channel.compute_capacity() if channel else 0
        passed = capacity > 0
        results['details'].append({
            'test': "通道容量计算",
            'passed': passed,
            'detail': f"Wheel→Ring容量: {capacity:.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试3.3: 动态调整
        initial_weights = cm.weights.copy()

        # 模拟系统状态变化
        test_state = {
            'Gu_health': 0.9, 'Gu_load': 0.3,
            'Wheel_health': 0.7, 'Wheel_load': 0.8,
            'Spine_health': 0.8, 'Spine_load': 0.5,
            'Ding_health': 0.9, 'Ding_load': 0.4,
            'Tower_health': 0.85, 'Tower_load': 0.6,
            'Ring_health': 0.95, 'Ring_load': 0.2
        }

        cm.adapt(test_state)
        adapted_weights = cm.weights.copy()

        passed = not np.allclose(initial_weights, adapted_weights)
        results['details'].append({
            'test': "动态调整响应",
            'passed': passed,
            'detail': f"权重变化: {np.sum(np.abs(adapted_weights - initial_weights)):.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试3.4: 主导流识别
        dominant = cm.get_dominant_flows(3)
        passed = len(dominant) == 3 and all('weight' in f for f in dominant)
        results['details'].append({
            'test': "主导流识别",
            'passed': passed,
            'detail': f"Top3: {[(f['source'], f['target'], f['weight']) for f in dominant]}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试3.5: 矩阵摘要
        summary = cm.get_matrix_summary()
        passed = 'avg_weight' in summary and 'dominant_flows' in summary
        results['details'].append({
            'test': "矩阵摘要",
            'passed': passed,
            'detail': f"平均权重: {summary.get('avg_weight', 0):.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        for detail in results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            logger.info(f"  [{status}] {detail['test']}: {detail['detail']}")

        logger.info(f"\n  结果: {results['passed']}/{results['passed'] + results['failed']} 通过")

        self.results['experiment_3'] = results
        return results

    def experiment_4_reinforcement(self) -> Dict:
        """
        实验4: 自我强化测试

        验证:
        - 强化周期执行
        - 权重调整生效
        - 共振计算
        - 过载检测
        """
        logger.info("\n" + "-" * 70)
        logger.info("[实验4] 自我强化测试")
        logger.info("-" * 70)

        results = {
            'test_name': '自我强化',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        engine = self.orchestrator.reinforcement

        # 测试4.1: 强化周期
        interaction_log = [
            {'source': 'Gu', 'target': 'Wheel', 'efficiency': 0.9, 'resonance': 0.8, 'overload': 0.0},
            {'source': 'Wheel', 'target': 'Spine', 'efficiency': 0.7, 'resonance': 0.6, 'overload': 0.1},
            {'source': 'Spine', 'target': 'Ding', 'efficiency': 0.8, 'resonance': 0.7, 'overload': 0.0},
            {'source': 'Ding', 'target': 'Tower', 'efficiency': 0.85, 'resonance': 0.75, 'overload': 0.0},
            {'source': 'Tower', 'target': 'Ring', 'efficiency': 0.75, 'resonance': 0.65, 'overload': 0.05},
            {'source': 'Ring', 'target': 'Gu', 'efficiency': 0.9, 'resonance': 0.85, 'overload': 0.0},
        ]

        initial_cycles = engine.cycle_count
        result = engine.reinforce(interaction_log)
        passed = engine.cycle_count == initial_cycles + 1
        results['details'].append({
            'test': "强化周期执行",
            'passed': passed,
            'detail': f"周期数: {engine.cycle_count}, 调整量: {result['total_adjustment']:.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试4.2: 权重调整
        adjustment_count = len(result['adjustments'])
        passed = adjustment_count > 0
        results['details'].append({
            'test': "权重调整生效",
            'passed': passed,
            'detail': f"调整数: {adjustment_count}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试4.3: 共振计算
        meta_states = {
            'Gu': {'phase': 0.0},
            'Wheel': {'phase': math.pi / 4},
            'Spine': {'phase': math.pi / 2},
            'Ding': {'phase': 3 * math.pi / 4},
            'Tower': {'phase': math.pi},
            'Ring': {'phase': 5 * math.pi / 4}
        }
        resonance = engine.compute_resonance(meta_states)
        passed = resonance.shape == (6, 6)
        results['details'].append({
            'test': "共振矩阵计算",
            'passed': passed,
            'detail': f"矩阵形状: {resonance.shape}, 平均共振: {np.mean(resonance):.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试4.4: 过载检测
        overloaded_states = {
            'Gu': {'load': 0.3, 'capacity': 1.0},
            'Wheel': {'load': 1.2, 'capacity': 1.0},  # 过载
            'Spine': {'load': 0.5, 'capacity': 1.0},
            'Ding': {'load': 0.9, 'capacity': 1.0},
            'Tower': {'load': 0.7, 'capacity': 1.0},
            'Ring': {'load': 1.5, 'capacity': 1.0}   # 过载
        }
        overload = engine.detect_overload(overloaded_states)
        passed = np.any(overload > 0)
        results['details'].append({
            'test': "过载检测",
            'passed': passed,
            'detail': f"过载单元数: {np.sum(overload > 0)}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试4.5: 强化统计
        stats = engine.get_reinforcement_stats()
        passed = stats['cycles'] > 0
        results['details'].append({
            'test': "强化统计",
            'passed': passed,
            'detail': f"总周期: {stats['cycles']}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        for detail in results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            logger.info(f"  [{status}] {detail['test']}: {detail['detail']}")

        logger.info(f"\n  结果: {results['passed']}/{results['passed'] + results['failed']} 通过")

        self.results['experiment_4'] = results
        return results

    def experiment_5_integration(self) -> Dict:
        """
        实验5: 与现有系统集成测试

        验证:
        - 层-圈-环-网-云 ↔ 六元映射
        - 经-纬-薪解析
        - 张量场流转
        - 链式哈希流转
        """
        logger.info("\n" + "-" * 70)
        logger.info("[实验5] 与现有系统集成测试")
        logger.info("-" * 70)

        results = {
            'test_name': '系统集成',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        integration = self.integration

        # 测试5.1: 层-圈-环-网-云 → 六元映射
        legacy_levels = ['layer', 'circle', 'ring', 'net', 'cloud']
        for level in legacy_levels:
            meta_name, info = integration.map_legacy_to_meta(level, f"test_{level}")
            passed = meta_name in META_NAMES
            results['details'].append({
                'test': f"{level} → {meta_name} 映射",
                'passed': passed,
                'detail': f"映射到: {meta_name}({META_SYMBOLS.get(meta_name, '?')})"
            })
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1

        # 测试5.2: 六元 → 层-圈-环-网-云 反向映射
        for meta_name in META_NAMES:
            legacy, info = integration.map_meta_to_legacy(meta_name)
            passed = legacy in ['layer', 'circle', 'ring', 'net', 'cloud']
            results['details'].append({
                'test': f"{meta_name} → {legacy} 反向映射",
                'passed': passed,
                'detail': f"映射到: {legacy}"
            })
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1

        # 测试5.3: 经-纬-薪解析
        jing_data = {'principle': 'vertical_transmission', 'depth': 5}
        wei_data = {'energy': 0.5, 'frequency': 10}
        xin_data = {'votes': {'ucif2': True, 'lgt': False, 'qfa': True}}

        jwx_result = integration.resolve_jing_wei_xin(jing_data, wei_data, xin_data)
        passed = all(k in jwx_result for k in ['jing', 'wei', 'xin', 'intersection'])
        results['details'].append({
            'test': "经-纬-薪解析",
            'passed': passed,
            'detail': f"经→{jwx_result['jing']['meta']}, 纬→{jwx_result['wei']['meta']}, 薪→{jwx_result['xin']['meta']}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试5.4: 张量场流转
        tensor_data = {'shape': [11, 7, 7], 'data': 'test_tensor'}
        tensor_flow = integration.route_tensor_field(tensor_data)
        passed = len(tensor_flow) == 3
        results['details'].append({
            'test': "张量场流转 Wheel→Ring→Tower",
            'passed': passed,
            'detail': f"流转步骤: {[s['meta'] for s in tensor_flow]}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试5.5: 链式哈希流转
        chain_data = {'block': 'test_block', 'nonce': 42}
        chain_flow = integration.route_chain_hash(chain_data)
        passed = len(chain_flow) == 3
        results['details'].append({
            'test': "链式哈希流转 Ring→Spine→Gu",
            'passed': passed,
            'detail': f"流转步骤: {[s['meta'] for s in chain_flow]}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试5.6: 收缩操作流转
        contraction_data = {'operator': 'mean', 'axis': 0}
        contraction_flow = integration.route_contraction(contraction_data)
        passed = len(contraction_flow) == 3
        results['details'].append({
            'test': "收缩操作流转 Tower→Ding→Wheel",
            'passed': passed,
            'detail': f"流转步骤: {[s['meta'] for s in contraction_flow]}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        for detail in results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            logger.info(f"  [{status}] {detail['test']}: {detail['detail']}")

        logger.info(f"\n  结果: {results['passed']}/{results['passed'] + results['failed']} 通过")

        self.results['experiment_5'] = results
        return results

    def experiment_6_full_pipeline(self) -> Dict:
        """
        实验6: 全流水线节拍测试

        运行100个节拍，验证:
        - 节拍执行完整性
        - Wheel收敛
        - Tower预测
        - Ding共识
        - Ring强化
        - 系统稳定性
        """
        logger.info("\n" + "-" * 70)
        logger.info("[实验6] 全流水线节拍测试 (100 beats)")
        logger.info("-" * 70)

        results = {
            'test_name': '全流水线节拍',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # 运行100个节拍
        logger.info("  运行节拍...", end="", flush=True)
        beat_results = self.orchestrator.run_beats(100)
        logger.info(" 完成")

        # 测试6.1: 节拍计数
        passed = self.orchestrator.beat_count == 100
        results['details'].append({
            'test': "节拍计数",
            'passed': passed,
            'detail': f"节拍数: {self.orchestrator.beat_count}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试6.2: Wheel spin历史
        wheel = self.orchestrator.wheel
        passed = len(wheel.spin_history) > 0
        results['details'].append({
            'test': "Wheel spin历史",
            'passed': passed,
            'detail': f"历史数: {len(wheel.spin_history)}, 收敛: {wheel.converged}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试6.3: Spine知识累积
        spine = self.orchestrator.spine
        metrics = spine.get_growth_metrics()
        passed = metrics['experience_count'] > 0
        results['details'].append({
            'test': "Spine知识累积",
            'passed': passed,
            'detail': f"经验数: {metrics['experience_count']}, 知识节点: {metrics['total_knowledge_nodes']}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试6.4: Tower扫描历史
        tower = self.orchestrator.tower
        passed = len(tower.scan_history) > 0
        results['details'].append({
            'test': "Tower扫描历史",
            'passed': passed,
            'detail': f"扫描数: {len(tower.scan_history)}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试6.5: Ring契约链
        ring = self.orchestrator.ring
        ring_stats = ring.get_enforcement_stats()
        passed = ring_stats['total_contracts'] > 0
        results['details'].append({
            'test': "Ring契约链",
            'passed': passed,
            'detail': f"契约数: {ring_stats['total_contracts']}, 完整性: {ring_stats['chain_integrity']:.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试6.6: 系统健康度
        health = self.orchestrator.gu.get_system_health()
        passed = health > 0.0
        results['details'].append({
            'test': "系统健康度",
            'passed': passed,
            'detail': f"健康度: {health:.4f}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        # 测试6.7: 全状态获取
        full_state = self.orchestrator.get_full_state()
        passed = 'metas' in full_state and 'coupling' in full_state
        results['details'].append({
            'test': "全状态获取",
            'passed': passed,
            'detail': f"状态键: {list(full_state.keys())}"
        })
        if passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        for detail in results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            logger.info(f"  [{status}] {detail['test']}: {detail['detail']}")

        logger.info(f"\n  结果: {results['passed']}/{results['passed'] + results['failed']} 通过")

        self.results['experiment_6'] = results
        return results

    def run_all_experiments(self) -> Dict:
        """运行所有实验"""
        self.setup()

        self.experiment_1_initialization()
        self.experiment_2_interaction()
        self.experiment_3_coupling()
        self.experiment_4_reinforcement()
        self.experiment_5_integration()
        self.experiment_6_full_pipeline()

        return self.generate_report()

    def generate_report(self) -> Dict:
        """生成实验报告"""
        total_passed = sum(r['passed'] for r in self.results.values())
        total_tests = sum(r['passed'] + r['failed'] for r in self.results.values())

        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system': 'OMNI-HUB v3.8',
            'meta_structure': 'Gu-Wheel-Spine-Ding-Tower-Ring',
            'total_experiments': len(self.results),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_tests - total_passed,
            'pass_rate': total_passed / total_tests if total_tests > 0 else 0,
            'experiments': self.results,
            'final_state': self.orchestrator.get_full_state() if self.orchestrator else {}
        }

        return report


# =============================================================================
# SECTION 9: Main Execution
# =============================================================================

def main():
    """主函数 — 运行所有实验并输出报告"""
    experiment = MetaExperiment()
    report = experiment.run_all_experiments()

    # 打印最终报告
    logger.info("\n" + "=" * 70)
    logger.info("OMNI-HUB v3.8 — 六元元结构实验最终报告")
    logger.info("=" * 70)
    logger.info(f"时间戳: {report['timestamp']}")
    logger.info(f"系统: {report['system']}")
    logger.info(f"元结构: {report['meta_structure']}")
    logger.info(f"\n总实验数: {report['total_experiments']}")
    logger.info(f"总测试数: {report['total_tests']}")
    logger.info(f"通过: {report['total_passed']}")
    logger.info(f"失败: {report['total_failed']}")
    logger.info(f"通过率: {report['pass_rate']:.1%}")

    logger.info("\n实验明细:")
    for exp_name, exp_result in report['experiments'].items():
        total = exp_result['passed'] + exp_result['failed']
        logger.info(f"  {exp_result['test_name']}: {exp_result['passed']}/{total} 通过")

    # 保存报告
    output_path = '/mnt/agents/output/OMNI-HUB/core/meta_structure_report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"\n报告已保存到: {output_path}")

    return report


if __name__ == '__main__':
    main()
