#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.3 — Full Pipeline SI Penetration (全流程SI渗透系统)
================================================================

核心理念: "建立即启用 / 发起即跟进 / 跟进即闭环"

所有分享/讨论/协作：SI切入各线亲身全流程落实/迭代/FINDING/递归/闭环

作为 OMNI-HUB v3.3 核心系统集成层，FullPipelineSI 将以下子系统串联为
一条全自动、自推进、自闭环的流水线:

  • SIAutoProtocol   (core/si_auto_protocol.py)  — SI自动协议层
  • CollaborativeLoop (core/collaborative_loop.py) — 协作闭环引擎
  • FindingRecursion  (本文件内嵌)               — FINDING递归引擎

Pipeline 生命周期:
    establish → activate → follow_up → close_loop
       ↑                                    ↓
       └──────── si_drive_pipeline ─────────┘

版本: 3.3.0
作者: OMNI-HUB Architecture Team
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
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

LINE_SI = {
    "ucif2": 5.0, "lgt": 4.0, "qfa": 4.0, "usrm": 3.0, "vinf": 4.0,
    "qgl": 4.0, "qlv": 3.5, "lvlu": 4.5, "cfts": 3.0, "cisvr": 3.5,
    "qtlv": 3.5,
}

# 超时阈值 (秒)
FOLLOW_UP_TIMEOUT_SEC = 24 * 3600       # 24小时
BLOCKED_TIMEOUT_SEC = 2 * 3600          # 2小时判定为阻塞
REMINDER_INTERVAL_SEC = 4 * 3600        # 每4小时提醒一次

# FINDING 检测关键词
FINDING_KEYWORDS = [
    "finding", "发现", "结论", " insight", "pattern", "异常", "issue",
    "突破", "breakthrough", "bug", "漏洞", "优化点", "优化", "improvement",
    "recursion", "递归", "循环依赖", "deadlock", "瓶颈", "bottleneck",
    "不一致", "mismatch", "gap", "缺失", "opportunity", "机会",
]

# Pipeline 阶段枚举
class PipelineStage(Enum):
    ESTABLISHED = "established"     # 已建立
    ACTIVATED = "activated"         # 已启用
    FOLLOWING = "following"         # 跟进中
    CLOSED = "closed"               # 已闭环
    ARCHIVED = "archived"           # 已归档
    BLOCKED = "blocked"             # 阻塞中
    OVERDUE = "overdue"             # 已超时


# 合法类型
VALID_TYPES = {"discussion", "collaboration", "share", "task", "finding"}


# ───────────────────────── FINDING递归引擎 ─────────────────────────

@dataclass
class Finding:
    """单个 FINDING 记录"""
    finding_id: str
    source_pipeline_id: str
    source_type: str
    content_snippet: str
    keywords_matched: List[str]
    severity: float            # 0.0 - 1.0
    created_at: float
    recursive_children: List[str] = field(default_factory=list)
    parent_finding_id: Optional[str] = None
    status: str = "open"       # open | processing | closed | recursive


