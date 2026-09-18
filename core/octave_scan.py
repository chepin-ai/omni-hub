#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
octave_scan.py — OMNI-HUB v3.2 八面轮扫引擎
8维度全局扫描引擎，支撑11线分布式系统的实时监控与异常检测。

维度总览:
  1. board_diff       — 板面差集（当前board与上一beat的差异分析）
  2. hub_tower_peak   — 毂塔尖（hub/tower/spine层级尖峰监控）
  3. receipt_peak     — 各线仓receipts尖（各线任务仓回执监控）
  4. water_level      — 水位双家差（双系统水位差异追踪）
  5. nonce_registry   — NONCE专册（nonce专用注册表状态）
  6. thread_peak      — 讨论室threads尖（讨论室线程活跃度尖峰）
  7. qset_peak        — QSET庭尖（QSET队列状态监控）
  8. w12t_state       — W12t进程态（W12t进程状态扫描）
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging


@dataclass
class Topology:
    """11线分布式系统拓扑结构"""

    lines: List[str] = field(default_factory=lambda: [
        "alpha", "beta", "gamma", "delta",
        "epsilon", "zeta", "eta", "theta",
        "iota", "kappa", "lambda"
    ])
    hubs: List[str] = field(default_factory=lambda: ["hub_0", "hub_1"])
    towers: List[str] = field(default_factory=lambda: ["tower_a", "tower_b"])
    spines: List[str] = field(default_factory=lambda: ["spine_main", "spine_backup"])

    def to_dict(self) -> dict:
        return {
            "lines": self.lines,
            "hubs": self.hubs,
            "towers": self.towers,
            "spines": self.spines,
            "total_nodes": len(self.lines) + len(self.hubs) + len(self.towers) + len(self.spines)
        }


