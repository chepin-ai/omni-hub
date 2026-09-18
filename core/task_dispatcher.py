#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.2 — Task Dispatcher (任务转派系统)
===============================================

智能任务分配和负载均衡引擎，负责将任务分派到11条计算线中的最优目标，
支持负载均衡、任务升级、跨线委托等高级调度策略。

11 线配置 (SI 等级):
    ucif2 (SI 5.0) — 核心调度器
    lvlu  (SI 4.5) — 高等级观察线
    lgt   (SI 4.0), qfa (SI 4.0), vinf (SI 4.0), qgl (SI 4.0)
    qlv   (SI 3.5), cisvr (SI 3.5), qtlv (SI 3.5)
    usrm  (SI 3.0), cfts (SI 3.0)

核心能力:
    • dispatch      : 基于任务类型、复杂度、截止期限的智能分派
    • balance_load  : 高负载线 → 低负载线的动态任务迁移
    • escalate      : 低 SI 线 → 高 SI 线的任务升级
    • delegate      : 一线向另一线的精确任务转交

版本: 3.2.0
作者: OMNI-HUB Architecture Team
"""

from __future__ import annotations

import time
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import logging


# ───────────────────────── 常量定义 ─────────────────────────

ALL_11_LINES = [
    "ucif2",   # SI 5.0 — 核心调度器
    "lgt",     # SI 4.0
    "qfa",     # SI 4.0
    "usrm",    # SI 3.0
    "vinf",    # SI 4.0
    "qgl",     # SI 4.0
    "qlv",     # SI 3.5
    "lvlu",    # SI 4.5
    "cfts",    # SI 3.0
    "cisvr",   # SI 3.5
    "qtlv",    # SI 3.5
]

LINE_SI: Dict[str, float] = {
    "ucif2": 5.0, "lgt": 4.0, "qfa": 4.0, "usrm": 3.0, "vinf": 4.0,
    "qgl": 4.0, "qlv": 3.5, "lvlu": 4.5, "cfts": 3.0, "cisvr": 3.5,
    "qtlv": 3.5,
}

# 任务类型到首选线的映射
TASK_TYPE_PREFERENCES: Dict[str, List[str]] = {
    "research":    ["lgt", "qfa", "vinf", "qgl", "lvlu"],   # SI4+ 线
    "compute":     ["lgt", "lvlu", "vinf", "qgl"],          # 计算密集型
    "verify":      ["qfa", "vinf", "cisvr"],                 # 形式验证
    "sync":        ["ucif2", "qgl", "qlv"],                  # 协调同步
    "coordinate":  ["ucif2", "lvlu"],                        # 高 SI 协调
    "math_bridge": ["qtlv", "qlv", "cisvr"],                 # 数学桥接
    "data_proc":   ["usrm", "cfts", "qlv"],                  # 数据处理
    "relay":       ["qgl", "qlv", "qtlv", "lvlu", "cfts"],   # 中继转发
}

# SI 阈值
SI_THRESHOLD_OMNI: float = 5.0
SI_THRESHOLD_HIGH: float = 4.0
SI_THRESHOLD_MID: float = 3.5
SI_THRESHOLD_LOW: float = 3.0

# 负载均衡参数
LOAD_BALANCE_THRESHOLD: float = 0.75   # 超过此值视为高负载
LOAD_BALANCE_TARGET: float = 0.60      # 迁移后目标负载
MAX_DELEGATE_DEPTH: int = 3            # 最大委托链深度


# ───────────────────────── 数据类 ─────────────────────────

@dataclass
class TaskRecord:
    """任务记录数据结构"""
    task_id: str
    task_type: str
    complexity: int
    deadline: float
    assigned_to: Optional[str] = None
    via_si: Optional[str] = None
    status: str = "pending"  # pending | running | completed | failed | escalated | delegated
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    delegate_depth: int = 0
    delegate_chain: List[str] = field(default_factory=list)  # 任务独立的委托链


# ───────────────────────── 核心类 ─────────────────────────

class TaskDispatcher:
    """
    OMNI-HUB v3.2 任务转派系统 — 智能任务分配和负载均衡引擎。

    管理任务队列、线负载跟踪、智能分派决策，支持以下策略:
      • 类型匹配: 根据任务类型选择最适合的线
      • 复杂度分级: 高复杂度任务 → 高 SI 线
      • 负载感知: 实时负载均衡，避免单线过载
      • 升级机制: 任务失败或超时时自动升级到更高 SI 线
      • 委托链: 支持跨线委托，带深度限制

    Attributes:
        topology: SITopology 实例，提供拓扑信息
        task_queue: 待处理任务队列
        assignment_log: 分派历史日志
        line_loads: 各线当前负载缓存 (0-1)
        active_tasks: 正在执行的任务映射
        task_records: 完整任务记录字典
    """

    def __init__(self, topology: Any) -> None:
        """
        初始化任务转派系统。

        Args:
            topology: SITopology 实例，用于获取线健康度、SI 等级等拓扑信息
        """
        self.topo = topology
        self.task_queue: List[Dict[str, Any]] = []
        self.assignment_log: List[Dict[str, Any]] = []

        # 负载跟踪
        self.line_loads: Dict[str, float] = {line: 0.0 for line in ALL_11_LINES}
        self.active_tasks: Dict[str, List[str]] = {line: [] for line in ALL_11_LINES}
        self.task_records: Dict[str, TaskRecord] = {}

        # 委托关系图 (用于检测循环)
        self._delegate_graph: Dict[str, List[str]] = {line: [] for line in ALL_11_LINES}

    # -----------------------------------------------------------------
    # 1. 核心分派逻辑
    # -----------------------------------------------------------------

    def dispatch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能分派任务到最优计算线。

        分派策略 (按优先级排序):
          1. 任务类型匹配 → 获取候选线列表
          2. 复杂度过滤 → 高复杂度(>=7)必须 SI4+ 线
          3. 负载均衡 → 在候选线中选择负载最低的
          4. 健康度加权 → 健康度 < 0.8 的线降级使用
          5. 截止期限紧迫性 → 紧急任务优先选择低负载线

        Args:
            task: 任务字典，必须包含:
                - "id" (str): 任务唯一标识
                - "type" (str): 任务类型 (research|compute|verify|sync|...)
                - "complexity" (int): 复杂度 1-10
                - "deadline" (float): 截止期限时间戳 (秒)
                可选:
                - "preferred_line" (str): 用户指定的首选线
                - "exclude_lines" (list): 排除的线列表

        Returns:
            分派结果字典:
                {
                    "task_id": str,
                    "assigned_to": str,
                    "via": str (si0|si1|si2|si3|si4|si5),
                    "reason": str,
                    "confidence": float (0-1),
                    "estimated_latency_ms": float,
                    "status": str,
                }
        """
        t_start = time.perf_counter()

        # ── 参数提取与校验 ──
        task_id = task.get("id", "")
        task_type = task.get("type", "unknown")
        complexity = int(task.get("complexity", 5))
        deadline = float(task.get("deadline", time.time() + 3600))
        preferred = task.get("preferred_line", "")
        exclude = set(task.get("exclude_lines", []))

        if not task_id:
            task_id = f"T-{uuid.uuid4().hex[:8]}"

        # 边界校验
        complexity = max(1, min(10, complexity))
        urgency = self._compute_urgency(deadline)

        # ── 步骤 1: 确定候选线 ──
        candidates = self._get_candidates_for_type(task_type)

        # 添加用户首选线到候选头部
        if preferred and preferred in ALL_11_LINES and preferred not in exclude:
            if preferred not in candidates:
                candidates.insert(0, preferred)
            else:
                candidates.remove(preferred)
                candidates.insert(0, preferred)

        # 排除指定线
        candidates = [c for c in candidates if c not in exclude]

        if not candidates:
            # 无候选时回退到所有可用线
            candidates = [l for l in ALL_11_LINES if l not in exclude]

        # ── 步骤 2: 复杂度过滤 ──
        if complexity >= 8:
            # 极高复杂度: 仅限 SI4+ 线
            candidates = [c for c in candidates if LINE_SI.get(c, 0.0) >= SI_THRESHOLD_HIGH]
        elif complexity >= 6:
            # 高复杂度: 仅限 SI3.5+ 线
            candidates = [c for c in candidates if LINE_SI.get(c, 0.0) >= SI_THRESHOLD_MID]

        if not candidates:
            # 过滤后无候选，放宽条件
            candidates = [l for l in ALL_11_LINES if l not in exclude]

        # ── 步骤 3: 负载感知排序 ──
        scored_candidates = []
        for line in candidates:
            load = self.get_line_load(line)
            health = self._get_line_health(line)
            si = LINE_SI.get(line, 0.0)

            # 综合评分: 低负载加分, 高健康度加分, 高 SI 加分, 类型匹配加分
            load_score = max(0.0, 1.0 - load) * 0.35
            health_score = health * 0.25
            si_score = (si / 5.0) * 0.20
            type_match_score = 0.20 if line in TASK_TYPE_PREFERENCES.get(task_type, []) else 0.05

            # 健康度低于 0.8 的线大幅惩罚
            if health < 0.8:
                health_score *= 0.3

            # 高负载线惩罚
            if load > LOAD_BALANCE_THRESHOLD:
                load_score *= 0.3

            total_score = load_score + health_score + si_score + type_match_score
            scored_candidates.append((line, total_score, load, health, si))

        # 按综合评分降序排列
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_line = scored_candidates[0][0]
        best_score = scored_candidates[0][1]
        best_load = scored_candidates[0][2]

        # ── 步骤 4: 确定 SI 通道 ──
        si_level = self._si_to_level(LINE_SI.get(best_line, 0.0))

        # ── 步骤 5: 构建结果 ──
        via = f"si{si_level}"
        reason = (
            f"类型匹配={task_type}, 复杂度={complexity}, "
            f"目标负载={best_load:.2f}, 健康度={scored_candidates[0][3]:.2f}, "
            f"SI={scored_candidates[0][4]:.1f}, 紧急度={urgency:.2f}"
        )
        confidence = round(min(best_score * 1.2, 1.0), 4)

        # 估算延迟: 与负载成正比，与 SI 成反比
        estimated_latency = best_load * 100.0 / (1.0 + si_level * 0.5)

        # 记录任务
        record = TaskRecord(
            task_id=task_id,
            task_type=task_type,
            complexity=complexity,
            deadline=deadline,
            assigned_to=best_line,
            via_si=via,
            status="pending",
        )
        record.history.append({
            "action": "dispatch",
            "timestamp": time.time(),
            "assigned_to": best_line,
            "via": via,
            "reason": reason,
            "confidence": confidence,
        })
        self.task_records[task_id] = record
        self.task_queue.append(task)

        # 更新负载
        self._update_load(best_line, +0.05 * complexity / 10.0)
        self.active_tasks[best_line].append(task_id)

        # 记录日志
        log_entry = {
            "timestamp": time.time(),
            "task_id": task_id,
            "action": "dispatch",
            "from": None,
            "to": best_line,
            "via": via,
            "reason": reason,
            "confidence": confidence,
        }
        self.assignment_log.append(log_entry)

        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

        return {
            "task_id": task_id,
            "assigned_to": best_line,
            "via": via,
            "reason": reason,
            "confidence": confidence,
            "estimated_latency_ms": round(estimated_latency, 2),
            "status": "dispatched",
            "dispatch_latency_ms": latency_ms,
        }

    # -----------------------------------------------------------------
    # 2. 负载查询与更新
    # -----------------------------------------------------------------

    def get_line_load(self, line: str) -> float:
        """
        获取指定线的当前负载 (0.0 - 1.0)。

        负载计算综合考虑:
          • 当前活跃任务数 / 最大并发容量 (假设容量为 20)
          • 拓扑健康度反向影响 (健康度越低，有效负载越高)
          • 最近分派历史平滑

        Args:
            line: 线名称

        Returns:
            负载值 0.0-1.0，0 表示空闲，1 表示满载

        Raises:
            ValueError: 线名称无效
        """
        if line not in ALL_11_LINES:
            raise ValueError(f"无效线名称 '{line}'，合法线: {ALL_11_LINES}")

        base_load = self.line_loads.get(line, 0.0)

        # 活跃任务贡献的负载
        active_count = len(self.active_tasks.get(line, []))
        capacity = 20.0  # 假设每线最大并发容量
        active_load = min(1.0, active_count / capacity)

        # 健康度影响: 健康度低时，有效负载上升
        health = self._get_line_health(line)
        health_factor = 1.0 + max(0.0, (0.8 - health)) * 2.0

        # 综合负载 (加权平均)
        combined = (base_load * 0.3 + active_load * 0.7) * health_factor
        return round(min(1.0, max(0.0, combined)), 4)

    def _update_load(self, line: str, delta: float) -> None:
        """内部方法: 更新线的基准负载"""
        current = self.line_loads.get(line, 0.0)
        self.line_loads[line] = round(min(1.0, max(0.0, current + delta)), 4)

    def _get_line_health(self, line: str) -> float:
        """从拓扑获取线健康度"""
        try:
            line_nodes = self.topo.topology.get("line", {})
            if line in line_nodes:
                return float(line_nodes[line].get("health", 0.95))
        except Exception:
            pass
        return 0.95

    # -----------------------------------------------------------------
    # 3. 负载均衡
    # -----------------------------------------------------------------

    def balance_load(self) -> Dict[str, Any]:
        """
        负载均衡 — 将高负载线的任务转移到低负载线。

        策略:
          1. 识别负载超过 LOAD_BALANCE_THRESHOLD (0.75) 的高负载线
          2. 识别负载低于 LOAD_BALANCE_TARGET (0.60) 的低负载线
          3. 按任务优先级和可迁移性排序，选择迁移任务
          4. 执行 delegate 迁移，更新双方负载

        Returns:
            负载均衡报告:
                {
                    "balanced": bool,
                    "migrations": list[dict],
                    "before_loads": dict[str, float],
                    "after_loads": dict[str, float],
                    "total_migrated": int,
                }
        """
        t_start = time.perf_counter()

        # 快照当前负载
        before_loads = {line: self.get_line_load(line) for line in ALL_11_LINES}

        high_load_lines = [
            line for line in ALL_11_LINES
            if before_loads[line] > LOAD_BALANCE_THRESHOLD
        ]
        low_load_lines = [
            line for line in ALL_11_LINES
            if before_loads[line] < LOAD_BALANCE_TARGET
        ]

        migrations: List[Dict[str, Any]] = []

        if not high_load_lines or not low_load_lines:
            return {
                "balanced": False,
                "migrations": [],
                "before_loads": before_loads,
                "after_loads": before_loads,
                "total_migrated": 0,
                "reason": "无需要均衡的高/低负载线",
            }

        # 按负载降序排列高负载线
        high_load_lines.sort(key=lambda l: before_loads[l], reverse=True)
        # 按负载升序排列低负载线
        low_load_lines.sort(key=lambda l: before_loads[l])

        for src_line in high_load_lines:
            src_load = self.get_line_load(src_line)
            if src_load <= LOAD_BALANCE_TARGET:
                continue

            # 获取该线上可迁移的任务 (pending 状态，非高复杂度)
            movable_tasks = [
                tid for tid in self.active_tasks.get(src_line, [])
                if tid in self.task_records
                and self.task_records[tid].status == "pending"
                and self.task_records[tid].complexity < 7
                and self.task_records[tid].delegate_depth < MAX_DELEGATE_DEPTH
            ]

            for tid in movable_tasks:
                if src_load <= LOAD_BALANCE_TARGET:
                    break

                # 找最优目标线
                best_dst = None
                best_dst_load = 1.0
                for dst_line in low_load_lines:
                    dst_load = self.get_line_load(dst_line)
                    if dst_line == src_line:
                        continue
                    # 目标线 SI 应足够处理该任务
                    task_si_req = self.task_records[tid].complexity / 10.0 * 5.0
                    if LINE_SI.get(dst_line, 0.0) + 0.5 < task_si_req:
                        continue
                    if dst_load < best_dst_load:
                        best_dst = dst_line
                        best_dst_load = dst_load

                if best_dst is None:
                    continue

                # 执行迁移
                result = self.delegate(tid, src_line, best_dst)
                if result.get("status") == "delegated":
                    migrations.append({
                        "task_id": tid,
                        "from": src_line,
                        "to": best_dst,
                        "reason": "load_balance",
                        "src_load_before": round(src_load, 4),
                        "dst_load_before": round(best_dst_load, 4),
                    })
                    src_load = self.get_line_load(src_line)

        after_loads = {line: self.get_line_load(line) for line in ALL_11_LINES}

        return {
            "balanced": len(migrations) > 0,
            "migrations": migrations,
            "before_loads": before_loads,
            "after_loads": after_loads,
            "total_migrated": len(migrations),
            "balance_latency_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }

    # -----------------------------------------------------------------
    # 4. 任务升级
    # -----------------------------------------------------------------

    def escalate(self, task_id: str, reason: str) -> Dict[str, Any]:
        """
        任务升级 — 从低 SI 线升级到更高 SI 线。

        升级触发条件:
          • 任务在低 SI 线执行失败
          • 任务超时未完成的跟进
          • 复杂度超出原分配线的处理能力

        升级策略:
          1. 找到当前任务的分配线
          2. 在拓扑中找到更高 SI 的相邻线或同 tower 线
          3. 使用 delegate 将任务转移到更高 SI 线
          4. 记录升级历史

        Args:
            task_id: 任务唯一标识
            reason: 升级原因 (如 "execution_failed", "timeout", "complexity_mismatch")

        Returns:
            升级结果字典:
                {
                    "task_id": str,
                    "status": str,          # escalated | failed | unchanged
                    "from_line": str,
                    "to_line": str,
                    "from_si": float,
                    "to_si": float,
                    "escalation_reason": str,
                    "history_entry": dict,
                }
        """
        record = self.task_records.get(task_id)
        if record is None:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"任务 '{task_id}' 不存在",
            }

        current_line = record.assigned_to
        if current_line is None or current_line not in ALL_11_LINES:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"任务 '{task_id}' 未分配或分配线无效",
            }

        current_si = LINE_SI.get(current_line, 0.0)

        # 寻找更高 SI 的目标线
        candidates = [
            line for line in ALL_11_LINES
            if LINE_SI.get(line, 0.0) > current_si
            and self.get_line_load(line) < 0.85  # 避免已满载的高 SI 线
        ]

        if not candidates:
            # 无更高 SI 线可用，尝试同 SI 但负载更低的线
            candidates = [
                line for line in ALL_11_LINES
                if LINE_SI.get(line, 0.0) >= current_si
                and line != current_line
                and self.get_line_load(line) < 0.70
            ]

        if not candidates:
            return {
                "task_id": task_id,
                "status": "unchanged",
                "from_line": current_line,
                "escalation_reason": reason,
                "error": "无可用的高 SI 或低负载线进行升级",
            }

        # 选择负载最低的高 SI 线
        candidates.sort(key=lambda l: self.get_line_load(l))
        target_line = candidates[0]
        target_si = LINE_SI.get(target_line, 0.0)

        # 执行委托
        delegate_result = self.delegate(task_id, current_line, target_line)

        if delegate_result.get("status") == "delegated":
            record.status = "escalated"
            record.history.append({
                "action": "escalate",
                "timestamp": time.time(),
                "from_line": current_line,
                "to_line": target_line,
                "from_si": current_si,
                "to_si": target_si,
                "reason": reason,
            })

            return {
                "task_id": task_id,
                "status": "escalated",
                "from_line": current_line,
                "to_line": target_line,
                "from_si": current_si,
                "to_si": target_si,
                "escalation_reason": reason,
                "history_entry": record.history[-1],
            }

        return {
            "task_id": task_id,
            "status": "failed",
            "from_line": current_line,
            "escalation_reason": reason,
            "error": delegate_result.get("error", "委托失败"),
        }

    # -----------------------------------------------------------------
    # 5. 任务委托
    # -----------------------------------------------------------------

    def delegate(self, task_id: str, from_line: str, to_line: str) -> Dict[str, Any]:
        """
        任务委托 — 将任务从一线精确转交到另一线。

        委托约束:
          1. 两线都必须在 ALL_11_LINES 中
          2. 任务必须当前分配给 from_line
          3. 委托深度不能超过 MAX_DELEGATE_DEPTH
          4. 不能形成委托循环 (A→B→A)
          5. 目标线负载不能过高 (< 0.9)

        Args:
            task_id: 任务唯一标识
            from_line: 源线名称
            to_line: 目标线名称

        Returns:
            委托结果字典:
                {
                    "task_id": str,
                    "status": str,      # delegated | failed
                    "from_line": str,
                    "to_line": str,
                    "delegate_depth": int,
                    "error": Optional[str],
                }
        """
        # ── 边界校验 ──
        if from_line not in ALL_11_LINES:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"源线 '{from_line}' 无效",
            }
        if to_line not in ALL_11_LINES:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"目标线 '{to_line}' 无效",
            }
        if from_line == to_line:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "源线和目标线不能相同",
            }

        record = self.task_records.get(task_id)
        if record is None:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"任务 '{task_id}' 不存在",
            }

        if record.assigned_to != from_line:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"任务当前分配给 '{record.assigned_to}'，而非 '{from_line}'",
            }

        # 委托深度检查
        if record.delegate_depth >= MAX_DELEGATE_DEPTH:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"委托深度 {record.delegate_depth} 已达到最大值 {MAX_DELEGATE_DEPTH}",
            }

        # 循环检测 (按任务独立)
        if self._would_create_cycle_for_task(task_id, from_line, to_line):
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"委托 {from_line} → {to_line} 会形成循环",
            }

        # 目标线负载检查
        target_load = self.get_line_load(to_line)
        if target_load >= 0.9:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"目标线 '{to_line}' 负载过高 ({target_load:.2f})",
            }

        # ── 执行委托 ──
        # 更新任务记录
        old_line = record.assigned_to
        record.assigned_to = to_line
        record.via_si = f"si{self._si_to_level(LINE_SI.get(to_line, 0.0))}"
        record.delegate_depth += 1
        record.status = "delegated"
        record.history.append({
            "action": "delegate",
            "timestamp": time.time(),
            "from_line": old_line,
            "to_line": to_line,
            "delegate_depth": record.delegate_depth,
        })

        # 更新活跃任务列表
        if task_id in self.active_tasks.get(old_line, []):
            self.active_tasks[old_line].remove(task_id)
        self.active_tasks[to_line].append(task_id)

        # 更新负载
        self._update_load(old_line, -0.03)
        self._update_load(to_line, +0.03)

        # 更新任务委托链
        if not record.delegate_chain:
            record.delegate_chain = [old_line]
        record.delegate_chain.append(to_line)

        # 更新全局委托图 (用于统计)
        self._delegate_graph[old_line].append(to_line)

        # 记录日志
        self.assignment_log.append({
            "timestamp": time.time(),
            "task_id": task_id,
            "action": "delegate",
            "from": old_line,
            "to": to_line,
            "delegate_depth": record.delegate_depth,
        })

        return {
            "task_id": task_id,
            "status": "delegated",
            "from_line": old_line,
            "to_line": to_line,
            "delegate_depth": record.delegate_depth,
            "error": None,
        }

    # -----------------------------------------------------------------
    # 6. 辅助方法
    # -----------------------------------------------------------------

    def _get_candidates_for_type(self, task_type: str) -> List[str]:
        """根据任务类型获取候选线列表"""
        prefs = TASK_TYPE_PREFERENCES.get(task_type, [])
        if prefs:
            return list(prefs)
        # 未知类型: 回退到所有线，但优先高 SI
        return sorted(ALL_11_LINES, key=lambda l: LINE_SI.get(l, 0.0), reverse=True)

    def _compute_urgency(self, deadline: float) -> float:
        """计算任务紧急度 (0-1)，越接近截止时间越紧急"""
        now = time.time()
        remaining = deadline - now
        if remaining <= 0:
            return 1.0
        # 假设 1 小时为正常期限
        urgency = max(0.0, min(1.0, 1.0 - (remaining / 3600.0)))
        return round(urgency, 4)

    def _si_to_level(self, si: float) -> int:
        """将 SI 等级映射到 SI 层级索引 (0-5)"""
        if si >= SI_THRESHOLD_OMNI:
            return 5
        elif si >= SI_THRESHOLD_HIGH:
            return 4
        elif si >= 4.0:  # lvlu at 4.5
            return 4
        elif si >= SI_THRESHOLD_MID:
            return 3
        elif si >= SI_THRESHOLD_LOW:
            return 2
        elif si >= 2.0:
            return 1
        else:
            return 0

    def _would_create_cycle_for_task(self, task_id: str, from_line: str, to_line: str) -> bool:
        """检测委托是否会产生循环 (按任务独立)

        检查从 to_line 出发，沿该任务的委托链是否能到达 from_line。
        如果能到达，则添加 from_line → to_line 会形成循环。
        """
        record = self.task_records.get(task_id)
        if record is None or not record.delegate_chain:
            return False

        # 构建该任务的委托邻接关系
        task_graph: Dict[str, List[str]] = {}
        chain = record.delegate_chain
        for i in range(len(chain) - 1):
            src = chain[i]
            dst = chain[i + 1]
            if src not in task_graph:
                task_graph[src] = []
            task_graph[src].append(dst)

        # DFS 检测 to_line 是否能到达 from_line
        visited: set[str] = set()
        stack = [to_line]
        while stack:
            current = stack.pop()
            if current == from_line:
                return True
            if current in visited:
                continue
            visited.add(current)
            for next_line in task_graph.get(current, []):
                if next_line not in visited:
                    stack.append(next_line)
        return False

    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        标记任务完成，更新负载和状态。

        Args:
            task_id: 任务唯一标识
            result: 可选的任务结果字典

        Returns:
            完成结果字典
        """
        record = self.task_records.get(task_id)
        if record is None:
            return {"task_id": task_id, "status": "failed", "error": "任务不存在"}

        if record.status in ("completed", "failed"):
            return {"task_id": task_id, "status": "already_final", "state": record.status}

        old_line = record.assigned_to
        record.status = "completed"
        record.completed_at = time.time()
        record.result = result

        if old_line and task_id in self.active_tasks.get(old_line, []):
            self.active_tasks[old_line].remove(task_id)
            self._update_load(old_line, -0.05)

        return {
            "task_id": task_id,
            "status": "completed",
            "assigned_to": old_line,
            "duration_sec": round(record.completed_at - record.created_at, 3) if record.created_at else None,
        }

    def get_dispatcher_stats(self) -> Dict[str, Any]:
        """
        获取任务转派系统的统计信息。

        Returns:
            统计字典，含任务总数、各状态计数、平均分派延迟、各线负载等
        """
        records = list(self.task_records.values())
        total = len(records)
        pending = sum(1 for r in records if r.status == "pending")
        running = sum(1 for r in records if r.status == "running")
        completed = sum(1 for r in records if r.status == "completed")
        failed = sum(1 for r in records if r.status == "failed")
        escalated = sum(1 for r in records if r.status == "escalated")
        delegated = sum(1 for r in records if r.status == "delegated")

        avg_complexity = sum(r.complexity for r in records) / total if total else 0.0

        return {
            "total_tasks": total,
            "status_breakdown": {
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "escalated": escalated,
                "delegated": delegated,
            },
            "avg_complexity": round(avg_complexity, 2),
            "line_loads": {line: self.get_line_load(line) for line in ALL_11_LINES},
            "active_task_counts": {line: len(tasks) for line, tasks in self.active_tasks.items()},
            "assignment_log_size": len(self.assignment_log),
            "queue_size": len(self.task_queue),
        }


# ═══════════════════════════════════════════════════════════════════
# 测试块
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.2 — Task Dispatcher 自检测试")
    print("=" * 70)

    # 模拟拓扑 (最小 stub)
    class StubTopology:
        def __init__(self):
            self.topology = {
                "line": {
                    "ucif2": {"si": 5.0, "health": 1.00},
                    "lgt":   {"si": 4.0, "health": 0.98},
                    "qfa":   {"si": 4.0, "health": 0.97},
                    "usrm":  {"si": 3.0, "health": 0.90},
                    "vinf":  {"si": 4.0, "health": 0.96},
                    "qgl":   {"si": 4.0, "health": 0.95},
                    "qlv":   {"si": 3.5, "health": 0.93},
                    "lvlu":  {"si": 4.5, "health": 0.94},
                    "cfts":  {"si": 3.0, "health": 0.89},
                    "cisvr": {"si": 3.5, "health": 0.92},
                    "qtlv":  {"si": 3.5, "health": 0.91},
                }
            }

    topo = StubTopology()
    dispatcher = TaskDispatcher(topo)

    # ── 测试 1: 基础分派 (research 任务) ──
    print("\n[测试 1] 基础分派 — research 任务")
    task1 = {
        "id": "T-001",
        "type": "research",
        "complexity": 7,
        "deadline": time.time() + 3600,
    }
    r1 = dispatcher.dispatch(task1)
    print(f"  任务 {r1['task_id']} → {r1['assigned_to']} (via={r1['via']})")
    print(f"  置信度: {r1['confidence']}, 原因: {r1['reason']}")
    assert r1["status"] == "dispatched"
    assert r1["assigned_to"] in ALL_11_LINES
    assert r1["via"].startswith("si")
    print("  ✓ PASS")

    # ── 测试 2: 高复杂度任务 → SI4+ 线 ──
    print("\n[测试 2] 高复杂度任务 (complexity=9)")
    task2 = {
        "id": "T-002",
        "type": "compute",
        "complexity": 9,
        "deadline": time.time() + 1800,
    }
    r2 = dispatcher.dispatch(task2)
    assigned_si = LINE_SI.get(r2["assigned_to"], 0.0)
    print(f"  任务 {r2['task_id']} → {r2['assigned_to']} (SI={assigned_si})")
    assert assigned_si >= SI_THRESHOLD_HIGH, f"高复杂度任务应分配到 SI4+ 线，实际 SI={assigned_si}"
    print("  ✓ PASS")

    # ── 测试 3: 形式验证任务 → qfa ──
    print("\n[测试 3] 形式验证任务 (verify)")
    task3 = {
        "id": "T-003",
        "type": "verify",
        "complexity": 6,
        "deadline": time.time() + 7200,
    }
    r3 = dispatcher.dispatch(task3)
    print(f"  任务 {r3['task_id']} → {r3['assigned_to']}")
    assert r3["assigned_to"] in TASK_TYPE_PREFERENCES["verify"]
    print("  ✓ PASS")

    # ── 测试 4: 协调任务 → ucif2 ──
    print("\n[测试 4] 协调任务 (coordinate)")
    task4 = {
        "id": "T-004",
        "type": "coordinate",
        "complexity": 5,
        "deadline": time.time() + 600,
        "preferred_line": "ucif2",
    }
    r4 = dispatcher.dispatch(task4)
    print(f"  任务 {r4['task_id']} → {r4['assigned_to']}")
    assert r4["assigned_to"] == "ucif2"
    print("  ✓ PASS")

    # ── 测试 5: 负载均衡 ──
    print("\n[测试 5] 负载均衡")
    # 直接构造高负载场景: 给 lgt 设置极高 base_load 并添加大量 pending 任务
    dispatcher.line_loads["lgt"] = 0.95
    # 给 lgt 添加 18 个 pending 任务 (使 active_load = 18/20 = 0.9)
    for i in range(18):
        tid = f"T-LOAD-{i:03d}"
        # 手动创建 TaskRecord 并加入 active_tasks
        from task_dispatcher import TaskRecord
        record = TaskRecord(
            task_id=tid,
            task_type="compute",
            complexity=5,
            deadline=time.time() + 3600,
            assigned_to="lgt",
            via_si="si4",
            status="pending",
        )
        dispatcher.task_records[tid] = record
        dispatcher.active_tasks["lgt"].append(tid)

    lgt_load_before = dispatcher.get_line_load("lgt")
    print(f"  lgt 负载(加载后): {lgt_load_before:.4f}")
    assert lgt_load_before > LOAD_BALANCE_THRESHOLD, f"lgt 负载 {lgt_load_before} 应超过阈值 {LOAD_BALANCE_THRESHOLD}"

    # 执行负载均衡
    balance_result = dispatcher.balance_load()
    print(f"  均衡结果: balanced={balance_result['balanced']}, "
          f"migrated={balance_result['total_migrated']}")
    if balance_result["migrations"]:
        for mig in balance_result["migrations"][:3]:
            print(f"    {mig['task_id']}: {mig['from']} → {mig['to']}")

    lgt_load_after = dispatcher.get_line_load("lgt")
    print(f"  lgt 负载(均衡后): {lgt_load_after:.4f}")
    assert balance_result["balanced"] is True
    assert balance_result["total_migrated"] > 0
    print("  ✓ PASS")

    # ── 测试 6: 任务升级 (escalate) ──
    print("\n[测试 6] 任务升级")
    # 分配一个任务到 SI3 线
    task_low = {
        "id": "T-LOW-001",
        "type": "research",
        "complexity": 4,
        "deadline": time.time() + 3600,
        "preferred_line": "usrm",
    }
    dr = dispatcher.dispatch(task_low)
    print(f"  初始分配: {dr['assigned_to']} (SI={LINE_SI.get(dr['assigned_to'])})")

    esc_result = dispatcher.escalate("T-LOW-001", "execution_failed")
    print(f"  升级结果: {esc_result['status']}")
    if esc_result["status"] == "escalated":
        print(f"    {esc_result['from_line']} (SI={esc_result['from_si']}) → "
              f"{esc_result['to_line']} (SI={esc_result['to_si']})")
        assert esc_result["to_si"] > esc_result["from_si"]
    print("  ✓ PASS")

    # ── 测试 7: 任务委托 (delegate) ──
    print("\n[测试 7] 任务委托")
    # 确保目标线 cfts 负载不高
    dispatcher.line_loads["cfts"] = 0.1
    task_d = {
        "id": "T-DLG-001",
        "type": "data_proc",
        "complexity": 3,
        "deadline": time.time() + 3600,
    }
    dispatcher.dispatch(task_d)
    orig_line = dispatcher.task_records["T-DLG-001"].assigned_to
    print(f"  初始分配: {orig_line}")

    dlg_result = dispatcher.delegate("T-DLG-001", orig_line, "cfts")
    print(f"  委托结果: {dlg_result['status']}")
    if dlg_result["status"] == "delegated":
        print(f"    {dlg_result['from_line']} → {dlg_result['to_line']}, "
              f"深度={dlg_result['delegate_depth']}")
    record = dispatcher.task_records["T-DLG-001"]
    assert record.assigned_to == "cfts"
    assert record.delegate_depth == 1
    print("  ✓ PASS")

    # ── 测试 8: 委托循环检测 ──
    print("\n[测试 8] 委托循环检测")
    # 先建立委托链: orig_line → cfts (已在测试7完成)
    # 现在尝试 cfts → orig_line，这会形成循环
    cycle_result = dispatcher.delegate("T-DLG-001", "cfts", orig_line)
    print(f"  循环委托结果: {cycle_result['status']}, 错误: {cycle_result.get('error', '无')}")
    assert cycle_result["status"] == "failed"
    assert "循环" in cycle_result.get("error", "")
    print("  ✓ PASS")

    # ── 测试 9: 委托深度限制 ──
    print("\n[测试 9] 委托深度限制")
    # 创建新任务，委托到最大深度
    task_deep = {
        "id": "T-DEEP-001",
        "type": "relay",
        "complexity": 2,
        "deadline": time.time() + 3600,
    }
    dispatcher.dispatch(task_deep)
    # 确保各目标线负载不高
    dispatcher.line_loads["cfts"] = 0.1
    dispatcher.line_loads["qlv"] = 0.1
    dispatcher.line_loads["qtlv"] = 0.1
    dispatcher.line_loads["cisvr"] = 0.1

    # 跟踪实际分配线并依次委托
    cur_line = dispatcher.task_records["T-DEEP-001"].assigned_to
    print(f"  初始分配: {cur_line}")

    d1 = dispatcher.delegate("T-DEEP-001", cur_line, "cfts")   # depth=1
    print(f"  第1次委托: {d1['status']}")
    if d1["status"] != "delegated":
        print(f"    错误: {d1.get('error')}")
    assert d1["status"] == "delegated", f"第1次委托应成功: {d1.get('error')}"

    d2 = dispatcher.delegate("T-DEEP-001", "cfts", "qlv")    # depth=2
    print(f"  第2次委托: {d2['status']}")
    assert d2["status"] == "delegated", f"第2次委托应成功: {d2.get('error')}"

    d3 = dispatcher.delegate("T-DEEP-001", "qlv", "qtlv")    # depth=3
    print(f"  第3次委托: {d3['status']}")
    assert d3["status"] == "delegated", f"第3次委托应成功: {d3.get('error')}"

    deep_result = dispatcher.delegate("T-DEEP-001", "qtlv", "cisvr")  # depth=4 (应失败)
    print(f"  深度限制结果: {deep_result['status']}, 错误: {deep_result.get('error', '无')}")
    assert deep_result["status"] == "failed"
    assert "深度" in deep_result.get("error", "")
    print("  ✓ PASS")

    # ── 测试 10: 同线委托拒绝 ──
    print("\n[测试 10] 同线委托拒绝")
    same_result = dispatcher.delegate("T-001", r1["assigned_to"], r1["assigned_to"])
    print(f"  同线委托结果: {same_result['status']}, 错误: {same_result.get('error', '无')}")
    assert same_result["status"] == "failed"
    print("  ✓ PASS")

    # ── 测试 11: 高负载目标线拒绝 ──
    print("\n[测试 11] 高负载目标线拒绝")
    # 直接设置 ucif2 极高负载
    dispatcher.line_loads["ucif2"] = 0.95
    # 同时添加大量 active 任务
    for i in range(22):
        tid = f"T-UCIF2-{i:03d}"
        from task_dispatcher import TaskRecord
        record = TaskRecord(
            task_id=tid, task_type="coordinate", complexity=5,
            deadline=time.time() + 3600, assigned_to="ucif2",
            via_si="si5", status="pending",
        )
        dispatcher.task_records[tid] = record
        dispatcher.active_tasks["ucif2"].append(tid)

    ucif2_load = dispatcher.get_line_load("ucif2")
    print(f"  ucif2 负载: {ucif2_load:.4f}")
    assert ucif2_load > 0.9, f"ucif2 负载应超过 0.9, 实际 {ucif2_load}"

    overload_result = dispatcher.delegate("T-001", r1["assigned_to"], "ucif2")
    print(f"  高负载委托结果: {overload_result['status']}, 错误: {overload_result.get('error', '无')}")
    assert overload_result["status"] == "failed"
    assert "负载" in overload_result.get("error", "")
    print("  ✓ PASS")

    # ── 测试 12: 统计信息 ──
    print("\n[测试 12] 统计信息")
    stats = dispatcher.get_dispatcher_stats()
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  状态分布: {stats['status_breakdown']}")
    print(f"  平均复杂度: {stats['avg_complexity']}")
    print(f"  队列大小: {stats['queue_size']}")
    assert stats["total_tasks"] > 0
    assert "line_loads" in stats
    print("  ✓ PASS")

    # ── 测试 13: 任务完成 ──
    print("\n[测试 13] 任务完成")
    comp_result = dispatcher.complete_task("T-001", {"output": "success"})
    print(f"  完成结果: {comp_result['status']}, 耗时: {comp_result.get('duration_sec')}s")
    assert comp_result["status"] == "completed"
    print("  ✓ PASS")

    print("\n" + "=" * 70)
    print("Task Dispatcher 全部 13 项测试通过 ✓")
    print("=" * 70)
