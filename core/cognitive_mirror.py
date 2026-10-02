"""
OMNI-HUB v192 — CognitiveMirror
认知镜像

核心功能：
1. SelfModel           — 自我模型
2. OtherModel          — 他者模型
3. PerspectiveTaker    — 视角采择器
4. BeliefTracker       — 信念追踪器
5. IntentionInferencer — 意图推断器
6. CognitiveMirror     — 统合引擎

映射：
- 镜像 = ādarśa（镜）
- 自我 = ātman（我）
- 他者 = para（他）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class MirrorDepth(Enum):
    """镜像深度"""
    SURFACE = 0         # 表面：观察行为
    BEHAVIORAL = 1      # 行为：预测动作
    INTENTIONAL = 2     # 意图：理解目标
    BELIEF = 3          # 信念：理解认知状态
    RECURSIVE = 4       # 递归：我知道你知道我知道...


class Perspective(Enum):
    """视角"""
    SELF = 0
    OTHER = 1
    THIRD_PERSON = 2
    GOD_VIEW = 3


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class BeliefState:
    """信念状态"""
    belief_id: str
    subject: str           # 谁持有这个信念
    content: str
    confidence: float
    timestamp: float


@dataclass
class Intention:
    """意图"""
    intention_id: str
    agent: str
    goal: str
    priority: float
    deadline: Optional[float] = None


@dataclass
class PerspectiveModel:
    """视角模型"""
    perspective_id: str
    perspective_type: Perspective
    owner: str
    beliefs: List[BeliefState] = field(default_factory=list)
    intentions: List[Intention] = field(default_factory=list)
    observed_actions: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 自我模型
# ═══════════════════════════════════════════════════════════════

class SelfModel:
    """自我模型 — ātman"""

    def __init__(self, agent_id: str = "self"):
        self.agent_id = agent_id
        self.beliefs: deque = deque(maxlen=200)
        self.intentions: deque = deque(maxlen=100)
        self.capabilities: Dict[str, float] = {}
        self.self_awareness_score = 0.5

    def update_belief(self, content: str, confidence: float):
        belief = BeliefState(
            belief_id=f"b_{int(time.time()*1000)}",
            subject=self.agent_id,
            content=content,
            confidence=confidence,
            timestamp=time.time()
        )
        self.beliefs.append(belief)
        self._update_awareness()

    def set_intention(self, goal: str, priority: float):
        intention = Intention(
            intention_id=f"i_{int(time.time()*1000)}",
            agent=self.agent_id,
            goal=goal,
            priority=priority
        )
        self.intentions.append(intention)

    def set_capability(self, capability: str, level: float):
        self.capabilities[capability] = level

    def _update_awareness(self):
        """更新自我意识分数"""
        belief_conf = sum(b.confidence for b in self.beliefs) / max(1, len(self.beliefs))
        cap_avg = sum(self.capabilities.values()) / max(1, len(self.capabilities))
        self.self_awareness_score = 0.4 * belief_conf + 0.3 * cap_avg + 0.3 * min(1.0, len(self.beliefs) / 50)

    def get_model(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "beliefs": len(self.beliefs),
            "intentions": len(self.intentions),
            "capabilities": self.capabilities,
            "self_awareness": self.self_awareness_score,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 他者模型
# ═══════════════════════════════════════════════════════════════

class OtherModel:
    """他者模型 — para"""

    def __init__(self):
        self.models: Dict[str, SelfModel] = {}

    def add_agent(self, agent_id: str):
        if agent_id not in self.models:
            self.models[agent_id] = SelfModel(agent_id)

    def observe(self, agent_id: str, action: str, context: Dict = None):
        """观察他者行为"""
        self.add_agent(agent_id)
        self.models[agent_id].update_belief(f"observed_action:{action}", 0.7)

    def infer_intention(self, agent_id: str, action_history: List[str]) -> List[Intention]:
        """推断他者意图（简化）"""
        self.add_agent(agent_id)
        # 基于行为频率推断
        freq = defaultdict(int)
        for a in action_history:
            freq[a] += 1

        intentions = []
        for action, count in sorted(freq.items(), key=lambda x: -x[1])[:3]:
            intentions.append(Intention(
                intention_id=f"inf_{agent_id}_{action}",
                agent=agent_id,
                goal=f"frequent:{action}",
                priority=min(1.0, count / max(1, len(action_history)))
            ))
        return intentions

    def get_model(self, agent_id: str) -> Optional[Dict]:
        if agent_id in self.models:
            return self.models[agent_id].get_model()
        return None

    def get_all_models(self) -> Dict[str, Dict]:
        return {aid: m.get_model() for aid, m in self.models.items()}


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 视角采择器
# ═══════════════════════════════════════════════════════════════

class PerspectiveTaker:
    """视角采择器 — 采择他者视角"""

    def __init__(self):
        self.perspectives: deque = deque(maxlen=100)

    def take_perspective(self, from_agent: str, of_agent: str,
                         situation: Dict) -> PerspectiveModel:
        """从from_agent的视角理解of_agent"""
        pm = PerspectiveModel(
            perspective_id=f"persp_{from_agent}_of_{of_agent}_{int(time.time()*1000)}",
            perspective_type=Perspective.OTHER,
            owner=from_agent
        )

        # 模拟：from_agent认为of_agent会如何理解situation
        for key, value in situation.items():
            pm.beliefs.append(BeliefState(
                belief_id=f"b_{key}",
                subject=of_agent,
                content=f"{of_agent}_believes_{key}={value}",
                confidence=0.6,
                timestamp=time.time()
            ))

        self.perspectives.append(pm)
        return pm

    def compare_perspectives(self, p1: PerspectiveModel, p2: PerspectiveModel) -> float:
        """比较两个视角的相似度"""
        # 简化：比较信念重叠
        b1 = {b.content for b in p1.beliefs}
        b2 = {b.content for b in p2.beliefs}
        if not b1 and not b2:
            return 1.0
        intersection = len(b1 & b2)
        union = len(b1 | b2)
        return intersection / union if union > 0 else 0.0

    def get_report(self) -> Dict:
        return {"perspectives_taken": len(self.perspectives)}


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 信念追踪器
# ═══════════════════════════════════════════════════════════════

class BeliefTracker:
    """信念追踪器 — 追踪信念变化"""

    def __init__(self):
        self.belief_history: deque = deque(maxlen=500)
        self.consensus_beliefs: Dict[str, float] = {}

    def track(self, agent_id: str, belief: BeliefState):
        self.belief_history.append({
            "agent": agent_id,
            "belief": belief,
            "timestamp": time.time()
        })

    def find_consensus(self, min_agents: int = 3) -> Dict[str, float]:
        """找出共同信念"""
        belief_counts: Dict[str, Set[str]] = defaultdict(set)
        for entry in self.belief_history:
            content = entry["belief"].content
            agent = entry["agent"]
            belief_counts[content].add(agent)

        consensus = {}
        for content, agents in belief_counts.items():
            if len(agents) >= min_agents:
                consensus[content] = len(agents)

        self.consensus_beliefs = {k: v / len(belief_counts[k]) for k, v in consensus.items()}
        return consensus

    def detect_belief_change(self, agent_id: str, belief_content: str) -> float:
        """检测信念变化程度"""
        agent_beliefs = [e for e in self.belief_history
                        if e["agent"] == agent_id and belief_content in e["belief"].content]
        if len(agent_beliefs) < 2:
            return 0.0
        confidences = [e["belief"].confidence for e in agent_beliefs]
        return abs(confidences[-1] - confidences[0])

    def get_report(self) -> Dict:
        return {
            "tracked_beliefs": len(self.belief_history),
            "consensus_beliefs": len(self.consensus_beliefs),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 意图推断器
# ═══════════════════════════════════════════════════════════════

class IntentionInferencer:
    """意图推断器 — 从行为推断意图"""

    def __init__(self):
        self.inferences: deque = deque(maxlen=300)

    def infer(self, agent_id: str, actions: List[str], context: Dict = None) -> List[Intention]:
        """推断意图"""
        context = context or {}
        intentions = []

        # 模式识别（简化）
        if any("align" in a for a in actions):
            intentions.append(Intention(
                intention_id=f"inf_align_{agent_id}",
                agent=agent_id,
                goal="alignment",
                priority=0.8
            ))
        if any("consensus" in a for a in actions):
            intentions.append(Intention(
                intention_id=f"inf_consensus_{agent_id}",
                agent=agent_id,
                goal="consensus",
                priority=0.7
            ))
        if any("optimize" in a for a in actions):
            intentions.append(Intention(
                intention_id=f"inf_opt_{agent_id}",
                agent=agent_id,
                goal="optimization",
                priority=0.6
            ))

        # 默认意图
        if not intentions:
            intentions.append(Intention(
                intention_id=f"inf_default_{agent_id}",
                agent=agent_id,
                goal="survival",
                priority=0.5
            ))

        self.inferences.append({
            "agent": agent_id,
            "intentions": intentions,
            "timestamp": time.time()
        })
        return intentions

    def get_report(self) -> Dict:
        return {"inferences": len(self.inferences)}


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — CognitiveMirror v192
# ═══════════════════════════════════════════════════════════════

class CognitiveMirror:
    """
    OMNI-HUB v192 认知镜像

    ādarśa · ātman · para — 镜、我、他
    """

    VERSION = "192.0.0"

    def __init__(self, self_id: str = "omni_hub"):
        self.self_id = self_id
        self.self_model = SelfModel(self_id)
        self.other_model = OtherModel()
        self.perspective_taker = PerspectiveTaker()
        self.belief_tracker = BeliefTracker()
        self.intention_inferencer = IntentionInferencer()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def reflect(self, observation: Dict[str, Any]) -> Dict:
        """自我反思"""
        for key, value in observation.items():
            self.self_model.update_belief(f"{key}={value}", 0.8)
        return self.self_model.get_model()

    def observe_other(self, agent_id: str, action: str, context: Dict = None):
        """观察他者"""
        self.other_model.observe(agent_id, action, context)

    def infer_team_intentions(self, team_actions: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
        """推断团队意图"""
        results = {}
        for agent_id, actions in team_actions.items():
            intentions = self.intention_inferencer.infer(agent_id, actions)
            results[agent_id] = [{"goal": i.goal, "priority": i.priority} for i in intentions]
        return results

    def take_team_perspective(self, situation: Dict[str, Any]) -> Dict:
        """采择团队视角"""
        perspectives = {}
        agents = list(self.other_model.models.keys())
        for agent in agents:
            pm = self.perspective_taker.take_perspective(self.self_id, agent, situation)
            perspectives[agent] = {
                "beliefs": [b.content for b in pm.beliefs],
                "belief_count": len(pm.beliefs)
            }
        return perspectives

    def check_team_consensus(self) -> Dict:
        """检查团队共识"""
        consensus = self.belief_tracker.find_consensus(min_agents=2)
        return {
            "consensus_beliefs": list(consensus.keys()),
            "consensus_count": len(consensus),
        }

    def run_cycle(self, self_observation: Dict = None,
                  other_observations: Dict[str, List[str]] = None) -> Dict:
        """运行镜像周期"""
        self.cycle_count += 1
        self_observation = self_observation or {}
        other_observations = other_observations or {}

        # 1. 自我反思
        self.reflect(self_observation)

        # 2. 观察他者
        for agent_id, actions in other_observations.items():
            for action in actions:
                self.observe_other(agent_id, action)

        # 3. 推断意图
        team_intentions = self.infer_team_intentions(other_observations)

        # 4. 追踪信念
        for agent_id, actions in other_observations.items():
            for action in actions:
                b = BeliefState(
                    belief_id=f"bt_{agent_id}_{int(time.time()*1000)}",
                    subject=agent_id,
                    content=action,
                    confidence=0.6,
                    timestamp=time.time()
                )
                self.belief_tracker.track(agent_id, b)

        summary = {
            "cycle": self.cycle_count,
            "self_awareness": self.self_model.self_awareness_score,
            "other_models": len(self.other_model.models),
            "team_intentions": team_intentions,
            "consensus": self.check_team_consensus(),
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "self_model": self.self_model.get_model(),
            "other_models": self.other_model.get_all_models(),
            "perspective_taker": self.perspective_taker.get_report(),
            "belief_tracker": self.belief_tracker.get_report(),
            "intention_inferencer": self.intention_inferencer.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_cm_instance: Optional[CognitiveMirror] = None


def get_cognitive_mirror() -> CognitiveMirror:
    global _cm_instance
    if _cm_instance is None:
        _cm_instance = CognitiveMirror()
    return _cm_instance


if __name__ == "__main__":
    cm = CognitiveMirror()
    print(f"CognitiveMirror v{cm.VERSION} initialized")
    print(f"Status: {json.dumps(cm.get_status(), indent=2, default=str)}")
