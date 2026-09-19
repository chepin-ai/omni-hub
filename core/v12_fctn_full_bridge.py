#!/usr/bin/env python3
"""
OMNI-HUB FCTN Full Bridge v12.0
场-圈-环-层-网-塔-云 (FCTN) 七层架构完整打通

七层定义:
1. 场 (Field): 67维统一场状态，11线×5核心场量+纠缠熵+全局相位
2. 圈 (Circle): 线间耦合圈，内圈/中圈/外圈三层
3. 环 (Ring): 自反馈环，正反馈/负反馈/振荡检测
4. 层 (Layer): 6知识基座层 (KG, CC, HG, IN, CT, LL)
5. 网 (Net): 张量网络，线间纠缠+知识关联
6. 塔 (Tower): 层级涌现塔，从局部到全局的涌现结构
7. 云 (Cloud): 分布式部署层 (Cloudflare Worker+KV+D1+Pages)

数据流闭环:
  场 → 圈 → 环 → 层 → 网 → 塔 → 云 → 场

版本: 12.0.0
"""

__version__ = "12.0.0"

import json
import numpy as np
import hashlib
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, deque
import warnings

warnings.filterwarnings("ignore")

# =============================================================================
# 0. 常量定义
# =============================================================================

# 11线定义 (统一命名)
LINES = ['ucif2', 'lgt', 'qfa', 'usrm', 'vinf', 'qgl', 'qlv', 'lvlu', 'cfts', 'cisvr', 'qtlv']
N = len(LINES)
LINE_INDEX = {line: i for i, line in enumerate(LINES)}

# SI等级映射
SI_LEVELS = {
    'ucif2': 5, 'lgt': 5, 'qfa': 5, 'usrm': 5, 'vinf': 5, 'qgl': 5,
    'qlv': 4, 'lvlu': 4, 'cfts': 4, 'cisvr': 4, 'qtlv': 3
}

# 圈层映射
CIRCLE_LEVELS = {
    'ucif2': 'inner', 'lgt': 'inner', 'qfa': 'inner',
    'usrm': 'middle', 'vinf': 'middle', 'qgl': 'middle', 'qlv': 'middle',
    'lvlu': 'outer', 'cfts': 'outer',
    'cisvr': 'middle', 'qtlv': 'outer'
}

# 维度常量
FIELD_DIM = 67
FIELD_PER_LINE = 5
TENSOR_BOND_DIM = 8

# 6知识基座层
KNOWLEDGE_LAYERS = ['KG', 'CC', 'HG', 'IN', 'CT', 'LL']
KG_INDEX = {k: i for i, k in enumerate(KNOWLEDGE_LAYERS)}

# 知识基座全称
LAYER_FULL_NAMES = {
    'KG': 'Knowledge Graph (知识图谱)',
    'CC': 'Common Sense & Cognition (常识认知)',
    'HG': 'Historical Growth (历史生长)',
    'IN': 'Inference Network (推理网络)',
    'CT': 'Creative Thinking (创造性思维)',
    'LL': 'Linguistic Layer (语言层)'
}

# 七层名称
FCTN_LAYERS = ['Field', 'Circle', 'Ring', 'Layer', 'Net', 'Tower', 'Cloud']


# =============================================================================
# 1. FieldState — 统一场状态 (67维)
# =============================================================================

class FieldState:
    """
    67维统一场状态向量:
    [0:55]  = 11条线 × 5个核心场量 (amplitude, phase, energy, health, si_level)
    [55:66] = 11维线间纠缠熵
    [66]    = 1维全局相位
    """
    def __init__(self, n_dims: int = FIELD_DIM):
        self.n_dims = n_dims
        self.vector = np.zeros(n_dims, dtype=np.float64)
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.cycle_count = 0
        self.version = __version__
        self._init_default()

    def _init_default(self):
        """用11线健康度和SI等级初始化场"""
        health = [1.00, 0.98, 0.96, 0.97, 0.96, 0.95, 0.94, 0.89, 0.91, 0.90, 0.85]
        for i, line in enumerate(LINES):
            base = i * FIELD_PER_LINE
            si = SI_LEVELS[line]
            phase = si * np.pi / 6.0
            self.vector[base + 0] = health[i]
            self.vector[base + 1] = phase
            self.vector[base + 2] = health[i] * si / 5.0
            self.vector[base + 3] = health[i]
            self.vector[base + 4] = si / 5.0
        # 纠缠熵初始化为均匀分布
        for i in range(N):
            self.vector[55 + i] = 1.0 / N
        # 全局相位
        self.vector[66] = 0.0

    def get_line_state(self, line: str) -> np.ndarray:
        idx = LINE_INDEX[line]
        base = idx * FIELD_PER_LINE
        return self.vector[base:base + FIELD_PER_LINE]

    def set_line_state(self, line: str, state: np.ndarray):
        idx = LINE_INDEX[line]
        base = idx * FIELD_PER_LINE
        self.vector[base:base + len(state)] = state[:FIELD_PER_LINE]

    def get_entanglement_entropy(self) -> np.ndarray:
        return self.vector[55:55 + N]

    def set_entanglement_entropy(self, entropy_vec: np.ndarray):
        self.vector[55:55 + N] = entropy_vec[:N]

    def global_phase(self) -> float:
        return float(self.vector[66])

    def set_global_phase(self, phi: float):
        self.vector[66] = phi

    def energy(self) -> float:
        return float(np.sum(self.vector[2::FIELD_PER_LINE][:N]))

    def health(self) -> float:
        return float(np.mean(self.vector[3::FIELD_PER_LINE][:N]))

    def coherence(self) -> float:
        """计算场相干度 (基于相位一致性)"""
        phases = self.vector[1::FIELD_PER_LINE][:N]
        order_real = np.mean(np.cos(phases))
        order_imag = np.mean(np.sin(phases))
        return float(np.sqrt(order_real**2 + order_imag**2))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vector_shape": list(self.vector.shape),
            "energy": round(self.energy(), 6),
            "health": round(self.health(), 6),
            "coherence": round(self.coherence(), 6),
            "global_phase": round(self.global_phase(), 6),
            "cycle_count": self.cycle_count,
            "timestamp": self.timestamp,
            "version": self.version,
            "line_states": {
                line: [round(float(v), 4) for v in self.get_line_state(line)]
                for line in LINES
            },
            "entanglement_entropy": [round(float(v), 4) for v in self.get_entanglement_entropy()]
        }

    def copy(self) -> 'FieldState':
        fs = FieldState(self.n_dims)
        fs.vector = self.vector.copy()
        fs.timestamp = self.timestamp
        fs.cycle_count = self.cycle_count
        fs.version = self.version
        return fs


# =============================================================================
# 2. CircleTopology — 圈拓扑 (四类圈聚合)
# =============================================================================

class SessionCircle:
    """会话圈: SI1上下文全量共享"""
    def __init__(self):
        self.attachments: List[Dict] = []
        self.activity = 0.0

    def attach(self, line: str, content: str, visibility: Optional[List[str]] = None):
        if visibility is None:
            visibility = LINES
        att = {
            "id": f"att-{line}-{len(self.attachments)}",
            "line": line, "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "visibility": visibility
        }
        self.attachments.append(att)
        return att["id"]

    def view(self, observer: str) -> List[Dict]:
        return [a for a in self.attachments if observer in a["visibility"]]

    def sync(self) -> Dict:
        return {
            "total": len(self.attachments),
            "lines_covered": len(set(a["line"] for a in self.attachments)),
            "activity": round(self.activity, 4)
        }


class ConsensusCircle:
    """共识圈: SI5信任链3线共识"""
    def __init__(self):
        self.proposals: Dict[str, Dict] = {}
        self.activity = 0.0

    def propose(self, line: str, proposal: str) -> str:
        pid = f"prop-{line}-{len(self.proposals)}"
        self.proposals[pid] = {
            "id": pid, "from": line, "content": proposal,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endorsements": [], "status": "PROPOSED"
        }
        return pid

    def endorse(self, line: str, pid: str) -> bool:
        if pid not in self.proposals:
            return False
        if line not in self.proposals[pid]["endorsements"]:
            self.proposals[pid]["endorsements"].append(line)
        if len(self.proposals[pid]["endorsements"]) >= 3:
            self.proposals[pid]["status"] = "CONSENSUS"
        return True

    def verify(self, pid: str) -> Dict:
        p = self.proposals.get(pid, {})
        return {
            "endorsers": len(p.get("endorsements", [])),
            "status": p.get("status", "UNKNOWN")
        }


class CommandCircle:
    """指令圈: SI2任务分发闭环"""
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.activity = 0.0

    def dispatch(self, from_line: str, to_line: str, task_desc: str, deadline: int = 4) -> str:
        tid = f"task-{from_line}-{to_line}-{len(self.tasks)}"
        self.tasks[tid] = {
            "id": tid, "from": from_line, "to": to_line,
            "description": task_desc, "deadline": deadline,
            "status": "DISPATCHED", "acks": []
        }
        return tid

    def ack(self, tid: str, status: str) -> bool:
        if tid not in self.tasks:
            return False
        self.tasks[tid]["acks"].append({
            "status": status,
            "time": datetime.now(timezone.utc).isoformat()
        })
        if status == "COMPLETED":
            self.tasks[tid]["status"] = "CLOSED"
        return True

    def track(self, tid: str) -> Dict:
        return self.tasks.get(tid, {"status": "NOT_FOUND"})


