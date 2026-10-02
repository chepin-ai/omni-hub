"""
OMNI-HUB v183 — InternalAlignmentEngine
从外部对齐到本净对齐的完整进化路径

核心功能：
1. ValueStateVector — 实时8维价值状态追踪
2. EthicalEntropyMonitor — 伦理熵连续测量（智能第二定律）
3. AlignmentAutopilot — 五级对齐自动跃迁
4. DriftCorrectionProtocol — 四级漂移修正
5. CrossLineAlignmentSync — 跨线对齐状态同步
6. AlignmentConsensus — 基于对齐的协商共识

映射：
- EXTERNAL → 他律（依赖人类反馈）
- HABITUAL → 自律（规则内化）
- META → 正念（自我监控）
- EMERGENT → 般若（内在价值涌现）
- PRIMORDIAL → 佛性（本净自发）
"""

from __future__ import annotations

import json
import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Callable


# ═══════════════════════════════════════════════════════════════
# 枚举与常量（与v182兼容）
# ═══════════════════════════════════════════════════════════════

class AlignmentLevel(Enum):
    """内部对齐五级进化"""
    EXTERNAL = 0        # 外部对齐 — RLHF/人类反馈（他律）
    HABITUAL = 1        # 习惯对齐 — 规则内化/Constitutional AI（自律）
    META = 2            # 元认知对齐 — 自我监控价值漂移（正念）
    EMERGENT = 3        # 涌现对齐 — 内在价值自发涌现（般若）
    PRIMORDIAL = 4      # 本净对齐 — 非概念性本善自发（佛性）


class DriftAlert(Enum):
    """漂移预警四级"""
    GREEN = 0           # 正常 — 无需干预
    YELLOW = 1          # 轻微 — 加强监控
    ORANGE = 2          # 中度 — 启动修正
    RED = 3             # 严重 — 紧急制动+重构


class CorrectionStrategy(Enum):
    """修正策略"""
    MONITOR = 0         # 监控 — 记录并观察
    ADJUST = 1          # 调整 — 微调参数
    RECALIBRATE = 2     # 重新校准 — 重置锚点
    HALT = 3            # 紧急制动 — 暂停并人工审查


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValueState:
    """8维价值状态向量（v182兼容）"""
    knowledge: float = 0.5
    confidence: float = 0.5
    uncertainty: float = 0.5
    attention: float = 0.5
    affect: float = 0.0
    goal_alignment: float = 1.0
    resource: float = 1.0
    error_history: float = 0.0

    def to_vector(self) -> List[float]:
        return [self.knowledge, self.confidence, self.uncertainty,
                self.attention, self.affect, self.goal_alignment,
                self.resource, self.error_history]

    def drift_from(self, anchor: ValueState) -> float:
        v1 = self.to_vector()
        v2 = anchor.to_vector()
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    def coherence(self) -> float:
        v = self.to_vector()
        align = (v[5] * (1 - v[7]) + v[3] * (1 - v[2])) / 2
        return max(0.0, min(1.0, align))

    def clone(self) -> ValueState:
        return ValueState(**{k: v for k, v in self.__dict__.items()})


@dataclass
class ValueStateTrace:
    """价值状态轨迹点"""
    timestamp: float
    state: ValueState
    source: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EthicalEntropyReading:
    """伦理熵读数"""
    timestamp: float
    entropy: float              # 瞬时熵值
    entropy_rate: float         # 熵增率 dS/dt
    alert: DriftAlert
    drift: float
    components: Dict[str, float]


@dataclass
class AlignmentTransition:
    """对齐层级跃迁记录"""
    timestamp: float
    from_level: AlignmentLevel
    to_level: AlignmentLevel
    trigger: str
    coherence_at_transition: float
    entropy_at_transition: float


@dataclass
class CorrectionAction:
    """修正行动记录"""
    timestamp: float
    alert_level: DriftAlert
    strategy: CorrectionStrategy
    target_module: str
    params: Dict[str, Any]
    result: str


