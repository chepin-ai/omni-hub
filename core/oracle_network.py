"""
OMNI-HUB v187 — OracleNetwork
预言机网络

核心功能：
1. OracleRegistry           — 预言机注册管理
2. MultiOracleAggregator     — 多预言机聚合
3. OracleReputationTracker   — 预言机信誉追踪
4. ChainDataBridge           — 链下数据桥接
5. OracleConsensusEngine     — 预言机共识引擎
6. OracleNetwork             — 统合引擎

映射：
- 预言机 = deva-cakṣus（天眼）
- 共识 = saṃgīti（结集）
- 信誉 = puṇya-karma（善业）
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class OracleStatus(Enum):
    """预言机状态"""
    OFFLINE = 0
    SYNCING = 1
    ONLINE = 2
    DEGRADED = 3
    BANNED = 4


class AggregationMethod(Enum):
    """聚合方法"""
    MEAN = 0
    MEDIAN = 1
    WEIGHTED_MEAN = 2
    MAJORITY_VOTE = 3
    STAKED_QUORUM = 4


class DataDomain(Enum):
    """数据域"""
    PRICE = 0
    WEATHER = 1
    TIMESTAMP = 2
    EVENT = 3
    IDENTITY = 4
    LOCATION = 5
    CUSTOM = 6


ALLIANCE_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
    "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"
]


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class OracleSource:
    """预言机源"""
    source_id: str
    name: str
    endpoint: str
    domain: DataDomain
    status: OracleStatus = OracleStatus.OFFLINE
    reliability: float = 0.5
    last_update: float = 0.0
    latency_ms: float = 0.0
    stake: float = 1.0
    line_affinity: Optional[str] = None


@dataclass
class OracleReading:
    """预言机读数"""
    reading_id: str
    source_id: str
    query: str
    value: Any
    timestamp: float
    confidence: float = 1.0
    signature: str = ""


@dataclass
class AggregatedResult:
    """聚合结果"""
    result_id: str
    query: str
    aggregated_value: Any
    method: AggregationMethod
    sources_used: List[str]
    confidence: float
    variance: float
    timestamp: float
    consensus_reached: bool = False


@dataclass
class OracleReputation:
    """预言机信誉"""
    source_id: str
    total_submissions: int = 0
    correct_predictions: int = 0
    incorrect_predictions: int = 0
    consistency_score: float = 0.5
    last_evaluated: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 预言机注册管理
# ═══════════════════════════════════════════════════════════════

class OracleRegistry:
    """预言机注册管理 — deva-cakṣus"""

    def __init__(self):
        self.oracles: Dict[str, OracleSource] = {}
        self.domain_index: Dict[DataDomain, List[str]] = {}

    def register(self, source: OracleSource) -> bool:
        """注册预言机"""
        self.oracles[source.source_id] = source
        if source.domain not in self.domain_index:
            self.domain_index[source.domain] = []
        if source.source_id not in self.domain_index[source.domain]:
            self.domain_index[source.domain].append(source.source_id)
        return True

    def deregister(self, source_id: str) -> bool:
        """注销预言机"""
        if source_id not in self.oracles:
            return False
        source = self.oracles[source_id]
        if source.domain in self.domain_index and source_id in self.domain_index[source.domain]:
            self.domain_index[source.domain].remove(source_id)
        del self.oracles[source_id]
        return True

    def update_status(self, source_id: str, status: OracleStatus):
        if source_id in self.oracles:
            self.oracles[source_id].status = status
            self.oracles[source_id].last_update = time.time()

    def get_by_domain(self, domain: DataDomain) -> List[OracleSource]:
        ids = self.domain_index.get(domain, [])
        return [self.oracles[sid] for sid in ids if sid in self.oracles]

    def get_online(self) -> List[OracleSource]:
        return [o for o in self.oracles.values() if o.status == OracleStatus.ONLINE]

    def get_report(self) -> Dict:
        status_counts = {}
        for o in self.oracles.values():
            status_counts[o.status.name] = status_counts.get(o.status.name, 0) + 1
        return {
            "total": len(self.oracles),
            "online": len(self.get_online()),
            "status_distribution": status_counts,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 多预言机聚合
# ═══════════════════════════════════════════════════════════════

class MultiOracleAggregator:
    """多预言机聚合"""

    def __init__(self, default_method: AggregationMethod = AggregationMethod.WEIGHTED_MEAN):
        self.default_method = default_method
        self.history: deque = deque(maxlen=1000)

    def aggregate(self, readings: List[OracleReading], method: AggregationMethod = None,
                  weights: Dict[str, float] = None) -> Optional[AggregatedResult]:
        """聚合读数"""
        if not readings:
            return None

        method = method or self.default_method
        query = readings[0].query
        result_id = f"agg_{hashlib.sha256(f'{query}:{time.time()}'.encode()).hexdigest()[:12]}"

        sources_used = [r.source_id for r in readings]
        weights = weights or {}

        # 提取数值
        numeric = [(r, r.value) for r in readings if isinstance(r.value, (int, float))]

        if not numeric:
            # 非数值：多数投票
            values = [r.value for r in readings]
            aggregated = max(set(values), key=values.count)
            confidence = values.count(aggregated) / len(values)
            variance = 0.0
            consensus = confidence >= 0.67
        else:
            vals = [v for _, v in numeric]
            if method == AggregationMethod.MEAN:
                aggregated = sum(vals) / len(vals)
            elif method == AggregationMethod.MEDIAN:
                sorted_vals = sorted(vals)
                mid = len(sorted_vals) // 2
                aggregated = sorted_vals[mid] if len(sorted_vals) % 2 == 1 else (sorted_vals[mid-1] + sorted_vals[mid]) / 2
            elif method == AggregationMethod.WEIGHTED_MEAN:
                total_weight = 0
                weighted_sum = 0
                for r, v in numeric:
                    w = weights.get(r.source_id, 1.0)
                    weighted_sum += v * w
                    total_weight += w
                aggregated = weighted_sum / total_weight if total_weight > 0 else sum(vals) / len(vals)
            else:
                aggregated = sum(vals) / len(vals)

            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals)
            std_dev = variance ** 0.5
            confidence = 1.0 - min(1.0, std_dev / max(abs(mean), 0.001))
            consensus = confidence >= 0.67

        result = AggregatedResult(
            result_id=result_id,
            query=query,
            aggregated_value=aggregated,
            method=method,
            sources_used=sources_used,
            confidence=confidence,
            variance=variance,
            timestamp=time.time(),
            consensus_reached=consensus
        )
        self.history.append(result)
        return result

    def get_report(self) -> Dict:
        if not self.history:
            return {"total_aggregations": 0}
        recent = list(self.history)[-20:]
        return {
            "total_aggregations": len(self.history),
            "avg_confidence": sum(r.confidence for r in recent) / len(recent),
            "consensus_rate": sum(1 for r in recent if r.consensus_reached) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 预言机信誉追踪
# ═══════════════════════════════════════════════════════════════

class OracleReputationTracker:
    """预言机信誉追踪 — puṇya-karma"""

    def __init__(self, decay_factor: float = 0.99):
        self.reputations: Dict[str, OracleReputation] = {}
        self.decay_factor = decay_factor
        self.evaluation_log: deque = deque(maxlen=1000)

    def register(self, source_id: str):
        if source_id not in self.reputations:
            self.reputations[source_id] = OracleReputation(source_id=source_id)

    def evaluate(self, source_id: str, predicted: Any, actual: Any):
        """评估预测准确性"""
        if source_id not in self.reputations:
            self.register(source_id)

        rep = self.reputations[source_id]
        rep.total_submissions += 1

        # 简化的正确性判断
        correct = self._is_correct(predicted, actual)
        if correct:
            rep.correct_predictions += 1
        else:
            rep.incorrect_predictions += 1

        # 更新一致性
        total = rep.correct_predictions + rep.incorrect_predictions
        rep.consistency_score = rep.correct_predictions / max(1, total)
        rep.last_evaluated = time.time()

        self.evaluation_log.append({
            "source_id": source_id,
            "correct": correct,
            "time": time.time(),
        })

    def _is_correct(self, predicted: Any, actual: Any) -> bool:
        if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
            return abs(predicted - actual) <= 0.05 * max(abs(actual), 0.001)
        return predicted == actual

    def get_reputation(self, source_id: str) -> float:
        rep = self.reputations.get(source_id)
        if not rep:
            return 0.5
        return rep.consistency_score

    def get_top_oracles(self, n: int = 5) -> List[Tuple[str, float]]:
        scores = [(sid, r.consistency_score) for sid, r in self.reputations.items()]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]

    def get_report(self) -> Dict:
        if not self.reputations:
            return {"oracles_tracked": 0}
        scores = [r.consistency_score for r in self.reputations.values()]
        return {
            "oracles_tracked": len(self.reputations),
            "avg_reputation": sum(scores) / len(scores),
            "top_oracle": max(self.reputations.items(), key=lambda x: x[1].consistency_score)[0] if self.reputations else None,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 链下数据桥接
# ═══════════════════════════════════════════════════════════════

class ChainDataBridge:
    """链下数据桥接"""

    def __init__(self):
        self.bridges: Dict[str, Dict] = {}
        self.pending: deque = deque(maxlen=500)
        self.confirmed: deque = deque(maxlen=500)

    def register_bridge(self, bridge_id: str, source_type: str, config: Dict):
        self.bridges[bridge_id] = {
            "type": source_type,
            "config": config,
            "status": "active",
            "created": time.time(),
        }

    def submit_offchain(self, bridge_id: str, data: Dict) -> str:
        """提交链下数据"""
        tx_id = f"offchain_{bridge_id}_{int(time.time()*1000)}"
        self.pending.append({
            "tx_id": tx_id,
            "bridge_id": bridge_id,
            "data": data,
            "submitted": time.time(),
        })
        return tx_id

    def confirm(self, tx_id: str):
        """确认数据上链/入系统"""
        for item in list(self.pending):
            if item["tx_id"] == tx_id:
                self.pending.remove(item)
                item["confirmed"] = time.time()
                self.confirmed.append(item)
                return True
        return False

    def get_report(self) -> Dict:
        return {
            "bridges": len(self.bridges),
            "pending": len(self.pending),
            "confirmed": len(self.confirmed),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 预言机共识引擎
# ═══════════════════════════════════════════════════════════════

class OracleConsensusEngine:
    """预言机共识引擎 — saṃgīti"""

    def __init__(self, quorum_threshold: float = 0.67):
        self.quorum_threshold = quorum_threshold
        self.consensus_log: deque = deque(maxlen=500)
        self.proposals: Dict[str, Dict] = {}

    def propose(self, query: str, proposed_value: Any, proposer: str) -> str:
        """提出共识提案"""
        pid = f"prop_{hashlib.sha256(f'{query}:{proposed_value}'.encode()).hexdigest()[:12]}"
        self.proposals[pid] = {
            "query": query,
            "proposed": proposed_value,
            "proposer": proposer,
            "votes": {},
            "status": "pending",
            "time": time.time(),
        }
        return pid

    def vote(self, proposal_id: str, voter: str, value: Any, weight: float = 1.0) -> Dict:
        """投票"""
        if proposal_id not in self.proposals:
            return {"error": "proposal_not_found"}

        self.proposals[proposal_id]["votes"][voter] = {
            "value": value,
            "weight": weight,
            "time": time.time(),
        }
        return self.proposals[proposal_id]

    def finalize(self, proposal_id: str) -> Dict:
        """ finalize共识"""
        if proposal_id not in self.proposals:
            return {"error": "proposal_not_found"}

        prop = self.proposals[proposal_id]
        votes = prop["votes"]
        if not votes:
            return {"consensus": False, "reason": "no_votes"}

        # 统计值分布
        value_weights: Dict[Any, float] = {}
        for v in votes.values():
            val = round(v["value"], 6) if isinstance(v["value"], float) else v["value"]
            value_weights[val] = value_weights.get(val, 0) + v["weight"]

        total_weight = sum(v["weight"] for v in votes.values())
        max_val, max_weight = max(value_weights.items(), key=lambda x: x[1])

        consensus = (max_weight / total_weight) >= self.quorum_threshold if total_weight > 0 else False

        result = {
            "proposal_id": proposal_id,
            "consensus": consensus,
            "winning_value": max_val if consensus else None,
            "agreement_ratio": max_weight / total_weight if total_weight > 0 else 0,
            "threshold": self.quorum_threshold,
            "total_votes": len(votes),
        }

        prop["status"] = "accepted" if consensus else "rejected"
        self.consensus_log.append(result)
        return result

    def get_report(self) -> Dict:
        accepted = sum(1 for r in self.consensus_log if r.get("consensus"))
        total = len(self.consensus_log)
        return {
            "total_proposals": len(self.proposals),
            "resolved": total,
            "accepted": accepted,
            "rejected": total - accepted,
            "consensus_rate": accepted / max(1, total),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OracleNetwork v187
# ═══════════════════════════════════════════════════════════════

class OracleNetwork:
    """
    OMNI-HUB v187 预言机网络

    deva-cakṣus — 天眼
    """

    VERSION = "187.0.0"

    def __init__(self):
        self.registry = OracleRegistry()
        self.aggregator = MultiOracleAggregator()
        self.reputation = OracleReputationTracker()
        self.bridge = ChainDataBridge()
        self.consensus = OracleConsensusEngine()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

        # 注册默认预言机
        self._register_defaults()

    def _register_defaults(self):
        """注册默认预言机"""
        defaults = [
            OracleSource("oracle_1", "Primary Oracle", "internal://primary", DataDomain.CUSTOM, OracleStatus.ONLINE, 0.9),
            OracleSource("oracle_2", "Secondary Oracle", "internal://secondary", DataDomain.CUSTOM, OracleStatus.ONLINE, 0.8),
            OracleSource("oracle_3", "Tertiary Oracle", "internal://tertiary", DataDomain.CUSTOM, OracleStatus.SYNCING, 0.7),
        ]
        for o in defaults:
            self.registry.register(o)
            self.reputation.register(o.source_id)

    def query(self, query: str, domain: DataDomain = DataDomain.CUSTOM,
              method: AggregationMethod = None) -> Optional[AggregatedResult]:
        """查询预言机网络"""
        oracles = self.registry.get_by_domain(domain)
        oracles = [o for o in oracles if o.status == OracleStatus.ONLINE]

        if not oracles:
            return None

        # 收集读数
        readings = []
        for oracle in oracles:
            # 模拟读数
            value = self._simulate_reading(query, oracle.source_id)
            reading = OracleReading(
                reading_id=f"read_{oracle.source_id}_{int(time.time()*1000)}",
                source_id=oracle.source_id,
                query=query,
                value=value,
                timestamp=time.time(),
                confidence=oracle.reliability
            )
            readings.append(reading)

        # 基于信誉的权重
        weights = {o.source_id: self.reputation.get_reputation(o.source_id) for o in oracles}

        return self.aggregator.aggregate(readings, method=method, weights=weights)

    def _simulate_reading(self, query: str, source_id: str) -> float:
        """模拟读数（基于hash的确定性随机）"""
        seed = int(hashlib.sha256(f"{query}:{source_id}:{self.cycle_count}".encode()).hexdigest(), 16)
        return 0.5 + (seed % 1000) / 1000.0 * 0.5

    def run_cycle(self, queries: List[str] = None) -> Dict:
        """运行完整预言机周期"""
        self.cycle_count += 1
        queries = queries or ["system_health", "coherence_check"]

        results = []
        for query in queries:
            result = self.query(query)
            if result:
                results.append(result)

        # 更新预言机状态
        for oracle in self.registry.oracles.values():
            if oracle.status == OracleStatus.SYNCING and self.cycle_count % 3 == 0:
                self.registry.update_status(oracle.source_id, OracleStatus.ONLINE)

        # 评估信誉（模拟）
        for oid in self.reputation.reputations:
            pred = self._simulate_reading("benchmark", oid)
            actual = 0.75  # 假设基准值
            self.reputation.evaluate(oid, pred, actual)

        consensus_results = []
        for result in results:
            if result and result.consensus_reached:
                pid = self.consensus.propose(result.query, result.aggregated_value, "oracle_network")
                for sid in result.sources_used:
                    self.consensus.vote(pid, sid, result.aggregated_value)
                consensus_results.append(self.consensus.finalize(pid))

        return {
            "cycle": self.cycle_count,
            "queries_processed": len(queries),
            "results": len(results),
            "consensus_finalized": len(consensus_results),
            "online_oracles": len(self.registry.get_online()),
        }

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "registry": self.registry.get_report(),
            "aggregator": self.aggregator.get_report(),
            "reputation": self.reputation.get_report(),
            "bridge": self.bridge.get_report(),
            "consensus": self.consensus.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_on_instance: Optional[OracleNetwork] = None


def get_oracle_network() -> OracleNetwork:
    global _on_instance
    if _on_instance is None:
        _on_instance = OracleNetwork()
    return _on_instance


if __name__ == "__main__":
    on = OracleNetwork()
    print(f"OracleNetwork v{on.VERSION} initialized")
    print(f"Status: {json.dumps(on.get_status(), indent=2, default=str)}")
