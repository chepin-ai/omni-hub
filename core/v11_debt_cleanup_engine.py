#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v11.0 — Debt Cleanup Engine (债务清理体系化引擎)
===============================================================
体系化清理三类债务：
  1. 理论债务 (Theoretical Debt) — 猜想/定理/证明依赖DAG
  2. 技术债务 (Technical Debt)   — 代码质量/静态分析/重构
  3. 工程债务 (Engineering Debt) — 架构/文档/测试/版本一致性

核心能力：
  - 自动审计债务并建立优先级DAG
  - 自动分配清理任务
  - 跟踪清理进度
  - 验证清理结果
  - Lean形式化证明器接口兼容

版本: 11.0.0
日期: 2026-09-17
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

# =============================================================================
# Compatibility import for v11_standards.py
# =============================================================================
try:
    from v11_standards import (
        OMNIHUBException,
        OMNIHUBTheoreticalError,
        OMNIHUBTechnicalError,
        OMNIHUBEngineeringError,
        VersionInfo,
        V11_VERSION,
        get_logger,
    )
except ImportError:
    # Fallback minimal definitions for standalone execution
    class OMNIHUBException(Exception):
        def __init__(self, message: str, error_code: str = "OMNI-000", context: Optional[Dict[str, Any]] = None) -> None:
            super().__init__(message)
            self.error_code = error_code
            self.context = context or {}

    class OMNIHUBTheoreticalError(OMNIHUBException):
        pass

    class OMNIHUBTechnicalError(OMNIHUBException):
        pass

    class OMNIHUBEngineeringError(OMNIHUBException):
        pass

    class VersionInfo:
        def __init__(self, major: int, minor: int, patch: int, stage: str = "stable") -> None:
            self.major, self.minor, self.patch, self.stage = major, minor, patch, stage
        def __str__(self) -> str:
            return f"{self.major}.{self.minor}.{self.patch}-{self.stage}"
        def __eq__(self, other: object) -> bool:
            if not isinstance(other, VersionInfo):
                return NotImplemented
            return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    V11_VERSION = VersionInfo(11, 0, 0, "stable")

    def get_logger(name: str) -> Any:
        import logging
        return logging.getLogger("OMNI-HUB." + name)


logger = get_logger("debt_cleanup_engine")

# =============================================================================
# 1. Debt Severity & Type Enums
# =============================================================================

class DebtType(Enum):
    THEORETICAL = "theoretical"
    TECHNICAL = "technical"
    ENGINEERING = "engineering"


class DebtSeverity(Enum):
    CRITICAL = "critical"    # 阻塞发布
    HIGH = "high"            # 必须修复
    MEDIUM = "medium"        # 应该修复
    LOW = "low"              # 可以延后

    @classmethod
    def from_string(cls, s: str) -> "DebtSeverity":
        mapping = {
            "critical": cls.CRITICAL,
            "high": cls.HIGH,
            "medium": cls.MEDIUM,
            "low": cls.LOW,
        }
        return mapping.get(s.lower(), cls.LOW)

    def numeric(self) -> int:
        return {self.CRITICAL: 4, self.HIGH: 3, self.MEDIUM: 2, self.LOW: 1}[self]


class DebtStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    WONTFIX = "wontfix"


# =============================================================================
# 2. DebtItem — 债务项数据结构
# =============================================================================

@dataclass
class DebtItem:
    """统一债务项 —— 三类债务的通用表示"""

    id: str                           # 全局唯一标识: "T-{type}-{hash}"
    debt_type: DebtType               # 债务类型
    severity: DebtSeverity            # 严重程度
    description: str                  # 描述
    file_path: Optional[str] = None   # 关联文件
    line_number: Optional[int] = None # 关联行号

    # 依赖DAG
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他债务项id

    # 验证
    verification_method: str = ""     # 如何验证已清理
    verification_result: Optional[bool] = None  # 验证结果

    # 工作量估计 (人时)
    estimated_effort: float = 0.0     # 估计工作量(小时)

    # Lean形式化
    lean_formalizable: bool = False   # 是否可用Lean形式化
    lean_skeleton: Optional[str] = None  # Lean证明骨架

    # 元数据
    status: DebtStatus = field(default=DebtStatus.OPEN)
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    aging_days: float = 0.0           # 债务龄(天)
    assigned_to: Optional[str] = None # 分配给谁
    tags: List[str] = field(default_factory=list)
    impact_score: float = 0.0         # 影响力分数(动态计算)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        d = asdict(self)
        d["debt_type"] = self.debt_type.value
        d["severity"] = self.severity.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebtItem":
        """从字典反序列化"""
        data = dict(data)
        data["debt_type"] = DebtType(data.get("debt_type", "technical"))
        data["severity"] = DebtSeverity.from_string(data.get("severity", "low"))
        data["status"] = DebtStatus(data.get("status", "open"))
        # Remove extra keys not in dataclass
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**data)

    def weight(self) -> float:
        """债务权重 = 严重度 x 龄化因子"""
        aging_factor = 1.0 + self.aging_days / 30.0  # 每月增长10%
        return self.severity.numeric() * aging_factor

    def is_blocked(self, resolved_ids: Set[str]) -> bool:
        """检查是否被未解决的依赖阻塞"""
        return any(dep not in resolved_ids for dep in self.dependencies)

    def mark_resolved(self, verified: bool = True) -> None:
        """标记为已解决"""
        self.status = DebtStatus.RESOLVED
        self.resolved_at = time.time()
        self.verification_result = verified

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DebtItem):
            return NotImplemented
        return self.id == other.id


# =============================================================================
# 3. DAG — 通用有向无环图（用于依赖管理）
# =============================================================================

T = TypeVar("T")


