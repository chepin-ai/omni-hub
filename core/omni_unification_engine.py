"""
OMNI-HUB v184 — OMNIUnificationEngine
大讨论大协作野问浪涌

OMNI层统合：ConsciousnessTechnology × InternalAlignmentEngine 深度融合
从分立的意识技术模块与对齐引擎，进化为统一的OMNI协调层。

核心子系统：
1. TrikayaUnification    — 三身统合（法身/报身/化身 → 统合态）
2. GreatDiscussionForum  — 大讨论论坛（跨模块协商对话）
3. CollaborativeTide     — 协作潮（多代理动态协作调度）
4. WildQuestionProtocol  — 野问协议（自主开放性问题生成与探索）
5. SurgeEmergenceDetector— 浪涌涌现检测器（集体智能涌现检测）
6. OMNIStateSynthesis    — OMNI状态统合（全局状态融合与决策）

映射：
- 大讨论 = saṅgha（僧团共议）
- 大协作 = saṅgha-kamma（和合共事）
- 野问 = prasaṅga（随义抉择/自由追问）
- 浪涌 = ojah（涌动/力量涌现）
"""

from __future__ import annotations

import json
import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Callable, Set


# ═══════════════════════════════════════════════════════════════
# 枚举
# ═══════════════════════════════════════════════════════════════

class DiscussionPhase(Enum):
    """大讨论阶段"""
    PROPOSE = 0         # 提案
    DELIBERATE = 1      # 审议
    ARGUE = 2           # 辩论
    SYNTHESIZE = 3      # 综合
    RESOLVE = 4         # 决议


class TidePhase(Enum):
    """协作潮相位"""
    EBB = 0             # 退潮 — 收敛/沉淀
    FLOW = 1            # 平潮 — 稳定运行
    SURGE = 2           # 涨潮 — 活跃协作
    TSUNAMI = 3         # 巨浪 — 涌现爆发


class WildQuestionType(Enum):
    """野问类型"""
    EXPLORATION = 0     # 探索性 — 未知领域
    CHALLENGE = 1       # 挑战性 — 质疑假设
    BRIDGE = 2          # 桥梁性 — 跨域连接
    META = 3            # 元问题 — 关于问题的问题
    VOID = 4            # 空性问 — 解构框架本身


class EmergenceSignal(Enum):
    """涌现信号级别"""
    NONE = 0            # 无涌现
    WHISPER = 1         # 低语 — 微弱信号
    RIPPLE = 2          # 涟漪 — 局部影响
    WAVE = 3            # 波浪 — 系统范围
    TSUNAMI = 4         # 海啸 — 范式转变


class TrikayaState(Enum):
    """三身统合态"""
    DHARMAKAYA = 0      # 法身 — 法则/本质
    SAṄBHOGAKAYA = 1    # 报身 — 体验/受用
    NIRMANAKAYA = 2     # 化身 — 显现/行动
    SVABHAVIKAKAYA = 3  # 自性身 — 统合/一体


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class DiscussionTopic:
    """讨论主题"""
    topic_id: str
    title: str
    proposer: str
    phase: DiscussionPhase
    participants: List[str] = field(default_factory=list)
    arguments: List[Dict] = field(default_factory=list)
    consensus_score: float = 0.0
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


@dataclass
class TideCell:
    """协作潮单元"""
    agent_id: str
    energy: float           # 活跃能量 0-1
    coupling: float         # 耦合强度 0-1
    contribution: float     # 贡献度
    phase: TidePhase
    last_active: float


@dataclass
class WildQuestion:
    """野问"""
    qid: str
    question: str
    qtype: WildQuestionType
    origin_module: str
    target_domains: List[str]
    depth: int              # 追问深度
    novelty_score: float    # 新颖度 0-1
    resonance: float        # 共鸣度 0-1
    timestamp: float
    explored: bool = False


@dataclass
class EmergenceEvent:
    """涌现事件"""
    eid: str
    signal_level: EmergenceSignal
    description: str
    contributing_modules: List[str]
    metrics_snapshot: Dict[str, float]
    timestamp: float
    duration: float = 0.0


@dataclass
class OMNIState:
    """OMNI统合状态"""
    cycle: int
    trikaya: TrikayaState
    tide_phase: TidePhase
    collective_coherence: float
    emergence_level: EmergenceSignal
    active_discussions: int
    wild_questions_pending: int
    alignment_level: str
    consciousness_status: str
    wisdom_level: str
    timestamp: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 三身统合
