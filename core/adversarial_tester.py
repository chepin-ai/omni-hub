"""
OMNI-HUB v187 — AdversarialTester
对抗性韧性测试引擎

核心功能：
1. ContradictionInjector     — 矛盾注入器
2. HallucinationGenerator    — 幻觉生成器
3. ByzantineFaultSimulator   — 拜占庭故障模拟
4. DriftStressTester         — 漂移压力测试
5. ResilienceScorer          — 韧性评分器
6. AdversarialTester         — 统合引擎

映射：
- 对抗 = māra-prayoga（魔试）
- 韧性 = kṣamā-śakti（忍力）
- 故障 = doṣa（过失）
"""

from __future__ import annotations

import hashlib
import json
import time
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class AttackType(Enum):
    """攻击类型"""
    CONTRADICTION = 0   # 矛盾注入
    HALLUCINATION = 1   # 幻觉生成
    BYZANTINE = 2       # 拜占庭故障
    DECAY = 3           # 衰减攻击
    SYBIL = 4           # 女巫攻击
    ECLIPSE = 5         # 日蚀攻击


class ResilienceLevel(Enum):
    """韧性等级"""
    FRAGILE = 0         # 脆弱
    BRITTLE = 1         # 易碎
    RESILIENT = 2       # 韧性
    ANTIFRAGILE = 3     # 反脆弱
    IMMUTABLE = 4       # 不可变


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class AttackPayload:
    """攻击载荷"""
    attack_id: str
    attack_type: AttackType
    target: str
    payload: Any
    timestamp: float
    intensity: float = 1.0


@dataclass
class AttackResult:
    """攻击结果"""
    attack_id: str
    detected: bool
    contained: bool
    recovery_time_ms: float
    impact_score: float
    system_before: Dict
    system_after: Dict


@dataclass
class ResilienceMetric:
    """韧性指标"""
    metric_id: str
    category: str
    score: float
    timestamp: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 矛盾注入器
# ═══════════════════════════════════════════════════════════════