class DAG(Generic[T]):
    """通用有向无环图 —— 支持拓扑排序、影响力传播"""

    def __init__(self) -> None:
        self.nodes: Dict[str, T] = {}
        self.edges: Dict[str, List[str]] = defaultdict(list)      # node -> children
        self.reverse_edges: Dict[str, List[str]] = defaultdict(list)  # node -> parents

    def add_node(self, node_id: str, value: T) -> None:
        self.nodes[node_id] = value

    def add_edge(self, from_id: str, to_id: str) -> None:
        """添加依赖边: from_id 依赖 to_id (to_id must be done before from_id)"""
        if from_id not in self.nodes or to_id not in self.nodes:
            raise OMNIHUBException(f"Cannot add edge: missing node {from_id} or {to_id}")
        if to_id not in self.edges[from_id]:
            self.edges[from_id].append(to_id)
            self.reverse_edges[to_id].append(from_id)
        self._check_cycle()

    def _check_cycle(self) -> None:
        """检测环（DFS）"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {nid: WHITE for nid in self.nodes}

        def dfs(nid: str) -> None:
            color[nid] = GRAY
            for child in self.edges[nid]:
                if color[child] == GRAY:
                    raise OMNIHUBTheoreticalError(
                        f"Cycle detected in dependency graph at {nid} -> {child}",
                        error_code="OMNI-DAG-001"
                    )
                if color[child] == WHITE:
                    dfs(child)
            color[nid] = BLACK

        for nid in self.nodes:
            if color[nid] == WHITE:
                dfs(nid)

    def topological_sort(self) -> List[str]:
        """Kahn算法拓扑排序"""
        in_degree = {nid: 0 for nid in self.nodes}
        for nid, children in self.edges.items():
            for child in children:
                in_degree[child] = in_degree.get(child, 0) + 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        result: List[str] = []

        while queue:
            nid = queue.popleft()
            result.append(nid)
            for child in self.edges[nid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(result) != len(self.nodes):
            raise OMNIHUBTheoreticalError(
                "Topological sort failed: graph contains cycles",
                error_code="OMNI-DAG-002"
            )
        return result

    def compute_impact_scores(self) -> Dict[str, float]:
        """
        影响力传播计算：
        节点的impact_score = 1 + sum(children impact * 0.5)
        反向传播：影响越多下游节点的上游节点，分数越高
        """
        scores: Dict[str, float] = {nid: 1.0 for nid in self.nodes}
        order = self.topological_sort()

        # 正向传播（从叶子到根）
        for nid in reversed(order):
            for child in self.edges[nid]:
                scores[nid] += scores[child] * 0.5

        # 反向传播（从根到叶子，累计上游影响）
        for nid in order:
            for parent in self.reverse_edges[nid]:
                scores[nid] += scores[parent] * 0.3

        return scores

    def get_blocked_nodes(self, completed: Set[str]) -> Set[str]:
        """获取被阻塞的节点"""
        blocked = set()
        for nid in self.nodes:
            if nid in completed:
                continue
            for dep in self.edges[nid]:
                if dep not in completed:
                    blocked.add(nid)
                    break
        return blocked

    def get_ready_nodes(self, completed: Set[str]) -> List[str]:
        """获取可执行的节点（依赖全部完成）"""
        ready = []
        for nid in self.nodes:
            if nid in completed:
                continue
            if all(dep in completed for dep in self.edges[nid]):
                ready.append(nid)
        return ready

    def subgraph(self, node_ids: Set[str]) -> "DAG[T]":
        """提取子图"""
        sub = DAG[T]()
        for nid in node_ids:
            if nid in self.nodes:
                sub.add_node(nid, self.nodes[nid])
        for nid in node_ids:
            for child in self.edges.get(nid, []):
                if child in node_ids:
                    sub.add_edge(nid, child)
        return sub


# =============================================================================
# 4. TheoreticalDebtEngine — 理论债务清理引擎
# =============================================================================

class TheoreticalDebtEngine:
    """
    理论债务清理引擎
    =================
    - 维护猜想<->定理<->证明的依赖DAG
    - 自动分配证明优先级（拓扑排序+影响力分析）
    - 与Lean接口：生成Lean证明骨架
    - 验证：检查Lean编译是否通过
    """

    def __init__(self) -> None:
        self.dag = DAG[DebtItem]()
        self.items: Dict[str, DebtItem] = {}
        self._lean_templates: Dict[str, str] = {}
        self._proof_cache: Dict[str, bool] = {}

    def load_items(self, items: List[DebtItem]) -> None:
        """加载理论债务项"""
        for item in items:
            if item.debt_type != DebtType.THEORETICAL:
                continue
            self.items[item.id] = item
            self.dag.add_node(item.id, item)

        # 建立依赖边
        for item in items:
            if item.debt_type != DebtType.THEORETICAL:
                continue
            for dep_id in item.dependencies:
                if dep_id in self.items:
                    self.dag.add_edge(item.id, dep_id)

        # 计算影响力分数
        scores = self.dag.compute_impact_scores()
        for nid, score in scores.items():
            self.items[nid].impact_score = score

    def build_priority_queue(self) -> List[DebtItem]:
        """
        构建优先级队列：
        优先级 = 严重度 x 影响力 x (1 / (1 + 依赖深度))
        返回排序后的债务项列表（优先级从高到低）
        """
        try:
            topo_order = self.dag.topological_sort()
            depth_map = {nid: 0 for nid in topo_order}
            for nid in topo_order:
                for child in self.dag.edges[nid]:
                    depth_map[nid] = max(depth_map[nid], depth_map[child] + 1)
        except OMNIHUBTheoreticalError:
            depth_map = {nid: 0 for nid in self.items}

        def priority_key(item: DebtItem) -> float:
            depth = depth_map.get(item.id, 0)
            return (
                item.severity.numeric()
                * item.impact_score
                / (1.0 + depth * 0.2)
            )

        sorted_items = sorted(self.items.values(), key=priority_key, reverse=True)
        return sorted_items

    def generate_lean_skeleton(self, item: DebtItem) -> str:
        """
        生成Lean 4证明骨架
        基于债务描述自动推断证明结构
        """
        if not item.lean_formalizable:
            return "-- Not formalizable in Lean"

        # 基于描述推断定理类型
        desc_lower = item.description.lower()

        if "conjecture" in desc_lower or "猜想" in desc_lower:
            theorem_type = "conjecture"
        elif "theorem" in desc_lower or "定理" in desc_lower:
            theorem_type = "theorem"
        elif "lemma" in desc_lower or "引理" in desc_lower:
            theorem_type = "lemma"
        else:
            theorem_type = "theorem"

        # 提取可能涉及的数学结构
        structures = []
        if "field" in desc_lower or "场" in desc_lower:
            structures.append("UnifiedField")
        if "entropy" in desc_lower or "熵" in desc_lower:
            structures.append("EntropyMeasure")
        if "coherence" in desc_lower or "相干" in desc_lower:
            structures.append("CoherenceSpace")
        if "emergence" in desc_lower or "涌现" in desc_lower:
            structures.append("EmergenceSystem")

        struct_str = " ".join(f"[{s}]" for s in structures) if structures else "[alpha : Type*]"

        skeleton = f"""-- Auto-generated Lean 4 skeleton for debt: {item.id}
-- Description: {item.description}
-- Severity: {item.severity.value}
-- Estimated effort: {item.estimated_effort}h

import Mathlib

namespace OMNIHUB.V11

{theorem_type} {item.id.replace("-", "_")} {struct_str} :
    -- TODO: Formalize the statement based on:
    -- {item.description}
    sorry := by
  -- Proof strategy:
  -- 1. Unfold definitions
  -- 2. Apply relevant lemmas from dependency items
  -- 3. Use automation (simp, linarith, etc.)
  sorry