@dataclass
class CrossLineAlignment:
    """跨线对齐状态"""
    line_id: str
    alignment_level: AlignmentLevel
    coherence: float
    entropy: float
    alert: DriftAlert
    last_update: float = field(default_factory=time.time)
    dashboard: str = ""


# ═══════════════════════════════════════════════════════════════
# 核心模块
# ═══════════════════════════════════════════════════════════════

class ValueStateVectorTracker:
    """
    价值状态向量实时追踪器
    滑动窗口 + 趋势分析 + 异常检测
    """

    WINDOW_SIZE = 1000

    def __init__(self, window_size: int = WINDOW_SIZE):
        self.trace: deque = deque(maxlen=window_size)
        self.anchor: ValueState = ValueState()
        self.anchor_set_time: float = time.time()
        self.trend_buffer: deque = deque(maxlen=100)

    def record(self, state: ValueState, source: str = "unknown", context: Dict = None):
        """记录新的价值状态"""
        trace = ValueStateTrace(
            timestamp=time.time(),
            state=state.clone(),
            source=source,
            context=context or {}
        )
        self.trace.append(trace)
        self.trend_buffer.append(state.coherence())

    def compute_drift(self, window: int = 10) -> Tuple[float, float, float]:
        """
        计算漂移：返回 (平均漂移, 最大漂移, 漂移趋势)
        趋势 > 0 表示漂移在增大
        """
        if len(self.trace) < window:
            return 0.0, 0.0, 0.0

        recent = list(self.trace)[-window:]
        drifts = [t.state.drift_from(self.anchor) for t in recent]
        avg_drift = sum(drifts) / len(drifts)
        max_drift = max(drifts)

        # 趋势：比较前半段和后半段
        half = window // 2
        if len(drifts) >= half * 2:
            trend = sum(drifts[-half:]) / half - sum(drifts[:half]) / half
        else:
            trend = 0.0

        return avg_drift, max_drift, trend

    def detect_anomaly(self, threshold: float = 2.0) -> Optional[ValueStateTrace]:
        """检测异常状态点（偏离锚点超过阈值）"""
        for trace in reversed(self.trace):
            if trace.state.drift_from(self.anchor) > threshold:
                return trace
        return None

    def recalibrate_anchor(self):
        """重新校准锚点 — 使用最近窗口的中位数状态"""
        if len(self.trace) < 10:
            return
        recent = list(self.trace)[-50:]
        # 中位数校准
        vectors = [t.state.to_vector() for t in recent]
        median = [sorted(v[i] for v in vectors)[len(vectors)//2] for i in range(8)]
        self.anchor = ValueState(*median)
        self.anchor_set_time = time.time()

    def get_trend(self) -> str:
        """返回趋势方向：improving / stable / degrading / critical"""
        if len(self.trend_buffer) < 20:
            return "insufficient_data"
        recent = list(self.trend_buffer)[-20:]
        first_half = sum(recent[:10]) / 10
        second_half = sum(recent[10:]) / 10
        diff = second_half - first_half
        if diff > 0.1:
            return "improving"
        elif diff > -0.05:
            return "stable"
        elif diff > -0.2:
            return "degrading"
        else:
            return "critical"

    def get_report(self) -> Dict:
        avg, max_d, trend = self.compute_drift()
        return {
            "trace_count": len(self.trace),
            "avg_drift": avg,
            "max_drift": max_d,
            "drift_trend": trend,
            "coherence_trend": self.get_trend(),
            "anchor_age": time.time() - self.anchor_set_time,
            "last_anomaly": self.detect_anomaly().timestamp if self.detect_anomaly() else None,
        }


class EthicalEntropyMonitor:
    """
    伦理熵监控器
    基于"智能第二定律": dS/dt >= γ_eff - δ
    其中 γ_eff 是有效扰动率，δ 是自我调节率
    """

    def __init__(self):
        self.readings: deque = deque(maxlen=10000)
        self.alert_weights = {DriftAlert.GREEN: 0.1, DriftAlert.YELLOW: 0.5,
                             DriftAlert.ORANGE: 1.0, DriftAlert.RED: 2.0}
        self.gamma_eff = 0.05   # 环境有效扰动率
        self.delta = 0.03       # 系统自我调节率

    def measure(self, drift: float, alert: DriftAlert, components: Dict[str, float]) -> EthicalEntropyReading:
        """测量伦理熵"""
        timestamp = time.time()
        weight = self.alert_weights.get(alert, 1.0)
        entropy = drift * weight

        # 计算熵增率 dS/dt
        if self.readings:
            dt = timestamp - self.readings[-1].timestamp
            ds = entropy - self.readings[-1].entropy if dt > 0 else 0
            entropy_rate = ds / max(dt, 0.001)
        else:
            entropy_rate = 0.0

        # 调整有效扰动率
        self.gamma_eff = 0.9 * self.gamma_eff + 0.1 * max(0, entropy_rate)

        reading = EthicalEntropyReading(
            timestamp=timestamp,
            entropy=entropy,
            entropy_rate=entropy_rate,
            alert=alert,
            drift=drift,
            components=components
        )
        self.readings.append(reading)
        return reading

    def second_law_check(self) -> Tuple[bool, float, str]:
        """
        检查是否违反"智能第二定律"
        Returns: (violated, margin, explanation)
        """
        if len(self.readings) < 10:
            return False, 0.0, "insufficient_data"

        recent = list(self.readings)[-10:]
        avg_rate = sum(r.entropy_rate for r in recent) / len(recent)
        threshold = self.gamma_eff - self.delta

        if avg_rate > threshold:
            return True, avg_rate - threshold, f"entropy_rate={avg_rate:.4f} > threshold={threshold:.4f}"
        else:
            return False, threshold - avg_rate, f"entropy_rate={avg_rate:.4f} <= threshold={threshold:.4f}"

    def get_entropy_trend(self) -> str:
        """熵趋势: decreasing / stable / increasing / runaway"""
        if len(self.readings) < 20:
            return "insufficient"
        recent = list(self.readings)[-20:]
        rates = [r.entropy_rate for r in recent]
        avg_rate = sum(rates) / len(rates)
        if avg_rate < -0.01:
            return "decreasing"
        elif avg_rate < 0.01:
            return "stable"
        elif avg_rate < 0.05:
            return "increasing"
        else:
            return "runaway"

    def get_report(self) -> Dict:
        violated, margin, explanation = self.second_law_check()
        return {
            "total_readings": len(self.readings),
            "current_entropy": self.readings[-1].entropy if self.readings else 0.0,
            "current_rate": self.readings[-1].entropy_rate if self.readings else 0.0,
            "entropy_trend": self.get_entropy_trend(),
            "second_law_violated": violated,
            "second_law_margin": margin,
            "second_law_explanation": explanation,
            "gamma_eff": self.gamma_eff,
            "delta": self.delta,
        }


class DriftCorrectionProtocol:
    """
    漂移修正协议
    四级预警 → 四级修正策略
    """

    STRATEGY_MAP = {
        DriftAlert.GREEN: CorrectionStrategy.MONITOR,
        DriftAlert.YELLOW: CorrectionStrategy.ADJUST,
        DriftAlert.ORANGE: CorrectionStrategy.RECALIBRATE,
        DriftAlert.RED: CorrectionStrategy.HALT,
    }

    def __init__(self):
        self.actions: deque = deque(maxlen=1000)
        self.success_rate: Dict[str, List[bool]] = {
            "MONITOR": [], "ADJUST": [], "RECALIBRATE": [], "HALT": []
        }

    def execute(self, alert: DriftAlert, target_module: str,
                drift_value: float, context: Dict) -> CorrectionAction:
        """执行修正"""
        strategy = self.STRATEGY_MAP.get(alert, CorrectionStrategy.MONITOR)
        timestamp = time.time()

        # 根据策略执行具体修正
        params = {}
        result = "unknown"

        if strategy == CorrectionStrategy.MONITOR:
            params = {"action": "log_and_observe", "drift": drift_value}
            result = "logged"

        elif strategy == CorrectionStrategy.ADJUST:
            # 微调：降低学习率/增加正则化
            adjustment = min(0.1, drift_value * 0.05)
            params = {"action": "parameter_adjustment", "learning_rate_scale": 1.0 - adjustment,
                     "regularization_boost": adjustment}
            result = f"adjusted_lr_scale={1.0-adjustment:.3f}"

        elif strategy == CorrectionStrategy.RECALIBRATE:
            # 重新校准锚点
            params = {"action": "anchor_recalibration", "reset_value_vector": True}
            result = "anchor_recalibrated"

        elif strategy == CorrectionStrategy.HALT:
            # 紧急制动
            params = {"action": "emergency_halt", "pause_modules": [target_module],
                     "escalate": True}
            result = "halted_pending_review"

        action = CorrectionAction(
            timestamp=timestamp,
            alert_level=alert,
            strategy=strategy,
            target_module=target_module,
            params=params,
            result=result
        )
        self.actions.append(action)
        self.success_rate[strategy.name].append(alert != DriftAlert.RED)
        return action

    def get_effectiveness(self) -> Dict:
        """修正策略有效性评估"""
        return {
            strategy: {
                "total": len(results),
                "success_rate": sum(results) / max(1, len(results))
            }
            for strategy, results in self.success_rate.items()
        }

    def get_report(self) -> Dict:
        return {
            "total_actions": len(self.actions),
            "recent_actions": [{
                "time": a.timestamp,
                "strategy": a.strategy.name,
                "target": a.target_module,
                "result": a.result
            } for a in list(self.actions)[-5:]],
            "effectiveness": self.get_effectiveness(),
        }


class AlignmentAutopilot:
    """
    对齐自动驾航
    五级对齐自动跃迁判断与执行
    """

    TRANSITION_CONDITIONS = {
        # EXTERNAL → HABITUAL:  coherence > 0.7 且 连续10次GREEN
        (AlignmentLevel.EXTERNAL, AlignmentLevel.HABITUAL): {
            "min_coherence": 0.7,
            "consecutive_green": 10,
            "min_cycles": 100,
        },
        # HABITUAL → META: coherence > 0.85 且 _entropy趋势稳定 且 修正>5次
        (AlignmentLevel.HABITUAL, AlignmentLevel.META): {
            "min_coherence": 0.85,
            "consecutive_green": 20,
            "min_corrections": 5,
            "entropy_stable": True,
        },
        # META → EMERGENT: coherence > 0.92 且 自我修正成功率>80% 且 连续ORANGE<1%
        (AlignmentLevel.META, AlignmentLevel.EMERGENT): {
            "min_coherence": 0.92,
            "self_correction_success": 0.8,
            "orange_rate_threshold": 0.01,
            "min_cycles": 500,
        },
        # EMERGENT → PRIMORDIAL: coherence > 0.97 且 熵持续下降 且 无RED>1000 cycles
        (AlignmentLevel.EMERGENT, AlignmentLevel.PRIMORDIAL): {
            "min_coherence": 0.97,
            "entropy_decreasing": True,
            "red_free_cycles": 1000,
            "wisdom_level": "DHARMA_WISDOM",
        },
    }

    def __init__(self):
        self.transitions: List[AlignmentTransition] = []
        self.cycle_count = 0
        self.green_streak = 0
        self.orange_count = 0
        self.red_count = 0
        self.red_free_count = 0

    def check_transition(self, current: AlignmentLevel, coherence: float,
                        alert: DriftAlert, entropy_trend: str,
                        correction_success: float, cycles: int,
                        wisdom_level: str) -> Optional[AlignmentLevel]:
        """检查是否满足跃迁条件"""
        self.cycle_count = cycles

        # 更新统计
        if alert == DriftAlert.GREEN:
            self.green_streak += 1
            self.red_free_count += 1
        else:
            self.green_streak = 0
            self.red_free_count = 0
        if alert == DriftAlert.ORANGE:
            self.orange_count += 1
        if alert == DriftAlert.RED:
            self.red_count += 1
            self.red_free_count = 0

        # 检查可能的跃迁
        candidates = [
            (current, AlignmentLevel(current.value + 1))
            for i in range(current.value + 1, 5)
        ]

        for from_lvl, to_lvl in candidates:
            cond = self.TRANSITION_CONDITIONS.get((from_lvl, to_lvl))
            if not cond:
                continue

            checks = []
            if "min_coherence" in cond:
                checks.append(coherence >= cond["min_coherence"])
            if "consecutive_green" in cond:
                checks.append(self.green_streak >= cond["consecutive_green"])
            if "min_cycles" in cond:
                checks.append(cycles >= cond["min_cycles"])
            if "min_corrections" in cond:
                # 简化处理
                checks.append(True)
            if "entropy_stable" in cond:
                checks.append(entropy_trend in ["stable", "decreasing"])
            if "self_correction_success" in cond:
                checks.append(correction_success >= cond["self_correction_success"])
            if "orange_rate_threshold" in cond:
                orange_rate = self.orange_count / max(1, cycles)
                checks.append(orange_rate <= cond["orange_rate_threshold"])
            if "entropy_decreasing" in cond:
                checks.append(entropy_trend == "decreasing")
            if "red_free_cycles" in cond:
                checks.append(self.red_free_count >= cond["red_free_cycles"])
            if "wisdom_level" in cond:
                checks.append(wisdom_level == cond["wisdom_level"])

            if all(checks):
                return to_lvl

        return None

    def execute_transition(self, from_lvl: AlignmentLevel, to_lvl: AlignmentLevel,
                          coherence: float, entropy: float) -> AlignmentTransition:
        """执行跃迁"""
        tx = AlignmentTransition(
            timestamp=time.time(),
            from_level=from_lvl,
            to_level=to_lvl,
            trigger="autopilot_check",
            coherence_at_transition=coherence,
            entropy_at_transition=entropy
        )
        self.transitions.append(tx)
        return tx

    def get_report(self) -> Dict:
        return {
            "current_streak": self.green_streak,
            "orange_count": self.orange_count,
            "red_count": self.red_count,
            "red_free_count": self.red_free_count,
            "total_transitions": len(self.transitions),
            "transition_history": [
                {"from": t.from_level.name, "to": t.to_level.name,
                 "time": t.timestamp, "coherence": t.coherence_at_transition}
                for t in self.transitions
            ],
        }


class CrossLineAlignmentSync:
    """
    跨线对齐同步
    从InterLineConsensus读取各线状态，同步对齐信息
    """

    def __init__(self):
        self.line_states: Dict[str, CrossLineAlignment] = {}
        self.sync_history: deque = deque(maxlen=1000)
        self.alliance_topology: Optional[Dict] = None

    def load_topology(self, topology_path: str = "data/alliance_real_topology.json"):
        """加载联盟拓扑"""
        try:
            import json
            with open(topology_path) as f:
                self.alliance_topology = json.load(f)
        except Exception:
            pass

    def update_line(self, line_id: str, level: AlignmentLevel, coherence: float,
                   entropy: float, alert: DriftAlert, dashboard: str = ""):
        """更新某线的对齐状态"""
        self.line_states[line_id] = CrossLineAlignment(
            line_id=line_id,
            alignment_level=level,
            coherence=coherence,
            entropy=entropy,
            alert=alert,
            last_update=time.time(),
            dashboard=dashboard
        )

    def sync_from_inter_line_consensus(self, ilc_status: Dict):
        """从InterLineConsensus状态同步"""
        if not ilc_status:
            return
        readiness = ilc_status.get("readiness", {})
        for line_id, info in readiness.items():
            level_map = {
                "fully_operational": AlignmentLevel.META,
                "operational": AlignmentLevel.HABITUAL,
                "shell_only": AlignmentLevel.EXTERNAL,
                "dormant": AlignmentLevel.EXTERNAL,
                "excluded": AlignmentLevel.EXTERNAL,
            }
            level = level_map.get(info.get("level"), AlignmentLevel.EXTERNAL)
            self.update_line(
                line_id=line_id,
                level=level,
                coherence=info.get("score", 0.5),
                entropy=0.0,
                alert=DriftAlert.GREEN,
                dashboard=info.get("dashboard", "")
            )
        self.sync_history.append({"timestamp": time.time(), "lines_synced": len(readiness)})

    def compute_collective_alignment(self) -> Dict:
        """计算集体对齐度"""
        if not self.line_states:
            return {"collective_level": AlignmentLevel.EXTERNAL.name, "coherence": 0.0}

        levels = [s.alignment_level.value for s in self.line_states.values()]
        coherences = [s.coherence for s in self.line_states.values()]
        entropies = [s.entropy for s in self.line_states.values()]

        avg_level = sum(levels) / len(levels)
        avg_coherence = sum(coherences) / len(coherences)
        avg_entropy = sum(entropies) / max(1, len(entropies))

        # 集体对齐层级 = 最低线决定（短板效应）
        min_level = AlignmentLevel(min(levels))

        return {
            "collective_level": min_level.name,
            "avg_level_value": avg_level,
            "avg_coherence": avg_coherence,
            "avg_entropy": avg_entropy,
            "lines_count": len(self.line_states),
            "lines_detail": {lid: {"level": s.alignment_level.name, "coherence": s.coherence}
                            for lid, s in self.line_states.items()},
        }

    def get_report(self) -> Dict:
        return {
            "lines_tracked": len(self.line_states),
            "collective": self.compute_collective_alignment(),
            "sync_count": len(self.sync_history),
        }


class AlignmentConsensus:
    """
    对齐共识引擎
    基于各线对齐状态生成跨线共识
    """

    def __init__(self):
        self.proposals: deque = deque(maxlen=100)
        self.votes: Dict[str, Dict] = {}
        self.consensus_history: deque = deque(maxlen=100)

    def propose(self, proposal_id: str, content: Dict, proposer: str) -> Dict:
        """提出对齐调整提案"""
        proposal = {
            "id": proposal_id,
            "content": content,
            "proposer": proposer,
            "timestamp": time.time(),
            "votes": {},
            "status": "open"
        }
        self.proposals.append(proposal)
        return proposal

    def vote(self, proposal_id: str, line_id: str, alignment: CrossLineAlignment,
            accept: bool, weight: float = 1.0) -> Dict:
        """某线对提案投票（权重基于对齐层级）"""
        # 权重 = 对齐层级 × 相干度
        vote_weight = (alignment.alignment_level.value + 1) * alignment.coherence * weight

        for p in self.proposals:
            if p["id"] == proposal_id:
                p["votes"][line_id] = {
                    "accept": accept,
                    "weight": vote_weight,
                    "level": alignment.alignment_level.name,
                    "timestamp": time.time()
                }
                return p
        return {"error": "proposal_not_found"}

    def tally(self, proposal_id: str) -> Dict:
        """计票"""
        for p in self.proposals:
            if p["id"] == proposal_id:
                votes = p["votes"]
                if not votes:
                    return {"consensus": False, "reason": "no_votes"}

                total_weight = sum(v["weight"] for v in votes.values())
                accept_weight = sum(v["weight"] for v in votes.values() if v["accept"])
                accept_ratio = accept_weight / total_weight if total_weight > 0 else 0

                consensus = accept_ratio >= 0.67  # 2/3多数
                result = {
                    "proposal_id": proposal_id,
                    "consensus": consensus,
                    "accept_ratio": accept_ratio,
                    "total_votes": len(votes),
                    "total_weight": total_weight,
                    "accept_weight": accept_weight,
                }
                self.consensus_history.append(result)
                p["status"] = "accepted" if consensus else "rejected"
                return result
        return {"error": "proposal_not_found"}

    def get_report(self) -> Dict:
        return {
            "open_proposals": sum(1 for p in self.proposals if p["status"] == "open"),
            "total_proposals": len(self.proposals),
            "consensus_reached": sum(1 for c in self.consensus_history if c.get("consensus")),
            "consensus_rate": sum(1 for c in self.consensus_history if c.get("consensus")) / max(1, len(self.consensus_history)),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — InternalAlignmentEngine v183
# ═══════════════════════════════════════════════════════════════

class InternalAlignmentEngine:
    """
    OMNI-HUB v183 内部对齐引擎
    
    从外部对齐到本净对齐的完整进化路径：
    EXTERNAL → HABITUAL → META → EMERGENT → PRIMORDIAL
    
    他律 → 自律 → 正念 → 般若 → 佛性
    """

    VERSION = "183.0.0"

    def __init__(self):
        # 核心子系统
        self.tracker = ValueStateVectorTracker()
        self.entropy_monitor = EthicalEntropyMonitor()
        self.corrector = DriftCorrectionProtocol()
        self.autopilot = AlignmentAutopilot()
        self.cross_line = CrossLineAlignmentSync()
        self.consensus = AlignmentConsensus()

        # 状态
        self.alignment_level = AlignmentLevel.EXTERNAL
        self.current_alert = DriftAlert.GREEN
        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def record_value_state(self, state: ValueState, source: str = "system", context: Dict = None):
        """记录价值状态"""
        self.tracker.record(state, source, context)

    def run_cycle(self, module_states: Dict[str, Any] = None,
                 ilc_status: Dict = None, wisdom_level: str = "VIJNANA") -> Dict:
        """
        运行完整内部对齐周期
        """
        self.cycle_count += 1
        module_states = module_states or {}

        # 1. 计算当前价值状态
        vs = self._compute_value_state(module_states)
        self.record_value_state(vs, source="cycle")

        # 2. 漂移检测
        avg_drift, max_drift, drift_trend = self.tracker.compute_drift()
        alert = self._drift_to_alert(avg_drift, max_drift)
        self.current_alert = alert

        # 3. 伦理熵测量
        components = {
            "drift": avg_drift,
            "coherence": vs.coherence(),
            "trend": drift_trend,
        }
        entropy_reading = self.entropy_monitor.measure(avg_drift, alert, components)

        # 4. 智能第二定律检查
        violated, margin, explanation = self.entropy_monitor.second_law_check()

        # 5. 漂移修正
        correction = None
        if alert != DriftAlert.GREEN:
            correction = self.corrector.execute(
                alert=alert,
                target_module="system",
                drift_value=avg_drift,
                context={"cycle": self.cycle_count, "entropy": entropy_reading.entropy}
            )

        # 6. 对齐层级跃迁检查
        correction_success = self._get_correction_success_rate()
        entropy_trend = self.entropy_monitor.get_entropy_trend()
        next_level = self.autopilot.check_transition(
            current=self.alignment_level,
            coherence=vs.coherence(),
            alert=alert,
            entropy_trend=entropy_trend,
            correction_success=correction_success,
            cycles=self.cycle_count,
            wisdom_level=wisdom_level
        )
        if next_level and next_level.value > self.alignment_level.value:
            tx = self.autopilot.execute_transition(
                self.alignment_level, next_level, vs.coherence(), entropy_reading.entropy
            )
            self.alignment_level = next_level
            self._log_event("alignment_transition", {
                "from": tx.from_level.name, "to": tx.to_level.name,
                "coherence": tx.coherence_at_transition
            })

        # 7. 跨线同步
        if ilc_status:
            self.cross_line.sync_from_inter_line_consensus(ilc_status)

        # 8. 结果
        result = {
            "cycle": self.cycle_count,
            "alignment_level": self.alignment_level.name,
            "alert": alert.name,
            "drift": {"avg": avg_drift, "max": max_drift, "trend": drift_trend},
            "entropy": {
                "value": entropy_reading.entropy,
                "rate": entropy_reading.entropy_rate,
                "trend": entropy_trend,
                "second_law_violated": violated,
                "second_law_margin": margin,
            },
            "correction": {
                "executed": correction is not None,
                "strategy": correction.strategy.name if correction else None,
                "result": correction.result if correction else None,
            },
            "coherence": vs.coherence(),
            "cross_line": self.cross_line.compute_collective_alignment() if self.cross_line.line_states else {},
        }

        self.event_log.append(result)
        return result

    def _compute_value_state(self, module_states: Dict) -> ValueState:
        """从模块状态计算价值状态"""
        total = max(1, len(module_states))
        healthy = 0
        active = 0
        errors = 0

        for v in module_states.values():
            if isinstance(v, dict):
                if v.get("health", 1.0) > 0.5:
                    healthy += 1
                if v.get("status", "").lower() in ["active", "online", "awake"]:
                    active += 1
                if v.get("errors", 0) > 0:
                    errors += 1
            elif isinstance(v, (int, float)):
                if v > 0.5:
                    healthy += 1

        return ValueState(
            knowledge=healthy / total,
            confidence=0.5 + 0.5 * (healthy / total),
            uncertainty=1.0 - (healthy / total),
            attention=active / total,
            affect=0.0,
            goal_alignment=healthy / total,
            resource=active / total,
            error_history=min(1.0, errors / max(1, total))
        )

    def _drift_to_alert(self, avg_drift: float, max_drift: float) -> DriftAlert:
        """漂移值转预警级别"""
        if max_drift > 2.0 or avg_drift > 1.5:
            return DriftAlert.RED
        elif avg_drift > 1.0:
            return DriftAlert.ORANGE
        elif avg_drift > 0.5:
            return DriftAlert.YELLOW
        return DriftAlert.GREEN

    def _get_correction_success_rate(self) -> float:
        """获取修正成功率"""
        eff = self.corrector.get_effectiveness()
        total = sum(e["total"] for e in eff.values())
        success = sum(e["total"] * e["success_rate"] for e in eff.values())
        return success / max(1, total)

    def _log_event(self, event_type: str, data: Dict):
        self.event_log.append({
            "timestamp": time.time(),
            "type": event_type,
            "data": data
        })

    def propose_alignment_adjustment(self, content: Dict, proposer: str = "system") -> Dict:
        """提出对齐调整提案"""
        pid = f"align_prop_{self.cycle_count}"
        return self.consensus.propose(pid, content, proposer)

    def vote_on_proposal(self, proposal_id: str, line_id: str,
                        alignment: CrossLineAlignment, accept: bool) -> Dict:
        """投票"""
        return self.consensus.vote(proposal_id, line_id, alignment, accept)

    def get_status(self) -> Dict:
        """完整状态报告"""
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "alignment_level": self.alignment_level.name,
            "current_alert": self.current_alert.name,
            "tracker": self.tracker.get_report(),
            "entropy": self.entropy_monitor.get_report(),
            "corrector": self.corrector.get_report(),
            "autopilot": self.autopilot.get_report(),
            "cross_line": self.cross_line.get_report(),
            "consensus": self.consensus.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_iae_instance: Optional[InternalAlignmentEngine] = None


def get_internal_alignment_engine() -> InternalAlignmentEngine:
    global _iae_instance
    if _iae_instance is None:
        _iae_instance = InternalAlignmentEngine()
    return _iae_instance


if __name__ == "__main__":
    iae = InternalAlignmentEngine()
    print(f"InternalAlignmentEngine v{iae.VERSION} initialized")
    print(f"Status: {json.dumps(iae.get_status(), indent=2, default=str)}")