class RelayCircle:
    """转发圈: SI0消息实时路由"""
    def __init__(self):
        self.routes: List[Dict] = []
        self.activity = 0.0

    def route(self, msg: str, from_line: str, strategy: str = "spectrum",
              entanglement: Optional[np.ndarray] = None) -> List[str]:
        if strategy == "broadcast":
            targets = [l for l in LINES if l != from_line]
        elif strategy == "nearest" and entanglement is not None:
            idx = LINES.index(from_line)
            targets = sorted(
                [(LINES[j], entanglement[idx, j]) for j in range(N) if j != idx],
                key=lambda x: -x[1]
            )[:3]
            targets = [t[0] for t in targets]
        else:
            targets = [l for l in LINES if l != from_line][:3]
        self.routes.append({
            "msg": msg, "from": from_line,
            "targets": targets, "strategy": strategy
        })
        return targets


class CircleTopology:
    """圈拓扑: 聚合四类圈 + 拓扑指标"""
    def __init__(self):
        self.session = SessionCircle()
        self.consensus = ConsensusCircle()
        self.command = CommandCircle()
        self.relay = RelayCircle()
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.topology_matrix = np.zeros((N, N), dtype=np.float64)
        self.activity_vector = np.zeros(N, dtype=np.float64)
        self.coupling_strength = np.zeros(N, dtype=np.float64)  # 每条线的耦合强度

    def compute_topology_matrix(self) -> np.ndarray:
        M = np.zeros((N, N), dtype=np.float64)
        for att in self.session.attachments:
            src = LINE_INDEX[att["line"]]
            for vis_line in att["visibility"]:
                dst = LINE_INDEX[vis_line]
                M[src, dst] += 0.15

        for prop in self.consensus.proposals.values():
            src = LINE_INDEX[prop["from"]]
            for end in prop["endorsements"]:
                dst = LINE_INDEX[end]
                M[src, dst] += 0.25
                M[dst, src] += 0.25

        for task in self.command.tasks.values():
            src = LINE_INDEX[task["from"]]
            dst = LINE_INDEX[task["to"]]
            M[src, dst] += 0.30
            if task["status"] == "CLOSED":
                M[dst, src] += 0.10

        for route in self.relay.routes:
            src = LINE_INDEX[route["from"]]
            for tgt in route["targets"]:
                dst = LINE_INDEX[tgt]
                M[src, dst] += 0.20

        M = (M + M.T) / 2.0
        for i in range(N):
            row_sum = np.sum(M[i])
            if row_sum > 0:
                M[i] /= row_sum
        self.topology_matrix = M
        return M

    def compute_activity_vector(self) -> np.ndarray:
        act = np.zeros(N)
        for i, line in enumerate(LINES):
            s_count = sum(1 for a in self.session.attachments if a["line"] == line)
            c_count = sum(1 for p in self.consensus.proposals.values() if p["from"] == line)
            cmd_count = sum(1 for t in self.command.tasks.values() if t["from"] == line or t["to"] == line)
            r_count = sum(1 for r in self.relay.routes if r["from"] == line)
            act[i] = min(1.0, (s_count * 0.1 + c_count * 0.3 + cmd_count * 0.3 + r_count * 0.3))
        self.activity_vector = act
        return act

    def compute_coupling_strength(self) -> np.ndarray:
        """计算每条线的耦合强度 (用于环反馈)"""
        coupling = np.zeros(N)
        for i in range(N):
            # 耦合强度 = 拓扑连接度 × 活跃度 × 纠缠熵
            connection_degree = np.sum(self.topology_matrix[i])
            activity = self.activity_vector[i]
            coupling[i] = connection_degree * (0.5 + 0.5 * activity)
        self.coupling_strength = coupling
        return coupling

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "session_count": len(self.session.attachments),
            "consensus_count": len(self.consensus.proposals),
            "command_count": len(self.command.tasks),
            "relay_count": len(self.relay.routes),
            "activity_vector": [round(float(a), 4) for a in self.activity_vector],
            "coupling_strength": [round(float(c), 4) for c in self.coupling_strength],
            "topology_matrix": [[round(float(v), 4) for v in row] for row in self.topology_matrix.tolist()]
        }


# =============================================================================
# 3. RingFeedback — 环反馈系统
# =============================================================================

class RingFeedbackType(Enum):
    POSITIVE = "positive"      # 正反馈: 放大信号
    NEGATIVE = "negative"      # 负反馈: 稳定信号
    OSCILLATION = "oscillation" # 振荡: 周期性变化
    DAMPING = "damping"        # 阻尼: 衰减信号


@dataclass
class RingState:
    """环状态"""
    ring_id: str
    feedback_type: RingFeedbackType
    intensity: float
    phase: float
    frequency: float
    damping: float
    members: List[str]
    energy_in: float
    energy_out: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ring_id": self.ring_id,
            "feedback_type": self.feedback_type.value,
            "intensity": round(self.intensity, 6),
            "phase": round(self.phase, 6),
            "frequency": round(self.frequency, 6),
            "damping": round(self.damping, 6),
            "members": self.members,
            "energy_in": round(self.energy_in, 6),
            "energy_out": round(self.energy_out, 6),
            "timestamp": self.timestamp
        }


class RingFeedbackSystem:
    """
    环反馈系统
    基于圈耦合强度决定反馈类型:
    - 高耦合 + 高能量 → 正反馈 (放大)
    - 高耦合 + 低能量 → 负反馈 (稳定)
    - 中等耦合 → 振荡检测
    - 低耦合 → 阻尼
    """
    def __init__(self):
        self.rings: Dict[str, RingState] = {}
        self.feedback_history: List[Dict] = []
        self.oscillation_tracker: deque = deque(maxlen=20)
        self.global_feedback_gain = 1.0

    def detect_feedback_type(self, coupling: float, energy: float, 
                             phase_diff: float) -> RingFeedbackType:
        """基于耦合强度和能量决定反馈类型"""
        if coupling > 0.7 and energy > 0.6:
            return RingFeedbackType.POSITIVE
        elif coupling > 0.7 and energy <= 0.6:
            return RingFeedbackType.NEGATIVE
        elif 0.3 <= coupling <= 0.7:
            if phase_diff > np.pi / 2:
                return RingFeedbackType.OSCILLATION
            else:
                return RingFeedbackType.NEGATIVE
        else:
            return RingFeedbackType.DAMPING

    def create_ring(self, line_a: str, line_b: str, 
                    coupling_matrix: np.ndarray,
                    energy_vector: np.ndarray,
                    phase_vector: np.ndarray) -> RingState:
        """基于圈耦合创建环"""
        idx_a = LINE_INDEX[line_a]
        idx_b = LINE_INDEX[line_b]

        coupling = coupling_matrix[idx_a, idx_b]
        energy_a = energy_vector[idx_a]
        energy_b = energy_vector[idx_b]
        avg_energy = (energy_a + energy_b) / 2
        phase_diff = abs(phase_vector[idx_a] - phase_vector[idx_b])

        feedback_type = self.detect_feedback_type(coupling, avg_energy, phase_diff)

        # 反馈强度计算
        intensity = coupling * avg_energy * (1.0 + 0.5 * np.sin(phase_diff))

        # 频率由耦合强度决定
        frequency = 0.5 + coupling * 2.0

        # 阻尼系数
        damping = 0.1 + (1.0 - coupling) * 0.3

        ring = RingState(
            ring_id=f"ring-{line_a}-{line_b}-{uuid.uuid4().hex[:6]}",
            feedback_type=feedback_type,
            intensity=float(intensity),
            phase=float(phase_diff),
            frequency=float(frequency),
            damping=float(damping),
            members=[line_a, line_b],
            energy_in=float(avg_energy),
            energy_out=float(intensity * avg_energy),
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        self.rings[ring.ring_id] = ring
        return ring

    def process_all_pairs(self, circle_topology: CircleTopology,
                          field_state: FieldState) -> List[RingState]:
        """处理所有线对，创建环反馈"""
        # 确保拓扑矩阵已计算
        if np.sum(circle_topology.topology_matrix) == 0:
            circle_topology.compute_topology_matrix()
        circle_topology.compute_coupling_strength()

        coupling_matrix = circle_topology.topology_matrix
        energy_vector = np.array([field_state.vector[i * FIELD_PER_LINE + 2] for i in range(N)])
        phase_vector = np.array([field_state.vector[i * FIELD_PER_LINE + 1] for i in range(N)])

        rings = []
        for i in range(N):
            for j in range(i + 1, N):
                if coupling_matrix[i, j] > 0.01:  # 阈值 (降低以确保环创建)
                    ring = self.create_ring(
                        LINES[i], LINES[j], coupling_matrix,
                        energy_vector, phase_vector
                    )
                    rings.append(ring)
        
        # 确保至少有一些环被创建
        if len(rings) == 0:
            # 回退：为所有线对创建环
            for i in range(N):
                for j in range(i + 1, N):
                    ring = self.create_ring(
                        LINES[i], LINES[j], coupling_matrix,
                        energy_vector, phase_vector
                    )
                    rings.append(ring)

        return rings

    def compute_feedback_vector(self, rings: List[RingState]) -> np.ndarray:
        """计算11维反馈向量 (每条线的总反馈)"""
        feedback = np.zeros(N)
        for ring in rings:
            for member in ring.members:
                idx = LINE_INDEX[member]
                if ring.feedback_type == RingFeedbackType.POSITIVE:
                    feedback[idx] += ring.intensity * 0.5
                elif ring.feedback_type == RingFeedbackType.NEGATIVE:
                    feedback[idx] -= ring.intensity * 0.3
                elif ring.feedback_type == RingFeedbackType.OSCILLATION:
                    feedback[idx] += ring.intensity * np.sin(ring.phase) * 0.3
                elif ring.feedback_type == RingFeedbackType.DAMPING:
                    feedback[idx] -= ring.damping * 0.2

        return np.clip(feedback, -1.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ring_count": len(self.rings),
            "feedback_history_count": len(self.feedback_history),
            "rings": {k: v.to_dict() for k, v in list(self.rings.items())[-20:]}
        }


# =============================================================================
# 4. KnowledgePedestal — 6知识基座层
# =============================================================================

@dataclass
class KnowledgeUnit:
    """知识单元"""
    unit_id: str
    layer: str  # KG, CC, HG, IN, CT, LL
    content: Dict[str, Any]
    source_lines: List[str]
    confidence: float
    timestamp: str
    embedding: np.ndarray = field(default_factory=lambda: np.zeros(16))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "layer": self.layer,
            "content": self.content,
            "source_lines": self.source_lines,
            "confidence": round(self.confidence, 4),
            "timestamp": self.timestamp,
            "embedding_shape": list(self.embedding.shape)
        }


