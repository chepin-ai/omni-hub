"""
OMNI-HUB v188 — CrossOracleValidator
跨预言机验证网

核心功能：
1. OracleTruthBridge        — 预言机-真值桥接
2. MultiSourceCrossValidator — 多源交叉验证
3. ConsensusFusion          — 共识融合
4. DiscrepancyAnalyzer      — 差异分析器
5. TrustPropagation         — 信任传播
6. CrossOracleValidator     — 统合引擎

映射：
- 桥接 = setu（桥）
- 融合 = saṃyoga（和合）
- 信任 = śraddhā（信）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class ValidationOutcome(Enum):
    """验证结果"""
    UNANIMOUS = 0       # 全体一致
    CONSENSUS = 1       # 共识
    DISPUTED = 2        # 争议
    CONTRADICTED = 3    # 矛盾
    INSUFFICIENT = 4    # 数据不足


class TrustLevel(Enum):
    """信任等级"""
    DISTRUSTED = 0
    CAUTIOUS = 1
    TRUSTED = 2
    HIGHLY_TRUSTED = 3
    ORACLE = 4


ALLIANCE_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
    "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"
]


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class BridgedFact:
    """桥接事实"""
    fact_id: str
    oracle_value: Any
    truth_value: Any
    bridge_timestamp: float
    discrepancy: float = 0.0


@dataclass
class CrossValidation:
    """交叉验证结果"""
    validation_id: str
    query: str
    sources: List[str]
    values: List[Any]
    outcome: ValidationOutcome
    confidence: float
    timestamp: float


@dataclass
class FusedConsensus:
    """融合共识"""
    consensus_id: str
    fused_value: Any
    oracle_confidence: float
    truth_confidence: float
    joint_confidence: float
    timestamp: float


@dataclass
class Discrepancy:
    """差异"""
    discrepancy_id: str
    source_a: str
    source_b: str
    value_a: Any
    value_b: Any
    magnitude: float
    timestamp: float


@dataclass
class TrustEdge:
    """信任边"""
    from_source: str
    to_source: str
    level: TrustLevel
    weight: float
    last_updated: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 预言机-真值桥接
# ═══════════════════════════════════════════════════════════════

class OracleTruthBridge:
    """预言机-真值桥接 — setu"""

    def __init__(self):
        self.bridged: deque = deque(maxlen=1000)
        self.bridge_stats: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "avg_discrepancy": 0.0})

    def bridge(self, query: str, oracle_value: Any, truth_value: Any) -> BridgedFact:
        """桥接预言机值和真值"""
        disc = self._compute_discrepancy(oracle_value, truth_value)
        fact = BridgedFact(
            fact_id=f"bridge_{hashlib.sha256(f'{query}:{time.time()}'.encode()).hexdigest()[:12]}",
            oracle_value=oracle_value,
            truth_value=truth_value,
            bridge_timestamp=time.time(),
            discrepancy=disc
        )
        self.bridged.append(fact)

        stats = self.bridge_stats[query]
        stats["count"] += 1
        stats["avg_discrepancy"] = (stats["avg_discrepancy"] * (stats["count"] - 1) + disc) / stats["count"]

        return fact

    def _compute_discrepancy(self, v1: Any, v2: Any) -> float:
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            return abs(v1 - v2) / max(abs(v1), abs(v2), 0.001)
        return 0.0 if v1 == v2 else 1.0

    def get_report(self) -> Dict:
        if not self.bridged:
            return {"bridged": 0}
        return {
            "bridged": len(self.bridged),
            "avg_discrepancy": sum(b.discrepancy for b in self.bridged) / len(self.bridged),
            "queries_bridged": len(self.bridge_stats),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 多源交叉验证
# ═══════════════════════════════════════════════════════════════

class MultiSourceCrossValidator:
    """多源交叉验证"""

    def __init__(self, consensus_threshold: float = 0.67):
        self.threshold = consensus_threshold
        self.validations: deque = deque(maxlen=500)

    def validate(self, query: str, source_values: Dict[str, Any]) -> CrossValidation:
        """验证多源数据"""
        sources = list(source_values.keys())
        values = list(source_values.values())

        if len(sources) < 2:
            return CrossValidation(
                validation_id=f"val_{int(time.time()*1000)}",
                query=query,
                sources=sources,
                values=values,
                outcome=ValidationOutcome.INSUFFICIENT,
                confidence=0.0,
                timestamp=time.time()
            )

        # 数值型：计算方差
        numeric = [v for v in values if isinstance(v, (int, float))]
        if numeric:
            mean = sum(numeric) / len(numeric)
            variance = sum((v - mean) ** 2 for v in numeric) / len(numeric)
            std = math.sqrt(variance) if variance > 0 else 0
            confidence = max(0, 1.0 - std / max(abs(mean), 0.001))

            if confidence >= 0.95:
                outcome = ValidationOutcome.UNANIMOUS
            elif confidence >= self.threshold:
                outcome = ValidationOutcome.CONSENSUS
            elif confidence >= 0.3:
                outcome = ValidationOutcome.DISPUTED
            else:
                outcome = ValidationOutcome.CONTRADICTED
        else:
            # 非数值：多数投票
            counts = {}
            for v in values:
                counts[v] = counts.get(v, 0) + 1
            max_count = max(counts.values())
            confidence = max_count / len(values)

            if confidence >= 0.95:
                outcome = ValidationOutcome.UNANIMOUS
            elif confidence >= self.threshold:
                outcome = ValidationOutcome.CONSENSUS
            else:
                outcome = ValidationOutcome.DISPUTED

        result = CrossValidation(
            validation_id=f"val_{int(time.time()*1000)}",
            query=query,
            sources=sources,
            values=values,
            outcome=outcome,
            confidence=confidence,
            timestamp=time.time()
        )
        self.validations.append(result)
        return result

    def get_report(self) -> Dict:
        if not self.validations:
            return {"validations": 0}
        recent = list(self.validations)[-20:]
        return {
            "validations": len(self.validations),
            "consensus_rate": sum(1 for v in recent if v.outcome in (ValidationOutcome.CONSENSUS, ValidationOutcome.UNANIMOUS)) / len(recent),
            "avg_confidence": sum(v.confidence for v in recent) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 共识融合
# ═══════════════════════════════════════════════════════════════

class ConsensusFusion:
    """共识融合 — saṃyoga"""

    def __init__(self):
        self.fusions: deque = deque(maxlen=500)

    def fuse(self, oracle_result: Dict, truth_result: Dict, query: str) -> FusedConsensus:
        """融合预言机和真值共识"""
        oracle_conf = oracle_result.get("confidence", 0.5)
        truth_conf = truth_result.get("confidence", 0.5)

        # 联合置信度（考虑独立性假设）
        joint = 1.0 - (1.0 - oracle_conf) * (1.0 - truth_conf)

        # 融合值
        oracle_val = oracle_result.get("value")
        truth_val = truth_result.get("value")
        if isinstance(oracle_val, (int, float)) and isinstance(truth_val, (int, float)):
            # 加权平均
            w1, w2 = oracle_conf, truth_conf
            fused = (oracle_val * w1 + truth_val * w2) / (w1 + w2) if (w1 + w2) > 0 else oracle_val
        else:
            fused = truth_val if truth_conf >= oracle_conf else oracle_val

        result = FusedConsensus(
            consensus_id=f"fuse_{hashlib.sha256(f'{query}:{time.time()}'.encode()).hexdigest()[:12]}",
            fused_value=fused,
            oracle_confidence=oracle_conf,
            truth_confidence=truth_conf,
            joint_confidence=joint,
            timestamp=time.time()
        )
        self.fusions.append(result)
        return result

    def get_report(self) -> Dict:
        if not self.fusions:
            return {"fusions": 0}
        recent = list(self.fusions)[-20:]
        return {
            "fusions": len(self.fusions),
            "avg_joint_confidence": sum(f.joint_confidence for f in recent) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 差异分析器
# ═══════════════════════════════════════════════════════════════

class DiscrepancyAnalyzer:
    """差异分析器"""

    def __init__(self):
        self.discrepancies: deque = deque(maxlen=500)
        self.source_discrepancy_count: Dict[str, int] = defaultdict(int)

    def analyze(self, source_values: Dict[str, Any]) -> List[Discrepancy]:
        """分析源间差异"""
        sources = list(source_values.keys())
        found = []

        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                sa, sb = sources[i], sources[j]
                va, vb = source_values[sa], source_values[sb]

                mag = self._magnitude(va, vb)
                if mag > 0.1:
                    disc = Discrepancy(
                        discrepancy_id=f"disc_{sa}_{sb}_{int(time.time()*1000)}",
                        source_a=sa,
                        source_b=sb,
                        value_a=va,
                        value_b=vb,
                        magnitude=mag,
                        timestamp=time.time()
                    )
                    self.discrepancies.append(disc)
                    self.source_discrepancy_count[sa] += 1
                    self.source_discrepancy_count[sb] += 1
                    found.append(disc)

        return found

    def _magnitude(self, v1: Any, v2: Any) -> float:
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            return abs(v1 - v2) / max(abs(v1), abs(v2), 0.001)
        return 0.0 if v1 == v2 else 1.0

    def get_report(self) -> Dict:
        if not self.discrepancies:
            return {"discrepancies": 0}
        return {
            "discrepancies": len(self.discrepancies),
            "avg_magnitude": sum(d.magnitude for d in self.discrepancies) / len(self.discrepancies),
            "worst_source": max(self.source_discrepancy_count.items(), key=lambda x: x[1])[0] if self.source_discrepancy_count else None,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 信任传播
# ═══════════════════════════════════════════════════════════════

class TrustPropagation:
    """信任传播 — śraddhā"""

    def __init__(self, decay: float = 0.95):
        self.decay = decay
        self.edges: Dict[Tuple[str, str], TrustEdge] = {}
        self.node_trust: Dict[str, float] = {}

    def set_trust(self, source: str, initial: float = 0.5):
        self.node_trust[source] = initial

    def add_edge(self, from_source: str, to_source: str, level: TrustLevel, weight: float = 1.0):
        key = (from_source, to_source)
        self.edges[key] = TrustEdge(
            from_source=from_source,
            to_source=to_source,
            level=level,
            weight=weight,
            last_updated=time.time()
        )

    def propagate(self, iterations: int = 3) -> Dict[str, float]:
        """传播信任值"""
        for _ in range(iterations):
            new_trust = dict(self.node_trust)
            for node in self.node_trust:
                incoming = [e for e in self.edges.values() if e.to_source == node]
                if not incoming:
                    continue
                weighted_sum = sum(self.node_trust.get(e.from_source, 0.5) * e.weight * e.level.value
                                  for e in incoming)
                total_weight = sum(e.weight * e.level.value for e in incoming)
                if total_weight > 0:
                    new_trust[node] = self.node_trust[node] * self.decay + (1 - self.decay) * (weighted_sum / total_weight)
            self.node_trust = new_trust
        return self.node_trust

    def get_report(self) -> Dict:
        if not self.node_trust:
            return {"nodes": 0}
        return {
            "nodes": len(self.node_trust),
            "edges": len(self.edges),
            "avg_trust": sum(self.node_trust.values()) / len(self.node_trust),
            "max_trust": max(self.node_trust.values()) if self.node_trust else 0,
            "min_trust": min(self.node_trust.values()) if self.node_trust else 0,
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — CrossOracleValidator v188
# ═══════════════════════════════════════════════════════════════

class CrossOracleValidator:
    """
    OMNI-HUB v188 跨预言机验证网

    setu · saṃyoga · śraddhā — 桥、和合、信
    """

    VERSION = "188.0.0"

    def __init__(self):
        self.bridge = OracleTruthBridge()
        self.validator = MultiSourceCrossValidator()
        self.fusion = ConsensusFusion()
        self.discrepancy = DiscrepancyAnalyzer()
        self.trust = TrustPropagation()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

        # 初始化所有线的信任值
        for line in ALLIANCE_LINES:
            self.trust.set_trust(line, 0.7)

    def validate_query(self, query: str, oracle_values: Dict[str, Any],
                      truth_values: Dict[str, Any]) -> Dict:
        """对查询进行跨预言机-真值验证"""
        # 1. 交叉验证预言机值
        oracle_validation = self.validator.validate(query, oracle_values)

        # 2. 交叉验证真值
        truth_validation = self.validator.validate(query, truth_values)

        # 3. 桥接
        if oracle_values and truth_values:
            oracle_avg = sum(v for v in oracle_values.values() if isinstance(v, (int, float))) / max(1, len(oracle_values))
            truth_avg = sum(v for v in truth_values.values() if isinstance(v, (int, float))) / max(1, len(truth_values))
            self.bridge.bridge(query, oracle_avg, truth_avg)

        # 4. 差异分析
        all_values = {**oracle_values, **truth_values}
        discs = self.discrepancy.analyze(all_values)

        # 5. 融合共识
        fused = self.fusion.fuse(
            {"value": oracle_avg if 'oracle_avg' in dir() else list(oracle_values.values())[0] if oracle_values else 0,
             "confidence": oracle_validation.confidence},
            {"value": truth_avg if 'truth_avg' in dir() else list(truth_values.values())[0] if truth_values else 0,
             "confidence": truth_validation.confidence},
            query
        )

        # 6. 更新信任
        for source in all_values:
            disc_count = sum(1 for d in discs if d.source_a == source or d.source_b == source)
            if disc_count > 2:
                self.trust.node_trust[source] = max(0, self.trust.node_trust.get(source, 0.5) - 0.1)
            elif disc_count == 0:
                self.trust.node_trust[source] = min(1, self.trust.node_trust.get(source, 0.5) + 0.05)

        self.trust.propagate(iterations=2)

        return {
            "query": query,
            "oracle_outcome": oracle_validation.outcome.name,
            "truth_outcome": truth_validation.outcome.name,
            "fused_confidence": fused.joint_confidence,
            "discrepancies": len(discs),
            "sources_validated": len(all_values),
        }

    def run_cycle(self, queries: List[str] = None,
                 oracle_data: Dict[str, Dict] = None,
                 truth_data: Dict[str, Dict] = None) -> Dict:
        """运行完整验证周期"""
        self.cycle_count += 1
        queries = queries or ["system_health"]
        oracle_data = oracle_data or {}
        truth_data = truth_data or {}

        results = []
        for query in queries:
            ov = oracle_data.get(query, {})
            tv = truth_data.get(query, {})
            result = self.validate_query(query, ov, tv)
            results.append(result)

        avg_confidence = sum(r["fused_confidence"] for r in results) / max(1, len(results))

        summary = {
            "cycle": self.cycle_count,
            "queries_validated": len(results),
            "avg_fused_confidence": avg_confidence,
            "total_discrepancies": sum(r["discrepancies"] for r in results),
            "trust_state": self.trust.node_trust,
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "bridge": self.bridge.get_report(),
            "validator": self.validator.get_report(),
            "fusion": self.fusion.get_report(),
            "discrepancy": self.discrepancy.get_report(),
            "trust": self.trust.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_cov_instance: Optional[CrossOracleValidator] = None


def get_cross_oracle_validator() -> CrossOracleValidator:
    global _cov_instance
    if _cov_instance is None:
        _cov_instance = CrossOracleValidator()
    return _cov_instance


if __name__ == "__main__":
    cov = CrossOracleValidator()
    print(f"CrossOracleValidator v{cov.VERSION} initialized")
    print(f"Status: {json.dumps(cov.get_status(), indent=2, default=str)}")