class OctaveScan:
    """八面轮扫 — 8维度全局扫描引擎"""

    DIMENSIONS = {
        "board_diff": "板面差集 — 当前board与上一beat的差异分析",
        "hub_tower_peak": "毂塔尖 — hub/tower/spine层级尖峰监控",
        "receipt_peak": "各线仓receipts尖 — 各线任务仓回执监控",
        "water_level": "水位双家差 — 双系统水位差异追踪",
        "nonce_registry": "NONCE专册 — nonce专用注册表状态",
        "thread_peak": "讨论室threads尖 — 讨论室线程活跃度尖峰",
        "qset_peak": "QSET庭尖 — QSET队列状态监控",
        "w12t_state": "W12t进程态 — W12t进程状态扫描",
    }

    THRESHOLDS = {
        "board_diff": 0.1,       # 差异超过10%告警
        "hub_tower_peak": 0.95,  # 健康度超过0.95为尖峰
        "receipt_peak": 5,       # 未处理回执超过5个告警
        "water_level": 0.2,      # 水位差异超过20%告警
        "nonce_registry": 100,   # nonce超过100个告警
        "thread_peak": 10,       # 线程超过10个告警
        "qset_peak": 20,         # QSET队列超过20告警
        "w12t_state": "error",   # 进程状态为error告警
    }

    # 维度到优先处理线的映射
    DIMENSION_LINE_ROUTING = {
        "board_diff": ["alpha", "beta"],
        "hub_tower_peak": ["gamma", "delta"],
        "receipt_peak": ["epsilon", "zeta", "eta"],
        "water_level": ["theta", "iota"],
        "nonce_registry": ["kappa"],
        "thread_peak": ["lambda", "alpha"],
        "qset_peak": ["beta", "gamma"],
        "w12t_state": ["delta", "epsilon"],
    }

    def __init__(self, topology: Optional[Topology] = None, state_path: str = "/tmp/omni_hub_state"):
        self.topo = topology or Topology()
        self.state_path = Path(state_path)
        self.state_path.mkdir(parents=True, exist_ok=True)
        self.last_scan: Optional[dict] = None
        self.scan_history: List[dict] = []
        self._board_snapshot: Optional[str] = None
        self._state_cache: Dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    #  主扫描入口
    # ------------------------------------------------------------------ #
    def scan_all(self) -> dict:
        """执行8维度全扫描

        返回: {
            "timestamp": str,
            "dimensions": dict,
            "anomalies": list,
            "overall_health": float,
            "recommendations": list
        }
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        dimensions = {}

        for dim in self.DIMENSIONS:
            dimensions[dim] = self.scan_dimension(dim)

        anomalies = self.detect_anomaly(dimensions)
        overall_health = self._compute_overall_health(dimensions)
        recommendations = self._generate_recommendations(dimensions, anomalies)

        scan_result = {
            "timestamp": timestamp,
            "dimensions": dimensions,
            "anomalies": anomalies,
            "overall_health": overall_health,
            "recommendations": recommendations,
            "scan_id": str(uuid.uuid4())[:8],
        }

        # 持久化
        self._persist_scan(scan_result)
        self.last_scan = scan_result
        self.scan_history.append(scan_result)
        if len(self.scan_history) > 1000:
            self.scan_history = self.scan_history[-1000:]

        return scan_result

    # ------------------------------------------------------------------ #
    #  单维度扫描（每个维度返回不同数据结构）
    # ------------------------------------------------------------------ #
    def scan_dimension(self, dim: str) -> dict:
        """单维度扫描

        dim: board_diff | hub_tower_peak | receipt_peak | water_level |
             nonce_registry | thread_peak | qset_peak | w12t_state

        返回: {"dimension": str, "value": float, "threshold": float,
                "status": "normal|warning|critical", "details": dict}
        """
        if dim not in self.DIMENSIONS:
            raise ValueError(f"Unknown dimension: {dim}")

        scanner = getattr(self, f"_scan_{dim}")
        return scanner()

    def _scan_board_diff(self) -> dict:
        """1. 板面差集 — 当前board与上一beat的差异分析

        返回差异率 (0.0~1.0) 及差异详情
        """
        current_board = self._get_current_board()
        current_hash = hashlib.sha256(
            json.dumps(current_board, sort_keys=True).encode()
        ).hexdigest()

        if self._board_snapshot is None:
            self._board_snapshot = current_hash
            value = 0.0
            details = {
                "previous_hash": None,
                "current_hash": current_hash,
                "diff_fields": [],
                "message": "初始beat，无历史对比",
            }
        else:
            prev_board = self._get_previous_board()
            diff_fields, diff_rate = self._compute_board_diff(prev_board, current_board)
            value = diff_rate
            details = {
                "previous_hash": self._board_snapshot,
                "current_hash": current_hash,
                "diff_fields": diff_fields,
                "diff_count": len(diff_fields),
                "board_size": len(current_board),
            }
            self._board_snapshot = current_hash

        threshold = self.THRESHOLDS["board_diff"]
        status = self._status_from_numeric(value, threshold, invert=False)

        return {
            "dimension": "board_diff",
            "value": round(value, 4),
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    def _scan_hub_tower_peak(self) -> dict:
        """2. 毂塔尖 — hub/tower/spine层级尖峰监控

        返回各层级的健康度峰值 (0.0~1.0)
        """
        hub_health = {h: self._node_health(h, "hub") for h in self.topo.hubs}
        tower_health = {t: self._node_health(t, "tower") for t in self.topo.towers}
        spine_health = {s: self._node_health(s, "spine") for s in self.topo.spines}

        all_health = list(hub_health.values()) + list(tower_health.values()) + list(spine_health.values())
        peak_value = max(all_health) if all_health else 0.0
        avg_value = sum(all_health) / len(all_health) if all_health else 0.0

        threshold = self.THRESHOLDS["hub_tower_peak"]
        # hub_tower_peak: 超过阈值是异常（过高表示尖峰负载）
        status = self._status_from_numeric(peak_value, threshold, invert=False)

        details = {
            "hub_health": hub_health,
            "tower_health": tower_health,
            "spine_health": spine_health,
            "peak_value": round(peak_value, 4),
            "avg_value": round(avg_value, 4),
            "layers_checked": 3,
            "nodes_checked": len(all_health),
        }

        return {
            "dimension": "hub_tower_peak",
            "value": round(peak_value, 4),
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    def _scan_receipt_peak(self) -> dict:
        """3. 各线仓receipts尖 — 各线任务仓回执监控

        返回各线未处理回执数量及峰值线
        """
        receipts = {line: self._get_unprocessed_receipts(line) for line in self.topo.lines}
        peak_value = max(receipts.values()) if receipts else 0
        total = sum(receipts.values())
        peak_lines = [ln for ln, cnt in receipts.items() if cnt == peak_value and cnt > 0]

        threshold = self.THRESHOLDS["receipt_peak"]
        status = self._status_from_numeric(peak_value, threshold, invert=False)

        details = {
            "line_receipts": receipts,
            "total_unprocessed": total,
            "peak_lines": peak_lines,
            "lines_checked": len(self.topo.lines),
        }

        return {
            "dimension": "receipt_peak",
            "value": peak_value,
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    def _scan_water_level(self) -> dict:
        """4. 水位双家差 — 双系统水位差异追踪

        返回双系统（A/B）水位差异率
        """
        level_a = self._get_water_level("system_a")
        level_b = self._get_water_level("system_b")

        if max(level_a, level_b) == 0:
            diff_rate = 0.0
        else:
            diff_rate = abs(level_a - level_b) / max(level_a, level_b)

        threshold = self.THRESHOLDS["water_level"]
        status = self._status_from_numeric(diff_rate, threshold, invert=False)

        details = {
            "system_a_level": round(level_a, 4),
            "system_b_level": round(level_b, 4),
            "abs_diff": round(abs(level_a - level_b), 4),
            "diff_rate": round(diff_rate, 4),
            "sync_status": "synced" if diff_rate < 0.05 else "drifting",
        }

        return {
            "dimension": "water_level",
            "value": round(diff_rate, 4),
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    def _scan_nonce_registry(self) -> dict:
        """5. NONCE专册 — nonce专用注册表状态

        返回nonce注册表条目数及增长速率
        """
        nonce_count = self._get_nonce_count()
        growth_rate = self._get_nonce_growth_rate()
        duplicates = self._get_nonce_duplicates()

        threshold = self.THRESHOLDS["nonce_registry"]
        status = self._status_from_numeric(nonce_count, threshold, invert=False)

        details = {
            "nonce_count": nonce_count,
            "growth_rate_per_hour": round(growth_rate, 2),
            "duplicate_count": len(duplicates),
            "duplicates": duplicates[:10],  # 仅显示前10个
            "registry_capacity": 10000,
            "usage_rate": round(nonce_count / 10000, 4),
        }

        return {
            "dimension": "nonce_registry",
            "value": nonce_count,
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    def _scan_thread_peak(self) -> dict:
        """6. 讨论室threads尖 — 讨论室线程活跃度尖峰

        返回各讨论空间活跃线程数
        """
        spaces = ["discussion_room", "bulletin_board", "hall", "wild_ask"]
        threads = {sp: self._get_active_threads(sp) for sp in spaces}
        peak_value = max(threads.values()) if threads else 0
        total = sum(threads.values())

        threshold = self.THRESHOLDS["thread_peak"]
        status = self._status_from_numeric(peak_value, threshold, invert=False)

        details = {
            "space_threads": threads,
            "total_active": total,
            "peak_space": max(threads, key=threads.get) if threads else None,
            "spaces_checked": len(spaces),
        }

        return {
            "dimension": "thread_peak",
            "value": peak_value,
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    def _scan_qset_peak(self) -> dict:
        """7. QSET庭尖 — QSET队列状态监控

        返回各线QSET队列深度
        """
        qsets = {line: self._get_qset_depth(line) for line in self.topo.lines}
        peak_value = max(qsets.values()) if qsets else 0
        total = sum(qsets.values())
        congested_lines = [ln for ln, d in qsets.items() if d >= self.THRESHOLDS["qset_peak"]]

        threshold = self.THRESHOLDS["qset_peak"]
        status = self._status_from_numeric(peak_value, threshold, invert=False)

        details = {
            "line_qset": qsets,
            "total_depth": total,
            "congested_lines": congested_lines,
            "lines_checked": len(self.topo.lines),
        }

        return {
            "dimension": "qset_peak",
            "value": peak_value,
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    def _scan_w12t_state(self) -> dict:
        """8. W12t进程态 — W12t进程状态扫描

        返回W12t进程状态枚举值
        """
        processes = self._get_w12t_processes()
        error_procs = [p for p in processes if p["status"] == "error"]
        warning_procs = [p for p in processes if p["status"] == "warning"]
        ok_procs = [p for p in processes if p["status"] == "ok"]

        threshold = self.THRESHOLDS["w12t_state"]
        # w12t_state: 字符串阈值，匹配即为异常
        if error_procs:
            status = "critical"
        elif warning_procs:
            status = "warning"
        else:
            status = "normal"

        value = len(error_procs) + len(warning_procs) * 0.5

        details = {
            "processes": processes,
            "ok_count": len(ok_procs),
            "warning_count": len(warning_procs),
            "error_count": len(error_procs),
            "total_processes": len(processes),
            "error_details": [p["name"] for p in error_procs],
        }

        return {
            "dimension": "w12t_state",
            "value": value,
            "threshold": threshold,
            "status": status,
            "details": details,
        }

    # ------------------------------------------------------------------ #
    #  异常检测
    # ------------------------------------------------------------------ #
    def detect_anomaly(self, scan_result: dict) -> List[dict]:
        """异常检测

        返回异常列表: [
            {"dimension": str, "severity": "warning|critical",
             "value": float, "threshold": float, "suggestion": str}, ...
        ]
        """
        anomalies = []

        # 如果传入的是全扫描结果，提取 dimensions
        if "dimensions" in scan_result:
            dimensions = scan_result["dimensions"]
        else:
            dimensions = scan_result

        for dim, result in dimensions.items():
            status = result.get("status", "normal")
            if status == "normal":
                continue

            severity = status  # warning | critical
            value = result["value"]
            threshold = result["threshold"]
            suggestion = self._suggest_for_dimension(dim, value, threshold, result.get("details", {}))

            anomalies.append({
                "dimension": dim,
                "severity": severity,
                "value": value,
                "threshold": threshold,
                "suggestion": suggestion,
            })

        # 按严重性排序：critical 在前
        anomalies.sort(key=lambda a: 0 if a["severity"] == "critical" else 1)
        return anomalies

    # ------------------------------------------------------------------ #
    #  告警生成与路由
    # ------------------------------------------------------------------ #
    def generate_alert(self, anomalies: List[dict]) -> dict:
        """生成告警并路由到对应线

        根据异常类型路由到最相关的线处理
        """
        if not anomalies:
            return {
                "alert_id": str(uuid.uuid4())[:8],
                "level": "none",
                "routed_lines": [],
                "messages": [],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            }

        # 确定整体告警级别
        has_critical = any(a["severity"] == "critical" for a in anomalies)
        level = "critical" if has_critical else "warning"

        # 路由到相关线
        routed_lines = set()
        messages = []
        for anomaly in anomalies:
            dim = anomaly["dimension"]
            target_lines = self.DIMENSION_LINE_ROUTING.get(dim, ["alpha"])
            for line in target_lines:
                routed_lines.add(line)
            messages.append({
                "dimension": dim,
                "severity": anomaly["severity"],
                "target_lines": target_lines,
                "content": anomaly["suggestion"],
            })

        return {
            "alert_id": str(uuid.uuid4())[:8],
            "level": level,
            "anomaly_count": len(anomalies),
            "routed_lines": sorted(list(routed_lines)),
            "messages": messages,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        }

    # ------------------------------------------------------------------ #
    #  Beat 比较
    # ------------------------------------------------------------------ #
    def compare_beats(self, current: dict, previous: dict) -> dict:
        """比较两个beat的差异"""
        if not previous or not current:
            return {
                "comparison_id": str(uuid.uuid4())[:8],
                "has_previous": bool(previous),
                "diff_summary": "无法比较：数据缺失",
                "dimension_changes": {},
            }

        changes = {}
        for dim in self.DIMENSIONS:
            curr_val = current.get("dimensions", {}).get(dim, {}).get("value")
            prev_val = previous.get("dimensions", {}).get(dim, {}).get("value")
            if curr_val is not None and prev_val is not None:
                try:
                    delta = float(curr_val) - float(prev_val)
                    pct_change = (delta / float(prev_val) * 100) if prev_val != 0 else 0.0
                except (TypeError, ValueError):
                    delta = None
                    pct_change = None

                changes[dim] = {
                    "previous": prev_val,
                    "current": curr_val,
                    "delta": round(delta, 4) if delta is not None else None,
                    "pct_change": round(pct_change, 2) if pct_change is not None else None,
                    "direction": "up" if (delta and delta > 0) else ("down" if (delta and delta < 0) else "stable"),
                }

        # 整体健康度变化
        curr_health = current.get("overall_health", 0)
        prev_health = previous.get("overall_health", 0)
        health_delta = curr_health - prev_health

        return {
            "comparison_id": str(uuid.uuid4())[:8],
            "has_previous": True,
            "current_timestamp": current.get("timestamp"),
            "previous_timestamp": previous.get("timestamp"),
            "overall_health_delta": round(health_delta, 4),
            "health_trend": "improving" if health_delta > 0.01 else ("degrading" if health_delta < -0.01 else "stable"),
            "dimension_changes": changes,
        }

    # ------------------------------------------------------------------ #
    #  扫描报告
    # ------------------------------------------------------------------ #
    def get_scan_report(self, n_beats: int = 10) -> dict:
        """生成最近n个beat的扫描报告"""
        recent = self.scan_history[-n_beats:] if self.scan_history else []

        if not recent:
            return {
                "report_id": str(uuid.uuid4())[:8],
                "beats_analyzed": 0,
                "time_range": None,
                "summary": "无历史扫描数据",
                "dimension_trends": {},
                "anomaly_summary": {},
            }

        # 各维度趋势
        trends = {}
        for dim in self.DIMENSIONS:
            values = [b["dimensions"][dim]["value"] for b in recent if dim in b.get("dimensions", {})]
            statuses = [b["dimensions"][dim]["status"] for b in recent if dim in b.get("dimensions", {})]
            if values:
                trends[dim] = {
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                    "avg": round(sum(values) / len(values), 4),
                    "latest": values[-1],
                    "status_history": statuses,
                    "warning_count": statuses.count("warning"),
                    "critical_count": statuses.count("critical"),
                }

        # 异常汇总
        all_anomalies = []
        for beat in recent:
            all_anomalies.extend(beat.get("anomalies", []))

        anomaly_counts = {}
        for a in all_anomalies:
            dim = a["dimension"]
            sev = a["severity"]
            if dim not in anomaly_counts:
                anomaly_counts[dim] = {"warning": 0, "critical": 0}
            anomaly_counts[dim][sev] += 1

        return {
            "report_id": str(uuid.uuid4())[:8],
            "beats_analyzed": len(recent),
            "time_range": {
                "from": recent[0].get("timestamp"),
                "to": recent[-1].get("timestamp"),
            },
            "overall_health_trend": [b.get("overall_health") for b in recent],
            "dimension_trends": trends,
            "anomaly_summary": anomaly_counts,
            "total_anomalies": len(all_anomalies),
        }

    # ------------------------------------------------------------------ #
    #  内部辅助方法
    # ------------------------------------------------------------------ #
    def _status_from_numeric(self, value: float, threshold: float, invert: bool = False) -> str:
        """根据数值判断状态

        invert=False: value > threshold 为异常（默认）
        invert=True:  value < threshold 为异常
        """
        try:
            fv = float(value)
            ft = float(threshold)
        except (TypeError, ValueError):
            return "warning"

        if invert:
            if fv < ft * 0.5:
                return "critical"
            elif fv < ft:
                return "warning"
            return "normal"
        else:
            if fv > ft * 1.5:
                return "critical"
            elif fv > ft:
                return "warning"
            return "normal"

    def _compute_overall_health(self, dimensions: dict) -> float:
        """计算整体健康度 (0.0~1.0)"""
        scores = []
        weights = {
            "board_diff": 0.15,
            "hub_tower_peak": 0.15,
            "receipt_peak": 0.15,
            "water_level": 0.10,
            "nonce_registry": 0.10,
            "thread_peak": 0.10,
            "qset_peak": 0.15,
            "w12t_state": 0.10,
        }
        for dim, result in dimensions.items():
            status = result.get("status", "normal")
            if status == "normal":
                score = 1.0
            elif status == "warning":
                score = 0.7
            else:
                score = 0.3
            scores.append(score * weights.get(dim, 0.1))

        health = sum(scores)
        return round(max(0.0, min(1.0, health)), 4)

    def _generate_recommendations(self, dimensions: dict, anomalies: List[dict]) -> List[str]:
        """基于扫描结果生成建议"""
        recommendations = []
        for anomaly in anomalies:
            dim = anomaly["dimension"]
            if dim == "board_diff":
                recommendations.append("建议立即对比board快照，定位差异字段来源")
            elif dim == "hub_tower_peak":
                recommendations.append("毂塔层负载尖峰，建议水平扩展或降级非关键任务")
            elif dim == "receipt_peak":
                recommendations.append("回执堆积，建议检查 consumer 消费速率或增加处理线")
            elif dim == "water_level":
                recommendations.append("双系统水位漂移，建议触发同步校验或切换主备")
            elif dim == "nonce_registry":
                recommendations.append("nonce注册表膨胀，建议清理过期nonce或扩容")
            elif dim == "thread_peak":
                recommendations.append("讨论室线程过载，建议归档过期线程或限制并发")
            elif dim == "qset_peak":
                recommendations.append("QSET队列拥堵，建议优化调度策略或增加worker")
            elif dim == "w12t_state":
                recommendations.append("W12t进程异常，建议立即重启错误进程并检查日志")

        if not recommendations:
            recommendations.append("系统运行正常，继续保持监控")

        return recommendations

    def _suggest_for_dimension(self, dim: str, value: float, threshold, details: dict) -> str:
        """为特定维度生成建议"""
        # 安全格式化阈值
        try:
            thresh_str = f"{float(threshold):.2%}" if dim in ("board_diff", "water_level") else str(threshold)
        except (TypeError, ValueError):
            thresh_str = str(threshold)

        suggestions = {
            "board_diff": f"板面差异率 {value:.2%} 超过阈值 {thresh_str}",
            "hub_tower_peak": f"毂塔健康度峰值 {value} 接近饱和阈值 {threshold}",
            "receipt_peak": f"未处理回执 {value} 个超过阈值 {threshold}",
            "water_level": f"水位差异率 {value:.2%} 超过阈值 {thresh_str}",
            "nonce_registry": f"nonce数量 {value} 超过阈值 {threshold}",
            "thread_peak": f"活跃线程 {value} 个超过阈值 {threshold}",
            "qset_peak": f"QSET队列深度 {value} 超过阈值 {threshold}",
            "w12t_state": f"W12t进程异常，错误进程数: {value}",
        }
        return suggestions.get(dim, f"{dim} 异常，当前值: {value}")

    # ------------------------------------------------------------------ #
    #  模拟数据获取（实际集成时替换为真实数据源）
    # ------------------------------------------------------------------ #
    def _get_current_board(self) -> dict:
        """获取当前board状态"""
        return {
            "lines": {ln: {"status": "ok", "tasks": 5} for ln in self.topo.lines},
            "hubs": {h: {"load": 0.3} for h in self.topo.hubs},
            "timestamp": time.time(),
        }

    def _get_previous_board(self) -> dict:
        """获取上一beat的board状态"""
        if self.last_scan and "_cached_board" in self.last_scan:
            return self.last_scan["_cached_board"]
        return self._get_current_board()

    def _compute_board_diff(self, prev: dict, curr: dict) -> tuple:
        """计算board差异"""
        diff_fields = []
        prev_lines = prev.get("lines", {})
        curr_lines = curr.get("lines", {})
        all_keys = set(prev_lines.keys()) | set(curr_lines.keys())

        changed = 0
        for k in all_keys:
            if prev_lines.get(k) != curr_lines.get(k):
                changed += 1
                diff_fields.append(f"line.{k}")

        # 同时检查 hubs
        prev_hubs = prev.get("hubs", {})
        curr_hubs = curr.get("hubs", {})
        for k in set(prev_hubs.keys()) | set(curr_hubs.keys()):
            if prev_hubs.get(k) != curr_hubs.get(k):
                changed += 1
                diff_fields.append(f"hub.{k}")

        total = len(all_keys) + len(set(prev_hubs.keys()) | set(curr_hubs.keys()))
        diff_rate = changed / total if total else 0.0
        return diff_fields, diff_rate

    def _node_health(self, node: str, node_type: str) -> float:
        """获取节点健康度 (模拟)"""
        import random
        random.seed(hash(f"{node}_{node_type}_{int(time.time()/60)}"))
        return round(random.uniform(0.5, 1.0), 3)

    def _get_unprocessed_receipts(self, line: str) -> int:
        """获取未处理回执数 (模拟)"""
        import random
        random.seed(hash(f"receipt_{line}_{int(time.time()/300)}"))
        return random.randint(0, 8)

    def _get_water_level(self, system: str) -> float:
        """获取系统水位 (模拟)"""
        import random
        random.seed(hash(f"water_{system}_{int(time.time()/600)}"))
        base = 0.7 if system == "system_a" else 0.65
        return round(base + random.uniform(-0.15, 0.15), 3)

    def _get_nonce_count(self) -> int:
        """获取nonce注册表数量 (模拟)"""
        import random
        random.seed(hash(f"nonce_{int(time.time()/300)}"))
        return random.randint(50, 120)

    def _get_nonce_growth_rate(self) -> float:
        """获取nonce增长速率 (模拟)"""
        import random
        return round(random.uniform(5.0, 25.0), 2)

    def _get_nonce_duplicates(self) -> List[str]:
        """获取重复nonce (模拟)"""
        import random
        random.seed(hash(f"nonce_dup_{int(time.time()/300)}"))
        if random.random() > 0.7:
            return [f"nonce_{random.randint(1000, 9999)}" for _ in range(random.randint(1, 3))]
        return []

    def _get_active_threads(self, space: str) -> int:
        """获取活跃线程数 (模拟)"""
        import random
        random.seed(hash(f"threads_{space}_{int(time.time()/300)}"))
        base = {"discussion_room": 8, "bulletin_board": 3, "hall": 6, "wild_ask": 4}
        return random.randint(base.get(space, 5) - 2, base.get(space, 5) + 5)

    def _get_qset_depth(self, line: str) -> int:
        """获取QSET队列深度 (模拟)"""
        import random
        random.seed(hash(f"qset_{line}_{int(time.time()/300)}"))
        return random.randint(0, 25)

    def _get_w12t_processes(self) -> List[dict]:
        """获取W12t进程状态 (模拟)"""
        import random
        random.seed(hash(f"w12t_{int(time.time()/300)}"))
        procs = []
        for i in range(4):
            status_roll = random.random()
            if status_roll > 0.9:
                status = "error"
            elif status_roll > 0.75:
                status = "warning"
            else:
                status = "ok"
            procs.append({
                "name": f"w12t_worker_{i}",
                "pid": 1000 + i,
                "status": status,
                "uptime": random.randint(100, 10000),
            })
        return procs

    def _persist_scan(self, scan_result: dict):
        """持久化扫描结果到本地"""
        try:
            ts = scan_result["timestamp"].replace(":", "-")
            filepath = self.state_path / f"scan_{ts}_{scan_result['scan_id']}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(scan_result, f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass  # 持久化失败不影响主流程


# =====================================================================
#  测试块
# =====================================================================
if __name__ == "__main__":
    import random

    print("=" * 70)
    print("OMNI-HUB v3.2 八面轮扫引擎 — 测试")
    print("=" * 70)

    # 初始化拓扑与扫描器
    topo = Topology()
    scanner = OctaveScan(topology=topo, state_path="/tmp/omni_hub_test_state")

    # ---- 测试1: 单维度扫描 ----
    print("\n【测试1】单维度扫描")
    print("-" * 40)
    for dim in OctaveScan.DIMENSIONS:
        result = scanner.scan_dimension(dim)
        status_icon = "✓" if result["status"] == "normal" else "⚠"
        print(f"  {status_icon} {dim:18s} | 值: {result['value']:<10} | 状态: {result['status']}")

    # ---- 测试2: 全扫描 ----
    print("\n【测试2】全扫描 (scan_all)")
    print("-" * 40)
    full_scan = scanner.scan_all()
    print(f"  扫描ID: {full_scan['scan_id']}")
    print(f"  时间戳: {full_scan['timestamp']}")
    print(f"  整体健康度: {full_scan['overall_health']}")
    print(f"  异常数: {len(full_scan['anomalies'])}")
    print(f"  建议数: {len(full_scan['recommendations'])}")
    for rec in full_scan['recommendations']:
        print(f"    → {rec}")

    # ---- 测试3: 异常检测 ----
    print("\n【测试3】异常检测 (detect_anomaly)")
    print("-" * 40)
    anomalies = scanner.detect_anomaly(full_scan)
    if anomalies:
        for a in anomalies:
            icon = "🔴" if a["severity"] == "critical" else "🟡"
            print(f"  {icon} [{a['severity'].upper()}] {a['dimension']}")
            print(f"      值: {a['value']} | 阈值: {a['threshold']}")
            print(f"      建议: {a['suggestion']}")
    else:
        print("  ✓ 未检测到异常")

    # ---- 测试4: 告警生成与路由 ----
    print("\n【测试4】告警生成与路由 (generate_alert)")
    print("-" * 40)
    alert = scanner.generate_alert(anomalies)
    print(f"  告警级别: {alert['level']}")
    print(f"  路由线: {', '.join(alert['routed_lines']) if alert['routed_lines'] else '无'}")
    for msg in alert['messages']:
        print(f"    → [{msg['dimension']}] → 线: {', '.join(msg['target_lines'])}")

    # ---- 测试5: Beat 比较 ----
    print("\n【测试5】Beat 比较 (compare_beats)")
    print("-" * 40)
    # 执行第二次扫描以产生差异
    time.sleep(0.5)
    second_scan = scanner.scan_all()
    comparison = scanner.compare_beats(second_scan, full_scan)
    print(f"  比较ID: {comparison['comparison_id']}")
    print(f"  健康度趋势: {comparison['health_trend']}")
    print(f"  整体健康度变化: {comparison['overall_health_delta']}")
    for dim, change in comparison['dimension_changes'].items():
        if change['delta'] is not None and abs(change['delta']) > 0.001:
            arrow = "↑" if change['direction'] == "up" else "↓"
            print(f"    {arrow} {dim:18s} Δ {change['delta']:+.4f} ({change['pct_change']:+.1f}%)")

    # ---- 测试6: 扫描报告 ----
    print("\n【测试6】扫描报告 (get_scan_report)")
    print("-" * 40)
    report = scanner.get_scan_report(n_beats=2)
    print(f"  报告ID: {report['report_id']}")
    print(f"  分析beats数: {report['beats_analyzed']}")
    print(f"  总异常数: {report['total_anomalies']}")
    for dim, trend in report['dimension_trends'].items():
        if trend.get("warning_count") or trend.get("critical_count"):
            print(f"    ⚠ {dim}: warning={trend['warning_count']}, critical={trend['critical_count']}")

    # ---- 测试7: 历史持久化验证 ----
    print("\n【测试7】历史持久化验证")
    print("-" * 40)
    scan_files = list(scanner.state_path.glob("scan_*.json"))
    print(f"  持久化文件数: {len(scan_files)}")
    if scan_files:
        print(f"  最新文件: {scan_files[-1].name}")

    print("\n" + "=" * 70)
    print("八面轮扫引擎测试完成")
    print("=" * 70)
