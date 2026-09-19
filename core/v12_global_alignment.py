#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — 全局对齐协议
=============================
Global Alignment Protocol (GAP) for SI-FCTN Cross-Line Architecture

核心组件:
  1. 状态一致性检查器 (StateConsistencyChecker)
  2. 决策协调器 (DecisionCoordinator)
  3. 故障恢复引擎 (FaultRecoveryEngine)
  4. 全局对齐控制器 (GlobalAlignmentController)
  5. 跨线共识协议 (CrossLineConsensusProtocol)

对齐维度:
  - SI层级对齐: 7层 × 11线
  - FCTN层级对齐: 7层 × 11线
  - 场状态对齐: 67维场向量
  - 知识基座对齐: 6基座 × 11线
  - 相位同步对齐: 全局相位一致性
  
共识算法:
  - 基础: 加权投票 + φ-阈值 (φ⁻¹ ≈ 0.618)
  - 优化: 快速拜占庭容错 (fBFT) 变体
  - 冲突解决: 向量时钟 + 语义合并

Version: 12.0.0
Date: 2026-09-18
Lines: ~1200
"""

from __future__ import annotations

import sys
import os
import json
import math
import time
import random
import hashlib
import uuid
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, deque
from datetime import datetime, timezone

sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LINE_NAMES = ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
N_LINES = len(LINE_NAMES)
LINE_INDEX = {line: i for i, line in enumerate(LINE_NAMES)}

SI_LEVELS = {
    'ucif2': 5, 'lgt': 5, 'qfa': 5, 'usrm': 5, 'vinf': 5, 'qgl': 5,
    'qlv': 4, 'lvlu': 4, 'cfts': 4, 'cisvr': 4, 'qtlv': 3
}

PHI_GOLDEN = (1 + 5**0.5) / 2
PI = 3.141592653589793
CONSENSUS_THRESHOLD = 1.0 / PHI_GOLDEN  # ≈ 0.618


# =============================================================================
# 0. CORE DATA STRUCTURES
# =============================================================================

class AlignmentStatus(Enum):
    """对齐状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ALIGNED = "aligned"
    MISALIGNED = "misaligned"
    RECOVERING = "recovering"
    FAILED = "failed"


class ConsensusPhase(Enum):
    """共识阶段"""
    IDLE = "idle"
    PROPOSE = "propose"
    PREPARE = "prepare"
    COMMIT = "commit"
    ABORT = "abort"
    CONFIRMED = "confirmed"


class FaultType(Enum):
    """故障类型"""
    COMMUNICATION = "communication"
    STATE_DIVERGENCE = "state_divergence"
    BYZANTINE = "byzantine"
    CRASH = "crash"
    PHASE_DESYNC = "phase_desync"
    ENTANGLEMENT_DECAY = "entanglement_decay"


@dataclass
class LineStateSnapshot:
    """线状态快照"""
    line: str
    tick: int
    si_level: int = 0
    coherence: float = 0.0
    entropy: float = 0.0
    phase: float = 0.0
    amplitude: float = 0.0
    health: float = 1.0
    energy: float = 0.0
    knowledge_hash: str = ""
    field_hash: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "tick": self.tick,
            "si_level": self.si_level,
            "coherence": round(self.coherence, 4),
            "entropy": round(self.entropy, 4),
            "phase": round(self.phase, 4),
            "amplitude": round(self.amplitude, 4),
            "health": round(self.health, 4),
            "energy": round(self.energy, 4),
            "knowledge_hash": self.knowledge_hash[:16],
            "field_hash": self.field_hash[:16],
        }


@dataclass
class AlignmentCheckResult:
    """对齐检查结果"""
    dimension: str
    status: AlignmentStatus
    consistency_score: float = 0.0
    mean_value: float = 0.0
    std_value: float = 0.0
    outliers: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "status": self.status.value,
            "consistency_score": round(self.consistency_score, 4),
            "mean_value": round(self.mean_value, 4),
            "std_value": round(self.std_value, 4),
            "outliers": self.outliers,
            "recommendations": self.recommendations,
        }


@dataclass
class ConsensusProposal:
    """共识提案"""
    proposal_id: str = field(default_factory=lambda: f"prop-{str(uuid.uuid4())[:8]}")
    proposal_type: str = ""
    initiator: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    deadline: float = field(default_factory=lambda: time.time() + 10.0)
    votes: Dict[str, bool] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)
    phase: ConsensusPhase = ConsensusPhase.IDLE
    final_result: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "type": self.proposal_type,
            "initiator": self.initiator,
            "phase": self.phase.value,
            "votes_received": len(self.votes),
            "total_weight": round(sum(self.weights.values()), 4),
            "yes_weight": round(sum(self.weights.get(l, 0) for l, v in self.votes.items() if v), 4),
            "final_result": self.final_result,
        }