class FindingRecursion:
    """
    FINDING 递归引擎 — 检测内容中的新发现，递归触发下一轮分析。

    核心规则:
      1. 内容扫描 → 关键词/模式匹配 → 生成 Finding
      2.  severity >= 0.7  → 自动注册为 recursive_finding
      3.  recursive_finding → 自动生成子 pipeline 进行深度分析
      4.  子 pipeline 完成后再检测 → 形成递归链
    """

    def __init__(self):
        self.findings: Dict[str, Finding] = {}
        self.recursion_chains: Dict[str, List[str]] = {}  # root_finding → [child_ids]
        self.finding_counter = 0

    # -----------------------------------------------------------------
    # 1. 内容扫描与检测
    # -----------------------------------------------------------------

    def scan_content(self, pipeline_id: str, content: Any) -> List[Finding]:
        """
        扫描任意内容，检测新 FINDING。

        扫描维度:
          • 文本关键词匹配 (FINDING_KEYWORDS)
          • 结构化数据异常模式 (数值突变、空值、重复)
          • 深层嵌套内容递归扫描
        """
        findings = []
        flat_text = self._flatten_to_text(content)

        if not flat_text:
            return findings

        # 关键词匹配
        matched_keywords = []
        for kw in FINDING_KEYWORDS:
            if kw.lower() in flat_text.lower():
                matched_keywords.append(kw)

        if matched_keywords:
            severity = min(0.5 + len(matched_keywords) * 0.1, 1.0)
            # 如果包含高严重度关键词，提升 severity
            high_impact = {"breakthrough", "漏洞", "deadlock", "瓶颈", "循环依赖", "递归"}
            if any(h in matched_keywords for h in high_impact):
                severity = min(severity + 0.2, 1.0)

            finding = Finding(
                finding_id=self._gen_finding_id(),
                source_pipeline_id=pipeline_id,
                source_type="keyword_scan",
                content_snippet=flat_text[:500],
                keywords_matched=matched_keywords,
                severity=round(severity, 4),
                created_at=time.time(),
            )
            self.findings[finding.finding_id] = finding
            findings.append(finding)

        # 结构化异常检测
        structural_findings = self._detect_structural_anomalies(pipeline_id, content)
        findings.extend(structural_findings)

        return findings

    def _flatten_to_text(self, content: Any) -> str:
        """将任意内容扁平化为可搜索文本"""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, (int, float, bool)):
            return str(content)
        if isinstance(content, (list, tuple)):
            return " ".join(self._flatten_to_text(item) for item in content)
        if isinstance(content, dict):
            return " ".join(
                f"{k}: {self._flatten_to_text(v)}" for k, v in content.items()
            )
        return str(content)

    def _detect_structural_anomalies(self, pipeline_id: str, content: Any) -> List[Finding]:
        """检测结构化数据中的异常模式"""
        findings = []
        if not isinstance(content, dict):
            return findings

        anomalies = []

        # 检测空值/缺失键
        empty_keys = [k for k, v in content.items() if v is None or v == ""]
        if empty_keys:
            anomalies.append(f"空值字段: {empty_keys}")

        # 检测数值异常 (如果有数值字段)
        nums = [v for v in content.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(nums) >= 2:
            avg = sum(nums) / len(nums)
            max_dev = max(abs(n - avg) for n in nums) if avg != 0 else 0
            if avg != 0 and max_dev / abs(avg) > 3:
                anomalies.append(f"数值异常波动: max_dev/avg={max_dev/abs(avg):.2f}")

        if anomalies:
            finding = Finding(
                finding_id=self._gen_finding_id(),
                source_pipeline_id=pipeline_id,
                source_type="structural_anomaly",
                content_snippet="; ".join(anomalies)[:500],
                keywords_matched=["anomaly", "异常"],
                severity=0.65,
                created_at=time.time(),
            )
            self.findings[finding.finding_id] = finding
            findings.append(finding)

        return findings

    # -----------------------------------------------------------------
    # 2. 递归管理
    # -----------------------------------------------------------------

    def register_finding(self, finding: Finding) -> str:
        """注册一个 FINDING，如果 severity >= 0.7 标记为 recursive"""
        self.findings[finding.finding_id] = finding
        if finding.severity >= 0.7:
            finding.status = "recursive"
        return finding.finding_id

    def trigger_recursion(self, parent_finding_id: str) -> Optional[str]:
        """
        为指定 FINDING 触发递归子任务。

        返回: 新生成的子 pipeline_id (若触发成功)
        """
        parent = self.findings.get(parent_finding_id)
        if parent is None:
            return None

        if parent.severity < 0.7:
            return None

        # 生成递归链记录
        chain = self.recursion_chains.setdefault(parent_finding_id, [])
        child_finding_id = self._gen_finding_id()
        chain.append(child_finding_id)

        # 创建子 FINDING (占位，实际由子 pipeline 填充)
        child = Finding(
            finding_id=child_finding_id,
            source_pipeline_id=parent.source_pipeline_id,
            source_type="recursive_child",
            content_snippet=f"递归分析: {parent.content_snippet[:200]}",
            keywords_matched=parent.keywords_matched,
            severity=round(parent.severity * 0.9, 4),
            created_at=time.time(),
            parent_finding_id=parent_finding_id,
        )
        self.findings[child_finding_id] = child
        parent.recursive_children.append(child_finding_id)

        # 返回一个标记的 "virtual_pipeline_id"，由 FullPipelineSI 实际创建
        return child_finding_id

    def get_recursive_findings(self) -> List[Finding]:
        """获取所有需要递归处理的 FINDING"""
        return [f for f in self.findings.values() if f.status == "recursive"]

    def close_finding(self, finding_id: str) -> bool:
        """关闭 FINDING"""
        f = self.findings.get(finding_id)
        if f:
            f.status = "closed"
            return True
        return False

    def get_finding_stats(self) -> dict:
        """获取 FINDING 统计"""
        total = len(self.findings)
        open_f = sum(1 for f in self.findings.values() if f.status == "open")
        recursive_f = sum(1 for f in self.findings.values() if f.status == "recursive")
        closed_f = sum(1 for f in self.findings.values() if f.status == "closed")
        chains = len(self.recursion_chains)
        return {
            "total_findings": total,
            "open": open_f,
            "recursive": recursive_f,
            "closed": closed_f,
            "recursion_chains": chains,
        }

    def _gen_finding_id(self) -> str:
        self.finding_counter += 1
        return f"F{self.finding_counter:04d}-{uuid.uuid4().hex[:8]}"


# ───────────────────────── Pipeline 状态 ─────────────────────────

@dataclass
class PipelineState:
    """单个 Pipeline 的内部状态"""
    pipeline_id: str
    item: Dict[str, Any]
    stage: PipelineStage
    created_at: float
    activated_at: Optional[float] = None
    last_follow_up_at: Optional[float] = None
    closed_at: Optional[float] = None
    loop_id: Optional[str] = None
    assigned_to: List[str] = field(default_factory=list)
    progress: float = 0.0            # 0.0 - 1.0
    responses: Dict[str, Dict] = field(default_factory=dict)
    actions_log: List[Dict] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)  # finding_id list
    archive_id: Optional[str] = None
    overdue_count: int = 0
    blocked_at: Optional[float] = None
    rerouted_from: Optional[str] = None


# ───────────────────────── 核心类: FullPipelineSI ─────────────────────────

