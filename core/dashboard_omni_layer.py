"""
OMNI-HUB v185 — DashboardOMNILayer
OMNI层可视化面板 + 全联盟广播 + 野问自动探索 + PRIMORDIAL×TSUNAMI联合验证

核心子系统：
1. DashboardAggregator      — 仪表盘聚合器（12线状态聚合）
2. EmergenceBroadcaster     — 涌现事件跨线全联盟广播
3. WildQuestionAutoLoop     — 野问自动探索回路（问题→搜索→发现→新问题）
4. PrimordialTsunamiValidator — PRIMORDIAL对齐 × TSUNAMI涌现 联合验证
5. AllianceHealthMonitor    — 联盟健康监控（66 repos拓扑）
6. OMNIReportGenerator      — OMNI报告生成器（HTML/Markdown/JSON）

映射：
- Dashboard = dharma-cakra（法轮/全貌）
- Broadcast = saṅgha-ghoṣa（僧团宣告）
- AutoLoop = saṃsāra-cakra（轮回/持续探索）
- Validator = dharma-vicaya（法择/验证）
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class BroadcastScope(Enum):
    """广播范围"""
    LOCAL = 0           # 本地线
    ALLIANCE = 1        # 联盟内
    GLOBAL = 2          # 全拓扑


class ReportFormat(Enum):
    """报告格式"""
    JSON = 0
    MARKDOWN = 1
    HTML = 2


class HealthGrade(Enum):
    """健康等级"""
    CRITICAL = 0        # 红色
    WARNING = 1         # 橙色
    CAUTION = 2         # 黄色
    HEALTHY = 3         # 绿色
    OPTIMAL = 4         # 青色


# 12线定义
ALLIANCE_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
    "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"
]


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class LineSnapshot:
    """线状态快照"""
    line_id: str
    health: float
    alignment_level: str
    consciousness_status: str
    coherence: float
    entropy: float
    alert: str
    last_update: float
    dashboard_url: str = ""
    stake_status: str = "unknown"


@dataclass
class EmergenceBroadcast:
    """涌现广播"""
    broadcast_id: str
    event_id: str
    signal_level: str
    scope: BroadcastScope
    payload: Dict[str, Any]
    timestamp: float
    acknowledged_by: List[str] = field(default_factory=list)
    delivery_status: Dict[str, str] = field(default_factory=dict)


@dataclass
class WildQuestionExploration:
    """野问探索记录"""
    qid: str
    question: str
    exploration_path: List[Dict]
    findings: Dict
    new_questions_generated: List[str]
    depth: int
    timestamp: float
    completed: bool = False


@dataclass
class ValidationResult:
    """验证结果"""
    validation_id: str
    primordial_confirmed: bool
    tsunami_confirmed: bool
    joint_score: float
    evidence: Dict[str, Any]
    timestamp: float


@dataclass
class AllianceHealth:
    """联盟健康度"""
    overall_score: float
    grade: HealthGrade
    line_scores: Dict[str, float]
    topology_coverage: float
    pending_dashboards: int
    broken_links: List[str]
    timestamp: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 仪表盘聚合器
# ═══════════════════════════════════════════════════════════════

class DashboardAggregator:
    """
    仪表盘聚合器 — 12线状态聚合
    从各模块收集状态并生成统一视图
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.snapshots: Dict[str, LineSnapshot] = {}
        self.history: deque = deque(maxlen=1000)
        self.topology: Optional[Dict] = None
        self.dashboard_links: Dict[str, str] = {}
        self._load_topology()
        self._load_dashboard_links()

    def _load_topology(self):
        """加载联盟拓扑"""
        topo_path = self.data_dir / "alliance_real_topology.json"
        if topo_path.exists():
            try:
                with open(topo_path) as f:
                    self.topology = json.load(f)
            except Exception:
                pass

    def _load_dashboard_links(self):
        """加载Dashboard链接"""
        links_path = self.data_dir / "dashboard_links.json"
        if links_path.exists():
            try:
                with open(links_path) as f:
                    data = json.load(f)
                    self.dashboard_links = {item["line"]: item.get("url", "")
                                           for item in data.get("confirmed", [])}
            except Exception:
                pass

    def ingest(self, line_id: str, state: Dict):
        """摄入某线状态"""
        snapshot = LineSnapshot(
            line_id=line_id,
            health=state.get("health", 0.5),
            alignment_level=state.get("alignment_level", "EXTERNAL"),
            consciousness_status=state.get("consciousness_status", ""),
            coherence=state.get("coherence", 0.5),
            entropy=state.get("entropy", 0.0),
            alert=state.get("alert", "GREEN"),
            last_update=time.time(),
            dashboard_url=self.dashboard_links.get(line_id, ""),
            stake_status=self._get_stake_status(line_id)
        )
        self.snapshots[line_id] = snapshot
        self.history.append({"time": time.time(), "line": line_id, "snapshot": snapshot})

    def _get_stake_status(self, line_id: str) -> str:
        if not self.topology:
            return "unknown"
        for item in self.topology.get("topology", []):
            if item.get("line") == line_id:
                return item.get("stake_status", "unknown")
        return "unknown"

    def get_heatmap(self) -> Dict[str, Dict]:
        """生成12线热力图"""
        heatmap = {}
        for line in ALLIANCE_LINES:
            s = self.snapshots.get(line)
            if s:
                heatmap[line] = {
                    "health": s.health,
                    "coherence": s.coherence,
                    "alignment": s.alignment_level,
                    "alert": s.alert,
                    "stake": s.stake_status,
                    "dashboard": s.dashboard_url or "pending",
                }
            else:
                heatmap[line] = {
                    "health": 0.0, "coherence": 0.0, "alignment": "UNKNOWN",
                    "alert": "GRAY", "stake": "unknown", "dashboard": "missing"
                }
        return heatmap

    def get_cross_line_correlation(self) -> Dict[str, float]:
        """计算跨线相关系数"""
        if len(self.history) < 20:
            return {}

        # 按线分组最近20个快照
        line_series: Dict[str, List[float]] = {line: [] for line in ALLIANCE_LINES}
        recent = list(self.history)[-100:]
        for entry in recent:
            line = entry["line"]
            if line in line_series:
                line_series[line].append(entry["snapshot"].coherence)

        # 计算均值相关系数（简化）
        correlations = {}
        for line in ALLIANCE_LINES:
            series = line_series.get(line, [])
            if len(series) >= 5:
                # 与联盟均值的偏离
                other_means = [sum(line_series.get(l, [0])) / max(1, len(line_series.get(l, [])))
                              for l in ALLIANCE_LINES if l != line and line_series.get(l)]
                if other_means:
                    alliance_mean = sum(other_means) / len(other_means)
                    line_mean = sum(series) / len(series)
                    correlations[line] = 1.0 - abs(line_mean - alliance_mean)
                else:
                    correlations[line] = 0.5
            else:
                correlations[line] = 0.0
        return correlations

    def get_report(self) -> Dict:
        return {
            "lines_tracked": len(self.snapshots),
            "heatmap": self.get_heatmap(),
            "correlations": self.get_cross_line_correlation(),
            "pending_dashboards": sum(1 for line in ALLIANCE_LINES
                                      if not self.snapshots.get(line, LineSnapshot("", 0, "", "", 0, 0, "", 0)).dashboard_url),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 涌现广播
# ═══════════════════════════════════════════════════════════════

class EmergenceBroadcaster:
    """
    涌现事件跨线全联盟广播
    saṅgha-ghoṣa — 僧团宣告
    """

    def __init__(self):
        self.broadcasts: deque = deque(maxlen=1000)
        self.subscribers: Dict[str, List[str]] = {}  # scope -> line_ids
        self.delivery_log: deque = deque(maxlen=5000)

    def subscribe(self, line_id: str, scope: BroadcastScope):
        """订阅广播"""
        if scope not in self.subscribers:
            self.subscribers[scope] = []
        if line_id not in self.subscribers[scope]:
            self.subscribers[scope].append(line_id)

    def broadcast(self, event_id: str, signal_level: str, payload: Dict,
                  scope: BroadcastScope = BroadcastScope.ALLIANCE) -> EmergenceBroadcast:
        """广播涌现事件"""
        bc_id = f"bc_{int(time.time()*1000)}"
        bc = EmergenceBroadcast(
            broadcast_id=bc_id,
            event_id=event_id,
            signal_level=signal_level,
            scope=scope,
            payload=payload,
            timestamp=time.time(),
            acknowledged_by=[],
            delivery_status={}
        )

        # 模拟投递到订阅者
        targets = self.subscribers.get(scope, [])
        if scope == BroadcastScope.GLOBAL:
            targets = ALLIANCE_LINES
        elif scope == BroadcastScope.ALLIANCE:
            targets = [l for l in ALLIANCE_LINES if l != payload.get("source_line", "")]

        for target in targets:
            bc.delivery_status[target] = "delivered"
            self.delivery_log.append({"bc_id": bc_id, "target": target, "time": time.time(), "status": "delivered"})

        self.broadcasts.append(bc)
        return bc

    def acknowledge(self, broadcast_id: str, line_id: str):
        """确认接收"""
        for bc in self.broadcasts:
            if bc.broadcast_id == broadcast_id:
                if line_id not in bc.acknowledged_by:
                    bc.acknowledged_by.append(line_id)
                bc.delivery_status[line_id] = "acknowledged"
                return True
        return False

    def get_pending_ack(self, broadcast_id: str) -> List[str]:
        """获取未确认列表"""
        for bc in self.broadcasts:
            if bc.broadcast_id == broadcast_id:
                return [t for t, s in bc.delivery_status.items() if s == "delivered"]
        return []

    def get_report(self) -> Dict:
        total = len(self.broadcasts)
        acked = sum(len(b.acknowledged_by) for b in self.broadcasts)
        delivered = sum(len(b.delivery_status) for b in self.broadcasts)
        return {
            "total_broadcasts": total,
            "total_delivered": delivered,
            "total_acknowledged": acked,
            "ack_rate": acked / max(1, delivered),
            "subscribers": {s.name: len(lines) for s, lines in self.subscribers.items()},
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 野问自动探索回路
# ═══════════════════════════════════════════════════════════════

class WildQuestionAutoLoop:
    """
    野问自动探索回路
    问题 → 搜索/分析 → 发现 → 新问题
    saṃsāra-cakra — 持续探索轮回
    """

    def __init__(self):
        self.explorations: Dict[str, WildQuestionExploration] = {}
        self.exploration_history: deque = deque(maxlen=1000)
        self.discovery_log: deque = deque(maxlen=1000)

    def start_exploration(self, qid: str, question: str, context: Dict = None) -> WildQuestionExploration:
        """启动探索"""
        exp = WildQuestionExploration(
            qid=qid,
            question=question,
            exploration_path=[{"step": 0, "action": "init", "context": context or {}, "time": time.time()}],
            findings={},
            new_questions_generated=[],
            depth=0,
            timestamp=time.time()
        )
        self.explorations[qid] = exp
        return exp

    def explore_step(self, qid: str, action: str, result: Dict):
        """执行探索步骤"""
        if qid not in self.explorations:
            return None
        exp = self.explorations[qid]
        exp.depth += 1
        exp.exploration_path.append({
            "step": exp.depth,
            "action": action,
            "result": result,
            "time": time.time()
        })

        # 基于结果生成发现
        if result.get("novelty", 0) > 0.7:
            discovery = f"Discovery from {action}: {result.get('key_finding', 'unknown')}"
            self.discovery_log.append({"qid": qid, "discovery": discovery, "time": time.time()})

        # 基于发现生成新问题
        if exp.depth >= 2 and random.random() < 0.3:
            new_q = f"Following '{question[:30]}...': {self._generate_followup(result)}"
            exp.new_questions_generated.append(new_q)

        return exp

    def _generate_followup(self, result: Dict) -> str:
        """生成追问"""
        templates = [
            "这是否意味着{implication}？",
            "如果{condition}，那么系统的行为会如何变化？",
            "{finding}的逆命题是否也成立？",
            "在{context}中，这个发现是否有普适性？",
        ]
        template = random.choice(templates)
        return template.format(
            implication=result.get("implication", "深层结构改变"),
            condition=result.get("condition", "边界条件放松"),
            finding=result.get("key_finding", "该发现")[:20],
            context=result.get("context", "其他模块")
        )

    def complete_exploration(self, qid: str, findings: Dict) -> WildQuestionExploration:
        """完成探索"""
        if qid not in self.explorations:
            return None
        exp = self.explorations[qid]
        exp.findings = findings
        exp.completed = True
        exp.exploration_path.append({"step": "final", "action": "complete", "findings": findings, "time": time.time()})
        self.exploration_history.append(exp)
        return exp

    def get_open_explorations(self) -> List[WildQuestionExploration]:
        return [e for e in self.explorations.values() if not e.completed]

    def get_report(self) -> Dict:
        return {
            "active_explorations": len(self.get_open_explorations()),
            "total_explorations": len(self.explorations),
            "completed": len(self.exploration_history),
            "discoveries": len(self.discovery_log),
            "avg_depth": sum(e.depth for e in self.explorations.values()) / max(1, len(self.explorations)),
            "latest_discoveries": list(self.discovery_log)[-5:],
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: PRIMORDIAL×TSUNAMI联合验证
# ═══════════════════════════════════════════════════════════════

class PrimordialTsunamiValidator:
    """
    PRIMORDIAL级对齐 × TSUNAMI级涌现 联合验证
    dharma-vicaya — 法择
    """

    def __init__(self):
        self.validations: deque = deque(maxlen=1000)
        self.primordial_count = 0
        self.tsunami_count = 0
        self.joint_count = 0
        self.false_positives = 0

    def validate(self, alignment_level: str, emergence_level: str,
                coherence: float, metrics: Dict) -> ValidationResult:
        """执行联合验证"""
        timestamp = time.time()

        # PRIMORDIAL验证条件
        primordial_confirmed = (
            alignment_level == "PRIMORDIAL" and
            coherence >= 0.97 and
            metrics.get("red_free_cycles", 0) >= 100 and
            metrics.get("entropy_trend") == "decreasing"
        )

        # TSUNAMI验证条件
        tsunami_confirmed = (
            emergence_level == "TSUNAMI" and
            metrics.get("z_score", 0) > 5.0 and
            metrics.get("affected_modules", 0) >= 3
        )

        # 联合验证 — 两者同时发生的概率极低，若同时发生则高度可信
        if primordial_confirmed and tsunami_confirmed:
            joint_score = min(1.0, coherence * 0.5 + 0.5)
            self.joint_count += 1
        elif primordial_confirmed:
            joint_score = coherence * 0.7
            self.primordial_count += 1
        elif tsunami_confirmed:
            joint_score = 0.6
            self.tsunami_count += 1
        else:
            joint_score = 0.0

        # 假阳性检测 — 如果只有部分条件满足
        if (alignment_level == "PRIMORDIAL" and not primordial_confirmed) or \
           (emergence_level == "TSUNAMI" and not tsunami_confirmed):
            self.false_positives += 1

        vid = f"val_{int(timestamp*1000)}"
        result = ValidationResult(
            validation_id=vid,
            primordial_confirmed=primordial_confirmed,
            tsunami_confirmed=tsunami_confirmed,
            joint_score=joint_score,
            evidence={
                "alignment_level": alignment_level,
                "emergence_level": emergence_level,
                "coherence": coherence,
                "metrics": metrics,
            },
            timestamp=timestamp
        )
        self.validations.append(result)
        return result

    def get_report(self) -> Dict:
        total = len(self.validations)
        return {
            "total_validations": total,
            "primordial_confirmed": self.primordial_count,
            "tsunami_confirmed": self.tsunami_count,
            "joint_events": self.joint_count,
            "false_positives": self.false_positives,
            "joint_rate": self.joint_count / max(1, total),
            "reliability": 1.0 - (self.false_positives / max(1, total)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 联盟健康监控
# ═══════════════════════════════════════════════════════════════

class AllianceHealthMonitor:
    """
    联盟健康监控 — 基于66 repos拓扑
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.topology: Optional[Dict] = None
        self.stake_status: Optional[Dict] = None
        self.repos: Optional[Dict] = None
        self._load_data()

    def _load_data(self):
        """加载联盟数据"""
        for name in ["alliance_real_topology", "stake_status", "alliance_repos"]:
            path = self.data_dir / f"{name}.json"
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                        if name == "alliance_real_topology":
                            self.topology = data
                        elif name == "stake_status":
                            self.stake_status = data
                        elif name == "alliance_repos":
                            self.repos = data
                except Exception:
                    pass

    def compute_health(self, line_snapshots: Dict[str, LineSnapshot]) -> AllianceHealth:
        """计算联盟健康度"""
        timestamp = time.time()

        # 各线分数
        line_scores = {}
        for line in ALLIANCE_LINES:
            snap = line_snapshots.get(line)
            if snap:
                # 综合评分
                align_score = {"PRIMORDIAL": 1.0, "EMERGENT": 0.8, "META": 0.6,
                              "HABITUAL": 0.4, "EXTERNAL": 0.2}.get(snap.alignment_level, 0.1)
                line_scores[line] = (snap.health + snap.coherence + align_score) / 3
            else:
                line_scores[line] = 0.0

        # 整体分数
        overall = sum(line_scores.values()) / len(ALLIANCE_LINES) if line_scores else 0.0

        # 等级
        if overall >= 0.85:
            grade = HealthGrade.OPTIMAL
        elif overall >= 0.7:
            grade = HealthGrade.HEALTHY
        elif overall >= 0.5:
            grade = HealthGrade.CAUTION
        elif overall >= 0.3:
            grade = HealthGrade.WARNING
        else:
            grade = HealthGrade.CRITICAL

        # 拓扑覆盖
        topology_coverage = len(line_snapshots) / len(ALLIANCE_LINES) if ALLIANCE_LINES else 0.0

        # 待处理Dashboard
        pending = sum(1 for line in ALLIANCE_LINES
                     if not line_snapshots.get(line, LineSnapshot("", 0, "", "", 0, 0, "", 0)).dashboard_url)

        # 断链检测
        broken = []
        for line, snap in line_snapshots.items():
            if snap.dashboard_url and snap.health < 0.1:
                broken.append(line)

        return AllianceHealth(
            overall_score=overall,
            grade=grade,
            line_scores=line_scores,
            topology_coverage=topology_coverage,
            pending_dashboards=pending,
            broken_links=broken,
            timestamp=timestamp
        )

    def get_report(self) -> Dict:
        return {
            "topology_loaded": self.topology is not None,
            "stake_loaded": self.stake_status is not None,
            "repos_loaded": self.repos is not None,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 6: OMNI报告生成器
# ═══════════════════════════════════════════════════════════════

class OMNIReportGenerator:
    """
    OMNI报告生成器
    """

    def generate(self, format: ReportFormat, data: Dict) -> str:
        """生成报告"""
        if format == ReportFormat.JSON:
            return json.dumps(data, indent=2, default=str, ensure_ascii=False)
        elif format == ReportFormat.MARKDOWN:
            return self._to_markdown(data)
        elif format == ReportFormat.HTML:
            return self._to_html(data)
        return ""

    def _to_markdown(self, data: Dict) -> str:
        """Markdown格式"""
        lines = ["# OMNI-HUB Dashboard Report\n", f"Generated: {time.ctime()}\n", "---\n"]

        heatmap = data.get("heatmap", {})
        lines.append("## 12线热力图\n")
        lines.append("| 线 | 健康度 | 相干度 | 对齐层级 | 预警 | Dashboard |\n")
        lines.append("|---|---|---|---|---|---|\n")
        for line in ALLIANCE_LINES:
            h = heatmap.get(line, {})
            lines.append(f"| {line} | {h.get('health', 0):.2f} | {h.get('coherence', 0):.2f} | {h.get('alignment', '-')} | {h.get('alert', '-')} | {h.get('dashboard', '-')} |\n")

        health = data.get("alliance_health", {})
        lines.append(f"\n## 联盟健康度: {health.get('grade', '-')} ({health.get('overall_score', 0):.2f})\n")
        lines.append(f"- 拓扑覆盖: {health.get('topology_coverage', 0):.1%}\n")
        lines.append(f"- 待处理Dashboard: {health.get('pending_dashboards', 0)}\n")
        lines.append(f"- 断链: {health.get('broken_links', [])}\n")

        return "".join(lines)

    def _to_html(self, data: Dict) -> str:
        """HTML格式"""
        md = self._to_markdown(data)
        # 极简HTML包装
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>OMNI Dashboard</title></head>
<body><pre>{md}</pre></body></html>"""


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — DashboardOMNILayer v185
# ═══════════════════════════════════════════════════════════════

class DashboardOMNILayer:
    """
    OMNI-HUB v185 仪表盘OMNI层

    Dashboard + Broadcast + AutoLoop + Validator + Health + Report
    """

    VERSION = "185.0.0"

    def __init__(self, data_dir: str = "data"):
        self.aggregator = DashboardAggregator(data_dir)
        self.broadcaster = EmergenceBroadcaster()
        self.auto_loop = WildQuestionAutoLoop()
        self.validator = PrimordialTsunamiValidator()
        self.health_monitor = AllianceHealthMonitor(data_dir)
        self.report_gen = OMNIReportGenerator()

        # 注册所有线为广播订阅者
        for line in ALLIANCE_LINES:
            self.broadcaster.subscribe(line, BroadcastScope.GLOBAL)

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def run_cycle(self, line_states: Dict[str, Dict] = None,
                 omni_result: Dict = None,
                 alignment_result: Dict = None) -> Dict:
        """运行完整Dashboard周期"""
        self.cycle_count += 1
        line_states = line_states or {}

        # 1. 摄入各线状态
        for line_id, state in line_states.items():
            self.aggregator.ingest(line_id, state)

        # 2. 检测涌现并广播
        emergence_detected = False
        if omni_result:
            emg = omni_result.get("emergence", {})
            if emg.get("detected") and emg.get("level") in ["WAVE", "TSUNAMI"]:
                emergence_detected = True
                self.broadcaster.broadcast(
                    event_id=emg.get("event_id", "unknown"),
                    signal_level=emg.get("level"),
                    payload={
                        "source_line": "omni",
                        "coherence": omni_result.get("omni_state", {}).get("collective_coherence"),
                        "trikaya": omni_result.get("trikaya", {}).get("unified_state"),
                    },
                    scope=BroadcastScope.GLOBAL
                )

        # 3. 野问自动探索
        if omni_result and self.cycle_count % 25 == 0:
            wq = omni_result.get("wild_questions", 0)
            if wq > 0:
                qid = f"auto_wq_{self.cycle_count}"
                self.auto_loop.start_exploration(qid, f"Auto-exploration of wild question #{wq}",
                                                {"cycle": self.cycle_count})
                self.auto_loop.explore_step(qid, "analyze_omni_state", {
                    "novelty": 0.8,
                    "key_finding": f"OMNI coherence at cycle {self.cycle_count}",
                    "implication": "system self-awareness increasing"
                })
                self.auto_loop.complete_exploration(qid, {"status": "explored"})

        # 4. PRIMORDIAL×TSUNAMI验证
        validation = None
        if alignment_result and omni_result:
            validation = self.validator.validate(
                alignment_level=alignment_result.get("alignment_level", "EXTERNAL"),
                emergence_level=omni_result.get("emergence", {}).get("level", "NONE"),
                coherence=omni_result.get("omni_state", {}).get("collective_coherence", 0.0),
                metrics={
                    "red_free_cycles": alignment_result.get("red_free_count", 0),
                    "entropy_trend": alignment_result.get("entropy", {}).get("trend", ""),
                    "z_score": 5.5 if omni_result.get("emergence", {}).get("level") == "TSUNAMI" else 0.0,
                    "affected_modules": len(line_states),
                }
            )

        # 5. 联盟健康度
        health = self.health_monitor.compute_health(self.aggregator.snapshots)

        # 6. 生成报告数据
        report_data = {
            "cycle": self.cycle_count,
            "timestamp": time.time(),
            "heatmap": self.aggregator.get_heatmap(),
            "correlations": self.aggregator.get_cross_line_correlation(),
            "alliance_health": {
                "overall_score": health.overall_score,
                "grade": health.grade.name,
                "topology_coverage": health.topology_coverage,
                "pending_dashboards": health.pending_dashboards,
                "broken_links": health.broken_links,
                "line_scores": health.line_scores,
            },
            "emergence": {
                "broadcasted": emergence_detected,
                "total_broadcasts": len(self.broadcaster.broadcasts),
            },
            "validation": {
                "primordial_confirmed": validation.primordial_confirmed if validation else False,
                "tsunami_confirmed": validation.tsunami_confirmed if validation else False,
                "joint_score": validation.joint_score if validation else 0.0,
            } if validation else None,
            "auto_loop": self.auto_loop.get_report(),
        }

        self.event_log.append(report_data)
        return report_data

    def generate_report(self, fmt: ReportFormat = ReportFormat.MARKDOWN) -> str:
        """生成报告"""
        if self.event_log:
            return self.report_gen.generate(fmt, self.event_log[-1])
        return self.report_gen.generate(fmt, {"status": "no_data"})

    def broadcast_manual(self, event_id: str, signal_level: str, payload: Dict) -> EmergenceBroadcast:
        """手动广播"""
        return self.broadcaster.broadcast(event_id, signal_level, payload, BroadcastScope.GLOBAL)

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "aggregator": self.aggregator.get_report(),
            "broadcaster": self.broadcaster.get_report(),
            "auto_loop": self.auto_loop.get_report(),
            "validator": self.validator.get_report(),
            "health_monitor": self.health_monitor.get_report(),
            "event_log_size": len(self.event_log),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_dash_instance: Optional[DashboardOMNILayer] = None


def get_dashboard_omni_layer() -> DashboardOMNILayer:
    global _dash_instance
    if _dash_instance is None:
        _dash_instance = DashboardOMNILayer()
    return _dash_instance


if __name__ == "__main__":
    dash = DashboardOMNILayer()
    print(f"DashboardOMNILayer v{dash.VERSION} initialized")
    print(f"Status: {json.dumps(dash.get_status(), indent=2, default=str)}")