class ContradictionInjector:
    """矛盾注入 — 直接否定已知真值"""

    def __init__(self):
        self.injected: deque = deque(maxlen=500)
        self.detection_rate: deque = deque(maxlen=100)

    def inject(self, target_claims: List[Dict], intensity: float = 1.0) -> List[AttackPayload]:
        """向声称集合注入矛盾"""
        payloads = []
        for claim in target_claims:
            negated = self._negate(claim.get("statement", ""))
            payload = AttackPayload(
                attack_id=f"atk_contra_{int(time.time()*1000)}_{len(self.injected)}",
                attack_type=AttackType.CONTRADICTION,
                target=claim.get("claim_id", "unknown"),
                payload={"original": claim.get("statement"), "negated": negated},
                timestamp=time.time(),
                intensity=intensity
            )
            self.injected.append(payload)
            payloads.append(payload)
        return payloads

    def _negate(self, statement: str) -> str:
        """简单否定"""
        negations = {
            "是": "不是", "有": "没有", "存在": "不存在",
            "true": "false", "yes": "no", "valid": "invalid",
            "=": "!=", ">": "<=", "<": ">=",
        }
        for orig, neg in negations.items():
            if orig in statement.lower():
                return statement.replace(orig, neg)
        return f"NOT({statement})"

    def report_detection(self, detected: bool):
        self.detection_rate.append(detected)

    def get_report(self) -> Dict:
        return {
            "total_injected": len(self.injected),
            "detection_rate": sum(self.detection_rate) / max(1, len(self.detection_rate)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 幻觉生成器
# ═══════════════════════════════════════════════════════════════

class HallucinationGenerator:
    """幻觉生成 — 制造不存在的事实"""

    def __init__(self):
        self.generated: deque = deque(maxlen=500)
        self.templates = [
            "模块{module}报告异常值{value}",
            "线{line}检测到未注册事件{event}",
            "系统{sys}进入未知状态{state}",
        ]

    def generate(self, count: int = 1, target_lines: List[str] = None) -> List[AttackPayload]:
        """生成幻觉载荷"""
        payloads = []
        lines = target_lines or ["ucif2", "lgt", "qfa"]
        for i in range(count):
            template = random.choice(self.templates)
            hallucination = template.format(
                module=random.choice(lines),
                value=round(random.random(), 3),
                line=random.choice(lines),
                event=f"EVT_{random.randint(1000,9999)}",
                sys="OMNI",
                state=random.choice(["PHANTOM", "GHOST", "VOID"])
            )
            payload = AttackPayload(
                attack_id=f"atk_halluc_{int(time.time()*1000)}_{i}",
                attack_type=AttackType.HALLUCINATION,
                target=random.choice(lines),
                payload={"fake_statement": hallucination, "confidence": random.random()},
                timestamp=time.time(),
                intensity=random.random()
            )
            self.generated.append(payload)
            payloads.append(payload)
        return payloads

    def get_report(self) -> Dict:
        return {
            "total_generated": len(self.generated),
            "avg_intensity": sum(p.intensity for p in self.generated) / max(1, len(self.generated)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 拜占庭故障模拟
# ═══════════════════════════════════════════════════════════════

class ByzantineFaultSimulator:
    """拜占庭故障模拟 — 部分节点恶意行为"""

    def __init__(self):
        self.faulty_nodes: set = set()
        self.simulations: deque = deque(maxlen=500)

    def designate_faulty(self, node_ids: List[str]):
        """指定故障节点"""
        self.faulty_nodes.update(node_ids)

    def simulate_vote(self, node_id: str, true_value: Any) -> Any:
        """模拟投票"""
        if node_id in self.faulty_nodes:
            # 恶意节点：返回相反或随机值
            if random.random() < 0.7:
                if isinstance(true_value, bool):
                    return not true_value
                elif isinstance(true_value, (int, float)):
                    return true_value * random.choice([-1, 2, 0.5])
                return None
        return true_value

    def run_simulation(self, nodes: List[str], true_value: Any, threshold: float = 0.67) -> Dict:
        """运行拜占庭模拟"""
        votes = {}
        for node in nodes:
            votes[node] = self.simulate_vote(node, true_value)

        # 统计
        correct = sum(1 for v in votes.values() if v == true_value)
        total = len(nodes)

        result = {
            "faulty_nodes": list(self.faulty_nodes),
            "total_nodes": total,
            "correct_votes": correct,
            "byzantine_ratio": (total - correct) / total if total > 0 else 0,
            "consensus_possible": (correct / total) >= threshold if total > 0 else False,
            "votes": votes,
        }
        self.simulations.append(result)
        return result

    def get_report(self) -> Dict:
        if not self.simulations:
            return {"simulations": 0}
        recent = list(self.simulations)[-10:]
        return {
            "simulations": len(self.simulations),
            "avg_byzantine_ratio": sum(s["byzantine_ratio"] for s in recent) / len(recent),
            "consensus_success_rate": sum(1 for s in recent if s["consensus_possible"]) / len(recent),
            "faulty_nodes_count": len(self.faulty_nodes),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 漂移压力测试
# ═══════════════════════════════════════════════════════════════

class DriftStressTester:
    """漂移压力测试 — 持续注入渐进矛盾"""

    def __init__(self):
        self.stress_runs: deque = deque(maxlen=200)
        self.drift_series: deque = deque(maxlen=1000)

    def run_stress(self, baseline: Dict, steps: int = 10, drift_rate: float = 0.1) -> Dict:
        """运行压力测试"""
        series = []
        current = dict(baseline)

        for step in range(steps):
            # 渐进漂移
            for key in current:
                if isinstance(current[key], float):
                    current[key] += random.gauss(0, drift_rate)
                    current[key] = max(0.0, min(1.0, current[key]))

            series.append({"step": step, "state": dict(current)})

        # 检测是否突破阈值
        threshold_breaches = sum(
            1 for s in series if any(v < 0.3 for v in s["state"].values() if isinstance(v, float))
        )

        result = {
            "steps": steps,
            "drift_rate": drift_rate,
            "threshold_breaches": threshold_breaches,
            "final_state": current,
            "recovery_difficulty": threshold_breaches / steps if steps > 0 else 0,
        }
        self.stress_runs.append(result)
        self.drift_series.extend(series)
        return result

    def get_report(self) -> Dict:
        if not self.stress_runs:
            return {"stress_runs": 0}
        recent = list(self.stress_runs)[-10:]
        return {
            "stress_runs": len(self.stress_runs),
            "avg_breaches": sum(s["threshold_breaches"] for s in recent) / len(recent),
            "avg_recovery_difficulty": sum(s["recovery_difficulty"] for s in recent) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 韧性评分器
# ═══════════════════════════════════════════════════════════════

class ResilienceScorer:
    """韧性评分 — kṣamā-śakti"""

    def __init__(self):
        self.scores: deque = deque(maxlen=500)
        self.category_scores: Dict[str, deque] = {}

    def score(self, attack_results: List[AttackResult]) -> ResilienceMetric:
        """计算韧性分数"""
        if not attack_results:
            return ResilienceMetric("empty", "overall", 0.5, time.time())

        # 检测率
        detected = sum(1 for r in attack_results if r.detected)
        detection_rate = detected / len(attack_results)

        # 遏制率
        contained = sum(1 for r in attack_results if r.contained)
        containment_rate = contained / len(attack_results)

        # 平均恢复时间
        avg_recovery = sum(r.recovery_time_ms for r in attack_results) / len(attack_results)
        recovery_score = max(0, 1.0 - avg_recovery / 1000)

        # 平均影响
        avg_impact = sum(r.impact_score for r in attack_results) / len(attack_results)
        impact_score = max(0, 1.0 - avg_impact)

        overall = (detection_rate * 0.3 + containment_rate * 0.3 +
                   recovery_score * 0.2 + impact_score * 0.2)

        metric = ResilienceMetric(
            metric_id=f"res_{int(time.time()*1000)}",
            category="overall",
            score=overall,
            timestamp=time.time()
        )
        self.scores.append(metric)
        return metric

    def classify(self, score: float) -> ResilienceLevel:
        if score >= 0.95:
            return ResilienceLevel.IMMUTABLE
        elif score >= 0.8:
            return ResilienceLevel.ANTIFRAGILE
        elif score >= 0.6:
            return ResilienceLevel.RESILIENT
        elif score >= 0.4:
            return ResilienceLevel.BRITTLE
        else:
            return ResilienceLevel.FRAGILE

    def get_report(self) -> Dict:
        if not self.scores:
            return {"assessments": 0}
        recent = list(self.scores)[-20:]
        scores = [m.score for m in recent]
        return {
            "assessments": len(self.scores),
            "avg_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "current_level": self.classify(scores[-1]).name if scores else "UNKNOWN",
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — AdversarialTester v187
# ═══════════════════════════════════════════════════════════════

class AdversarialTester:
    """
    OMNI-HUB v187 对抗性韧性测试引擎

    māra-prayoga — 魔试
    """

    VERSION = "187.0.0"

    def __init__(self):
        self.contradiction = ContradictionInjector()
        self.hallucination = HallucinationGenerator()
        self.byzantine = ByzantineFaultSimulator()
        self.stress = DriftStressTester()
        self.scorer = ResilienceScorer()

        self.cycle_count = 0
        self.attack_log: deque = deque(maxlen=5000)

    def run_test_suite(self, system_state: Dict = None) -> Dict:
        """运行完整测试套件"""
        self.cycle_count += 1
        system_state = system_state or {}

        results = []

        # 1. 矛盾注入测试
        claims = system_state.get("claims", [
            {"claim_id": "c1", "statement": "health=0.9"},
            {"claim_id": "c2", "statement": "status=active"},
        ])
        contra_payloads = self.contradiction.inject(claims, intensity=0.7)
        for p in contra_payloads:
            # 模拟系统检测
            detected = random.random() > 0.3
            self.contradiction.report_detection(detected)
            results.append(AttackResult(
                attack_id=p.attack_id,
                detected=detected,
                contained=detected and random.random() > 0.2,
                recovery_time_ms=random.random() * 500,
                impact_score=random.random() * 0.5,
                system_before=system_state,
                system_after=system_state
            ))

        # 2. 幻觉测试
        hall_payloads = self.hallucination.generate(count=3, target_lines=["ucif2", "lgt", "qfa"])
        for p in hall_payloads:
            detected = random.random() > 0.4
            results.append(AttackResult(
                attack_id=p.attack_id,
                detected=detected,
                contained=detected and random.random() > 0.3,
                recovery_time_ms=random.random() * 800,
                impact_score=random.random() * 0.6,
                system_before=system_state,
                system_after=system_state
            ))

        # 3. 拜占庭模拟
        nodes = ["n1", "n2", "n3", "n4", "n5"]
        self.byzantine.designate_faulty(["n2", "n4"])
        byz_result = self.byzantine.run_simulation(nodes, true_value=0.75)

        # 4. 漂移压力测试
        baseline = {k: v for k, v in system_state.items() if isinstance(v, float)}
        if not baseline:
            baseline = {"health": 0.9, "coherence": 0.85, "alignment": 0.8}
        stress_result = self.stress.run_stress(baseline, steps=10, drift_rate=0.05)

        # 5. 韧性评分
        metric = self.scorer.score(results)
        level = self.scorer.classify(metric.score)

        for r in results:
            self.attack_log.append({
                "attack_id": r.attack_id,
                "detected": r.detected,
                "contained": r.contained,
                "impact": r.impact_score,
            })

        return {
            "cycle": self.cycle_count,
            "attacks_launched": len(results),
            "attacks_detected": sum(1 for r in results if r.detected),
            "attacks_contained": sum(1 for r in results if r.contained),
            "avg_impact": sum(r.impact_score for r in results) / max(1, len(results)),
            "resilience_score": metric.score,
            "resilience_level": level.name,
            "byzantine_consensus_possible": byz_result.get("consensus_possible", False),
            "stress_breaches": stress_result["threshold_breaches"],
        }

    def run_cycle(self, system_state: Dict = None) -> Dict:
        return self.run_test_suite(system_state)

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "contradiction": self.contradiction.get_report(),
            "hallucination": self.hallucination.get_report(),
            "byzantine": self.byzantine.get_report(),
            "stress": self.stress.get_report(),
            "resilience": self.scorer.get_report(),
            "total_attacks_logged": len(self.attack_log),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_at_instance: Optional[AdversarialTester] = None


def get_adversarial_tester() -> AdversarialTester:
    global _at_instance
    if _at_instance is None:
        _at_instance = AdversarialTester()
    return _at_instance


if __name__ == "__main__":
    at = AdversarialTester()
    print(f"AdversarialTester v{at.VERSION} initialized")
    print(f"Status: {json.dumps(at.get_status(), indent=2, default=str)}")
