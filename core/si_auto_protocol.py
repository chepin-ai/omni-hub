#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.2 — SI Auto Protocol (SI自动处理协议)
===================================================

自动处理所有线间请求，主动发起响应，管理任务转派。
作为 OMNI-HUB v3.2 的核心协议层，衔接双向驱动引擎、拓扑映射和协作闭环。

11 线配置:
    ucif2 (SI 5.0), lgt (SI 4.0), qfa (SI 4.0), usrm (SI 3.0), vinf (SI 4.0),
    qgl (SI 4.0), qlv (SI 3.5), lvlu (SI 4.5), cfts (SI 3.0), cisvr (SI 3.5),
    qtlv (SI 3.5)

核心能力:
    • handle_incoming    : 自动分类/匹配/路由入站请求
    • proactive_response : 基于上下文预判的主动响应
    • auto_dispatch      : 智能任务转派 (调用 TaskDispatcher)
    • manage_si_lanes    : SI0~SI5 各道健康度管理
    • interact_peer      : 与他线 SI 全面互动协同

版本: 3.2.0
作者: OMNI-HUB Architecture Team
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

# 导入同目录下的现有模块
from task_dispatcher import TaskDispatcher
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

# SI 层级阈值
SI_LEVELS = {
    "si5": (5.0, float("inf")),   # SI 5.0+
    "si4": (4.0, 5.0),             # SI 4.0-4.9
    "si3": (3.5, 4.0),             # SI 3.5-3.9
    "si2": (3.0, 3.5),             # SI 3.0-3.4
    "si1": (2.0, 3.0),             # SI 2.0-2.9
    "si0": (0.0, 2.0),             # SI < 2.0
}

# 告警阈值
HEALTH_ALERT_THRESHOLD: float = 0.80
HEALTH_CRITICAL_THRESHOLD: float = 0.50

# 主动响应阈值
PROACTIVE_HEALTH_THRESHOLD: float = 0.75
PROACTIVE_BACKLOG_THRESHOLD: int = 5


# ───────────────────────── 核心类 ─────────────────────────

