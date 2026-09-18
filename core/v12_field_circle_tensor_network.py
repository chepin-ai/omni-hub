#!/usr/bin/env python3
"""
Field-Circle-Tensor Network (FCTN) v1.2
场→圈→张量网 完整联通架构
Integrates: field, circles, tensor subsystems of OMNI-HUB
"""

__version__ = "1.2.0"

import json
import numpy as np
import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

# ────────────────────────────────────────────────
# 0. Constants
# ────────────────────────────────────────────────
LINES = ['ucif2', 'lgt', 'qfa', 'usrm', 'vinf', 'qgl', 'qlv', 'lvlu', 'cfts', 'cisvr', 'qtlv']
N = len(LINES)
LINE_INDEX = {line: i for i, line in enumerate(LINES)}

# 11线SI等级映射
SI_LEVELS = {
    'ucif2': 5, 'lgt': 5, 'qfa': 5, 'usrm': 5, 'vinf': 5, 'qgl': 5,
    'qlv': 4, 'lvlu': 4, 'cfts': 4, 'cisvr': 4, 'qtlv': 3
}

# 圈层级映射 (from CIRCLES-v1.0.json)
CIRCLE_LEVELS = {
    'ucif2': 'inner', 'lgt': 'inner', 'qfa': 'inner',
    'usrm': 'middle', 'vinf': 'middle', 'qgl': 'middle', 'qlv': 'middle',
    'lvlu': 'outer', 'cfts': 'outer',
    'cisvr': 'middle', 'qtlv': 'outer'
}

# 维度常量
FIELD_DIM = 67          # 统一场状态维度
FIELD_PER_LINE = 5      # 每条线的场维度 (amplitude, phase, energy, health, si_level)
TENSOR_BOND_DIM = 8     # 张量键维度

