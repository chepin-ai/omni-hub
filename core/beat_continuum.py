#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.3 — BeatContinuum Engine
=====================================
拍自续引擎 — "会话歇而拍自续"

Core Philosophy:
- "链在仓在，会话歇而拍自续" — 用户会话暂停时，节拍仍自动延续
- "SI1为纬非薪" — SI1只是通道，拍自续不依赖会话

This module implements the autonomous beat continuation mechanism that keeps
system momentum alive even when user sessions are paused. It integrates with
the SelfDriveEngine to perform autonomous spins, tracks all activities,
ensures beat continuity, and provides comprehensive reports upon session
resumption.
"""

from __future__ import annotations

import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# Configure module-level logger
logger = logging.getLogger("OMNI-HUB.BeatContinuum")
logger.addHandler(logging.NullHandler())


class ContinuumState(Enum):
    """自续引擎状态枚举"""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    EMERGENCY_STOPPED = "emergency_stopped"
    MAX_SPINS_REACHED = "max_spins_reached"


@dataclass
class BeatRecord:
    """单条节拍记录"""
    beat_id: str
    iteration: int
    timestamp: str
    spin_result: dict
    fuel_consumed: float = 0.0
    fuel_generated: float = 0.0
    findings: list = field(default_factory=list)
    tasks_completed: list = field(default_factory=list)
    tasks_triggered: list = field(default_factory=list)
    anomalies: list = field(default_factory=list)
    linked_to_previous: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ContinuumSnapshot:
    """自续期间快照"""
    snapshot_id: str
    created_at: str
    spins_count: int
    total_fuel_consumed: float
    total_fuel_generated: float
    beat_chain_length: int
    anomalies_detected: int


class BeatContinuum:
    """
    拍自续引擎 — 会话歇而拍自续

    Manages autonomous system continuation during user session pauses.
    Maintains beat history, ensures chain continuity, detects anomalies,
    and provides comprehensive reporting upon session resumption.
    """

    def __init__(
        self,
        self_drive_engine,
        max_spins_per_pause: int = 100,
        auto_link_beats: bool = True,
        anomaly_threshold: int = 3,
    ):
        self.engine = self_drive_engine
        self.beat_history: list[BeatRecord] = []
        self.continuum_active: bool = False
        self.session_paused_at: Optional[str] = None
        self.spins_since_pause: int = 0
        self.max_spins_per_pause: int = max_spins_per_pause
        self.continuum_log: list[dict] = []
        self.auto_link_beats: bool = auto_link_beats
        self.anomaly_threshold: int = anomaly_threshold

        # Internal tracking
        self._state: ContinuumState = ContinuumState.IDLE
        self._pause_beats: list[BeatRecord] = []
        self._findings_buffer: list[dict] = []
        self._tasks_completed_buffer: list[str] = []
        self._tasks_triggered_buffer: list[str] = []
        self._fuel_consumed_total: float = 0.0
        self._fuel_generated_total: float = 0.0
        self._anomaly_count: int = 0
        self._emergency_reason: Optional[str] = None
        self._continuum_start_time: Optional[float] = None
        self._last_beat_timestamp: Optional[str] = None
        self._current_iteration: int = 0
        self._snapshots: list[ContinuumSnapshot] = []

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def on_session_pause(self) -> dict:
        """
        会话暂停时触发 — 启动自续模式

        1. 记录暂停时间
        2. 标记 continuum_active = True
        3. 启动自续循环 (调用 continuum_beat 多次)

        Returns:
            {"paused_at": str, "continuum_started": bool, "projected_beats": int}
        """
        paused_at = self._now_iso()
        self.session_paused_at = paused_at
        self.continuum_active = True
        self._state = ContinuumState.ACTIVE
        self._continuum_start_time = time.time()
        self.spins_since_pause = 0
        self._pause_beats = []
        self._findings_buffer = []
        self._tasks_completed_buffer = []
        self._tasks_triggered_buffer = []
        self._fuel_consumed_total = 0.0
        self._fuel_generated_total = 0.0
        self._anomaly_count = 0
        self._emergency_reason = None
        self._current_iteration = len(self.beat_history)

        self._log_event(
            "SESSION_PAUSE",
            f"Session paused at {paused_at}. Starting autonomous continuum...",
            {"projected_beats": self.max_spins_per_pause},
        )

        # ── 启动自续循环 ──
        projected_beats = self.max_spins_per_pause
        actual_spins = 0

        try:
            while self.continuum_active and self.spins_since_pause < self.max_spins_per_pause:
                if self._state == ContinuumState.EMERGENCY_STOPPED:
                    break

                beat_result = self.continuum_beat()
                actual_spins += 1

                # Check for anomalies that may trigger emergency stop
                if self._anomaly_count >= self.anomaly_threshold:
                    self.emergency_stop(
                        reason=f"Anomaly threshold exceeded ({self._anomaly_count} >= {self.anomaly_threshold})"
                    )
                    break

                # Periodic snapshot every 10 spins
                if actual_spins % 10 == 0:
                    self._take_snapshot()

        except Exception as e:
            self.emergency_stop(reason=f"Exception during continuum: {type(e).__name__}: {e}")
            logger.exception("Continuum loop encountered fatal error")

        self._log_event(
            "CONTINUUM_LOOP_END",
            f"Autonomous loop completed. Spins executed: {actual_spins}",
            {"actual_spins": actual_spins, "final_state": self._state.value},
        )

        return {
            "paused_at": paused_at,
            "continuum_started": True,
            "projected_beats": projected_beats,
            "actual_spins": actual_spins,
            "final_state": self._state.value,
        }

    def on_session_resume(self) -> dict:
        """
        会话恢复时触发 — 汇报自续期间所有成果

        Returns:
            {
                "spins_executed": int,
                "findings": list,
                "tasks_completed": list,
                "tasks_triggered": list,
                "fuel_consumed": float,
                "fuel_generated": float,
                "continuum_duration_sec": float,
                "anomalies_detected": int,
                "emergency_stopped": bool,
                "beat_chain_integrity": dict,
                "snapshots": list,
            }
        """
        resumed_at = self._now_iso()
        continuum_duration = (
            time.time() - self._continuum_start_time if self._continuum_start_time else 0.0
        )

        # Validate beat chain integrity
        chain_integrity = self._validate_beat_chain()

        # Build comprehensive report
        report = {
            "spins_executed": self.spins_since_pause,
            "findings": self._findings_buffer.copy(),
            "tasks_completed": self._tasks_completed_buffer.copy(),
            "tasks_triggered": self._tasks_triggered_buffer.copy(),
            "fuel_consumed": round(self._fuel_consumed_total, 6),
            "fuel_generated": round(self._fuel_generated_total, 6),
            "continuum_duration_sec": round(continuum_duration, 3),
            "anomalies_detected": self._anomaly_count,
            "emergency_stopped": self._state == ContinuumState.EMERGENCY_STOPPED,
            "emergency_reason": self._emergency_reason,
            "beat_chain_integrity": chain_integrity,
            "snapshots": [self._snapshot_to_dict(s) for s in self._snapshots],
            "resumed_at": resumed_at,
            "paused_at": self.session_paused_at,
        }

        # Reset state for next cycle
        self.continuum_active = False
        self._state = ContinuumState.IDLE
        previous_spins = self.spins_since_pause
        self.spins_since_pause = 0

        self._log_event(
            "SESSION_RESUME",
            f"Session resumed at {resumed_at}. Report generated for {previous_spins} spins.",
            {"report_keys": list(report.keys())},
        )

        return report

    def continuum_beat(self) -> dict:
        """
        自续节拍 — 会话暂停期间自动执行

        1. 调用 self_drive_engine.spin()
        2. 记录到 beat_history
        3. spins_since_pause += 1
        4. 如果 spins_since_pause >= max_spins_per_pause → 自动暂停

        Returns:
            {"beat_id": str, "spin_result": dict, "timestamp": str}
        """
        if self._state == ContinuumState.EMERGENCY_STOPPED:
            raise RuntimeError(f"Continuum is emergency stopped: {self._emergency_reason}")

        if not self.continuum_active:
            raise RuntimeError("Continuum is not active. Call on_session_pause() first.")

        self._current_iteration += 1
        beat_id = f"beat_{uuid.uuid4().hex[:12]}"
        timestamp = self._now_iso()

        # ── 1. 调用 self_drive_engine.spin() ──
        spin_result = self._safe_engine_spin()

        # ── 2. 构建 BeatRecord ──
        record = BeatRecord(
            beat_id=beat_id,
            iteration=self._current_iteration,
            timestamp=timestamp,
            spin_result=spin_result,
            fuel_consumed=spin_result.get("fuel_consumed", 0.0),
            fuel_generated=spin_result.get("fuel_generated", 0.0),
            findings=spin_result.get("findings", []),
            tasks_completed=spin_result.get("tasks_completed", []),
            tasks_triggered=spin_result.get("tasks_triggered", []),
            anomalies=spin_result.get("anomalies", []),
        )

        # ── 3. 自动链接检测 ──
        if self.auto_link_beats and self._last_beat_timestamp:
            link_check = self.link_beats(
                self._last_beat_record(),
                record.to_dict(),
            )
            record.linked_to_previous = link_check["continuous"]
            if not link_check["continuous"]:
                record.anomalies.append({
                    "type": "beat_continuity_break",
                    "details": link_check,
                })
                self._anomaly_count += 1
                self._log_event(
                    "CONTINUITY_BREAK",
                    f"Beat continuity broken at iteration {self._current_iteration}",
                    link_check,
                )

        # ── 4. 记录到历史 ──
        self.beat_history.append(record)
        self._pause_beats.append(record)
        self._last_beat_timestamp = timestamp

        # ── 5. 聚合成果 ──
        self._fuel_consumed_total += record.fuel_consumed
        self._fuel_generated_total += record.fuel_generated
        self._findings_buffer.extend(record.findings)
        self._tasks_completed_buffer.extend(record.tasks_completed)
        self._tasks_triggered_buffer.extend(record.tasks_triggered)
        self._anomaly_count += len(record.anomalies)

        # ── 6. 计数与上限检查 ──
        self.spins_since_pause += 1
        if self.spins_since_pause >= self.max_spins_per_pause:
            self._state = ContinuumState.MAX_SPINS_REACHED
            self.continuum_active = False
            self._log_event(
                "MAX_SPINS_REACHED",
                f"Max spins limit ({self.max_spins_per_pause}) reached. Auto-pausing continuum.",
                {"spins": self.spins_since_pause},
            )

        return {
            "beat_id": beat_id,
            "spin_result": spin_result,
            "timestamp": timestamp,
            "iteration": self._current_iteration,
            "linked": record.linked_to_previous,
        }

    def link_beats(self, beat_a: dict, beat_b: dict) -> dict:
        """
        链接两个beat — 确保拍的连续性

        检查:
        - 时间连续性 (beat_b.timestamp > beat_a.timestamp)
        - 迭代连续性 (beat_b.iteration == beat_a.iteration + 1)
        - 状态一致性

        如果断裂 → 返回断裂位置和修复建议

        Returns:
            {
                "continuous": bool,
                "gaps": list,
                "repair_suggestions": list,
            }
        """
        gaps = []
        repair_suggestions = []

        # ── 检查1: 时间连续性 ──
        ts_a = beat_a.get("timestamp", "")
        ts_b = beat_b.get("timestamp", "")
        if ts_a and ts_b:
            try:
                time_a = datetime.fromisoformat(ts_a.replace("Z", "+00:00"))
                time_b = datetime.fromisoformat(ts_b.replace("Z", "+00:00"))
                if time_b <= time_a:
                    gaps.append({
                        "type": "time_regression",
                        "description": f"Beat B timestamp ({ts_b}) <= Beat A timestamp ({ts_a})",
                        "severity": "critical",
                    })
                    repair_suggestions.append(
                        "Regenerate beat_b with corrected timestamp or investigate clock skew"
                    )
            except ValueError:
                gaps.append({
                    "type": "invalid_timestamp",
                    "description": "Unable to parse timestamps for comparison",
                    "severity": "warning",
                })

        # ── 检查2: 迭代连续性 ──
        iter_a = beat_a.get("iteration", -1)
        iter_b = beat_b.get("iteration", -1)
        if iter_a >= 0 and iter_b >= 0:
            expected = iter_a + 1
            if iter_b != expected:
                gaps.append({
                    "type": "iteration_gap",
                    "description": f"Expected iteration {expected}, got {iter_b}",
                    "severity": "critical" if iter_b < expected else "warning",
                    "missing_iterations": list(range(expected, iter_b)) if iter_b > expected else [],
                })
                if iter_b > expected:
                    repair_suggestions.append(
                        f"Insert {iter_b - expected} missing beat record(s) between iterations"
                    )
                else:
                    repair_suggestions.append(
                        "Reorder beats or fix iteration numbering to ensure monotonic increase"
                    )

        # ── 检查3: beat_id 唯一性 ──
        id_a = beat_a.get("beat_id", "")
        id_b = beat_b.get("beat_id", "")
        if id_a and id_b and id_a == id_b:
            gaps.append({
                "type": "duplicate_beat_id",
                "description": "Both beats share the same beat_id",
                "severity": "critical",
            })
            repair_suggestions.append("Regenerate unique beat_id for beat_b")

        # ── 检查4: spin_result 状态一致性 ──
        result_a = beat_a.get("spin_result", {})
        result_b = beat_b.get("spin_result", {})
        status_a = result_a.get("status", "")
        status_b = result_b.get("status", "")
        if status_a == "fatal_error" and status_b == "fatal_error":
            gaps.append({
                "type": "consecutive_fatal_errors",
                "description": "Two consecutive beats report fatal errors",
                "severity": "critical",
            })
            repair_suggestions.append("Invoke emergency_stop and investigate engine health")

        # ── 检查5: 燃料异常 ──
        fuel_a = beat_a.get("fuel_consumed", 0.0)
        fuel_b = beat_b.get("fuel_consumed", 0.0)
        if fuel_a > 0 and fuel_b > fuel_a * 10:
            gaps.append({
                "type": "fuel_spike",
                "description": f"Fuel consumption spiked from {fuel_a} to {fuel_b}",
                "severity": "warning",
            })
            repair_suggestions.append("Review engine fuel efficiency; possible runaway process")

        is_continuous = len(gaps) == 0

        return {
            "continuous": is_continuous,
            "gaps": gaps,
            "repair_suggestions": repair_suggestions,
            "beat_a_id": id_a,
            "beat_b_id": id_b,
        }

    def get_continuum_report(self) -> dict:
        """
        获取自续期间完整报告

        Returns comprehensive report of all continuum activities including
        beat chain analysis, fuel accounting, anomaly summary, and snapshots.
        """
        if not self._pause_beats:
            return {
                "status": "no_data",
                "message": "No continuum data available. Session may not have been paused.",
            }

        # Analyze entire beat chain
        chain_analysis = self._analyze_full_chain()

        # Fuel net calculation
        fuel_net = self._fuel_generated_total - self._fuel_consumed_total

        # Task deduplication stats
        unique_completed = list(dict.fromkeys(self._tasks_completed_buffer))
        unique_triggered = list(dict.fromkeys(self._tasks_triggered_buffer))

        report = {
            "report_id": f"rpt_{uuid.uuid4().hex[:8]}",
            "generated_at": self._now_iso(),
            "session_paused_at": self.session_paused_at,
            "continuum_state": self._state.value,
            "spins_executed": self.spins_since_pause,
            "beat_chain": chain_analysis,
            "fuel": {
                "consumed": round(self._fuel_consumed_total, 6),
                "generated": round(self._fuel_generated_total, 6),
                "net": round(fuel_net, 6),
                "efficiency": round(
                    (self._fuel_generated_total / max(self._fuel_consumed_total, 1e-9)), 4
                ),
            },
            "findings": {
                "total": len(self._findings_buffer),
                "items": self._findings_buffer.copy(),
            },
            "tasks": {
                "completed": {
                    "total": len(self._tasks_completed_buffer),
                    "unique": len(unique_completed),
                    "items": unique_completed,
                },
                "triggered": {
                    "total": len(self._tasks_triggered_buffer),
                    "unique": len(unique_triggered),
                    "items": unique_triggered,
                },
            },
            "anomalies": {
                "count": self._anomaly_count,
                "threshold": self.anomaly_threshold,
                "threshold_exceeded": self._anomaly_count >= self.anomaly_threshold,
            },
            "snapshots": [self._snapshot_to_dict(s) for s in self._snapshots],
            "metadata": {
                "max_spins_configured": self.max_spins_per_pause,
                "auto_link_enabled": self.auto_link_beats,
                "total_historical_beats": len(self.beat_history),
            },
        }

        return report

    def emergency_stop(self, reason: str = "Unknown emergency") -> dict:
        """
        紧急停止自续 — 当检测到严重异常时

        Immediately halts the continuum, preserves all current state,
        and logs the emergency condition.

        Args:
            reason: Human-readable reason for emergency stop

        Returns:
            {"stopped": bool, "reason": str, "spins_at_stop": int, "preserved_beats": int}
        """
        was_active = self.continuum_active
        self.continuum_active = False
        self._state = ContinuumState.EMERGENCY_STOPPED
        self._emergency_reason = reason

        preserved_count = len(self._pause_beats)

        self._log_event(
            "EMERGENCY_STOP",
            f"EMERGENCY STOP triggered: {reason}",
            {
                "was_active": was_active,
                "spins_at_stop": self.spins_since_pause,
                "preserved_beats": preserved_count,
            },
        )

        logger.critical(
            "BeatContinuum emergency stop: %s (spins=%d, beats=%d)",
            reason,
            self.spins_since_pause,
            preserved_count,
        )

        return {
            "stopped": True,
            "reason": reason,
            "spins_at_stop": self.spins_since_pause,
            "preserved_beats": preserved_count,
            "timestamp": self._now_iso(),
        }

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    def _safe_engine_spin(self) -> dict:
        """安全地调用 engine.spin()，处理所有异常"""
        try:
            if hasattr(self.engine, "spin") and callable(self.engine.spin):
                result = self.engine.spin()
                if not isinstance(result, dict):
                    result = {"raw_result": result, "status": "ok"}
            else:
                # Fallback: engine 没有 spin 方法时的模拟行为
                result = self._simulate_spin()
        except Exception as e:
            result = {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "findings": [],
                "tasks_completed": [],
                "tasks_triggered": [],
                "fuel_consumed": 0.0,
                "fuel_generated": 0.0,
                "anomalies": [{"type": "spin_exception", "details": str(e)}],
            }
            logger.warning("Engine spin failed: %s", e)

        return result

    def _simulate_spin(self) -> dict:
        """
        模拟 engine spin — 当真实 engine 不可用时使用
        产生确定性伪随机结果用于测试和降级运行
        """
        import random
        # Seed with current time fraction for deterministic-ish behavior
        random.seed(hash(time.time() * 1000) % (2**31))

        findings_pool = [
            {"type": "pattern_detected", "confidence": round(random.random(), 3), "domain": "dataflow"},
            {"type": "optimization_opportunity", "gain_estimate": round(random.random() * 0.1, 4), "domain": "compute"},
            {"type": "anomaly_flagged", "severity": random.choice(["low", "medium", "high"]), "domain": "monitoring"},
            {"type": "resource_idle", "savings_potential": round(random.random() * 0.05, 4), "domain": "resources"},
        ]

        tasks_pool = [
            "cleanup_stale_cache",
            "optimize_index",
            "sync_metadata",
            "prune_logs",
            "balance_shards",
            "refresh_tokens",
            "compress_history",
            "verify_integrity",
        ]

        num_findings = random.randint(0, 2)
        num_tasks_done = random.randint(0, 1)
        num_tasks_triggered = random.randint(0, 2)

        findings = random.sample(findings_pool, min(num_findings, len(findings_pool)))
        tasks_done = random.sample(tasks_pool, min(num_tasks_done, len(tasks_pool)))
        remaining_tasks = [t for t in tasks_pool if t not in tasks_done]
        tasks_triggered = random.sample(remaining_tasks, min(num_tasks_triggered, len(remaining_tasks)))

        fuel_c = round(random.random() * 0.01 + 0.001, 6)
        fuel_g = round(random.random() * 0.015 + 0.0005, 6)

        return {
            "status": "ok",
            "findings": findings,
            "tasks_completed": tasks_done,
            "tasks_triggered": tasks_triggered,
            "fuel_consumed": fuel_c,
            "fuel_generated": fuel_g,
            "anomalies": [],
            "spin_metadata": {
                "simulated": True,
                "spin_seq": self.spins_since_pause + 1,
            },
        }

    def _validate_beat_chain(self) -> dict:
        """验证整个暂停期间的 beat 链完整性"""
        if len(self._pause_beats) < 2:
            return {
                "valid": True,
                "total_links": 0,
                "broken_links": 0,
                "break_points": [],
            }

        broken = 0
        break_points = []

        for i in range(1, len(self._pause_beats)):
            prev = self._pause_beats[i - 1].to_dict()
            curr = self._pause_beats[i].to_dict()
            link = self.link_beats(prev, curr)
            if not link["continuous"]:
                broken += 1
                break_points.append({
                    "index": i,
                    "beat_a": prev["beat_id"],
                    "beat_b": curr["beat_id"],
                    "gaps": link["gaps"],
                })

        return {
            "valid": broken == 0,
            "total_links": len(self._pause_beats) - 1,
            "broken_links": broken,
            "break_points": break_points,
        }

    def _analyze_full_chain(self) -> dict:
        """分析完整 beat 链的统计信息"""
        if not self._pause_beats:
            return {"length": 0, "analysis": "empty"}

        timestamps = []
        for b in self._pause_beats:
            try:
                ts = datetime.fromisoformat(b.timestamp.replace("Z", "+00:00"))
                timestamps.append(ts)
            except ValueError:
                pass

        if len(timestamps) >= 2:
            duration = (timestamps[-1] - timestamps[0]).total_seconds()
            avg_interval = duration / (len(timestamps) - 1)
        else:
            duration = 0.0
            avg_interval = 0.0

        return {
            "length": len(self._pause_beats),
            "first_beat": self._pause_beats[0].beat_id,
            "last_beat": self._pause_beats[-1].beat_id,
            "duration_sec": round(duration, 3),
            "avg_beat_interval_sec": round(avg_interval, 3),
            "iterations": {
                "first": self._pause_beats[0].iteration,
                "last": self._pause_beats[-1].iteration,
            },
        }

    def _take_snapshot(self) -> None:
        """创建当前状态快照"""
        snapshot = ContinuumSnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:8]}",
            created_at=self._now_iso(),
            spins_count=self.spins_since_pause,
            total_fuel_consumed=self._fuel_consumed_total,
            total_fuel_generated=self._fuel_generated_total,
            beat_chain_length=len(self._pause_beats),
            anomalies_detected=self._anomaly_count,
        )
        self._snapshots.append(snapshot)

    def _last_beat_record(self) -> dict:
        """获取最后一个 beat 的字典表示"""
        if self._pause_beats:
            return self._pause_beats[-1].to_dict()
        return {}

    def _now_iso(self) -> str:
        """返回当前 UTC ISO 8601 时间字符串"""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _log_event(self, event_type: str, message: str, data: dict) -> None:
        """记录 continuum 事件到日志"""
        entry = {
            "event_type": event_type,
            "message": message,
            "timestamp": self._now_iso(),
            "data": data,
        }
        self.continuum_log.append(entry)

    @staticmethod
    def _snapshot_to_dict(snapshot: ContinuumSnapshot) -> dict:
        return asdict(snapshot)


# ═══════════════════════════════════════════════════════════════════════
# 测试块 — 验证所有核心功能
# ═══════════════════════════════════════════════════════════════════════

class MockSelfDriveEngine:
    """模拟自驱引擎，用于测试"""

    def __init__(self, failure_rate: float = 0.0):
        self.spin_count = 0
        self.failure_rate = failure_rate

    def spin(self) -> dict:
        import random
        self.spin_count += 1
        if random.random() < self.failure_rate:
            raise RuntimeError(f"Simulated spin failure #{self.spin_count}")

        return {
            "status": "ok",
            "spin_number": self.spin_count,
            "findings": [
                {"type": "mock_finding", "seq": self.spin_count}
            ],
            "tasks_completed": [f"mock_task_{self.spin_count}"] if self.spin_count % 3 == 0 else [],
            "tasks_triggered": [f"triggered_{self.spin_count}"] if self.spin_count % 2 == 0 else [],
            "fuel_consumed": 0.005,
            "fuel_generated": 0.008,
            "anomalies": [],
        }


def _run_tests():
    """运行完整测试套件"""
    import json

    logger.info("=" * 70)
    logger.info("OMNI-HUB v3.3 — BeatContinuum Test Suite")
    logger.info("=" * 70)

    tests_passed = 0
    tests_failed = 0

    def assert_true(condition, msg):
        nonlocal tests_passed, tests_failed
        if condition:
            tests_passed += 1
            logger.info(f"  [PASS] {msg}")
        else:
            tests_failed += 1
            logger.info(f"  [FAIL] {msg}")

    # ── Test 1: 基本初始化和状态 ──
    logger.info("\n[Test 1] 基本初始化和状态检查")
    engine = MockSelfDriveEngine()
    bc = BeatContinuum(engine, max_spins_per_pause=5)
    assert_true(bc.continuum_active == False, "初始状态 continuum_active 应为 False")
    assert_true(bc.spins_since_pause == 0, "初始 spins_since_pause 应为 0")
    assert_true(len(bc.beat_history) == 0, "初始 beat_history 应为空")
    assert_true(len(bc.continuum_log) == 0, "初始 continuum_log 应为空")

    # ── Test 2: 会话暂停→自续→恢复完整流程 ──
    logger.info("\n[Test 2] 完整流程: 暂停 → 自续 → 恢复")
    engine2 = MockSelfDriveEngine()
    bc2 = BeatContinuum(engine2, max_spins_per_pause=5)

    pause_result = bc2.on_session_pause()
    assert_true(pause_result["continuum_started"] == True, "continuum 应成功启动")
    assert_true(pause_result["actual_spins"] == 5, f"应执行 5 次 spin (got {pause_result['actual_spins']})")
    assert_true(bc2.spins_since_pause == 5, "spins_since_pause 应为 5")
    assert_true(len(bc2.beat_history) == 5, "beat_history 应记录 5 条")
    assert_true(len(bc2._pause_beats) == 5, "_pause_beats 应记录 5 条")

    resume_result = bc2.on_session_resume()
    assert_true(resume_result["spins_executed"] == 5, "恢复报告应显示 5 次 spins")
    assert_true(len(resume_result["findings"]) > 0, "应有 findings 被收集")
    assert_true(len(resume_result["tasks_completed"]) > 0, "应有 tasks_completed")
    assert_true(resume_result["fuel_consumed"] > 0, "应有 fuel 消耗记录")
    assert_true(resume_result["fuel_generated"] > 0, "应有 fuel 生成记录")
    assert_true("beat_chain_integrity" in resume_result, "应有 beat_chain_integrity 字段")
    assert_true(resume_result["beat_chain_integrity"]["valid"] == True, "beat 链应有效")

    # ── Test 3: 模拟 engine 不可用时的降级运行 ──
    logger.info("\n[Test 3] 降级运行: 无 spin() 方法的 engine")

    class DummyEngine:
        pass

    bc3 = BeatContinuum(DummyEngine(), max_spins_per_pause=3)
    pause3 = bc3.on_session_pause()
    assert_true(pause3["actual_spins"] == 3, "降级模式仍应完成 3 次 spins")
    assert_true(len(bc3.beat_history) == 3, "降级模式应生成 3 条 beat 记录")
    resume3 = bc3.on_session_resume()
    assert_true(resume3["spins_executed"] == 3, "降级模式恢复报告应正确")

    # ── Test 4: link_beats 连续性检测 ──
    logger.info("\n[Test 4] Beat 链接连续性检测")
    bc4 = BeatContinuum(MockSelfDriveEngine(), max_spins_per_pause=2)

    beat_a = {
        "beat_id": "beat_a_001",
        "iteration": 1,
        "timestamp": "2024-01-15T10:00:00Z",
        "fuel_consumed": 0.01,
        "spin_result": {"status": "ok"},
    }
    beat_b = {
        "beat_id": "beat_b_002",
        "iteration": 2,
        "timestamp": "2024-01-15T10:00:01Z",
        "fuel_consumed": 0.012,
        "spin_result": {"status": "ok"},
    }
    link_ok = bc4.link_beats(beat_a, beat_b)
    assert_true(link_ok["continuous"] == True, "正常连续的 beats 应返回 continuous=True")
    assert_true(len(link_ok["gaps"]) == 0, "正常连续的 beats 应无 gaps")

    # 时间倒退
    beat_bad_time = {
        "beat_id": "beat_bad_003",
        "iteration": 3,
        "timestamp": "2024-01-15T09:59:59Z",  # 早于 beat_b
        "fuel_consumed": 0.01,
        "spin_result": {"status": "ok"},
    }
    link_bad = bc4.link_beats(beat_b, beat_bad_time)
    assert_true(link_bad["continuous"] == False, "时间倒退应返回 continuous=False")
    assert_true(any(g["type"] == "time_regression" for g in link_bad["gaps"]), "应检测 time_regression gap")
    assert_true(len(link_bad["repair_suggestions"]) > 0, "应提供修复建议")

    # 迭代断裂
    beat_gap_iter = {
        "beat_id": "beat_gap_004",
        "iteration": 5,  # 跳过了 4
        "timestamp": "2024-01-15T10:00:02Z",
        "fuel_consumed": 0.01,
        "spin_result": {"status": "ok"},
    }
    link_gap = bc4.link_beats(beat_b, beat_gap_iter)
    assert_true(link_gap["continuous"] == False, "迭代断裂应返回 continuous=False")
    assert_true(any(g["type"] == "iteration_gap" for g in link_gap["gaps"]), "应检测 iteration_gap")
    assert_true(any("missing" in s.lower() for s in link_gap["repair_suggestions"]), "应建议插入缺失 beats")

    # 重复 beat_id
    beat_dup = {
        "beat_id": "beat_b_002",  # 与 beat_b 相同
        "iteration": 3,
        "timestamp": "2024-01-15T10:00:02Z",
        "fuel_consumed": 0.01,
        "spin_result": {"status": "ok"},
    }
    link_dup = bc4.link_beats(beat_b, beat_dup)
    assert_true(link_dup["continuous"] == False, "重复 beat_id 应返回 continuous=False")
    assert_true(any(g["type"] == "duplicate_beat_id" for g in link_dup["gaps"]), "应检测 duplicate_beat_id")

    # 连续致命错误
    beat_fatal1 = {
        "beat_id": "fatal_001",
        "iteration": 10,
        "timestamp": "2024-01-15T10:00:10Z",
        "fuel_consumed": 0.01,
        "spin_result": {"status": "fatal_error"},
    }
    beat_fatal2 = {
        "beat_id": "fatal_002",
        "iteration": 11,
        "timestamp": "2024-01-15T10:00:11Z",
        "fuel_consumed": 0.01,
        "spin_result": {"status": "fatal_error"},
    }
    link_fatal = bc4.link_beats(beat_fatal1, beat_fatal2)
    assert_true(link_fatal["continuous"] == False, "连续 fatal_error 应返回 continuous=False")
    assert_true(any(g["type"] == "consecutive_fatal_errors" for g in link_fatal["gaps"]), "应检测 consecutive_fatal_errors")

    # 燃料飙升
    beat_fuel_spike = {
        "beat_id": "fuel_002",
        "iteration": 2,
        "timestamp": "2024-01-15T10:00:01Z",
        "fuel_consumed": 0.5,  # 远高于前者的 0.01
        "spin_result": {"status": "ok"},
    }
    link_fuel = bc4.link_beats(beat_a, beat_fuel_spike)
    assert_true(link_fuel["continuous"] == False, "燃料飙升应返回 continuous=False")
    assert_true(any(g["type"] == "fuel_spike" for g in link_fuel["gaps"]), "应检测 fuel_spike")

    # ── Test 5: 紧急停止机制 ──
    logger.info("\n[Test 5] 紧急停止机制")
    bc5 = BeatContinuum(MockSelfDriveEngine(), max_spins_per_pause=100)
    bc5.on_session_pause()
    # 手动触发紧急停止
    stop_result = bc5.emergency_stop(reason="Test emergency stop")
    assert_true(stop_result["stopped"] == True, "emergency_stop 应返回 stopped=True")
    assert_true(stop_result["reason"] == "Test emergency stop", "应保留停止原因")
    assert_true(bc5.continuum_active == False, "紧急停止后 continuum_active 应为 False")
    assert_true(bc5._state == ContinuumState.EMERGENCY_STOPPED, "状态应为 EMERGENCY_STOPPED")

    # 验证 emergency_stop 后再调用 continuum_beat 会抛出异常
    try:
        bc5.continuum_beat()
        assert_true(False, "紧急停止后再调用 continuum_beat 应抛出 RuntimeError")
    except RuntimeError as e:
        assert_true("emergency stopped" in str(e).lower(), "异常消息应包含 emergency stopped")

    resume5 = bc5.on_session_resume()
    assert_true(resume5["emergency_stopped"] == True, "恢复报告应标记 emergency_stopped")
    assert_true(resume5["emergency_reason"] == "Test emergency stop", "应保留 emergency_reason")

    # ── Test 6: 自续报告生成 ──
    logger.info("\n[Test 6] 自续报告生成")
    bc6 = BeatContinuum(MockSelfDriveEngine(), max_spins_per_pause=25)
    bc6.on_session_pause()
    report = bc6.get_continuum_report()
    assert_true("report_id" in report, "报告应有 report_id")
    assert_true(report["continuum_state"] == ContinuumState.MAX_SPINS_REACHED.value, "完成 max_spins 后状态应为 MAX_SPINS_REACHED")
    assert_true(report["spins_executed"] == 25, "报告应显示 25 次 spins")
    assert_true("fuel" in report, "报告应有 fuel 字段")
    assert_true("tasks" in report, "报告应有 tasks 字段")
    assert_true("anomalies" in report, "报告应有 anomalies 字段")
    assert_true("beat_chain" in report, "报告应有 beat_chain 字段")
    assert_true(len(report["snapshots"]) >= 2, "25 spins 应产生至少 2 个快照 (每10次一个)")
    assert_true(report["fuel"]["efficiency"] > 0, "fuel efficiency 应大于 0")

    # ── Test 7: 异常阈值触发紧急停止 ──
    logger.info("\n[Test 7] 异常阈值自动触发紧急停止")

    class AnomalyEngine:
        def spin(self):
            return {
                "status": "ok",
                "findings": [],
                "tasks_completed": [],
                "tasks_triggered": [],
                "fuel_consumed": 0.001,
                "fuel_generated": 0.001,
                "anomalies": [{"type": "test_anomaly", "severity": "high"}],
            }

    bc7 = BeatContinuum(AnomalyEngine(), max_spins_per_pause=100, anomaly_threshold=3)
    pause7 = bc7.on_session_pause()
    # 由于每次 spin 产生 1 个 anomaly，threshold=3，应在 3 次 spin 后触发 emergency_stop
    assert_true(
        pause7["actual_spins"] == 3,
        f"异常阈值应在 3 次 spin 后触发停止 (got {pause7['actual_spins']})"
    )
    assert_true(bc7._state == ContinuumState.EMERGENCY_STOPPED, "状态应为 EMERGENCY_STOPPED")
    assert_true(bc7._anomaly_count >= 3, "anomaly_count 应 >= 3")

    # ── Test 8: 多轮暂停/恢复 ──
    logger.info("\n[Test 8] 多轮暂停/恢复持久性")
    bc8 = BeatContinuum(MockSelfDriveEngine(), max_spins_per_pause=3)

    # 第一轮
    bc8.on_session_pause()
    r1 = bc8.on_session_resume()
    hist_after_r1 = len(bc8.beat_history)

    # 第二轮
    bc8.on_session_pause()
    r2 = bc8.on_session_resume()
    hist_after_r2 = len(bc8.beat_history)

    assert_true(hist_after_r1 == 3, "第一轮后 history 应有 3 条")
    assert_true(hist_after_r2 == 6, "第二轮后 history 应有 6 条")
    assert_true(r1["spins_executed"] == 3, "第一轮报告应有 3 spins")
    assert_true(r2["spins_executed"] == 3, "第二轮报告应有 3 spins")

    # ── Test 9: 引擎异常时的容错 ──
    logger.info("\n[Test 9] 引擎异常容错")

    class BrokenEngine:
        def spin(self):
            raise ValueError("Intentional breakage for testing")

    bc9 = BeatContinuum(BrokenEngine(), max_spins_per_pause=3)
    pause9 = bc9.on_session_pause()
    # 即使每次 spin 都失败，也应完成全部 spins（容错模式）
    assert_true(pause9["actual_spins"] == 3, "容错模式下应完成 3 次 spins")
    assert_true(len(bc9.beat_history) == 3, "应有 3 条 beat 记录（含错误状态）")
    assert_true(all(
        b.spin_result.get("status") == "error" for b in bc9.beat_history
    ), "所有记录应标记为 error 状态")

    # ── Test 10: 燃料计算精确性 ──
    logger.info("\n[Test 10] 燃料计算精确性")

    class PreciseEngine:
        def __init__(self):
            self._n = 0

        def spin(self):
            self._n += 1
            return {
                "status": "ok",
                "findings": [],
                "tasks_completed": [],
                "tasks_triggered": [],
                "fuel_consumed": 0.1,
                "fuel_generated": 0.15,
                "anomalies": [],
            }

    bc10 = BeatContinuum(PreciseEngine(), max_spins_per_pause=10)
    bc10.on_session_pause()
    report10 = bc10.get_continuum_report()
    assert_true(
        abs(report10["fuel"]["consumed"] - 1.0) < 0.0001,
        f"10 spins × 0.1 consumed = 1.0 (got {report10['fuel']['consumed']})"
    )
    assert_true(
        abs(report10["fuel"]["generated"] - 1.5) < 0.0001,
        f"10 spins × 0.15 generated = 1.5 (got {report10['fuel']['generated']})"
    )
    assert_true(
        abs(report10["fuel"]["net"] - 0.5) < 0.0001,
        f"Net fuel should be 0.5 (got {report10['fuel']['net']})"
    )

    # ── 测试总结 ──
    logger.info("\n" + "=" * 70)
    logger.info(f"测试结果: {tests_passed} 通过, {tests_failed} 失败")
    logger.info("=" * 70)

    if tests_failed > 0:
        logger.info("\n[!] 部分测试未通过，请检查实现")
        return False
    else:
        logger.info("\n[OK] 全部测试通过 — BeatContinuum 引擎就绪")
        return True


if __name__ == "__main__":
    import sys
    success = _run_tests()
    sys.exit(0 if success else 1)