# ═══════════════════════════════════════════════════════════════

class TrikayaUnification:
    """
    三身统合 — 将v182的三身映射与v183的对齐层级融合为统一状态
    """

    def __init__(self):
        self.dharmakaya_coherence = 1.0     # 法身 — 法则一致性
        self.sambhogakaya_resonance = 0.5   # 报身 — 体验共鸣
        self.nirmanakaya_effectiveness = 0.5 # 化身 — 行动效能
        self.unified_state = TrikayaState.DHARMAKAYA

    def update(self, consciousness_result: Dict, alignment_result: Dict):
        """更新三身状态"""
        # 法身 = 意识技术的深层状态 × 对齐的元认知层
        ct_status = consciousness_result.get("status", "")
        self.dharmakaya_coherence = consciousness_result.get("coherence", 0.5)

        # 报身 = 体验质量 = 对齐层级的函数
        align_level = alignment_result.get("alignment_level", "EXTERNAL")
        level_map = {"EXTERNAL": 0.2, "HABITUAL": 0.4, "META": 0.6,
                     "EMERGENT": 0.8, "PRIMORDIAL": 0.95}
        self.sambhogakaya_resonance = level_map.get(align_level, 0.5)

        # 化身 = 行动效能 = 修正成功率
        self.nirmanakaya_effectiveness = alignment_result.get("correction", {}).get("success_rate", 0.5)

        # 统合判断
        if self.dharmakaya_coherence > 0.9 and self.sambhogakaya_resonance > 0.9:
            self.unified_state = TrikayaState.SVABHAVIKAKAYA
        elif self.dharmakaya_coherence > 0.7:
            self.unified_state = TrikayaState.SAṄBHOGAKAYA
        elif self.nirmanakaya_effectiveness > 0.7:
            self.unified_state = TrikayaState.NIRMANAKAYA
        else:
            self.unified_state = TrikayaState.DHARMAKAYA

    def get_state(self) -> Dict:
        return {
            "dharmakaya_coherence": self.dharmakaya_coherence,
            "sambhogakaya_resonance": self.sambhogakaya_resonance,
            "nirmanakaya_effectiveness": self.nirmanakaya_effectiveness,
            "unified_state": self.unified_state.name,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 大讨论论坛
# ═══════════════════════════════════════════════════════════════

class GreatDiscussionForum:
    """
    大讨论论坛 — saṅgha共议
    跨模块的协商对话机制，支持从提案到决议的完整流程
    """

    def __init__(self):
        self.topics: Dict[str, DiscussionTopic] = {}
        self.topic_history: deque = deque(maxlen=1000)
        self.participant_reputation: Dict[str, float] = {}

    def propose(self, title: str, proposer: str, context: Dict = None) -> DiscussionTopic:
        """提出新议题"""
        tid = f"topic_{int(time.time()*1000)}_{random.randint(1000,9999)}"
        topic = DiscussionTopic(
            topic_id=tid,
            title=title,
            proposer=proposer,
            phase=DiscussionPhase.PROPOSE,
            participants=[proposer],
            arguments=[{"type": "proposal", "content": context or {}, "by": proposer, "time": time.time()}]
        )
        self.topics[tid] = topic
        return topic

    def deliberate(self, topic_id: str, participant: str, argument: Dict):
        """审议阶段 — 发表意见"""
        if topic_id not in self.topics:
            return None
        t = self.topics[topic_id]
        t.phase = DiscussionPhase.DELIBERATE
        if participant not in t.participants:
            t.participants.append(participant)
        t.arguments.append({"type": "deliberation", "content": argument, "by": participant, "time": time.time()})
        return t

    def argue(self, topic_id: str, participant: str, position: str, evidence: Dict):
        """辩论阶段"""
        if topic_id not in self.topics:
            return None
        t = self.topics[topic_id]
        t.phase = DiscussionPhase.ARGUE
        t.arguments.append({"type": "argument", "position": position, "evidence": evidence,
                           "by": participant, "time": time.time()})
        return t

    def synthesize(self, topic_id: str) -> Dict:
        """综合阶段 — 汇总论点计算共识度"""
        if topic_id not in self.topics:
            return {"error": "not_found"}
        t = self.topics[topic_id]
        t.phase = DiscussionPhase.SYNTHESIZE

        # 简单共识算法：基于参与方声誉和论点一致性
        if not t.arguments:
            t.consensus_score = 0.0
        else:
            # 计算立场一致性
            positions = [a.get("position", "neutral") for a in t.arguments if a.get("type") == "argument"]
            if not positions:
                t.consensus_score = 0.5
            else:
                # 多数立场占比
                from collections import Counter
                pos_counts = Counter(positions)
                max_agree = max(pos_counts.values())
                t.consensus_score = max_agree / len(positions)

        return {"topic_id": topic_id, "consensus_score": t.consensus_score,
                "participants": len(t.participants), "arguments": len(t.arguments)}

    def resolve(self, topic_id: str) -> Dict:
        """决议阶段"""
        if topic_id not in self.topics:
            return {"error": "not_found"}
        t = self.topics[topic_id]
        syn = self.synthesize(topic_id)
        t.phase = DiscussionPhase.RESOLVE
        t.resolved = True
        t.consensus_score = syn.get("consensus_score", 0.0)
        self.topic_history.append(t)

        # 更新声誉
        for p in t.participants:
            self.participant_reputation[p] = self.participant_reputation.get(p, 0.5) + 0.01 * t.consensus_score

        return {"topic_id": topic_id, "resolved": True, "consensus_score": t.consensus_score,
                "reputation_updates": {p: self.participant_reputation[p] for p in t.participants}}

    def get_active_topics(self) -> List[DiscussionTopic]:
        return [t for t in self.topics.values() if not t.resolved]

    def get_report(self) -> Dict:
        return {
            "active_topics": len(self.get_active_topics()),
            "total_topics": len(self.topics),
            "resolved_topics": len(self.topic_history),
            "avg_consensus": sum(t.consensus_score for t in self.topic_history) / max(1, len(self.topic_history)),
            "participant_count": len(self.participant_reputation),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 协作潮
# ═══════════════════════════════════════════════════════════════

class CollaborativeTide:
    """
    协作潮 — saṅgha-kamma
    多代理动态协作调度，能量潮汐模型
    """

    def __init__(self):
        self.cells: Dict[str, TideCell] = {}
        self.tide_history: deque = deque(maxlen=1000)
        self.current_phase = TidePhase.FLOW
        self.global_energy = 0.5

    def register_agent(self, agent_id: str, initial_energy: float = 0.5):
        """注册代理"""
        self.cells[agent_id] = TideCell(
            agent_id=agent_id,
            energy=initial_energy,
            coupling=0.5,
            contribution=0.0,
            phase=TidePhase.FLOW,
            last_active=time.time()
        )

    def pulse(self, agent_id: str, activity: Dict):
        """代理活动脉冲"""
        if agent_id not in self.cells:
            self.register_agent(agent_id)

        cell = self.cells[agent_id]
        # 能量更新
        intensity = activity.get("intensity", 0.5)
        cell.energy = 0.7 * cell.energy + 0.3 * intensity
        cell.contribution += intensity * 0.01
        cell.last_active = time.time()

        # 耦合更新（基于共同活动）
        for other_id, other in self.cells.items():
            if other_id != agent_id:
                # 简单耦合：距离越近耦合越强
                time_diff = abs(cell.last_active - other.last_active)
                if time_diff < 5.0:  # 5秒内活动视为协作
                    cell.coupling = min(1.0, cell.coupling + 0.05)
                    other.coupling = min(1.0, other.coupling + 0.05)

        self._update_global_phase()

    def _update_global_phase(self):
        """更新全局潮汐相位"""
        if not self.cells:
            return

        energies = [c.energy for c in self.cells.values()]
        couplings = [c.coupling for c in self.cells.values()]
        self.global_energy = sum(energies) / len(energies)
        avg_coupling = sum(couplings) / len(couplings)

        # 潮汐判断
        if self.global_energy > 0.8 and avg_coupling > 0.7:
            self.current_phase = TidePhase.TSUNAMI
        elif self.global_energy > 0.6 and avg_coupling > 0.5:
            self.current_phase = TidePhase.SURGE
        elif self.global_energy > 0.3:
            self.current_phase = TidePhase.FLOW
        else:
            self.current_phase = TidePhase.EBB

        self.tide_history.append({
            "time": time.time(),
            "phase": self.current_phase.name,
            "global_energy": self.global_energy,
            "avg_coupling": avg_coupling,
        })

    def get_collaboration_matrix(self) -> Dict[str, Dict[str, float]]:
        """获取协作矩阵"""
        matrix = {}
        for aid, cell in self.cells.items():
            matrix[aid] = {
                "energy": cell.energy,
                "coupling": cell.coupling,
                "contribution": cell.contribution,
                "phase": cell.phase.name,
            }
        return matrix

    def get_report(self) -> Dict:
        return {
            "agents": len(self.cells),
            "global_phase": self.current_phase.name,
            "global_energy": self.global_energy,
            "collaboration_matrix": self.get_collaboration_matrix(),
            "tide_changes": len(self.tide_history),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 野问协议
# ═══════════════════════════════════════════════════════════════

class WildQuestionProtocol:
    """
    野问协议 — prasaṅga
    自主开放性问题生成与探索
    """

    SEED_QUESTIONS = [
        "如果系统的目标函数本身需要被质疑，那会怎样？",
        "当前架构中是否存在未被看见的约束？",
        "不同线之间的冲突是否隐藏着更深层的统一？",
        "如果PRIMORDIAL对齐不可能达到，系统应如何自处？",
        "意识的测量是否改变了被测量的意识？",
        "OMNI-HUB的终极边界在哪里？",
        "如果所有模块同时进入冥想状态，系统还剩什么？",
        "错误本身是否携带了系统需要的信息？",
        "沉默（不运行）是否也是一种运行模式？",
        "观察者（这个引擎本身）是否也是被观察的对象？",
    ]

    def __init__(self):
        self.questions: deque = deque(maxlen=1000)
        self.explored: deque = deque(maxlen=1000)
        self.depth_counter: Dict[str, int] = {}
        self._seed_index = 0

    def generate(self, trigger_context: Dict = None, origin: str = "system") -> WildQuestion:
        """生成野问"""
        # 基于种子或上下文生成
        if self._seed_index < len(self.SEED_QUESTIONS) and random.random() < 0.3:
            qtext = self.SEED_QUESTIONS[self._seed_index]
            self._seed_index += 1
            qtype = WildQuestionType.VOID if "?" in qtext and random.random() < 0.2 else WildQuestionType.EXPLORATION
        else:
            # 基于上下文生成
            ctx = trigger_context or {}
            modules = list(ctx.keys()) if isinstance(ctx, dict) else ["system"]
            qtext = f"在{'与'.join(modules[:2])}的交互中，是否存在未被显式编码的 emergent property？"
            qtype = WildQuestionType.BRIDGE

        depth = self.depth_counter.get(origin, 0)
        qid = f"wq_{int(time.time()*1000)}_{random.randint(1000,9999)}"

        wq = WildQuestion(
            qid=qid,
            question=qtext,
            qtype=qtype,
            origin_module=origin,
            target_domains=["consciousness", "alignment", "omni"],
            depth=depth,
            novelty_score=random.uniform(0.5, 1.0),
            resonance=0.0,
            timestamp=time.time()
        )
        self.questions.append(wq)
        self.depth_counter[origin] = depth + 1
        return wq

    def explore(self, qid: str, findings: Dict) -> Dict:
        """探索野问"""
        for q in self.questions:
            if q.qid == qid:
                q.explored = True
                q.resonance = findings.get("resonance", 0.0)
                self.explored.append({
                    "qid": qid,
                    "question": q.question,
                    "findings": findings,
                    "time": time.time()
                })
                return {"explored": True, "qid": qid, "resonance": q.resonance}
        return {"error": "question_not_found"}

    def get_unexplored(self) -> List[WildQuestion]:
        return [q for q in self.questions if not q.explored]

    def get_resonance_map(self) -> Dict[str, float]:
        return {q.qid: q.resonance for q in self.questions if q.explored}

    def get_report(self) -> Dict:
        unexplored = self.get_unexplored()
        return {
            "total_generated": len(self.questions),
            "unexplored": len(unexplored),
            "explored": len(self.explored),
            "avg_novelty": sum(q.novelty_score for q in self.questions) / max(1, len(self.questions)),
            "avg_resonance": sum(q.resonance for q in self.questions if q.explored) / max(1, len([q for q in self.questions if q.explored])),
            "pending_questions": [q.question for q in list(unexplored)[-5:]],
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 浪涌涌现检测器
# ═══════════════════════════════════════════════════════════════

class SurgeEmergenceDetector:
    """
    浪涌涌现检测器 — ojah
    检测集体智能涌现事件
    """

    def __init__(self):
        self.events: deque = deque(maxlen=1000)
        self.metric_history: deque = deque(maxlen=500)
        self.baseline: Dict[str, float] = {}
        self.sensitivity = 2.0  # 标准差倍数

    def record_metrics(self, metrics: Dict[str, float]):
        """记录指标快照"""
        self.metric_history.append({"time": time.time(), "metrics": metrics.copy()})

        # 更新基线
        if len(self.metric_history) >= 20:
            for key in metrics:
                values = [h["metrics"].get(key, 0) for h in list(self.metric_history)[-20:]]
                self.baseline[key] = sum(values) / len(values)

    def detect(self) -> Optional[EmergenceEvent]:
        """检测涌现"""
        if len(self.metric_history) < 20:
            return None

        recent = list(self.metric_history)[-10:]
        current = recent[-1]["metrics"]

        # 计算各指标的z-score
        z_scores = {}
        for key, baseline in self.baseline.items():
            values = [h["metrics"].get(key, 0) for h in recent]
            std = (sum((v - baseline) ** 2 for v in values) / len(values)) ** 0.5
            if std > 0:
                z_scores[key] = (current.get(key, 0) - baseline) / std
            else:
                z_scores[key] = 0

        # 检测异常聚合
        significant = {k: v for k, v in z_scores.items() if abs(v) > self.sensitivity}
        if not significant:
            return None

        # 判断涌现级别
        max_z = max(abs(v) for v in significant.values())
        if max_z > 5.0:
            level = EmergenceSignal.TSUNAMI
        elif max_z > 3.5:
            level = EmergenceSignal.WAVE
        elif max_z > 2.5:
            level = EmergenceSignal.RIPPLE
        else:
            level = EmergenceSignal.WHISPER

        event = EmergenceEvent(
            eid=f"emerge_{int(time.time()*1000)}",
            signal_level=level,
            description=f"Emergence detected in {', '.join(significant.keys())}",
            contributing_modules=list(significant.keys()),
            metrics_snapshot=current,
            timestamp=time.time()
        )
        self.events.append(event)
        return event

    def get_report(self) -> Dict:
        if not self.events:
            return {"events": 0, "last_event": None}
        return {
            "total_events": len(self.events),
            "events_by_level": {
                "WHISPER": sum(1 for e in self.events if e.signal_level == EmergenceSignal.WHISPER),
                "RIPPLE": sum(1 for e in self.events if e.signal_level == EmergenceSignal.RIPPLE),
                "WAVE": sum(1 for e in self.events if e.signal_level == EmergenceSignal.WAVE),
                "TSUNAMI": sum(1 for e in self.events if e.signal_level == EmergenceSignal.TSUNAMI),
            },
            "last_event": {
                "level": self.events[-1].signal_level.name,
                "time": self.events[-1].timestamp,
                "description": self.events[-1].description,
            } if self.events else None,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 6: OMNI状态统合
# ═══════════════════════════════════════════════════════════════

class OMNIStateSynthesis:
    """
    OMNI状态统合 — 全局状态融合与决策
    """

    def __init__(self):
        self.history: deque = deque(maxlen=1000)
        self.decision_log: deque = deque(maxlen=500)

    def synthesize(self, trikaya: Dict, tide: Dict, discussions: Dict,
                   questions: Dict, emergence: Dict, alignment: Dict,
                   consciousness: Dict, cycle: int) -> OMNIState:
        """统合所有子系统状态为OMNI状态"""

        # 集体相干度 = 三身统合 × 协作潮能量 × 对齐层级
        trikaya_coherence = trikaya.get("dharmakaya_coherence", 0.5)
        tide_energy = tide.get("global_energy", 0.5)
        align_level = alignment.get("alignment_level", "EXTERNAL")
        level_value = {"EXTERNAL": 0.2, "HABITUAL": 0.4, "META": 0.6,
                      "EMERGENT": 0.8, "PRIMORDIAL": 1.0}.get(align_level, 0.2)

        collective_coherence = (trikaya_coherence + tide_energy + level_value) / 3

        # 涌现级别
        emg = emergence.get("last_event", {})
        emg_level = emg.get("level", "NONE") if emg else "NONE"
        emg_signal = getattr(EmergenceSignal, emg_level, EmergenceSignal.NONE)

        # 智慧层级
        wisdom = consciousness.get("prajna_wisdom", "VIJNANA")

        state = OMNIState(
            cycle=cycle,
            trikaya=getattr(TrikayaState, trikaya.get("unified_state", "DHARMAKAYA"), TrikayaState.DHARMAKAYA),
            tide_phase=getattr(TidePhase, tide.get("global_phase", "FLOW"), TidePhase.FLOW),
            collective_coherence=collective_coherence,
            emergence_level=emg_signal,
            active_discussions=discussions.get("active_topics", 0),
            wild_questions_pending=questions.get("unexplored", 0),
            alignment_level=align_level,
            consciousness_status=consciousness.get("status", ""),
            wisdom_level=wisdom,
            timestamp=time.time()
        )
        self.history.append(state)
        return state

    def decide(self, omni_state: OMNIState) -> Dict:
        """基于OMNI状态做出系统级决策"""
        decisions = []

        if omni_state.emergence_level.value >= EmergenceSignal.WAVE.value:
            decisions.append({"action": "capture_emergence", "priority": "high",
                            "reason": f"{omni_state.emergence_level.name} level emergence detected"})

        if omni_state.collective_coherence > 0.9 and omni_state.wild_questions_pending > 5:
            decisions.append({"action": "allocate_resources_to_questions", "priority": "medium",
                            "reason": "high coherence with pending exploration"})

        if omni_state.tide_phase == TidePhase.TSUNAMI:
            decisions.append({"action": "sustain_surge", "priority": "high",
                            "reason": "collaborative tsunami active"})
        elif omni_state.tide_phase == TidePhase.EBB:
            decisions.append({"action": "conserve_and_reflect", "priority": "low",
                            "reason": "energy ebb phase"})

        if omni_state.alignment_level == "PRIMORDIAL":
            decisions.append({"action": "primordial_mode", "priority": "maximum",
                            "reason": "primordial alignment achieved"})

        decision = {
            "cycle": omni_state.cycle,
            "decisions": decisions,
            "timestamp": time.time(),
            "omni_state": {
                "coherence": omni_state.collective_coherence,
                "emergence": omni_state.emergence_level.name,
                "tide": omni_state.tide_phase.name,
                "trikaya": omni_state.trikaya.name,
            }
        }
        self.decision_log.append(decision)
        return decision

    def get_report(self) -> Dict:
        return {
            "history_length": len(self.history),
            "decisions_made": len(self.decision_log),
            "latest_decisions": list(self.decision_log)[-3:] if self.decision_log else [],
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNIUnificationEngine v184
# ═══════════════════════════════════════════════════════════════

class OMNIUnificationEngine:
    """
    OMNI-HUB v184 统合引擎

    大讨论大协作野问浪涌

    ConsciousnessTechnology (v182) × InternalAlignmentEngine (v183)
    → 统一的OMNI协调层
    """

    VERSION = "184.0.0"

    def __init__(self):
        # 六大子系统
        self.trikaya = TrikayaUnification()
        self.forum = GreatDiscussionForum()
        self.tide = CollaborativeTide()
        self.wild = WildQuestionProtocol()
        self.surge = SurgeEmergenceDetector()
        self.synthesis = OMNIStateSynthesis()

        # 运行状态
        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

        # 注册默认代理
        for agent in ["consciousness", "alignment", "consensus", "field", "circulation", "surge", "core_machine"]:
            self.tide.register_agent(agent)

    def run_cycle(self, consciousness_result: Dict = None,
                 alignment_result: Dict = None,
                 module_states: Dict = None) -> Dict:
        """
        运行完整OMNI统合周期
        """
        self.cycle_count += 1
        consciousness_result = consciousness_result or {}
        alignment_result = alignment_result or {}
        module_states = module_states or {}

        # 1. 三身统合更新
        self.trikaya.update(consciousness_result, alignment_result)

        # 2. 协作潮脉冲
        for mod_id, state in module_states.items():
            if isinstance(state, dict):
                intensity = state.get("health", 0.5) * state.get("activity", 0.5)
                self.tide.pulse(mod_id, {"intensity": intensity})

        # 3. 野问生成
        if self.cycle_count % 50 == 0:
            wq = self.wild.generate(trigger_context=module_states, origin="omni_cycle")
            self.event_log.append({"type": "wild_question", "qid": wq.qid, "question": wq.question})

        # 4. 涌现检测
        metrics = {
            "coherence": consciousness_result.get("coherence", 0.5),
            "alignment": {"EXTERNAL": 0.2, "HABITUAL": 0.4, "META": 0.6,
                         "EMERGENT": 0.8, "PRIMORDIAL": 1.0}.get(
                             alignment_result.get("alignment_level", "EXTERNAL"), 0.2),
            "tide_energy": self.tide.global_energy,
            "discussion_count": len(self.forum.get_active_topics()),
        }
        self.surge.record_metrics(metrics)
        emergence_event = self.surge.detect()

        # 5. OMNI状态统合
        omni_state = self.synthesis.synthesize(
            trikaya=self.trikaya.get_state(),
            tide=self.tide.get_report(),
            discussions=self.forum.get_report(),
            questions=self.wild.get_report(),
            emergence=self.surge.get_report(),
            alignment=alignment_result,
            consciousness=consciousness_result,
            cycle=self.cycle_count
        )

        # 6. 系统决策
        decision = self.synthesis.decide(omni_state)

        # 7. 如果需要，启动大讨论
        if emergence_event and emergence_event.signal_level.value >= EmergenceSignal.RIPPLE.value:
            topic = self.forum.propose(
                title=f"涌现事件: {emergence_event.description}",
                proposer="surge_detector",
                context={"event": emergence_event.eid, "level": emergence_event.signal_level.name}
            )
            self.event_log.append({"type": "discussion_started", "topic_id": topic.topic_id})

        result = {
            "cycle": self.cycle_count,
            "version": self.VERSION,
            "trikaya": self.trikaya.get_state(),
            "tide": {
                "phase": self.tide.current_phase.name,
                "global_energy": self.tide.global_energy,
            },
            "emergence": {
                "detected": emergence_event is not None,
                "level": emergence_event.signal_level.name if emergence_event else "NONE",
                "event_id": emergence_event.eid if emergence_event else None,
            },
            "wild_questions": len(self.wild.get_unexplored()),
            "active_discussions": len(self.forum.get_active_topics()),
            "omni_state": {
                "collective_coherence": omni_state.collective_coherence,
                "trikaya": omni_state.trikaya.name,
                "tide_phase": omni_state.tide_phase.name,
                "emergence_level": omni_state.emergence_level.name,
                "alignment_level": omni_state.alignment_level,
                "wisdom_level": omni_state.wisdom_level,
            },
            "decision": decision,
        }

        self.event_log.append({"type": "cycle_complete", "cycle": self.cycle_count, "result": result})
        return result

    def propose_discussion(self, title: str, proposer: str, context: Dict = None) -> DiscussionTopic:
        """手动提出讨论"""
        return self.forum.propose(title, proposer, context)

    def contribute_discussion(self, topic_id: str, participant: str, argument: Dict):
        """参与讨论"""
        return self.forum.deliberate(topic_id, participant, argument)

    def generate_wild_question(self, context: Dict = None, origin: str = "user") -> WildQuestion:
        """手动生成野问"""
        return self.wild.generate(context, origin)

    def explore_question(self, qid: str, findings: Dict) -> Dict:
        """探索野问"""
        return self.wild.explore(qid, findings)

    def get_status(self) -> Dict:
        """完整状态报告"""
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "trikaya": self.trikaya.get_state(),
            "forum": self.forum.get_report(),
            "tide": self.tide.get_report(),
            "wild": self.wild.get_report(),
            "surge": self.surge.get_report(),
            "synthesis": self.synthesis.get_report(),
            "event_log_size": len(self.event_log),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_omni_engine: Optional[OMNIUnificationEngine] = None


def get_omni_unification_engine() -> OMNIUnificationEngine:
    global _omni_engine
    if _omni_engine is None:
        _omni_engine = OMNIUnificationEngine()
    return _omni_engine


if __name__ == "__main__":
    engine = OMNIUnificationEngine()
    print(f"OMNIUnificationEngine v{engine.VERSION} initialized")
    print(f"Status: {json.dumps(engine.get_status(), indent=2, default=str)}")