# ────────────────────────────────────────────────
# 1. FieldState — 统一场状态 (67维)
# ────────────────────────────────────────────────
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
        self._init_default()

    def _init_default(self):
        """用11线健康度和SI等级初始化场"""
        health = [1.00, 0.98, 0.96, 0.97, 0.96, 0.95, 0.94, 0.89, 0.91, 0.90, 0.85]
        for i, line in enumerate(LINES):
            base = i * FIELD_PER_LINE
            si = SI_LEVELS[line]
            phase = si * np.pi / 6.0
            self.vector[base + 0] = health[i]               # amplitude
            self.vector[base + 1] = phase                    # phase
            self.vector[base + 2] = health[i] * si / 5.0     # energy
            self.vector[base + 3] = health[i]                # health
            self.vector[base + 4] = si / 5.0                  # si_level normalized
        # 纠缠熵初始化为均匀分布
        for i in range(N):
            self.vector[55 + i] = 1.0 / N
        # 全局相位
        self.vector[66] = 0.0

    def get_line_state(self, line: str) -> np.ndarray:
        """获取单条线的场状态 (5维)"""
        idx = LINE_INDEX[line]
        base = idx * FIELD_PER_LINE
        return self.vector[base:base + FIELD_PER_LINE]

    def set_line_state(self, line: str, state: np.ndarray):
        """设置单条线的场状态"""
        idx = LINE_INDEX[line]
        base = idx * FIELD_PER_LINE
        self.vector[base:base + len(state)] = state[:FIELD_PER_LINE]

    def get_entanglement_entropy(self) -> np.ndarray:
        """获取线间纠缠熵 (11维)"""
        return self.vector[55:55 + N]

    def set_entanglement_entropy(self, entropy_vec: np.ndarray):
        """设置线间纠缠熵"""
        self.vector[55:55 + N] = entropy_vec[:N]

    def global_phase(self) -> float:
        return float(self.vector[66])

    def set_global_phase(self, phi: float):
        self.vector[66] = phi

    def energy(self) -> float:
        """计算总场能量"""
        return float(np.sum(self.vector[2::FIELD_PER_LINE][:N]))

    def health(self) -> float:
        """计算平均健康度"""
        return float(np.mean(self.vector[3::FIELD_PER_LINE][:N]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vector_shape": self.vector.shape,
            "energy": round(self.energy(), 6),
            "health": round(self.health(), 6),
            "global_phase": round(self.global_phase(), 6),
            "cycle_count": self.cycle_count,
            "timestamp": self.timestamp,
            "line_states": {
                line: [round(float(v), 4) for v in self.get_line_state(line)]
                for line in LINES
            }
        }

    def copy(self) -> 'FieldState':
        fs = FieldState(self.n_dims)
        fs.vector = self.vector.copy()
        fs.timestamp = self.timestamp
        fs.cycle_count = self.cycle_count
        return fs

# ────────────────────────────────────────────────
# 2. CircleTopology — 圈拓扑结构
# ────────────────────────────────────────────────
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
    """
    圈拓扑: 聚合四类圈 + 拓扑指标
    """
    def __init__(self):
        self.session = SessionCircle()
        self.consensus = ConsensusCircle()
        self.command = CommandCircle()
        self.relay = RelayCircle()
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.topology_matrix = np.zeros((N, N), dtype=np.float64)
        self.activity_vector = np.zeros(N, dtype=np.float64)

    def compute_topology_matrix(self) -> np.ndarray:
        """
        基于四类圈的活动计算11×11拓扑邻接矩阵:
        - session: 附件共享关系
        - consensus: 背书关系
        - command: 任务分发关系
        - relay: 路由关系
        """
        M = np.zeros((N, N), dtype=np.float64)

        # Session圈贡献: visibility关系
        for att in self.session.attachments:
            src = LINE_INDEX[att["line"]]
            for vis_line in att["visibility"]:
                dst = LINE_INDEX[vis_line]
                M[src, dst] += 0.15

        # Consensus圈贡献: 背书关系
        for prop in self.consensus.proposals.values():
            src = LINE_INDEX[prop["from"]]
            for end in prop["endorsements"]:
                dst = LINE_INDEX[end]
                M[src, dst] += 0.25
                M[dst, src] += 0.25

        # Command圈贡献: 任务分发
        for task in self.command.tasks.values():
            src = LINE_INDEX[task["from"]]
            dst = LINE_INDEX[task["to"]]
            M[src, dst] += 0.30
            if task["status"] == "CLOSED":
                M[dst, src] += 0.10  # 闭环反馈

        # Relay圈贡献: 路由关系
        for route in self.relay.routes:
            src = LINE_INDEX[route["from"]]
            for tgt in route["targets"]:
                dst = LINE_INDEX[tgt]
                M[src, dst] += 0.20

        # 对称化 + 归一化
        M = (M + M.T) / 2.0
        for i in range(N):
            row_sum = np.sum(M[i])
            if row_sum > 0:
                M[i] /= row_sum
        self.topology_matrix = M
        return M

    def compute_activity_vector(self) -> np.ndarray:
        """计算每条线的圈活跃度 (0-1)"""
        act = np.zeros(N)
        for i, line in enumerate(LINES):
            # session activity
            s_count = sum(1 for a in self.session.attachments if a["line"] == line)
            # consensus activity
            c_count = sum(1 for p in self.consensus.proposals.values() if p["from"] == line)
            # command activity
            cmd_count = sum(1 for t in self.command.tasks.values() if t["from"] == line or t["to"] == line)
            # relay activity
            r_count = sum(1 for r in self.relay.routes if r["from"] == line)
            act[i] = min(1.0, (s_count * 0.1 + c_count * 0.3 + cmd_count * 0.3 + r_count * 0.3))
        self.activity_vector = act
        return act

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "session_count": len(self.session.attachments),
            "consensus_count": len(self.consensus.proposals),
            "command_count": len(self.command.tasks),
            "relay_count": len(self.relay.routes),
            "activity_vector": [round(float(a), 4) for a in self.activity_vector],
            "topology_matrix": [[round(float(v), 4) for v in row] for row in self.topology_matrix.tolist()]
        }