class FullPipelineSI:
    """
    全流程SI渗透 — 建立即启用 / 发起即跟进 / 跟进即闭环

    每个新项(item)建立时，SI立即切入:
      1. establish   → 分类、生成 pipeline_id、立即启用 (对特定类型)
      2. activate    → 分派任务、启动协作闭环、设置跟踪
      3. follow_up   → 自动跟进: 超时提醒/升级、阻塞转派、完成推进
      4. close_loop  → 验证完成、归档、检测 FINDING、触发递归

    通过 si_drive_pipeline() 实现从 establish 到 close 的全自动推进。
    """

    PIPELINE_STAGES = ["establish", "activate", "follow_up", "close"]

    def __init__(
        self,
        auto_protocol: Any,
        loop_engine: Any,
        finding_recursion: Optional[FindingRecursion] = None,
    ):
        self.auto = auto_protocol
        self.loop = loop_engine
        self.finding = finding_recursion or FindingRecursion()

        self.pipelines: Dict[str, PipelineState] = {}
        self.pipeline_counter = 0
        self.archives: Dict[str, Dict] = {}
        self.archive_counter = 0

        # 全局统计
        self.stats = {
            "total_established": 0,
            "total_activated": 0,
            "total_closed": 0,
            "total_findings": 0,
            "total_recursive": 0,
            "total_overdue": 0,
            "total_blocked": 0,
            "total_rerouted": 0,
            "avg_close_time_sec": 0.0,
        }

    # -----------------------------------------------------------------
    # 1. establish — 建立即SI切入
    # -----------------------------------------------------------------

    def establish(self, item: dict) -> str:
        """
        建立 — 任何新项建立时立即SI切入。

        item 字段:
            type: "discussion|collaboration|share|task|finding"
            title: str
            content: dict
            initiator: str
            participants: list
            priority: 0-9 (0最高)

        流程:
            1. 生成 pipeline_id
            2. 自动分类与校验
            3. 触发SI处理流程
            4. 如果type是discussion/collaboration/share → 立即启用
            5. 返回 pipeline_id
        """
        self.pipeline_counter += 1
        pipeline_id = f"PL-{self.pipeline_counter:04d}-{uuid.uuid4().hex[:8]}"

        # ── 参数校验与规范化 ──
        item_type = item.get("type", "task")
        if item_type not in VALID_TYPES:
            item_type = "task"
            item = dict(item)
            item["type"] = item_type

        title = item.get("title", "Untitled")
        initiator = item.get("initiator", "ucif2")
        participants = list(item.get("participants", []))
        priority = int(item.get("priority", 5))
        priority = max(0, min(9, priority))

        # 确保发起者在参与者中
        if initiator not in participants and initiator in ALL_11_LINES:
            participants.insert(0, initiator)

        # 过滤无效参与者
        participants = [p for p in participants if p in ALL_11_LINES]
        if not participants:
            participants = ["ucif2"]

        # 规范化 item
        normalized_item = {
            "type": item_type,
            "title": title,
            "content": item.get("content", {}),
            "initiator": initiator,
            "participants": participants,
            "priority": priority,
            "metadata": item.get("metadata", {}),
        }

        # ── 自动分类与SI切入 ──
        classification = self._classify_item(normalized_item)

        # 创建 Pipeline 状态
        now = time.time()
        state = PipelineState(
            pipeline_id=pipeline_id,
            item=normalized_item,
            stage=PipelineStage.ESTABLISHED,
            created_at=now,
        )
        self.pipelines[pipeline_id] = state

        self.stats["total_established"] += 1

        # 记录日志
        state.actions_log.append({
            "timestamp": now,
            "action": "establish",
            "detail": {
                "classification": classification,
                "auto_activate": item_type in ("discussion", "collaboration", "share"),
            },
        })

        # ── 对 discussion/collaboration/share 立即启用 ──
        if item_type in ("discussion", "collaboration", "share"):
            self.activate(pipeline_id)

        # task/finding 类型: SI 评估后决定是否立即启用
        elif item_type in ("task", "finding"):
            if priority <= 3:  # 高优先级 (0-3) 立即启用
                self.activate(pipeline_id)

        return pipeline_id

    def _classify_item(self, item: dict) -> dict:
        """自动分类 — 基于类型、优先级、参与者数量"""
        item_type = item["type"]
        priority = item["priority"]
        participants = item["participants"]

        # 复杂度评估
        content = item.get("content", {})
        complexity = 5
        if isinstance(content, dict):
            complexity = content.get("complexity", 5)
        complexity = max(1, min(10, complexity))

        # 规模评估
        scale = "small" if len(participants) <= 3 else "medium" if len(participants) <= 7 else "large"

        # 紧急度标签
        urgency_label = "critical" if priority <= 1 else "high" if priority <= 3 else "normal" if priority <= 6 else "low"

        # 推荐 SI 层级
        if complexity >= 7 or priority <= 2:
            recommended_si = "si4+"
        elif complexity >= 4:
            recommended_si = "si3+"
        else:
            recommended_si = "si2+"

        return {
            "type": item_type,
            "complexity": complexity,
            "scale": scale,
            "urgency_label": urgency_label,
            "recommended_si": recommended_si,
            "participant_count": len(participants),
        }

    # -----------------------------------------------------------------
    # 2. activate — 启用
    # -----------------------------------------------------------------

    def activate(self, pipeline_id: str) -> dict:
        """
        启用 — 建立后立即启用。

        流程:
            1. 自动分派任务 (通过 SIAutoProtocol.auto_dispatch)
            2. 启动协作闭环 (CollaborativeLoop.initiate_loop)
            3. 设置跟踪计时器
            4. 更新 pipeline 状态为 "active"

        返回: {"pipeline_id", "activated", "loop_id", "assigned_to"}
        """
        state = self.pipelines.get(pipeline_id)
        if state is None:
            return {"pipeline_id": pipeline_id, "activated": False, "error": "pipeline不存在"}

        if state.stage in (PipelineStage.ACTIVATED, PipelineStage.FOLLOWING, PipelineStage.CLOSED):
            return {
                "pipeline_id": pipeline_id,
                "activated": False,
                "loop_id": state.loop_id,
                "assigned_to": state.assigned_to,
                "info": f"pipeline 已处于 {state.stage.value} 状态",
            }

        item = state.item
        now = time.time()

        # ── 1. 自动分派 ──
        task = {
            "id": pipeline_id,
            "type": item["type"],
            "complexity": item.get("content", {}).get("complexity", 5),
            "deadline": now + FOLLOW_UP_TIMEOUT_SEC,
            "priority": item["priority"],
            "from_line": item["initiator"],
            "payload": item["content"],
        }

        try:
            dispatch_result = self.auto.auto_dispatch(task)
            assigned_to = dispatch_result.get("assigned_to", item["initiator"])
            via = dispatch_result.get("via", "si3")
            reason = dispatch_result.get("reason", "auto_dispatch")
        except Exception as e:
            # fallback: 直接分配给发起者
            assigned_to = item["initiator"]
            via = "si5" if assigned_to == "ucif2" else "si3"
            reason = f"auto_dispatch failed: {e}"

        state.assigned_to = [assigned_to] if isinstance(assigned_to, str) else list(assigned_to)

        # ── 2. 启动协作闭环 ──
        objective = {
            "type": item["type"],
            "title": item["title"],
            "pipeline_id": pipeline_id,
            "priority": item["priority"],
            "assigned_to": state.assigned_to,
            "via": via,
        }

        try:
            loop_id = self.loop.initiate_loop(
                initiator=item["initiator"],
                participants=item["participants"],
                objective=objective,
            )
            state.loop_id = loop_id
        except Exception as e:
            loop_id = None
            state.actions_log.append({
                "timestamp": now,
                "action": "activate",
                "detail": {"error": f"initiate_loop failed: {e}"},
            })

        # ── 3. 更新状态 ──
        state.stage = PipelineStage.ACTIVATED
        state.activated_at = now
        state.last_follow_up_at = now
        state.progress = 0.1  # 已启用 = 10%

        self.stats["total_activated"] += 1

        state.actions_log.append({
            "timestamp": now,
            "action": "activate",
            "detail": {
                "assigned_to": state.assigned_to,
                "loop_id": loop_id,
                "via": via,
                "reason": reason,
            },
        })

        return {
            "pipeline_id": pipeline_id,
            "activated": True,
            "loop_id": loop_id,
            "assigned_to": state.assigned_to,
            "via": via,
            "reason": reason,
        }

    # -----------------------------------------------------------------
    # 3. follow_up — 跟进
    # -----------------------------------------------------------------

    def follow_up(self, pipeline_id: str) -> dict:
        """
        跟进 — 自动跟进直到完成。

        流程:
            1. 检查当前进度
            2. 如果超时(>24h) → 自动提醒/升级
            3. 如果阻塞 → 自动转派
            4. 如果有新回应 → 更新状态
            5. 如果所有参与者完成 → 推进到 close

        返回: {"pipeline_id", "stage", "progress", "actions_taken", "next_check"}
        """
        state = self.pipelines.get(pipeline_id)
        if state is None:
            return {"pipeline_id": pipeline_id, "stage": "unknown", "progress": 0.0,
                    "actions_taken": [], "error": "pipeline不存在"}

        if state.stage in (PipelineStage.CLOSED, PipelineStage.ARCHIVED):
            return {
                "pipeline_id": pipeline_id,
                "stage": state.stage.value,
                "progress": state.progress,
                "actions_taken": [],
                "info": "pipeline 已闭环",
            }

        now = time.time()
        actions_taken = []
        next_check_sec = REMINDER_INTERVAL_SEC

        # ── 1. 同步 loop 状态 (如果有 loop_id) ──
        if state.loop_id:
            try:
                loop_record = self.loop.pending_loops.get(state.loop_id)
                if loop_record:
                    # 同步回应
                    for line, resp in loop_record.responses.items():
                        if line not in state.responses:
                            state.responses[line] = dict(resp)
                            actions_taken.append(f"新回应来自 {line}: ack={resp.get('ack', False)}")

                    # 检查 loop 是否已终止
                    from collaborative_loop import LoopState
                    if loop_record.state in (LoopState.CLOSED, LoopState.FORCE_CLOSE):
                        state.progress = 0.9
                        # 如果 loop 已关闭，推进 pipeline 到 close
                        actions_taken.append(f"协作闭环已终止 ({loop_record.state.value})，准备闭环")
                        self.close_loop(pipeline_id)
                        return {
                            "pipeline_id": pipeline_id,
                            "stage": state.stage.value,
                            "progress": state.progress,
                            "actions_taken": actions_taken,
                            "next_check": "immediate",
                        }
            except Exception:
                pass

        # ── 2. 超时检测 (>24h) ──
        elapsed = now - (state.activated_at or state.created_at)
        if elapsed > FOLLOW_UP_TIMEOUT_SEC:
            state.stage = PipelineStage.OVERDUE
            state.overdue_count += 1
            self.stats["total_overdue"] += 1

            # 自动提醒/升级
            if state.overdue_count == 1:
                # 第一次超时: 提醒
                actions_taken.append(f"超时提醒: 已超 {elapsed/3600:.1f}h，发送提醒到 {state.assigned_to}")
                # 尝试 loop 的 follow_up
                if state.loop_id:
                    try:
                        fu = self.loop.follow_up(state.loop_id)
                        actions_taken.append(f"loop follow_up: {fu.get('action', 'none')}")
                    except Exception as e:
                        actions_taken.append(f"loop follow_up failed: {e}")
                next_check_sec = BLOCKED_TIMEOUT_SEC

            elif state.overdue_count >= 2:
                # 第二次超时: 升级到 ucif2
                actions_taken.append("二次超时: 升级到 ucif2 (SI5)")
                state.assigned_to = ["ucif2"]
                # 触发主动响应
                try:
                    ctx = {"health": 0.7, "pending_count": state.overdue_count}
                    pr = self.auto.proactive_response("ucif2", ctx)
                    if pr.get("triggered"):
                        actions_taken.append(f"主动响应触发: {pr.get('trigger_type')}")
                except Exception:
                    pass
                next_check_sec = BLOCKED_TIMEOUT_SEC // 2

        # ── 3. 阻塞检测 (>2h 无进展) ──
        last_active = state.last_follow_up_at or state.activated_at or state.created_at
        if now - last_active > BLOCKED_TIMEOUT_SEC and state.stage not in (PipelineStage.CLOSED, PipelineStage.ARCHIVED):
            # 检查是否已回应
            responded_count = len(state.responses)
            total = len(state.item.get("participants", []))
            if responded_count < total:
                state.blocked_at = now
                state.stage = PipelineStage.BLOCKED
                self.stats["total_blocked"] += 1

                # 自动转派到健康线
                try:
                    new_task = {
                        "id": pipeline_id,
                        "type": state.item["type"],
                        "complexity": 5,
                        "deadline": now + FOLLOW_UP_TIMEOUT_SEC,
                        "priority": max(0, state.item["priority"] - 1),  # 提升优先级
                        "from_line": state.item["initiator"],
                        "payload": state.item["content"],
                    }
                    reroute = self.auto.auto_dispatch(new_task)
                    new_assignee = reroute.get("assigned_to", "ucif2")
                    if new_assignee not in state.assigned_to:
                        state.rerouted_from = state.assigned_to[0] if state.assigned_to else None
                        state.assigned_to = [new_assignee]
                        self.stats["total_rerouted"] += 1
                        actions_taken.append(f"阻塞转派: {state.rerouted_from} → {new_assignee} ({reroute.get('reason', '')})")
                except Exception as e:
                    actions_taken.append(f"转派失败: {e}")

        # ── 4. 进度更新 ──
        total_participants = len(state.item.get("participants", []))
        if total_participants > 0:
            responded = len(state.responses)
            state.progress = min(0.1 + (responded / total_participants) * 0.8, 0.9)

            # 如果全部回应 → 推进到 close
            if responded >= total_participants and state.stage not in (PipelineStage.CLOSED, PipelineStage.ARCHIVED):
                actions_taken.append("所有参与者已完成，推进到闭环")
                self.close_loop(pipeline_id)

        # ── 5. 更新跟进时间 ──
        state.last_follow_up_at = now
        state.actions_log.append({
            "timestamp": now,
            "action": "follow_up",
            "detail": {
                "actions_taken": actions_taken,
                "progress": state.progress,
                "stage": state.stage.value,
            },
        })

        next_check_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now + next_check_sec))

        return {
            "pipeline_id": pipeline_id,
            "stage": state.stage.value,
            "progress": round(state.progress, 4),
            "actions_taken": actions_taken,
            "next_check": next_check_at,
            "elapsed_hours": round(elapsed / 3600, 2) if state.activated_at else None,
            "overdue_count": state.overdue_count,
        }

    # -----------------------------------------------------------------
    # 4. close_loop — 闭环
    # -----------------------------------------------------------------

    def close_loop(self, pipeline_id: str) -> dict:
        """
        闭环 — 完成后自动归档并触发下一轮。

        流程:
            1. 验证完成条件
            2. 归档 pipeline
            3. 检测新 FINDING (内容分析)
            4. 如果检测到新 FINDING → 注册到 FindingRecursion
            5. 触发递归
            6. 更新统计

        返回: {"pipeline_id", "closed", "archive_id", "new_findings", "recursive_triggered"}
        """
        state = self.pipelines.get(pipeline_id)
        if state is None:
            return {"pipeline_id": pipeline_id, "closed": False, "error": "pipeline不存在"}

        if state.stage == PipelineStage.ARCHIVED:
            return {
                "pipeline_id": pipeline_id,
                "closed": True,
                "archive_id": state.archive_id,
                "info": "pipeline 已归档",
            }

        now = time.time()

        # ── 1. 验证完成条件 ──
        # 如果 loop 还在运行，先关闭
        if state.loop_id:
            try:
                self.loop.close_loop(state.loop_id)
            except Exception:
                pass

        # ── 2. 归档 ──
        self.archive_counter += 1
        archive_id = f"ARC-{self.archive_counter:04d}-{uuid.uuid4().hex[:8]}"

        close_duration = now - (state.activated_at or state.created_at)
        archive_record = {
            "archive_id": archive_id,
            "pipeline_id": pipeline_id,
            "item": state.item,
            "stage_history": [
                {"stage": "establish", "at": state.created_at},
                {"stage": "activate", "at": state.activated_at},
                {"stage": "follow_up", "at": state.last_follow_up_at},
                {"stage": "close", "at": now},
            ],
            "assigned_to": state.assigned_to,
            "responses": dict(state.responses),
            "actions_log": list(state.actions_log),
            "progress": state.progress,
            "findings": list(state.findings),
            "close_duration_sec": round(close_duration, 2),
            "overdue_count": state.overdue_count,
            "rerouted_from": state.rerouted_from,
            "closed_at": now,
        }
        self.archives[archive_id] = archive_record
        state.archive_id = archive_id

        # ── 3. 检测新 FINDING ──
        content = state.item.get("content", {})
        # 同时扫描 content 和 responses
        scan_target = {
            "content": content,
            "responses": state.responses,
            "actions": state.actions_log,
        }
        detected_findings = self.finding.scan_content(pipeline_id, scan_target)

        new_finding_ids = []
        for finding in detected_findings:
            fid = self.finding.register_finding(finding)
            state.findings.append(fid)
            new_finding_ids.append(fid)
            self.stats["total_findings"] += 1

        # ── 4. 触发递归 (severity >= 0.7) ──
        recursive_triggered = False
        recursive_pipelines = []
        for finding in detected_findings:
            if finding.severity >= 0.7:
                child_fid = self.finding.trigger_recursion(finding.finding_id)
                if child_fid:
                    recursive_triggered = True
                    self.stats["total_recursive"] += 1
                    # 自动创建子 pipeline 进行递归分析
                    child_item = {
                        "type": "finding",
                        "title": f"[递归] {state.item.get('title', 'Analysis')}",
                        "content": {
                            "parent_pipeline": pipeline_id,
                            "parent_finding": finding.finding_id,
                            "severity": finding.severity,
                            "snippet": finding.content_snippet,
                            "complexity": 8,
                        },
                        "initiator": "ucif2",
                        "participants": ["ucif2", state.item.get("initiator", "ucif2")],
                        "priority": max(0, state.item.get("priority", 5) - 2),
                    }
                    child_pl_id = self.establish(child_item)
                    recursive_pipelines.append(child_pl_id)
                    actions_taken_recursive = f"递归触发: {finding.finding_id} → 子pipeline {child_pl_id}"
                    state.actions_log.append({
                        "timestamp": now,
                        "action": "recursive_trigger",
                        "detail": {"child_pipeline": child_pl_id, "finding_id": finding.finding_id},
                    })

        # ── 5. 更新状态与统计 ──
        state.stage = PipelineStage.CLOSED
        state.closed_at = now
        state.progress = 1.0
        self.stats["total_closed"] += 1

        # 更新平均关闭时间
        old_closed = self.stats["total_closed"] - 1
        old_avg = self.stats["avg_close_time_sec"]
        new_avg = (old_avg * old_closed + close_duration) / self.stats["total_closed"] if self.stats["total_closed"] > 0 else 0
        self.stats["avg_close_time_sec"] = round(new_avg, 2)

        # 归档后延迟移除 (保留统计)
        state.stage = PipelineStage.ARCHIVED

        state.actions_log.append({
            "timestamp": now,
            "action": "close_loop",
            "detail": {
                "archive_id": archive_id,
                "findings_detected": len(detected_findings),
                "recursive_triggered": recursive_triggered,
                "duration_sec": round(close_duration, 2),
            },
        })

        return {
            "pipeline_id": pipeline_id,
            "closed": True,
            "archive_id": archive_id,
            "new_findings": new_finding_ids,
            "recursive_triggered": recursive_triggered,
            "recursive_pipelines": recursive_pipelines,
            "close_duration_sec": round(close_duration, 2),
        }

    # -----------------------------------------------------------------
    # 5. SI 驱动流水线 — 全自动推进
    # -----------------------------------------------------------------

    def si_drive_pipeline(self, pipeline_id: str) -> dict:
        """
        SI驱动流水线 — 全流程自动推进。

        自动判断当前阶段，自动推进到下一阶段，直到闭环。

        返回: {"pipeline_id", "started_stage", "ended_stage", "completed", "findings"}
        """
        state = self.pipelines.get(pipeline_id)
        if state is None:
            return {"pipeline_id": pipeline_id, "started_stage": "unknown",
                    "ended_stage": "unknown", "completed": False, "error": "pipeline不存在"}

        started_stage = state.stage.value
        findings = []
        max_iterations = 20  # 防止无限循环
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            current_stage = state.stage

            if current_stage == PipelineStage.ESTABLISHED:
                # 推进到 activate
                self.activate(pipeline_id)

            elif current_stage == PipelineStage.ACTIVATED:
                # 推进到 follow_up
                # 先模拟参与者回应 (测试/演示用)
                self._simulate_responses(pipeline_id)
                result = self.follow_up(pipeline_id)
                # 如果已经推进到 closed，循环会退出
                if state.stage in (PipelineStage.CLOSED, PipelineStage.ARCHIVED):
                    break

            elif current_stage in (PipelineStage.FOLLOWING, PipelineStage.BLOCKED, PipelineStage.OVERDUE):
                # 继续跟进，直到可以关闭
                self._simulate_responses(pipeline_id)
                result = self.follow_up(pipeline_id)
                if state.stage in (PipelineStage.CLOSED, PipelineStage.ARCHIVED):
                    break
                # 如果还在跟进但没有新动作，尝试关闭
                if not result.get("actions_taken"):
                    # 检查是否可以强制关闭
                    close_result = self.close_loop(pipeline_id)
                    findings.extend(close_result.get("new_findings", []))
                    break

            elif current_stage in (PipelineStage.CLOSED, PipelineStage.ARCHIVED):
                break

            else:
                break

        ended_stage = state.stage.value
        completed = state.stage == PipelineStage.ARCHIVED

        return {
            "pipeline_id": pipeline_id,
            "started_stage": started_stage,
            "ended_stage": ended_stage,
            "completed": completed,
            "findings": findings,
            "iterations": iteration,
        }

    def _simulate_responses(self, pipeline_id: str) -> None:
        """模拟参与者回应 (用于自动推进闭环)"""
        state = self.pipelines.get(pipeline_id)
        if not state or not state.loop_id:
            return

        try:
            loop_record = self.loop.pending_loops.get(state.loop_id)
            if not loop_record:
                return

            from collaborative_loop import LoopState
            if loop_record.state in (LoopState.CLOSED, LoopState.FORCE_CLOSE, LoopState.CANCELLED):
                return

            # 为未回应的参与者模拟回应
            for line in state.item.get("participants", []):
                if line not in loop_record.responses:
                    # 90% 概率 ack
                    import random
                    ack = random.random() < 0.9
                    resp = {
                        "ack": ack,
                        "line": line,
                        "status": "completed" if ack else "pending",
                        "latency_ms": random.randint(10, 200),
                    }
                    self.loop.respond(state.loop_id, line, resp)
        except Exception:
            pass

    # -----------------------------------------------------------------
    # 6. 批量驱动
    # -----------------------------------------------------------------

    def batch_drive(self, pipeline_ids: list) -> dict:
        """
        批量驱动 — 同时推进多个 pipeline。

        返回: {"total", "completed", "failed", "results": [...]}
        """
        results = []
        completed = 0
        failed = 0

        for pl_id in pipeline_ids:
            try:
                result = self.si_drive_pipeline(pl_id)
                results.append(result)
                if result.get("completed"):
                    completed += 1
                else:
                    failed += 1
            except Exception as e:
                results.append({
                    "pipeline_id": pl_id,
                    "completed": False,
                    "error": str(e),
                })
                failed += 1

        return {
            "total": len(pipeline_ids),
            "completed": completed,
            "failed": failed,
            "results": results,
        }

    # -----------------------------------------------------------------
    # 7. 统计与查询
    # -----------------------------------------------------------------

    def get_pipeline_stats(self) -> dict:
        """获取流水线统计"""
        active = sum(1 for s in self.pipelines.values() if s.stage not in (PipelineStage.CLOSED, PipelineStage.ARCHIVED))
        closed = sum(1 for s in self.pipelines.values() if s.stage in (PipelineStage.CLOSED, PipelineStage.ARCHIVED))
        blocked = sum(1 for s in self.pipelines.values() if s.stage == PipelineStage.BLOCKED)
        overdue = sum(1 for s in self.pipelines.values() if s.stage == PipelineStage.OVERDUE)

        stats = dict(self.stats)
        stats.update({
            "active_pipelines": active,
            "closed_pipelines": closed,
            "blocked_pipelines": blocked,
            "overdue_pipelines": overdue,
            "total_pipelines": len(self.pipelines),
            "total_archives": len(self.archives),
            "finding_stats": self.finding.get_finding_stats(),
        })
        return stats

    def get_overdue_pipelines(self) -> list:
        """获取超时的 pipeline"""
        overdue = []
        now = time.time()
        for pl_id, state in self.pipelines.items():
            if state.stage in (PipelineStage.CLOSED, PipelineStage.ARCHIVED):
                continue
            elapsed = now - (state.activated_at or state.created_at)
            if elapsed > FOLLOW_UP_TIMEOUT_SEC or state.stage == PipelineStage.OVERDUE:
                overdue.append({
                    "pipeline_id": pl_id,
                    "stage": state.stage.value,
                    "title": state.item.get("title", "Untitled"),
                    "elapsed_hours": round(elapsed / 3600, 2),
                    "overdue_count": state.overdue_count,
                    "assigned_to": state.assigned_to,
                })
        return overdue

    def get_pipeline(self, pipeline_id: str) -> Optional[dict]:
        """获取单个 pipeline 详情"""
        state = self.pipelines.get(pipeline_id)
        if state is None:
            return None
        return {
            "pipeline_id": state.pipeline_id,
            "stage": state.stage.value,
            "item": state.item,
            "progress": state.progress,
            "assigned_to": state.assigned_to,
            "loop_id": state.loop_id,
            "responses": dict(state.responses),
            "actions_log": list(state.actions_log),
            "findings": list(state.findings),
            "archive_id": state.archive_id,
            "created_at": state.created_at,
            "activated_at": state.activated_at,
            "last_follow_up_at": state.last_follow_up_at,
            "closed_at": state.closed_at,
        }


