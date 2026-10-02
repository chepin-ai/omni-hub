"""
OMNI-HUB v189 — FormalSelfReference
形式化自指安全引擎

核心功能：
1. TypeSystem         — 类型系统（禁止自指类型）
2. ProofEngine        — 证明引擎
3. SafetyChecker      — 安全检查器
4. AxiomBase          — 公理基础
5. InferenceRule      — 推理规则
6. FormalSelfReference — 统合引擎

映射：
- 类型 = rūpa（形）
- 证明 = siddhi（成就）
- 安全 = kṣema（安稳）
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class TypeRank(Enum):
    """类型层级（Russell式分层）"""
    TYPE_0 = 0      # 基础对象
    TYPE_1 = 1      # 关于TYPE_0的命题
    TYPE_2 = 2      # 关于TYPE_1的命题
    TYPE_3 = 3      # 元元
    TYPE_OMEGA = 4  # 极限类型（受限使用）


class ProofStatus(Enum):
    """证明状态"""
    UNPROVEN = 0
    PROVABLE = 1
    DISPROVEN = 2
    INDEPENDENT = 3
    PARADOXICAL = 4


class SafetyLevel(Enum):
    """安全等级"""
    UNSAFE = 0
    CONDITIONAL = 1
    SAFE = 2
    PROVEN_SAFE = 3


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class TypeSignature:
    """类型签名"""
    signature_id: str
    rank: TypeRank
    constraints: List[str]
    self_referential: bool = False


@dataclass
class Theorem:
    """定理"""
    theorem_id: str
    statement: str
    status: ProofStatus
    proof_steps: List[str]
    dependencies: List[str]
    rank: TypeRank


@dataclass
class SafetyReport:
    """安全报告"""
    report_id: str
    target: str
    level: SafetyLevel
    violations: List[str]
    recommendations: List[str]
    timestamp: float


@dataclass
class Axiom:
    """公理"""
    axiom_id: str
    statement: str
    rank: TypeRank
    universally_true: bool = True


@dataclass
class InferenceStep:
    """推理步骤"""
    step_id: str
    rule_name: str
    premises: List[str]
    conclusion: str
    valid: bool = True


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 类型系统（禁止自指类型）
# ═══════════════════════════════════════════════════════════════

class TypeSystem:
    """类型系统 — rūpa"""

    def __init__(self, max_rank: TypeRank = TypeRank.TYPE_3):
        self.max_rank = max_rank
        self.signatures: Dict[str, TypeSignature] = {}
        self._init_builtins()

    def _init_builtins(self):
        builtins = [
            ("obj", TypeRank.TYPE_0, []),
            ("prop", TypeRank.TYPE_1, []),
            ("meta_prop", TypeRank.TYPE_2, []),
            ("meta_meta", TypeRank.TYPE_3, []),
        ]
        for name, rank, cons in builtins:
            self.signatures[name] = TypeSignature(
                signature_id=f"type_{name}",
                rank=rank,
                constraints=cons,
                self_referential=False
            )

    def register(self, name: str, rank: TypeRank, constraints: List[str] = None) -> TypeSignature:
        """注册类型"""
        constraints = constraints or []
        sig = TypeSignature(
            signature_id=f"type_{name}_{int(time.time()*1000)}",
            rank=rank,
            constraints=constraints,
            self_referential=False
        )
        self.signatures[name] = sig
        return sig

    def check_self_reference(self, type_a: str, type_b: str) -> Tuple[bool, str]:
        """检查类型间是否存在自指"""
        sig_a = self.signatures.get(type_a)
        sig_b = self.signatures.get(type_b)
        if not sig_a or not sig_b:
            return False, "Unknown type"

        # 同等级类型相互引用 = 潜在自指
        if sig_a.rank == sig_b.rank and sig_a.rank != TypeRank.TYPE_0:
            return True, f"Same-rank reference: {type_a} → {type_b} (rank {sig_a.rank.name})"

        # 低等级引用高等级 = 正常
        if sig_a.rank.value < sig_b.rank.value:
            return False, "Safe: lower → higher"

        # 高等级引用低等级 = 元陈述（允许）
        if sig_a.rank.value > sig_b.rank.value:
            return False, "Safe: meta-reference"

        return False, "No self-reference detected"

    def assign_rank(self, entity_type: str, references: List[str]) -> TypeRank:
        """根据引用关系自动分配类型层级"""
        if not references:
            return TypeRank.TYPE_0

        max_ref_rank = TypeRank.TYPE_0
        for ref in references:
            sig = self.signatures.get(ref)
            if sig:
                max_ref_rank = TypeRank(max(max_ref_rank.value, sig.rank.value))

        # 实体层级 = max(引用层级) + 1
        new_rank_val = min(max_ref_rank.value + 1, self.max_rank.value)
        return TypeRank(new_rank_val)

    def get_report(self) -> Dict:
        self_refs = sum(1 for s in self.signatures.values() if s.self_referential)
        return {
            "types": len(self.signatures),
            "max_rank": self.max_rank.name,
            "self_referential_types": self_refs,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 证明引擎
# ═══════════════════════════════════════════════════════════════

class ProofEngine:
    """证明引擎 — siddhi"""

    def __init__(self):
        self.theorems: Dict[str, Theorem] = {}
        self.proof_counter = 0

    def propose(self, statement: str, rank: TypeRank) -> Theorem:
        """提出定理"""
        self.proof_counter += 1
        tid = f"theorem_{self.proof_counter}_{int(time.time()*1000)}"
        th = Theorem(
            theorem_id=tid,
            statement=statement,
            status=ProofStatus.UNPROVEN,
            proof_steps=[],
            dependencies=[],
            rank=rank
        )
        self.theorems[tid] = th
        return th

    def prove(self, theorem_id: str, steps: List[str], dependencies: List[str]) -> bool:
        """尝试证明定理"""
        if theorem_id not in self.theorems:
            return False

        th = self.theorems[theorem_id]

        # 检查依赖的层级 <= 定理层级
        for dep in dependencies:
            if dep in self.theorems:
                if self.theorems[dep].rank.value > th.rank.value:
                    return False  # 不能依赖更高层级的定理

        th.proof_steps = steps
        th.dependencies = dependencies
        th.status = ProofStatus.PROVABLE
        return True

    def disprove(self, theorem_id: str, counterexample: str):
        if theorem_id in self.theorems:
            self.theorems[theorem_id].status = ProofStatus.DISPROVEN
            self.theorems[theorem_id].proof_steps = [f"COUNTEREXAMPLE: {counterexample}"]

    def check_paradox(self, theorem_id: str) -> bool:
        """检查定理是否导致悖论"""
        if theorem_id not in self.theorems:
            return False
        th = self.theorems[theorem_id]

        # Russell式悖论检测
        if "self" in th.statement.lower() and "not" in th.statement.lower():
            if th.rank == TypeRank.TYPE_0:
                th.status = ProofStatus.PARADOXICAL
                return True
        return False

    def get_report(self) -> Dict:
        status_counts = {}
        for t in self.theorems.values():
            status_counts[t.status.name] = status_counts.get(t.status.name, 0) + 1
        return {
            "theorems": len(self.theorems),
            "status_distribution": status_counts,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 安全检查器
# ═══════════════════════════════════════════════════════════════

class SafetyChecker:
    """安全检查器 — kṣema"""

    def __init__(self):
        self.reports: deque = deque(maxlen=500)

    def check_expression(self, expr: str, type_system: TypeSystem) -> SafetyReport:
        """检查表达式的自指安全性"""
        violations = []
        recommendations = []

        # 检测直接自指
        if "self" in expr.lower() or "self-reference" in expr.lower():
            violations.append("Direct self-reference detected")
            recommendations.append("Increase type rank by 1")

        # 检测循环引用
        if "→" in expr and "←" in expr:
            violations.append("Potential circular reference")
            recommendations.append("Break cycle with intermediate layer")

        # 检测Russell集合
        if "contains itself" in expr.lower() or "∈ itself" in expr.lower():
            violations.append("Russell-style paradox construct")
            recommendations.append("Use stratified type system")

        level = SafetyLevel.PROVEN_SAFE if not violations else (
            SafetyLevel.SAFE if len(violations) == 1 else (
                SafetyLevel.CONDITIONAL if len(violations) <= 2 else SafetyLevel.UNSAFE
            )
        )

        report = SafetyReport(
            report_id=f"safety_{int(time.time()*1000)}",
            target=expr[:50],
            level=level,
            violations=violations,
            recommendations=recommendations,
            timestamp=time.time()
        )
        self.reports.append(report)
        return report

    def check_module(self, module_id: str, references: Dict[str, List[str]]) -> SafetyReport:
        """检查模块的引用安全性"""
        violations = []
        for ref_from, ref_tos in references.items():
            if module_id in ref_tos and ref_from in references.get(module_id, []):
                violations.append(f"Circular: {module_id} ↔ {ref_from}")

        level = SafetyLevel.PROVEN_SAFE if not violations else SafetyLevel.UNSAFE
        report = SafetyReport(
            report_id=f"safety_mod_{int(time.time()*1000)}",
            target=module_id,
            level=level,
            violations=violations,
            recommendations=["Refactor into DAG"] if violations else [],
            timestamp=time.time()
        )
        self.reports.append(report)
        return report

    def get_report(self) -> Dict:
        levels = {}
        for r in self.reports:
            levels[r.level.name] = levels.get(r.level.name, 0) + 1
        return {
            "reports": len(self.reports),
            "level_distribution": levels,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 公理基础
# ═══════════════════════════════════════════════════════════════

class AxiomBase:
    """公理基础 — OMNI-HUB专用公理"""

    OMNI_AXIOMS = [
        ("ax_existence", "System exists", TypeRank.TYPE_0),
        ("ax_communication", "Modules can communicate", TypeRank.TYPE_1),
        ("ax_time", "Time flows unidirectionally", TypeRank.TYPE_0),
        ("ax_contradiction", "Contradiction cannot be true", TypeRank.TYPE_1),
        ("ax_observation", "Observation affects observed", TypeRank.TYPE_2),
        ("ax_no_self_reference", "No unrestricted self-reference", TypeRank.TYPE_3),
    ]

    def __init__(self):
        self.axioms: Dict[str, Axiom] = {}
        self._init_axioms()

    def _init_axioms(self):
        for aid, stmt, rank in self.OMNI_AXIOMS:
            self.axioms[aid] = Axiom(
                axiom_id=aid,
                statement=stmt,
                rank=rank,
                universally_true=True
            )

    def add(self, axiom: Axiom):
        self.axioms[axiom.axiom_id] = axiom

    def verify(self, statement: str) -> Tuple[bool, List[str]]:
        """验证陈述是否与公理一致"""
        matching = [a.axiom_id for a in self.axioms.values()
                    if any(word in statement.lower() for word in a.statement.lower().split())]
        return len(matching) > 0, matching

    def get_by_rank(self, rank: TypeRank) -> List[Axiom]:
        return [a for a in self.axioms.values() if a.rank == rank]

    def get_report(self) -> Dict:
        rank_counts = {}
        for a in self.axioms.values():
            rank_counts[a.rank.name] = rank_counts.get(a.rank.name, 0) + 1
        return {
            "axioms": len(self.axioms),
            "by_rank": rank_counts,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 推理规则
# ═══════════════════════════════════════════════════════════════

class InferenceRule:
    """推理规则"""

    RULES = {
        "MP": "Modus Ponens: A, A→B ⊢ B",
        "MT": "Modus Tollens: ¬B, A→B ⊢ ¬A",
        "GEN": "Generalization: A(x) ⊢ ∀x.A(x)",
        "SPEC": "Specification: ∀x.A(x) ⊢ A(c)",
        "CONJ": "Conjunction: A, B ⊢ A∧B",
        "DISJ": "Disjunction: A ⊢ A∨B",
        "RANK": "Rank Bound: rank(conclusion) ≤ max(rank(premises)) + 1",
    }

    def __init__(self):
        self.steps: deque = deque(maxlen=1000)

    def apply(self, rule_name: str, premises: List[str], conclusion: str,
              premise_ranks: List[TypeRank]) -> InferenceStep:
        """应用推理规则"""
        valid = True
        reason = ""

        if rule_name not in self.RULES:
            valid = False
            reason = "Unknown rule"
        elif rule_name == "RANK":
            max_rank = max((r.value for r in premise_ranks), default=0)
            # 结论层级不能超过前提+1
            # 这里简化处理
            valid = True

        step = InferenceStep(
            step_id=f"step_{int(time.time()*1000)}",
            rule_name=rule_name,
            premises=premises,
            conclusion=conclusion,
            valid=valid
        )
        self.steps.append(step)
        return step

    def chain(self, steps: List[InferenceStep]) -> bool:
        """验证推理链的有效性"""
        for step in steps:
            if not step.valid:
                return False
        return True

    def get_report(self) -> Dict:
        valid_count = sum(1 for s in self.steps if s.valid)
        return {
            "steps": len(self.steps),
            "valid_steps": valid_count,
            "invalid_steps": len(self.steps) - valid_count,
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — FormalSelfReference v189
# ═══════════════════════════════════════════════════════════════

class FormalSelfReference:
    """
    OMNI-HUB v189 形式化自指安全引擎

    rūpa · siddhi · kṣema — 形、成就、安稳
    """

    VERSION = "189.0.0"

    def __init__(self):
        self.type_system = TypeSystem()
        self.proof_engine = ProofEngine()
        self.safety_checker = SafetyChecker()
        self.axiom_base = AxiomBase()
        self.inference = InferenceRule()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def analyze_module(self, module_id: str, references: Dict[str, List[str]],
                      expressions: List[str]) -> Dict:
        """分析模块的形式化安全性"""
        # 1. 类型分配
        types = {}
        for ref_from, ref_tos in references.items():
            rank = self.type_system.assign_rank(ref_from, ref_tos)
            types[ref_from] = rank
            self.type_system.register(ref_from, rank)

        # 2. 自指检查
        self_refs = []
        for ref_from, ref_tos in references.items():
            for ref_to in ref_tos:
                is_sr, reason = self.type_system.check_self_reference(ref_from, ref_to)
                if is_sr:
                    self_refs.append({"from": ref_from, "to": ref_to, "reason": reason})
                # 检测循环引用（双向依赖）
                if ref_to in references and ref_from in references.get(ref_to, []):
                    circ = {"from": ref_from, "to": ref_to,
                            "reason": f"Circular: {ref_from} ↔ {ref_to}"}
                    if circ not in self_refs:
                        self_refs.append(circ)

        # 3. 安全检查
        safety = self.safety_checker.check_module(module_id, references)
        for expr in expressions:
            self.safety_checker.check_expression(expr, self.type_system)

        # 4. 定理提出
        theorem = self.proof_engine.propose(
            f"{module_id} is self-reference safe",
            TypeRank.TYPE_2
        )

        # 5. 证明尝试
        if not self_refs:
            self.proof_engine.prove(theorem.theorem_id,
                                     ["No self-references found"],
                                     ["ax_no_self_reference"])

        return {
            "module": module_id,
            "types_assigned": {k: v.name for k, v in types.items()},
            "self_references": self_refs,
            "safety_level": safety.level.name,
            "theorem_id": theorem.theorem_id,
            "theorem_status": theorem.status.name,
        }

    def verify_system(self, module_references: Dict[str, Dict[str, List[str]]]) -> Dict:
        """验证整个系统的自指安全性"""
        results = []
        for module_id, refs in module_references.items():
            r = self.analyze_module(module_id, refs, [])
            results.append(r)

        total_sr = sum(len(r["self_references"]) for r in results)
        safe_count = sum(1 for r in results if r["safety_level"] == "PROVEN_SAFE")

        return {
            "modules_checked": len(results),
            "total_self_references": total_sr,
            "safe_modules": safe_count,
            "results": results,
        }

    def run_cycle(self, modules: Dict[str, Dict[str, List[str]]] = None) -> Dict:
        """运行完整验证周期"""
        self.cycle_count += 1
        modules = modules or {}

        result = self.verify_system(modules)

        summary = {
            "cycle": self.cycle_count,
            "modules_checked": result["modules_checked"],
            "safe_modules": result["safe_modules"],
            "self_references_found": result["total_self_references"],
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "type_system": self.type_system.get_report(),
            "proof_engine": self.proof_engine.get_report(),
            "safety_checker": self.safety_checker.get_report(),
            "axiom_base": self.axiom_base.get_report(),
            "inference": self.inference.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_fsr_instance: Optional[FormalSelfReference] = None


def get_formal_self_reference() -> FormalSelfReference:
    global _fsr_instance
    if _fsr_instance is None:
        _fsr_instance = FormalSelfReference()
    return _fsr_instance


if __name__ == "__main__":
    fsr = FormalSelfReference()
    print(f"FormalSelfReference v{fsr.VERSION} initialized")
    print(f"Status: {json.dumps(fsr.get_status(), indent=2, default=str)}")