# ────────────────────────────────────────────────
# 3. TensorNetwork — 张量网络
# ────────────────────────────────────────────────
class TensorNetwork:
    """
    张量网络: 基于contraction JSON的节点-边张量网络
    每个节点 = rank-3张量 (物理维度 × 键维度 × 键维度)
    每条边 = 纠缠度权重
    """
    def __init__(self, bond_dim: int = TENSOR_BOND_DIM):
        self.bond_dim = bond_dim
        self.nodes: Dict[str, np.ndarray] = {}
        self.edges: Dict[Tuple[str, str], float] = {}
        self.contraction_order: List[str] = []
        self.global_metrics: Dict[str, float] = {}
        self.node_list: List[str] = []
        self.result_scalar: float = 0.0
        self.result_vector: np.ndarray = np.zeros(N)

    def load_from_json(self, data: Dict[str, Any]):
        """从contraction JSON加载网络结构"""
        self.node_list = data.get("nodes", [])
        self.contraction_order = data.get("contraction_order", self.node_list)
        self.global_metrics = data.get("global_metrics", {})

        # 解析entanglement边
        ent = data.get("entanglement", {})
        self.edges = {}
        for key, val in ent.items():
            a, b = key.split(":")
            self.edges[(a, b)] = float(val)
            self.edges[(b, a)] = float(val)

        # 初始化节点张量 (rank-3: 物理维 × bond_dim × bond_dim)
        phys_dim = 4  # (energy, health, entropy, excitation)
        for node in self.node_list:
            # 随机初始化但保持可重复性
            np.random.seed(hash(node) % (2**31))
            T = np.random.randn(phys_dim, self.bond_dim, self.bond_dim) * 0.1
            # 对角线增强
            for d in range(min(self.bond_dim, phys_dim)):
                T[d, d, d % self.bond_dim] += 1.0
            self.nodes[node] = T

    def load_latest_contraction(self, tensor_dir: str = "/mnt/agents/output/OMNI-HUB/tensor") -> bool:
        """自动加载最新的contraction JSON文件"""
        if not os.path.isdir(tensor_dir):
            return False
        files = [f for f in os.listdir(tensor_dir) if f.startswith("contraction_") and f.endswith(".json")]
        if not files:
            return False
        files.sort()
        latest = os.path.join(tensor_dir, files[-1])
        with open(latest, 'r') as f:
            data = json.load(f)
        self.load_from_json(data)
        return True

    def contract_network(self) -> Dict[str, Any]:
        """
        执行张量网络收缩:
        1. 沿contraction_order顺序收缩
        2. 计算全局标量和线结果向量
        """
        if not self.nodes:
            return {"scalar": 0.0, "vector": [0.0] * N}

        # 简化的收缩: 对每个节点沿键求迹后加权求和
        contracted = {}
        for node, T in self.nodes.items():
            # trace over bond indices -> phys_dim vector
            tr = np.einsum('ikk->i', T)
            contracted[node] = tr

        # 边权重调制
        for (a, b), w in self.edges.items():
            if a in contracted and b in contracted:
                # 纠缠边调制两个节点的能量分量
                contracted[a][0] *= (1.0 + w * 0.01)
                contracted[b][0] *= (1.0 + w * 0.01)

        # 全局标量 = 所有节点物理迹的和
        scalar = sum(np.sum(v) for v in contracted.values())

        # 结果向量映射到11维
        result_vec = np.zeros(N)
        for node, vec in contracted.items():
            if node in LINE_INDEX:
                idx = LINE_INDEX[node]
                result_vec[idx] = float(np.sum(vec))

        # 归一化
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
            "nodes": self.node_list,
            "bond_dim": self.bond_dim,
            "scalar": round(self.result_scalar, 6),
            "vector": [round(float(v), 6) for v in self.result_vector],
            "global_metrics": self.global_metrics,
            "contraction_order": self.contraction_order
        }