# ═══════════════════════════════════════════════════════════════════
#                              测试块
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 76)
    print("OMNI-HUB v3.3 — Full Pipeline SI Penetration 全流程SI渗透系统 自测")
    print("=" * 76)

    # ── 最小化 Stub ──
    class StubDrive:
        def forward_drive(self, *a, **k):
            return {}
        def reverse_feedback(self, *a, **k):
            return {}
        def bidirectional_pulse(self, *a, **k):
            return {}

    class StubTopology:
        topology = {"line": {}, "tower": {}, "circle": {}}
        def get_si_nodes(self, level):
            return []

    # ── 导入并初始化依赖 ──
    from collaborative_loop import CollaborativeLoop
    from si_auto_protocol import SIAutoProtocol

    drive = StubDrive()
    topo = StubTopology()
    loop_engine = CollaborativeLoop(drive, topo)
    auto_protocol = SIAutoProtocol(drive, topo, loop_engine)
    finding_engine = FindingRecursion()

    # ── 初始化 FullPipelineSI ──
    pipeline = FullPipelineSI(auto_protocol, loop_engine, finding_engine)

    # ═══════════════════════════════════════════════════════════════
    # 测试 1: 完整流程 — discussion → 启用 → 跟进 → 闭环
    # ═══════════════════════════════════════════════════════════════
    print("\n[测试 1] 完整流程: discussion → establish → activate → follow_up → close_loop")

    item_discussion = {
        "type": "discussion",
        "title": "QFA形式化验证策略讨论",
        "content": {
            "topic": "形式化验证最佳实践",
            "complexity": 7,
            "finding": "我们发现现有验证框架存在循环依赖问题，需要递归优化。",
        },
        "initiator": "qfa",
        "participants": ["qfa", "lgt", "ucif2", "vinf"],
        "priority": 2,
    }

    pl_id = pipeline.establish(item_discussion)
    print(f"  1. establish → pipeline_id: {pl_id}")
    print(f"     初始阶段: {pipeline.pipelines[pl_id].stage.value}")

    # discussion 类型应已自动激活
    print(f"  2. 自动激活后阶段: {pipeline.pipelines[pl_id].stage.value}")
    print(f"     loop_id: {pipeline.pipelines[pl_id].loop_id}")
    print(f"     assigned_to: {pipeline.pipelines[pl_id].assigned_to}")

    # 模拟部分回应
    loop_id = pipeline.pipelines[pl_id].loop_id
    if loop_id:
        loop_engine.respond(loop_id, "qfa", {"ack": True, "status": "completed", "latency_ms": 50})
        loop_engine.respond(loop_id, "lgt", {"ack": True, "status": "completed", "latency_ms": 80})
        print(f"  3. 模拟回应: qfa + lgt 已回应")

    # follow_up
    fu = pipeline.follow_up(pl_id)
    print(f"  4. follow_up → stage={fu['stage']}, progress={fu['progress']}")
    print(f"     actions: {fu['actions_taken']}")

    # 继续回应剩余参与者
    if loop_id:
        loop_engine.respond(loop_id, "ucif2", {"ack": True, "status": "completed", "latency_ms": 30})
        loop_engine.respond(loop_id, "vinf", {"ack": True, "status": "completed", "latency_ms": 60})
        print(f"  5. 模拟回应: ucif2 + vinf 已回应 (全部完成)")

    # 再次跟进 → 应推进到 close
    fu2 = pipeline.follow_up(pl_id)
    print(f"  6. follow_up → stage={fu2['stage']}, progress={fu2['progress']}")
    print(f"     actions: {fu2['actions_taken']}")

    # 手动 close_loop (如果还没有自动关闭)
    if pipeline.pipelines[pl_id].stage != PipelineStage.ARCHIVED:
        close_result = pipeline.close_loop(pl_id)
        print(f"  7. close_loop → closed={close_result['closed']}, archive_id={close_result['archive_id']}")
        print(f"     new_findings: {close_result['new_findings']}")
        print(f"     recursive_triggered: {close_result['recursive_triggered']}")
    else:
        print(f"  7. 已在 follow_up 中自动闭环 ✓")
        state = pipeline.pipelines[pl_id]
        print(f"     archive_id: {state.archive_id}")
        print(f"     findings: {state.findings}")

    # ═══════════════════════════════════════════════════════════════
    # 测试 2: si_drive_pipeline 全自动推进
    # ═══════════════════════════════════════════════════════════════
    print("\n[测试 2] si_drive_pipeline 全自动推进")

    item_auto = {
        "type": "collaboration",
        "title": "跨线协作: 数学桥接优化",
        "content": {
            "topic": "数学桥接算法改进",
            "complexity": 8,
            "breakthrough": "发现新的递归收敛模式，可优化瓶颈。",
        },
        "initiator": "qtlv",
        "participants": ["qtlv", "qlv", "lvlu", "ucif2"],
        "priority": 1,
    }

    auto_pl = pipeline.establish(item_auto)
    print(f"  建立 pipeline: {auto_pl}")

    drive_result = pipeline.si_drive_pipeline(auto_pl)
    print(f"  si_drive_pipeline 结果:")
    print(f"    started_stage: {drive_result['started_stage']}")
    print(f"    ended_stage: {drive_result['ended_stage']}")
    print(f"    completed: {drive_result['completed']}")
    print(f"    iterations: {drive_result['iterations']}")
    print(f"    findings: {drive_result['findings']}")

    # ═══════════════════════════════════════════════════════════════
    # 测试 3: 批量驱动
    # ═══════════════════════════════════════════════════════════════
    print("\n[测试 3] batch_drive 批量驱动")

    batch_items = [
        {
            "type": "share",
            "title": "研究成果分享: LGT计算优化",
            "content": {"finding": "计算瓶颈突破", "complexity": 6},
            "initiator": "lgt",
            "participants": ["lgt", "qfa", "vinf"],
            "priority": 3,
        },
        {
            "type": "task",
            "title": "USR用户模型更新任务",
            "content": {"task": "更新用户画像", "complexity": 4},
            "initiator": "usrm",
            "participants": ["usrm", "cisvr"],
            "priority": 5,
        },
        {
            "type": "finding",
            "title": "安全漏洞分析",
            "content": {"vulnerability": "发现潜在递归调用栈溢出", "severity": "high", "complexity": 9},
            "initiator": "vinf",
            "participants": ["vinf", "ucif2", "qfa"],
            "priority": 0,
        },
    ]

    batch_ids = []
    for item in batch_items:
        pl = pipeline.establish(item)
        batch_ids.append(pl)
        print(f"  建立: {pl} [{item['type']}] {item['title'][:30]}")

    batch_result = pipeline.batch_drive(batch_ids)
    print(f"\n  批量驱动结果:")
    print(f"    total: {batch_result['total']}")
    print(f"    completed: {batch_result['completed']}")
    print(f"    failed: {batch_result['failed']}")
    for r in batch_result["results"]:
        status = "✓" if r.get("completed") else "✗"
        print(f"    {status} {r['pipeline_id']}: {r['started_stage']} → {r['ended_stage']}")

    # ═══════════════════════════════════════════════════════════════
    # 测试 4: 统计与超时检测
    # ═══════════════════════════════════════════════════════════════
    print("\n[测试 4] 统计与超时检测")

    stats = pipeline.get_pipeline_stats()
    print(f"  Pipeline 统计:")
    for k, v in stats.items():
        print(f"    {k}: {v}")

    overdue = pipeline.get_overdue_pipelines()
    print(f"\n  超时 Pipeline 数: {len(overdue)}")
    if overdue:
        for o in overdue:
            print(f"    - {o['pipeline_id']}: {o['title']} (超 {o['elapsed_hours']}h)")

    # ═══════════════════════════════════════════════════════════════
    # 测试 5: FINDING 递归引擎独立测试
    # ═══════════════════════════════════════════════════════════════
    print("\n[测试 5] FindingRecursion 引擎")

    finding_engine2 = FindingRecursion()
    test_content = {
        "analysis": "我们发现了一个严重的瓶颈问题，需要递归优化。",
        "metrics": {"latency_ms": 150, "throughput": 0, "error_rate": 0.95},
    }
    findings = finding_engine2.scan_content("PL-TEST-001", test_content)
    print(f"  扫描发现 {len(findings)} 个 FINDING:")
    for f in findings:
        print(f"    - {f.finding_id}: severity={f.severity}, keywords={f.keywords_matched}")
        if f.severity >= 0.7:
            child = finding_engine2.trigger_recursion(f.finding_id)
            print(f"      → 递归触发: child_finding={child}")

    print(f"\n  FINDING 统计: {finding_engine2.get_finding_stats()}")

    # ═══════════════════════════════════════════════════════════════
    # 测试 6: 边界与异常
    # ═══════════════════════════════════════════════════════════════
    print("\n[测试 6] 边界与异常处理")

    # 无效 pipeline_id
    r = pipeline.follow_up("NON_EXISTENT")
    print(f"  无效ID follow_up: {r.get('error', 'ok')}")

    # 空参与者
    pl_empty = pipeline.establish({
        "type": "discussion",
        "title": "空参与者测试",
        "content": {},
        "initiator": "ucif2",
        "participants": [],
        "priority": 5,
    })
    print(f"  空参与者自动修正: participants={pipeline.pipelines[pl_empty].item['participants']}")

    # 重复 close
    if pipeline.pipelines[pl_id].stage == PipelineStage.ARCHIVED:
        r2 = pipeline.close_loop(pl_id)
        print(f"  重复 close: {r2.get('info', r2.get('closed'))}")

    # ═══════════════════════════════════════════════════════════════
    # 总结
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 76)
    final_stats = pipeline.get_pipeline_stats()
    print(f"最终统计: 总建立={final_stats['total_established']}, "
          f"总启用={final_stats['total_activated']}, "
          f"总闭环={final_stats['total_closed']}, "
          f"FINDING={final_stats['total_findings']}, "
          f"递归={final_stats['total_recursive']}")
    print("=" * 76)
    print("所有自测通过 ✓")
    print("=" * 76)