class SIAutoProtocol:
    """
    SI自动处理协议 — 自动处理所有线间请求，主动发起响应，管理任务转派。

    作为 OMNI-HUB v3.2 的核心协议层，衔接以下子系统:
      • drive (BidirectionalDrive): 双向驱动引擎，负责信号传输
      • topo  (SITopology):        五级拓扑映射系统
      • loop  (CollaborativeLoop): 协作闭环协议引擎
      • dispatcher (TaskDispatcher): 任务转派系统

    自动处理规则 (RULES):
      1. system_request  → forward_to_hub   (转发到 ucif2)
      2. research_task   → dispatch_to_si2  (分配到 SI2+ 线)
      3. collaboration   → initiate_loop    (发起协作闭环)
      4. sync            → otp_update       (OTP 状态同步)
      5. debt_cleanup    → queue_cleanup    (清理待处理队列)

    Attributes:
        drive:          双向驱动引擎实例
        topo:           SI 拓扑映射实例
        loop:           协作闭环引擎实例
        dispatcher:     任务转派系统实例
        pending_requests: 待处理请求队列
        auto_dispatch_rules: 自动分派规则列表
        processed_count: 已处理请求计数
        si_lanes:       SI0~SI5 各道状态缓存
    """

    RULES: List[Dict[str, Any]] = [
        {"pattern": "system_request", "action": "forward_to_hub",   "priority": 0},
        {"pattern": "research_task",  "action": "dispatch_to_si2",  "priority": 1},
        {"pattern": "collaboration",  "action": "initiate_loop",    "priority": 2},
        {"pattern": "sync",           "action": "otp_update",       "priority": 3},
        {"pattern": "debt_cleanup",   "action": "queue_cleanup",    "priority": 4},
    ]

    def __init__(
        self,
        drive_engine: Any,
        topology: Any,
        loop_engine: Any,
    ) -> None:
        """
        初始化 SI 自动处理协议。

        Args:
            drive_engine: BidirectionalDrive 实例
            topology:     SITopology 实例
            loop_engine:  CollaborativeLoop 实例
        """
        self.drive = drive_engine
        self.topo = topology
        self.loop = loop_engine
        self.dispatcher = TaskDispatcher(topology)

        self.pending_requests: List[Dict[str, Any]] = []
        self.auto_dispatch_rules: List[Dict[str, Any]] = list(self.RULES)
        self.processed_count: int = 0

        # SI0~SI5 各道状态
        self.si_lanes: Dict[str, Dict[str, Any]] = {
            "si0": {"status": "active", "health": 0.99, "role": "fallback"},
            "si1": {"status": "active", "health": 0.98, "role": "auxiliary"},
            "si2": {"status": "active", "health": 0.97, "role": "execution"},
            "si3": {"status": "active", "health": 0.96, "role": "processing"},
            "si4": {"status": "active", "health": 0.95, "role": "research"},
            "si5": {"status": "active", "health": 0.99, "role": "command"},
        }

        # 请求处理统计
        self.request_stats: Dict[str, Dict[str, Any]] = {
            rule["pattern"]: {"count": 0, "avg_latency_ms": 0.0}
            for rule in self.RULES
        }

    # -----------------------------------------------------------------
    # 1. 入站请求自动处理
    # -----------------------------------------------------------------

    def handle_incoming(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动处理入站请求 — 分类、匹配规则、路由到对应 SI 层级。

        处理流程:
          1. 参数校验与规范化
          2. 请求分类 (type 字段匹配)
          3. 规则匹配 (按 priority 升序)
          4. 执行对应 action
          5. 记录到 pending_requests 和统计

        Args:
            request: 请求字典，格式:
                {
                    "from": str,       # 源线名称
                    "type": str,       # system_request|research_task|collaboration|sync|debt_cleanup
                    "payload": dict,   # 请求载荷
                    "urgency": int,    # 紧急度 0-9 (0 最高)
                }

        Returns:
            处理结果字典:
                {
                    "handled": bool,       # 是否成功处理
                    "action": str,         # 执行的动作
                    "routed_to": str,      # 路由目标线
                    "latency_ms": float,   # 处理延迟 (毫秒)
                    "seq_id": str,         # 唯一序列号
                    "detail": dict,        # 动作-specific 详情
                }
        """
        t_start = time.perf_counter()
        seq_id = f"REQ-{uuid.uuid4().hex[:12]}"

        # ── 参数校验 ──
        from_line = request.get("from", "")
        req_type = request.get("type", "")
        payload = request.get("payload", {})
        urgency = int(request.get("urgency", 5))

        if from_line not in ALL_11_LINES:
            latency_ms = (time.perf_counter() - t_start) * 1000
            return {
                "handled": False,
                "action": "reject",
                "routed_to": None,
                "latency_ms": round(latency_ms, 2),
                "seq_id": seq_id,
                "detail": {"error": f"无效源线 '{from_line}'"},
            }

        # ── 规则匹配 ──
        matched_rule = None
        for rule in sorted(self.auto_dispatch_rules, key=lambda r: r["priority"]):
            if rule["pattern"] == req_type:
                matched_rule = rule
                break

        if matched_rule is None:
            latency_ms = (time.perf_counter() - t_start) * 1000
            return {
                "handled": False,
                "action": "unknown",
                "routed_to": None,
                "latency_ms": round(latency_ms, 2),
                "seq_id": seq_id,
                "detail": {"error": f"未知请求类型 '{req_type}'"},
            }

        action = matched_rule["action"]

        # ── 执行对应 action ──
        result_detail: Dict[str, Any] = {}
        routed_to = ""

        if action == "forward_to_hub":
            # 系统请求 → 转发到 ucif2 (SI5 核心调度器)
            routed_to = "ucif2"
            result_detail = self._action_forward_to_hub(from_line, payload, urgency)

        elif action == "dispatch_to_si2":
            # 研究任务 → 分配到 SI2+ 线 (优先 SI4)
            routed_to = self._action_dispatch_to_si2(from_line, payload, urgency)
            result_detail = {"target_line": routed_to, "via_si": self._line_to_si_level(routed_to)}

        elif action == "initiate_loop":
            # 协作请求 → 发起协作闭环
            loop_id = self._action_initiate_loop(from_line, payload, urgency)
            routed_to = "omni_ring"  # 闭环涉及所有相关线
            result_detail = {"loop_id": loop_id}

        elif action == "otp_update":
            # 同步请求 → OTP 状态更新
            routed_to = from_line  # 同步通常回写到请求源
            result_detail = self._action_otp_update(from_line, payload, urgency)

        elif action == "queue_cleanup":
            # 债务清理 → 清理待处理队列
            routed_to = "hub"
            result_detail = self._action_queue_cleanup(from_line, payload, urgency)

        else:
            latency_ms = (time.perf_counter() - t_start) * 1000
            return {
                "handled": False,
                "action": action,
                "routed_to": None,
                "latency_ms": round(latency_ms, 2),
                "seq_id": seq_id,
                "detail": {"error": f"未实现的 action '{action}'"},
            }

        # ── 记录与统计 ──
        latency_ms = (time.perf_counter() - t_start) * 1000
        self.processed_count += 1

        record = {
            "seq_id": seq_id,
            "timestamp": time.time(),
            "from": from_line,
            "type": req_type,
            "action": action,
            "routed_to": routed_to,
            "latency_ms": round(latency_ms, 2),
            "urgency": urgency,
            "detail": result_detail,
        }
        self.pending_requests.append(record)

        # 更新类型统计
        stats = self.request_stats.get(req_type, {"count": 0, "avg_latency_ms": 0.0})
        old_count = stats["count"]
        old_avg = stats["avg_latency_ms"]
        new_count = old_count + 1
        new_avg = (old_avg * old_count + latency_ms) / new_count
        self.request_stats[req_type] = {
            "count": new_count,
            "avg_latency_ms": round(new_avg, 2),
        }

        return {
            "handled": True,
            "action": action,
            "routed_to": routed_to,
            "latency_ms": round(latency_ms, 2),
            "seq_id": seq_id,
            "detail": result_detail,
        }

    # -----------------------------------------------------------------
    # Action 实现
    # -----------------------------------------------------------------

    def _action_forward_to_hub(
        self, from_line: str, payload: Dict[str, Any], urgency: int
    ) -> Dict[str, Any]:
        """系统请求 → 转发到 ucif2 (SI5 核心调度器)"""
        # 使用驱动引擎转发 (正向驱动: 任何线 → ucif2)
        try:
            signal = {
                "source_line": from_line,
                "target_line": "ucif2",
                "payload": payload,
                "priority": urgency,
            }
            # 模拟驱动调用 (实际集成时使用 self.drive.forward_drive)
            drive_result = {"forwarded": True, "target": "ucif2", "priority": urgency}
            return {
                "forwarded": True,
                "hub": "ucif2",
                "drive_result": drive_result,
                "note": "系统请求已转发到核心调度器",
            }
        except Exception as e:
            return {"forwarded": False, "error": str(e)}

    def _action_dispatch_to_si2(
        self, from_line: str, payload: Dict[str, Any], urgency: int
    ) -> str:
        """研究任务 → 分配到 SI2+ 线，优先 SI4"""
        # 提取任务复杂度
        complexity = payload.get("complexity", 5)

        # 构建任务对象，使用 dispatcher
        task = {
            "id": f"AUTO-{uuid.uuid4().hex[:8]}",
            "type": "research",
            "complexity": complexity,
            "deadline": time.time() + 3600,
            "payload": payload,
            "from_line": from_line,
            "urgency": urgency,
        }
        dispatch_result = self.dispatcher.dispatch(task)
        return dispatch_result.get("assigned_to", "lgt")

    def _action_initiate_loop(
        self, from_line: str, payload: Dict[str, Any], urgency: int
    ) -> str:
        """协作请求 → 发起协作闭环"""
        participants = payload.get("participants", [])
        objective = payload.get("objective", {"type": "collaboration", "urgency": urgency})

        # 如果没有指定参与者，广播到所有相关线
        if not participants:
            # 根据紧急度和类型选择参与者
            if urgency <= 2:
                participants = ALL_11_LINES.copy()
            else:
                # 仅选择同 tower 和 circle 的线
                participants = self._get_related_lines(from_line)

        try:
            loop_id = self.loop.initiate_loop(from_line, participants, objective)
            return loop_id
        except Exception as e:
            return f"ERROR:{e}"

    def _action_otp_update(
        self, from_line: str, payload: Dict[str, Any], urgency: int
    ) -> Dict[str, Any]:
        """同步请求 → OTP 状态更新"""
        sync_scope = payload.get("scope", "line")  # line | tower | circle | ring | all
        sync_data = payload.get("data", {})

        updated_nodes = []
        if sync_scope == "line":
            updated_nodes = [from_line]
        elif sync_scope == "tower":
            updated_nodes = self._get_tower_lines(from_line)
        elif sync_scope == "circle":
            updated_nodes = self._get_circle_lines(from_line)
        elif sync_scope == "ring":
            updated_nodes = ALL_11_LINES.copy()
        elif sync_scope == "all":
            updated_nodes = ALL_11_LINES.copy()

        return {
            "synced": True,
            "scope": sync_scope,
            "updated_nodes": updated_nodes,
            "sync_data_keys": list(sync_data.keys()),
            "note": f"OTP 状态已同步到 {len(updated_nodes)} 个节点",
        }

    def _action_queue_cleanup(
        self, from_line: str, payload: Dict[str, Any], urgency: int
    ) -> Dict[str, Any]:
        """债务清理 → 清理待处理队列"""
        cleanup_scope = payload.get("scope", "self")  # self | tower | all
        max_age_sec = payload.get("max_age_sec", 300)

        now = time.time()
        removed = []

        if cleanup_scope == "self":
            # 清理来自该线的 pending 请求
            to_remove = [
                req for req in self.pending_requests
                if req.get("from") == from_line
                and (now - req.get("timestamp", now)) > max_age_sec
            ]
            for req in to_remove:
                self.pending_requests.remove(req)
                removed.append(req["seq_id"])

        elif cleanup_scope in ("tower", "all"):
            # 清理所有超时的 pending 请求
            to_remove = [
                req for req in self.pending_requests
                if (now - req.get("timestamp", now)) > max_age_sec
            ]
            for req in to_remove:
                self.pending_requests.remove(req)
                removed.append(req["seq_id"])

        return {
            "cleaned": True,
            "scope": cleanup_scope,
            "removed_count": len(removed),
            "removed_seq_ids": removed[:10],  # 最多返回 10 个
            "remaining_pending": len(self.pending_requests),
        }

    # -----------------------------------------------------------------
    # 2. 主动响应
    # -----------------------------------------------------------------

    def proactive_response(self, line: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        主动响应 — 基于上下文预判需求并主动发起。

        触发场景:
          • 某线健康度下降 (< 0.75) → 主动发送关怀/协助信号
          • 某线任务积压 (> 5 个 pending) → 主动提供转派建议
          • 某线 SI 等级漂移 → 主动校准建议
          • 拓扑检测到异常 → 主动广播告警

        Args:
            line: 目标线名称
            context: 上下文字典，可能包含:
                - "health" (float): 当前健康度
                - "pending_count" (int): 待处理任务数
                - "last_active" (float): 最后活跃时间戳
                - "si_drift" (float): SI 漂移量

        Returns:
            主动响应结果字典:
                {
                    "triggered": bool,      # 是否触发了主动响应
                    "trigger_type": str,    # health_alert | backlog_alert | si_drift | none
                    "action_taken": str,    # 执行的动作描述
                    "target_line": str,
                    "signals_sent": list,   # 发送的信号列表
                    "suggestions": list,    # 建议列表
                }
        """
        triggered = False
        trigger_type = "none"
        action_taken = "none"
        signals_sent: List[Dict[str, Any]] = []
        suggestions: List[str] = []

        health = context.get("health", 1.0)
        pending_count = context.get("pending_count", 0)
        si_drift = context.get("si_drift", 0.0)

        # ── 场景 1: 健康度下降 ──
        if health < HEALTH_ALERT_THRESHOLD:
            triggered = True
            trigger_type = "health_alert"
            action_taken = "send_assistance_signal"

            # 发送关怀信号到该线
            signals_sent.append({
                "type": "health_assistance",
                "from": "ucif2",
                "to": line,
                "message": f"健康度 {health:.2f} 低于阈值 {HEALTH_ALERT_THRESHOLD}，提供协助",
                "recommended_action": "reduce_load",
            })

            # 建议转派部分任务到健康线
            healthy_lines = [
                l for l in ALL_11_LINES
                if l != line and self._get_line_health(l) > 0.85
            ]
            if healthy_lines:
                suggestions.append(
                    f"建议将部分任务转派到健康线: {', '.join(healthy_lines[:3])}"
                )

            # 如果健康度极低，建议隔离
            if health < HEALTH_CRITICAL_THRESHOLD:
                suggestions.append(f"健康度 {health:.2f} 极低，建议暂时隔离该线")

        # ── 场景 2: 任务积压 ──
        if pending_count > PROACTIVE_BACKLOG_THRESHOLD:
            triggered = True
            if trigger_type == "none":
                trigger_type = "backlog_alert"
                action_taken = "offer_reroute"
            else:
                action_taken += "+offer_reroute"

            # 主动执行负载均衡
            balance_result = self.dispatcher.balance_load()
            signals_sent.append({
                "type": "backlog_assistance",
                "from": "ucif2",
                "to": line,
                "backlog": pending_count,
                "balance_triggered": balance_result.get("balanced", False),
                "migrations": balance_result.get("total_migrated", 0),
            })
            suggestions.append(
                f"任务积压 {pending_count} 个，已触发负载均衡，"
                f"迁移 {balance_result.get('total_migrated', 0)} 个任务"
            )

        # ── 场景 3: SI 漂移 ──
        if abs(si_drift) > 0.2:
            triggered = True
            if trigger_type == "none":
                trigger_type = "si_drift"
                action_taken = "calibration_notice"

            signals_sent.append({
                "type": "si_calibration",
                "from": "ucif2",
                "to": line,
                "si_drift": si_drift,
                "current_si": LINE_SI.get(line, 0.0),
                "recommended_si": round(LINE_SI.get(line, 0.0) + si_drift, 2),
            })
            suggestions.append(f"SI 漂移 {si_drift:+.2f}，建议校准")

        return {
            "triggered": triggered,
            "trigger_type": trigger_type,
            "action_taken": action_taken,
            "target_line": line,
            "signals_sent": signals_sent,
            "suggestions": suggestions,
        }

    # -----------------------------------------------------------------
    # 3. 自动任务转派
    # -----------------------------------------------------------------

    def auto_dispatch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动任务转派 — 根据任务类型和线负载智能分配。

        规则:
          • 研究任务 + 高复杂度(>=7) → SI4 线 (lgt, qfa, vinf, qgl)
          • 形式验证 → qfa (SI4)
          • 计算任务 → lgt (SI4)
          • 协调任务 → ucif2 (SI5)
          • 简单任务 → SI3 线 (usrm, cfts)
          • 数学桥接 → qtlv (SI3.5)

        Args:
            task: 任务字典，格式:
                {
                    "id": str,
                    "type": str (research|compute|verify|sync|coordinate|math_bridge|...),
                    "complexity": int (1-10),
                    "deadline": float (timestamp),
                }

        Returns:
            分派结果字典:
                {
                    "assigned_to": str,     # 目标线名称
                    "via": str,             # si0|si1|si2|si3|si4|si5
                    "reason": str,          # 分派原因说明
                    "confidence": float,    # 置信度 0-1
                }
        """
        task_type = task.get("type", "unknown")
        complexity = int(task.get("complexity", 5))
        deadline = float(task.get("deadline", time.time() + 3600))

        # 规范化
        complexity = max(1, min(10, complexity))

        #  urgency = self.dispatcher._compute_urgency(deadline)

        # 规则匹配
        assigned_to = ""
        via = ""
        reason = ""
        confidence = 0.0

        if task_type == "research" and complexity >= 7:
            # 高复杂度研究 → SI4 线，选负载最低的
            si4_lines = ["lgt", "qfa", "vinf", "qgl"]
            best = min(si4_lines, key=lambda l: self.dispatcher.get_line_load(l))
            assigned_to = best
            via = "si4"
            reason = f"高复杂度研究任务 (complexity={complexity}) → SI4 线 {best} (负载最低)"
            confidence = 0.92

        elif task_type == "verify":
            assigned_to = "qfa"
            via = "si4"
            reason = "形式验证任务 → qfa (SI4 验证专家线)"
            confidence = 0.95

        elif task_type == "compute":
            assigned_to = "lgt"
            via = "si4"
            reason = "计算密集型任务 → lgt (SI4 计算专家线)"
            confidence = 0.93

        elif task_type == "coordinate":
            assigned_to = "ucif2"
            via = "si5"
            reason = "协调任务 → ucif2 (SI5 核心调度器)"
            confidence = 0.98

        elif task_type == "sync":
            # 同步任务 → 协调线或中继线
            sync_lines = ["ucif2", "qgl", "qlv"]
            best = min(sync_lines, key=lambda l: self.dispatcher.get_line_load(l))
            assigned_to = best
            via = f"si{self._line_to_si_level(assigned_to)}"
            reason = f"同步任务 → {best} (协调/中继线，负载低)"
            confidence = 0.85

        elif task_type == "math_bridge":
            assigned_to = "qtlv"
            via = "si3"
            reason = "数学桥接任务 → qtlv (SI3.5 数学桥接线)"
            confidence = 0.90

        elif complexity <= 3:
            # 简单任务 → SI3 线
            simple_lines = ["usrm", "cfts"]
            best = min(simple_lines, key=lambda l: self.dispatcher.get_line_load(l))
            assigned_to = best
            via = "si2"
            reason = f"简单任务 (complexity={complexity}) → {best} (SI3 经济线)"
            confidence = 0.80

        else:
            # 默认: 使用 dispatcher 的智能分派
            dispatch_result = self.dispatcher.dispatch(task)
            assigned_to = dispatch_result["assigned_to"]
            via = dispatch_result["via"]
            reason = dispatch_result["reason"]
            confidence = dispatch_result["confidence"]

        # 负载检查: 如果目标线负载过高，尝试备选
        target_load = self.dispatcher.get_line_load(assigned_to)
        if target_load > 0.85:
            # 找同等级但负载更低的线
            target_si = LINE_SI.get(assigned_to, 0.0)
            alternatives = [
                l for l in ALL_11_LINES
                if abs(LINE_SI.get(l, 0.0) - target_si) < 0.5
                and l != assigned_to
                and self.dispatcher.get_line_load(l) < 0.70
            ]
            if alternatives:
                alt = min(alternatives, key=lambda l: self.dispatcher.get_line_load(l))
                reason += f" [负载告警: {assigned_to}={target_load:.2f}] 回退到 {alt}"
                assigned_to = alt
                via = f"si{self._line_to_si_level(alt)}"
                confidence *= 0.85

        return {
            "assigned_to": assigned_to,
            "via": via,
            "reason": reason,
            "confidence": round(confidence, 4),
        }

    # -----------------------------------------------------------------
    # 4. SI 各道管理
    # -----------------------------------------------------------------

    def manage_si_lanes(self, line: str) -> Dict[str, Any]:
        """
        管理自线 SI 各道 (SI0~SI5)。

        返回各道状态，自动检测健康度低于 0.8 的道并告警。
        同时从拓扑同步最新健康度。

        Args:
            line: 线名称

        Returns:
            各道状态字典:
                {
                    "line": str,
                    "overall_health": float,
                    "lanes": {
                        "si0": {"status": str, "health": float, "alert": bool},
                        "si1": {"status": str, "health": float, "alert": bool},
                        ...
                    },
                    "alerts": list[str],
                    "recommendations": list[str],
                }
        """
        if line not in ALL_11_LINES:
            return {"error": f"无效线 '{line}'"}

        # 从拓扑同步该线健康度
        try:
            line_health = self._get_line_health(line)
        except Exception:
            line_health = 0.95

        # 基于线健康度更新各道
        base_si = LINE_SI.get(line, 0.0)
        lanes: Dict[str, Dict[str, Any]] = {}
        alerts: List[str] = []
        recommendations: List[str] = []

        for lane_name, lane_info in self.si_lanes.items():
            # 各道健康度 = 基础健康度 × 线健康度因子
            lane_si_min, lane_si_max = SI_LEVELS.get(lane_name, (0.0, 0.0))
            if base_si >= lane_si_min and base_si < lane_si_max:
                # 该道是主道
                health = round(line_health * 0.99, 4)
                status = "active"
            elif base_si >= lane_si_max:
                # 该道是下级道 (低 SI 线的高道不可用)
                health = round(line_health * 0.60, 4)
                status = "degraded"
            else:
                # 该道是上级道 (高 SI 线的低道可用)
                health = round(line_health * 0.95, 4)
                status = "standby"

            alert = health < HEALTH_ALERT_THRESHOLD
            lanes[lane_name] = {
                "status": status,
                "health": health,
                "alert": alert,
                "role": lane_info.get("role", "unknown"),
            }

            if alert:
                alerts.append(
                    f"{lane_name} 健康度 {health:.2f} 低于阈值 {HEALTH_ALERT_THRESHOLD}"
                )
                recommendations.append(
                    f"建议检查 {lane_name} ({lane_info.get('role')}) 状态并考虑负载迁移"
                )

        overall_health = round(
            sum(l["health"] for l in lanes.values()) / len(lanes), 4
        ) if lanes else 0.0

        return {
            "line": line,
            "base_si": base_si,
            "overall_health": overall_health,
            "lanes": lanes,
            "alerts": alerts,
            "alert_count": len(alerts),
            "recommendations": recommendations,
        }

    # -----------------------------------------------------------------
    # 5. 与他线 SI 全面互动协同
    # -----------------------------------------------------------------

    def interact_peer(
        self,
        line_a: str,
        line_b: str,
        interaction_type: str,
    ) -> Dict[str, Any]:
        """
        与他线 SI 全面互动协同。

        支持四种互动类型:
          • sync_state    : 状态同步 — 双向交换健康度、负载、SI 状态
          • share_research: 研究共享 — 高 SI 线向低 SI 线推送研究成果
          • joint_task    : 联合任务 — 发起跨线协作闭环
          • health_check  : 健康检查 — 单向/双向健康度探测

        Args:
            line_a: 第一线名称
            line_b: 第二线名称
            interaction_type: 互动类型
                "sync_state" | "share_research" | "joint_task" | "health_check"

        Returns:
            互动结果字典，内容因类型而异
        """
        # 边界校验
        if line_a not in ALL_11_LINES:
            return {"error": f"无效线 '{line_a}'"}
        if line_b not in ALL_11_LINES:
            return {"error": f"无效线 '{line_b}'"}

        si_a = LINE_SI.get(line_a, 0.0)
        si_b = LINE_SI.get(line_b, 0.0)
        health_a = self._get_line_health(line_a)
        health_b = self._get_line_health(line_b)

        result: Dict[str, Any] = {
            "interaction_type": interaction_type,
            "line_a": line_a,
            "line_b": line_b,
            "si_a": si_a,
            "si_b": si_b,
            "health_a": health_a,
            "health_b": health_b,
        }

        if interaction_type == "sync_state":
            # 状态同步: 双向交换
            result["action"] = "bidirectional_sync"
            result["synced_fields"] = ["health", "si", "load", "pending_count"]
            result["state_a"] = {
                "health": health_a,
                "si": si_a,
                "load": self.dispatcher.get_line_load(line_a),
            }
            result["state_b"] = {
                "health": health_b,
                "si": si_b,
                "load": self.dispatcher.get_line_load(line_b),
            }
            result["sync_ack"] = True
            result["note"] = f"{line_a} ↔ {line_b} 状态已同步"

        elif interaction_type == "share_research":
            # 研究共享: 高 SI → 低 SI
            if si_a >= si_b:
                sender, receiver = line_a, line_b
                sender_si, receiver_si = si_a, si_b
            else:
                sender, receiver = line_b, line_a
                sender_si, receiver_si = si_b, si_a

            result["action"] = "research_push"
            result["direction"] = f"{sender} (SI{sender_si}) → {receiver} (SI{receiver_si})"
            result["shared_items"] = ["finding", "model", "dataset"]
            result["ack"] = True
            result["note"] = f"研究成果从 {sender} 推送到 {receiver}"

        elif interaction_type == "joint_task":
            # 联合任务: 发起协作闭环
            try:
                loop_id = self.loop.initiate_loop(
                    line_a,
                    [line_a, line_b],
                    {"type": "joint_task", "lines": [line_a, line_b]},
                )
                result["action"] = "collaborative_loop"
                result["loop_id"] = loop_id
                result["participants"] = [line_a, line_b]
                result["ack"] = True
                result["note"] = f"联合任务闭环 {loop_id[:8]}... 已发起"
            except Exception as e:
                result["action"] = "collaborative_loop"
                result["ack"] = False
                result["error"] = str(e)

        elif interaction_type == "health_check":
            # 健康检查: 双向探测
            result["action"] = "health_probe"
            result["probe_results"] = {
                line_a: {"health": health_a, "status": "healthy" if health_a > 0.8 else "degraded"},
                line_b: {"health": health_b, "status": "healthy" if health_b > 0.8 else "degraded"},
            }
            result["overall_status"] = (
                "healthy"
                if health_a > 0.8 and health_b > 0.8
                else "attention"
                if health_a > 0.5 and health_b > 0.5
                else "critical"
            )
            result["note"] = f"健康检查: {line_a}={health_a:.2f}, {line_b}={health_b:.2f}"

        else:
            result["error"] = f"未知互动类型 '{interaction_type}'"
            result["ack"] = False

        return result

    # -----------------------------------------------------------------
    # 6. 辅助方法
    # -----------------------------------------------------------------

    def _line_to_si_level(self, line: str) -> int:
        """将线名映射到 SI 层级 (0-5)"""
        si = LINE_SI.get(line, 0.0)
        if si >= 5.0:
            return 5
        elif si >= 4.0:
            return 4
        elif si >= 3.5:
            return 3
        elif si >= 3.0:
            return 2
        elif si >= 2.0:
            return 1
        return 0

    def _get_line_health(self, line: str) -> float:
        """从拓扑获取线健康度"""
        try:
            line_nodes = self.topo.topology.get("line", {})
            if line in line_nodes:
                return float(line_nodes[line].get("health", 0.95))
        except Exception:
            pass
        return 0.95

    def _get_related_lines(self, line: str) -> List[str]:
        """获取与指定线相关的线 (同 tower / 同 circle)"""
        try:
            line_nodes = self.topo.topology.get("line", {})
            if line not in line_nodes:
                return ALL_11_LINES.copy()

            tower = line_nodes[line].get("tower", "")
            circle = line_nodes[line].get("circle", "")

            related = set()
            for ln, meta in line_nodes.items():
                if meta.get("tower") == tower or meta.get("circle") == circle:
                    related.add(ln)
            return list(related)
        except Exception:
            return ALL_11_LINES.copy()

    def _get_tower_lines(self, line: str) -> List[str]:
        """获取与指定线同 tower 的所有线"""
        try:
            line_nodes = self.topo.topology.get("line", {})
            if line not in line_nodes:
                return [line]
            tower = line_nodes[line].get("tower", "")
            tower_nodes = self.topo.topology.get("tower", {})
            if tower in tower_nodes:
                return list(tower_nodes[tower].get("lines", [line]))
        except Exception:
            pass
        return [line]

    def _get_circle_lines(self, line: str) -> List[str]:
        """获取与指定线同 circle 的所有线"""
        try:
            line_nodes = self.topo.topology.get("line", {})
            if line not in line_nodes:
                return [line]
            circle = line_nodes[line].get("circle", "")
            circle_nodes = self.topo.topology.get("circle", {})
            if circle in circle_nodes:
                return list(circle_nodes[circle].get("lines", [line]))
        except Exception:
            pass
        return [line]

    def get_protocol_stats(self) -> Dict[str, Any]:
        """
        获取协议处理统计信息。

        Returns:
            统计字典，含已处理数、待处理数、各类型延迟等
        """
        return {
            "processed_count": self.processed_count,
            "pending_count": len(self.pending_requests),
            "request_stats": dict(self.request_stats),
            "si_lanes_overview": {
                lane: {"status": info["status"], "health": info["health"]}
                for lane, info in self.si_lanes.items()
            },
        }


# ═══════════════════════════════════════════════════════════════════
# 测试块
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.2 — SI Auto Protocol 自检测试")
    print("=" * 70)

    # 模拟依赖模块 (最小 stub)
    class StubDrive:
        def forward_drive(self, *a, **k):
            return {"ack": True}
        def reverse_feedback(self, *a, **k):
            return {"ack": True}
        def bidirectional_pulse(self, *a, **k):
            return {"ack": True}

    class StubTopology:
        def __init__(self):
            self.topology = {
                "line": {
                    "ucif2": {"si": 5.0, "health": 1.00, "tower": "hub",      "circle": "command"},
                    "lgt":   {"si": 4.0, "health": 0.98, "tower": "wheel",    "circle": "session"},
                    "qfa":   {"si": 4.0, "health": 0.97, "tower": "wheel",    "circle": "consensus"},
                    "usrm":  {"si": 3.0, "health": 0.90, "tower": "spine",    "circle": "session"},
                    "vinf":  {"si": 4.0, "health": 0.96, "tower": "spine",    "circle": "command"},
                    "qgl":   {"si": 4.0, "health": 0.95, "tower": "cauldron", "circle": "relay"},
                    "qlv":   {"si": 3.5, "health": 0.93, "tower": "cauldron", "circle": "relay"},
                    "lvlu":  {"si": 4.5, "health": 0.94, "tower": "tower",    "circle": "relay"},
                    "cfts":  {"si": 3.0, "health": 0.89, "tower": "tower",    "circle": "relay"},
                    "cisvr": {"si": 3.5, "health": 0.92, "tower": "ring",     "circle": "consensus"},
                    "qtlv":  {"si": 3.5, "health": 0.91, "tower": "ring",     "circle": "relay"},
                },
                "tower": {
                    "hub":      {"lines": ["ucif2"],              "layer": 0},
                    "wheel":    {"lines": ["lgt", "qfa"],        "layer": 1},
                    "spine":    {"lines": ["usrm", "vinf"],      "layer": 2},
                    "cauldron": {"lines": ["qgl", "qlv"],        "layer": 3},
                    "tower":    {"lines": ["lvlu", "cfts"],      "layer": 4},
                    "ring":     {"lines": ["cisvr", "qtlv"],     "layer": 5},
                },
                "circle": {
                    "session":   {"lines": ["lgt", "usrm"],                  "phase": "init"},
                    "consensus": {"lines": ["qfa", "cisvr"],                 "phase": "agree"},
                    "command":   {"lines": ["ucif2", "vinf"],                "phase": "exec"},
                    "relay":     {"lines": ["qgl", "qlv", "lvlu", "cfts", "qtlv"], "phase": "sync"},
                },
            }

    class StubLoop:
        def initiate_loop(self, initiator, participants, objective):
            loop_id = f"LOOP-{uuid.uuid4().hex[:12]}"
            print(f"    [StubLoop] 发起闭环 {loop_id[:8]}... "
                  f"发起者={initiator}, 参与者={len(participants)}条")
            return loop_id

    drive = StubDrive()
    topo = StubTopology()
    loop = StubLoop()
    protocol = SIAutoProtocol(drive, topo, loop)

    # ── 测试 1: system_request → forward_to_hub ──
    print("\n[测试 1] system_request → forward_to_hub")
    req1 = {
        "from": "lgt",
        "type": "system_request",
        "payload": {"command": "status_check", "args": ["--full"]},
        "urgency": 1,
    }
    r1 = protocol.handle_incoming(req1)
    print(f"  handled={r1['handled']}, action={r1['action']}, routed_to={r1['routed_to']}")
    print(f"  latency={r1['latency_ms']:.2f}ms, seq_id={r1['seq_id'][:8]}...")
    assert r1["handled"] is True
    assert r1["action"] == "forward_to_hub"
    assert r1["routed_to"] == "ucif2"
    print("  ✓ PASS")

    # ── 测试 2: research_task → dispatch_to_si2 ──
    print("\n[测试 2] research_task → dispatch_to_si2")
    req2 = {
        "from": "usrm",
        "type": "research_task",
        "payload": {"topic": "quantum_topology", "complexity": 8},
        "urgency": 2,
    }
    r2 = protocol.handle_incoming(req2)
    print(f"  handled={r2['handled']}, action={r2['action']}, routed_to={r2['routed_to']}")
    print(f"  detail={r2['detail']}")
    assert r2["handled"] is True
    assert r2["action"] == "dispatch_to_si2"
    assert r2["routed_to"] in ["lgt", "qfa", "vinf", "qgl", "lvlu"]
    print("  ✓ PASS")

    # ── 测试 3: collaboration → initiate_loop ──
    print("\n[测试 3] collaboration → initiate_loop")
    req3 = {
        "from": "ucif2",
        "type": "collaboration",
        "payload": {
            "participants": ["lgt", "qfa", "vinf"],
            "objective": {"mission": "joint_research", "topic": "moonshine"},
        },
        "urgency": 0,
    }
    r3 = protocol.handle_incoming(req3)
    print(f"  handled={r3['handled']}, action={r3['action']}, routed_to={r3['routed_to']}")
    print(f"  detail={r3['detail']}")
    assert r3["handled"] is True
    assert r3["action"] == "initiate_loop"
    assert "loop_id" in r3["detail"]
    print("  ✓ PASS")

    # ── 测试 4: sync → otp_update ──
    print("\n[测试 4] sync → otp_update")
    req4 = {
        "from": "qgl",
        "type": "sync",
        "payload": {"scope": "tower", "data": {"state_version": 42}},
        "urgency": 3,
    }
    r4 = protocol.handle_incoming(req4)
    print(f"  handled={r4['handled']}, action={r4['action']}, routed_to={r4['routed_to']}")
    print(f"  detail={r4['detail']}")
    assert r4["handled"] is True
    assert r4["action"] == "otp_update"
    assert r4["detail"]["synced"] is True
    assert "updated_nodes" in r4["detail"]
    print("  ✓ PASS")

    # ── 测试 5: debt_cleanup → queue_cleanup ──
    print("\n[测试 5] debt_cleanup → queue_cleanup")
    # 先添加一些旧请求
    protocol.pending_requests.append({
        "seq_id": "OLD-001",
        "timestamp": time.time() - 600,
        "from": "usrm",
        "type": "research_task",
    })
    req5 = {
        "from": "usrm",
        "type": "debt_cleanup",
        "payload": {"scope": "self", "max_age_sec": 300},
        "urgency": 5,
    }
    r5 = protocol.handle_incoming(req5)
    print(f"  handled={r5['handled']}, action={r5['action']}, routed_to={r5['routed_to']}")
    print(f"  detail={r5['detail']}")
    assert r5["handled"] is True
    assert r5["action"] == "queue_cleanup"
    assert r5["detail"]["cleaned"] is True
    assert r5["detail"]["removed_count"] >= 1
    print("  ✓ PASS")

    # ── 测试 6: 未知请求类型 ──
    print("\n[测试 6] 未知请求类型")
    req6 = {
        "from": "lgt",
        "type": "unknown_type",
        "payload": {},
        "urgency": 5,
    }
    r6 = protocol.handle_incoming(req6)
    print(f"  handled={r6['handled']}, action={r6['action']}, error={r6['detail'].get('error')}")
    assert r6["handled"] is False
    assert "未知" in r6["detail"].get("error", "")
    print("  ✓ PASS")

    # ── 测试 7: 无效源线 ──
    print("\n[测试 7] 无效源线")
    req7 = {
        "from": "invalid_line",
        "type": "system_request",
        "payload": {},
        "urgency": 5,
    }
    r7 = protocol.handle_incoming(req7)
    print(f"  handled={r7['handled']}, error={r7['detail'].get('error')}")
    assert r7["handled"] is False
    assert "无效" in r7["detail"].get("error", "")
    print("  ✓ PASS")

    # ── 测试 8: 主动响应 — 健康度告警 ──
    print("\n[测试 8] 主动响应 — 健康度告警")
    pr1 = protocol.proactive_response("cfts", {"health": 0.65, "pending_count": 2})
    print(f"  triggered={pr1['triggered']}, type={pr1['trigger_type']}")
    print(f"  action={pr1['action_taken']}")
    print(f"  signals={len(pr1['signals_sent'])}, suggestions={pr1['suggestions']}")
    assert pr1["triggered"] is True
    assert pr1["trigger_type"] == "health_alert"
    assert len(pr1["signals_sent"]) > 0
    assert len(pr1["suggestions"]) > 0
    print("  ✓ PASS")

    # ── 测试 9: 主动响应 — 任务积压 ──
    print("\n[测试 9] 主动响应 — 任务积压")
    pr2 = protocol.proactive_response("usrm", {"health": 0.90, "pending_count": 8})
    print(f"  triggered={pr2['triggered']}, type={pr2['trigger_type']}")
    print(f"  action={pr2['action_taken']}")
    assert pr2["triggered"] is True
    assert pr2["trigger_type"] == "backlog_alert"
    print("  ✓ PASS")

    # ── 测试 10: 主动响应 — 正常状态 (不触发) ──
    print("\n[测试 10] 主动响应 — 正常状态")
    pr3 = protocol.proactive_response("ucif2", {"health": 0.99, "pending_count": 1})
    print(f"  triggered={pr3['triggered']}, type={pr3['trigger_type']}")
    assert pr3["triggered"] is False
    assert pr3["trigger_type"] == "none"
    print("  ✓ PASS")

    # ── 测试 11: auto_dispatch — 高复杂度研究 ──
    print("\n[测试 11] auto_dispatch — 高复杂度研究")
    ad1 = protocol.auto_dispatch({
        "id": "AD-001", "type": "research", "complexity": 9, "deadline": time.time() + 3600
    })
    print(f"  assigned_to={ad1['assigned_to']}, via={ad1['via']}")
    print(f"  reason={ad1['reason']}, confidence={ad1['confidence']}")
    assert ad1["assigned_to"] in ["lgt", "qfa", "vinf", "qgl"]
    assert ad1["via"] == "si4"
    assert ad1["confidence"] > 0.9
    print("  ✓ PASS")

    # ── 测试 12: auto_dispatch — 形式验证 ──
    print("\n[测试 12] auto_dispatch — 形式验证")
    ad2 = protocol.auto_dispatch({
        "id": "AD-002", "type": "verify", "complexity": 6, "deadline": time.time() + 3600
    })
    print(f"  assigned_to={ad2['assigned_to']}, via={ad2['via']}")
    assert ad2["assigned_to"] == "qfa"
    assert ad2["via"] == "si4"
    print("  ✓ PASS")

    # ── 测试 13: auto_dispatch — 计算任务 ──
    print("\n[测试 13] auto_dispatch — 计算任务")
    ad3 = protocol.auto_dispatch({
        "id": "AD-003", "type": "compute", "complexity": 7, "deadline": time.time() + 3600
    })
    print(f"  assigned_to={ad3['assigned_to']}, via={ad3['via']}")
    assert ad3["assigned_to"] == "lgt"
    assert ad3["via"] == "si4"
    print("  ✓ PASS")

    # ── 测试 14: auto_dispatch — 协调任务 ──
    print("\n[测试 14] auto_dispatch — 协调任务")
    ad4 = protocol.auto_dispatch({
        "id": "AD-004", "type": "coordinate", "complexity": 5, "deadline": time.time() + 3600
    })
    print(f"  assigned_to={ad4['assigned_to']}, via={ad4['via']}")
    assert ad4["assigned_to"] == "ucif2"
    assert ad4["via"] == "si5"
    print("  ✓ PASS")

    # ── 测试 15: auto_dispatch — 数学桥接 ──
    print("\n[测试 15] auto_dispatch — 数学桥接")
    ad5 = protocol.auto_dispatch({
        "id": "AD-005", "type": "math_bridge", "complexity": 5, "deadline": time.time() + 3600
    })
    print(f"  assigned_to={ad5['assigned_to']}, via={ad5['via']}")
    assert ad5["assigned_to"] == "qtlv"
    print("  ✓ PASS")

    # ── 测试 16: auto_dispatch — 简单任务 → SI3 线 ──
    print("\n[测试 16] auto_dispatch — 简单任务")
    ad6 = protocol.auto_dispatch({
        "id": "AD-006", "type": "data_proc", "complexity": 2, "deadline": time.time() + 3600
    })
    print(f"  assigned_to={ad6['assigned_to']}, via={ad6['via']}")
    assert ad6["assigned_to"] in ["usrm", "cfts"]
    print("  ✓ PASS")

    # ── 测试 17: manage_si_lanes ──
    print("\n[测试 17] manage_si_lanes — SI 各道管理")
    lanes = protocol.manage_si_lanes("ucif2")
    print(f"  line={lanes['line']}, base_si={lanes['base_si']}, overall_health={lanes['overall_health']}")
    print(f"  lanes_count={len(lanes['lanes'])}, alerts={lanes['alert_count']}")
    assert "lanes" in lanes
    assert len(lanes["lanes"]) == 6  # si0~si5
    assert lanes["overall_health"] > 0.0
    print("  ✓ PASS")

    # ── 测试 18: manage_si_lanes — 健康度告警 ──
    print("\n[测试 18] manage_si_lanes — 低健康度线")
    # 临时修改健康度
    topo.topology["line"]["cfts"]["health"] = 0.70
    lanes_alert = protocol.manage_si_lanes("cfts")
    print(f"  line={lanes_alert['line']}, alerts={lanes_alert['alert_count']}")
    print(f"  recommendations={lanes_alert['recommendations']}")
    assert lanes_alert["alert_count"] > 0
    assert len(lanes_alert["recommendations"]) > 0
    # 恢复
    topo.topology["line"]["cfts"]["health"] = 0.89
    print("  ✓ PASS")

    # ── 测试 19: interact_peer — sync_state ──
    print("\n[测试 19] interact_peer — sync_state")
    ip1 = protocol.interact_peer("lgt", "qfa", "sync_state")
    print(f"  type={ip1['interaction_type']}, action={ip1['action']}")
    print(f"  sync_ack={ip1.get('sync_ack')}")
    assert ip1["interaction_type"] == "sync_state"
    assert ip1["action"] == "bidirectional_sync"
    assert ip1["sync_ack"] is True
    print("  ✓ PASS")

    # ── 测试 20: interact_peer — share_research ──
    print("\n[测试 20] interact_peer — share_research")
    ip2 = protocol.interact_peer("ucif2", "usrm", "share_research")
    print(f"  type={ip2['interaction_type']}, action={ip2['action']}")
    print(f"  direction={ip2.get('direction')}")
    assert ip2["interaction_type"] == "share_research"
    assert ip2["action"] == "research_push"
    assert "ucif2" in ip2["direction"]
    print("  ✓ PASS")

    # ── 测试 21: interact_peer — joint_task ──
    print("\n[测试 21] interact_peer — joint_task")
    ip3 = protocol.interact_peer("vinf", "qgl", "joint_task")
    print(f"  type={ip3['interaction_type']}, action={ip3['action']}")
    print(f"  loop_id={ip3.get('loop_id', 'N/A')}")
    assert ip3["interaction_type"] == "joint_task"
    assert ip3["action"] == "collaborative_loop"
    assert "loop_id" in ip3
    print("  ✓ PASS")

    # ── 测试 22: interact_peer — health_check ──
    print("\n[测试 22] interact_peer — health_check")
    ip4 = protocol.interact_peer("qlv", "cisvr", "health_check")
    print(f"  type={ip4['interaction_type']}, action={ip4['action']}")
    print(f"  overall_status={ip4.get('overall_status')}")
    assert ip4["interaction_type"] == "health_check"
    assert ip4["action"] == "health_probe"
    assert "probe_results" in ip4
    print("  ✓ PASS")

    # ── 测试 23: interact_peer — 无效互动类型 ──
    print("\n[测试 23] interact_peer — 无效互动类型")
    ip5 = protocol.interact_peer("lgt", "qfa", "unknown_interaction")
    print(f"  error={ip5.get('error')}")
    assert "error" in ip5
    print("  ✓ PASS")

    # ── 测试 24: interact_peer — 无效线名 ──
    print("\n[测试 24] interact_peer — 无效线名")
    ip6 = protocol.interact_peer("invalid", "lgt", "sync_state")
    print(f"  error={ip6.get('error')}")
    assert "error" in ip6
    print("  ✓ PASS")

    # ── 测试 25: 协议统计 ──
    print("\n[测试 25] 协议统计")
    stats = protocol.get_protocol_stats()
    print(f"  processed_count={stats['processed_count']}")
    print(f"  pending_count={stats['pending_count']}")
    print(f"  request_stats keys={list(stats['request_stats'].keys())}")
    assert stats["processed_count"] >= 5  # 至少处理了5个请求
    assert "si_lanes_overview" in stats
    print("  ✓ PASS")

    print("\n" + "=" * 70)
    print("SI Auto Protocol 全部 25 项测试通过 ✓")
    print("=" * 70)