# ────────────────────────────────────────────────
# 4. FieldCircleTensorBridge — 三者桥接
# ────────────────────────────────────────────────
class FieldCircleTensorBridge:
    """
    场↔圈↔张量 桥接器
    核心映射:
      field → circle: 场能量驱动圈活跃度
      circle → tensor: 圈拓扑定义张量边权重
      tensor → field: 收缩结果反馈场状态更新
    """
    def __init__(self):
        self.field_state: Optional[FieldState] = None
        self.circle_topology: Optional[CircleTopology] = None
        self.tensor_network: Optional[TensorNetwork] = None
        self.history: List[Dict] = []

    # ── field → circle ──
    def propagate_field_to_circle(self, field_state: FieldState) -> CircleTopology:
        """
        场状态 → 圈拓扑演化
        规则:
        - 高能量线 → 更多提案(consensus)
        - 高振幅线 → 更多附件(session)
        - 高相位同步 → 更多任务(command)
        - 高纠缠 → 更多路由(relay)
        """
        self.field_state = field_state
        ct = CircleTopology()

        # 1. Session圈: 每条线根据振幅附加内容
        for i, line in enumerate(LINES):
            amp = field_state.vector[i * FIELD_PER_LINE + 0]
            if amp > 0.5:
                content = f"场驱动产出 from {line} (amp={amp:.3f})"
                vis = [l for l in LINES if SI_LEVELS[l] >= SI_LEVELS[line] - 1]
                ct.session.attach(line, content, vis)

        # 2. Consensus圈: 高能量线发起提案
        for i, line in enumerate(LINES):
            energy = field_state.vector[i * FIELD_PER_LINE + 2]
            if energy > 0.7:
                ct.consensus.propose(line, f"场能量共识: {energy:.3f}")

        # 3. Command圈: 相位差大的线对形成任务
        for i in range(N):
            for j in range(i + 1, N):
                phase_i = field_state.vector[i * FIELD_PER_LINE + 1]
                phase_j = field_state.vector[j * FIELD_PER_LINE + 1]
                phase_diff = abs(phase_i - phase_j)
                if phase_diff > 1.0 and phase_diff < 2.5:
                    ct.command.dispatch(LINES[i], LINES[j],
                                        f"相位补偿任务 dφ={phase_diff:.3f}")

        # 4. Relay圈: 纠缠熵高的线作为路由源
        ent = field_state.get_entanglement_entropy()
        top_idx = np.argsort(ent)[-3:]
        for idx in top_idx:
            line = LINES[idx]
            ct.relay.route(f"场同步信号 entropy={ent[idx]:.3f}", line, "broadcast")

        # 计算拓扑矩阵和活跃度
        ct.compute_topology_matrix()
        ct.compute_activity_vector()
        self.circle_topology = ct
        return ct

    # ── circle → tensor ──
    def propagate_circle_to_tensor(self, circle_topology: CircleTopology) -> TensorNetwork:
        """
        圈拓扑 → 张量网络生成
        规则:
        - 圈拓扑矩阵 → 张量边权重
        - 活跃度向量 → 节点张量初始幅值
        - 共识状态 → 收缩顺序优先级
        """
        self.circle_topology = circle_topology
        tn = TensorNetwork(bond_dim=TENSOR_BOND_DIM)

        # 选择最活跃的节点构建子网络
        active_idx = np.where(circle_topology.activity_vector > 0.1)[0]
        if len(active_idx) == 0:
            active_idx = np.arange(N)
        active_nodes = [LINES[i] for i in active_idx if LINES[i] in LINE_INDEX]

        # 构建节点列表和收缩顺序
        tn.node_list = active_nodes
        tn.contraction_order = active_nodes

        # 从圈拓扑矩阵构建边权重
        top = circle_topology.topology_matrix
        tn.edges = {}
        for i, ni in enumerate(active_nodes):
            for j, nj in enumerate(active_nodes):
                if i != j:
                    ii = LINE_INDEX[ni]
                    jj = LINE_INDEX[nj]
                    w = float(top[ii, jj])
                    tn.edges[(ni, nj)] = w * 10.0  # 缩放到张量级

        # 初始化节点张量 (由活跃度调制)
        phys_dim = 4
        for node in active_nodes:
            idx = LINE_INDEX[node]
            act = circle_topology.activity_vector[idx]
            np.random.seed(hash(node) % (2**31))
            T = np.random.randn(phys_dim, tn.bond_dim, tn.bond_dim) * 0.1
            # 活跃度调制对角线
            scale = 0.5 + act * 2.0
            for d in range(min(tn.bond_dim, phys_dim)):
                T[d, d, d % tn.bond_dim] += scale
            tn.nodes[node] = T

        # 全局指标继承
        if self.field_state:
            health_val = float(np.mean([self.field_state.vector[i * FIELD_PER_LINE + 3] for i in range(N)]))
        else:
            health_val = 1.0
        tn.global_metrics = {
            "health": health_val,
            "load": float(np.mean(circle_topology.activity_vector)),
            "entropy": float(-np.sum(
                circle_topology.activity_vector * np.log(circle_topology.activity_vector + 1e-10)
            )),
            "excitation_level": float(np.max(circle_topology.activity_vector)),
            "circle_driven": True
        }

        self.tensor_network = tn
        return tn

    # ── tensor → field ──
    def propagate_tensor_to_field(self, tensor_result: Dict[str, Any]) -> FieldState:
        """
        张量收缩结果 → 场状态更新
        规则:
        - 标量结果 → 全局相位
        - 向量结果 → 各线能量更新
        - 全局指标 → 健康度和纠缠熵更新
        """
        if self.field_state is None:
            self.field_state = FieldState()

        fs = self.field_state.copy()
        fs.cycle_count += 1
        fs.timestamp = datetime.now(timezone.utc).isoformat()

        vec = np.array(tensor_result.get("vector", [0.0] * N))
        scalar = tensor_result.get("scalar", 0.0)

        # 1. 全局相位更新 (由标量驱动)
        fs.set_global_phase(fs.global_phase() + scalar * 0.01)

        # 2. 各线能量更新 (由收缩向量驱动)
        for i, line in enumerate(LINES):
            base = i * FIELD_PER_LINE
            delta_e = vec[i] * 0.1  # 反馈强度
            fs.vector[base + 2] = np.clip(fs.vector[base + 2] + delta_e, 0.1, 2.0)

        # 3. 健康度更新 (衰减+反馈)
        for i in range(N):
            base = i * FIELD_PER_LINE
            fs.vector[base + 3] *= 0.98  # 自然衰减
            fs.vector[base + 3] = np.clip(fs.vector[base + 3] + vec[i] * 0.02, 0.5, 1.0)

        # 4. 纠缠熵更新 (由张量结果向量重归一化)
        entropy_vec = np.abs(vec)
        if np.sum(entropy_vec) > 0:
            entropy_vec /= np.sum(entropy_vec)
        fs.set_entanglement_entropy(entropy_vec)

        # 5. 振幅归一化
        for i in range(N):
            base = i * FIELD_PER_LINE
            fs.vector[base + 0] = np.clip(fs.vector[base + 0], 0.0, 1.0)

        self.field_state = fs
        return fs

    # ── 完整循环 ──
    def run_full_cycle(self) -> Dict[str, Any]:
        """
        完整循环: 场 → 圈 → 张量 → 场
        """
        # Step 1: 初始化或复用场
        if self.field_state is None:
            self.field_state = FieldState()
        fs_initial = self.field_state.copy()

        # Step 2: field → circle
        ct = self.propagate_field_to_circle(self.field_state)

        # Step 3: circle → tensor
        tn = self.propagate_circle_to_tensor(ct)
        tensor_result = tn.contract_network()

        # Step 4: tensor → field
        fs_new = self.propagate_tensor_to_field(tensor_result)

        # 记录历史
        cycle_record = {
            "cycle": fs_new.cycle_count,
            "timestamp": fs_new.timestamp,
            "initial_energy": round(fs_initial.energy(), 6),
            "final_energy": round(fs_new.energy(), 6),
            "initial_health": round(fs_initial.health(), 6),
            "final_health": round(fs_new.health(), 6),
            "circle_activity": [round(float(a), 4) for a in ct.activity_vector],
            "tensor_scalar": tensor_result.get("scalar", 0.0),
            "tensor_vector": tensor_result.get("vector", [])
        }
        self.history.append(cycle_record)

        return {
            "cycle": fs_new.cycle_count,
            "field_before": fs_initial.to_dict(),
            "field_after": fs_new.to_dict(),
            "circle": ct.to_dict(),
            "tensor": tensor_result,
            "status": "CYCLE_COMPLETE"
        }

