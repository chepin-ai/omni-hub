"""
OMNI-HUB v192 — DistributedConsensusLayer
分布式共识层

核心功能：
1. RaftNode            — Raft共识节点
2. BFTReplica          — BFT拜占庭容错副本
3. ConsensusCoordinator — 共识协调器
4. LogReplicator       — 日志复制器
5. LeaderElection      — 领导者选举
6. DistributedConsensusLayer — 统合引擎

映射：
- 共识 = saṃmati（一致同意）
- 领导 = netṛ（领袖）
- 复制 = anukaraṇa（复制）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
import random
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class NodeState(Enum):
    """节点状态"""
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2
    BYZANTINE = 3


class ConsensusStatus(Enum):
    """共识状态"""
    PENDING = 0
    COMMITTED = 1
    REJECTED = 2
    TIMEOUT = 3


class ConsensusMode(Enum):
    """共识模式"""
    RAFT = 0
    BFT = 1
    HYBRID = 2


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class LogEntry:
    """日志条目"""
    index: int
    term: int
    command: str
    timestamp: float
    checksum: str = ""


@dataclass
class ConsensusMessage:
    """共识消息"""
    msg_id: str
    msg_type: str  # REQUEST_VOTE, APPEND_ENTRIES, PREPARE, COMMIT
    sender: str
    term: int
    payload: Dict
    timestamp: float


@dataclass
class ConsensusResult:
    """共识结果"""
    result_id: str
    entry: LogEntry
    status: ConsensusStatus
    confirmations: int
    rejections: int
    latency_ms: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: Raft节点
# ═══════════════════════════════════════════════════════════════

class RaftNode:
    """Raft共识节点 — saṃmati"""

    def __init__(self, node_id: str, total_nodes: int = 5):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        self.leader_id = None
        self.votes_received: Set[str] = set()
        self.heartbeat_timeout = 0.15  # 150ms
        self.election_timeout = 0.3 + (hash(node_id) % 1000) / 10000.0  # 300-400ms
        self.last_heartbeat = time.time()

    def request_vote(self, term: int, candidate_id: str) -> bool:
        """响应投票请求"""
        if term > self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.voted_for = None

        if term < self.current_term:
            return False
        if self.voted_for is not None and self.voted_for != candidate_id:
            return False

        # 检查日志是否至少一样新
        last_log_index = len(self.log)
        candidate_last = self._get_candidate_last_log(candidate_id)
        if candidate_last < last_log_index:
            return False

        self.voted_for = candidate_id
        return True

    def _get_candidate_last_log(self, candidate_id: str) -> int:
        # 简化：假设候选人的日志索引
        return hash(candidate_id) % 10

    def append_entries(self, term: int, leader_id: str, entries: List[LogEntry]) -> bool:
        """追加日志条目"""
        if term < self.current_term:
            return False

        self.current_term = term
        self.leader_id = leader_id
        self.state = NodeState.FOLLOWER
        self.last_heartbeat = time.time()

        for entry in entries:
            if entry.index > len(self.log):
                self.log.append(entry)
            elif entry.index <= len(self.log):
                # 检查冲突
                if entry.index > 0 and self.log[entry.index - 1].term != entry.term:
                    self.log = self.log[:entry.index - 1]
                    self.log.append(entry)

        return True

    def start_election(self) -> ConsensusMessage:
        """开始选举"""
        self.current_term += 1
        self.state = NodeState.CANDIDATE
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}

        return ConsensusMessage(
            msg_id=f"vote_req_{self.node_id}_{self.current_term}",
            msg_type="REQUEST_VOTE",
            sender=self.node_id,
            term=self.current_term,
            payload={"last_log_index": len(self.log)},
            timestamp=time.time()
        )

    def become_leader(self):
        """成为领导者"""
        if len(self.votes_received) > self.total_nodes // 2:
            self.state = NodeState.LEADER
            self.leader_id = self.node_id

    def get_report(self) -> Dict:
        return {
            "node_id": self.node_id,
            "state": self.state.name,
            "term": self.current_term,
            "log_length": len(self.log),
            "commit_index": self.commit_index,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: BFT副本
# ═══════════════════════════════════════════════════════════════

class BFTReplica:
    """BFT拜占庭容错副本"""

    def __init__(self, replica_id: str, total_replicas: int = 7):
        self.replica_id = replica_id
        self.total_replicas = total_replicas
        self.fault_tolerance = (total_replicas - 1) // 3  # f = (n-1)/3
        self.sequence_num = 0
        self.prepared: Dict[int, Set[str]] = defaultdict(set)
        self.committed: Dict[int, Set[str]] = defaultdict(set)
        self.is_byzantine = False

    def set_byzantine(self, byzantine: bool = True):
        self.is_byzantine = byzantine

    def prepare(self, seq: int, digest: str) -> bool:
        """PREPARE阶段"""
        if self.is_byzantine:
            # 拜占庭节点可能返回随机结果
            return hash(f"{self.replica_id}:{seq}") % 2 == 0
        self.prepared[seq].add(self.replica_id)
        return True

    def commit(self, seq: int) -> bool:
        """COMMIT阶段"""
        if self.is_byzantine:
            return hash(f"{self.replica_id}:{seq}:commit") % 2 == 0
        if len(self.prepared.get(seq, set())) >= 2 * self.fault_tolerance:
            self.committed[seq].add(self.replica_id)
            return True
        return False

    def check_commit_certificate(self, seq: int) -> bool:
        """检查是否达成commit证书"""
        return len(self.committed.get(seq, set())) >= 2 * self.fault_tolerance + 1

    def get_report(self) -> Dict:
        return {
            "replica_id": self.replica_id,
            "fault_tolerance": self.fault_tolerance,
            "is_byzantine": self.is_byzantine,
            "prepared_count": len(self.prepared),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 共识协调器
# ═══════════════════════════════════════════════════════════════

class ConsensusCoordinator:
    """共识协调器 — 选择Raft或BFT"""

    def __init__(self, mode: ConsensusMode = ConsensusMode.HYBRID):
        self.mode = mode
        self.results: deque = deque(maxlen=500)

    def coordinate(self, nodes: List[RaftNode], replicas: List[BFTReplica],
                   command: str) -> ConsensusResult:
        """协调共识"""
        start = time.time()

        if self.mode == ConsensusMode.RAFT:
            result = self._raft_consensus(nodes, command)
        elif self.mode == ConsensusMode.BFT:
            result = self._bft_consensus(replicas, command)
        else:  # HYBRID
            result = self._hybrid_consensus(nodes, replicas, command)

        latency = (time.time() - start) * 1000
        result.latency_ms = latency
        self.results.append(result)
        return result

    def _raft_consensus(self, nodes: List[RaftNode], command: str) -> ConsensusResult:
        # 找leader
        leader = next((n for n in nodes if n.state == NodeState.LEADER), None)
        if leader is None:
            return ConsensusResult(
                result_id=f"raft_{int(time.time()*1000)}",
                entry=LogEntry(0, 0, command, time.time()),
                status=ConsensusStatus.TIMEOUT,
                confirmations=0,
                rejections=len(nodes),
                latency_ms=0
            )

        entry = LogEntry(
            index=len(leader.log) + 1,
            term=leader.current_term,
            command=command,
            timestamp=time.time()
        )

        # 复制到follower
        confirmations = 1
        for node in nodes:
            if node.node_id != leader.node_id:
                if node.append_entries(leader.current_term, leader.node_id, [entry]):
                    confirmations += 1

        status = ConsensusStatus.COMMITTED if confirmations > len(nodes) // 2 else ConsensusStatus.REJECTED
        return ConsensusResult(
            result_id=f"raft_{int(time.time()*1000)}",
            entry=entry,
            status=status,
            confirmations=confirmations,
            rejections=len(nodes) - confirmations,
            latency_ms=0
        )

    def _bft_consensus(self, replicas: List[BFTReplica], command: str) -> ConsensusResult:
        seq = hash(command) % 10000
        digest = hashlib.sha256(command.encode()).hexdigest()[:16]

        # PREPARE阶段
        prepare_count = 0
        for rep in replicas:
            if rep.prepare(seq, digest):
                prepare_count += 1

        # COMMIT阶段
        commit_count = 0
        for rep in replicas:
            if rep.commit(seq):
                commit_count += 1

        f = (len(replicas) - 1) // 3
        status = ConsensusStatus.COMMITTED if commit_count >= 2 * f + 1 else ConsensusStatus.REJECTED

        return ConsensusResult(
            result_id=f"bft_{int(time.time()*1000)}",
            entry=LogEntry(index=seq, term=0, command=command, timestamp=time.time()),
            status=status,
            confirmations=commit_count,
            rejections=len(replicas) - commit_count,
            latency_ms=0
        )

    def _hybrid_consensus(self, nodes: List[RaftNode], replicas: List[BFTReplica],
                          command: str) -> ConsensusResult:
        """混合：先用Raft选leader，再用BFT提交"""
        raft_result = self._raft_consensus(nodes, command)
        if raft_result.status != ConsensusStatus.COMMITTED:
            return raft_result
        bft_result = self._bft_consensus(replicas, command)
        bft_result.entry = raft_result.entry
        return bft_result

    def get_report(self) -> Dict:
        committed = sum(1 for r in self.results if r.status == ConsensusStatus.COMMITTED)
        return {
            "total_consensus": len(self.results),
            "committed": committed,
            "commit_rate": committed / max(1, len(self.results)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 日志复制器
# ═══════════════════════════════════════════════════════════════

class LogReplicator:
    """日志复制器 — anukaraṇa"""

    def __init__(self):
        self.replication_log: deque = deque(maxlen=1000)
        self.replica_states: Dict[str, int] = {}  # node_id -> next_index

    def replicate(self, leader: RaftNode, followers: List[RaftNode],
                  entry: LogEntry) -> Dict[str, bool]:
        """复制日志到follower"""
        results = {}
        for follower in followers:
            if follower.node_id == leader.node_id:
                continue
            success = follower.append_entries(leader.current_term, leader.node_id, [entry])
            results[follower.node_id] = success
            if success:
                self.replica_states[follower.node_id] = entry.index

        self.replication_log.append({
            "entry": entry,
            "results": results,
            "timestamp": time.time()
        })
        return results

    def get_replication_lag(self) -> Dict[str, int]:
        """获取各节点的复制延迟"""
        lags = {}
        max_index = max(self.replica_states.values(), default=0)
        for node_id, idx in self.replica_states.items():
            lags[node_id] = max_index - idx
        return lags

    def get_report(self) -> Dict:
        return {
            "replications": len(self.replication_log),
            "replica_states": dict(self.replica_states),
            "lag": self.get_replication_lag(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 领导者选举
# ═══════════════════════════════════════════════════════════════

class LeaderElection:
    """领导者选举 — netṛ"""

    def __init__(self):
        self.elections: deque = deque(maxlen=100)

    def elect(self, nodes: List[RaftNode]) -> Optional[RaftNode]:
        """执行选举"""
        # 模拟选举过程
        candidates = [n for n in nodes if n.state in (NodeState.CANDIDATE, NodeState.FOLLOWER)]
        if not candidates:
            return None

        # 每个candidate发起投票
        for candidate in candidates:
            if candidate.state == NodeState.FOLLOWER:
                # 超时后变成candidate
                if time.time() - candidate.last_heartbeat > candidate.election_timeout:
                    candidate.start_election()

        # 收集投票
        for candidate in candidates:
            if candidate.state != NodeState.CANDIDATE:
                continue
            for node in nodes:
                if node.node_id != candidate.node_id:
                    if node.request_vote(candidate.current_term, candidate.node_id):
                        candidate.votes_received.add(node.node_id)
            candidate.become_leader()

        leader = next((n for n in nodes if n.state == NodeState.LEADER), None)
        self.elections.append({
            "leader": leader.node_id if leader else None,
            "term": max((n.current_term for n in nodes), default=0),
            "timestamp": time.time()
        })
        return leader

    def get_report(self) -> Dict:
        return {"elections": len(self.elections)}


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — DistributedConsensusLayer v192
# ═══════════════════════════════════════════════════════════════

class DistributedConsensusLayer:
    """
    OMNI-HUB v192 分布式共识层

    saṃmati · netṛ · anukaraṇa — 一致、领袖、复制
    """

    VERSION = "192.0.0"

    def __init__(self, node_count: int = 5, replica_count: int = 7):
        self.nodes = [RaftNode(f"raft_{i}", node_count) for i in range(node_count)]
        self.replicas = [BFTReplica(f"bft_{i}", replica_count) for i in range(replica_count)]
        self.coordinator = ConsensusCoordinator(ConsensusMode.HYBRID)
        self.replicator = LogReplicator()
        self.election = LeaderElection()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def propose(self, command: str) -> ConsensusResult:
        """提议命令"""
        # 确保有leader
        leader = next((n for n in self.nodes if n.state == NodeState.LEADER), None)
        if leader is None:
            leader = self.election.elect(self.nodes)

        return self.coordinator.coordinate(self.nodes, self.replicas, command)

    def replicate_alliance_state(self, state: Dict[str, Any]) -> Dict:
        """复制联盟状态"""
        command = json.dumps(state, sort_keys=True, default=str)
        result = self.propose(command)

        if result.status == ConsensusStatus.COMMITTED:
            followers = [n for n in self.nodes if n.state != NodeState.LEADER]
            leader = next((n for n in self.nodes if n.state == NodeState.LEADER), self.nodes[0])
            replication = self.replicator.replicate(leader, followers, result.entry)
            return {
                "consensus": "COMMITTED",
                "replication": replication,
                "entry_index": result.entry.index,
            }

        return {"consensus": result.status.name, "replication": {}}

    def simulate_byzantine(self, replica_ids: List[str]):
        """模拟拜占庭故障"""
        for rep in self.replicas:
            if rep.replica_id in replica_ids:
                rep.set_byzantine(True)

    def run_cycle(self, alliance_state: Dict[str, Any] = None) -> Dict:
        """运行共识周期"""
        self.cycle_count += 1
        alliance_state = alliance_state or {}

        # 1. 选举检查
        leader = self.election.elect(self.nodes)

        # 2. 提议状态
        result = self.replicate_alliance_state(alliance_state)

        summary = {
            "cycle": self.cycle_count,
            "leader": leader.node_id if leader else None,
            "consensus_status": result.get("consensus", "UNKNOWN"),
            "log_index": result.get("entry_index", 0),
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        leader = next((n for n in self.nodes if n.state == NodeState.LEADER), None)
        byzantine_count = sum(1 for r in self.replicas if r.is_byzantine)
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "leader": leader.node_id if leader else None,
            "nodes": [n.get_report() for n in self.nodes],
            "replicas": [r.get_report() for r in self.replicas],
            "coordinator": self.coordinator.get_report(),
            "replicator": self.replicator.get_report(),
            "election": self.election.get_report(),
            "byzantine_replicas": byzantine_count,
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_dcl_instance: Optional[DistributedConsensusLayer] = None


def get_distributed_consensus_layer() -> DistributedConsensusLayer:
    global _dcl_instance
    if _dcl_instance is None:
        _dcl_instance = DistributedConsensusLayer()
    return _dcl_instance


if __name__ == "__main__":
    dcl = DistributedConsensusLayer()
    print(f"DistributedConsensusLayer v{dcl.VERSION} initialized")
    print(f"Status: {json.dumps(dcl.get_status(), indent=2, default=str)}")