end OMNIHUB.V11
"""
        item.lean_skeleton = skeleton
        self._lean_templates[item.id] = skeleton
        return skeleton

    def verify_lean_proof(self, item: DebtItem, lean_file_path: Optional[str] = None) -> bool:
        """
        验证Lean证明：
        1. 如果提供了lean文件路径，尝试编译
        2. 否则检查本地缓存
        3. 返回编译是否通过
        """
        if lean_file_path and Path(lean_file_path).exists():
            try:
                result = subprocess.run(
                    ["lake", "build", lean_file_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                passed = result.returncode == 0
                self._proof_cache[item.id] = passed
                item.verification_result = passed
                return passed
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # lake不可用，标记为待验证
                item.verification_result = None
                return False

        # 回退：检查骨架完整性
        if item.lean_skeleton and "sorry" not in item.lean_skeleton:
            item.verification_result = True
            return True

        item.verification_result = False
        return False

    def get_proof_status(self, item_id: str) -> Dict[str, Any]:
        """获取证明状态报告"""
        item = self.items.get(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}

        return {
            "id": item_id,
            "status": item.status.value,
            "lean_formalizable": item.lean_formalizable,
            "has_skeleton": item.lean_skeleton is not None,
            "verification_result": item.verification_result,
            "impact_score": round(item.impact_score, 4),
            "dependencies": item.dependencies,
            "blocked_by": [
                dep for dep in item.dependencies
                if dep in self.items and self.items[dep].status != DebtStatus.RESOLVED
            ],
        }

    def generate_dependency_graphviz(self) -> str:
        """生成依赖图DOT格式"""
        lines = ["digraph TheoreticalDebt {"]
        for nid, item in self.items.items():
            color = {"critical": "red", "high": "orange",
                     "medium": "yellow", "low": "green"}.get(item.severity.value, "gray")
            shape = "box" if item.lean_formalizable else "ellipse"
            lines.append(f'  "{nid}" [label="{item.file_path or nid}", color={color}, shape={shape}];')
        for nid, children in self.dag.edges.items():
            for child in children:
                lines.append(f'  "{nid}" -> "{child}";')
        lines.append("}")
        return "\n".join(lines)

# =============================================================================
# 5. TechnicalDebtEngine — 技术债务清理引擎
# =============================================================================

@dataclass
class CodeMetrics:
    """代码质量度量"""
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    duplicate_blocks: int = 0
    coupling_score: float = 0.0
    type_coverage: float = 0.0
    doc_coverage: float = 0.0
    test_coverage: float = 0.0


@dataclass
class RefactorSuggestion:
    """重构建议"""
    debt_id: str
    suggestion: str
    auto_applicable: bool = False
    patch: Optional[str] = None
    expected_improvement: str = ""


class TechnicalDebtEngine:
    """
    技术债务清理引擎
    =================
    - 代码静态分析：圈复杂度、重复代码、耦合度
    - 自动重构建议
    - 兼容性矩阵维护
    - 验证：单元测试通过率、性能基准
    """

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = Path(project_root) if project_root else Path(".")
        self.dag = DAG[DebtItem]()
        self.items: Dict[str, DebtItem] = {}
        self.metrics_cache: Dict[str, CodeMetrics] = {}
        self.suggestions: Dict[str, List[RefactorSuggestion]] = defaultdict(list)
        self.compatibility_matrix: Dict[str, Dict[str, bool]] = defaultdict(dict)
        self._test_results: Dict[str, Dict[str, Any]] = {}

    def load_items(self, items: List[DebtItem]) -> None:
        """加载技术债务项"""
        for item in items:
            if item.debt_type != DebtType.TECHNICAL:
                continue
            self.items[item.id] = item
            self.dag.add_node(item.id, item)

        # 建立依赖（同文件的债务互相依赖）
        file_to_items: Dict[str, List[str]] = defaultdict(list)
        for item in self.items.values():
            if item.file_path:
                file_to_items[item.file_path].append(item.id)

        for file_path, ids in file_to_items.items():
            for i, id1 in enumerate(ids):
                for id2 in ids[i + 1:]:
                    # 同文件内的债务有弱依赖关系
                    self.dag.add_edge(id1, id2)

        scores = self.dag.compute_impact_scores()
        for nid, score in scores.items():
            self.items[nid].impact_score = score

    def analyze_file(self, file_path: str) -> CodeMetrics:
        """静态分析单个Python文件"""
        path = self.project_root / file_path
        if not path.exists():
            return CodeMetrics()

        try:
            source = path.read_text(encoding="utf-8")
        except Exception:
            return CodeMetrics()

        tree = ast.parse(source)

        # 圈复杂度（简化McCabe）
        complexity = self._compute_cyclomatic_complexity(tree)

        # 代码行数
        loc = len([l for l in source.splitlines() if l.strip() and not l.strip().startswith("#")])

        # 类型注解覆盖率
        type_coverage = self._compute_type_coverage(tree, source)

        # 文档覆盖率
        doc_coverage = self._compute_doc_coverage(tree)

        metrics = CodeMetrics(
            cyclomatic_complexity=complexity,
            lines_of_code=loc,
            type_coverage=type_coverage,
            doc_coverage=doc_coverage,
        )
        self.metrics_cache[file_path] = metrics
        return metrics

    def _compute_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度（简化版）"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def _compute_type_coverage(self, tree: ast.AST, source: str) -> float:
        """计算类型注解覆盖率"""
        total_funcs = 0
        typed_funcs = 0
        total_args = 0
        typed_args = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                if node.returns:
                    typed_funcs += 1
                for arg in node.args.args + node.args.kwonlyargs:
                    total_args += 1
                    if arg.annotation:
                        typed_args += 1

        if total_args == 0:
            return 1.0 if total_funcs == 0 or typed_funcs == total_funcs else 0.0
        return typed_args / total_args

    def _compute_doc_coverage(self, tree: ast.AST) -> float:
        """计算文档字符串覆盖率"""
        total = 0
        documented = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                total += 1
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                    documented += 1
        return documented / total if total > 0 else 1.0

    def find_duplicate_code(self, files: List[str], min_lines: int = 5) -> List[Dict[str, Any]]:
        """查找重复代码块"""
        blocks: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

        for file_path in files:
            path = self.project_root / file_path
            if not path.exists():
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue

            for i in range(len(lines) - min_lines + 1):
                block = "\n".join(lines[i:i + min_lines])
                block = re.sub(r"\s+", " ", block).strip()
                if len(block) > 20:
                    blocks[block].append((file_path, i + 1))

        duplicates = []
        for block, locations in blocks.items():
            if len(locations) > 1:
                duplicates.append({
                    "block_preview": block[:80] + "...",
                    "locations": locations,
                    "count": len(locations),
                })
        return duplicates

    def generate_refactor_suggestions(self, item: DebtItem) -> List[RefactorSuggestion]:
        """基于债务类型生成重构建议"""
        suggestions: List[RefactorSuggestion] = []
        desc_lower = item.description.lower()

        if "print" in desc_lower:
            suggestions.append(RefactorSuggestion(
                debt_id=item.id,
                suggestion="Replace print() with structured logging via get_logger()",
                auto_applicable=True,
                expected_improvement="Improved observability and log level control",
                patch="s/print(/logger.debug(/g",
            ))

        if "hardcoded" in desc_lower or "path" in desc_lower:
            suggestions.append(RefactorSuggestion(
                debt_id=item.id,
                suggestion="Replace hardcoded paths with ConfigLoader or environment variables",
                auto_applicable=False,
                expected_improvement="Improved portability and configurability",
            ))

        if "broad exception" in desc_lower or "except:" in desc_lower:
            suggestions.append(RefactorSuggestion(
                debt_id=item.id,
                suggestion="Replace bare except: with specific exception types",
                auto_applicable=True,
                expected_improvement="Improved error handling precision and debugging",
                patch="s/except:/except SpecificError:/g",
            ))

        if "todo" in desc_lower or "fixme" in desc_lower:
            suggestions.append(RefactorSuggestion(
                debt_id=item.id,
                suggestion="Resolve TODO/FIXME markers or convert to tracked debt items",
                auto_applicable=False,
                expected_improvement="Clearer codebase and better task tracking",
            ))

        self.suggestions[item.id] = suggestions
        return suggestions

    def update_compatibility_matrix(self, module_a: str, module_b: str, compatible: bool) -> None:
        """更新模块兼容性矩阵"""
        self.compatibility_matrix[module_a][module_b] = compatible
        self.compatibility_matrix[module_b][module_a] = compatible

    def check_compatibility(self, module_a: str, module_b: str) -> Optional[bool]:
        """检查模块兼容性"""
        return self.compatibility_matrix.get(module_a, {}).get(module_b)

    def run_unit_tests(self, test_path: str) -> Dict[str, Any]:
        """运行单元测试并收集结果"""
        result = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "pass_rate": 0.0,
            "duration": 0.0,
            "details": [],
        }

        try:
            start = time.time()
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            duration = time.time() - start
            result["duration"] = duration

            # 解析pytest输出
            for line in proc.stdout.splitlines():
                if line.startswith("PASSED"):
                    result["passed"] += 1
                elif line.startswith("FAILED"):
                    result["failed"] += 1
                elif line.startswith("SKIPPED"):
                    result["skipped"] += 1

            result["total"] = result["passed"] + result["failed"] + result["skipped"]
            if result["total"] > 0:
                result["pass_rate"] = result["passed"] / result["total"]

        except (subprocess.TimeoutExpired, FileNotFoundError):
            result["error"] = "Test execution failed or pytest not available"

        self._test_results[test_path] = result
        return result

    def build_priority_queue(self) -> List[DebtItem]:
        """技术债务优先级：严重度 x 影响力 x 文件复杂度因子"""
        def priority_key(item: DebtItem) -> float:
            metrics = self.metrics_cache.get(item.file_path or "", CodeMetrics())
            complexity_factor = 1.0 + metrics.cyclomatic_complexity / 20.0
            return item.severity.numeric() * item.impact_score * complexity_factor

        return sorted(self.items.values(), key=priority_key, reverse=True)

    def get_technical_health_report(self) -> Dict[str, Any]:
        """生成技术健康报告"""
        total_items = len(self.items)
        resolved = sum(1 for i in self.items.values() if i.status == DebtStatus.RESOLVED)
        total_complexity = sum(m.cyclomatic_complexity for m in self.metrics_cache.values())
        avg_type_coverage = (
            sum(m.type_coverage for m in self.metrics_cache.values()) / len(self.metrics_cache)
            if self.metrics_cache else 1.0
        )

        return {
            "total_debt_items": total_items,
            "resolved": resolved,
            "resolution_rate": resolved / total_items if total_items > 0 else 1.0,
            "total_cyclomatic_complexity": total_complexity,
            "average_type_coverage": round(avg_type_coverage, 4),
            "files_analyzed": len(self.metrics_cache),
            "compatibility_pairs": sum(len(v) for v in self.compatibility_matrix.values()),
        }

# =============================================================================
# 6. EngineeringDebtEngine — 工程债务清理引擎
# =============================================================================

@dataclass
class ArchitectureCheckResult:
    """架构检查结果"""
    check_name: str
    passed: bool
    severity: DebtSeverity
    details: str
    recommendation: str


@dataclass
class DriftReport:
    """版本漂移报告"""
    module: str
    declared_version: str
    actual_version: str
    drift_detected: bool
    severity: DebtSeverity


class EngineeringDebtEngine:
    """
    工程债务清理引擎
    =================
    - 架构一致性检查
    - 文档-代码-测试三重同步检测
    - 版本漂移检测
    - 验证：架构评审清单
    """

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = Path(project_root) if project_root else Path(".")
        self.dag = DAG[DebtItem]()
        self.items: Dict[str, DebtItem] = {}
        self.architecture_rules: List[Callable[[], ArchitectureCheckResult]] = []
        self.drift_reports: List[DriftReport] = []
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """注册默认架构规则"""
        self.architecture_rules.append(self._check_module_naming)
        self.architecture_rules.append(self._check_init_files)
        self.architecture_rules.append(self._check_standards_import)

    def load_items(self, items: List[DebtItem]) -> None:
        """加载工程债务项"""
        for item in items:
            if item.debt_type != DebtType.ENGINEERING:
                continue
            self.items[item.id] = item
            self.dag.add_node(item.id, item)

        for item in self.items.values():
            for dep_id in item.dependencies:
                if dep_id in self.items:
                    self.dag.add_edge(item.id, dep_id)

    def _check_module_naming(self) -> ArchitectureCheckResult:
        """检查模块命名规范"""
        violations = []
        for py_file in self.project_root.rglob("*.py"):
            rel = py_file.relative_to(self.project_root)
            name = py_file.stem
            if not re.match(r"^[a-z][a-z0-9_]*$", name):
                violations.append(str(rel))

        passed = len(violations) == 0
        return ArchitectureCheckResult(
            check_name="module_naming",
            passed=passed,
            severity=DebtSeverity.LOW if passed else DebtSeverity.MEDIUM,
            details=f"{len(violations)} naming violations" if violations else "All modules follow naming convention",
            recommendation="Rename modules to snake_case" if violations else "",
        )

    def _check_init_files(self) -> ArchitectureCheckResult:
        """检查__init__.py完整性"""
        missing = []
        for pkg_dir in self.project_root.rglob("*/"):
            if any((pkg_dir / f).exists() for f in ["*.py"]):
                if not (pkg_dir / "__init__.py").exists():
                    rel = pkg_dir.relative_to(self.project_root)
                    if str(rel) != ".":
                        missing.append(str(rel))

        passed = len(missing) == 0
        return ArchitectureCheckResult(
            check_name="init_files",
            passed=passed,
            severity=DebtSeverity.LOW if passed else DebtSeverity.MEDIUM,
            details=f"{len(missing)} packages missing __init__.py" if missing else "All packages have __init__.py",
            recommendation="Add __init__.py to all Python packages" if missing else "",
        )

    def _check_standards_import(self) -> ArchitectureCheckResult:
        """检查是否导入v11_standards"""
        missing = []
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name == "v11_standards.py":
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                if "v11_standards" not in content and "OMNI-HUB" in content:
                    rel = py_file.relative_to(self.project_root)
                    missing.append(str(rel))
            except Exception:
                pass

        passed = len(missing) == 0
        return ArchitectureCheckResult(
            check_name="standards_import",
            passed=passed,
            severity=DebtSeverity.LOW if passed else DebtSeverity.MEDIUM,
            details=f"{len(missing)} files not importing standards" if missing else "All files import v11_standards",
            recommendation="Import v11_standards in all core modules" if missing else "",
        )

    def run_architecture_checks(self) -> List[ArchitectureCheckResult]:
        """运行所有架构检查"""
        results = []
        for rule in self.architecture_rules:
            try:
                results.append(rule())
            except Exception as e:
                results.append(ArchitectureCheckResult(
                    check_name=rule.__name__,
                    passed=False,
                    severity=DebtSeverity.MEDIUM,
                    details=f"Check failed with error: {e}",
                    recommendation="Review check implementation",
                ))
        return results

    def check_doc_code_test_sync(self, module_name: str) -> Dict[str, Any]:
        """
        文档-代码-测试三重同步检测
        检查：
        1. 模块是否有文档
        2. 文档中的API是否与代码一致
        3. 是否有对应的测试文件
        """
        module_path = self.project_root / f"{module_name}.py"
        doc_path = self.project_root / "docs" / f"{module_name}.md"
        test_path = self.project_root / "tests" / f"test_{module_name}.py"

        has_code = module_path.exists()
        has_doc = doc_path.exists()
        has_test = test_path.exists()

        # 检查文档中的函数签名是否与代码一致
        signature_match = True
        if has_code and has_doc:
            try:
                code = module_path.read_text(encoding="utf-8")
                doc = doc_path.read_text(encoding="utf-8")
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        if func_name.startswith("_"):
                            continue
                        if func_name not in doc:
                            signature_match = False
                            break
            except Exception:
                signature_match = False

        sync_score = sum([has_code, has_doc, has_test, signature_match]) / 4.0

        return {
            "module": module_name,
            "has_code": has_code,
            "has_doc": has_doc,
            "has_test": has_test,
            "signature_match": signature_match,
            "sync_score": sync_score,
            "fully_synced": sync_score == 1.0,
        }

    def detect_version_drift(self, modules: List[str]) -> List[DriftReport]:
        """
        版本漂移检测
        检查各模块声明的版本是否与主版本一致
        """
        reports = []
        main_version = str(V11_VERSION)

        for module_name in modules:
            module_path = self.project_root / f"{module_name}.py"
            declared = "unknown"
            try:
                if module_path.exists():
                    content = module_path.read_text(encoding="utf-8")
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        declared = match.group(1)
            except Exception:
                pass

            drift = declared != main_version
            reports.append(DriftReport(
                module=module_name,
                declared_version=declared,
                actual_version=main_version,
                drift_detected=drift,
                severity=DebtSeverity.HIGH if drift else DebtSeverity.LOW,
            ))

        self.drift_reports = reports
        return reports

    def generate_architecture_review_checklist(self) -> List[Dict[str, Any]]:
        """生成架构评审清单"""
        checks = self.run_architecture_checks()
        checklist = []
        for check in checks:
            checklist.append({
                "item": check.check_name,
                "status": "PASS" if check.passed else "FAIL",
                "severity": check.severity.value,
                "details": check.details,
                "action": check.recommendation,
            })
        return checklist

    def build_priority_queue(self) -> List[DebtItem]:
        """工程债务优先级"""
        def priority_key(item: DebtItem) -> float:
            return item.severity.numeric() * item.impact_score * (1.0 + item.aging_days / 30.0)
        return sorted(self.items.values(), key=priority_key, reverse=True)

# =============================================================================
# 7. CleanupTask — 清理任务
# =============================================================================

@dataclass
class CleanupTask:
    """单个清理任务"""
    task_id: str
    debt_id: str
    debt_type: DebtType
    priority: float
    assigned_to: Optional[str]
    estimated_hours: float
    description: str
    action_items: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


# =============================================================================
# 8. CleanupRoadmap — 清理路线图
# =============================================================================

@dataclass
class CleanupRoadmap:
    """清理路线图"""
    version: str
    created_at: float
    phases: List[Dict[str, Any]] = field(default_factory=list)
    total_estimated_hours: float = 0.0
    critical_path: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "phases": self.phases,
            "total_estimated_hours": self.total_estimated_hours,
            "critical_path": self.critical_path,
        }


# =============================================================================
# 9. DebtCleanupOrchestrator — 债务清理协调器
# =============================================================================

class DebtCleanupOrchestrator:
    """
    债务清理协调器
    ==============
    - 整合三类债务引擎
    - 生成清理路线图（Roadmap）
    - 跟踪清理进度
    - 计算"债务健康指数" DebtHealthIndex = 1 / (1 + sum(severity_i x aging_i))
    """

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = Path(project_root) if project_root else Path(".")
        self.theoretical = TheoreticalDebtEngine()
        self.technical = TechnicalDebtEngine(str(self.project_root))
        self.engineering = EngineeringDebtEngine(str(self.project_root))

        self.all_items: Dict[str, DebtItem] = {}
        self.tasks: Dict[str, CleanupTask] = {}
        self.roadmap: Optional[CleanupRoadmap] = None
        self._progress_history: List[Dict[str, Any]] = []

    def load_from_report(self, report_path: str) -> None:
        """从债务报告加载所有债务项"""
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        all_items: List[DebtItem] = []

        # 加载理论债务
        for idx, item_data in enumerate(report.get("theoretical_debt", {}).get("items", [])):
            debt = DebtItem(
                id=f"T-THEO-{idx:04d}",
                debt_type=DebtType.THEORETICAL,
                severity=DebtSeverity.from_string(item_data.get("severity", "medium")),
                description=item_data.get("description", ""),
                file_path=item_data.get("file"),
                verification_method="Lean proof compilation",
                estimated_effort=self._estimate_theoretical_effort(item_data),
                lean_formalizable=item_data.get("type") == "unproven_conjecture",
                tags=[item_data.get("type", "unknown")],
            )
            all_items.append(debt)

        # 加载技术债务
        for idx, item_data in enumerate(report.get("technical_debt", {}).get("items", [])):
            debt = DebtItem(
                id=f"T-TECH-{idx:04d}",
                debt_type=DebtType.TECHNICAL,
                severity=DebtSeverity.from_string(item_data.get("severity", "low")),
                description=item_data.get("description", ""),
                file_path=item_data.get("file"),
                verification_method="Static analysis + unit tests",
                estimated_effort=self._estimate_technical_effort(item_data),
                lean_formalizable=False,
                tags=[item_data.get("type", "unknown")],
            )
            all_items.append(debt)

        # 加载工程债务（如果存在）
        for idx, item_data in enumerate(report.get("engineering_debt", {}).get("items", [])):
            debt = DebtItem(
                id=f"T-ENGG-{idx:04d}",
                debt_type=DebtType.ENGINEERING,
                severity=DebtSeverity.from_string(item_data.get("severity", "medium")),
                description=item_data.get("description", ""),
                file_path=item_data.get("file"),
                verification_method="Architecture review checklist",
                estimated_effort=self._estimate_engineering_effort(item_data),
                lean_formalizable=False,
                tags=[item_data.get("type", "unknown")],
            )
            all_items.append(debt)

        # 自动推断依赖关系
        self._infer_dependencies(all_items)

        self.all_items = {item.id: item for item in all_items}
        self.theoretical.load_items(all_items)
        self.technical.load_items(all_items)
        self.engineering.load_items(all_items)

        logger.info("Loaded %d debt items from report", len(all_items))

    def _estimate_theoretical_effort(self, item_data: Dict[str, Any]) -> float:
        """估计理论债务工作量"""
        base = {"high": 16.0, "medium": 8.0, "low": 4.0}.get(item_data.get("severity", "low"), 4.0)
        if item_data.get("type") == "unproven_conjecture":
            base *= 2.0
        return base

    def _estimate_technical_effort(self, item_data: Dict[str, Any]) -> float:
        """估计技术债务工作量"""
        base = {"high": 8.0, "medium": 4.0, "low": 2.0}.get(item_data.get("severity", "low"), 2.0)
        desc = item_data.get("description", "")
        if "print" in desc.lower():
            count_match = re.search(r'(\d+)', desc)
            if count_match:
                base += int(count_match.group(1)) * 0.1
        return base

    def _estimate_engineering_effort(self, item_data: Dict[str, Any]) -> float:
        """估计工程债务工作量"""
        return {"high": 12.0, "medium": 6.0, "low": 3.0}.get(item_data.get("severity", "low"), 3.0)

    def _infer_dependencies(self, items: List[DebtItem]) -> None:
        """自动推断债务依赖关系"""
        file_map: Dict[str, List[DebtItem]] = defaultdict(list)
        for item in items:
            if item.file_path:
                file_map[item.file_path].append(item)

        # 同文件内：理论债务优先于技术债务
        for file_path, file_items in file_map.items():
            theo_items = [i for i in file_items if i.debt_type == DebtType.THEORETICAL]
            tech_items = [i for i in file_items if i.debt_type == DebtType.TECHNICAL]
            for tech in tech_items:
                for theo in theo_items:
                    if theo.id not in tech.dependencies:
                        tech.dependencies.append(theo.id)

        # 严重依赖：high severity依赖同类型的medium severity
        high_items = [i for i in items if i.severity == DebtSeverity.HIGH]
        for high in high_items:
            for other in items:
                if (other.debt_type == high.debt_type
                        and other.severity == DebtSeverity.MEDIUM
                        and other.file_path == high.file_path
                        and other.id != high.id):
                    if other.id not in high.dependencies:
                        high.dependencies.append(other.id)

    def generate_roadmap(self, team_capacity: float = 40.0) -> CleanupRoadmap:
        """
        生成清理路线图
        team_capacity: 每周团队工时
        """
        roadmap = CleanupRoadmap(
            version=str(V11_VERSION),
            created_at=time.time(),
        )

        # 获取各引擎的优先级队列
        theo_queue = self.theoretical.build_priority_queue()
        tech_queue = self.technical.build_priority_queue()
        engg_queue = self.engineering.build_priority_queue()

        # 合并并按优先级排序
        all_queue = sorted(
            theo_queue + tech_queue + engg_queue,
            key=lambda x: x.severity.numeric() * x.impact_score,
            reverse=True,
        )

        # 分阶段（每周一个阶段）
        phases = []
        current_phase_items = []
        current_hours = 0.0
        phase_num = 1

        for item in all_queue:
            if item.status == DebtStatus.RESOLVED:
                continue

            if current_hours + item.estimated_effort > team_capacity and current_phase_items:
                phases.append({
                    "phase": phase_num,
                    "focus": self._determine_phase_focus(current_phase_items),
                    "items": [i.id for i in current_phase_items],
                    "estimated_hours": round(current_hours, 2),
                    "item_count": len(current_phase_items),
                })
                phase_num += 1
                current_phase_items = []
                current_hours = 0.0

            current_phase_items.append(item)
            current_hours += item.estimated_effort

        if current_phase_items:
            phases.append({
                "phase": phase_num,
                "focus": self._determine_phase_focus(current_phase_items),
                "items": [i.id for i in current_phase_items],
                "estimated_hours": round(current_hours, 2),
                "item_count": len(current_phase_items),
            })

        roadmap.phases = phases
        roadmap.total_estimated_hours = sum(p["estimated_hours"] for p in phases)
        roadmap.critical_path = self._compute_critical_path(all_queue)
        self.roadmap = roadmap

        return roadmap

    def _determine_phase_focus(self, items: List[DebtItem]) -> str:
        """确定阶段重点"""
        type_counts: Dict[str, int] = defaultdict(int)
        for item in items:
            type_counts[item.debt_type.value] += 1
        dominant = max(type_counts, key=type_counts.get) if type_counts else "mixed"
        return f"{dominant}_cleanup"

    def _compute_critical_path(self, items: List[DebtItem]) -> List[str]:
        """计算关键路径（最高优先级未解决项）"""
        unresolved = [i for i in items if i.status != DebtStatus.RESOLVED]
        # 按严重度和影响力排序，取前N个
        critical = sorted(
            unresolved,
            key=lambda x: x.severity.numeric() * x.impact_score,
            reverse=True,
        )[:10]
        return [i.id for i in critical]

    def assign_tasks(self, team_members: Optional[List[str]] = None) -> List[CleanupTask]:
        """
        分配清理任务给团队成员
        使用负载均衡算法
        """
        if team_members is None:
            team_members = ["theoretical_specialist", "technical_lead", "engineering_lead"]

        # 按类型映射到专长
        type_to_specialist = {
            DebtType.THEORETICAL: "theoretical_specialist",
            DebtType.TECHNICAL: "technical_lead",
            DebtType.ENGINEERING: "engineering_lead",
        }

        tasks = []
        member_loads: Dict[str, float] = {m: 0.0 for m in team_members}

        for item in self.all_items.values():
            if item.status == DebtStatus.RESOLVED:
                continue

            # 确定最佳分配
            preferred = type_to_specialist.get(item.debt_type, team_members[0])
            if preferred not in team_members:
                preferred = min(member_loads, key=member_loads.get)

            # 负载均衡：如果负载过高，分配给最空闲的成员
            if member_loads[preferred] > sum(member_loads.values()) / len(team_members) * 1.5:
                preferred = min(member_loads, key=member_loads.get)

            task = CleanupTask(
                task_id=f"TASK-{item.id}",
                debt_id=item.id,
                debt_type=item.debt_type,
                priority=item.weight(),
                assigned_to=preferred,
                estimated_hours=item.estimated_effort,
                description=item.description,
                action_items=self._generate_action_items(item),
            )
            tasks.append(task)
            member_loads[preferred] += item.estimated_effort

        self.tasks = {t.task_id: t for t in tasks}
        return tasks

    def _generate_action_items(self, item: DebtItem) -> List[str]:
        """为债务项生成行动项"""
        actions = []
        if item.debt_type == DebtType.THEORETICAL:
            if item.lean_formalizable:
                actions.append("Generate Lean proof skeleton")
                actions.append("Complete formal proof")
                actions.append("Run Lean compiler verification")
            else:
                actions.append("Write informal proof")
                actions.append("Peer review proof")
        elif item.debt_type == DebtType.TECHNICAL:
            if "print" in item.description.lower():
                actions.append("Replace print statements with logging")
            if "hardcoded" in item.description.lower():
                actions.append("Extract hardcoded values to configuration")
            if "broad exception" in item.description.lower():
                actions.append("Refine exception handling")
            actions.append("Run static analysis")
            actions.append("Run unit tests")
        elif item.debt_type == DebtType.ENGINEERING:
            actions.append("Review architecture consistency")
            actions.append("Update documentation")
            actions.append("Verify test coverage")
        return actions

    def track_progress(self) -> Dict[str, Any]:
        """跟踪清理进度"""
        total = len(self.all_items)
        by_type: Dict[str, Dict[str, int]] = {
            "theoretical": {"total": 0, "resolved": 0, "in_progress": 0},
            "technical": {"total": 0, "resolved": 0, "in_progress": 0},
            "engineering": {"total": 0, "resolved": 0, "in_progress": 0},
        }

        for item in self.all_items.values():
            t = item.debt_type.value
            by_type[t]["total"] += 1
            if item.status == DebtStatus.RESOLVED:
                by_type[t]["resolved"] += 1
            elif item.status == DebtStatus.IN_PROGRESS:
                by_type[t]["in_progress"] += 1

        overall_resolved = sum(by_type[t]["resolved"] for t in by_type)
        overall_in_progress = sum(by_type[t]["in_progress"] for t in by_type)

        progress = {
            "timestamp": time.time(),
            "total_items": total,
            "resolved": overall_resolved,
            "in_progress": overall_in_progress,
            "open": total - overall_resolved - overall_in_progress,
            "completion_rate": overall_resolved / total if total > 0 else 1.0,
            "by_type": by_type,
            "health_index": self.compute_health_index(),
        }
        self._progress_history.append(progress)
        return progress

    def compute_health_index(self) -> float:
        """
        计算债务健康指数
        DebtHealthIndex = 1 / (1 + sum(severity_i x aging_i))
        """
        total_weight = 0.0
        for item in self.all_items.values():
            if item.status != DebtStatus.RESOLVED:
                aging = max(1.0, item.aging_days)
                total_weight += item.severity.numeric() * aging

        if total_weight == 0:
            return 1.0
        return 1.0 / (1.0 + total_weight / 100.0)

    def compute_improved_health_index(self) -> Dict[str, float]:
        """
        计算改进版健康指数（分类加权）
        """
        weights = {"theoretical": 0.0, "technical": 0.0, "engineering": 0.0}
        counts = {"theoretical": 0, "technical": 0, "engineering": 0}

        for item in self.all_items.values():
            if item.status != DebtStatus.RESOLVED:
                t = item.debt_type.value
                aging = max(1.0, item.aging_days)
                weights[t] += item.severity.numeric() * aging
                counts[t] += 1

        indices = {}
        for t in weights:
            if weights[t] == 0:
                indices[t] = 1.0
            else:
                indices[t] = 1.0 / (1.0 + weights[t] / max(counts[t], 1) * 0.5)

        # 总体指数（加权平均）
        total = sum(weights.values())
        overall = 1.0 / (1.0 + total / 100.0) if total > 0 else 1.0
        indices["overall"] = overall
        return indices

    def verify_cleanup(self, debt_id: str) -> bool:
        """验证单个债务项的清理结果"""
        item = self.all_items.get(debt_id)
        if not item:
            return False

        if item.debt_type == DebtType.THEORETICAL:
            result = self.theoretical.verify_lean_proof(item)
        elif item.debt_type == DebtType.TECHNICAL:
            # 技术债务：检查文件是否仍然存在该问题
            result = self._verify_technical_cleanup(item)
        else:
            result = self._verify_engineering_cleanup(item)

        if result:
            item.mark_resolved(verified=True)
            task = self.tasks.get(f"TASK-{debt_id}")
            if task:
                task.status = "completed"
                task.completed_at = time.time()

        return result

    def _verify_technical_cleanup(self, item: DebtItem) -> bool:
        """验证技术债务清理"""
        if not item.file_path:
            return True
        path = self.project_root / item.file_path
        if not path.exists():
            return True  # 文件已删除视为已清理

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return False

        desc_lower = item.description.lower()
        if "print" in desc_lower:
            # 检查是否还有裸print（非logger.print）
            # 简化检查：是否有print( 但不匹配logger
            lines = content.splitlines()
            for line in lines:
                if re.search(r'(?<!\.)\bprint\s*\(', line):
                    return False
        if "hardcoded" in desc_lower:
            # 检查是否还有硬编码路径
            if re.search(r'["\']\s*/\w+/', content):
                return False
        if "broad exception" in desc_lower:
            if "except:" in content:
                return False

        return True

    def _verify_engineering_cleanup(self, item: DebtItem) -> bool:
        """验证工程债务清理"""
        # 重新运行架构检查
        results = self.engineering.run_architecture_checks()
        return all(r.passed for r in results)

    def generate_full_report(self) -> Dict[str, Any]:
        """生成完整清理报告"""
        health = self.compute_improved_health_index()
        progress = self.track_progress()

        # 各引擎报告
        theo_report = {
            "total_items": len(self.theoretical.items),
            "priority_queue": [i.id for i in self.theoretical.build_priority_queue()[:5]],
            "lean_formalizable_count": sum(1 for i in self.theoretical.items.values() if i.lean_formalizable),
        }

        tech_report = self.technical.get_technical_health_report()

        engg_report = {
            "total_items": len(self.engineering.items),
            "architecture_checks": [asdict(r) if hasattr(r, '__dataclass_fields__') else r.__dict__ for r in self.engineering.run_architecture_checks()],
            "version_drifts": [asdict(r) if hasattr(r, '__dataclass_fields__') else r.__dict__ for r in self.engineering.drift_reports],
        }

        return {
            "report_version": "11.0.0",
            "generated_at": time.time(),
            "health_index": health,
            "progress": progress,
            "roadmap": self.roadmap.to_dict() if self.roadmap else None,
            "theoretical": theo_report,
            "technical": tech_report,
            "engineering": engg_report,
            "tasks_assigned": len(self.tasks),
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """生成高层建议"""
        recs = []
        health = self.compute_improved_health_index()

        if health.get("theoretical", 1.0) < 0.7:
            recs.append("PRIORITY: Focus on theoretical debt - high-severity conjectures need proofs")
        if health.get("technical", 1.0) < 0.7:
            recs.append("PRIORITY: Address technical debt - code quality metrics below threshold")
        if health.get("engineering", 1.0) < 0.7:
            recs.append("PRIORITY: Fix engineering debt - architecture consistency issues detected")

        if not recs:
            recs.append("System is in good health. Continue monitoring and preventive maintenance.")

        return recs

    def export_to_json(self, output_path: str) -> None:
        """导出完整报告到JSON"""
        report = self.generate_full_report()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        class DebtEncoder(json.JSONEncoder):
            def default(self, obj: Any) -> Any:
                if isinstance(obj, Enum):
                    return obj.value
                if hasattr(obj, '__dataclass_fields__'):
                    return asdict(obj)
                return super().default(obj)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, cls=DebtEncoder)

# =============================================================================
# 10. Utility Functions
# =============================================================================

def create_debt_id(debt_type: DebtType, index: int, file_hint: str = "") -> str:
    """生成标准债务ID"""
    prefix = {"theoretical": "THEO", "technical": "TECH", "engineering": "ENGG"}.get(
        debt_type.value, "DEBT"
    )
    hint = f"-{file_hint[:8]}" if file_hint else ""
    return f"T-{prefix}-{index:04d}{hint}"


def severity_to_float(severity: DebtSeverity) -> float:
    """严重度转数值"""
    return severity.numeric()


# =============================================================================
# 11. Main Execution & Testing
# =============================================================================

if __name__ == "__main__":
    import logging

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    )
    logger.info("=" * 70)
    logger.info("OMNI-HUB v11.0 — Debt Cleanup Engine Startup")
    logger.info("=" * 70)

    # 确定路径
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    report_path = project_root / "hub" / "v11_debt_report.json"

    if not report_path.exists():
        # 尝试绝对路径
        report_path = Path("/mnt/agents/output/OMNI-HUB/hub/v11_debt_report.json")

    if not report_path.exists():
        logger.error("Debt report not found at %s", report_path)
        # 创建演示数据
        logger.info("Creating demonstration debt data...")
        demo_items = [
            DebtItem(
                id="T-THEO-0000",
                debt_type=DebtType.THEORETICAL,
                severity=DebtSeverity.HIGH,
                description="Unproven conjecture: Field coherence implies emergence stability",
                file_path="v11_knowledge_pedestal_unified.py",
                verification_method="Lean proof compilation",
                estimated_effort=24.0,
                lean_formalizable=True,
            ),
            DebtItem(
                id="T-TECH-0000",
                debt_type=DebtType.TECHNICAL,
                severity=DebtSeverity.MEDIUM,
                description="36 print statements should use logging",
                file_path="bidirectional_drive.py",
                verification_method="Static analysis + unit tests",
                estimated_effort=4.0,
            ),
        ]
        orchestrator = DebtCleanupOrchestrator(str(project_root))
        orchestrator.all_items = {i.id: i for i in demo_items}
        orchestrator.theoretical.load_items(demo_items)
        orchestrator.technical.load_items(demo_items)
    else:
        logger.info("Loading debt report from: %s", report_path)
        orchestrator = DebtCleanupOrchestrator(str(project_root))
        orchestrator.load_from_report(str(report_path))

    # =====================================================================
    # 执行完整清理流程
    # =====================================================================

    # 1. 生成优先级队列
    logger.info("\n--- Theoretical Debt Priority Queue ---")
    theo_queue = orchestrator.theoretical.build_priority_queue()
    for i, item in enumerate(theo_queue[:5], 1):
        logger.info(
            "  %d. [%s] %s (impact=%.2f, effort=%.1fh)",
            i, item.severity.value.upper(), item.file_path or item.id,
            item.impact_score, item.estimated_effort,
        )

    logger.info("\n--- Technical Debt Priority Queue ---")
    tech_queue = orchestrator.technical.build_priority_queue()
    for i, item in enumerate(tech_queue[:5], 1):
        logger.info(
            "  %d. [%s] %s (impact=%.2f, effort=%.1fh)",
            i, item.severity.value.upper(), item.file_path or item.id,
            item.impact_score, item.estimated_effort,
        )

    # 2. 生成Lean证明骨架（对可形式化的理论债务）
    logger.info("\n--- Lean Proof Skeletons ---")
    lean_count = 0
    for item in orchestrator.theoretical.items.values():
        if item.lean_formalizable:
            skeleton = orchestrator.theoretical.generate_lean_skeleton(item)
            lean_count += 1
            if lean_count <= 3:
                logger.info("Generated skeleton for %s (first 80 chars): %s...",
                           item.id, skeleton[:80].replace('\n', ' '))
    logger.info("Total Lean skeletons generated: %d", lean_count)

    # 3. 生成重构建议（对技术债务）
    logger.info("\n--- Refactor Suggestions ---")
    suggestion_count = 0
    for item in orchestrator.technical.items.values():
        suggestions = orchestrator.technical.generate_refactor_suggestions(item)
        suggestion_count += len(suggestions)
        if suggestions and suggestion_count <= 20:
            logger.info("  %s -> %s", item.id, suggestions[0].suggestion)
    logger.info("Total suggestions generated: %d", suggestion_count)

    # 4. 运行架构检查
    logger.info("\n--- Architecture Checks ---")
    arch_results = orchestrator.engineering.run_architecture_checks()
    for result in arch_results:
        status = "PASS" if result.passed else "FAIL"
        logger.info("  [%s] %s: %s", status, result.check_name, result.details)

    # 5. 生成清理路线图
    logger.info("\n--- Cleanup Roadmap ---")
    roadmap = orchestrator.generate_roadmap(team_capacity=40.0)
    logger.info("Total phases: %d", len(roadmap.phases))
    logger.info("Total estimated hours: %.1f", roadmap.total_estimated_hours)
    logger.info("Critical path length: %d", len(roadmap.critical_path))
    for phase in roadmap.phases[:3]:
        logger.info(
            "  Phase %d [%s]: %d items, %.1f hours",
            phase["phase"], phase["focus"], phase["item_count"], phase["estimated_hours"],
        )
    if len(roadmap.phases) > 3:
        logger.info("  ... and %d more phases", len(roadmap.phases) - 3)

    # 6. 分配任务
    logger.info("\n--- Task Assignment ---")
    tasks = orchestrator.assign_tasks(team_members=["theoretical_specialist", "technical_lead", "engineering_lead"])
    member_loads: Dict[str, float] = defaultdict(float)
    for task in tasks:
        member_loads[task.assigned_to or "unassigned"] += task.estimated_hours
    for member, load in sorted(member_loads.items(), key=lambda x: x[1], reverse=True):
        logger.info("  %s: %.1f hours (%d tasks)", member, load,
                   sum(1 for t in tasks if t.assigned_to == member))

    # 7. 计算健康指数
    logger.info("\n--- Debt Health Index ---")
    health = orchestrator.compute_improved_health_index()
    logger.info("  Overall Health Index: %.4f", health["overall"])
    logger.info("  Theoretical Health:   %.4f", health["theoretical"])
    logger.info("  Technical Health:     %.4f", health["technical"])
    logger.info("  Engineering Health:   %.4f", health["engineering"])

    # 8. 跟踪进度
    logger.info("\n--- Progress Tracking ---")
    progress = orchestrator.track_progress()
    logger.info("  Total items: %d", progress["total_items"])
    logger.info("  Resolved: %d (%.1f%%)", progress["resolved"], progress["completion_rate"] * 100)
    logger.info("  In progress: %d", progress["in_progress"])
    logger.info("  Open: %d", progress["open"])

    # 9. 生成完整报告
    logger.info("\n--- Full Report Generation ---")
    full_report = orchestrator.generate_full_report()
    logger.info("  Report generated at: %s", datetime.fromtimestamp(full_report["generated_at"]).isoformat())
    logger.info("  Recommendations:")
    for rec in full_report["recommendations"]:
        logger.info("    - %s", rec)

    # 10. 导出JSON
    output_path = script_dir / "v11_debt_cleanup_report.json"
    orchestrator.export_to_json(str(output_path))
    logger.info("\nReport exported to: %s", output_path)

    # =====================================================================
    # 统计输出
    # =====================================================================
    logger.info("\n" + "=" * 70)
    logger.info("STATISTICS SUMMARY")
    logger.info("=" * 70)

    # 代码行数统计
    engine_file = Path(__file__)
    try:
        code_lines = len(engine_file.read_text(encoding="utf-8").splitlines())
    except Exception:
        code_lines = 0

    total_debt_items = len(orchestrator.all_items)
    theo_items = len(orchestrator.theoretical.items)
    tech_items = len(orchestrator.technical.items)
    engg_items = len(orchestrator.engineering.items)

    logger.info("Engine code lines:        %d", code_lines)
    logger.info("Total debt items loaded:  %d", total_debt_items)
    logger.info("  - Theoretical:          %d", theo_items)
    logger.info("  - Technical:            %d", tech_items)
    logger.info("  - Engineering:          %d", engg_items)
    logger.info("Debt Health Index:        %.6f", health["overall"])
    logger.info("Tasks assigned:           %d", len(tasks))
    logger.info("Roadmap phases:           %d", len(roadmap.phases))
    logger.info("Estimated total hours:    %.1f", roadmap.total_estimated_hours)
    logger.info("=" * 70)

    print("\n" + "=" * 70)
    print("OMNI-HUB v11.0 — Debt Cleanup Engine Execution Complete")
    print(f"  Code lines:          {code_lines}")
    print(f"  Debt items handled:  {total_debt_items}")
    print(f"  Health Index:        {health['overall']:.6f}")
    print("=" * 70)