# ────────────────────────────────────────────────
# 5. SI11Integration — 11线SI集成
# ────────────────────────────────────────────────
class SI11Integration:
    """
    11线SI集成器:
    - ucif2线 ↔ field (形式化数学↔场)
    - cfts线 ↔ circle (跨功能同步↔圈)
    - cisvr线 ↔ tensor (意识/信息↔张量)
    - 其余8线通过各自的映射参与
    """
    def __init__(self):
        self.bridge = FieldCircleTensorBridge()
        self.line_bindings: Dict[str, Dict[str, str]] = {}
        self._setup_bindings()

    def _setup_bindings(self):
        """设置每条线的绑定关系"""
        self.line_bindings = {
            'ucif2':  {'primary': 'field',  'role': 'formalizer',     'dimension': 'math'},
            'lgt':    {'primary': 'field',  'role': 'logic_gate',     'dimension': 'logic'},
            'qfa':    {'primary': 'field',  'role': 'quantifier',     'dimension': 'quantum'},
            'usrm':   {'primary': 'circle', 'role': 'user_room',      'dimension': 'social'},
            'vinf':   {'primary': 'field',  'role': 'info_validator', 'dimension': 'info'},
            'qgl':    {'primary': 'circle', 'role': 'goal_learner',   'dimension': 'goal'},
            'qlv':    {'primary': 'tensor', 'role': 'value_learner',  'dimension': 'value'},
            'lvlu':   {'primary': 'tensor', 'role': 'level_up',       'dimension': 'level'},
            'cfts':   {'primary': 'circle', 'role': 'cross_sync',     'dimension': 'sync'},
            'cisvr':  {'primary': 'tensor', 'role': 'consciousness',  'dimension': 'cognition'},
            'qtlv':   {'primary': 'tensor', 'role': 'time_learner',   'dimension': 'time'}
        }

    def inject_line_signal(self, line: str, signal_type: str, value: float):
        """
        向指定线注入信号:
        - signal_type: 'energy', 'phase', 'health', 'proposal', 'task', 'route'
        """
        if self.bridge.field_state is None:
            self.bridge.field_state = FieldState()

        idx = LINE_INDEX.get(line, -1)
        if idx < 0:
            return False

        binding = self.line_bindings.get(line, {})
        primary = binding.get('primary', 'field')

        if signal_type in ('energy', 'phase', 'health'):
            base = idx * FIELD_PER_LINE
            if signal_type == 'energy':
                self.bridge.field_state.vector[base + 2] = np.clip(value, 0.1, 2.0)
            elif signal_type == 'phase':
                self.bridge.field_state.vector[base + 1] = value
            elif signal_type == 'health':
                self.bridge.field_state.vector[base + 3] = np.clip(value, 0.5, 1.0)

        elif signal_type == 'proposal' and primary == 'circle':
            if self.bridge.circle_topology is None:
                self.bridge.circle_topology = CircleTopology()
            self.bridge.circle_topology.consensus.propose(line, f"SI注入提案: {value}")

        elif signal_type == 'task' and primary == 'circle':
            if self.bridge.circle_topology is None:
                self.bridge.circle_topology = CircleTopology()
            target = LINES[(idx + 1) % N]
            self.bridge.circle_topology.command.dispatch(line, target, f"SI注入任务: {value}")

        elif signal_type == 'route' and primary == 'tensor':
            if self.bridge.circle_topology is None:
                self.bridge.circle_topology = CircleTopology()
            self.bridge.circle_topology.relay.route(f"SI信号: {value}", line, "broadcast")

        return True

    def read_line_state(self, line: str) -> Dict[str, Any]:
        """读取指定线的当前状态"""
        if self.bridge.field_state is None:
            return {}
        idx = LINE_INDEX.get(line, -1)
        if idx < 0:
            return {}
        fs = self.bridge.field_state
        binding = self.line_bindings.get(line, {})
        return {
            "line": line,
            "binding": binding,
            "field_state": [round(float(v), 4) for v in fs.get_line_state(line)],
            "entropy": round(float(fs.get_entanglement_entropy()[idx]), 4),
            "global_phase": round(fs.global_phase(), 4)
        }

    def propagate_all_lines(self) -> Dict[str, Any]:
        """
        对所有11线执行一次完整传播:
        1. 为每条线注入基础信号
        2. 运行完整FCT循环
        3. 收集各线状态
        """
        # 为每条线注入基础能量信号
        for line in LINES:
            si = SI_LEVELS[line]
            self.inject_line_signal(line, 'energy', si / 5.0)

        # 运行完整循环
        result = self.bridge.run_full_cycle()

        # 收集所有线状态
        line_states = {line: self.read_line_state(line) for line in LINES}

        return {
            "fct_result": result,
            "line_states": line_states,
            "cycle": result["cycle"]
        }

    def run_multi_cycle(self, n_cycles: int = 3) -> Dict[str, Any]:
        """运行多轮完整循环"""
        results = []
        for _ in range(n_cycles):
            # 每轮轻微扰动
            for line in LINES:
                noise = np.random.randn() * 0.05
                self.inject_line_signal(line, 'energy', SI_LEVELS[line] / 5.0 + noise)
            result = self.bridge.run_full_cycle()
            results.append(result)

        return {
            "n_cycles": n_cycles,
            "cycles": results,
            "history": self.bridge.history,
            "final_field": self.bridge.field_state.to_dict() if self.bridge.field_state else {}
        }

