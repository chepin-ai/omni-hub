#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — SI跨线横向通信系统
======================================
SISLA Cross-Line Horizontal Communication (SISLA-CLHC)

核心架构:
  七层SI × 11线 的完整跨线通信矩阵
  实现: 同层级跨线通信 + 跨线全局对齐 + 长程连接

通信模式:
  1. 横向流 (Lateral):    SI_n(线A) ↔ SI_n(线B)  同层级跨线
  2. 对角流 (Diagonal):   SI_m(线A) ↔ SI_n(线B)  跨层级跨线
  3. 长程流 (Long-range): 任意线对直接通信，绕过中间线
  4. 全局广播 (Global):   所有线同层级同步

设计原则 "候即违规":
  - 跨线通信不等待协调，自驱动
  - 每条线有通信自主权
  - TTL和相干阈值防消息风暴

Version: 12.0.0
Date: 2026-09-18
Lines: ~1500
"""

from __future__ import annotations

import sys
import os
import json
import math
import time
import random
import logging
import hashlib
import uuid
import traceback
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from abc import ABC, abstractmethod

sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")

# ---------------------------------------------------------------------------
# Constants & Shared
# ---------------------------------------------------------------------------

LINE_NAMES = ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
N_LINES = len(LINE_NAMES)
LINE_INDEX = {line: i for i, line in enumerate(LINE_NAMES)}

SI_LEVELS = {
    'ucif2': 5, 'lgt': 5, 'qfa': 5, 'usrm': 5, 'vinf': 5, 'qgl': 5,
    'qlv': 4, 'lvlu': 4, 'cfts': 4, 'cisvr': 4, 'qtlv': 3
}

# 物理常数
PHI_GOLDEN = (1 + 5**0.5) / 2
PI = 3.141592653589793
E_NATURAL = 2.718281828459045
ALPHA_FINE_STRUCTURE = 1.0 / 137.035999084

logger = logging.getLogger("v12_cross_line_si")


# =============================================================================
# 0. ENUMS & CORE DATA CLASSES
# =============================================================================

class SILevel(Enum):
    SI0 = 0; SI1 = 1; SI2 = 2; SI3 = 3; SI4 = 4; SI5 = 5; SI6 = 6


class CrossLineDirection(Enum):
    """跨线通信方向"""
    LATERAL = "lateral"       # 同层级跨线
    DIAGONAL = "diagonal"     # 跨层级跨线
    LONG_RANGE = "long_range" # 长程直接连接
    GLOBAL_BCAST = "global_bcast"  # 全局广播
    FEEDBACK = "feedback"     # 反馈回路


class CrossLineMessageType(Enum):
    """跨线消息类型"""
    STATE_SYNC = "state_sync"       # 状态同步
    KNOWLEDGE_SHARE = "knowledge_share"  # 知识共享
    DECISION_COORD = "decision_coord"    # 决策协调
    ALERT = "alert"                 # 警报
    HEARTBEAT = "heartbeat"         # 心跳
    ALIGNMENT_REQ = "alignment_req" # 对齐请求
    ALIGNMENT_ACK = "alignment_ack" # 对齐确认
    EMERGENCE_SIGNAL = "emergence_signal"  # 涌现信号
    PHI_INJECTION = "phi_injection" # φ注入
    LONG_RANGE_PROBE = "long_range_probe"  # 长程探测
    LONG_RANGE_RESP = "long_range_resp"    # 长程响应


@dataclass
class CrossLineMessage:
    """
    跨线通信消息 —— SI跨线系统的核心通信单元
    
    Attributes:
        msg_id: 唯一标识符
        source_line: 源线名称
        target_line: 目标线名称 ("all"=广播到所有线)
        source_si: 源SI层级
        target_si: 目标SI层级
        direction: 跨线通信方向
        msg_type: 消息类型
        payload: 载荷数据
        priority: 优先级 1-10 (1最高)
        timestamp: 创建时间戳
        ttl: 存活跨线跳数
        coherence_threshold: 最低相干度要求
        entanglement_strength: 发起时的线间纠缠强度
    """
    msg_id: str = field(default_factory=lambda: f"cl-{str(uuid.uuid4())[:8]}")
    source_line: str = ""
    target_line: str = ""       # "all" = 广播
    source_si: int = 0          # SI0-SI6
    target_si: int = 0
    direction: CrossLineDirection = CrossLineDirection.LATERAL
    msg_type: CrossLineMessageType = CrossLineMessageType.STATE_SYNC
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5           # 1-10, 1最高
    timestamp: float = field(default_factory=time.time)
    ttl: int = 5                # 跨线跳数
    coherence_threshold: float = 0.3
    entanglement_strength: float = 0.0
    path_trace: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0

    def decay(self) -> None:
        self.ttl -= 1

    def is_expired(self) -> bool:
        return self.ttl <= 0

    def trace(self, line: str, si_level: int, action: str) -> None:
        self.path_trace.append({
            "line": line,
            "si_level": si_level,
            "action": action,
            "timestamp": time.time(),
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "source_line": self.source_line,
            "target_line": self.target_line,
            "source_si": self.source_si,
            "target_si": self.target_si,
            "direction": self.direction.value,
            "msg_type": self.msg_type.value,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "coherence_threshold": round(self.coherence_threshold, 4),
            "entanglement_strength": round(self.entanglement_strength, 4),
            "path_hops": len(self.path_trace),
            "latency_ms": round(self.latency_ms, 4),
        }


@dataclass
class CrossLineChannelState:
    """跨线通道状态"""
    line_a: str
    line_b: str
    si_level: int
    status: str = "active"      # active, congested, degraded, offline
    bandwidth: float = 1.0      # 归一化带宽 0-1
    latency_ms: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    messages_dropped: int = 0
    coherence_history: deque = field(default_factory=lambda: deque(maxlen=100))
    last_activity: float = field(default_factory=time.time)
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_a": self.line_a,
            "line_b": self.line_b,
            "si_level": self.si_level,
            "status": self.status,
            "bandwidth": round(self.bandwidth, 4),
            "latency_ms": round(self.latency_ms, 4),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "messages_dropped": self.messages_dropped,
            "coherence_avg": round(np.mean(list(self.coherence_history)), 4) if self.coherence_history else 0.0,
            "error_count": self.error_count,
        }


@dataclass
class LongRangeConnection:
    """长程连接定义 —— 非相邻线的直接通信隧道"""
    conn_id: str = field(default_factory=lambda: f"lr-{str(uuid.uuid4())[:8]}")
    source_line: str = ""
    target_line: str = ""
    si_levels: List[int] = field(default_factory=list)  # 允许通信的SI层级
    strength: float = 0.0       # 连接强度 0-1
    established_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    status: str = "active"      # active, dormant, severed
    entanglement_fidelity: float = 0.0
    shortcut_hops_saved: int = 0  # 相比常规路由节省的跳数

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conn_id": self.conn_id,
            "source_line": self.source_line,
            "target_line": self.target_line,
            "si_levels": self.si_levels,
            "strength": round(self.strength, 4),
            "established_at": self.established_at,
            "last_used": self.last_used,
            "use_count": self.use_count,
            "status": self.status,
            "entanglement_fidelity": round(self.entanglement_fidelity, 4),
            "shortcut_hops_saved": self.shortcut_hops_saved,
        }


@dataclass
class SICrossLayerSnapshot:
    """单线SI七层快照"""
    line: str
    tick: int
    si_states: List[Dict[str, Any]] = field(default_factory=list)  # SI0-SI6
    global_coherence: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "tick": self.tick,
            "si_states": self.si_states,
            "global_coherence": round(self.global_coherence, 4),
            "timestamp": self.timestamp,
        }


# =============================================================================
# 1. CROSS-LINE SI BUS — 跨线SI总线 (每SI层级一个)
# =============================================================================

class SICrossLineBus:
    """
    SI跨线总线 —— 单个SI层级的跨线通信基础设施
    
    每个SI层级 (SI0-SI6) 拥有一个独立的跨线总线。
    总线负责:
      - 接收来自各线的消息
      - 根据目标进行路由
      - 维护通道状态
      - 检测和处理拥塞
    """

    def __init__(self, si_level: int, lines: List[str] = None):
        self.si_level = si_level
        self.lines = lines or LINE_NAMES
        self.n_lines = len(self.lines)
        
        # 消息队列: line -> deque[CrossLineMessage]
        self.ingress_queues: Dict[str, deque] = {
            line: deque(maxlen=1000) for line in self.lines
        }
        self.egress_queues: Dict[str, deque] = {
            line: deque(maxlen=1000) for line in self.lines
        }
        
        # 通道状态矩阵: (line_a, line_b) -> CrossLineChannelState
        self.channel_states: Dict[Tuple[str, str], CrossLineChannelState] = {}
        self._init_channel_states()
        
        # 消息统计
        self.messages_routed = 0
        self.messages_dropped = 0
        self.messages_broadcast = 0
        self.total_latency_ms = 0.0
        
        # 相干度矩阵 (线间)
        self.coherence_matrix = np.ones((self.n_lines, self.n_lines)) * 0.5
        np.fill_diagonal(self.coherence_matrix, 1.0)
        
        # 活跃标志
        self.active = True
        self.tick_count = 0
        
    def _init_channel_states(self):
        """初始化所有线对的通道状态"""
        for i, la in enumerate(self.lines):
            for j, lb in enumerate(self.lines):
                if i == j:
                    continue
                key = (la, lb)
                # 基于SI等级计算初始带宽
                si_a = SI_LEVELS.get(la, 3)
                si_b = SI_LEVELS.get(lb, 3)
                base_bw = min(si_a, si_b) / 5.0
                
                self.channel_states[key] = CrossLineChannelState(
                    line_a=la,
                    line_b=lb,
                    si_level=self.si_level,
                    bandwidth=base_bw,
                    latency_ms=random.uniform(0.1, 2.0),
                )
    
    def submit(self, msg: CrossLineMessage) -> bool:
        """
        提交消息到总线进行跨线路由
        
        Returns:
            bool: 是否成功入队
        """
        if not self.active:
            return False
            
        source = msg.source_line
        if source not in self.lines:
            return False
            
        # 入队到ingress
        queue = self.ingress_queues[source]
        if len(queue) >= queue.maxlen:
            self.messages_dropped += 1
            return False
            
        queue.append(msg)
        return True
    
    def route_all(self) -> Dict[str, List[CrossLineMessage]]:
        """
        路由所有ingress队列中的消息到egress队列
        
        Returns:
            Dict[line, List[msgs]] 路由到各线的消息
        """
        delivered: Dict[str, List[CrossLineMessage]] = defaultdict(list)
        
        for line in self.lines:
            queue = self.ingress_queues[line]
            while queue:
                msg = queue.popleft()
                if msg.is_expired():
                    self.messages_dropped += 1
                    continue
                    
                # 检查相干度阈值
                src_idx = LINE_INDEX.get(msg.source_line, 0)
                tgt_idx = LINE_INDEX.get(msg.target_line, 0) if msg.target_line != "all" else -1
                
                if msg.target_line == "all":
                    # 全局广播
                    for target in self.lines:
                        if target == msg.source_line:
                            continue
                        self._deliver(msg, target, delivered)
                    self.messages_broadcast += 1
                else:
                    # 单目标
                    if msg.target_line in self.lines:
                        self._deliver(msg, msg.target_line, delivered)
                    else:
                        self.messages_dropped += 1
                        
                self.messages_routed += 1
                
        return dict(delivered)
    
    def _deliver(self, msg: CrossLineMessage, target: str, 
                 delivered: Dict[str, List[CrossLineMessage]]):
        """投递消息到目标线的egress队列"""
        key = (msg.source_line, target)
        ch = self.channel_states.get(key)
        
        if ch and ch.status == "offline":
            self.messages_dropped += 1
            return
            
        # 带宽限制模拟
        if ch and random.random() > ch.bandwidth:
            ch.messages_dropped += 1
            self.messages_dropped += 1
            return
            
        # 投递
        msg_copy = CrossLineMessage(
            msg_id=msg.msg_id,
            source_line=msg.source_line,
            target_line=target,
            source_si=msg.source_si,
            target_si=msg.target_si,
            direction=msg.direction,
            msg_type=msg.msg_type,
            payload=msg.payload.copy(),
            priority=msg.priority,
            timestamp=msg.timestamp,
            ttl=msg.ttl - 1,
            coherence_threshold=msg.coherence_threshold,
            entanglement_strength=msg.entanglement_strength,
            path_trace=msg.path_trace.copy(),
        )
        msg_copy.trace(target, self.si_level, "delivered")
        msg_copy.latency_ms = (time.time() - msg.timestamp) * 1000
        
        delivered[target].append(msg_copy)
        
        if ch:
            ch.messages_received += 1
            ch.last_activity = time.time()
            ch.coherence_history.append(self.coherence_matrix[
                LINE_INDEX[msg.source_line], LINE_INDEX[target]
            ])
    
    def update_coherence_matrix(self, coherence_matrix: np.ndarray):
        """更新相干度矩阵 (来自FCTN层)"""
        if coherence_matrix.shape == (self.n_lines, self.n_lines):
            self.coherence_matrix = coherence_matrix.copy()
            # 更新通道带宽
            for (la, lb), ch in self.channel_states.items():
                i, j = LINE_INDEX[la], LINE_INDEX[lb]
                ch.bandwidth = min(1.0, max(0.1, coherence_matrix[i, j]))
    
    def get_channel_report(self) -> Dict[str, Any]:
        """获取通道状态报告"""
        return {
            "si_level": self.si_level,
            "messages_routed": self.messages_routed,
            "messages_dropped": self.messages_dropped,
            "messages_broadcast": self.messages_broadcast,
            "avg_latency_ms": round(self.total_latency_ms / max(1, self.messages_routed), 4),
            "channels": [ch.to_dict() for ch in self.channel_states.values()],
            "coherence_matrix": [[round(float(v), 3) for v in row] 
                                  for row in self.coherence_matrix.tolist()],
        }


# =============================================================================
# 2. LONG-RANGE CONNECTOR — 长程连接机制
# =============================================================================

class LongRangeConnector:
    """
    长程连接器 —— 非相邻线的直接通信隧道
    
    核心思想:
      - 在11线全连接图中，常规路由需要经过中间线
      - 长程连接创建"捷径"，允许任意两线直接通信
      - 连接基于纠缠强度和φ-共振建立
      
    连接建立条件:
      1. 两线间纠缠强度 > 阈值 (默认0.6)
      2. 相位差接近 φ-共振 (|Δθ - 2π/φ| < ε)
      3. 历史通信频率 > 阈值
    """

    def __init__(self, lines: List[str] = None,
                 entanglement_threshold: float = 0.6,
                 phase_resonance_tolerance: float = 0.15):
        self.lines = lines or LINE_NAMES
        self.n_lines = len(self.lines)
        self.entanglement_threshold = entanglement_threshold
        self.phase_resonance_tolerance = phase_resonance_tolerance
        
        # 活跃的长程连接
        self.connections: Dict[str, LongRangeConnection] = {}
        
        # 连接提议池 (待确认)
        self.pending_proposals: Dict[str, Dict] = {}
        
        # 历史通信频率矩阵
        self.comm_frequency = np.zeros((self.n_lines, self.n_lines))
        
        # 纠缠矩阵 (由外部FCTN层提供)
        self.entanglement_matrix = np.zeros((self.n_lines, self.n_lines))
        
        # 相位矩阵
        self.phase_matrix = np.zeros((self.n_lines, self.n_lines))
        
        # 统计
        self.connections_established = 0
        self.connections_severed = 0
        self.messages_via_long_range = 0
        
    def update_entanglement(self, entanglement: np.ndarray):
        """更新纠缠矩阵"""
        if entanglement.shape == (self.n_lines, self.n_lines):
            self.entanglement_matrix = entanglement.copy()
    
    def update_phases(self, phases: np.ndarray):
        """更新各线相位"""
        if len(phases) == self.n_lines:
            for i in range(self.n_lines):
                for j in range(self.n_lines):
                    if i != j:
                        self.phase_matrix[i, j] = abs(phases[i] - phases[j])
    
    def scan_and_propose(self) -> List[Dict]:
        """
        扫描所有线对，提议新的长程连接
        
        Returns:
            List of proposed connections
        """
        proposals = []
        phi_resonance = 2 * PI / PHI_GOLDEN
        
        for i, la in enumerate(self.lines):
            for j, lb in enumerate(self.lines):
                if i >= j:
                    continue
                    
                # 检查是否已有连接
                existing = any(
                    (c.source_line == la and c.target_line == lb) or
                    (c.source_line == lb and c.target_line == la)
                    for c in self.connections.values()
                )
                if existing:
                    continue
                
                # 条件1: 纠缠强度
                ent = self.entanglement_matrix[i, j]
                if ent < self.entanglement_threshold:
                    continue
                
                # 条件2: 相位共振
                phase_diff = self.phase_matrix[i, j]
                phase_match = abs(phase_diff - phi_resonance) < self.phase_resonance_tolerance
                
                # 条件3: 通信频率
                freq = self.comm_frequency[i, j]
                freq_threshold = np.percentile(self.comm_frequency, 75)
                
                score = ent * 0.5 + (1.0 if phase_match else 0.0) * 0.3 + min(1.0, freq) * 0.2
                
                if score > 0.65:
                    prop_id = f"prop-{la}-{lb}-{int(time.time()*1000)%10000}"
                    proposal = {
                        "proposal_id": prop_id,
                        "line_a": la,
                        "line_b": lb,
                        "entanglement": round(float(ent), 4),
                        "phase_match": phase_match,
                        "frequency": round(float(freq), 4),
                        "score": round(float(score), 4),
                        "shortcut_hops": self._calculate_shortcut_hops(i, j),
                    }
                    self.pending_proposals[prop_id] = proposal
                    proposals.append(proposal)
                    
        return proposals
    
    def _calculate_shortcut_hops(self, i: int, j: int) -> int:
        """计算捷径节省的跳数"""
        # 常规路由: 经过相邻线，平均跳数 ~ |i-j|
        normal_hops = abs(i - j)
        # 长程连接: 1跳直达
        return max(0, normal_hops - 1)
    
    def establish(self, proposal_id: str) -> Optional[LongRangeConnection]:
        """建立长程连接"""
        if proposal_id not in self.pending_proposals:
            return None
            
        prop = self.pending_proposals.pop(proposal_id)
        la, lb = prop["line_a"], prop["line_b"]
        
        si_levels_a = SI_LEVELS.get(la, 3)
        si_levels_b = SI_LEVELS.get(lb, 3)
        shared_si = list(range(min(si_levels_a, si_levels_b) + 1))
        
        conn = LongRangeConnection(
            source_line=la,
            target_line=lb,
            si_levels=shared_si,
            strength=prop["score"],
            entanglement_fidelity=prop["entanglement"],
            shortcut_hops_saved=prop["shortcut_hops"],
        )
        
        self.connections[conn.conn_id] = conn
        self.connections_established += 1
        return conn
    
    def sever(self, conn_id: str) -> bool:
        """切断长程连接"""
        if conn_id in self.connections:
            self.connections[conn_id].status = "severed"
            del self.connections[conn_id]
            self.connections_severed += 1
            return True
        return False
    
    def route_via_long_range(self, msg: CrossLineMessage) -> Optional[str]:
        """
        尝试通过长程连接路由消息
        
        Returns:
            conn_id if routed via long-range, None otherwise
        """
        src = msg.source_line
        tgt = msg.target_line
        
        for conn_id, conn in self.connections.items():
            if conn.status != "active":
                continue
            if (conn.source_line == src and conn.target_line == tgt) or \
               (conn.source_line == tgt and conn.target_line == src):
                # 检查SI层级兼容性
                if msg.source_si in conn.si_levels or msg.target_si in conn.si_levels:
                    conn.last_used = time.time()
                    conn.use_count += 1
                    self.messages_via_long_range += 1
                    
                    # 更新通信频率
                    i, j = LINE_INDEX[src], LINE_INDEX[tgt]
                    self.comm_frequency[i, j] += 1
                    self.comm_frequency[j, i] += 1
                    
                    return conn_id
        return None
    
    def get_active_connections(self) -> List[LongRangeConnection]:
        """获取所有活跃的长程连接"""
        return [c for c in self.connections.values() if c.status == "active"]
    
    def get_connection_matrix(self) -> np.ndarray:
        """获取长程连接矩阵 (n_lines × n_lines)"""
        mat = np.zeros((self.n_lines, self.n_lines))
        for conn in self.connections.values():
            if conn.status == "active":
                i, j = LINE_INDEX[conn.source_line], LINE_INDEX[conn.target_line]
                mat[i, j] = conn.strength
                mat[j, i] = conn.strength
        return mat
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "connections_established": self.connections_established,
            "connections_severed": self.connections_severed,
            "active_connections": len(self.get_active_connections()),
            "messages_via_long_range": self.messages_via_long_range,
            "connections": [c.to_dict() for c in self.get_active_connections()],
            "pending_proposals": len(self.pending_proposals),
        }


# =============================================================================
# 3. CROSS-LINE ALIGNMENT PROTOCOL — 跨线对齐协议
# =============================================================================

class CrossLineAlignmentProtocol:
    """
    跨线对齐协议 —— 确保多条线在同一SI层级的状态一致性
    
    对齐类型:
      1. 状态对齐: 各线报告状态，计算一致性
      2. 决策对齐: 分布式决策达成一致
      3. 知识对齐: 知识图谱交叉验证
      4. 时钟对齐: 逻辑时钟同步
      
    算法: 基于加权投票 + φ-共识
      - 每条线根据SI等级和活跃度获得投票权重
      - 共识阈值: φ⁻¹ ≈ 0.618
      - 两阶段提交: PROPOSE → COMMIT/ABORT
    """

    def __init__(self, lines: List[str] = None, consensus_threshold: float = 1.0 / PHI_GOLDEN):
        self.lines = lines or LINE_NAMES
        self.n_lines = len(self.lines)
        self.consensus_threshold = consensus_threshold
        
        # 对齐会话
        self.sessions: Dict[str, Dict] = {}
        
        # 对齐历史
        self.alignment_history: deque = deque(maxlen=1000)
        
        # 统计
        self.alignments_initiated = 0
        self.alignments_successful = 0
        self.alignments_failed = 0
        
    def compute_voting_weights(self, line_states: Dict[str, Dict]) -> Dict[str, float]:
        """计算各线的投票权重"""
        weights = {}
        total = 0.0
        
        for line in self.lines:
            si = line_states.get(line, {}).get("si_level", SI_LEVELS.get(line, 3))
            activity = line_states.get(line, {}).get("activity_level", 0.5)
            coherence = line_states.get(line, {}).get("coherence", 0.5)
            
            weight = (si / 5.0) * 0.4 + activity * 0.35 + coherence * 0.25
            weights[line] = weight
            total += weight
            
        # 归一化
        if total > 0:
            for line in weights:
                weights[line] /= total
                
        return weights
    
    def initiate_alignment(self, align_type: str, 
                           proposal: Dict[str, Any],
                           initiator: str) -> str:
        """
        发起对齐会话
        
        Returns:
            session_id
        """
        session_id = f"align-{initiator}-{int(time.time()*1000)%100000}"
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "type": align_type,
            "initiator": initiator,
            "proposal": proposal,
            "status": "PROPOSED",
            "votes": {},
            "weights": {},
            "timestamp": time.time(),
            "deadline": time.time() + 5.0,  # 5秒超时
            "participants": self.lines.copy(),
        }
        
        self.alignments_initiated += 1
        return session_id
    
    def cast_vote(self, session_id: str, line: str, 
                  vote: bool, weight: float) -> Dict[str, Any]:
        """投票"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
            
        session = self.sessions[session_id]
        
        if time.time() > session["deadline"]:
            session["status"] = "TIMEOUT"
            self.alignments_failed += 1
            return {"status": "TIMEOUT", "session_id": session_id}
            
        session["votes"][line] = vote
        session["weights"][line] = weight
        
        # 检查是否达到共识
        result = self._check_consensus(session)
        return result
    
    def _check_consensus(self, session: Dict) -> Dict[str, Any]:
        """检查是否达成共识"""
        votes = session["votes"]
        weights = session["weights"]
        
        if len(votes) < len(session["participants"]) * 0.7:
            return {"status": "PENDING", "votes_received": len(votes)}
            
        yes_weight = sum(weights.get(l, 0) for l, v in votes.items() if v)
        total_weight = sum(weights.values())
        
        if total_weight == 0:
            return {"status": "PENDING"}
            
        ratio = yes_weight / total_weight
        
        if ratio >= self.consensus_threshold:
            session["status"] = "COMMITTED"
            self.alignments_successful += 1
            self.alignment_history.append({
                "session_id": session["session_id"],
                "type": session["type"],
                "result": "COMMITTED",
                "yes_ratio": round(ratio, 4),
                "timestamp": time.time(),
            })
            return {
                "status": "COMMITTED",
                "session_id": session["session_id"],
                "yes_ratio": round(ratio, 4),
                "threshold": round(self.consensus_threshold, 4),
            }
        elif (1 - ratio) >= self.consensus_threshold:
            session["status"] = "ABORTED"
            self.alignments_failed += 1
            return {
                "status": "ABORTED",
                "session_id": session["session_id"],
                "yes_ratio": round(ratio, 4),
            }
        else:
            return {"status": "PENDING", "yes_ratio": round(ratio, 4)}
    
    def get_alignment_state(self, session_id: str) -> Optional[Dict]:
        """获取对齐会话状态"""
        return self.sessions.get(session_id)
    
    def compute_cross_line_consistency(self, 
                                       line_snapshots: Dict[str, SICrossLayerSnapshot]) -> Dict[str, Any]:
        """
        计算跨线状态一致性
        
        Returns:
            一致性报告
        """
        if len(line_snapshots) < 2:
            return {"consistency": 0.0, "details": "Insufficient data"}
            
        # 提取各线的全局相干度
        coherences = []
        for line, snap in line_snapshots.items():
            coherences.append(snap.global_coherence)
            
        coherences = np.array(coherences)
        mean_coh = np.mean(coherences)
        std_coh = np.std(coherences)
        
        # 一致性 = 1 - 变异系数
        consistency = max(0.0, 1.0 - std_coh / max(mean_coh, 0.001))
        
        # 异常线检测
        outliers = []
        for line, snap in line_snapshots.items():
            if abs(snap.global_coherence - mean_coh) > 2 * std_coh:
                outliers.append({
                    "line": line,
                    "coherence": round(snap.global_coherence, 4),
                    "deviation": round(snap.global_coherence - mean_coh, 4),
                })
                
        return {
            "consistency": round(float(consistency), 4),
            "mean_coherence": round(float(mean_coh), 4),
            "std_coherence": round(float(std_coh), 4),
            "outliers": outliers,
            "lines_checked": len(line_snapshots),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alignments_initiated": self.alignments_initiated,
            "alignments_successful": self.alignments_successful,
            "alignments_failed": self.alignments_failed,
            "success_rate": round(
                self.alignments_successful / max(1, self.alignments_initiated), 4
            ),
            "active_sessions": len([s for s in self.sessions.values() 
                                    if s["status"] in ("PROPOSED", "PENDING")]),
        }