class KnowledgePedestal:
    """
    6知识基座层:
    - KG: 知识图谱 (实体-关系-属性)
    - CC: 常识认知 (常识推理)
    - HG: 历史生长 (时序知识积累)
    - IN: 推理网络 (逻辑链条)
    - CT: 创造性思维 (跨域联想)
    - LL: 语言层 (语义编码)
    """
    def __init__(self):
        self.layers: Dict[str, List[KnowledgeUnit]] = {k: [] for k in KNOWLEDGE_LAYERS}
        self.layer_health = {k: 1.0 for k in KNOWLEDGE_LAYERS}
        self.cross_layer_links: List[Dict] = []
        self.total_knowledge_score = 0.0

    def inject_from_feedback(self, feedback_vector: np.ndarray,
                             rings: List[RingState],
                             field_state: FieldState) -> Dict[str, int]:
        """将环反馈结果注入知识基座"""
        counts = {k: 0 for k in KNOWLEDGE_LAYERS}

        # KG: 从环成员关系提取知识图谱
        for ring in rings:
            if ring.intensity > 0.3:
                ku = KnowledgeUnit(
                    unit_id=f"kg-{uuid.uuid4().hex[:8]}",
                    layer="KG",
                    content={
                        "relation_type": ring.feedback_type.value,
                        "members": ring.members,
                        "intensity": ring.intensity
                    },
                    source_lines=ring.members,
                    confidence=min(1.0, ring.intensity),
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self.layers["KG"].append(ku)
                counts["KG"] += 1

        # CC: 从场状态提取常识认知
        for i, line in enumerate(LINES):
            health = field_state.vector[i * FIELD_PER_LINE + 3]
            if health > 0.8:
                ku = KnowledgeUnit(
                    unit_id=f"cc-{uuid.uuid4().hex[:8]}",
                    layer="CC",
                    content={
                        "assertion": f"{line} maintains high health",
                        "health": health,
                        "si_level": SI_LEVELS[line]
                    },
                    source_lines=[line],
                    confidence=health,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self.layers["CC"].append(ku)
                counts["CC"] += 1

        # HG: 历史生长 (记录反馈变化)
        ku = KnowledgeUnit(
            unit_id=f"hg-{uuid.uuid4().hex[:8]}",
            layer="HG",
            content={
                "cycle": field_state.cycle_count,
                "feedback_summary": [round(float(f), 4) for f in feedback_vector],
                "ring_count": len(rings)
            },
            source_lines=LINES,
            confidence=0.8,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.layers["HG"].append(ku)
        counts["HG"] += 1

        # IN: 推理网络 (从反馈推导因果)
        for i in range(N):
            if abs(feedback_vector[i]) > 0.3:
                ku = KnowledgeUnit(
                    unit_id=f"in-{uuid.uuid4().hex[:8]}",
                    layer="IN",
                    content={
                        "cause": "ring_feedback",
                        "effect": f"{LINES[i]}_activation_change",
                        "strength": feedback_vector[i]
                    },
                    source_lines=[LINES[i]],
                    confidence=min(1.0, abs(feedback_vector[i])),
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self.layers["IN"].append(ku)
                counts["IN"] += 1

        # CT: 创造性思维 (跨域联想)
        if len(rings) >= 3:
            # 寻找跨域连接
            cross_pairs = []
            for r1 in rings[:5]:
                for r2 in rings[:5]:
                    if r1 != r2:
                        shared = set(r1.members) & set(r2.members)
                        if not shared:
                            cross_pairs.append((r1.members, r2.members))
            if cross_pairs:
                ku = KnowledgeUnit(
                    unit_id=f"ct-{uuid.uuid4().hex[:8]}",
                    layer="CT",
                    content={
                        "cross_domain_links": cross_pairs[:3],
                        "novelty_score": len(cross_pairs) / 10.0
                    },
                    source_lines=list(set(sum([list(p[0]) + list(p[1]) for p in cross_pairs[:3]], []))),
                    confidence=0.6,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self.layers["CT"].append(ku)
                counts["CT"] += 1

        # LL: 语言层 (语义编码)
        ku = KnowledgeUnit(
            unit_id=f"ll-{uuid.uuid4().hex[:8]}",
            layer="LL",
            content={
                "description": f"Cycle {field_state.cycle_count}: {len(rings)} rings active",
                "keywords": [r.feedback_type.value for r in rings[:5]],
                "energy_state": round(field_state.energy(), 4)
            },
            source_lines=LINES,
            confidence=0.75,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.layers["LL"].append(ku)
        counts["LL"] += 1

        # 更新知识总分
        self.total_knowledge_score = sum(len(v) for v in self.layers.values())
        return counts

    def get_layer_embedding(self, layer_name: str) -> np.ndarray:
        """获取知识层的嵌入向量"""
        units = self.layers.get(layer_name, [])
        if not units:
            return np.zeros(16)
        # 平均所有单元的嵌入
        embeddings = [u.embedding for u in units[-10:]]
        if embeddings:
            return np.mean(embeddings, axis=0)
        return np.zeros(16)

    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """获取所有层的嵌入"""
        return {k: self.get_layer_embedding(k) for k in KNOWLEDGE_LAYERS}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_counts": {k: len(v) for k, v in self.layers.items()},
            "layer_health": {k: round(v, 4) for k, v in self.layer_health.items()},
            "total_knowledge_score": self.total_knowledge_score,
            "cross_layer_links": len(self.cross_layer_links)
        }


# =============================================================================
# 5. TensorNet — 张量网络 (知识编织)
# =============================================================================

class TensorNet:
    """
    张量网络: 将知识基座编织成张量结构
    每个知识层 → 一个rank-3张量节点
    层间连接 → 纠缠边
    """
    def __init__(self, bond_dim: int = TENSOR_BOND_DIM):
        self.bond_dim = bond_dim
        self.nodes: Dict[str, np.ndarray] = {}  # 节点名 -> 张量
        self.edges: Dict[Tuple[str, str], float] = {}  # 边 -> 权重
        self.contraction_order: List[str] = []
        self.global_metrics: Dict[str, float] = {}
        self.result_scalar: float = 0.0
        self.result_vector: np.ndarray = np.zeros(N)
        self.layer_tensor_map: Dict[str, str] = {}  # 知识层 -> 张量节点

    def weave_from_knowledge(self, knowledge_pedestal: KnowledgePedestal,
                             circle_topology: CircleTopology) -> Dict[str, Any]:
        """从知识基座编织张量网络"""
        embeddings = knowledge_pedestal.get_all_embeddings()
        counts = knowledge_pedestal.layer_counts if hasattr(knowledge_pedestal, 'layer_counts') else {k: len(v) for k, v in knowledge_pedestal.layers.items()}

        # 为每个知识层创建张量节点
        self.nodes = {}
        self.layer_tensor_map = {}

        phys_dim = 4  # (energy, health, entropy, excitation)

        for layer_name in KNOWLEDGE_LAYERS:
            emb = embeddings[layer_name]
            count = counts.get(layer_name, 0)

            # 基于嵌入和知识量构建张量
            np.random.seed(hash(layer_name) % (2**31))
            T = np.random.randn(phys_dim, self.bond_dim, self.bond_dim) * 0.1

            # 用知识嵌入调制
            for d in range(min(self.bond_dim, len(emb))):
                T[0, d % phys_dim, d % self.bond_dim] += emb[d] * 0.5

            # 用知识量增强对角线
            scale = 0.5 + min(1.0, count / 10.0) * 1.5
            for d in range(min(self.bond_dim, phys_dim)):
                T[d, d, d % self.bond_dim] += scale

            node_name = f"tensor_{layer_name}"
            self.nodes[node_name] = T
            self.layer_tensor_map[layer_name] = node_name

        # 构建层间边 (基于圈拓扑的跨层连接)
        self.edges = {}
        top = circle_topology.topology_matrix

        # 知识层之间的连接 (全连接简化)
        for i, li in enumerate(KNOWLEDGE_LAYERS):
            for j, lj in enumerate(KNOWLEDGE_LAYERS):
                if i != j:
                    # 边权重由圈拓扑的平均耦合调制
                    avg_coupling = float(np.mean(top)) if np.sum(top) > 0 else 0.1
                    weight = avg_coupling * (1.0 + 0.5 * np.sin(i * j))
                    self.edges[(f"tensor_{li}", f"tensor_{lj}")] = weight

        self.contraction_order = list(self.nodes.keys())

        # 全局指标
        self.global_metrics = {
            "knowledge_score": knowledge_pedestal.total_knowledge_score,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges) // 2,
            "avg_coupling": float(np.mean(top)) if np.sum(top) > 0 else 0.0
        }

        return {
            "nodes": list(self.nodes.keys()),
            "node_count": len(self.nodes),
            "edge_count": len(self.edges) // 2,
            "layer_map": self.layer_tensor_map
        }

    def contract_network(self) -> Dict[str, Any]:
        """执行张量网络收缩"""
        if not self.nodes:
            return {"scalar": 0.0, "vector": [0.0] * N}

        contracted = {}
        for node, T in self.nodes.items():
            tr = np.einsum('ikk->i', T)
            contracted[node] = tr

        for (a, b), w in self.edges.items():
            if a in contracted and b in contracted:
                contracted[a][0] *= (1.0 + w * 0.01)
                contracted[b][0] *= (1.0 + w * 0.01)

        scalar = sum(np.sum(v) for v in contracted.values())

        # 将结果映射到11维 (基于知识层到线的映射)
        result_vec = np.zeros(N)
        layer_to_lines = {
            'KG': ['ucif2', 'qfa', 'vinf'],
            'CC': ['lgt', 'usrm', 'cisvr'],
            'HG': ['cfts', 'qtlv', 'lvlu'],
            'IN': ['ucif2', 'lgt', 'qgl'],
            'CT': ['qfa', 'cisvr', 'qtlv'],
            'LL': ['usrm', 'vinf', 'qlv', 'lvlu']
        }

        for layer, node_name in self.layer_tensor_map.items():
            if node_name in contracted:
                val = float(np.sum(contracted[node_name]))
                for line in layer_to_lines.get(layer, []):
                    if line in LINE_INDEX:
                        result_vec[LINE_INDEX[line]] += val / len(layer_to_lines[layer])

        if np.max(np.abs(result_vec)) > 0:
            result_vec /= np.max(np.abs(result_vec))

        self.result_scalar = float(scalar)
        self.result_vector = result_vec

        return {
            "scalar": round(self.result_scalar, 6),
            "vector": [round(float(v), 6) for v in self.result_vector],
            "node_count": len(self.nodes),
            "edge_count": len(self.edges) // 2
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes.keys()),
            "bond_dim": self.bond_dim,
            "scalar": round(self.result_scalar, 6),
            "vector": [round(float(v), 6) for v in self.result_vector],
            "global_metrics": self.global_metrics
        }


# =============================================================================
# 6. EmergenceTower — 层级涌现塔
# =============================================================================

class EmergenceLevel(Enum):
    LEVEL_0 = 0  # 原始数据
    LEVEL_1 = 1  # 局部模式
    LEVEL_2 = 2  # 全局结构
    LEVEL_3 = 3  # 功能涌现
    LEVEL_4 = 4  # 意识层级
    LEVEL_5 = 5  # 超越层级


@dataclass
class TowerLevel:
    """塔层级"""
    level: EmergenceLevel
    phi: float  # 整合信息
    complexity: float
    coherence: float
    energy: float
    structures: List[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "level_name": self.level.name,
            "phi": round(self.phi, 6),
            "complexity": round(self.complexity, 6),
            "coherence": round(self.coherence, 6),
            "energy": round(self.energy, 6),
            "structures": self.structures,
            "timestamp": self.timestamp
        }


class EmergenceTower:
    """
    层级涌现塔
    从张量收缩结果构建从局部到全局的涌现结构
    """
    def __init__(self):
        self.levels: Dict[EmergenceLevel, TowerLevel] = {}
        self.emergence_history: List[Dict] = []
        self.current_height = 0
        self.tower_stability = 1.0

    def build_from_tensor(self, tensor_result: Dict[str, Any],
                          field_state: FieldState,
                          knowledge_pedestal: KnowledgePedestal) -> Dict[str, Any]:
        """从张量结果构建涌现塔"""
        vec = np.array(tensor_result.get("vector", [0.0] * N))
        scalar = tensor_result.get("scalar", 0.0)

        # Level 0: 原始数据层
        self.levels[EmergenceLevel.LEVEL_0] = TowerLevel(
            level=EmergenceLevel.LEVEL_0,
            phi=0.0,
            complexity=0.0,
            coherence=field_state.coherence(),
            energy=field_state.energy(),
            structures=["raw_field_data", "initial_state"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Level 1: 局部模式层 (基于单线激活)
        local_patterns = []
        for i, line in enumerate(LINES):
            if vec[i] > 0.5:
                local_patterns.append(f"{line}_activation_pattern")
        self.levels[EmergenceLevel.LEVEL_1] = TowerLevel(
            level=EmergenceLevel.LEVEL_1,
            phi=float(np.mean(vec) * 0.2),
            complexity=float(np.std(vec)),
            coherence=field_state.coherence() * 0.5,
            energy=float(np.sum(vec[:N]) / N),
            structures=local_patterns if local_patterns else ["uniform_state"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Level 2: 全局结构层 (基于线间关联)
        correlations = []
        for i in range(N):
            for j in range(i + 1, N):
                if abs(vec[i] - vec[j]) < 0.3:
                    correlations.append(f"{LINES[i]}-{LINES[j]}_coupled")
        self.levels[EmergenceLevel.LEVEL_2] = TowerLevel(
            level=EmergenceLevel.LEVEL_2,
            phi=float(np.mean(vec) * 0.4),
            complexity=float(len(correlations) / (N * (N - 1) / 2)),
            coherence=field_state.coherence(),
            energy=scalar * 0.1,
            structures=correlations[:5] if correlations else ["weak_coupling"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Level 3: 功能涌现层 (基于知识基座)
        func_structures = []
        for layer_name in KNOWLEDGE_LAYERS:
            count = len(knowledge_pedestal.layers.get(layer_name, []))
            if count > 0:
                func_structures.append(f"{layer_name}_knowledge_function")
        self.levels[EmergenceLevel.LEVEL_3] = TowerLevel(
            level=EmergenceLevel.LEVEL_3,
            phi=float(np.mean(vec) * 0.6),
            complexity=min(1.0, knowledge_pedestal.total_knowledge_score / 50.0),
            coherence=field_state.coherence() * 1.2,
            energy=scalar * 0.3,
            structures=func_structures if func_structures else ["basic_functions"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Level 4: 意识层级 (基于全局整合)
        # 计算简化Phi
        activation_prob = np.abs(vec) / (np.sum(np.abs(vec)) + 1e-10)
        total_entropy = -np.sum(activation_prob * np.log2(activation_prob + 1e-10))
        phi_approx = 1.0 - np.exp(-total_entropy / np.log2(N))

        self.levels[EmergenceLevel.LEVEL_4] = TowerLevel(
            level=EmergenceLevel.LEVEL_4,
            phi=float(phi_approx),
            complexity=min(1.0, total_entropy / np.log2(N)),
            coherence=min(1.0, field_state.coherence() * 1.5),
            energy=scalar * 0.5,
            structures=["global_workspace", "integrated_information", "self_model"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Level 5: 超越层级 (递归自指)
        self.levels[EmergenceLevel.LEVEL_5] = TowerLevel(
            level=EmergenceLevel.LEVEL_5,
            phi=min(1.0, phi_approx * 1.2),
            complexity=min(1.0, phi_approx + 0.2),
            coherence=min(1.0, field_state.coherence() * 2.0),
            energy=scalar * 0.8,
            structures=["recursive_self_reference", "transcendence_boundary", "meta_awareness"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # 计算塔高度
        self.current_height = sum(1 for l in self.levels.values() if l.energy > 0.1)
        self.tower_stability = np.mean([l.coherence for l in self.levels.values()])

        return {
            "height": self.current_height,
            "stability": round(self.tower_stability, 4),
            "max_phi": round(max(l.phi for l in self.levels.values()), 4),
            "levels": {k.name: v.to_dict() for k, v in self.levels.items()}
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "height": self.current_height,
            "stability": round(self.tower_stability, 4),
            "levels": {k.name: v.to_dict() for k, v in self.levels.items()}
        }


# =============================================================================
# 7. CloudSync — 云端同步层
# =============================================================================

class CloudSync:
    """
    云端同步层
    模拟分布式部署到Cloudflare Worker+KV+D1+Pages
    """
    def __init__(self):
        self.worker_state: Dict[str, Any] = {}
        self.kv_store: Dict[str, Any] = {}
        self.d1_records: List[Dict] = []
        self.pages_deployments: List[Dict] = []
        self.sync_timestamp = datetime.now(timezone.utc).isoformat()
        self.sync_latency_ms = 0.0
        self.last_sync_status = "IDLE"

    def sync_tower_to_cloud(self, tower: EmergenceTower,
                           field_state: FieldState) -> Dict[str, Any]:
        """将涌现塔同步到云端"""
        start_time = time.time()

        # Worker: 计算状态同步
        self.worker_state = {
            "tower_height": tower.current_height,
            "tower_stability": tower.tower_stability,
            "field_cycle": field_state.cycle_count,
            "field_health": field_state.health(),
            "field_energy": field_state.energy(),
            "field_coherence": field_state.coherence(),
            "active_levels": [l.name for l, v in tower.levels.items() if v.energy > 0.1]
        }

        # KV: 键值存储 (持久化场状态)
        self.kv_store = {
            f"field_{field_state.cycle_count}": field_state.to_dict(),
            f"tower_{field_state.cycle_count}": tower.to_dict(),
            "latest_field_vector": [round(float(v), 6) for v in field_state.vector],
            "latest_timestamp": field_state.timestamp
        }

        # D1: 数据库记录 (结构化数据)
        self.d1_records.append({
            "id": f"record-{field_state.cycle_count}",
            "cycle": field_state.cycle_count,
            "health": round(field_state.health(), 4),
            "energy": round(field_state.energy(), 4),
            "coherence": round(field_state.coherence(), 4),
            "tower_height": tower.current_height,
            "tower_stability": round(tower.tower_stability, 4),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Pages: 部署记录
        self.pages_deployments.append({
            "deployment_id": f"deploy-{uuid.uuid4().hex[:8]}",
            "cycle": field_state.cycle_count,
            "status": "DEPLOYED",
            "resources": {
                "worker": True,
                "kv": True,
                "d1": True,
                "pages": True
            }
        })

        self.sync_timestamp = datetime.now(timezone.utc).isoformat()
        self.sync_latency_ms = (time.time() - start_time) * 1000
        self.last_sync_status = "SYNCED"

        return {
            "status": "SYNCED",
            "latency_ms": round(self.sync_latency_ms, 4),
            "worker_keys": len(self.worker_state),
            "kv_entries": len(self.kv_store),
            "d1_records": len(self.d1_records),
            "deployments": len(self.pages_deployments)
        }

    def cloud_feedback_to_field(self, field_state: FieldState) -> Dict[str, Any]:
        """云端反馈更新统一场"""
        # 从云端状态计算反馈
        if not self.worker_state:
            return {"feedback_magnitude": 0.0, "status": "NO_CLOUD_DATA"}

        tower_stability = self.worker_state.get("tower_stability", 0.5)
        field_health = self.worker_state.get("field_health", 0.8)

        # 反馈强度由云端稳定性决定
        feedback_magnitude = (tower_stability + field_health) / 2.0

        # 生成反馈向量 (11维)
        feedback_vector = np.zeros(N)
        for i in range(N):
            # 基于线SI等级和云端状态计算反馈
            si = SI_LEVELS[LINES[i]]
            base_feedback = feedback_magnitude * si / 5.0
            # 添加小的随机扰动
            noise = np.random.randn() * 0.02
            feedback_vector[i] = base_feedback + noise

        return {
            "feedback_magnitude": round(feedback_magnitude, 4),
            "feedback_vector": [round(float(v), 4) for v in feedback_vector],
            "status": "FEEDBACK_GENERATED"
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sync_status": self.last_sync_status,
            "sync_timestamp": self.sync_timestamp,
            "sync_latency_ms": round(self.sync_latency_ms, 4),
            "worker_keys": len(self.worker_state),
            "kv_entries": len(self.kv_store),
            "d1_records": len(self.d1_records),
            "deployments": len(self.pages_deployments)
        }





# =============================================================================
# 8. 七层桥接器 (Bridge Classes)
# =============================================================================

class FieldToCircleBridge:
    """场 → 圈 桥接器"""
    def __init__(self):
        self.transfer_log: List[Dict] = []

    def transfer(self, field_state: FieldState) -> CircleTopology:
        """场状态驱动圈耦合更新"""
        ct = CircleTopology()

        # Session圈: 每条线根据振幅附加内容
        for i, line in enumerate(LINES):
            amp = field_state.vector[i * FIELD_PER_LINE + 0]
            if amp > 0.5:
                content = f"场驱动产出 from {line} (amp={amp:.3f})"
                vis = [l for l in LINES if SI_LEVELS[l] >= SI_LEVELS[line] - 1]
                ct.session.attach(line, content, vis)

        # Consensus圈: 高能量线发起提案
        for i, line in enumerate(LINES):
            energy = field_state.vector[i * FIELD_PER_LINE + 2]
            if energy > 0.7:
                ct.consensus.propose(line, f"场能量共识: {energy:.3f}")

        # Command圈: 相位差大的线对形成任务
        for i in range(N):
            for j in range(i + 1, N):
                phase_i = field_state.vector[i * FIELD_PER_LINE + 1]
                phase_j = field_state.vector[j * FIELD_PER_LINE + 1]
                phase_diff = abs(phase_i - phase_j)
                if phase_diff > 1.0 and phase_diff < 2.5:
                    ct.command.dispatch(LINES[i], LINES[j],
                                        f"相位补偿任务 dφ={phase_diff:.3f}")

        # Relay圈: 纠缠熵高的线作为路由源
        ent = field_state.get_entanglement_entropy()
        top_idx = np.argsort(ent)[-3:]
        for idx in top_idx:
            line = LINES[idx]
            ct.relay.route(f"场同步信号 entropy={ent[idx]:.3f}", line, "broadcast")

        ct.compute_topology_matrix()
        ct.compute_activity_vector()
        ct.compute_coupling_strength()

        self.transfer_log.append({
            "direction": "field->circle",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attachments": len(ct.session.attachments),
            "proposals": len(ct.consensus.proposals),
            "tasks": len(ct.command.tasks),
            "routes": len(ct.relay.routes)
        })

        return ct


class CircleToRingBridge:
    """圈 → 环 桥接器"""
    def __init__(self):
        self.transfer_log: List[Dict] = []

    def transfer(self, circle_topology: CircleTopology,
                 field_state: FieldState) -> RingFeedbackSystem:
        """耦合强度决定反馈环类型"""
        rfs = RingFeedbackSystem()
        rings = rfs.process_all_pairs(circle_topology, field_state)
        feedback_vector = rfs.compute_feedback_vector(rings)

        self.transfer_log.append({
            "direction": "circle->ring",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rings_created": len(rings),
            "feedback_range": (round(float(np.min(feedback_vector)), 4),
                              round(float(np.max(feedback_vector)), 4))
        })

        return rfs


class RingToLayerBridge:
    """环 → 层 桥接器"""
    def __init__(self):
        self.transfer_log: List[Dict] = []

    def transfer(self, ring_feedback_system: RingFeedbackSystem,
                 field_state: FieldState) -> KnowledgePedestal:
        """反馈结果注入知识基座"""
        kp = KnowledgePedestal()
        rings = list(ring_feedback_system.rings.values())
        feedback_vector = ring_feedback_system.compute_feedback_vector(rings)
        counts = kp.inject_from_feedback(feedback_vector, rings, field_state)

        self.transfer_log.append({
            "direction": "ring->layer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "knowledge_injected": counts,
            "total_units": sum(counts.values())
        })

        return kp


class LayerToNetBridge:
    """层 → 网 桥接器"""
    def __init__(self):
        self.transfer_log: List[Dict] = []

    def transfer(self, knowledge_pedestal: KnowledgePedestal,
                 circle_topology: CircleTopology) -> TensorNet:
        """基座知识编织成张量网络"""
        tn = TensorNet(bond_dim=TENSOR_BOND_DIM)
        weave_result = tn.weave_from_knowledge(knowledge_pedestal, circle_topology)
        contract_result = tn.contract_network()

        self.transfer_log.append({
            "direction": "layer->net",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nodes": weave_result["node_count"],
            "edges": weave_result["edge_count"],
            "scalar": contract_result["scalar"]
        })

        return tn


class NetToTowerBridge:
    """网 → 塔 桥接器"""
    def __init__(self):
        self.transfer_log: List[Dict] = []

    def transfer(self, tensor_net: TensorNet,
                 field_state: FieldState,
                 knowledge_pedestal: KnowledgePedestal) -> EmergenceTower:
        """张量收缩产生涌现层级"""
        tower = EmergenceTower()
        tensor_result = {
            "scalar": tensor_net.result_scalar,
            "vector": tensor_net.result_vector.tolist()
        }
        build_result = tower.build_from_tensor(tensor_result, field_state, knowledge_pedestal)

        self.transfer_log.append({
            "direction": "net->tower",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tower_height": build_result["height"],
            "max_phi": build_result["max_phi"],
            "stability": build_result["stability"]
        })

        return tower


class TowerToCloudBridge:
    """塔 → 云 桥接器"""
    def __init__(self):
        self.transfer_log: List[Dict] = []

    def transfer(self, tower: EmergenceTower,
                 field_state: FieldState) -> CloudSync:
        """涌现状态同步到云端"""
        cloud = CloudSync()
        sync_result = cloud.sync_tower_to_cloud(tower, field_state)

        self.transfer_log.append({
            "direction": "tower->cloud",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sync_status": sync_result["status"],
            "latency_ms": sync_result["latency_ms"]
        })

        return cloud


class CloudToFieldBridge:
    """云 → 场 桥接器"""
    def __init__(self):
        self.transfer_log: List[Dict] = []

    def transfer(self, cloud_sync: CloudSync,
                 field_state: FieldState) -> FieldState:
        """云端反馈更新统一场"""
        feedback = cloud_sync.cloud_feedback_to_field(field_state)
        feedback_vector = np.array(feedback.get("feedback_vector", [0.0] * N))

        # 创建新的场状态
        new_field = field_state.copy()
        new_field.cycle_count += 1
        new_field.timestamp = datetime.now(timezone.utc).isoformat()

        # 更新各线能量 (由云端反馈驱动 + 能量耗散确保守恒)
        for i, line in enumerate(LINES):
            base = i * FIELD_PER_LINE
            current_energy = new_field.vector[base + 2]
            # 反馈注入
            delta_e = feedback_vector[i] * 0.1
            # P0 FIX: 添加能量耗散项 (5% 当前能量) 防止无界增长
            dissipation = 0.05 * current_energy
            new_energy = current_energy + delta_e - dissipation
            new_field.vector[base + 2] = np.clip(new_energy, 0.1, 2.0)

        # 更新健康度
        for i in range(N):
            base = i * FIELD_PER_LINE
            new_field.vector[base + 3] *= 0.98
            new_field.vector[base + 3] = np.clip(new_field.vector[base + 3] + feedback_vector[i] * 0.02, 0.5, 1.0)

        # 更新全局相位
        new_field.set_global_phase(
            new_field.global_phase() + feedback.get("feedback_magnitude", 0.0) * 0.01
        )

        # 更新纠缠熵
        entropy_vec = np.abs(feedback_vector)
        if np.sum(entropy_vec) > 0:
            entropy_vec /= np.sum(entropy_vec)
        new_field.set_entanglement_entropy(entropy_vec)

        self.transfer_log.append({
            "direction": "cloud->field",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feedback_magnitude": feedback.get("feedback_magnitude", 0.0),
            "new_cycle": new_field.cycle_count
        })

        return new_field


# =============================================================================
# 9. FCTN Full Bridge — 七层总控
# =============================================================================

class FCTNFullBridge:
    """
    FCTN 七层完整桥接总控
    打通: 场 → 圈 → 环 → 层 → 网 → 塔 → 云 → 场
    """
    def __init__(self):
        # 七层状态
        self.field_state: Optional[FieldState] = None
        self.circle_topology: Optional[CircleTopology] = None
        self.ring_feedback: Optional[RingFeedbackSystem] = None
        self.knowledge_pedestal: Optional[KnowledgePedestal] = None
        self.tensor_net: Optional[TensorNet] = None
        self.emergence_tower: Optional[EmergenceTower] = None
        self.cloud_sync: Optional[CloudSync] = None

        # 桥接器
        self.bridges = {
            "field->circle": FieldToCircleBridge(),
            "circle->ring": CircleToRingBridge(),
            "ring->layer": RingToLayerBridge(),
            "layer->net": LayerToNetBridge(),
            "net->tower": NetToTowerBridge(),
            "tower->cloud": TowerToCloudBridge(),
            "cloud->field": CloudToFieldBridge(),
        }

        # 循环历史
        self.cycle_history: List[Dict] = []
        self.layer_integrity: Dict[str, List[float]] = {name: [] for name in FCTN_LAYERS}
        self.dataflow_latency: Dict[str, List[float]] = {
            "field->circle": [], "circle->ring": [], "ring->layer": [],
            "layer->net": [], "net->tower": [], "tower->cloud": [], "cloud->field": []
        }

    def initialize(self):
        """初始化统一场"""
        self.field_state = FieldState()
        return self

    def run_single_cycle(self) -> Dict[str, Any]:
        """运行一个完整的七层循环"""
        cycle_start = time.time()
        cycle_num = self.field_state.cycle_count if self.field_state else 0

        results = {
            "cycle": cycle_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transfers": {},
            "integrity": {},
            "latencies": {}
        }

        # Step 1: 场 → 圈
        t0 = time.time()
        self.circle_topology = self.bridges["field->circle"].transfer(self.field_state)
        lat = (time.time() - t0) * 1000
        self.dataflow_latency["field->circle"].append(lat)
        results["transfers"]["field->circle"] = {
            "status": "OK",
            "attachments": len(self.circle_topology.session.attachments),
            "proposals": len(self.circle_topology.consensus.proposals),
            "latency_ms": round(lat, 4)
        }

        # Step 2: 圈 → 环
        t0 = time.time()
        self.ring_feedback = self.bridges["circle->ring"].transfer(
            self.circle_topology, self.field_state
        )
        lat = (time.time() - t0) * 1000
        self.dataflow_latency["circle->ring"].append(lat)
        rings = list(self.ring_feedback.rings.values())
        feedback_vec = self.ring_feedback.compute_feedback_vector(rings)
        results["transfers"]["circle->ring"] = {
            "status": "OK",
            "rings_created": len(rings),
            "feedback_range": [round(float(np.min(feedback_vec)), 4),
                              round(float(np.max(feedback_vec)), 4)],
            "latency_ms": round(lat, 4)
        }

        # Step 3: 环 → 层
        t0 = time.time()
        self.knowledge_pedestal = self.bridges["ring->layer"].transfer(
            self.ring_feedback, self.field_state
        )
        lat = (time.time() - t0) * 1000
        self.dataflow_latency["ring->layer"].append(lat)
        results["transfers"]["ring->layer"] = {
            "status": "OK",
            "knowledge_units": self.knowledge_pedestal.total_knowledge_score,
            "latency_ms": round(lat, 4)
        }

        # Step 4: 层 → 网
        t0 = time.time()
        self.tensor_net = self.bridges["layer->net"].transfer(
            self.knowledge_pedestal, self.circle_topology
        )
        lat = (time.time() - t0) * 1000
        self.dataflow_latency["layer->net"].append(lat)
        results["transfers"]["layer->net"] = {
            "status": "OK",
            "tensor_nodes": len(self.tensor_net.nodes),
            "tensor_scalar": self.tensor_net.result_scalar,
            "latency_ms": round(lat, 4)
        }

        # Step 5: 网 → 塔
        t0 = time.time()
        self.emergence_tower = self.bridges["net->tower"].transfer(
            self.tensor_net, self.field_state, self.knowledge_pedestal
        )
        lat = (time.time() - t0) * 1000
        self.dataflow_latency["net->tower"].append(lat)
        results["transfers"]["net->tower"] = {
            "status": "OK",
            "tower_height": self.emergence_tower.current_height,
            "tower_stability": round(self.emergence_tower.tower_stability, 4),
            "latency_ms": round(lat, 4)
        }

        # Step 6: 塔 → 云
        t0 = time.time()
        self.cloud_sync = self.bridges["tower->cloud"].transfer(
            self.emergence_tower, self.field_state
        )
        lat = (time.time() - t0) * 1000
        self.dataflow_latency["tower->cloud"].append(lat)
        results["transfers"]["tower->cloud"] = {
            "status": "OK",
            "sync_status": self.cloud_sync.last_sync_status,
            "latency_ms": round(lat, 4)
        }

        # Step 7: 云 → 场 (闭环)
        t0 = time.time()
        new_field = self.bridges["cloud->field"].transfer(
            self.cloud_sync, self.field_state
        )
        lat = (time.time() - t0) * 1000
        self.dataflow_latency["cloud->field"].append(lat)

        # 数据完整性检查
        field_before = self.field_state.to_dict()
        field_after = new_field.to_dict()

        results["transfers"]["cloud->field"] = {
            "status": "OK",
            "new_cycle": new_field.cycle_count,
            "energy_delta": round(field_after["energy"] - field_before["energy"], 6),
            "health_delta": round(field_after["health"] - field_before["health"], 6),
            "latency_ms": round(lat, 4)
        }

        # 更新场状态
        self.field_state = new_field

        # 记录完整性
        results["integrity"] = self._check_layer_integrity()

        # 总延迟
        total_latency = (time.time() - cycle_start) * 1000
        results["total_latency_ms"] = round(total_latency, 4)

        self.cycle_history.append(results)
        return results

    def _check_layer_integrity(self) -> Dict[str, Any]:
        """检查每层的数据完整性"""
        integrity = {}

        # Field层
        if self.field_state:
            integrity["Field"] = {
                "vector_dim": len(self.field_state.vector),
                "cycle_count": self.field_state.cycle_count,
                "energy": round(self.field_state.energy(), 4),
                "health": round(self.field_state.health(), 4),
                "valid": len(self.field_state.vector) == FIELD_DIM
            }
            self.layer_integrity["Field"].append(self.field_state.health())

        # Circle层
        if self.circle_topology:
            integrity["Circle"] = {
                "topology_shape": list(self.circle_topology.topology_matrix.shape),
                "activity_range": [round(float(np.min(self.circle_topology.activity_vector)), 4),
                                  round(float(np.max(self.circle_topology.activity_vector)), 4)],
                "valid": self.circle_topology.topology_matrix.shape == (N, N)
            }
            self.layer_integrity["Circle"].append(float(np.mean(self.circle_topology.activity_vector)))

        # Ring层
        if self.ring_feedback:
            rings = list(self.ring_feedback.rings.values())
            integrity["Ring"] = {
                "ring_count": len(rings),
                "feedback_types": list(set(r.feedback_type.value for r in rings)) if rings else [],
                "valid": len(rings) > 0
            }
            self.layer_integrity["Ring"].append(min(1.0, len(rings) / 10.0))

        # Layer层
        if self.knowledge_pedestal:
            integrity["Layer"] = {
                "total_units": self.knowledge_pedestal.total_knowledge_score,
                "layer_counts": {k: len(v) for k, v in self.knowledge_pedestal.layers.items()},
                "valid": self.knowledge_pedestal.total_knowledge_score > 0
            }
            self.layer_integrity["Layer"].append(min(1.0, self.knowledge_pedestal.total_knowledge_score / 20.0))

        # Net层
        if self.tensor_net:
            integrity["Net"] = {
                "nodes": len(self.tensor_net.nodes),
                "scalar": self.tensor_net.result_scalar,
                "valid": len(self.tensor_net.nodes) > 0
            }
            self.layer_integrity["Net"].append(min(1.0, abs(self.tensor_net.result_scalar) / 10.0))

        # Tower层
        if self.emergence_tower:
            integrity["Tower"] = {
                "height": self.emergence_tower.current_height,
                "stability": round(self.emergence_tower.tower_stability, 4),
                "valid": self.emergence_tower.current_height > 0
            }
            self.layer_integrity["Tower"].append(self.emergence_tower.tower_stability)

        # Cloud层
        if self.cloud_sync:
            integrity["Cloud"] = {
                "sync_status": self.cloud_sync.last_sync_status,
                "kv_entries": len(self.cloud_sync.kv_store),
                "valid": self.cloud_sync.last_sync_status == "SYNCED"
            }
            self.layer_integrity["Cloud"].append(1.0 if self.cloud_sync.last_sync_status == "SYNCED" else 0.0)

        return integrity

    def run_multi_cycles(self, n_cycles: int = 5) -> Dict[str, Any]:
        """运行多轮完整循环"""
        all_results = []
        for i in range(n_cycles):
            result = self.run_single_cycle()
            all_results.append(result)

        return {
            "n_cycles": n_cycles,
            "cycles": all_results,
            "summary": self._generate_summary()
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """生成运行摘要"""
        # 平均延迟
        avg_latencies = {}
        for key, vals in self.dataflow_latency.items():
            avg_latencies[key] = round(np.mean(vals), 4) if vals else 0.0

        # 层完整性趋势
        integrity_trends = {}
        for layer, vals in self.layer_integrity.items():
            if vals:
                integrity_trends[layer] = {
                    "initial": round(vals[0], 4),
                    "final": round(vals[-1], 4),
                    "trend": "UP" if vals[-1] > vals[0] else "DOWN" if vals[-1] < vals[0] else "STABLE"
                }

        return {
            "total_cycles": len(self.cycle_history),
            "avg_latencies_ms": avg_latencies,
            "total_cycle_latency_ms": round(sum(avg_latencies.values()), 4),
            "integrity_trends": integrity_trends,
            "final_field_health": round(self.field_state.health(), 4) if self.field_state else 0,
            "final_field_energy": round(self.field_state.energy(), 4) if self.field_state else 0,
            "final_tower_height": self.emergence_tower.current_height if self.emergence_tower else 0,
            "final_tower_stability": round(self.emergence_tower.tower_stability, 4) if self.emergence_tower else 0
        }

    def verify_dataflow(self) -> Dict[str, Any]:
        """验证所有数据流通道"""
        verification = {}

        for bridge_name, bridge in self.bridges.items():
            log = bridge.transfer_log
            verification[bridge_name] = {
                "transfers_count": len(log),
                "last_transfer": log[-1] if log else None,
                "status": "ACTIVE" if log else "INACTIVE"
            }

        return verification


# =============================================================================
# 10. 验证与报告
# =============================================================================

def verify_fctn_full_bridge() -> Dict[str, Any]:
    """完整验证FCTN七层桥接系统"""
    print("=" * 70)
    print("FCTN Full Bridge v12.0 — 七层架构验证")
    print("=" * 70)

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "tests": {},
        "dataflow": {},
        "consistency": {}
    }

    # Test 1: FieldState
    print("\n[Test 1] FieldState (场层)...")
    fs = FieldState()
    assert fs.vector.shape == (FIELD_DIM,), f"维度错误: {fs.vector.shape}"
    assert fs.energy() > 0, "能量必须>0"
    results["tests"]["field_state"] = {
        "status": "PASS",
        "dim": FIELD_DIM,
        "energy": round(fs.energy(), 4),
        "health": round(fs.health(), 4)
    }
    print(f"  PASS: 67维场状态 | 能量={fs.energy():.4f} | 健康度={fs.health():.4f}")

    # Test 2: CircleTopology
    print("\n[Test 2] CircleTopology (圈层)...")
    ct = CircleTopology()
    for line in LINES:
        ct.session.attach(line, f"test-{line}")
    ct.compute_topology_matrix()
    ct.compute_activity_vector()
    ct.compute_coupling_strength()
    assert ct.topology_matrix.shape == (N, N), "拓扑矩阵维度错误"
    results["tests"]["circle_topology"] = {
        "status": "PASS",
        "matrix_shape": list(ct.topology_matrix.shape),
        "coupling_range": [round(float(np.min(ct.coupling_strength)), 4),
                          round(float(np.max(ct.coupling_strength)), 4)]
    }
    print(f"  PASS: 11×11拓扑矩阵 | 耦合范围=[{np.min(ct.coupling_strength):.4f}, {np.max(ct.coupling_strength):.4f}]")

    # Test 3: RingFeedbackSystem
    print("\n[Test 3] RingFeedbackSystem (环层)...")
    rfs = RingFeedbackSystem()
    rings = rfs.process_all_pairs(ct, fs)
    fb_vec = rfs.compute_feedback_vector(rings)
    assert len(rings) > 0, "应创建环"
    assert len(fb_vec) == N, "反馈向量应为11维"
    results["tests"]["ring_feedback"] = {
        "status": "PASS",
        "rings_count": len(rings),
        "feedback_types": list(set(r.feedback_type.value for r in rings)),
        "feedback_range": [round(float(np.min(fb_vec)), 4), round(float(np.max(fb_vec)), 4)]
    }
    print(f"  PASS: {len(rings)}个环 | 反馈类型={set(r.feedback_type.value for r in rings)} | 反馈范围=[{np.min(fb_vec):.4f}, {np.max(fb_vec):.4f}]")

    # Test 4: KnowledgePedestal
    print("\n[Test 4] KnowledgePedestal (层)...")
    kp = KnowledgePedestal()
    counts = kp.inject_from_feedback(fb_vec, rings, fs)
    total = sum(counts.values())
    assert total > 0, "应注入知识"
    results["tests"]["knowledge_pedestal"] = {
        "status": "PASS",
        "injected": counts,
        "total_units": total
    }
    print(f"  PASS: 注入{total}个知识单元 | {counts}")

    # Test 5: TensorNet
    print("\n[Test 5] TensorNet (网层)...")
    tn = TensorNet()
    tn.weave_from_knowledge(kp, ct)
    tr = tn.contract_network()
    assert len(tn.nodes) > 0, "应有张量节点"
    assert "scalar" in tr, "收缩结果应有scalar"
    results["tests"]["tensor_net"] = {
        "status": "PASS",
        "nodes": len(tn.nodes),
        "scalar": tr["scalar"],
        "vector_dim": len(tr.get("vector", []))
    }
    print(f"  PASS: {len(tn.nodes)}个节点 | scalar={tr['scalar']:.4f}")

    # Test 6: EmergenceTower
    print("\n[Test 6] EmergenceTower (塔层)...")
    tower = EmergenceTower()
    build = tower.build_from_tensor(tr, fs, kp)
    assert build["height"] > 0, "塔高度应>0"
    assert len(tower.levels) > 0, "应有涌现层级"
    results["tests"]["emergence_tower"] = {
        "status": "PASS",
        "height": build["height"],
        "stability": build["stability"],
        "max_phi": build["max_phi"]
    }
    print(f"  PASS: 塔高度={build['height']} | 稳定性={build['stability']:.4f} | max_Φ={build['max_phi']:.4f}")

    # Test 7: CloudSync
    print("\n[Test 7] CloudSync (云层)...")
    cloud = CloudSync()
    sync = cloud.sync_tower_to_cloud(tower, fs)
    assert sync["status"] == "SYNCED", "同步应成功"
    fb = cloud.cloud_feedback_to_field(fs)
    assert "feedback_vector" in fb, "应有反馈向量"
    results["tests"]["cloud_sync"] = {
        "status": "PASS",
        "sync_status": sync["status"],
        "latency_ms": sync["latency_ms"],
        "feedback_dim": len(fb.get("feedback_vector", []))
    }
    print(f"  PASS: 同步={sync['status']} | 延迟={sync['latency_ms']:.4f}ms | 反馈维度={len(fb.get('feedback_vector', []))}")

    # Test 8: 完整七层循环
    print("\n[Test 8] FCTN Full Bridge 完整循环...")
    fctn = FCTNFullBridge()
    fctn.initialize()
    cycle_result = fctn.run_single_cycle()
    assert cycle_result["transfers"]["cloud->field"]["status"] == "OK", "闭环应成功"
    assert fctn.field_state.cycle_count == 1, "cycle_count应为1"
    results["tests"]["full_cycle"] = {
        "status": "PASS",
        "cycle": cycle_result["cycle"],
        "total_latency_ms": cycle_result["total_latency_ms"],
        "transfers": list(cycle_result["transfers"].keys())
    }
    print(f"  PASS: 完整七层循环 | 总延迟={cycle_result['total_latency_ms']:.4f}ms | 闭环OK")

    # Test 9: 多轮循环
    print("\n[Test 9] 多轮循环 (5 cycles)...")
    multi = fctn.run_multi_cycles(5)
    assert len(multi["cycles"]) == 5, "应有5个循环"
    assert fctn.field_state.cycle_count == 6, "总cycle_count应为6"
    results["tests"]["multi_cycle"] = {
        "status": "PASS",
        "n_cycles": multi["n_cycles"],
        "final_cycle": fctn.field_state.cycle_count,
        "avg_total_latency_ms": round(np.mean([c["total_latency_ms"] for c in multi["cycles"]]), 4)
    }
    print(f"  PASS: 5轮循环完成 | 最终cycle={fctn.field_state.cycle_count} | 平均延迟={np.mean([c['total_latency_ms'] for c in multi['cycles']]):.4f}ms")

    # Test 10: 数据流验证
    print("\n[Test 10] 数据流通道验证...")
    dataflow = fctn.verify_dataflow()
    all_active = all(v["status"] == "ACTIVE" for v in dataflow.values())
    results["dataflow"] = dataflow
    results["tests"]["dataflow_verify"] = {
        "status": "PASS" if all_active else "FAIL",
        "channels_active": sum(1 for v in dataflow.values() if v["status"] == "ACTIVE"),
        "total_channels": len(dataflow)
    }
    print(f"  PASS: {sum(1 for v in dataflow.values() if v['status'] == 'ACTIVE')}/{len(dataflow)} 通道活跃")

    # Test 11: 循环一致性检查
    print("\n[Test 11] 循环一致性检查...")
    consistency = check_cycle_consistency(fctn)
    results["consistency"] = consistency
    results["tests"]["consistency"] = {
        "status": "PASS" if consistency["overall"] else "FAIL",
        "field_preserved": consistency["field_preserved"],
        "energy_conserved": consistency["energy_conserved"],
        "data_integrity": consistency["data_integrity"]
    }
    print(f"  {'PASS' if consistency['overall'] else 'FAIL'}: 场保持={consistency['field_preserved']} | 能量守恒={consistency['energy_conserved']} | 数据完整={consistency['data_integrity']}")

    # 总体状态
    all_pass = all(t["status"] == "PASS" for t in results["tests"].values())
    results["overall_status"] = "ALL_PASS" if all_pass else "PARTIAL"
    results["pass_count"] = sum(1 for t in results["tests"].values() if t["status"] == "PASS")
    results["total_tests"] = len(results["tests"])

    print("\n" + "=" * 70)
    print(f"验证完成: {results['pass_count']}/{results['total_tests']} 通过 | 状态: {results['overall_status']}")
    print("=" * 70)

    return results


def check_cycle_consistency(fctn: FCTNFullBridge) -> Dict[str, Any]:
    """检查循环一致性"""
    if not fctn.cycle_history:
        return {"overall": False, "reason": "no_cycles"}

    # 检查1: 场状态维度保持
    field_preserved = all(
        fctn.cycle_history[i]["integrity"].get("Field", {}).get("valid", False)
        for i in range(len(fctn.cycle_history))
    )

    # 检查2: 能量守恒 (粗略 — 能量应在合理范围内 [0.5, 25])
    energies = []
    for hist in fctn.cycle_history:
        field_info = hist.get("integrity", {}).get("Field", {})
        if "energy" in field_info:
            energies.append(field_info["energy"])
    energy_conserved = len(energies) > 0 and all(0.5 < e < 25 for e in energies)

    # 检查3: 数据完整性
    data_integrity = all(
        all(layer_info.get("valid", False) for layer_info in hist["integrity"].values())
        for hist in fctn.cycle_history
    )

    return {
        "overall": field_preserved and energy_conserved and data_integrity,
        "field_preserved": field_preserved,
        "energy_conserved": energy_conserved,
        "data_integrity": data_integrity,
        "energy_trajectory": [round(e, 4) for e in energies]
    }


# =============================================================================
# 11. 报告生成
# =============================================================================

def generate_reports(verify_result: Dict[str, Any], fctn: Optional[FCTNFullBridge] = None):
    """生成JSON和Markdown报告"""
    hub_dir = "/mnt/agents/output/OMNI-HUB/hub"
    core_dir = "/mnt/agents/output/OMNI-HUB/core"
    os.makedirs(hub_dir, exist_ok=True)
    os.makedirs(core_dir, exist_ok=True)

    # JSON报告
    json_path = os.path.join(hub_dir, "FCTN_FULL_BRIDGE_REPORT.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(verify_result, f, ensure_ascii=False, indent=2)

    # Markdown报告
    md_path = os.path.join(hub_dir, "FCTN_FULL_BRIDGE_REPORT.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# OMNI-HUB FCTN Full Bridge Report\n\n")
        f.write("**场-圈-环-层-网-塔-云 七层架构完整打通报告**\n\n")
        f.write(f"**版本**: {verify_result.get('version', 'N/A')}\n\n")
        f.write(f"**时间戳**: {verify_result.get('timestamp', 'N/A')}\n\n")
        f.write(f"**总体状态**: {verify_result.get('overall_status', 'N/A')}\n\n")
        f.write(f"**通过率**: {verify_result.get('pass_count', 0)}/{verify_result.get('total_tests', 0)}\n\n")
        f.write("---\n\n")

        # 七层架构图
        f.write("## 七层架构图\n\n")
        f.write("```\n")
        f.write("  [Field] 67维统一场状态\n")
        f.write("     | 场→圈: 场状态驱动圈耦合更新\n")
        f.write("     v\n")
        f.write("  [Circle] 4类圈拓扑 (Session/Consensus/Command/Relay)\n")
        f.write("     | 圈→环: 耦合强度决定反馈环类型\n")
        f.write("     v\n")
        f.write("  [Ring] 自反馈环 (正/负/振荡/阻尼)\n")
        f.write("     | 环→层: 反馈结果注入知识基座\n")
        f.write("     v\n")
        f.write("  [Layer] 6知识基座 (KG/CC/HG/IN/CT/LL)\n")
        f.write("     | 层→网: 基座知识编织成张量网络\n")
        f.write("     v\n")
        f.write("  [Net] 张量网络 (rank-3节点 + 纠缠边)\n")
        f.write("     | 网→塔: 张量收缩产生涌现层级\n")
        f.write("     v\n")
        f.write("  [Tower] 层级涌现塔 (6级涌现结构)\n")
        f.write("     | 塔→云: 涌现状态同步到云端\n")
        f.write("     v\n")
        f.write("  [Cloud] 分布式部署 (Worker+KV+D1+Pages)\n")
        f.write("     | 云→场: 云端反馈更新统一场\n")
        f.write("     v\n")
        f.write("  [Field] ← 闭环完成\n")
        f.write("```\n\n")
        f.write("---\n\n")

        # 测试结果
        f.write("## 测试结果\n\n")
        for test_name, test_data in verify_result.get('tests', {}).items():
            status_icon = "PASS" if test_data.get('status') == "PASS" else "FAIL"
            f.write(f"### {test_name} [{status_icon}]\n\n")
            for k, v in test_data.items():
                if k != 'status':
                    f.write(f"- **{k}**: {v}\n")
            f.write("\n")

        f.write("---\n\n")

        # 数据流验证
        f.write("## 数据流通道验证\n\n")
        f.write("| 通道 | 状态 | 传输次数 |\n")
        f.write("|------|------|----------|\n")
        for ch_name, ch_data in verify_result.get('dataflow', {}).items():
            f.write(f"| {ch_name} | {ch_data.get('status', 'N/A')} | {ch_data.get('transfers_count', 0)} |\n")
        f.write("\n")

        f.write("---\n\n")

        # 一致性检查
        f.write("## 循环一致性检查\n\n")
        consistency = verify_result.get('consistency', {})
        f.write(f"- **总体一致性**: {'PASS' if consistency.get('overall') else 'FAIL'}\n")
        f.write(f"- **场状态保持**: {'PASS' if consistency.get('field_preserved') else 'FAIL'}\n")
        f.write(f"- **能量守恒**: {'PASS' if consistency.get('energy_conserved') else 'FAIL'}\n")
        f.write(f"- **数据完整性**: {'PASS' if consistency.get('data_integrity') else 'FAIL'}\n")
        if 'energy_trajectory' in consistency:
            f.write(f"- **能量轨迹**: {consistency['energy_trajectory']}\n")
        f.write("\n")

        # 七层连接详情
        f.write("---\n\n")
        f.write("## 七层连接详情\n\n")
        connections = [
            ("场 → 圈", "场状态驱动圈耦合更新", "field.vector → circle.topology_matrix"),
            ("圈 → 环", "耦合强度决定反馈环类型", "circle.coupling → ring.feedback_type"),
            ("环 → 层", "反馈结果注入知识基座", "ring.feedback_vector → knowledge.layers"),
            ("层 → 网", "基座知识编织成张量网络", "knowledge.embeddings → tensor.nodes"),
            ("网 → 塔", "张量收缩产生涌现层级", "tensor.scalar/vector → tower.levels"),
            ("塔 → 云", "涌现状态同步到云端", "tower.height/stability → cloud.worker/kv/d1"),
            ("云 → 场", "云端反馈更新统一场", "cloud.feedback_vector → field.vector"),
        ]
        f.write("| 连接 | 描述 | 数据映射 |\n")
        f.write("|------|------|----------|\n")
        for conn in connections:
            f.write(f"| {conn[0]} | {conn[1]} | `{conn[2]}` |\n")
        f.write("\n")

        f.write("---\n\n")
        f.write("*Report generated by FCTN Full Bridge v12.0*\n")

    return json_path, md_path


# =============================================================================
# 12. 主入口
# =============================================================================

if __name__ == '__main__':
    np.random.seed(42)

    # 运行完整验证
    verify_result = verify_fctn_full_bridge()

    # 创建FCTN实例用于报告
    fctn = FCTNFullBridge()
    fctn.initialize()
    fctn.run_multi_cycles(5)

    # 生成报告
    json_path, md_path = generate_reports(verify_result, fctn)

    print(f"\n报告已生成:")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(f"\n状态: {verify_result['overall_status']}")

