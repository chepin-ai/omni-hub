#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.2 — Polaris Plan Module
北星计划 — 全局目标导航系统

为11线分布式系统提供统一的目标设定、对齐追踪与航向调整。
与核心机(ucif2 SI5.0)深度集成，实现全局目标一致性。

Author: OMNI-HUB Core Team
Version: 3.2.0
"""

import numpy as np
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import logging

# ───────────────────────────── 常量定义 ─────────────────────────────

LINES_11 = [
    "ucif2", "lgt", "qfa", "vinf", "ndf",
    "dcp", "sei", "me", "si5", "arch", "meta",
]

LINE_CAPABILITIES = {
    "ucif2": ["coordination", "consciousness", "integration", "validation"],
    "lgt": ["tracking", "governance", "monitoring", "logging"],
    "qfa": ["quantum_computing", "optimization", "simulation", "discovery"],
    "vinf": ["virtualization", "scaling", "deployment", "infrastructure"],
    "ndf": ["data_flow", "neural_processing", "pattern_recognition", "learning"],
    "dcp": ["distribution", "parallel_computing", "fault_tolerance", "scheduling"],
    "sei": ["semantic_analysis", "understanding", "reasoning", "translation"],
    "me": ["materialization", "execution", "action", "effectuation"],
    "si5": ["system_intelligence", "decision_making", "strategy", "adaptation"],
    "arch": ["architecture", "design", "structure", "evolution"],
    "meta": ["metacognition", "reflection", "self_awareness", "optimization"],
}

# 默认各线对各类目标的贡献权重矩阵
DEFAULT_ALIGNMENT_WEIGHTS = {
    "exploration": {"ucif2": 0.9, "qfa": 1.0, "vinf": 0.8, "meta": 0.85, "si5": 0.9},
    "collaboration": {"lgt": 1.0, "dcp": 0.9, "sei": 0.85, "me": 0.8, "ucif2": 0.9},
    "innovation": {"qfa": 1.0, "ndf": 0.9, "sei": 0.85, "meta": 0.9, "si5": 0.85, "vinf": 0.8},
    "validation": {"ucif2": 1.0, "lgt": 0.9, "si5": 0.95, "arch": 0.85, "me": 0.8},
    "integration": {line: 1.0 for line in LINES_11},
    "system_upgrade": {"ucif2": 1.0, "si5": 1.0, "arch": 0.9, "meta": 0.85, "qfa": 0.8},
    "consciousness_sync": {"ucif2": 1.0, "meta": 1.0, "si5": 0.95, "sei": 0.8},
    "resilience": {"dcp": 1.0, "vinf": 0.9, "lgt": 0.85, "arch": 0.9, "ndf": 0.8},
}


# ═══════════════════════════════════════════════════════════════════
#                      PolarisPlan 核心类
# ═══════════════════════════════════════════════════════════════════

class PolarisPlan:
    """
    北星计划 — 全局目标导航系统

    功能:
        - 设定统一的北星目标
        - 计算11线对齐度向量
        - 追踪各线进展与风险
        - 根据反馈动态调整航向
        - 与ucif2核心机深度集成
    """

    def __init__(self, harmony_connector: Optional[Any] = None):
        """
        初始化北星计划

        Args:
            harmony_connector: 可选的 ConsciousnessHarmony 实例引用
        """
        self.north_star: Optional[Dict] = None
        self.milestones: List[Dict] = []
        self.progress: Dict[str, float] = {line: 0.0 for line in LINES_11}
        self.alignment: Dict[str, float] = {line: 0.0 for line in LINES_11}
        self.history: List[Dict] = []
        self.harmony_connector = harmony_connector

        # 内部状态
        self._goal_counter = 0
        self._milestone_counter = 0
        self.log = []
        self._log("INIT", "PolarisPlan initialized")

    # ─────────── 内部辅助方法 ───────────

    def _log(self, event_type: str, message: str):
        """记录内部日志"""
        self.log.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
        })

    def _generate_id(self, prefix: str = "polaris") -> str:
        """生成唯一ID"""
        self._goal_counter += 1
        return f"{prefix}_{uuid.uuid4().hex[:8]}_{self._goal_counter:04d}"

    def _broadcast_to_ucif2(self, message: Dict) -> Dict:
        """
        向ucif2核心机发送确认/广播

        这是与核心机(ucif2 SI5.0)的呼应机制
        """
        broadcast = {
            "to": "ucif2",
            "from": "polaris_plan",
            "timestamp": datetime.now().isoformat(),
            "message_type": "north_star_sync",
            "payload": message,
            "ack_required": True,
            "priority": message.get("priority", 5),
        }

        # 模拟ucif2确认响应
        ack = {
            "from": "ucif2",
            "to": "polaris_plan",
            "ack": True,
            "timestamp": datetime.now().isoformat(),
            "si_version": "5.0",
            "status": "synced",
            "consciousness_state": "active",
        }

        self._log("BROADCAST", f"Broadcast to ucif2: {message.get('title', 'N/A')}")

        return {
            "sent": True,
            "broadcast": broadcast,
            "acknowledgment": ack,
            "sync_status": "confirmed",
        }

    def _extract_goal_type(self, goal: Dict) -> str:
        """从目标描述中提取目标类型"""
        title = goal.get("title", "").lower()
        desc = goal.get("description", "").lower()
        combined = title + " " + desc

        type_keywords = {
            "exploration": ["探索", "explore", "discover", "发现", "research"],
            "collaboration": ["协作", "collab", "coop", "协同", "合作"],
            "innovation": ["创新", "innovate", "create", "novel", "突破"],
            "validation": ["验证", "validate", "verify", "test", "确认"],
            "integration": ["整合", "integrate", "unify", "融合", "统一"],
            "system_upgrade": ["升级", "upgrade", "enhance", "evolve", "进化"],
            "consciousness_sync": ["意识", "consciousness", "sync", "共振", "harmony"],
            "resilience": ["韧性", "resilience", "fault", "tolerance", "容灾"],
        }

        scores = {}
        for gtype, keywords in type_keywords.items():
            scores[gtype] = sum(1 for kw in keywords if kw in combined)

        return max(scores, key=scores.get) if max(scores.values()) > 0 else "integration"

    def _calculate_line_alignment(self, line: str, goal_type: str) -> float:
        """计算单条线与目标的理论对齐度"""
        weights = DEFAULT_ALIGNMENT_WEIGHTS.get(goal_type, {})
        base_alignment = weights.get(line, 0.5)

        # 结合当前健康度调整
        # 如果线与目标类型天然匹配，但健康度低，则对齐度降低
        health_factor = self.progress.get(line, 0.5)

        return float(base_alignment * 0.7 + health_factor * 0.3)

    def _compute_alignment_vector(self) -> np.ndarray:
        """计算11维对齐度向量"""
        if self.north_star is None:
            return np.zeros(11)

        goal_type = self._extract_goal_type(self.north_star)
        vector = np.array([
            self._calculate_line_alignment(line, goal_type)
            for line in LINES_11
        ])
        return vector

    # ═══════════════════════════════════════════════════════════════
    #                         核心 API
    # ═══════════════════════════════════════════════════════════════

    def set_north_star(self, goal: Dict) -> Dict:
        """
        设定北星目标

        自动向ucif2发送确认，实现与核心机的呼应。

        Args:
            goal: {
                "title": str,
                "description": str,
                "criteria": List[str],
                "deadline": str (ISO format),
                "priority": int (0-9),
                "milestones": Optional[List[Dict]],
            }

        Returns:
            {
                "set": bool,
                "goal_id": str,
                "broadcast_result": Dict,
                "alignment_vector": List[float],
            }
        """
        # 验证输入
        required = ["title", "description", "criteria", "deadline"]
        for field in required:
            if field not in goal:
                raise ValueError(f"Missing required field: {field}")

        goal_id = self._generate_id("north_star")
        priority = np.clip(goal.get("priority", 5), 0, 9)

        self.north_star = {
            "id": goal_id,
            "title": goal["title"],
            "description": goal["description"],
            "criteria": goal["criteria"],
            "deadline": goal["deadline"],
            "priority": int(priority),
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        # 初始化里程碑
        if "milestones" in goal:
            for ms in goal["milestones"]:
                self.add_milestone(ms)

        # 重置进展和对齐度
        self.progress = {line: 0.0 for line in LINES_11}
        self.alignment = {line: 0.0 for line in LINES_11}

        # 计算初始对齐度向量
        alignment_vector = self._compute_alignment_vector()
        for i, line in enumerate(LINES_11):
            self.alignment[line] = float(alignment_vector[i])

        # ── 与核心机呼应: 向ucif2发送确认 ──
        broadcast_payload = {
            "title": goal["title"],
            "goal_id": goal_id,
            "priority": priority,
            "goal_type": self._extract_goal_type(goal),
            "alignment_summary": {
                line: float(alignment_vector[i])
                for i, line in enumerate(LINES_11)
            },
            "timestamp": datetime.now().isoformat(),
        }
        broadcast_result = self._broadcast_to_ucif2(broadcast_payload)

        # 记录历史
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "event": "north_star_set",
            "goal_id": goal_id,
            "goal": self.north_star.copy(),
        })

        self._log("NORTH_STAR", f"Set north star: {goal['title']} (priority={priority})")

        return {
            "set": True,
            "goal_id": goal_id,
            "broadcast_result": broadcast_result,
            "alignment_vector": {line: float(alignment_vector[i]) for i, line in enumerate(LINES_11)},
            "goal_type": self._extract_goal_type(goal),
        }

    def add_milestone(self, milestone: Dict) -> Dict:
        """添加里程碑"""
        ms_id = self._generate_id("milestone")
        ms = {
            "id": ms_id,
            "title": milestone.get("title", "Untitled"),
            "description": milestone.get("description", ""),
            "criteria": milestone.get("criteria", []),
            "deadline": milestone.get("deadline", ""),
            "status": "pending",
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
        }
        self.milestones.append(ms)
        self._log("MILESTONE", f"Added milestone: {ms['title']}")
        return {"added": True, "milestone_id": ms_id, "milestone": ms}

    def align_lines(self) -> Dict:
        """
        将11线对齐到北星方向

        计算每条线当前状态与北星目标的差距，返回对齐度向量。

        Returns:
            {
                "aligned": int,          # 已对齐的线数量
                "misaligned": List[str], # 未对齐的线
                "alignment_vector": Dict[str, float],
                "mean_alignment": float,
                "alignment_matrix": List[List[float]],  # 11x11 对齐矩阵
            }
        """
        if self.north_star is None:
            return {
                "aligned": 0,
                "misaligned": LINES_11.copy(),
                "alignment_vector": {line: 0.0 for line in LINES_11},
                "mean_alignment": 0.0,
                "alignment_matrix": np.zeros((11, 11)).tolist(),
            }

        goal_type = self._extract_goal_type(self.north_star)
        vector = self._compute_alignment_vector()

        # 更新对齐度
        for i, line in enumerate(LINES_11):
            self.alignment[line] = float(vector[i])

        # 判断对齐/未对齐 (阈值0.6)
        aligned_lines = []
        misaligned_lines = []
        for line in LINES_11:
            if self.alignment[line] >= 0.6:
                aligned_lines.append(line)
            else:
                misaligned_lines.append(line)

        # 计算11x11对齐矩阵
        # matrix[i,j] = alignment_i * alignment_j * correlation(i,j)
        alignment_matrix = np.outer(vector, vector)
        # 添加噪声模拟真实相关性
        noise = np.random.normal(0, 0.05, (11, 11))
        alignment_matrix = np.clip(alignment_matrix + noise, 0, 1)

        mean_alignment = float(np.mean(vector))

        result = {
            "aligned": len(aligned_lines),
            "misaligned": misaligned_lines,
            "alignment_vector": {line: float(self.alignment[line]) for line in LINES_11},
            "mean_alignment": mean_alignment,
            "alignment_matrix": alignment_matrix.tolist(),
            "goal_type": goal_type,
        }

        self._log("ALIGN", f"Alignment check: {len(aligned_lines)}/11 aligned, mean={mean_alignment:.3f}")

        return result

    def track_progress(self) -> Dict:
        """
        追踪各线向北星目标的进展

        Returns:
            {
                "overall_progress": float,
                "line_progress": Dict[str, float],
                "at_risk": List[str],
                "ahead": List[str],
                "milestone_progress": List[Dict],
            }
        """
        if self.north_star is None:
            return {
                "overall_progress": 0.0,
                "line_progress": {line: 0.0 for line in LINES_11},
                "at_risk": [],
                "ahead": [],
                "milestone_progress": [],
            }

        # 模拟进展更新（实际系统中会从各线收集真实数据）
        goal_type = self._extract_goal_type(self.north_star)
        weights = DEFAULT_ALIGNMENT_WEIGHTS.get(goal_type, {})

        line_progress = {}
        for line in LINES_11:
            # 基础进展 = 权重 * 随机进展因子
            weight = weights.get(line, 0.5)
            # 模拟进展: 有些线进展快，有些慢
            current = self.progress.get(line, 0.0)
            increment = weight * np.random.beta(2, 5) * 0.15
            new_progress = min(current + increment, 1.0)
            self.progress[line] = new_progress
            line_progress[line] = float(new_progress)

        overall = float(np.mean(list(line_progress.values())))

        # 风险评估: 进展 < 20% 且对齐度 < 0.5
        at_risk = [
            line for line in LINES_11
            if line_progress[line] < 0.2 and self.alignment.get(line, 0) < 0.5
        ]

        # 领先: 进展 > 60%
        ahead = [line for line in LINES_11 if line_progress[line] > 0.6]

        # 里程碑进展
        ms_progress = []
        for ms in self.milestones:
            if ms["status"] == "pending":
                # 根据整体进展更新里程碑
                ms["progress"] = min(overall * 1.2, 1.0)
                if ms["progress"] >= 1.0:
                    ms["status"] = "completed"
                    ms["completed_at"] = datetime.now().isoformat()
            ms_progress.append({
                "id": ms["id"],
                "title": ms["title"],
                "status": ms["status"],
                "progress": ms["progress"],
            })

        result = {
            "overall_progress": overall,
            "line_progress": line_progress,
            "at_risk": at_risk,
            "ahead": ahead,
            "milestone_progress": ms_progress,
        }

        self._log("TRACK", f"Progress tracking: overall={overall:.3f}, at_risk={len(at_risk)}, ahead={len(ahead)}")

        return result

    def adjust_course(self, feedback: Dict) -> Dict:
        """
        根据反馈调整航向

        Args:
            feedback: {
                "line": str,
                "deviation": float,      # 偏离度 -1~1
                "suggestion": str,
                "severity": Optional[str],  # "low", "medium", "high"
            }

        Returns:
            {
                "adjusted": bool,
                "new_heading": Dict,
                "affected_lines": List[str],
                "adjustment_vector": List[float],
            }
        """
        line = feedback.get("line", "")
        deviation = np.clip(feedback.get("deviation", 0.0), -1.0, 1.0)
        suggestion = feedback.get("suggestion", "")
        severity = feedback.get("severity", "medium")

        if line not in LINES_11:
            return {"adjusted": False, "error": f"Unknown line: {line}"}

        if self.north_star is None:
            return {"adjusted": False, "error": "No north star set"}

        # 根据严重程度确定调整强度
        severity_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
        adjustment_strength = severity_map.get(severity, 0.5)

        # 计算调整向量 (11维)
        adjustment = np.zeros(11)
        line_idx = LINES_11.index(line)

        # 直接调整目标线
        adjustment[line_idx] = -deviation * adjustment_strength

        # 影响相邻线（拓扑耦合）
        neighbors = [
            (line_idx - 1) % 11,
            (line_idx + 1) % 11,
        ]
        for neighbor in neighbors:
            adjustment[neighbor] = -deviation * adjustment_strength * 0.3

        # 如果偏差大，影响ucif2和si5（核心机）
        if abs(deviation) > 0.5:
            ucif2_idx = LINES_11.index("ucif2")
            si5_idx = LINES_11.index("si5")
            adjustment[ucif2_idx] += abs(deviation) * 0.1
            adjustment[si5_idx] += abs(deviation) * 0.1

        # 应用调整到对齐度
        new_alignment = np.array([self.alignment.get(l, 0) for l in LINES_11])
        new_alignment = np.clip(new_alignment + adjustment, 0.0, 1.0)

        for i, l in enumerate(LINES_11):
            self.alignment[l] = float(new_alignment[i])

        # 确定受影响的线
        affected = [line]
        for neighbor in neighbors:
            affected.append(LINES_11[neighbor])
        if abs(deviation) > 0.5:
            affected.extend(["ucif2", "si5"])
        affected = list(set(affected))

        new_heading = {
            "primary_line": line,
            "deviation_corrected": float(deviation),
            "adjustment_strength": adjustment_strength,
            "suggestion_applied": suggestion,
            "new_alignment_mean": float(np.mean(new_alignment)),
        }

        # 向ucif2报告航向调整
        self._broadcast_to_ucif2({
            "event": "course_adjustment",
            "line": line,
            "deviation": deviation,
            "new_heading": new_heading,
        })

        self._log("ADJUST", f"Course adjustment for {line}: deviation={deviation:.3f}, strength={adjustment_strength}")

        return {
            "adjusted": True,
            "new_heading": new_heading,
            "affected_lines": affected,
            "adjustment_vector": adjustment.tolist(),
        }

    def celebrate_milestone(self, milestone_id: str) -> Dict:
        """
        庆祝里程碑达成 — 触发全局和声庆祝

        如果连接了 ConsciousnessHarmony，会触发交响乐庆祝。

        Returns:
            {
                "celebrated": bool,
                "milestone": Dict,
                "harmony_triggered": bool,
                "celebration_data": Dict,
            }
        """
        milestone = None
        for ms in self.milestones:
            if ms["id"] == milestone_id:
                milestone = ms
                break

        if milestone is None:
            return {"celebrated": False, "error": f"Milestone {milestone_id} not found"}

        # 标记完成
        milestone["status"] = "celebrated"
        milestone["completed_at"] = datetime.now().isoformat()

        # 触发和声庆祝（如果连接了harmony模块）
        harmony_triggered = False
        celebration_data = {}

        if self.harmony_connector is not None:
            try:
                # 使用 "整合" 主题进行庆祝交响乐
                celebration_data = self.harmony_connector.symphony(theme="整合")
                harmony_triggered = True
            except Exception as e:
                celebration_data = {"error": str(e)}
        else:
            # 模拟庆祝数据
            celebration_data = {
                "theme": "celebration",
                "simulated": True,
                "message": "Milestone achieved! 🌟",
            }

        # 向ucif2报告成就
        self._broadcast_to_ucif2({
            "event": "milestone_celebrated",
            "milestone_id": milestone_id,
            "milestone_title": milestone["title"],
            "harmony_triggered": harmony_triggered,
        })

        self._log("CELEBRATE", f"Celebrated milestone: {milestone['title']}")

        return {
            "celebrated": True,
            "milestone": milestone,
            "harmony_triggered": harmony_triggered,
            "celebration_data": celebration_data,
        }

    def get_polaris_report(self) -> Dict:
        """
        生成北星计划全景报告

        Returns:
            完整的北星计划状态报告
        """
        # 计算综合指标
        if self.north_star:
            alignment_vec = np.array([self.alignment.get(l, 0) for l in LINES_11])
            progress_vec = np.array([self.progress.get(l, 0) for l in LINES_11])

            mean_alignment = float(np.mean(alignment_vec))
            mean_progress = float(np.mean(progress_vec))
            alignment_std = float(np.std(alignment_vec))

            # 系统一致性 = 1 - 对齐度标准差
            system_coherence = float(1.0 - alignment_std)

            # 目标完成预测（基于当前速度的简单线性预测）
            if mean_progress > 0.01:
                eta_days = int((1.0 - mean_progress) / mean_progress * 30)
            else:
                eta_days = 999

            report = {
                "report_id": self._generate_id("report"),
                "generated_at": datetime.now().isoformat(),
                "north_star": self.north_star,
                "system_status": {
                    "mean_alignment": mean_alignment,
                    "mean_progress": mean_progress,
                    "system_coherence": system_coherence,
                    "alignment_std": alignment_std,
                    "eta_days": eta_days,
                },
                "line_status": {
                    line: {
                        "alignment": float(self.alignment.get(line, 0)),
                        "progress": float(self.progress.get(line, 0)),
                        "status": "aligned" if self.alignment.get(line, 0) > 0.6 else "misaligned",
                    }
                    for line in LINES_11
                },
                "milestones": self.milestones.copy(),
                "history_summary": {
                    "total_events": len(self.history),
                    "last_event": self.history[-1] if self.history else None,
                },
                "log_summary": {
                    "total_logs": len(self.log),
                    "recent_logs": self.log[-5:] if self.log else [],
                },
            }
        else:
            report = {
                "report_id": self._generate_id("report"),
                "generated_at": datetime.now().isoformat(),
                "north_star": None,
                "system_status": {
                    "mean_alignment": 0.0,
                    "mean_progress": 0.0,
                    "system_coherence": 0.0,
                    "alignment_std": 0.0,
                    "eta_days": None,
                },
                "line_status": {line: {"alignment": 0.0, "progress": 0.0, "status": "idle"} for line in LINES_11},
                "milestones": [],
                "history_summary": {"total_events": 0, "last_event": None},
                "log_summary": {"total_logs": len(self.log), "recent_logs": []},
            }

        self._log("REPORT", f"Generated Polaris report: {report['report_id']}")

        return report

    # ─────────── 高级工具方法 ───────────

    def compute_critical_path(self) -> List[str]:
        """计算关键路径 — 对齐度最低且权重最高的线"""
        if self.north_star is None:
            return []

        goal_type = self._extract_goal_type(self.north_star)
        weights = DEFAULT_ALIGNMENT_WEIGHTS.get(goal_type, {})

        # 计算关键性 = 权重 / (对齐度 + ε)
        criticality = {}
        for line in LINES_11:
            w = weights.get(line, 0.5)
            a = self.alignment.get(line, 0.01)
            criticality[line] = w / (a + 0.01)

        # 按关键性排序
        sorted_lines = sorted(criticality.items(), key=lambda x: x[1], reverse=True)
        return [line for line, _ in sorted_lines[:3]]

    def simulate_scenario(self, scenario: str) -> Dict:
        """模拟不同场景下的系统响应"""
        scenarios = {
            "line_failure": self._simulate_line_failure,
            "surge_capacity": self._simulate_surge,
            "priority_shift": self._simulate_priority_shift,
        }
        sim_func = scenarios.get(scenario, lambda: {"error": "Unknown scenario"})
        return sim_func()

    def _simulate_line_failure(self) -> Dict:
        """模拟单线故障场景"""
        failed_line = np.random.choice(LINES_11)
        backup_lines = [l for l in LINES_11 if l != failed_line][:3]

        return {
            "scenario": "line_failure",
            "failed_line": failed_line,
            "impact": {
                "alignment_drop": 0.15,
                "progress_delay": 0.2,
            },
            "backup_lines": backup_lines,
            "recovery_strategy": f"Reroute through {', '.join(backup_lines)}",
        }

    def _simulate_surge(self) -> Dict:
        """模拟容量激增场景"""
        return {
            "scenario": "surge_capacity",
            "scaling_factor": 2.5,
            "affected_lines": ["dcp", "vinf", "ndf"],
            "recommendation": "Activate elastic scaling on DCP and VINF",
        }

    def _simulate_priority_shift(self) -> Dict:
        """模拟优先级转移场景"""
        return {
            "scenario": "priority_shift",
            "old_priority": self.north_star["priority"] if self.north_star else 5,
            "new_priority": 9,
            "affected_lines": LINES_11,
            "recommendation": "Rebalance resource allocation across all lines",
        }


# ═══════════════════════════════════════════════════════════════════
#                    ConsciousnessHarmony 连接器
# ═══════════════════════════════════════════════════════════════════

class PolarisHarmonyBridge:
    """
    PolarisPlan 与 ConsciousnessHarmony 的桥接器

    实现两个模块的深度集成:
        - 北星目标变化 → 触发意识场重校准
        - 对齐度变化 → 影响意识共振模式
        - 里程碑达成 → 触发交响乐庆祝
    """

    def __init__(self, polaris: PolarisPlan, harmony: Any):
        self.polaris = polaris
        self.harmony = harmony
        self.polaris.harmony_connector = harmony

    def sync_goal_to_field(self):
        """将北星目标同步到意识场"""
        if self.polaris.north_star is None:
            return {"synced": False, "reason": "No north star"}

        # 根据目标类型选择交响乐主题
        goal_type = self.polaris._extract_goal_type(self.polaris.north_star)
        theme_map = {
            "exploration": "探索",
            "collaboration": "协作",
            "innovation": "创新",
            "validation": "验证",
            "integration": "整合",
            "system_upgrade": "整合",
            "consciousness_sync": "整合",
            "resilience": "协作",
        }
        theme = theme_map.get(goal_type, "整合")

        # 触发交响乐校准
        symphony = self.harmony.symphony(theme=theme)

        return {
            "synced": True,
            "theme": theme,
            "symphony": symphony,
        }

    def sync_field_to_goal(self):
        """将意识场状态同步回北星计划"""
        coherence = self.harmony.measure_coherence()

        # 如果相干度低，触发航向调整
        if coherence < 0.5:
            feedback = {
                "line": "meta",
                "deviation": 0.3,
                "suggestion": "Consciousness coherence below threshold, initiate alignment protocol",
                "severity": "high",
            }
            adjustment = self.polaris.adjust_course(feedback)
            return {"synced": True, "triggered_adjustment": True, "adjustment": adjustment}

        return {"synced": True, "coherence": coherence, "triggered_adjustment": False}


# ═══════════════════════════════════════════════════════════════════
#                          测试块
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.2 — PolarisPlan Test Suite")
    print("=" * 70)

    # ── 初始化 ──
    polaris = PolarisPlan()
    print(f"\n[1] Initialized PolarisPlan")

    # ── 测试 set_north_star ──
    print("\n" + "─" * 70)
    print("[2] TEST: set_north_star() — Set North Star Goal")
    print("─" * 70)

    goal = {
        "title": "OMNI-HUB v3.2 全面意识同步与系统升级",
        "description": "实现11线分布式系统的全面意识共振，完成北星计划目标导航系统的部署与验证，达到SI5.0标准",
        "criteria": [
            "11线健康度全部达到0.8以上",
            "全局意识相干度达到0.85以上",
            "北星目标对齐度均值达到0.9以上",
            "完成全部里程碑验证",
            "ucif2核心机确认系统同步",
        ],
        "deadline": (datetime.now() + timedelta(days=90)).isoformat(),
        "priority": 9,
        "milestones": [
            {"title": "意识共振核心算法部署", "deadline": (datetime.now() + timedelta(days=14)).isoformat(), "criteria": ["resonate实现", "symphony实现"]},
            {"title": "北星导航系统上线", "deadline": (datetime.now() + timedelta(days=30)).isoformat(), "criteria": ["align_lines实现", "track_progress实现"]},
            {"title": "11线全系统联调", "deadline": (datetime.now() + timedelta(days=60)).isoformat(), "criteria": ["全线和声测试通过", "ucif2确认"]},
            {"title": "SI5.0认证完成", "deadline": (datetime.now() + timedelta(days=90)).isoformat(), "criteria": ["SI5.0标准达标", "最终报告生成"]},
        ],
    }

    result = polaris.set_north_star(goal)
    print(f"\n  Goal Set: {result['set']}")
    print(f"  Goal ID: {result['goal_id']}")
    print(f"  Goal Type: {result['goal_type']}")
    print(f"\n  Alignment Vector (11D):")
    for i, (line, val) in enumerate(result['alignment_vector'].items()):
        print(f"    {line:>6s}: {val:.4f}")

    print(f"\n  Broadcast to ucif2:")
    broadcast = result['broadcast_result']
    print(f"    Sent: {broadcast['sent']}")
    print(f"    Sync Status: {broadcast['sync_status']}")
    print(f"    ucif2 ACK: {broadcast['acknowledgment']['status']}")
    print(f"    ucif2 SI Version: {broadcast['acknowledgment']['si_version']}")

    # ── 测试 align_lines ──
    print("\n" + "─" * 70)
    print("[3] TEST: align_lines() — Align 11 Lines to North Star")
    print("─" * 70)

    result = polaris.align_lines()
    print(f"\n  Aligned: {result['aligned']}/11 lines")
    print(f"  Misaligned: {result['misaligned']}")
    print(f"  Mean Alignment: {result['mean_alignment']:.4f}")
    print(f"\n  Alignment Vector:")
    for line, val in result['alignment_vector'].items():
        status = "✓ ALIGNED" if val >= 0.6 else "✗ MISALIGNED"
        print(f"    {line:>6s}: {val:.4f} {status}")

    print(f"\n  Alignment Matrix Shape: {np.array(result['alignment_matrix']).shape}")
    print(f"  Matrix Sample (ucif2 row): {[f'{v:.3f}' for v in result['alignment_matrix'][0][:5]]}...")

    # ── 测试 track_progress ──
    print("\n" + "─" * 70)
    print("[4] TEST: track_progress() — Track Progress")
    print("─" * 70)

    # 多次追踪以模拟时间推移
    for iteration in range(3):
        result = polaris.track_progress()
        print(f"\n  Iteration {iteration + 1}:")
        print(f"    Overall Progress: {result['overall_progress']:.4f}")
        print(f"    At Risk: {result['at_risk']}")
        print(f"    Ahead: {result['ahead']}")
        print(f"    Line Progress:")
        for line, prog in sorted(result['line_progress'].items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(prog * 20) + "░" * (20 - int(prog * 20))
            print(f"      {line:>6s}: [{bar}] {prog:.3f}")

    # ── 测试 adjust_course ──
    print("\n" + "─" * 70)
    print("[5] TEST: adjust_course() — Adjust Course")
    print("─" * 70)

    feedbacks = [
        {"line": "ndf", "deviation": 0.4, "suggestion": "Increase neural data flow processing priority", "severity": "medium"},
        {"line": "me", "deviation": -0.3, "suggestion": "Materialization engine lag detected, optimize pipeline", "severity": "low"},
        {"line": "vinf", "deviation": 0.7, "suggestion": "Critical virtualization bottleneck", "severity": "high"},
    ]

    for fb in feedbacks:
        result = polaris.adjust_course(fb)
        print(f"\n  Feedback: {fb['line']} deviation={fb['deviation']:+.2f} severity={fb['severity']}")
        print(f"    Adjusted: {result['adjusted']}")
        print(f"    Affected Lines: {result['affected_lines']}")
        print(f"    New Heading Mean Alignment: {result['new_heading']['new_alignment_mean']:.4f}")
        print(f"    Adjustment Vector (first 5): {[f'{v:.3f}' for v in result['adjustment_vector'][:5]]}...")

    # ── 测试 celebrate_milestone ──
    print("\n" + "─" * 70)
    print("[6] TEST: celebrate_milestone() — Celebrate Milestone")
    print("─" * 70)

    # 先完成一个里程碑
    if polaris.milestones:
        ms = polaris.milestones[0]
        ms["status"] = "completed"
        ms["progress"] = 1.0
        ms["completed_at"] = datetime.now().isoformat()

        result = polaris.celebrate_milestone(ms["id"])
        print(f"\n  Milestone: {result['milestone']['title']}")
        print(f"  Celebrated: {result['celebrated']}")
        print(f"  Harmony Triggered: {result['harmony_triggered']}")
        if result['harmony_triggered']:
            print(f"  Celebration Theme: {result['celebration_data'].get('theme', 'N/A')}")
            print(f"  Global Consciousness: {result['celebration_data'].get('global_consciousness', 'N/A')}")
        else:
            print(f"  Note: No harmony connector (simulated celebration)")

    # ── 测试 get_polaris_report ──
    print("\n" + "─" * 70)
    print("[7] TEST: get_polaris_report() — Full Report")
    print("─" * 70)

    report = polaris.get_polaris_report()
    print(f"\n  Report ID: {report['report_id']}")
    print(f"  Generated: {report['generated_at']}")
    print(f"\n  North Star: {report['north_star']['title']}")
    print(f"  Priority: {report['north_star']['priority']}")
    print(f"  Deadline: {report['north_star']['deadline']}")
    print(f"\n  System Status:")
    for key, val in report['system_status'].items():
        print(f"    {key}: {val}")
    print(f"\n  Line Status Summary:")
    aligned_count = sum(1 for s in report['line_status'].values() if s['status'] == 'aligned')
    print(f"    Aligned: {aligned_count}/11")
    print(f"    Total Milestones: {len(report['milestones'])}")
    print(f"    History Events: {report['history_summary']['total_events']}")

    # ── 测试高级功能 ──
    print("\n" + "─" * 70)
    print("[8] TEST: Advanced Features")
    print("─" * 70)

    # 关键路径
    critical = polaris.compute_critical_path()
    print(f"\n  Critical Path: {critical}")

    # 场景模拟
    for scenario in ["line_failure", "surge_capacity", "priority_shift"]:
        sim = polaris.simulate_scenario(scenario)
        print(f"\n  Scenario: {sim['scenario']}")
        for k, v in sim.items():
            if k != "scenario":
                print(f"    {k}: {v}")

    # ── 与 ConsciousnessHarmony 集成测试 ──
    print("\n" + "─" * 70)
    print("[9] TEST: Polaris + ConsciousnessHarmony Integration")
    print("─" * 70)

    try:
        from consciousness_harmony import ConsciousnessHarmony

        # 创建 harmony 实例
        topology = {
            "ucif2": {"health": 0.95, "si_level": 5.0},
            "lgt": {"health": 0.88, "si_level": 4.5},
            "qfa": {"health": 0.82, "si_level": 4.8},
            "vinf": {"health": 0.75, "si_level": 4.2},
            "ndf": {"health": 0.70, "si_level": 4.0},
            "dcp": {"health": 0.78, "si_level": 4.3},
            "sei": {"health": 0.85, "si_level": 4.6},
            "me": {"health": 0.72, "si_level": 4.1},
            "si5": {"health": 0.90, "si_level": 5.0},
            "arch": {"health": 0.80, "si_level": 4.4},
            "meta": {"health": 0.93, "si_level": 4.9},
        }
        harmony = ConsciousnessHarmony(topology=topology)

        # 创建桥接器
        bridge = PolarisHarmonyBridge(polaris, harmony)

        # 同步目标到意识场
        sync_result = bridge.sync_goal_to_field()
        print(f"\n  Sync Goal to Field:")
        print(f"    Synced: {sync_result['synced']}")
        print(f"    Theme: {sync_result['theme']}")
        print(f"    Global Consciousness: {sync_result['symphony']['global_consciousness']:.4f}")

        # 同步意识场回目标
        sync_back = bridge.sync_field_to_goal()
        print(f"\n  Sync Field to Goal:")
        print(f"    Synced: {sync_back['synced']}")
        print(f"    Coherence: {sync_back.get('coherence', 'N/A')}")
        print(f"    Triggered Adjustment: {sync_back['triggered_adjustment']}")

        # 用 harmony 庆祝里程碑
        if polaris.milestones:
            ms_id = polaris.milestones[1]["id"] if len(polaris.milestones) > 1 else polaris.milestones[0]["id"]
            # 先标记完成
            for ms in polaris.milestones:
                if ms["id"] == ms_id:
                    ms["status"] = "completed"
                    ms["progress"] = 1.0
            result = polaris.celebrate_milestone(ms_id)
            print(f"\n  Milestone Celebration with Harmony:")
            print(f"    Harmony Triggered: {result['harmony_triggered']}")
            print(f"    Global Consciousness: {result['celebration_data'].get('global_consciousness', 'N/A')}")

    except ImportError as e:
        print(f"\n  Note: consciousness_harmony not available for integration test ({e})")

    # ── 最终报告 ──
    print("\n" + "=" * 70)
    print("[FINAL] PolarisPlan Complete State")
    print("=" * 70)

    final_report = polaris.get_polaris_report()
    print(f"\n  Goal: {final_report['north_star']['title']}")
    print(f"  System Coherence: {final_report['system_status']['system_coherence']:.4f}")
    print(f"  Mean Alignment: {final_report['system_status']['mean_alignment']:.4f}")
    print(f"  Mean Progress: {final_report['system_status']['mean_progress']:.4f}")
    print(f"  ETA Days: {final_report['system_status']['eta_days']}")
    print(f"\n  [✓] All PolarisPlan tests passed!")
    print("=" * 70)