# ────────────────────────────────────────────────
# 6. Verification & Main
# ────────────────────────────────────────────────
def verify_fctn() -> Dict[str, Any]:
    """完整验证FCTN系统"""
    print("[FCTN] 开始完整验证...")
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "tests": {}
    }

    # Test 1: FieldState
    print("[FCTN] Test 1: FieldState 初始化...")
    fs = FieldState()
    assert fs.vector.shape == (FIELD_DIM,), "FieldState维度错误"
    assert fs.energy() > 0, "FieldState能量必须>0"
    results["tests"]["field_state"] = {"status": "PASS", "energy": round(fs.energy(), 4)}

    # Test 2: CircleTopology
    print("[FCTN] Test 2: CircleTopology 构建...")
    ct = CircleTopology()
    for line in LINES:
        ct.session.attach(line, f"test-{line}")
    ct.compute_topology_matrix()
    ct.compute_activity_vector()
    assert ct.topology_matrix.shape == (N, N), "拓扑矩阵维度错误"
    results["tests"]["circle_topology"] = {
        "status": "PASS",
        "session_count": len(ct.session.attachments),
        "matrix_shape": list(ct.topology_matrix.shape)
    }

    # Test 3: TensorNetwork
    print("[FCTN] Test 3: TensorNetwork 收缩...")
    tn = TensorNetwork()
    # 构造测试数据
    test_data = {
        "nodes": ["ucif2", "lgt", "qfa", "cfts"],
        "contraction_order": ["ucif2", "lgt", "qfa", "cfts"],
        "global_metrics": {"health": 1.0, "entropy": 0.5},
        "entanglement": {
            "ucif2:lgt": 1.5, "ucif2:qfa": 1.2, "lgt:qfa": 0.8,
            "cfts:ucif2": 1.0, "cfts:lgt": 0.9
        }
    }
    tn.load_from_json(test_data)
    tr = tn.contract_network()
    assert "scalar" in tr, "张量收缩结果缺少scalar"
    results["tests"]["tensor_network"] = {
        "status": "PASS",
        "scalar": tr["scalar"],
        "node_count": tr["node_count"]
    }

    # Test 4: Bridge field→circle
    print("[FCTN] Test 4: Bridge field→circle...")
    bridge = FieldCircleTensorBridge()
    ct2 = bridge.propagate_field_to_circle(fs)
    assert len(ct2.session.attachments) > 0, "field→circle后应有附件"
    results["tests"]["bridge_field_to_circle"] = {
        "status": "PASS",
        "attachments": len(ct2.session.attachments)
    }

    # Test 5: Bridge circle→tensor
    print("[FCTN] Test 5: Bridge circle→tensor...")
    tn2 = bridge.propagate_circle_to_tensor(ct2)
    tr2 = tn2.contract_network()
    assert tr2["scalar"] != 0, "circle→tensor标量不应为0"
    results["tests"]["bridge_circle_to_tensor"] = {
        "status": "PASS",
        "scalar": tr2["scalar"]
    }

    # Test 6: Bridge tensor→field
    print("[FCTN] Test 6: Bridge tensor→field...")
    fs_new = bridge.propagate_tensor_to_field(tr2)
    assert fs_new.cycle_count == 1, "cycle_count应为1"
    results["tests"]["bridge_tensor_to_field"] = {
        "status": "PASS",
        "cycle_count": fs_new.cycle_count,
        "energy_delta": round(fs_new.energy() - fs.energy(), 4)
    }

    # Test 7: 完整循环
    print("[FCTN] Test 7: 完整循环 run_full_cycle...")
    bridge2 = FieldCircleTensorBridge()
    cycle_result = bridge2.run_full_cycle()
    assert cycle_result["status"] == "CYCLE_COMPLETE", "循环状态错误"
    results["tests"]["full_cycle"] = {
        "status": "PASS",
        "cycle": cycle_result["cycle"]
    }

    # Test 8: SI11集成
    print("[FCTN] Test 8: SI11集成...")
    si = SI11Integration()
    si_result = si.propagate_all_lines()
    assert si_result["cycle"] == 1, "SI传播循环应为1"
    results["tests"]["si11_integration"] = {
        "status": "PASS",
        "line_count": len(si_result["line_states"]),
        "cycle": si_result["cycle"]
    }

    # Test 9: 多轮循环
    print("[FCTN] Test 9: 多轮循环 (3 cycles)...")
    multi = si.run_multi_cycle(3)
    assert len(multi["cycles"]) == 3, "应有3个循环结果"
    results["tests"]["multi_cycle"] = {
        "status": "PASS",
        "n_cycles": multi["n_cycles"]
    }

    # 总体状态
    all_pass = all(t["status"] == "PASS" for t in results["tests"].values())
    results["overall_status"] = "ALL_PASS" if all_pass else "PARTIAL"
    results["pass_count"] = sum(1 for t in results["tests"].values() if t["status"] == "PASS")
    results["total_tests"] = len(results["tests"])

    print(f"[FCTN] 验证完成: {results['pass_count']}/{results['total_tests']} 通过")
    return results


