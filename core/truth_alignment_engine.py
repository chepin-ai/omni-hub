"""
OMNI-HUB v186 — TruthAlignmentEngine
真值对齐引擎

核心功能：
1. CrossLineFactChecker      — 跨线事实一致性检查
2. MultiSourceValidator      — 多源数据交叉验证
3. TruthConsensusProtocol    — 真值共识协议
4. EpistemicDriftDetector    — 认知漂移检测
5. RealityAnchorManager      — 现实锚点管理
6. TruthAlignmentEngine      — 统合引擎

映射：
- 真值 = satya（谛/真实）
- 共识 = saṅgha-vinaya（僧团律）
- 认知漂移 = māyā-viparyaya（幻颠倒）
- 现实锚点 = dharmadhātu（法界）
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class TruthStatus(Enum):
    """真值状态"""
    UNVERIFIED = 0      # 未验证
    PROVISIONAL = 1     # 暂定
    CONFIRMED = 2       # 已确认
    CONSENSUS = 3       # 共识级
    AXIOMATIC = 4       # 公理级（不可动摇）


class SourceReliability(Enum):
    """源可靠性"""
    UNTRUSTED = 0       # 不可信
    LOW = 1             # 低
    MEDIUM = 2          # 中
    HIGH = 3            # 高
    ORACLE = 4          # 预言机级


class DriftType(Enum):
    """漂移类型"""
    NONE = 0
    CONTRADICTION = 1   # 矛盾
    DECAY = 2           # 衰减
    INJECTION = 3       # 注入
    HALLUCINATION = 4   # 幻觉


ALLIANCE_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
    "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"
]


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class FactClaim:
    """事实声称"""
    claim_id: str
    statement: str
    source_line: str
    source_module: str
    timestamp: float
    hash_digest: str = ""
    status: TruthStatus = TruthStatus.UNVERIFIED
    confirmations: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.hash_digest:
            self.hash_digest = hashlib.sha256(
                f"{self.statement}:{self.source_line}:{self.timestamp}".encode()
            ).hexdigest()[:16]


@dataclass
class SourceRecord:
    """源记录"""
    source_id: str
    line_id: str
    reliability: SourceReliability
    claim_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    last_updated: float = field(default_factory=time.time)


@dataclass
class ValidationResult:
    """验证结果"""
    claim_id: str
    is_valid: bool
    confidence: float
    supporting_sources: List[str]
    conflicting_sources: List[str]
    method: str
    timestamp: float


@dataclass
class EpistemicDrift:
    """认知漂移"""
    drift_id: str
    drift_type: DriftType
    affected_claims: List[str]
    severity: float
    description: str
    timestamp: float


@dataclass
class RealityAnchor:
    """现实锚点"""
    anchor_id: str
    proposition: str
    truth_status: TruthStatus
    established_at: float
    confirmed_by: List[str]
    revision_count: int = 0


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 跨线事实检查器
# ═══════════════════════════════════════════════════════════════

class CrossLineFactChecker:
    """
    跨线事实一致性检查
    比较不同线对同一事实的声称
    """

    def __init__(self):
        self.claims: Dict[str, FactClaim] = {}
        self.claim_index: Dict[str, List[str]] = {}  # statement_hash -> claim_ids
        self._claim_counter = 0

    def __init__(self):
        self.claims: Dict[str, FactClaim] = {}
        self.claim_index: Dict[str, List[str]] = {}  # statement_hash -> claim_ids
        self._claim_counter = 0

    def submit_claim(self, statement: str, source_line: str, source_module: str,
                    evidence: Dict = None) -> FactClaim:
        """提交事实声称"""
        self._claim_counter += 1
        cid = f"claim_{int(time.time()*1000)}_{self._claim_counter}_{hashlib.sha256(f'{statement}:{source_line}'.encode()).hexdigest()[:8]}"
        claim = FactClaim(
            claim_id=cid,
            statement=statement,
            source_line=source_line,
            source_module=source_module,
            timestamp=time.time(),
            evidence=evidence or {}
        )
        self.claims[cid] = claim

        # 索引
        stmt_hash = hashlib.sha256(statement.encode()).hexdigest()[:16]
        if stmt_hash not in self.claim_index:
            self.claim_index[stmt_hash] = []
        self.claim_index[stmt_hash].append(cid)

        return claim

    def check_consistency(self, claim_id: str) -> Dict:
        """检查某声称与其他线的一致性"""
        if claim_id not in self.claims:
            return {"error": "claim_not_found"}

        claim = self.claims[claim_id]
        stmt_hash = hashlib.sha256(claim.statement.encode()).hexdigest()[:16]
        siblings = self.claim_index.get(stmt_hash, [])

        confirmations = []
        contradictions = []

        for sid in siblings:
            if sid == claim_id:
                continue
            other = self.claims[sid]
            # 简单一致性：来源不同即视为确认（简化版）
            if other.source_line != claim.source_line:
                confirmations.append(other.source_line)
            # 检查证据矛盾
            if evidence_contradicts(claim.evidence, other.evidence):
                contradictions.append(other.source_line)

        claim.confirmations = confirmations
        claim.contradictions = contradictions

        # 更新状态
        if contradictions:
            claim.status = TruthStatus.UNVERIFIED
        elif len(confirmations) >= 3:
            claim.status = TruthStatus.CONSENSUS
        elif len(confirmations) >= 1:
            claim.status = TruthStatus.CONFIRMED
        else:
            claim.status = TruthStatus.PROVISIONAL

        return {
            "claim_id": claim_id,
            "confirmations": len(confirmations),
            "contradictions": len(contradictions),
            "status": claim.status.name,
            "cross_line_coverage": len(set(confirmations + [claim.source_line])) / len(ALLIANCE_LINES),
        }

    def get_claims_by_line(self, line_id: str) -> List[FactClaim]:
        return [c for c in self.claims.values() if c.source_line == line_id]

    def get_report(self) -> Dict:
        status_counts = {}
        for c in self.claims.values():
            status_counts[c.status.name] = status_counts.get(c.status.name, 0) + 1
        return {
            "total_claims": len(self.claims),
            "status_distribution": status_counts,
            "unique_statements": len(self.claim_index),
        }


def evidence_contradicts(ev1: Dict, ev2: Dict) -> bool:
    """简单证据矛盾检测"""
    if not ev1 or not ev2:
        return False
    # 检查数值矛盾
    for key in set(ev1.keys()) & set(ev2.keys()):
        v1, v2 = ev1[key], ev2[key]
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            if abs(v1 - v2) > 0.5 * max(abs(v1), abs(v2), 0.001):
                return True
    return False


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 多源验证器
# ═══════════════════════════════════════════════════════════════

class MultiSourceValidator:
    """
    多源数据交叉验证
    加权投票机制
    """

    def __init__(self):
        self.sources: Dict[str, SourceRecord] = {}
        self.validation_history: deque = deque(maxlen=1000)

    def register_source(self, source_id: str, line_id: str,
                       reliability: SourceReliability = SourceReliability.MEDIUM):
        """注册数据源"""
        self.sources[source_id] = SourceRecord(
            source_id=source_id,
            line_id=line_id,
            reliability=reliability
        )

    def validate(self, claim: FactClaim, reference_values: Dict[str, Any] = None) -> ValidationResult:
        """验证声称"""
        supporting = []
        conflicting = []
        total_weight = 0
        support_weight = 0

        # 检查所有已知源
        for src_id, src in self.sources.items():
            if src.line_id == claim.source_line:
                continue  # 跳过自验证

            # 模拟验证：如果有参考值则比较
            if reference_values and claim.statement in reference_values:
                expected = reference_values[claim.statement]
                # 简化：如果声明包含预期值则为支持
                if str(expected) in claim.statement or claim.statement in str(expected):
                    supporting.append(src_id)
                    support_weight += src.reliability.value
                else:
                    conflicting.append(src_id)
                total_weight += src.reliability.value
            else:
                # 无参考值时，基于源声誉投票
                if src.reliability.value >= SourceReliability.HIGH.value:
                    supporting.append(src_id)
                    support_weight += src.reliability.value
                    total_weight += src.reliability.value

        confidence = support_weight / max(1, total_weight) if total_weight > 0 else 0.0
        is_valid = confidence >= 0.6

        result = ValidationResult(
            claim_id=claim.claim_id,
            is_valid=is_valid,
            confidence=confidence,
            supporting_sources=supporting,
            conflicting_sources=conflicting,
            method="weighted_vote",
            timestamp=time.time()
        )
        self.validation_history.append(result)

        # 更新源记录
        for src_id in supporting + conflicting:
            if src_id in self.sources:
                self.sources[src_id].claim_count += 1
                if is_valid:
                    self.sources[src_id].true_positives += 1
                else:
                    self.sources[src_id].false_positives += 1

        return result

    def get_source_reliability(self, source_id: str) -> float:
        """计算源的实际可靠性"""
        src = self.sources.get(source_id)
        if not src or src.claim_count == 0:
            return 0.5
        return src.true_positives / max(1, src.claim_count)

    def get_report(self) -> Dict:
        return {
            "registered_sources": len(self.sources),
            "total_validations": len(self.validation_history),
            "source_reliabilities": {
                sid: self.get_source_reliability(sid)
                for sid in self.sources
            },
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 真值共识协议
# ═══════════════════════════════════════════════════════════════

class TruthConsensusProtocol:
    """
    真值共识协议
    基于拜占庭容错的简化共识
    """

    def __init__(self, threshold: float = 2.0 / 3.0):
        self.threshold = threshold
        self.consensus_log: deque = deque(maxlen=500)
        self.votes: Dict[str, Dict[str, Any]] = {}

    def propose_truth(self, proposition: str, proposer: str) -> str:
        """提出真值提案"""
        pid = f"truth_{hashlib.sha256(proposition.encode()).hexdigest()[:12]}"
        self.votes[pid] = {
            "proposition": proposition,
            "proposer": proposer,
            "votes": {},
            "status": "pending",
            "timestamp": time.time(),
        }
        return pid

    def vote(self, proposition_id: str, voter: str, accept: bool,
            weight: float = 1.0, signature: str = "") -> Dict:
        """投票"""
        if proposition_id not in self.votes:
            return {"error": "proposition_not_found"}

        self.votes[proposition_id]["votes"][voter] = {
            "accept": accept,
            "weight": weight,
            "signature": signature,
            "time": time.time(),
        }
        return self.votes[proposition_id]

    def tally(self, proposition_id: str) -> Dict:
        """计票"""
        if proposition_id not in self.votes:
            return {"error": "proposition_not_found"}

        prop = self.votes[proposition_id]
        votes = prop["votes"]
        if not votes:
            return {"consensus": False, "reason": "no_votes"}

        total_weight = sum(v["weight"] for v in votes.values())
        accept_weight = sum(v["weight"] for v in votes.values() if v["accept"])

        # 拜占庭容错：需要2/3多数
        consensus = (accept_weight / total_weight) >= self.threshold if total_weight > 0 else False

        result = {
            "proposition_id": proposition_id,
            "consensus": consensus,
            "accept_ratio": accept_weight / total_weight if total_weight > 0 else 0,
            "threshold": self.threshold,
            "total_votes": len(votes),
            "total_weight": total_weight,
        }

        prop["status"] = "accepted" if consensus else "rejected"
        self.consensus_log.append(result)
        return result

    def get_report(self) -> Dict:
        accepted = sum(1 for r in self.consensus_log if r.get("consensus"))
        total = len(self.consensus_log)
        return {
            "total_propositions": len(self.votes),
            "resolved": total,
            "accepted": accepted,
            "rejected": total - accepted,
            "consensus_rate": accepted / max(1, total),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 认知漂移检测
# ═══════════════════════════════════════════════════════════════

class EpistemicDriftDetector:
    """
    认知漂移检测
    māyā-viparyaya — 检测事实的幻颠倒
    """

    def __init__(self):
        self.drifts: deque = deque(maxlen=500)
        self.claim_history: Dict[str, deque] = {}  # claim_id -> history
        self.sensitivity = 0.3

    def record_claim_state(self, claim: FactClaim):
        """记录声称状态"""
        if claim.claim_id not in self.claim_history:
            self.claim_history[claim.claim_id] = deque(maxlen=100)
        self.claim_history[claim.claim_id].append({
            "time": time.time(),
            "status": claim.status,
            "confirmations": len(claim.confirmations),
            "contradictions": len(claim.contradictions),
        })

    def detect(self) -> List[EpistemicDrift]:
        """检测漂移"""
        detected = []

        for cid, history in self.claim_history.items():
            if len(history) < 3:
                continue

            recent = list(history)[-5:]
            if len(recent) < 3:
                continue

            # 检测矛盾增加
            contradictions_trend = [h["contradictions"] for h in recent]
            if contradictions_trend[-1] > contradictions_trend[0] and contradictions_trend[-1] > 0:
                detected.append(EpistemicDrift(
                    drift_id=f"drift_{cid}_{int(time.time())}",
                    drift_type=DriftType.CONTRADICTION,
                    affected_claims=[cid],
                    severity=min(1.0, contradictions_trend[-1] * 0.2),
                    description="Increasing contradictions detected",
                    timestamp=time.time()
                ))

            # 检测状态衰减
            status_values = [h["status"].value for h in recent]
            if status_values[-1] < status_values[0]:
                detected.append(EpistemicDrift(
                    drift_id=f"drift_decay_{cid}_{int(time.time())}",
                    drift_type=DriftType.DECAY,
                    affected_claims=[cid],
                    severity=(status_values[0] - status_values[-1]) / 4.0,
                    description="Truth status decay",
                    timestamp=time.time()
                ))

        self.drifts.extend(detected)
        return detected

    def get_report(self) -> Dict:
        type_counts = {}
        for d in self.drifts:
            type_counts[d.drift_type.name] = type_counts.get(d.drift_type.name, 0) + 1
        return {
            "total_drifts": len(self.drifts),
            "type_distribution": type_counts,
            "monitored_claims": len(self.claim_history),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 现实锚点管理
# ═══════════════════════════════════════════════════════════════

class RealityAnchorManager:
    """
    现实锚点管理
    dharmadhātu — 不可动摇的基础命题
    """

    DEFAULT_ANCHORS = [
        "系统存在",
        "时间单向流逝",
        "矛盾不可同时为真",
        "观测影响被观测",
        "模块间可通信",
    ]

    def __init__(self):
        self.anchors: Dict[str, RealityAnchor] = {}
        self._init_default_anchors()

    def _init_default_anchors(self):
        """初始化默认锚点"""
        for prop in self.DEFAULT_ANCHORS:
            aid = f"anchor_{hashlib.sha256(prop.encode()).hexdigest()[:8]}"
            self.anchors[aid] = RealityAnchor(
                anchor_id=aid,
                proposition=prop,
                truth_status=TruthStatus.AXIOMATIC,
                established_at=time.time(),
                confirmed_by=["system"],
            )

    def add_anchor(self, proposition: str, confirmed_by: List[str]) -> RealityAnchor:
        """添加新锚点"""
        aid = f"anchor_{hashlib.sha256(proposition.encode()).hexdigest()[:8]}"
        anchor = RealityAnchor(
            anchor_id=aid,
            proposition=proposition,
            truth_status=TruthStatus.CONSENSUS,
            established_at=time.time(),
            confirmed_by=confirmed_by,
        )
        self.anchors[aid] = anchor
        return anchor

    def verify_against_anchors(self, statement: str) -> Tuple[bool, List[str]]:
        """验证命题是否违反锚点"""
        violations = []
        for anchor in self.anchors.values():
            # 简化检查：如果statement与锚点命题矛盾
            if contradicts_anchor(statement, anchor.proposition):
                violations.append(anchor.anchor_id)
        return len(violations) == 0, violations

    def revise_anchor(self, anchor_id: str, new_proposition: str, reason: str):
        """修订锚点（极慎重）"""
        if anchor_id not in self.anchors:
            return None
        anchor = self.anchors[anchor_id]
        anchor.revision_count += 1
        anchor.proposition = new_proposition
        anchor.truth_status = TruthStatus.PROVISIONAL  # 降级为暂定
        return anchor

    def get_report(self) -> Dict:
        status_counts = {}
        for a in self.anchors.values():
            status_counts[a.truth_status.name] = status_counts.get(a.truth_status.name, 0) + 1
        return {
            "total_anchors": len(self.anchors),
            "status_distribution": status_counts,
            "total_revisions": sum(a.revision_count for a in self.anchors.values()),
            "anchors": [{"id": a.anchor_id, "prop": a.proposition, "status": a.truth_status.name}
                       for a in self.anchors.values()],
        }


def contradicts_anchor(statement: str, anchor: str) -> bool:
    """简单矛盾检测"""
    negations = ["不", "非", "not", "no ", "never", "false", "无", "没"]
    stmt_lower = statement.lower()
    anchor_lower = anchor.lower()
    for neg in negations:
        if neg in stmt_lower:
            simplified = stmt_lower.replace(neg, "").replace(" ", "")
            simplified_anchor = anchor_lower.replace(" ", "")
            if simplified == simplified_anchor or simplified in simplified_anchor or simplified_anchor in simplified:
                return True
    return False


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — TruthAlignmentEngine v186
# ═══════════════════════════════════════════════════════════════

class TruthAlignmentEngine:
    """
    OMNI-HUB v186 真值对齐引擎

    satya — 谛/真实
    """

    VERSION = "186.0.0"

    def __init__(self):
        self.fact_checker = CrossLineFactChecker()
        self.validator = MultiSourceValidator()
        self.consensus = TruthConsensusProtocol()
        self.drift_detector = EpistemicDriftDetector()
        self.anchor_manager = RealityAnchorManager()

        # 注册所有线为数据源
        for line in ALLIANCE_LINES:
            self.validator.register_source(f"src_{line}", line, SourceReliability.MEDIUM)

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def submit_claim(self, statement: str, source_line: str, source_module: str,
                    evidence: Dict = None) -> FactClaim:
        """提交事实声称"""
        # 先检查是否违反锚点
        valid, violations = self.anchor_manager.verify_against_anchors(statement)
        if not valid:
            self.event_log.append({
                "type": "anchor_violation",
                "statement": statement,
                "violations": violations,
                "time": time.time()
            })

        claim = self.fact_checker.submit_claim(statement, source_line, source_module, evidence)
        return claim

    def run_cycle(self, line_states: Dict[str, Dict] = None) -> Dict:
        """运行完整真值对齐周期"""
        self.cycle_count += 1
        line_states = line_states or {}

        # 1. 从各线收集声称
        new_claims = []
        for line_id, state in line_states.items():
            if isinstance(state, dict):
                claims_data = state.get("claims", [])
                for cd in claims_data:
                    claim = self.submit_claim(
                        statement=cd.get("statement", ""),
                        source_line=line_id,
                        source_module=cd.get("module", "unknown"),
                        evidence=cd.get("evidence", {})
                    )
                    new_claims.append(claim)

        # 2. 跨线一致性检查
        consistency_results = []
        for claim in new_claims:
            result = self.fact_checker.check_consistency(claim.claim_id)
            consistency_results.append(result)

        # 3. 多源验证
        validation_results = []
        for claim in new_claims:
            if claim.status.value >= TruthStatus.PROVISIONAL.value:
                vr = self.validator.validate(claim)
                validation_results.append(vr)

        # 4. 认知漂移检测
        for claim in new_claims:
            self.drift_detector.record_claim_state(claim)
        drifts = self.drift_detector.detect()

        # 5. 真值共识（对高价值声称）
        consensus_results = []
        for claim in new_claims:
            if claim.status.value >= TruthStatus.CONFIRMED.value:
                pid = self.consensus.propose_truth(claim.statement, claim.source_line)
                # 自动收集确认作为投票
                for confirmer in claim.confirmations[:5]:
                    self.consensus.vote(pid, confirmer, True, weight=1.0)
                result = self.consensus.tally(pid)
                consensus_results.append(result)

        # 6. 结果
        confirmed_count = sum(1 for c in new_claims if c.status.value >= TruthStatus.CONFIRMED.value)
        consensus_count = sum(1 for c in new_claims if c.status == TruthStatus.CONSENSUS)

        result = {
            "cycle": self.cycle_count,
            "claims_processed": len(new_claims),
            "confirmed": confirmed_count,
            "consensus": consensus_count,
            "drifts_detected": len(drifts),
            "validations": len(validation_results),
            "consensus_votes": len(consensus_results),
            "anchor_violations": sum(1 for e in self.event_log
                                      if isinstance(e, dict) and e.get("type") == "anchor_violation"),
        }

        self.event_log.append(result)
        return result

    def get_truth_status(self, statement: str) -> Dict:
        """查询某命题的真值状态"""
        stmt_hash = hashlib.sha256(statement.encode()).hexdigest()[:16]
        cids = self.fact_checker.claim_index.get(stmt_hash, [])
        if not cids:
            return {"status": "unknown", "confidence": 0.0}

        claims = [self.fact_checker.claims[cid] for cid in cids]
        best = max(claims, key=lambda c: c.status.value)
        return {
            "status": best.status.name,
            "confidence": len(best.confirmations) / max(1, len(ALLIANCE_LINES)),
            "sources": list(set(c.source_line for c in claims)),
            "confirmations": len(best.confirmations),
            "contradictions": len(best.contradictions),
        }

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "fact_checker": self.fact_checker.get_report(),
            "validator": self.validator.get_report(),
            "consensus": self.consensus.get_report(),
            "drift_detector": self.drift_detector.get_report(),
            "anchor_manager": self.anchor_manager.get_report(),
            "event_log_size": len(self.event_log),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_tae_instance: Optional[TruthAlignmentEngine] = None


def get_truth_alignment_engine() -> TruthAlignmentEngine:
    global _tae_instance
    if _tae_instance is None:
        _tae_instance = TruthAlignmentEngine()
    return _tae_instance


if __name__ == "__main__":
    tae = TruthAlignmentEngine()
    print(f"TruthAlignmentEngine v{tae.VERSION} initialized")
    print(f"Status: {json.dumps(tae.get_status(), indent=2, default=str)}")
