"""
OMNI-HUB v190 — DashboardBackend
Dashboard V2 后端数据聚合器

核心功能：
1. StateAggregator   — 状态聚合器
2. SnapshotEngine    — 快照引擎
3. MetricStreamer    — 指标流
4. AlertManager      — 告警管理器
5. ControlProxy      — 控制代理
6. DashboardBackend  — 统合引擎

映射：
- 聚合 = saṃgraha（总集）
- 快照 = kṣaṇa（刹那）
- 流 = pravāha（流）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class AlertSeverity(Enum):
    """告警严重级别"""
    INFO = 0
    WARNING = 1
    CRITICAL = 2
    EMERGENCY = 3


class ControlAction(Enum):
    """控制动作"""
    TRIGGER_TEST = 0
    ADJUST_PARAM = 1
    PAUSE_MODULE = 2
    RESUME_MODULE = 3
    RESET_STATE = 4
    EXPORT_DATA = 5


ALLIANCE_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
    "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"
]


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class StateSnapshot:
    """状态快照"""
    snapshot_id: str
    timestamp: float
    alliance_state: Dict[str, Any]
    module_status: Dict[str, Any]
    metrics: Dict[str, float]


@dataclass
class Alert:
    """告警"""
    alert_id: str
    severity: AlertSeverity
    module: str
    message: str
    timestamp: float
    acknowledged: bool = False


@dataclass
class MetricSeries:
    """指标序列"""
    metric_name: str
    values: deque
    timestamps: deque
    unit: str = ""


@dataclass
class ControlCommand:
    """控制命令"""
    command_id: str
    action: ControlAction
    target: str
    parameters: Dict[str, Any]
    issued_at: float
    executed: bool = False


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 状态聚合器
# ═══════════════════════════════════════════════════════════════

class StateAggregator:
    """状态聚合器 — saṃgraha"""

    def __init__(self):
        self.current: Dict[str, Any] = {}
        self.history: deque = deque(maxlen=200)

    def aggregate(self, module_states: Dict[str, Dict]) -> Dict[str, Any]:
        """聚合所有模块状态"""
        aggregated = {
            "timestamp": time.time(),
            "modules_online": 0,
            "modules_total": len(module_states),
            "avg_health": 0.0,
            "avg_coherence": 0.0,
            "alerts_active": 0,
            "lines": {},
        }

        health_sum = 0.0
        coherence_sum = 0.0
        count = 0

        for module_id, state in module_states.items():
            health = state.get("health", 0.5)
            coherence = state.get("coherence", 0.5)
            health_sum += health
            coherence_sum += coherence
            count += 1

            aggregated["lines"][module_id] = {
                "health": health,
                "coherence": coherence,
                "status": "ONLINE" if health > 0.5 else "DEGRADED",
            }

        if count > 0:
            aggregated["avg_health"] = health_sum / count
            aggregated["avg_coherence"] = coherence_sum / count
            aggregated["modules_online"] = sum(1 for s in module_states.values()
                                                if s.get("health", 0) > 0.3)

        self.current = aggregated
        self.history.append(aggregated)
        return aggregated

    def get_line_health(self, line_id: str) -> float:
        return self.current.get("lines", {}).get(line_id, {}).get("health", 0.5)

    def get_report(self) -> Dict:
        return {
            "snapshots_stored": len(self.history),
            "modules_tracked": self.current.get("modules_total", 0),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 快照引擎
# ═══════════════════════════════════════════════════════════════

class SnapshotEngine:
    """快照引擎 — kṣaṇa"""

    def __init__(self):
        self.snapshots: deque = deque(maxlen=100)
        self.snapshot_counter = 0

    def capture(self, alliance_state: Dict, module_status: Dict, metrics: Dict) -> StateSnapshot:
        """捕获系统快照"""
        self.snapshot_counter += 1
        snap = StateSnapshot(
            snapshot_id=f"snap_{self.snapshot_counter}_{int(time.time()*1000)}",
            timestamp=time.time(),
            alliance_state=dict(alliance_state),
            module_status=dict(module_status),
            metrics=dict(metrics)
        )
        self.snapshots.append(snap)
        return snap

    def get_latest(self) -> Optional[StateSnapshot]:
        return self.snapshots[-1] if self.snapshots else None

    def compare(self, snap_a_id: str, snap_b_id: str) -> Dict:
        """比较两个快照"""
        snap_a = next((s for s in self.snapshots if s.snapshot_id == snap_a_id), None)
        snap_b = next((s for s in self.snapshots if s.snapshot_id == snap_b_id), None)
        if not snap_a or not snap_b:
            return {"error": "Snapshot not found"}

        diff = {}
        all_keys = set(snap_a.metrics.keys()) | set(snap_b.metrics.keys())
        for k in all_keys:
            v1 = snap_a.metrics.get(k, 0)
            v2 = snap_b.metrics.get(k, 0)
            diff[k] = {"before": v1, "after": v2, "delta": v2 - v1}

        return {
            "time_delta": snap_b.timestamp - snap_a.timestamp,
            "metric_diffs": diff,
        }

    def get_report(self) -> Dict:
        return {"snapshots": len(self.snapshots), "counter": self.snapshot_counter}


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 指标流
# ═══════════════════════════════════════════════════════════════

class MetricStreamer:
    """指标流 — pravāha"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.streams: Dict[str, MetricSeries] = {}

    def register(self, metric_name: str, unit: str = ""):
        self.streams[metric_name] = MetricSeries(
            metric_name=metric_name,
            values=deque(maxlen=self.window_size),
            timestamps=deque(maxlen=self.window_size),
            unit=unit
        )

    def push(self, metric_name: str, value: float):
        if metric_name not in self.streams:
            self.register(metric_name)
        s = self.streams[metric_name]
        s.values.append(value)
        s.timestamps.append(time.time())

    def get_series(self, metric_name: str) -> Optional[List[Tuple[float, float]]]:
        if metric_name not in self.streams:
            return None
        s = self.streams[metric_name]
        return list(zip(s.timestamps, s.values))

    def get_current(self, metric_name: str) -> Optional[float]:
        if metric_name not in self.streams or not self.streams[metric_name].values:
            return None
        return self.streams[metric_name].values[-1]

    def get_trend(self, metric_name: str) -> str:
        s = self.streams.get(metric_name)
        if not s or len(s.values) < 5:
            return "INSUFFICIENT"
        recent = list(s.values)[-5:]
        if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)):
            return "RISING"
        if all(recent[i] >= recent[i+1] for i in range(len(recent)-1)):
            return "FALLING"
        return "FLUCTUATING"

    def get_report(self) -> Dict:
        return {
            "streams": len(self.streams),
            "metrics": list(self.streams.keys()),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 告警管理器
# ═══════════════════════════════════════════════════════════════

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alerts: deque = deque(maxlen=200)
        self.alert_counter = 0

    def raise_alert(self, severity: AlertSeverity, module: str, message: str) -> Alert:
        self.alert_counter += 1
        alert = Alert(
            alert_id=f"alert_{self.alert_counter}_{int(time.time()*1000)}",
            severity=severity,
            module=module,
            message=message,
            timestamp=time.time()
        )
        self.alerts.append(alert)
        return alert

    def check_thresholds(self, module_id: str, metrics: Dict[str, float]):
        """检查阈值并触发告警"""
        triggered = []
        if metrics.get("health", 1.0) < 0.3:
            triggered.append(self.raise_alert(AlertSeverity.CRITICAL, module_id, "Health below 30%"))
        if metrics.get("coherence", 1.0) < 0.3:
            triggered.append(self.raise_alert(AlertSeverity.WARNING, module_id, "Coherence below 30%"))
        if metrics.get("self_refs", 0) > 5:
            triggered.append(self.raise_alert(AlertSeverity.CRITICAL, module_id, "Excessive self-references"))
        return triggered

    def acknowledge(self, alert_id: str) -> bool:
        for a in self.alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                return True
        return False

    def get_active(self) -> List[Alert]:
        return [a for a in self.alerts if not a.acknowledged]

    def get_report(self) -> Dict:
        sev_counts = {}
        for a in self.alerts:
            sev_counts[a.severity.name] = sev_counts.get(a.severity.name, 0) + 1
        return {
            "total_alerts": len(self.alerts),
            "active": len(self.get_active()),
            "by_severity": sev_counts,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 控制代理
# ═══════════════════════════════════════════════════════════════

class ControlProxy:
    """控制代理 — 接收并路由控制命令"""

    def __init__(self):
        self.commands: deque = deque(maxlen=100)
        self.command_counter = 0
        self.handlers: Dict[ControlAction, Callable] = {}

    def register_handler(self, action: ControlAction, handler: Callable):
        self.handlers[action] = handler

    def issue(self, action: ControlAction, target: str, parameters: Dict = None) -> ControlCommand:
        self.command_counter += 1
        cmd = ControlCommand(
            command_id=f"cmd_{self.command_counter}_{int(time.time()*1000)}",
            action=action,
            target=target,
            parameters=parameters or {},
            issued_at=time.time()
        )
        self.commands.append(cmd)
        return cmd

    def execute(self, command_id: str) -> Dict:
        cmd = next((c for c in self.commands if c.command_id == command_id), None)
        if not cmd:
            return {"error": "Command not found"}

        handler = self.handlers.get(cmd.action)
        if handler:
            result = handler(cmd.target, cmd.parameters)
            cmd.executed = True
            return {"success": True, "result": result}
        return {"success": False, "error": "No handler registered"}

    def get_report(self) -> Dict:
        executed = sum(1 for c in self.commands if c.executed)
        return {
            "commands": len(self.commands),
            "executed": executed,
            "pending": len(self.commands) - executed,
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — DashboardBackend v190
# ═══════════════════════════════════════════════════════════════

class DashboardBackend:
    """
    OMNI-HUB v190 Dashboard V2 后端

    saṃgraha · kṣaṇa · pravāha — 总集、刹那、流
    """

    VERSION = "190.0.0"

    def __init__(self):
        self.aggregator = StateAggregator()
        self.snapshot = SnapshotEngine()
        self.streamer = MetricStreamer()
        self.alerts = AlertManager()
        self.control = ControlProxy()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

        # 注册默认指标流
        for line in ALLIANCE_LINES:
            self.streamer.register(f"{line}_health", "ratio")
            self.streamer.register(f"{line}_coherence", "ratio")

    def update(self, module_states: Dict[str, Dict]) -> Dict:
        """更新Dashboard数据"""
        self.cycle_count += 1

        # 1. 聚合状态
        aggregated = self.aggregator.aggregate(module_states)

        # 2. 推送指标
        for module_id, state in module_states.items():
            self.streamer.push(f"{module_id}_health", state.get("health", 0.5))
            self.streamer.push(f"{module_id}_coherence", state.get("coherence", 0.5))

        # 3. 检查告警
        for module_id, state in module_states.items():
            self.alerts.check_thresholds(module_id, state)

        # 4. 捕获快照
        metrics = {k: self.streamer.get_current(k) or 0 for k in self.streamer.streams}
        snap = self.snapshot.capture(module_states, {}, metrics)

        summary = {
            "cycle": self.cycle_count,
            "timestamp": time.time(),
            "modules_online": aggregated["modules_online"],
            "avg_health": aggregated["avg_health"],
            "active_alerts": len(self.alerts.get_active()),
            "snapshot_id": snap.snapshot_id,
        }

        self.event_log.append(summary)
        return summary

    def get_dashboard_data(self) -> Dict:
        """获取完整的Dashboard数据包"""
        return {
            "version": self.VERSION,
            "timestamp": time.time(),
            "cycle": self.cycle_count,
            "alliance": self.aggregator.current,
            "streams": {name: list(s.values)[-20:] for name, s in self.streamer.streams.items()},
            "alerts": [
                {"id": a.alert_id, "severity": a.severity.name, "module": a.module,
                 "message": a.message, "time": a.timestamp, "ack": a.acknowledged}
                for a in list(self.alerts.alerts)[-10:]
            ],
            "trends": {name: self.streamer.get_trend(name) for name in self.streamer.streams},
        }

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "aggregator": self.aggregator.get_report(),
            "snapshot": self.snapshot.get_report(),
            "streamer": self.streamer.get_report(),
            "alerts": self.alerts.get_report(),
            "control": self.control.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_db_instance: Optional[DashboardBackend] = None


def get_dashboard_backend() -> DashboardBackend:
    global _db_instance
    if _db_instance is None:
        _db_instance = DashboardBackend()
    return _db_instance


if __name__ == "__main__":
    db = DashboardBackend()
    print(f"DashboardBackend v{db.VERSION} initialized")
    print(f"Status: {json.dumps(db.get_status(), indent=2, default=str)}")