def generate_reports(verify_result: Dict[str, Any]):
    """生成JSON和Markdown报告"""
    hub_dir = "/mnt/agents/output/OMNI-HUB/hub"
    os.makedirs(hub_dir, exist_ok=True)

    # JSON报告
    json_path = os.path.join(hub_dir, "FCT_NETWORK_REPORT.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(verify_result, f, ensure_ascii=False, indent=2)

    # Markdown报告
    md_path = os.path.join(hub_dir, "FCT_NETWORK_REPORT.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# OMNI-HUB Field-Circle-Tensor Network Report\n\n")
        f.write(f"**版本**: {verify_result.get('version', 'N/A')}\n\n")
        f.write(f"**时间戳**: {verify_result.get('timestamp', 'N/A')}\n\n")
        f.write(f"**总体状态**: {verify_result.get('overall_status', 'N/A')}\n\n")
        f.write(f"**通过率**: {verify_result.get('pass_count', 0)}/{verify_result.get('total_tests', 0)}\n\n")
        f.write("---\n\n")
        f.write("## 测试详情\n\n")
        for test_name, test_data in verify_result.get('tests', {}).items():
            f.write(f"### {test_name}\n\n")
            f.write(f"- **状态**: {test_data.get('status', 'N/A')}\n")
            for k, v in test_data.items():
                if k != 'status':
                    f.write(f"- **{k}**: {v}\n")
            f.write("\n")
        f.write("---\n\n")
        f.write("## 架构概览\n\n")
        f.write("```\n")
        f.write("FieldState (67维) → CircleTopology (4类圈) → TensorNetwork (rank-3张量) → FieldState\n")
        f.write("     ↑                                                              |\n")
        f.write("     └────────────────── 反馈闭环 ←─────────────────────────────────┘\n")
        f.write("```\n\n")
        f.write("### 11线SI映射\n\n")
        f.write("| 线 | 主域 | 角色 | 维度 |\n")
        f.write("|---|---|---|---|\n")
        for line in LINES:
            binding = SI11Integration().line_bindings.get(line, {})
            f.write(f"| {line} | {binding.get('primary','')} | {binding.get('role','')} | {binding.get('dimension','')} |\n")
        f.write("\n")
        f.write("---\n\n")
        f.write("*Report generated by FCTN v1.2*\n")

    return json_path, md_path


# ────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────
if __name__ == '__main__':
    np.random.seed(42)
    verify_result = verify_fctn()
    json_path, md_path = generate_reports(verify_result)
    print(f"\n报告已生成:")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(f"\n状态: {verify_result['overall_status']}")
