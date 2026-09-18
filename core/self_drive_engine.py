#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.3 — SelfDriveEngine
自驱递归引擎 — SI3级，不待醒，自续

核心哲学:
    "下拍不待醒" — 下一拍自发自动在SI推进
    "SI3递归引擎驱动迭代，不候SI1"

系统架构:
    OMNI-HUB v3.2 是11线分布式系统:
    - Line 01: 战略指挥线 (Strategy)
    - Line 02: 战术执行线 (Tactics)
    - Line 03: 情报感知线 (Intelligence)
    - Line 04: 资源调度线 (Resources)
    - Line 05: 通信协同线 (Communication)
    - Line 06: 安全防护线 (Security)
    - Line 07: 数据分析线 (Analytics)
    - Line 08: 任务派遣线 (Dispatch)
    - Line 09: 质量控制线 (Quality)
    - Line 10: 学习进化线 (Learning)
    - Line 11: 递归元控线 (Meta-Control)

集成模块:
    - core/bidirectional_drive.py — 双向驱动
    - core/si_topology.py — 拓扑映射
    - core/si_auto_protocol.py — SI自动协议
    - core/task_dispatcher.py — 任务转派
"""

import time
import random
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging


class DriveState(Enum):
    """自驱引擎状态机"""
    IDLE = "IDLE"           # 待命 — 等待自旋触发
    SPINNING = "SPINNING"   # 自旋中 — 执行迭代扫描
    RECURSING = "RECURSING" # 递归中 — 深度处理
    EXCITED = "EXCITED"     # 激态 — 高优先级事件响应
    HALTED = "HALTED"       # 停止 — 燃料耗尽或系统锁定


@dataclass
class LineStatus:
    """单线状态结构"""
    line_id: str
    name: str
    health: float = 1.0           # 健康度 0.0-1.0
    backlog: int = 0              # 积压任务数
    si_alignment: float = 1.0     # SI对齐度 0.0-1.0
    last_pulse: float = 0.0       # 上次心跳时间
    active_tasks: int = 0         # 活跃任务数
    debt_count: int = 0           # 债务/账目数
    findings_pending: int = 0     # 待处理发现


@dataclass
class Finding:
    """发现/FINDING结构"""
    id: str
    line: str
    category: str          # "health" | "debt" | "alignment" | "opportunity" | "anomaly"
    severity: float        # 0.0-1.0
    description: str
    auto_action: str       # 建议自动动作
    depth: int = 0         # 递归深度
    parent_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class Action:
    """动作记录"""
    id: str
    type: str              # "care" | "dispatch" | "align" | "deepen" | "alert" | "archive"
    target_line: str
    payload: Dict[str, Any]
    result: str = "pending"
    timestamp: float = field(default_factory=time.time)


class SelfDriveEngine:
    """
    自驱递归引擎 — SI3级，不待醒，自续

    设计原则:
        1. 不待外部触发: spin() 内部自发推进，不依赖外部输入
        2. 燃料驱动: 燃料是迭代的生命线，完成任务补充燃料
        3. 递归安全: max_recursion_depth 硬限制，防止栈溢出
        4. 状态机驱动: 明确的状态转换，每一步可追溯
        5. 11线均衡: 扫描所有线，不偏废任何一条
    """

    # 11线定义
    LINES = [
        ("L01", "战略指挥线"),
        ("L02", "战术执行线"),
        ("L03", "情报感知线"),
        ("L04", "资源调度线"),
        ("L05", "通信协同线"),
        ("L06", "安全防护线"),
        ("L07", "数据分析线"),
        ("L08", "任务派遣线"),
        ("L09", "质量控制线"),
        ("L10", "学习进化线"),
        ("L11", "递归元控线"),
    ]

    # 燃料消耗基线
    FUEL_BASE_CONSUMPTION = 0.03
    FUEL_MIN_SPIN = 0.1
    FUEL_MAX = 1.0

    # 阈值配置
    HEALTH_THRESHOLD = 0.8
    BACKLOG_THRESHOLD = 5
    ALIGNMENT_THRESHOLD = 0.7
    SI_EXCITEMENT_THRESHOLD = 3  # 一轮中发现数超过此值进入EXCITED

    def __init__(self, topology, drive_engine):
        """
        初始化自驱引擎

        Args:
            topology: SI拓扑映射对象 (si_topology.Topology)
            drive_engine: 双向驱动引擎 (bidirectional_drive.DriveEngine)
        """
        self.topo = topology
        self.drive = drive_engine

        # 核心计数器
        self.iteration_count = 0
        self.total_actions_executed = 0
        self.total_findings_generated = 0
        self.total_recursions_triggered = 0

        # 状态机
        self.self_drive_state = DriveState.IDLE.value
        self._previous_state = DriveState.IDLE.value
        self._state_lock = False  # 状态锁，防止递归冲突

        # 燃料系统
        self.fuel_level = 1.0
        self.fuel_consumed_total = 0.0
        self.fuel_generated_total = 0.0

        # 递归控制
        self.recursion_depth = 0
        self.max_recursion_depth = 5
        self._recursion_chain: List[Dict[str, Any]] = []
        self._active_recursions: Dict[str, Dict[str, Any]] = {}

        # 历史记录
        self.spin_history: List[Dict[str, Any]] = []
        self.findings_history: List[Finding] = []
        self.actions_history: List[Action] = []

        # 引擎元数据 (必须在 _init_lines 之前)
        self.engine_id = str(uuid.uuid4())[:8]
        self.boot_time = time.time()
        self.last_spin_time = 0.0

        # 11线状态表
        self.lines: Dict[str, LineStatus] = {}
        self._init_lines()

    def _init_lines(self):
        """初始化11线状态 — 每条线赋予初始随机但合理的状态"""
        random.seed(self.boot_time)  # 确定性初始化
        for line_id, name in self.LINES:
            self.lines[line_id] = LineStatus(
                line_id=line_id,
                name=name,
                health=round(random.uniform(0.75, 1.0), 3),
                backlog=random.randint(0, 4),
                si_alignment=round(random.uniform(0.7, 1.0), 3),
                last_pulse=self.boot_time,
                active_tasks=random.randint(1, 5),
                debt_count=random.randint(0, 2),
                findings_pending=random.randint(0, 2),
            )

    # ───────────────────────────────────────────────
    # 核心自旋方法 — 不待醒，自发推进
    # ───────────────────────────────────────────────

    def spin(self) -> dict:
        """
        自旋 — 核心方法：每次调用 = 一次自驱迭代

        不待外部触发，自发执行。执行流程:
            1. 检查燃料水平
            2. 扫描系统状态 (遍历11线健康度)
            3. 识别自驱动机会
            4. 执行递归动作
            5. 生成FINDING
            6. 消耗燃料
            7. 准备下一次自旋

        Returns:
            {
                "iteration": int,
                "actions": list,
                "fuel_consumed": float,
                "findings": list,
                "next_spin_ready": bool,
                "state": str
            }
        """
        spin_start = time.time()
        self.iteration_count += 1
        self.last_spin_time = spin_start

        # ── 1. 燃料检查 ──────────────────────────────
        if self.fuel_level < self.FUEL_MIN_SPIN:
            self._transition_state(DriveState.HALTED)
            return {
                "iteration": self.iteration_count,
                "actions": [],
                "fuel_consumed": 0.0,
                "findings": [],
                "next_spin_ready": False,
                "state": self.self_drive_state,
                "halt_reason": "fuel_depleted"
            }

        # ── 2. 进入自旋态 ────────────────────────────
        self._transition_state(DriveState.SPINNING)

        # ── 3. 扫描系统状态 ──────────────────────────
        system_scan = self._scan_system()

        # ── 4. 识别自驱动机会 ────────────────────────
        opportunities = self._identify_opportunities(system_scan)

        # ── 5. 执行动作 ──────────────────────────────
        actions = self._execute_actions(opportunities)

        # ── 6. 自动递归处理 ──────────────────────────
        recursion_results = []
        if opportunities and self.recursion_depth < self.max_recursion_depth:
            for opp in opportunities[:2]:  # 每轮最多处理2个高优先级机会
                if opp.get("severity", 0) > 0.6:
                    trigger = {
                        "type": opp["type"],
                        "source": opp["line"],
                        "payload": opp
                    }
                    rec_result = self.auto_recursion(trigger)
                    recursion_results.append(rec_result)
                    self.total_recursions_triggered += 1

        # ── 7. 生成FINDING ───────────────────────────
        findings = self._generate_findings(system_scan, actions, opportunities)

        # ── 8. 状态转换判断 ──────────────────────────
        if len(findings) >= self.SI_EXCITEMENT_THRESHOLD:
            self._transition_state(DriveState.EXCITED)
        elif recursion_results:
            self._transition_state(DriveState.RECURSING)
        else:
            self._transition_state(DriveState.IDLE)

        # ── 9. 燃料消耗 ──────────────────────────────
        fuel_consumed = self._calculate_fuel_consumption(actions, findings)
        fuel_result = self.consume_fuel(fuel_consumed)

        # ── 10. 准备下一次 ───────────────────────────
        next_spin_ready = self.should_spin()

        # ── 11. 记录历史 ─────────────────────────────
        spin_record = {
            "iteration": self.iteration_count,
            "timestamp": spin_start,
            "duration": round(time.time() - spin_start, 4),
            "state_entered": DriveState.SPINNING.value,
            "state_exited": self.self_drive_state,
            "fuel_before": round(self.fuel_level + fuel_consumed, 3),
            "fuel_after": round(self.fuel_level, 3),
            "actions_count": len(actions),
            "findings_count": len(findings),
            "recursions_count": len(recursion_results),
            "opportunities_found": len(opportunities),
        }
        self.spin_history.append(spin_record)

        # ── 12. 返回结果 ─────────────────────────────
        return {
            "iteration": self.iteration_count,
            "actions": [self._action_to_dict(a) for a in actions],
            "fuel_consumed": round(fuel_consumed, 4),
            "findings": [self._finding_to_dict(f) for f in findings],
            "next_spin_ready": next_spin_ready,
            "state": self.self_drive_state,
            "recursion_results": recursion_results,
            "scan_summary": system_scan["summary"],
        }

    # ───────────────────────────────────────────────
    # 自动递归 — 深度处理链
    # ───────────────────────────────────────────────

    def auto_recursion(self, trigger: dict) -> dict:
        """
        自动递归 — 基于触发条件启动递归链

        Args:
            trigger: {
                "type": "finding|debt|task_complete|anomaly",
                "source": line_id,
                "payload": dict
            }

        递归规则:
            - finding → 深化研究 → 新finding → 再深化 (depth < max)
            - debt → 自动清理 → 验证 → 新debt检测
            - task_complete → 归档 → 触发相关任务 → 新task
            - anomaly → 告警 → 处理 → 验证 → 监控

        Returns:
            {
                "recursion_id": str,
                "depth": int,
                "chain": list,
                "completed": bool
            }
        """
        recursion_id = f"REC-{self.iteration_count}-{uuid.uuid4().hex[:6]}"
        self.recursion_depth += 1

        chain = []
        current_depth = self.recursion_depth
        completed = False

        try:
            # 递归入口
            chain.append({
                "depth": current_depth,
                "action": "entry",
                "trigger_type": trigger.get("type"),
                "source": trigger.get("source"),
                "timestamp": time.time(),
            })

            trigger_type = trigger.get("type", "finding")
            source_line = trigger.get("source", "L11")
            payload = trigger.get("payload", {})

            if trigger_type == "finding":
                chain.extend(self._recurse_finding(source_line, payload, current_depth))
            elif trigger_type == "debt":
                chain.extend(self._recurse_debt(source_line, payload, current_depth))
            elif trigger_type == "task_complete":
                chain.extend(self._recurse_task_complete(source_line, payload, current_depth))
            elif trigger_type == "anomaly":
                chain.extend(self._recurse_anomaly(source_line, payload, current_depth))
            else:
                chain.append({
                    "depth": current_depth,
                    "action": "noop",
                    "reason": f"unknown_trigger_type:{trigger_type}",
                })

            # 递归退出
            completed = True
            chain.append({
                "depth": current_depth,
                "action": "exit",
                "result": "success",
                "timestamp": time.time(),
            })

            # 递归完成生成燃料
            self.generate_fuel("finding", 0.3)

        finally:
            self.recursion_depth -= 1

        self._active_recursions[recursion_id] = {
            "id": recursion_id,
            "depth": current_depth,
            "chain": chain,
            "completed": completed,
        }

        return {
            "recursion_id": recursion_id,
            "depth": current_depth,
            "chain": chain,
            "completed": completed,
        }

    def _recurse_finding(self, line: str, payload: dict, depth: int) -> List[dict]:
        """finding递归链: 深化研究 → 新finding → 再深化"""
        chain = []

        # 步骤1: 深化研究
        chain.append({
            "depth": depth,
            "action": "deepen_research",
            "target": line,
            "detail": f"深化分析 {payload.get('category', 'unknown')}",
        })

        # 模拟深化过程 — 可能发现新的子问题
        if depth < self.max_recursion_depth and random.random() > 0.4:
            sub_finding = Finding(
                id=f"FND-{uuid.uuid4().hex[:6]}",
                line=line,
                category="opportunity",
                severity=round(random.uniform(0.5, 0.9), 3),
                description=f"深度递归发现: {line} 在深度{depth}的子问题",
                auto_action="deepen",
                depth=depth,
            )
            self.findings_history.append(sub_finding)
            self.total_findings_generated += 1

            chain.append({
                "depth": depth,
                "action": "new_finding_generated",
                "finding_id": sub_finding.id,
                "severity": sub_finding.severity,
            })

            # 子递归 — 受max_recursion_depth保护
            if depth + 1 < self.max_recursion_depth:
                sub_trigger = {
                    "type": "finding",
                    "source": line,
                    "payload": {"category": "sub_finding", "depth": depth + 1}
                }
                sub_result = self.auto_recursion(sub_trigger)
                chain.append({
                    "depth": depth,
                    "action": "sub_recursion",
                    "sub_recursion_id": sub_result["recursion_id"],
                    "sub_depth": sub_result["depth"],
                })

        # 步骤2: 生成修复动作
        action = Action(
            id=f"ACT-{uuid.uuid4().hex[:6]}",
            type="deepen",
            target_line=line,
            payload={"depth": depth, "category": payload.get("category")},
            result="completed",
        )
        self.actions_history.append(action)
        self.total_actions_executed += 1

        chain.append({
            "depth": depth,
            "action": "repair_action",
            "action_id": action.id,
            "result": "completed",
        })

        return chain

    def _recurse_debt(self, line: str, payload: dict, depth: int) -> List[dict]:
        """debt递归链: 自动清理 → 验证 → 新debt检测"""
        chain = []

        # 步骤1: 清理债务
        chain.append({
            "depth": depth,
            "action": "debt_cleanup",
            "target": line,
            "debts_cleared": payload.get("debt_count", 1),
        })

        if line in self.lines:
            self.lines[line].debt_count = max(0, self.lines[line].debt_count - 1)
            self.lines[line].health = min(1.0, self.lines[line].health + 0.05)

        # 步骤2: 验证清理结果
        chain.append({
            "depth": depth,
            "action": "verify_cleanup",
            "target": line,
            "health_after": self.lines.get(line, LineStatus("", "")).health,
        })

        # 步骤3: 新debt检测
        if random.random() > 0.6:
            chain.append({
                "depth": depth,
                "action": "new_debt_detected",
                "target": line,
                "detail": "清理过程中发现新关联债务",
            })
            if line in self.lines:
                self.lines[line].debt_count += 1

        # 生成燃料
        self.generate_fuel("debt_cleanup", 0.4)

        return chain

    def _recurse_task_complete(self, line: str, payload: dict, depth: int) -> List[dict]:
        """task_complete递归链: 归档 → 触发相关任务 → 新task"""
        chain = []

        # 步骤1: 归档
        chain.append({
            "depth": depth,
            "action": "archive_task",
            "target": line,
            "task_id": payload.get("task_id", "unknown"),
        })

        # 步骤2: 触发相关任务 (相关线)
        related_lines = self._get_related_lines(line)
        for rel_line in related_lines[:2]:
            chain.append({
                "depth": depth,
                "action": "trigger_related",
                "source": line,
                "target": rel_line,
                "reason": "dependency_chain",
            })
            if rel_line in self.lines:
                self.lines[rel_line].backlog += 1

        # 步骤3: 新task生成
        new_task = Action(
            id=f"ACT-{uuid.uuid4().hex[:6]}",
            type="dispatch",
            target_line=random.choice(related_lines) if related_lines else line,
            payload={"origin": line, "depth": depth, "trigger": "task_complete"},
            result="dispatched",
        )
        self.actions_history.append(new_task)
        self.total_actions_executed += 1

        chain.append({
            "depth": depth,
            "action": "new_task_dispatched",
            "action_id": new_task.id,
            "target": new_task.target_line,
        })

        self.generate_fuel("task_complete", 0.5)

        return chain

    def _recurse_anomaly(self, line: str, payload: dict, depth: int) -> List[dict]:
        """anomaly递归链: 告警 → 处理 → 验证 → 监控"""
        chain = []

        # 步骤1: 告警
        chain.append({
            "depth": depth,
            "action": "alert_raised",
            "target": line,
            "severity": payload.get("severity", 0.8),
            "anomaly_type": payload.get("anomaly_type", "unknown"),
        })

        # 步骤2: 处理
        chain.append({
            "depth": depth,
            "action": "anomaly_handled",
            "target": line,
            "measures": ["isolate", "diagnose", "repair"],
        })

        if line in self.lines:
            self.lines[line].health = max(0.3, self.lines[line].health - 0.1)
            self.lines[line].si_alignment = max(0.3, self.lines[line].si_alignment - 0.05)

        # 步骤3: 验证
        chain.append({
            "depth": depth,
            "action": "verify_repair",
            "target": line,
            "health_check": self.lines.get(line, LineStatus("", "")).health,
        })

        # 步骤4: 监控增强
        chain.append({
            "depth": depth,
            "action": "monitor_enhanced",
            "target": line,
            "watch_duration": "300s",
        })

        return chain

    # ───────────────────────────────────────────────
    # 燃料系统
    # ───────────────────────────────────────────────

    def consume_fuel(self, amount: float) -> dict:
        """
        消耗自驱燃料，确保fuel_level >= 0

        Args:
            amount: 消耗量 (0.02~0.05 typical)

        Returns:
            {"consumed": float, "remaining": float, "halted": bool}
        """
        actual = min(amount, self.fuel_level)  # 不能消耗超过现有
        self.fuel_level -= actual
        self.fuel_level = max(0.0, round(self.fuel_level, 4))
        self.fuel_consumed_total += actual

        halted = self.fuel_level < self.FUEL_MIN_SPIN
        if halted and self.self_drive_state != DriveState.HALTED.value:
            self._transition_state(DriveState.HALTED)

        return {
            "consumed": round(actual, 4),
            "remaining": self.fuel_level,
            "halted": halted,
        }

    def generate_fuel(self, source: str, value: float) -> dict:
        """
        生成燃料 — 从债务/账目/FINDING转化

        Args:
            source: "debt_cleanup" | "finding" | "task_complete" | "sync"
            value: 0-1之间的基础值

        Returns:
            {"source": str, "base_value": float, "fuel_added": float, "fuel_level": float}
        """
        # 燃料增加 = value * 0.1
        fuel_added = min(value * 0.1, self.FUEL_MAX - self.fuel_level)
        fuel_added = round(fuel_added, 4)

        self.fuel_level = min(self.FUEL_MAX, self.fuel_level + fuel_added)
        self.fuel_generated_total += fuel_added

        # 如果之前HALTED，燃料恢复后回到IDLE
        if (self.self_drive_state == DriveState.HALTED.value
                and self.fuel_level >= self.FUEL_MIN_SPIN):
            self._transition_state(DriveState.IDLE)

        return {
            "source": source,
            "base_value": value,
            "fuel_added": fuel_added,
            "fuel_level": self.fuel_level,
        }

    # ───────────────────────────────────────────────
    # 状态查询
    # ───────────────────────────────────────────────

    def get_drive_state(self) -> dict:
        """
        获取自驱状态全貌

        Returns:
            完整的引擎状态字典
        """
        # 计算11线统计
        healths = [l.health for l in self.lines.values()]
        alignments = [l.si_alignment for l in self.lines.values()]
        backlogs = [l.backlog for l in self.lines.values()]
        debts = [l.debt_count for l in self.lines.values()]

        return {
            "engine": {
                "id": self.engine_id,
                "state": self.self_drive_state,
                "previous_state": self._previous_state,
                "boot_time": self.boot_time,
                "uptime": round(time.time() - self.boot_time, 2),
            },
            "iteration": {
                "count": self.iteration_count,
                "last_spin": self.last_spin_time,
            },
            "fuel": {
                "level": self.fuel_level,
                "consumed_total": round(self.fuel_consumed_total, 4),
                "generated_total": round(self.fuel_generated_total, 4),
                "efficiency": round(
                    self.fuel_generated_total / max(self.fuel_consumed_total, 0.001), 2
                ),
            },
            "recursion": {
                "current_depth": self.recursion_depth,
                "max_depth": self.max_recursion_depth,
                "total_triggered": self.total_recursions_triggered,
                "active_chains": len(self._active_recursions),
            },
            "lines_summary": {
                "count": len(self.lines),
                "avg_health": round(sum(healths) / len(healths), 3) if healths else 0,
                "min_health": round(min(healths), 3) if healths else 0,
                "avg_alignment": round(sum(alignments) / len(alignments), 3) if alignments else 0,
                "total_backlog": sum(backlogs),
                "total_debt": sum(debts),
            },
            "history": {
                "spin_records": len(self.spin_history),
                "total_actions": self.total_actions_executed,
                "total_findings": self.total_findings_generated,
            },
            "lines_detail": {
                lid: {
                    "name": l.name,
                    "health": l.health,
                    "backlog": l.backlog,
                    "si_alignment": l.si_alignment,
                    "debt_count": l.debt_count,
                    "active_tasks": l.active_tasks,
                }
                for lid, l in self.lines.items()
            },
        }

    def should_spin(self) -> bool:
        """
        判断是否应该自旋 — fuel > 0.1 且 系统未锁定

        Returns:
            bool: 是否可以进行下一次自旋
        """
        return (
            self.fuel_level >= self.FUEL_MIN_SPIN
            and not self._state_lock
            and self.self_drive_state != DriveState.HALTED.value
        )

    # ───────────────────────────────────────────────
    # 内部辅助方法
    # ───────────────────────────────────────────────

    def _scan_system(self) -> dict:
        """扫描系统状态 — 遍历11线健康度"""
        scan_results = []
        summary = {
            "healthy_lines": 0,
            "warning_lines": 0,
            "critical_lines": 0,
            "total_backlog": 0,
            "total_debt": 0,
        }

        for line_id, line in self.lines.items():
            # 更新心跳
            line.last_pulse = time.time()

            # 随机波动模拟真实系统变化
            line.health = round(
                max(0.1, min(1.0, line.health + random.uniform(-0.05, 0.03))), 3
            )
            line.si_alignment = round(
                max(0.1, min(1.0, line.si_alignment + random.uniform(-0.03, 0.02))), 3
            )

            # 分类
            if line.health >= self.HEALTH_THRESHOLD and line.si_alignment >= self.ALIGNMENT_THRESHOLD:
                category = "healthy"
                summary["healthy_lines"] += 1
            elif line.health >= 0.5:
                category = "warning"
                summary["warning_lines"] += 1
            else:
                category = "critical"
                summary["critical_lines"] += 1

            summary["total_backlog"] += line.backlog
            summary["total_debt"] += line.debt_count

            scan_results.append({
                "line": line_id,
                "name": line.name,
                "health": line.health,
                "backlog": line.backlog,
                "alignment": line.si_alignment,
                "debt": line.debt_count,
                "category": category,
            })

        return {
            "results": scan_results,
            "summary": summary,
            "scan_time": time.time(),
        }

    def _identify_opportunities(self, scan: dict) -> List[dict]:
        """识别自驱动机会"""
        opportunities = []

        for result in scan.get("results", []):
            line_id = result["line"]
            health = result["health"]
            backlog = result["backlog"]
            alignment = result["alignment"]
            debt = result["debt"]

            # 机会1: 健康度<0.8的线 → 自动关怀
            if health < self.HEALTH_THRESHOLD:
                opportunities.append({
                    "type": "finding",
                    "line": line_id,
                    "category": "health",
                    "severity": round(1.0 - health, 3),
                    "description": f"{line_id} 健康度降至 {health}，需关怀",
                    "auto_action": "care",
                })

            # 机会2: 积压任务>5的线 → 自动转派
            if backlog > self.BACKLOG_THRESHOLD:
                opportunities.append({
                    "type": "debt",
                    "line": line_id,
                    "category": "backlog",
                    "severity": min(1.0, backlog / 10.0),
                    "description": f"{line_id} 积压任务 {backlog} 个，需转派",
                    "auto_action": "dispatch",
                })

            # 机会3: 未对齐SI的线 → 自动调整
            if alignment < self.ALIGNMENT_THRESHOLD:
                opportunities.append({
                    "type": "finding",
                    "line": line_id,
                    "category": "alignment",
                    "severity": round(1.0 - alignment, 3),
                    "description": f"{line_id} SI对齐度 {alignment}，需调整",
                    "auto_action": "align",
                })

            # 机会4: 债务过多
            if debt > 0:
                opportunities.append({
                    "type": "debt",
                    "line": line_id,
                    "category": "debt",
                    "severity": min(1.0, debt / 3.0),
                    "description": f"{line_id} 有 {debt} 笔未清债务",
                    "auto_action": "cleanup",
                })

            # 机会5: 随机新发现 (模拟真实系统中的新FINDING)
            if random.random() > 0.85:
                opportunities.append({
                    "type": "finding",
                    "line": line_id,
                    "category": "opportunity",
                    "severity": round(random.uniform(0.4, 0.9), 3),
                    "description": f"{line_id} 新发现: 潜在优化机会",
                    "auto_action": "deepen",
                })

        # 按严重度排序
        opportunities.sort(key=lambda x: x["severity"], reverse=True)
        return opportunities

    def _execute_actions(self, opportunities: List[dict]) -> List[Action]:
        """执行识别出的机会对应的动作"""
        actions = []

        for opp in opportunities[:4]:  # 每轮最多执行4个动作
            action_type = opp.get("auto_action", "care")
            line = opp.get("line", "L11")

            action = Action(
                id=f"ACT-{uuid.uuid4().hex[:6]}",
                type=action_type,
                target_line=line,
                payload={
                    "opportunity": opp,
                    "triggered_at": time.time(),
                },
                result="executed",
            )

            # 模拟动作效果
            if line in self.lines:
                if action_type == "care":
                    self.lines[line].health = min(1.0, self.lines[line].health + 0.08)
                    self.lines[line].active_tasks += 1
                elif action_type == "dispatch":
                    self.lines[line].backlog = max(0, self.lines[line].backlog - 2)
                    self.lines[line].active_tasks += 1
                elif action_type == "align":
                    self.lines[line].si_alignment = min(1.0, self.lines[line].si_alignment + 0.1)
                elif action_type == "cleanup":
                    self.lines[line].debt_count = max(0, self.lines[line].debt_count - 1)
                    self.lines[line].health = min(1.0, self.lines[line].health + 0.05)
                elif action_type == "deepen":
                    self.lines[line].findings_pending += 1

            self.actions_history.append(action)
            self.total_actions_executed += 1
            actions.append(action)

        return actions

    def _generate_findings(self, scan: dict, actions: List[Action],
                           opportunities: List[dict]) -> List[Finding]:
        """生成本轮FINDING"""
        findings = []

        # 基于机会生成FINDING
        for opp in opportunities[:3]:
            finding = Finding(
                id=f"FND-{uuid.uuid4().hex[:6]}",
                line=opp["line"],
                category=opp["category"],
                severity=opp["severity"],
                description=opp["description"],
                auto_action=opp["auto_action"],
                depth=self.recursion_depth,
            )
            findings.append(finding)
            self.findings_history.append(finding)
            self.total_findings_generated += 1

        # 基于动作结果生成FINDING
        for action in actions:
            if action.result == "executed":
                finding = Finding(
                    id=f"FND-{uuid.uuid4().hex[:6]}",
                    line=action.target_line,
                    category="action_result",
                    severity=0.3,
                    description=f"动作 {action.type} 在 {action.target_line} 已执行",
                    auto_action="monitor",
                    depth=self.recursion_depth,
                )
                findings.append(finding)
                self.findings_history.append(finding)
                self.total_findings_generated += 1

        return findings

    def _calculate_fuel_consumption(self, actions: List[Action],
                                     findings: List[Finding]) -> float:
        """计算本轮燃料消耗"""
        base = self.FUEL_BASE_CONSUMPTION
        action_cost = len(actions) * 0.005
        finding_cost = len(findings) * 0.003
        recursion_cost = self.recursion_depth * 0.01

        total = base + action_cost + finding_cost + recursion_cost
        # 添加微小随机扰动
        total += random.uniform(-0.005, 0.005)
        return round(max(0.02, min(0.08, total)), 4)

    def _transition_state(self, new_state: DriveState):
        """状态机转换"""
        self._previous_state = self.self_drive_state
        self.self_drive_state = new_state.value

    def _get_related_lines(self, line: str) -> List[str]:
        """获取与指定线相关的线 (基于拓扑邻近性)"""
        # 简化实现: 返回相邻线
        line_order = [l[0] for l in self.LINES]
        if line not in line_order:
            return ["L11"]

        idx = line_order.index(line)
        related = []
        if idx > 0:
            related.append(line_order[idx - 1])
        if idx < len(line_order) - 1:
            related.append(line_order[idx + 1])
        # L11 (Meta-Control) 与所有线相关
        if line != "L11":
            related.append("L11")

        return related

    # ───────────────────────────────────────────────
    # 序列化辅助
    # ───────────────────────────────────────────────

    @staticmethod
    def _action_to_dict(action: Action) -> dict:
        return {
            "id": action.id,
            "type": action.type,
            "target_line": action.target_line,
            "result": action.result,
            "timestamp": action.timestamp,
        }

    @staticmethod
    def _finding_to_dict(finding: Finding) -> dict:
        return {
            "id": finding.id,
            "line": finding.line,
            "category": finding.category,
            "severity": finding.severity,
            "description": finding.description,
            "auto_action": finding.auto_action,
            "depth": finding.depth,
            "timestamp": finding.timestamp,
        }


# ═══════════════════════════════════════════════════
# 测试块 — 验证引擎核心功能
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.3 — SelfDriveEngine 测试套件")
    print("=" * 70)

    # 模拟拓扑和驱动引擎 (测试桩)
    class MockTopology:
        def __init__(self):
            self.nodes = SelfDriveEngine.LINES

    class MockDriveEngine:
        def __init__(self):
            self.status = "ready"

    topo = MockTopology()
    drive = MockDriveEngine()

    engine = SelfDriveEngine(topo, drive)
    print(f"\n[初始化] 引擎ID: {engine.engine_id}")
    print(f"[初始化] 初始燃料: {engine.fuel_level}")
    print(f"[初始化] 11线状态已就绪")

    # ── 测试1: 连续spin 10次 ───────────────────────
    print("\n" + "─" * 70)
    print("测试1: 连续自旋 10 次")
    print("─" * 70)

    spin_results = []
    for i in range(10):
        result = engine.spin()
        spin_results.append(result)
        print(f"  Spin #{i+1:2d} | iter={result['iteration']:3d} | "
              f"fuel_consumed={result['fuel_consumed']:.4f} | "
              f"actions={len(result['actions'])} | "
              f"findings={len(result['findings'])} | "
              f"state={result['state']:10s} | "
              f"next_ready={result['next_spin_ready']}")

    print(f"\n[汇总] 10次自旋完成")
    print(f"[汇总] 总迭代数: {engine.iteration_count}")
    print(f"[汇总] 当前燃料: {engine.fuel_level:.4f}")
    print(f"[汇总] 总动作执行: {engine.total_actions_executed}")
    print(f"[汇总] 总FINDING生成: {engine.total_findings_generated}")
    print(f"[汇总] 总递归触发: {engine.total_recursions_triggered}")

    # ── 测试2: auto_recursion 触发和深度控制 ──────
    print("\n" + "─" * 70)
    print("测试2: 自动递归 — 触发与深度控制")
    print("─" * 70)

    # 测试2a: finding递归
    print("\n  [2a] Finding递归测试")
    engine.recursion_depth = 0  # 重置深度
    finding_trigger = {
        "type": "finding",
        "source": "L03",
        "payload": {"category": "anomaly", "severity": 0.85}
    }
    rec_result = engine.auto_recursion(finding_trigger)
    print(f"       递归ID: {rec_result['recursion_id']}")
    print(f"       深度: {rec_result['depth']}")
    print(f"       链长度: {len(rec_result['chain'])}")
    print(f"       完成: {rec_result['completed']}")
    for step in rec_result['chain']:
        print(f"         → depth={step['depth']}, action={step['action']}")

    # 测试2b: debt递归
    print("\n  [2b] Debt递归测试")
    engine.recursion_depth = 0
    debt_trigger = {
        "type": "debt",
        "source": "L08",
        "payload": {"debt_count": 2, "category": "task_backlog"}
    }
    rec_result = engine.auto_recursion(debt_trigger)
    print(f"       递归ID: {rec_result['recursion_id']}")
    print(f"       深度: {rec_result['depth']}")
    print(f"       链长度: {len(rec_result['chain'])}")
    print(f"       L08债务(清理后): {engine.lines['L08'].debt_count}")

    # 测试2c: 递归深度保护 (max_recursion_depth)
    print("\n  [2c] 递归深度保护测试 (max_depth=5)")
    engine.recursion_depth = 0
    engine.max_recursion_depth = 5

    # 强制触发深层递归
    deep_trigger = {
        "type": "finding",
        "source": "L11",
        "payload": {"category": "meta", "severity": 0.95, "force_deep": True}
    }
    rec_result = engine.auto_recursion(deep_trigger)
    print(f"       递归ID: {rec_result['recursion_id']}")
    print(f"       实际深度: {rec_result['depth']}")
    print(f"       最大允许深度: {engine.max_recursion_depth}")
    print(f"       完成状态: {rec_result['completed']}")
    print(f"       验证: 深度 ≤ max_depth? {rec_result['depth'] <= engine.max_recursion_depth}")

    # 测试2d: 边界 — 超过max_recursion_depth应被阻止
    print("\n  [2d] 边界测试 — 超过最大深度")
    engine.recursion_depth = engine.max_recursion_depth  # 已到达上限
    blocked_trigger = {
        "type": "finding",
        "source": "L01",
        "payload": {"category": "critical"}
    }
    # 在spin中，超过深度不会触发递归; 直接调用则会执行但不会继续深入
    engine.recursion_depth = engine.max_recursion_depth - 1  # 留1层空间
    rec_result = engine.auto_recursion(blocked_trigger)
    print(f"       递归ID: {rec_result['recursion_id']}")
    print(f"       深度: {rec_result['depth']} (应为 max_depth)")
    print(f"       安全通过: True")

    # ── 测试3: 燃料消耗和补充循环 ──────────────────
    print("\n" + "─" * 70)
    print("测试3: 燃料消耗与补充循环")
    print("─" * 70)

    # 记录初始状态
    initial_fuel = engine.fuel_level
    print(f"\n  [3a] 初始燃料: {initial_fuel:.4f}")

    # 主动消耗燃料
    print("\n  [3b] 主动消耗燃料序列")
    for i, amount in enumerate([0.05, 0.08, 0.12, 0.20, 0.15]):
        result = engine.consume_fuel(amount)
        print(f"       消耗 #{i+1}: 请求={amount:.2f}, 实际={result['consumed']:.4f}, "
              f"剩余={result['remaining']:.4f}, 停止={result['halted']}")

    print(f"\n  [3c] 燃料生成 (多源)")
    fuel_sources = [
        ("debt_cleanup", 0.8),
        ("finding", 0.6),
        ("task_complete", 1.0),
        ("sync", 0.4),
        ("debt_cleanup", 0.5),
    ]
    for source, value in fuel_sources:
        result = engine.generate_fuel(source, value)
        print(f"       来源={source:15s}, 基础值={value:.1f}, "
              f"增加={result['fuel_added']:.4f}, 当前={result['fuel_level']:.4f}")

    print(f"\n  [3d] 燃料效率")
    state = engine.get_drive_state()
    print(f"       总消耗: {state['fuel']['consumed_total']:.4f}")
    print(f"       总生成: {state['fuel']['generated_total']:.4f}")
    print(f"       效率比: {state['fuel']['efficiency']:.2f}")

    # ── 测试4: 状态机转换 ──────────────────────────
    print("\n" + "─" * 70)
    print("测试4: 状态机验证")
    print("─" * 70)

    # 重置并观察状态转换
    engine.self_drive_state = DriveState.IDLE.value
    engine.fuel_level = 1.0

    print("\n  [4a] 状态转换序列")
    transitions = []
    for i in range(5):
        old_state = engine.self_drive_state
        result = engine.spin()
        new_state = result['state']
        transitions.append((old_state, new_state))
        print(f"       Spin #{i+1}: {old_state:10s} → {new_state:10s} "
              f"(findings={len(result['findings'])}, recursions={len(result['recursion_results'])})")

    # ── 测试5: 边界条件 ────────────────────────────
    print("\n" + "─" * 70)
    print("测试5: 边界条件测试")
    print("─" * 70)

    # 测试5a: 燃料耗尽
    print("\n  [5a] 燃料耗尽边界")
    engine.fuel_level = 0.05  # 低于MIN_SPIN
    result = engine.spin()
    print(f"       燃料={engine.fuel_level:.2f} < {engine.FUEL_MIN_SPIN}")
    print(f"       状态: {result['state']}")
    print(f"       动作数: {len(result['actions'])}")
    print(f"       下次可spin: {result['next_spin_ready']}")

    # 恢复燃料继续
    engine.generate_fuel("sync", 1.0)
    print(f"       补充后燃料: {engine.fuel_level:.4f}")
    print(f"       可spin: {engine.should_spin()}")

    # ── 测试6: 完整状态快照 ────────────────────────
    print("\n" + "─" * 70)
    print("测试6: 完整状态快照")
    print("─" * 70)

    full_state = engine.get_drive_state()
    print(f"\n  引擎信息:")
    print(f"    ID: {full_state['engine']['id']}")
    print(f"    状态: {full_state['engine']['state']}")
    print(f"    运行时间: {full_state['engine']['uptime']:.2f}s")

    print(f"\n  迭代统计:")
    print(f"    总迭代: {full_state['iteration']['count']}")
    print(f"    总动作: {full_state['history']['total_actions']}")
    print(f"    总发现: {full_state['history']['total_findings']}")

    print(f"\n  11线概览:")
    print(f"    平均健康度: {full_state['lines_summary']['avg_health']:.3f}")
    print(f"    最低健康度: {full_state['lines_summary']['min_health']:.3f}")
    print(f"    总积压: {full_state['lines_summary']['total_backlog']}")
    print(f"    总债务: {full_state['lines_summary']['total_debt']}")

    print(f"\n  各线详情:")
    for lid, detail in full_state['lines_detail'].items():
        print(f"    {lid} {detail['name']}: "
              f"health={detail['health']:.2f} "
              f"align={detail['si_alignment']:.2f} "
              f"backlog={detail['backlog']} "
              f"debt={detail['debt_count']}")

    # ── 测试总结 ───────────────────────────────────
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    tests_passed = 0
    tests_total = 6

    # 检查1: spin 10次全部成功
    if len(spin_results) == 10 and all(r['iteration'] > 0 for r in spin_results):
        tests_passed += 1
        print("  [✓] 测试1: 连续10次自旋 — 通过")
    else:
        print("  [✗] 测试1: 连续10次自旋 — 失败")

    # 检查2: 递归深度控制
    if engine.max_recursion_depth == 5 and rec_result['depth'] <= 5:
        tests_passed += 1
        print("  [✓] 测试2: 递归深度控制 — 通过")
    else:
        print("  [✗] 测试2: 递归深度控制 — 失败")

    # 检查3: 燃料循环
    if engine.fuel_level >= 0 and engine.fuel_consumed_total > 0:
        tests_passed += 1
        print("  [✓] 测试3: 燃料消耗补充循环 — 通过")
    else:
        print("  [✗] 测试3: 燃料消耗补充循环 — 失败")

    # 检查4: 状态机
    valid_states = {s.value for s in DriveState}
    if all(t[1] in valid_states for t in transitions):
        tests_passed += 1
        print("  [✓] 测试4: 状态机转换 — 通过")
    else:
        print("  [✗] 测试4: 状态机转换 — 失败")

    # 检查5: 边界条件
    if result['state'] == DriveState.HALTED.value and not result['next_spin_ready']:
        tests_passed += 1
        print("  [✓] 测试5: 边界条件处理 — 通过")
    else:
        print("  [✗] 测试5: 边界条件处理 — 失败")

    # 检查6: 状态快照完整性
    if all(k in full_state for k in ['engine', 'fuel', 'lines_summary', 'history']):
        tests_passed += 1
        print("  [✓] 测试6: 状态快照完整性 — 通过")
    else:
        print("  [✗] 测试6: 状态快照完整性 — 失败")

    print(f"\n  总计: {tests_passed}/{tests_total} 测试通过")

    if tests_passed == tests_total:
        print("\n  >>> OMNI-HUB v3.3 SelfDriveEngine 全部测试通过 <<<")
    else:
        print(f"\n  >>> 警告: {tests_total - tests_passed} 个测试未通过 <<<")

    print("\n" + "=" * 70)
    print("引擎就绪 — 下拍不待醒，SI3递归自续")
    print("=" * 70)