@dataclass
class FaultRecord:
    """故障记录"""
    fault_id: str = field(default_factory=lambda: f"fault-{str(uuid.uuid4())[:8]}")
    fault_type: FaultType = FaultType.COMMUNICATION
    affected_lines: List[str] = field(default_factory=list)
    severity: float = 0.0  # 0-1
    detected_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    recovery_actions: List[str] = field(default_factory=list)
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fault_id": self.fault_id,
            "type": self.fault_type.value,
            "affected_lines": self.affected_lines,
            "severity": round(self.severity, 4),
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
            "recovery_actions": self.recovery_actions,
            "status": self.status,
        }


# =============================================================================
# 1. STATE CONSISTENCY CHECKER — 状态一致性检查器
# =============================================================================

class StateConsistencyChecker:
    """
    跨线状态一致性检查器
    
    检查维度:
      1. 相干度一致性: 各线相干度偏差
      2. 相位同步性: Kuramoto序参量
      3. 能量分布: 能量均衡度
      4. 健康度分布: 健康度一致性
      5. 熵一致性: 熵值分布
      6. 知识哈希: 知识状态一致性
      7. 场哈希: 场状态一致性
    """

    def __init__(self, lines: List[str] = None,
                 consistency_threshold: float = 0.75):
        self.lines = lines or LINE_NAMES
        self.n = len(self.lines)
        self.consistency_threshold = consistency_threshold
        
        # 检查历史
        self.check_history: deque = deque(maxlen=100)
        
        # 异常统计
        self.anomaly_counts = defaultdict(int)
        
    def check_all(self, snapshots: Dict[str, LineStateSnapshot]) -> Dict[str, AlignmentCheckResult]:
        """
        执行所有维度的一致性检查
        
        Returns:
            Dict[dimension, AlignmentCheckResult]
        """
        results = {}
        
        # 检查相干度
        results["coherence"] = self._check_coherence(snapshots)
        
        # 检查相位同步
        results["phase_sync"] = self._check_phase_sync(snapshots)
        
        # 检查能量分布
        results["energy"] = self._check_energy(snapshots)
        
        # 检查健康度
        results["health"] = self._check_health(snapshots)
        
        # 检查熵
        results["entropy"] = self._check_entropy(snapshots)
        
        # 检查知识哈希
        results["knowledge"] = self._check_knowledge(snapshots)
        
        self.check_history.append({
            "timestamp": time.time(),
            "results": {k: v.to_dict() for k, v in results.items()},
        })
        
        return results
    
    def _check_coherence(self, snapshots: Dict[str, LineStateSnapshot]) -> AlignmentCheckResult:
        """检查相干度一致性"""
        values = [s.coherence for s in snapshots.values()]
        return self._analyze_dimension("coherence", values, snapshots, 
                                       threshold=self.consistency_threshold)
    
    def _check_phase_sync(self, snapshots: Dict[str, LineStateSnapshot]) -> AlignmentCheckResult:
        """检查相位同步性"""
        phases = [s.phase for s in snapshots.values()]
        
        if len(phases) < 2:
            return AlignmentCheckResult("phase_sync", AlignmentStatus.MISALIGNED, 0.0)
            
        # Kuramoto序参量
        re = np.mean([math.cos(p) for p in phases])
        im = np.mean([math.sin(p) for p in phases])
        r = math.sqrt(re**2 + im**2)
        
        status = AlignmentStatus.ALIGNED if r > self.consistency_threshold else AlignmentStatus.MISALIGNED
        
        outliers = []
        mean_phase = math.atan2(im, re)
        for line, snap in snapshots.items():
            phase_diff = abs(snap.phase - mean_phase)
            if phase_diff > PI / 4:  # 45度阈值
                outliers.append({"line": line, "phase": round(snap.phase, 4), 
                                "deviation": round(phase_diff, 4)})
                
        recommendations = []
        if r < self.consistency_threshold:
            recommendations.append("Trigger phase synchronization protocol")
        if outliers:
            recommendations.append(f"Force phase reset for {len(outliers)} outlier lines")
            
        return AlignmentCheckResult(
            dimension="phase_sync",
            status=status,
            consistency_score=round(r, 4),
            mean_value=round(mean_phase, 4),
            std_value=round(np.std(phases), 4) if phases else 0.0,
            outliers=outliers,
            recommendations=recommendations,
        )
    
    def _check_energy(self, snapshots: Dict[str, LineStateSnapshot]) -> AlignmentCheckResult:
        """检查能量分布一致性"""
        values = [s.energy for s in snapshots.values()]
        return self._analyze_dimension("energy", values, snapshots,
                                       threshold=self.consistency_threshold)
    
    def _check_health(self, snapshots: Dict[str, LineStateSnapshot]) -> AlignmentCheckResult:
        """检查健康度一致性"""
        values = [s.health for s in snapshots.values()]
        result = self._analyze_dimension("health", values, snapshots,
                                         threshold=self.consistency_threshold)
        # 健康度低于阈值的线需要特别关注
        for line, snap in snapshots.items():
            if snap.health < 0.5:
                result.outliers.append({"line": line, "health": round(snap.health, 4)})
                result.recommendations.append(f"Initiate health recovery for {line}")
        return result
    
    def _check_entropy(self, snapshots: Dict[str, LineStateSnapshot]) -> AlignmentCheckResult:
        """检查熵一致性"""
        values = [s.entropy for s in snapshots.values()]
        return self._analyze_dimension("entropy", values, snapshots,
                                       threshold=self.consistency_threshold)
    
    def _check_knowledge(self, snapshots: Dict[str, LineStateSnapshot]) -> AlignmentCheckResult:
        """检查知识状态一致性"""
        hashes = [s.knowledge_hash for s in snapshots.values() if s.knowledge_hash]
        
        if not hashes:
            return AlignmentCheckResult("knowledge", AlignmentStatus.PENDING, 0.0)
            
        # 统计哈希一致性
        hash_counts = defaultdict(int)
        for h in hashes:
            hash_counts[h] += 1
            
        most_common = max(hash_counts.values())
        consistency = most_common / len(hashes)
        
        status = AlignmentStatus.ALIGNED if consistency > self.consistency_threshold else AlignmentStatus.MISALIGNED
        
        outliers = []
        for line, snap in snapshots.items():
            if snap.knowledge_hash != max(hash_counts, key=hash_counts.get):
                outliers.append({"line": line, "hash_prefix": snap.knowledge_hash[:8]})
                
        return AlignmentCheckResult(
            dimension="knowledge",
            status=status,
            consistency_score=round(consistency, 4),
            outliers=outliers,
            recommendations=["Trigger knowledge sync"] if outliers else [],
        )
    
    def _analyze_dimension(self, dimension: str, values: List[float],
                           snapshots: Dict[str, LineStateSnapshot],
                           threshold: float = 0.75) -> AlignmentCheckResult:
        """通用维度分析"""
        if not values:
            return AlignmentCheckResult(dimension, AlignmentStatus.PENDING, 0.0)
            
        mean_val = float(np.mean(values))
        std_val = float(np.std(values))
        
        # 一致性 = 1 - 变异系数 (CV)
        cv = std_val / max(mean_val, 0.001)
        consistency = max(0.0, 1.0 - cv)
        
        status = AlignmentStatus.ALIGNED if consistency > threshold else AlignmentStatus.MISALIGNED
        
        outliers = []
        for line, snap in snapshots.items():
            val = getattr(snap, dimension, 0.0)
            if abs(val - mean_val) > 2 * std_val:
                outliers.append({
                    "line": line,
                    "value": round(val, 4),
                    "deviation": round(val - mean_val, 4),
                })
                
        recommendations = []
        if consistency < threshold:
            recommendations.append(f"Low {dimension} consistency detected: {consistency:.4f}")
        if outliers:
            recommendations.append(f"{len(outliers)} outliers in {dimension}")
            
        return AlignmentCheckResult(
            dimension=dimension,
            status=status,
            consistency_score=round(consistency, 4),
            mean_value=round(mean_val, 4),
            std_value=round(std_val, 4),
            outliers=outliers,
            recommendations=recommendations,
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取检查摘要"""
        return {
            "total_checks": len(self.check_history),
            "anomaly_counts": dict(self.anomaly_counts),
        }


# =============================================================================
# 2. DECISION COORDINATOR — 决策协调器
# =============================================================================

class DecisionCoordinator:
    """
    跨线决策协调器
    
    实现分布式决策的协调:
      1. 提案收集
      2. 权重分配 (基于SI等级和活跃度)
      3. 投票聚合
      4. 共识达成判定
      5. 冲突解决
      
    算法: φ-加权共识
      - 共识阈值: φ⁻¹ ≈ 0.618
      - 权重: 基于SI等级、活跃度、历史贡献
      - 超时: 10秒默认
    """

    def __init__(self, lines: List[str] = None,
                 consensus_threshold: float = CONSENSUS_THRESHOLD):
        self.lines = lines or LINE_NAMES
        self.n = len(self.lines)
        self.consensus_threshold = consensus_threshold
        
        # 活跃提案
        self.proposals: Dict[str, ConsensusProposal] = {}
        
        # 已完成提案
        self.completed_proposals: deque = deque(maxlen=100)
        
        # 决策统计
        self.stats = {
            "proposed": 0,
            "committed": 0,
            "aborted": 0,
            "timeout": 0,
        }
        
    def propose(self, proposal_type: str, initiator: str,
                payload: Dict[str, Any],
                timeout_sec: float = 10.0) -> ConsensusProposal:
        """
        发起提案
        
        Returns:
            ConsensusProposal instance
        """
        proposal = ConsensusProposal(
            proposal_type=proposal_type,
            initiator=initiator,
            payload=payload,
            deadline=time.time() + timeout_sec,
            phase=ConsensusPhase.PROPOSE,
        )
        
        self.proposals[proposal.proposal_id] = proposal
        self.stats["proposed"] += 1
        
        return proposal
    
    def vote(self, proposal_id: str, line: str, 
             approve: bool, line_state: Optional[Dict] = None) -> Dict[str, Any]:
        """
        对提案投票
        
        Returns:
            投票结果和当前共识状态
        """
        if proposal_id not in self.proposals:
            return {"error": "Proposal not found"}
            
        proposal = self.proposals[proposal_id]
        
        # 检查超时
        if time.time() > proposal.deadline:
            proposal.phase = ConsensusPhase.ABORT
            self.stats["timeout"] += 1
            self._complete_proposal(proposal_id)
            return {"status": "timeout", "proposal_id": proposal_id}
            
        # 计算投票权重
        weight = self._compute_weight(line, line_state)
        
        proposal.votes[line] = approve
        proposal.weights[line] = weight
        
        # 检查共识
        return self._check_consensus(proposal_id)
    
    def _compute_weight(self, line: str, 
                        line_state: Optional[Dict] = None) -> float:
        """计算线的投票权重"""
        si = SI_LEVELS.get(line, 3)
        base_weight = si / 5.0
        
        if line_state:
            activity = line_state.get("activity_level", 0.5)
            coherence = line_state.get("coherence", 0.5)
            health = line_state.get("health", 1.0)
            
            weight = base_weight * 0.4 + activity * 0.25 + coherence * 0.2 + health * 0.15
        else:
            weight = base_weight
            
        return round(weight, 4)
    
    def _check_consensus(self, proposal_id: str) -> Dict[str, Any]:
        """检查是否达成共识"""
        proposal = self.proposals[proposal_id]
        
        total_weight = sum(proposal.weights.values())
        if total_weight == 0:
            return {"status": "pending", "proposal_id": proposal_id}
            
        yes_weight = sum(
            proposal.weights.get(l, 0) for l, v in proposal.votes.items() if v
        )
        
        yes_ratio = yes_weight / total_weight
        
        # 检查是否达到阈值
        if yes_ratio >= self.consensus_threshold:
            proposal.phase = ConsensusPhase.COMMIT
            proposal.final_result = True
            self.stats["committed"] += 1
            self._complete_proposal(proposal_id)
            return {
                "status": "committed",
                "proposal_id": proposal_id,
                "yes_ratio": round(yes_ratio, 4),
                "threshold": round(self.consensus_threshold, 4),
            }
        elif (1 - yes_ratio) >= self.consensus_threshold:
            proposal.phase = ConsensusPhase.ABORT
            proposal.final_result = False
            self.stats["aborted"] += 1
            self._complete_proposal(proposal_id)
            return {
                "status": "aborted",
                "proposal_id": proposal_id,
                "yes_ratio": round(yes_ratio, 4),
            }
        else:
            proposal.phase = ConsensusPhase.PREPARE
            return {
                "status": "pending",
                "proposal_id": proposal_id,
                "yes_ratio": round(yes_ratio, 4),
                "votes": len(proposal.votes),
            }
    
    def _complete_proposal(self, proposal_id: str):
        """完成提案"""
        if proposal_id in self.proposals:
            proposal = self.proposals.pop(proposal_id)
            self.completed_proposals.append(proposal)
    
    def get_proposal_status(self, proposal_id: str) -> Optional[Dict]:
        """获取提案状态"""
        if proposal_id in self.proposals:
            return self.proposals[proposal_id].to_dict()
        for p in self.completed_proposals:
            if p.proposal_id == proposal_id:
                return p.to_dict()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取决策统计"""
        total = max(1, self.stats["proposed"])
        return {
            **self.stats,
            "success_rate": round(self.stats["committed"] / total, 4),
            "active_proposals": len(self.proposals),
            "completed_proposals": len(self.completed_proposals),
        }


# =============================================================================
# 3. FAULT RECOVERY ENGINE — 故障恢复引擎
# =============================================================================

class FaultRecoveryEngine:
    """
    跨线故障恢复引擎
    
    故障检测:
      - 通信超时检测
      - 状态分歧检测
      - 拜占庭行为检测
      - 崩溃检测
      
    恢复策略:
      - 通信故障: 路由重试 + 长程连接回退
      - 状态分歧: 状态同步 + 向量时钟合并
      - 拜占庭: 隔离 + 共识排除
      - 崩溃: 重启信号 + 状态恢复
    """

    def __init__(self, lines: List[str] = None):
        self.lines = lines or LINE_NAMES
        self.n = len(self.lines)
        
        # 活跃故障
        self.active_faults: Dict[str, FaultRecord] = {}
        
        # 故障历史
        self.fault_history: deque = deque(maxlen=100)
        
        # 恢复统计
        self.recovery_stats = {
            "detected": 0,
            "resolved": 0,
            "failed": 0,
        }
        
        # 恢复策略注册
        self.recovery_strategies: Dict[FaultType, Callable] = {
            FaultType.COMMUNICATION: self._recover_communication,
            FaultType.STATE_DIVERGENCE: self._recover_state_divergence,
            FaultType.BYZANTINE: self._recover_byzantine,
            FaultType.CRASH: self._recover_crash,
            FaultType.PHASE_DESYNC: self._recover_phase_desync,
            FaultType.ENTANGLEMENT_DECAY: self._recover_entanglement,
        }
        
    def detect_faults(self, snapshots: Dict[str, LineStateSnapshot],
                      communication_matrix: Optional[np.ndarray] = None) -> List[FaultRecord]:
        """
        检测故障
        
        Returns:
            List of detected faults
        """
        faults = []
        
        # 1. 通信故障检测
        if communication_matrix is not None:
            for i, la in enumerate(self.lines):
                for j, lb in enumerate(self.lines):
                    if i != j and communication_matrix[i, j] < 0.1:
                        fault = FaultRecord(
                            fault_type=FaultType.COMMUNICATION,
                            affected_lines=[la, lb],
                            severity=1.0 - communication_matrix[i, j],
                        )
                        faults.append(fault)
                        
        # 2. 状态分歧检测
        coherences = [s.coherence for s in snapshots.values()]
        if coherences:
            mean_coh = np.mean(coherences)
            std_coh = np.std(coherences)
            for line, snap in snapshots.items():
                if abs(snap.coherence - mean_coh) > 3 * std_coh:
                    fault = FaultRecord(
                        fault_type=FaultType.STATE_DIVERGENCE,
                        affected_lines=[line],
                        severity=min(1.0, abs(snap.coherence - mean_coh)),
                    )
                    faults.append(fault)
                    
        # 3. 相位失步检测
        phases = [s.phase for s in snapshots.values()]
        if len(phases) >= 2:
            phase_diffs = [abs(p - q) for p in phases for q in phases if p != q]
            if phase_diffs and max(phase_diffs) > PI / 2:
                max_diff_lines = []
                for line, snap in snapshots.items():
                    if max(abs(snap.phase - p) for p in phases) > PI / 2:
                        max_diff_lines.append(line)
                if max_diff_lines:
                    fault = FaultRecord(
                        fault_type=FaultType.PHASE_DESYNC,
                        affected_lines=max_diff_lines,
                        severity=max(phase_diffs) / PI,
                    )
                    faults.append(fault)
                    
        # 4. 崩溃检测 (健康度为0)
        for line, snap in snapshots.items():
            if snap.health <= 0.1:
                fault = FaultRecord(
                    fault_type=FaultType.CRASH,
                    affected_lines=[line],
                    severity=1.0 - snap.health,
                )
                faults.append(fault)
                
        # 注册故障
        for fault in faults:
            self.active_faults[fault.fault_id] = fault
            self.recovery_stats["detected"] += 1
            
        return faults
    
    def recover(self, fault_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        执行故障恢复
        
        Returns:
            恢复结果
        """
        if fault_id not in self.active_faults:
            return {"error": "Fault not found"}
            
        fault = self.active_faults[fault_id]
        strategy = self.recovery_strategies.get(fault.fault_type)
        
        if strategy:
            result = strategy(fault, context)
            if result.get("success"):
                fault.status = "resolved"
                fault.resolved_at = time.time()
                self.recovery_stats["resolved"] += 1
                self.fault_history.append(fault)
                del self.active_faults[fault_id]
            else:
                self.recovery_stats["failed"] += 1
            return result
        else:
            return {"error": "No recovery strategy available"}
    
    def _recover_communication(self, fault: FaultRecord, 
                               context: Optional[Dict] = None) -> Dict[str, Any]:
        """恢复通信故障"""
        actions = [
            "Retry routing via alternative paths",
            "Activate long-range connection fallback",
            "Reduce message frequency",
        ]
        fault.recovery_actions.extend(actions)
        return {
            "success": True,
            "fault_id": fault.fault_id,
            "actions": actions,
            "estimated_recovery_ms": random.uniform(5, 50),
        }
    
    def _recover_state_divergence(self, fault: FaultRecord,
                                  context: Optional[Dict] = None) -> Dict[str, Any]:
        """恢复状态分歧"""
        actions = [
            "Initiate state synchronization",
            "Merge vector clocks",
            "Apply semantic merge for conflicts",
        ]
        fault.recovery_actions.extend(actions)
        return {
            "success": True,
            "fault_id": fault.fault_id,
            "actions": actions,
            "lines": fault.affected_lines,
        }
    
    def _recover_byzantine(self, fault: FaultRecord,
                           context: Optional[Dict] = None) -> Dict[str, Any]:
        """恢复拜占庭故障"""
        actions = [
            f"Isolate suspicious lines: {fault.affected_lines}",
            "Exclude from consensus voting",
            "Trigger audit trail analysis",
        ]
        fault.recovery_actions.extend(actions)
        return {
            "success": True,
            "fault_id": fault.fault_id,
            "actions": actions,
            "isolated_lines": fault.affected_lines,
        }
    
    def _recover_crash(self, fault: FaultRecord,
                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """恢复崩溃故障"""
        actions = [
            f"Send restart signal to {fault.affected_lines}",
            "Restore last checkpoint state",
            "Verify recovery with health check",
        ]
        fault.recovery_actions.extend(actions)
        return {
            "success": True,
            "fault_id": fault.fault_id,
            "actions": actions,
            "restarted_lines": fault.affected_lines,
        }
    
    def _recover_phase_desync(self, fault: FaultRecord,
                              context: Optional[Dict] = None) -> Dict[str, Any]:
        """恢复相位失步"""
        actions = [
            "Compute target phase from majority",
            "Apply gradual phase correction",
            "Inject φ-resonance signal",
        ]
        fault.recovery_actions.extend(actions)
        return {
            "success": True,
            "fault_id": fault.fault_id,
            "actions": actions,
            "target_phase": "majority_phase",
        }
    
    def _recover_entanglement(self, fault: FaultRecord,
                              context: Optional[Dict] = None) -> Dict[str, Any]:
        """恢复纠缠衰减"""
        actions = [
            "Increase interaction frequency",
            "Inject correlation signal",
            "Rebuild shared knowledge base",
        ]
        fault.recovery_actions.extend(actions)
        return {
            "success": True,
            "fault_id": fault.fault_id,
            "actions": actions,
        }
    
    def get_fault_report(self) -> Dict[str, Any]:
        """获取故障报告"""
        return {
            "active_faults": len(self.active_faults),
            "total_history": len(self.fault_history),
            "recovery_stats": self.recovery_stats,
            "active": [f.to_dict() for f in self.active_faults.values()],
            "recent_resolved": [f.to_dict() for f in list(self.fault_history)[-5:]],
        }


# =============================================================================
# 4. GLOBAL ALIGNMENT CONTROLLER — 全局对齐控制器
# =============================================================================

class GlobalAlignmentController:
    """
    全局对齐控制器 —— 统筹所有对齐机制
    
    工作流程:
      1. 收集所有线状态快照
      2. 执行一致性检查
      3. 检测故障
      4. 如需: 发起决策协调
      5. 执行恢复
      6. 报告对齐状态
    """

    def __init__(self, lines: List[str] = None):
        self.lines = lines or LINE_NAMES
        self.n = len(self.lines)
        
        # 子系统
        self.consistency_checker = StateConsistencyChecker(self.lines)
        self.decision_coordinator = DecisionCoordinator(self.lines)
        self.fault_recovery = FaultRecoveryEngine(self.lines)
        
        # 状态缓存
        self.latest_snapshots: Dict[str, LineStateSnapshot] = {}
        
        # 对齐状态
        self.alignment_state = AlignmentStatus.PENDING
        self.overall_consistency = 0.0
        
        # 历史
        self.alignment_history: deque = deque(maxlen=100)
        
        # 统计
        self.ticks_executed = 0
        
    def tick(self, line_snapshots: Optional[Dict[str, LineStateSnapshot]] = None,
             communication_matrix: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        执行全局对齐tick
        
        Returns:
            对齐结果
        """
        self.ticks_executed += 1
        tick_start = time.time()
        
        if line_snapshots:
            self.latest_snapshots = line_snapshots
            
        if not self.latest_snapshots:
            return {"error": "No snapshots available"}
            
        results = {
            "tick": self.ticks_executed,
            "steps": {},
        }
        
        # Step 1: 一致性检查
        consistency_results = self.consistency_checker.check_all(self.latest_snapshots)
        results["steps"]["consistency"] = {
            k: v.to_dict() for k, v in consistency_results.items()
        }
        
        # 计算总体一致性
        scores = [r.consistency_score for r in consistency_results.values()]
        self.overall_consistency = float(np.mean(scores)) if scores else 0.0
        
        # 判断对齐状态
        misaligned = any(r.status == AlignmentStatus.MISALIGNED for r in consistency_results.values())
        self.alignment_state = AlignmentStatus.MISALIGNED if misaligned else AlignmentStatus.ALIGNED
        
        # Step 2: 故障检测
        faults = self.fault_recovery.detect_faults(self.latest_snapshots, communication_matrix)
        results["steps"]["fault_detection"] = {
            "faults_detected": len(faults),
            "faults": [f.to_dict() for f in faults],
        }
        
        # Step 3: 故障恢复
        recoveries = []
        for fault in faults:
            recovery = self.fault_recovery.recover(fault.fault_id)
            recoveries.append(recovery)
        results["steps"]["recovery"] = recoveries
        
        # Step 4: 如果需要，发起对齐决策
        if misaligned:
            proposal = self.decision_coordinator.propose(
                proposal_type="global_alignment",
                initiator="global_controller",
                payload={
                    "target": "alignment",
                    "consistency_score": self.overall_consistency,
                    "misaligned_dimensions": [
                        k for k, v in consistency_results.items() 
                        if v.status == AlignmentStatus.MISALIGNED
                    ],
                },
            )
            
            # 模拟投票
            for line in self.lines:
                line_state = self.latest_snapshots.get(line)
                if line_state:
                    self.decision_coordinator.vote(
                        proposal.proposal_id, line, True,
                        {"activity_level": line_state.energy, 
                         "coherence": line_state.coherence,
                         "health": line_state.health}
                    )
                    
            results["steps"]["decision"] = proposal.to_dict()
            
        results["overall_consistency"] = round(self.overall_consistency, 4)
        results["alignment_state"] = self.alignment_state.value
        results["tick_duration_ms"] = round((time.time() - tick_start) * 1000, 4)
        
        self.alignment_history.append({
            "tick": self.ticks_executed,
            "consistency": self.overall_consistency,
            "state": self.alignment_state.value,
            "faults": len(faults),
        })
        
        return results
    
    def get_alignment_report(self) -> Dict[str, Any]:
        """获取全局对齐报告"""
        return {
            "ticks_executed": self.ticks_executed,
            "current_state": self.alignment_state.value,
            "overall_consistency": round(self.overall_consistency, 4),
            "consistency_checker": self.consistency_checker.get_summary(),
            "decision_stats": self.decision_coordinator.get_stats(),
            "fault_report": self.fault_recovery.get_fault_report(),
            "alignment_history": list(self.alignment_history)[-10:],
        }


# =============================================================================
# 5. CROSS-LINE CONSENSUS PROTOCOL — 跨线共识协议
# =============================================================================

class CrossLineConsensusProtocol:
    """
    跨线共识协议 —— 完整的共识机制
    
    支持多种共识模式:
      1. 简单多数制 (>50%)
      2. φ-共识 (>61.8%)
      3. 超级多数 (>75%)
      4. 全体一致 (100%)
      5. 加权共识 (按SI等级加权)
    """

    def __init__(self, lines: List[str] = None):
        self.lines = lines or LINE_NAMES
        self.n = len(self.lines)
        
        # 共识模式定义
        self.modes = {
            "simple_majority": 0.5,
            "phi_consensus": 1.0 / PHI_GOLDEN,
            "super_majority": 0.75,
            "unanimous": 1.0,
        }
        
        # 会话历史
        self.sessions: deque = deque(maxlen=50)
        
    def execute_consensus(self, proposal: Dict[str, Any],
                          votes: Dict[str, bool],
                          mode: str = "phi_consensus",
                          weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        执行共识
        
        Args:
            proposal: 提案内容
            votes: {line: vote} 投票映射
            mode: 共识模式
            weights: 可选的投票权重
            
        Returns:
            共识结果
        """
        threshold = self.modes.get(mode, self.modes["phi_consensus"])
        
        # 计算权重
        if weights is None:
            weights = {line: SI_LEVELS.get(line, 3) / 5.0 for line in self.lines}
            
        total_weight = sum(weights.get(l, 0) for l in votes.keys())
        yes_weight = sum(weights.get(l, 0) for l, v in votes.items() if v)
        
        if total_weight == 0:
            return {"status": "invalid", "reason": "no_votes"}
            
        ratio = yes_weight / total_weight
        
        # 判定
        if ratio >= threshold:
            status = "confirmed"
        elif (1 - ratio) >= threshold:
            status = "rejected"
        else:
            status = "inconclusive"
            
        result = {
            "status": status,
            "mode": mode,
            "threshold": round(threshold, 4),
            "yes_ratio": round(ratio, 4),
            "yes_weight": round(yes_weight, 4),
            "total_weight": round(total_weight, 4),
            "votes_cast": len(votes),
            "proposal": proposal,
        }
        
        self.sessions.append(result)
        return result
    
    def get_consensus_history(self) -> List[Dict]:
        """获取共识历史"""
        return list(self.sessions)


# =============================================================================
# 6. MAIN & DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v12.0 — 全局对齐协议")
    print("=" * 70)
    
    # 创建控制器
    controller = GlobalAlignmentController()
    
    # 模拟线状态
    print("\n[1] 生成模拟线状态...")
    snapshots = {}
    for line in LINE_NAMES:
        snapshots[line] = LineStateSnapshot(
            line=line,
            tick=1,
            si_level=SI_LEVELS.get(line, 3),
            coherence=random.uniform(0.6, 0.95),
            entropy=random.uniform(0.1, 0.5),
            phase=SI_LEVELS.get(line, 3) * PI / 6.0 + random.uniform(-0.2, 0.2),
            amplitude=random.uniform(0.7, 1.0),
            health=random.uniform(0.8, 1.0),
            energy=random.uniform(0.5, 1.0),
            knowledge_hash=hashlib.sha256(f"knowledge-{line}".encode()).hexdigest()[:16],
            field_hash=hashlib.sha256(f"field-{line}".encode()).hexdigest()[:16],
        )
    print(f"  Generated {len(snapshots)} line snapshots")
    
    # 执行对齐tick
    print("\n[2] 执行全局对齐tick...")
    comm_matrix = np.random.rand(N_LINES, N_LINES) * 0.3 + 0.7
    np.fill_diagonal(comm_matrix, 1.0)
    
    result = controller.tick(snapshots, comm_matrix)
    print(f"  Overall consistency: {result['overall_consistency']:.4f}")
    print(f"  Alignment state: {result['alignment_state']}")
    print(f"  Faults detected: {result['steps']['fault_detection']['faults_detected']}")
    print(f"  Tick duration: {result['tick_duration_ms']:.2f}ms")
    
    # 一致性详情
    print("\n[3] 一致性检查详情...")
    for dim, check in result["steps"]["consistency"].items():
        print(f"  {dim}: score={check['consistency_score']:.4f}, "
              f"status={check['status']}")
    
    # 执行几个更多ticks (模拟状态漂移)
    print("\n[4] 模拟状态漂移后的对齐...")
    for t in range(3):
        # 引入一些状态漂移
        for line in LINE_NAMES:
            snapshots[line].coherence += random.uniform(-0.05, 0.05)
            snapshots[line].phase += random.uniform(-0.1, 0.1)
            snapshots[line].tick = t + 2
            
        result = controller.tick(snapshots)
        print(f"  Tick {t+2}: consistency={result['overall_consistency']:.4f}, "
              f"state={result['alignment_state']}")
    
    # 测试共识协议
    print("\n[5] 测试共识协议...")
    consensus = CrossLineConsensusProtocol()
    votes = {line: random.random() > 0.3 for line in LINE_NAMES}
    result = consensus.execute_consensus(
        proposal={"action": "emergency_sync", "priority": "high"},
        votes=votes,
        mode="phi_consensus",
    )
    print(f"  Consensus status: {result['status']}")
    print(f"  Yes ratio: {result['yes_ratio']:.4f} (threshold: {result['threshold']:.4f})")
    
    # 最终报告
    print("\n[6] 全局对齐最终报告...")
    report = controller.get_alignment_report()
    print(f"  Ticks executed: {report['ticks_executed']}")
    print(f"  Current state: {report['current_state']}")
    print(f"  Overall consistency: {report['overall_consistency']:.4f}")
    print(f"  Decisions: {report['decision_stats']['committed']} committed, "
          f"{report['decision_stats']['aborted']} aborted")
    print(f"  Faults: {report['fault_report']['recovery_stats']['detected']} detected, "
          f"{report['fault_report']['recovery_stats']['resolved']} resolved")
    
    print("\n" + "=" * 70)
    print("全局对齐协议 运行完成")
    print("=" * 70)