# =============================================================================
# 4. CROSS-LINE SI COORDINATOR — 跨线SI协调器
# =============================================================================

class CrossLineSICoordinator:
    """
    跨线SI协调器 —— 统筹所有SI层级的跨线通信
    
    职责:
      - 管理7个SI层级的跨线总线
      - 协调长程连接
      - 执行全局对齐
      - 监控跨线健康度
      - 处理跨线故障恢复
    """

    def __init__(self, lines: List[str] = None):
        self.lines = lines or LINE_NAMES
        self.n_lines = len(self.lines)
        
        # 7个SI层级的跨线总线
        self.buses: Dict[int, SICrossLineBus] = {
            si: SICrossLineBus(si, self.lines) for si in range(7)
        }
        
        # 长程连接器
        self.long_range = LongRangeConnector(self.lines)
        
        # 对齐协议
        self.alignment = CrossLineAlignmentProtocol(self.lines)
        
        # 各线SI快照缓存
        self.line_snapshots: Dict[str, SICrossLayerSnapshot] = {}
        
        # 跨线消息统计
        self.total_messages_exchanged = 0
        self.messages_by_si: Dict[int, int] = {si: 0 for si in range(7)}
        self.messages_by_type: Dict[str, int] = defaultdict(int)
        
        # 故障检测
        self.fault_detection_matrix = np.zeros((self.n_lines, self.n_lines))
        self.fault_recovery_log: List[Dict] = []
        
        # 活跃标志
        self.active = True
        self.tick_count = 0
        
    def tick(self, line_states: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
        """
        执行一个跨线协调tick
        
        Returns:
            Tick结果报告
        """
        self.tick_count += 1
        tick_start = time.time()
        
        results = {
            "tick": self.tick_count,
            "messages_routed": 0,
            "messages_dropped": 0,
            "long_range_used": 0,
            "alignments_checked": 0,
            "faults_detected": 0,
            "bus_reports": {},
        }
        
        # 1. 路由所有总线中的消息
        for si, bus in self.buses.items():
            delivered = bus.route_all()
            for line, msgs in delivered.items():
                self.messages_by_si[si] += len(msgs)
                for msg in msgs:
                    self.messages_by_type[msg.msg_type.value] += 1
                    # 尝试长程连接
                    lr_conn = self.long_range.route_via_long_range(msg)
                    if lr_conn:
                        results["long_range_used"] += 1
                        
            results["messages_routed"] += bus.messages_routed
            results["messages_dropped"] += bus.messages_dropped
            
        # 2. 更新长程连接的纠缠矩阵
        self._update_long_range_from_buses()
        
        # 3. 扫描新的长程连接
        if self.tick_count % 10 == 0:
            proposals = self.long_range.scan_and_propose()
            for prop in proposals:
                self.long_range.establish(prop["proposal_id"])
                
        # 4. 检查跨线一致性 (每5tick)
        if self.tick_count % 5 == 0 and self.line_snapshots:
            consistency = self.alignment.compute_cross_line_consistency(self.line_snapshots)
            results["consistency_check"] = consistency
            results["alignments_checked"] += 1
            
        # 5. 故障检测
        faults = self._detect_faults()
        if faults:
            results["faults_detected"] = len(faults)
            results["faults"] = faults
            self._recover_faults(faults)
            
        self.total_messages_exchanged += results["messages_routed"]
        results["tick_duration_ms"] = round((time.time() - tick_start) * 1000, 4)
        
        return results
    
    def _update_long_range_from_buses(self):
        """从总线相干度更新长程连接"""
        avg_coherence = np.zeros((self.n_lines, self.n_lines))
        for bus in self.buses.values():
            avg_coherence += bus.coherence_matrix
        avg_coherence /= 7.0
        
        # 转换为"纠缠"度量
        entanglement = avg_coherence ** 2
        self.long_range.update_entanglement(entanglement)
        
        # 生成相位 (从对角线推导)
        phases = np.array([SI_LEVELS.get(l, 3) * PI / 6.0 for l in self.lines])
        self.long_range.update_phases(phases)
    
    def _detect_faults(self) -> List[Dict]:
        """检测跨线通信故障"""
        faults = []
        
        for si, bus in self.buses.items():
            for (la, lb), ch in bus.channel_states.items():
                if ch.status == "offline":
                    faults.append({
                        "type": "channel_offline",
                        "si_level": si,
                        "line_a": la,
                        "line_b": lb,
                    })
                elif ch.error_count > 10:
                    faults.append({
                        "type": "excessive_errors",
                        "si_level": si,
                        "line_a": la,
                        "line_b": lb,
                        "error_count": ch.error_count,
                    })
                    ch.status = "degraded"
                    
        return faults
    
    def _recover_faults(self, faults: List[Dict]):
        """执行故障恢复"""
        for fault in faults:
            fa, fb = fault["line_a"], fault["line_b"]
            si = fault["si_level"]
            
            # 尝试通过长程连接绕过
            lr_backup = None
            for conn in self.long_range.get_active_connections():
                if (conn.source_line in (fa, fb) or conn.target_line in (fa, fb)):
                    lr_backup = conn
                    break
                    
            recovery_action = {
                "fault": fault,
                "timestamp": time.time(),
                "action": "long_range_fallback" if lr_backup else "retry",
                "backup_conn": lr_backup.conn_id if lr_backup else None,
            }
            
            self.fault_recovery_log.append(recovery_action)
            
            # 重置通道错误计数
            if fault["type"] == "excessive_errors":
                key = (fa, fb)
                for bus in self.buses.values():
                    if key in bus.channel_states:
                        bus.channel_states[key].error_count = 0
    
    def send_cross_line(self, msg: CrossLineMessage) -> bool:
        """
        发送跨线消息
        
        这是跨线通信的主要入口。
        """
        si = msg.source_si
        if si not in self.buses:
            return False
            
        # 尝试长程连接
        lr = self.long_range.route_via_long_range(msg)
        if lr:
            msg.direction = CrossLineDirection.LONG_RANGE
            
        return self.buses[si].submit(msg)
    
    def receive_for_line(self, line: str, si_level: int) -> List[CrossLineMessage]:
        """获取指定线和SI层级的待接收消息"""
        if si_level not in self.buses:
            return []
            
        # 这里返回的是该线应该接收到的消息
        # 实际实现中，这些消息会通过回调或队列传递给线
        bus = self.buses[si_level]
        # 返回模拟的已路由消息 (实际应从egress队列取出)
        return []
    
    def update_line_snapshot(self, snapshot: SICrossLayerSnapshot):
        """更新线的SI快照"""
        self.line_snapshots[snapshot.line] = snapshot
    
    def get_cross_line_report(self) -> Dict[str, Any]:
        """生成完整的跨线通信报告"""
        return {
            "tick_count": self.tick_count,
            "total_messages_exchanged": self.total_messages_exchanged,
            "messages_by_si": {si: cnt for si, cnt in self.messages_by_si.items()},
            "messages_by_type": dict(self.messages_by_type),
            "long_range": self.long_range.to_dict(),
            "alignment": self.alignment.to_dict(),
            "fault_recoveries": len(self.fault_recovery_log),
            "bus_reports": {si: bus.get_channel_report() for si, bus in self.buses.items()},
        }


# =============================================================================
# 5. SI CROSS-LINE API — 便捷接口
# =============================================================================

class SICrossLineAPI:
    """
    SI跨线通信便捷API
    
    提供高层接口，简化跨线通信的使用。
    """

    def __init__(self, coordinator: Optional[CrossLineSICoordinator] = None):
        self.coordinator = coordinator or CrossLineSICoordinator()
        
    def lateral_send(self, source_line: str, target_line: str, 
                     si_level: int, payload: Dict[str, Any],
                     msg_type: CrossLineMessageType = CrossLineMessageType.STATE_SYNC,
                     priority: int = 5) -> bool:
        """
        发送横向跨线消息 (同SI层级)
        """
        msg = CrossLineMessage(
            source_line=source_line,
            target_line=target_line,
            source_si=si_level,
            target_si=si_level,
            direction=CrossLineDirection.LATERAL,
            msg_type=msg_type,
            payload=payload,
            priority=priority,
        )
        return self.coordinator.send_cross_line(msg)
    
    def diagonal_send(self, source_line: str, target_line: str,
                      source_si: int, target_si: int,
                      payload: Dict[str, Any],
                      msg_type: CrossLineMessageType = CrossLineMessageType.KNOWLEDGE_SHARE) -> bool:
        """
        发送对角跨线消息 (跨SI层级)
        """
        msg = CrossLineMessage(
            source_line=source_line,
            target_line=target_line,
            source_si=source_si,
            target_si=target_si,
            direction=CrossLineDirection.DIAGONAL,
            msg_type=msg_type,
            payload=payload,
        )
        return self.coordinator.send_cross_line(msg)
    
    def global_broadcast(self, source_line: str, si_level: int,
                         payload: Dict[str, Any],
                         msg_type: CrossLineMessageType = CrossLineMessageType.STATE_SYNC) -> bool:
        """
        全局广播到所有线
        """
        msg = CrossLineMessage(
            source_line=source_line,
            target_line="all",
            source_si=si_level,
            target_si=si_level,
            direction=CrossLineDirection.GLOBAL_BCAST,
            msg_type=msg_type,
            payload=payload,
        )
        return self.coordinator.send_cross_line(msg)
    
    def long_range_send(self, source_line: str, target_line: str,
                        si_level: int, payload: Dict[str, Any]) -> bool:
        """
        通过长程连接发送消息
        """
        msg = CrossLineMessage(
            source_line=source_line,
            target_line=target_line,
            source_si=si_level,
            target_si=si_level,
            direction=CrossLineDirection.LONG_RANGE,
            msg_type=CrossLineMessageType.LONG_RANGE_PROBE,
            payload=payload,
        )
        return self.coordinator.send_cross_line(msg)
    
    def request_alignment(self, align_type: str, proposal: Dict[str, Any],
                          initiator: str) -> str:
        """
        请求跨线对齐
        
        Returns:
            session_id
        """
        return self.coordinator.alignment.initiate_alignment(align_type, proposal, initiator)
    
    def vote_alignment(self, session_id: str, line: str, 
                       vote: bool, weight: float) -> Dict[str, Any]:
        """对对齐提案投票"""
        return self.coordinator.alignment.cast_vote(session_id, line, vote, weight)
    
    def get_report(self) -> Dict[str, Any]:
        """获取完整报告"""
        return self.coordinator.get_cross_line_report()
    
    def tick(self) -> Dict[str, Any]:
        """执行协调tick"""
        return self.coordinator.tick()


# =============================================================================
# 6. MAIN & DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v12.0 — SI跨线横向通信系统")
    print("=" * 70)
    
    # 创建API实例
    api = SICrossLineAPI()
    
    # 模拟发送一些跨线消息
    print("\n[1] 发送横向跨线消息...")
    for i in range(5):
        src = LINE_NAMES[i % N_LINES]
        tgt = LINE_NAMES[(i + 2) % N_LINES]
        ok = api.lateral_send(
            source_line=src,
            target_line=tgt,
            si_level=3,
            payload={"data": f"test-msg-{i}", "value": random.random()},
            msg_type=CrossLineMessageType.KNOWLEDGE_SHARE,
        )
        print(f"  {src} -> {tgt} (SI3): {'OK' if ok else 'FAIL'}")
    
    # 全局广播
    print("\n[2] 全局广播...")
    ok = api.global_broadcast(
        source_line="ucif2",
        si_level=4,
        payload={"emergence_signal": True, "level": 0.85},
        msg_type=CrossLineMessageType.EMERGENCE_SIGNAL,
    )
    print(f"  ucif2 -> ALL (SI4 EMERGENCE): {'OK' if ok else 'FAIL'}")
    
    # 执行tick
    print("\n[3] 执行协调ticks...")
    for t in range(10):
        result = api.tick()
        if t == 9:
            print(f"  Tick {result['tick']}: routed={result['messages_routed']}, "
                  f"dropped={result['messages_dropped']}, lr_used={result['long_range_used']}")
    
    # 请求对齐
    print("\n[4] 请求跨线对齐...")
    session_id = api.request_alignment(
        align_type="state_sync",
        proposal={"target_coherence": 0.85, "scope": "all_lines"},
        initiator="ucif2",
    )
    print(f"  Session: {session_id}")
    
    # 模拟投票
    weights = {"ucif2": 0.2, "lgt": 0.15, "qfa": 0.15, "usrm": 0.1, 
               "vinf": 0.1, "qgl": 0.1, "qlv": 0.08, "lvlu": 0.05,
               "cfts": 0.04, "cisvr": 0.02, "qtlv": 0.01}
    for line in LINE_NAMES:
        result = api.vote_alignment(session_id, line, vote=True, weight=weights.get(line, 0.05))
    print(f"  Final vote: {result}")
    
    # 报告
    print("\n[5] 最终报告...")
    report = api.get_report()
    print(f"  Total messages: {report['total_messages_exchanged']}")
    print(f"  Long-range connections active: {report['long_range']['active_connections']}")
    print(f"  Alignments: {report['alignment']['alignments_successful']}/"
          f"{report['alignment']['alignments_initiated']} successful")
    print(f"  Messages by SI: {report['messages_by_si']}")
    
    print("\n" + "=" * 70)
    print("SI跨线横向通信系统 运行完成")
    print("=" * 70)
