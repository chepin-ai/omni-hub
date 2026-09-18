#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__version__ = "11.0.0"
"""
v10_knowledge_life_backbone.py — OMNI-HUB v10.0 知识-生命 backbone-bus 全系统集成
==================================================================================

核心功能：
1. UCIF2SandboxScanner     — ucif2沙箱全量遍历器
2. KnowledgeBackboneBus    — 知识谱系backbone-bus（6基座实时同步）
3. EnhancedKnowledgeSelfComputation — 知识自运算增强（10条规则）
4. ConsciousnessEmotionLifeBind     — 意识-情绪-生命三维绑定
5. SurgeRippleActivator    — 正反向浪涌/涟漪激活器
6. AutonomousEvolutionCore — 全系统自推进核心

架构闭环：
    CK自由意志 → 整体意识 → 情绪人格 → 形式化生命 → 知识生成效率 → 新知识 → 意识状态

Author: OMNI-HUB v10.0 Knowledge-Life Integration Engine
Version: 10.0.0
Date: 2025-09-17
"""

import ast
import hashlib
import json
import math
import os
import random
import re
import sys
import time
import uuid
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import (
    Any, Callable, Dict, Generic, Iterator, List, Literal,
    Optional, Set, Tuple, TypeVar, Union, cast
)

import numpy as np
import logging

# Optional dependencies with graceful fallback
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    warnings.warn("networkx not available; using fallback graph implementations.")

try:
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    warnings.warn("scipy not available; using numpy fallback.")

# =============================================================================
# 0. GLOBAL CONSTANTS — OMNI-HUB v10.0 统一场常数
# =============================================================================

FIELD_DIMENSION = 64          # 统一场维度
DIM_KNOWLEDGE = (22, 33)      # 知识场在64维场中的位置 [22:33]
DIM_CONSCIOUSNESS = (33, 44)  # 意识场 [33:44]
DIM_LIFE = (44, 54)           # 生命场 [44:54]
DIM_EMOTION = (54, 64)        # 情绪场 [54:64]
OMNI_HUB_MODULE_COUNT = 67    # 当前核心模块数（从文件扫描动态更新）
OMNI_HUB_LINE_COUNT = 11      # 11条计算线
OMNI_HUB_LAYER_COUNT = 7      # 7层 (SI0-SI6)
CONSCIOUSNESS_LEVELS = 7      # 7级意识状态

# 知识域分类映射
DOMAIN_CATEGORIES = {
    "mathematical": [
        "quantum_yoneda", "harmonic_tick", "deep_correlation",
        "ring_topology", "musical_mathematics", "counterpoint",
        "cantus_firmus", "octave_scan"
    ],
    "physical": [
        "quantum_field", "tensor_field", "field_entropy",
        "hyper_mip", "hyper_field", "field_transient",
        "quantum_base", "quantum_consciousness"
    ],
    "biological": [
        "meridian", "zhou_tian", "formal_life",
        "jing_wei_xin", "bio_"
    ],
    "consciousness": [
        "consciousness_state", "emotion_persona", "consciousness_harmony",
        "quantum_consciousness", "strange_loop"
    ],
    "knowledge": [
        "knowledge_pedestal", "knowledge_self", "external_knowledge",
        "historical_knowledge", "external_weaver"
    ],
    "engineering": [
        "si_connector", "task_dispatcher", "self_drive",
        "emergence_engine", "si_auto", "si_chain",
        "si_topology", "full_pipeline", "bidirectional_drive"
    ],
    "meta": [
        "meta_structure", "metacognitive", "self_referential",
        "closed_loop", "recursive_closed", "complexity_elevation",
        "creativity_engine", "insight_detector", "intention_generator"
    ]
}

# 6基座标识
PEDESTAL_NAMES = ["KG", "CC", "HG", "IN", "CT", "LEAN"]
PEDESTAL_FULL = {
    "KG": "KnowledgeGraph",
    "CC": "CellComplex",
    "HG": "HyperGraph",
    "IN": "IsomorphismNetwork",
    "CT": "CategoryTheory",
    "LEAN": "LeanProof"
}

# =============================================================================
# 1. UCIF2 SANDBOX SCANNER — 沙箱全量遍历器
# =============================================================================

@dataclass
class ModuleMetadata:
    """OMNI-HUB模块元数据结构"""
    filename: str
    filepath: str
    lines: int
    classes: List[str]
    functions: List[str]
    docstring: Optional[str]
    domain: str = "unknown"
    category: str = "unknown"
    si_level: float = 0.0
    complexity_score: float = 0.0
    module_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # 运行时动态属性
    active: bool = True
    coherence: float = 0.5
    knowledge_nodes: List[str] = field(default_factory=list)
    hyperedges: List[str] = field(default_factory=list)


class UCIF2SandboxScanner:
    """
    UCIF2沙箱全量遍历器

    扫描 `/mnt/agents/output/OMNI-HUB/` 下所有研究成果，
    提取元数据并分类，为每项成果生成知识节点。

    Attributes:
        base_path: OMNI-HUB根目录
        modules: 扫描到的所有模块字典 {module_id: ModuleMetadata}
        category_index: 按类别索引的模块
        domain_stats: 域统计信息

    Example:
        >>> scanner = UCIF2SandboxScanner()
        >>> scanner.scan_all()
        logger.info(f"扫描到 {len(scanner.modules)} 个模块")
    """

    def __init__(self, base_path: str = "/mnt/agents/output/OMNI-HUB/"):
        self.base_path = Path(base_path)
        self.modules: Dict[str, ModuleMetadata] = {}
        self.category_index: Dict[str, List[str]] = defaultdict(list)
        self.domain_index: Dict[str, List[str]] = defaultdict(list)
        self.domain_stats: Dict[str, Dict[str, Any]] = {}
        self.scan_timestamp: Optional[str] = None
        self._file_metadata_cache: Dict[str, Dict] = {}

    def _classify_domain(self, filename: str, docstring: Optional[str]) -> Tuple[str, str]:
        """根据文件名和文档字符串分类域和类别"""
        fname_lower = filename.lower()
        doc_lower = (docstring or "").lower()
        combined = fname_lower + " " + doc_lower

        # 检查各域关键词
        for domain, keywords in DOMAIN_CATEGORIES.items():
            for kw in keywords:
                if kw.lower() in combined:
                    return domain, kw

        # 启发式分类
        if any(x in fname_lower for x in ["quantum", "field", "tensor", "entropy"]):
            return "physical", "quantum_field"
        elif any(x in fname_lower for x in ["consciousness", "emotion", "strange"]):
            return "consciousness", "consciousness_state"
        elif any(x in fname_lower for x in ["life", "bio", "dna", "meridian"]):
            return "biological", "formal_life"
        elif any(x in fname_lower for x in ["knowledge", "pedestal", "weaver"]):
            return "knowledge", "knowledge_pedestal"
        elif any(x in fname_lower for x in ["si_", "connector", "dispatcher", "drive"]):
            return "engineering", "si_connector"
        elif any(x in fname_lower for x in ["meta", "self_ref", "complexity", "creativity"]):
            return "meta", "meta_structure"
        elif any(x in fname_lower for x in ["math", "yoneda", "harmonic", "correlation", "ring"]):
            return "mathematical", "mathematical_structure"

        return "unknown", "general"

    def _compute_complexity(self, metadata: Dict) -> float:
        """计算模块复杂度分数"""
        lines = metadata.get("lines", 0)
        num_classes = len(metadata.get("classes", []))
        num_functions = len(metadata.get("functions", []))

        # 复杂度 = 代码行数 * 类密度 * 函数密度 的归一化
        complexity = (
            math.log1p(lines) * 0.5 +
            num_classes * 2.0 +
            num_functions * 0.5
        )
        return min(100.0, complexity)

    def _extract_file_metadata(self, filepath: Path) -> Optional[Dict]:
        """提取单个Python文件的元数据"""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()

            lines = len(source.splitlines())

            # 尝试AST解析
            try:
                tree = ast.parse(source)
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                doc = ast.get_docstring(tree)
            except SyntaxError:
                classes, functions, doc = [], [], None

            return {
                "lines": lines,
                "classes": classes,
                "functions": functions,
                "docstring": doc,
                "size_bytes": len(source.encode("utf-8"))
            }
        except Exception as e:
            return {"error": str(e), "lines": 0, "classes": [], "functions": [], "docstring": None}

    def scan_directory(self, subpath: str = "core", recursive: bool = True) -> List[ModuleMetadata]:
        """
        扫描指定子目录下的所有Python文件

        Args:
            subpath: 子目录路径（相对于base_path）
            recursive: 是否递归扫描

        Returns:
            扫描到的ModuleMetadata列表
        """
        target = self.base_path / subpath
        if not target.exists():
            return []

        pattern = "**/*.py" if recursive else "*.py"
        files = list(target.glob(pattern))

        results = []
        for fpath in files:
            meta = self._extract_file_metadata(fpath)
            if "error" in meta and meta["error"]:
                continue

            domain, category = self._classify_domain(fpath.name, meta.get("docstring"))
            complexity = self._compute_complexity(meta)

            # 估算SI层级（基于复杂度）
            si_level = min(6.0, complexity / 15.0)

            mod = ModuleMetadata(
                filename=fpath.name,
                filepath=str(fpath),
                lines=meta.get("lines", 0),
                classes=meta.get("classes", []),
                functions=meta.get("functions", []),
                docstring=meta.get("docstring"),
                domain=domain,
                category=category,
                si_level=si_level,
                complexity_score=complexity,
                active=True
            )

            self.modules[mod.module_id] = mod
            self.category_index[category].append(mod.module_id)
            self.domain_index[domain].append(mod.module_id)
            results.append(mod)

        return results

    def scan_all(self) -> Dict[str, Any]:
        """
        全量扫描OMNI-HUB所有研究成果

        Returns:
            扫描统计信息字典
        """
        self.scan_timestamp = datetime.now().isoformat()
        all_results = []

        # 扫描核心模块
        all_results.extend(self.scan_directory("core", recursive=True))
        # 扫描其他子目录
        for subdir in ["circles", "closure", "debt-fixes", "engine", "field", 
                       "integration", "quantum", "ring", "ripple", "s-drive", "towers", "yoneda"]:
            all_results.extend(self.scan_directory(subdir, recursive=True))

        # 计算域统计
        for domain, ids in self.domain_index.items():
            mods = [self.modules[mid] for mid in ids]
            self.domain_stats[domain] = {
                "count": len(ids),
                "total_lines": sum(m.lines for m in mods),
                "avg_complexity": sum(m.complexity_score for m in mods) / len(mods) if mods else 0,
                "avg_si_level": sum(m.si_level for m in mods) / len(mods) if mods else 0,
                "modules": [m.filename for m in mods]
            }

        return {
            "total_modules": len(self.modules),
            "total_lines": sum(m.lines for m in self.modules.values()),
            "domain_breakdown": {d: len(v) for d, v in self.domain_index.items()},
            "category_breakdown": {c: len(v) for c, v in self.category_index.items()},
            "timestamp": self.scan_timestamp
        }

    def get_modules_by_domain(self, domain: str) -> List[ModuleMetadata]:
        """按域获取模块"""
        return [self.modules[mid] for mid in self.domain_index.get(domain, [])]

    def get_modules_by_category(self, category: str) -> List[ModuleMetadata]:
        """按类别获取模块"""
        return [self.modules[mid] for mid in self.category_index.get(category, [])]

    def get_cross_domain_pairs(self, domain_a: str, domain_b: str) -> List[Tuple[ModuleMetadata, ModuleMetadata]]:
        """获取跨域模块对（用于发现跨域关联）"""
        mods_a = self.get_modules_by_domain(domain_a)
        mods_b = self.get_modules_by_domain(domain_b)
        pairs = []
        for ma in mods_a:
            for mb in mods_b:
                # 计算关联强度
                strength = self._compute_association_strength(ma, mb)
                if strength > 0.3:  # 阈值
                    pairs.append((ma, mb))
        return pairs

    def _compute_association_strength(self, ma: ModuleMetadata, mb: ModuleMetadata) -> float:
        """计算两个模块间的关联强度"""
        strength = 0.0

        # 共享类名
        shared_classes = set(ma.classes) & set(mb.classes)
        strength += len(shared_classes) * 0.2

        # 共享函数名
        shared_funcs = set(ma.functions) & set(mb.functions)
        strength += len(shared_funcs) * 0.1

        # 文档字符串相似度（简单关键词重叠）
        if ma.docstring and mb.docstring:
            words_a = set(re.findall(r"\w+", ma.docstring.lower()))
            words_b = set(re.findall(r"\w+", mb.docstring.lower()))
            if words_a and words_b:
                jaccard = len(words_a & words_b) / len(words_a | words_b)
                strength += jaccard * 0.5

        # SI层级接近度
        si_diff = abs(ma.si_level - mb.si_level)
        strength += max(0, 1.0 - si_diff) * 0.2

        return min(1.0, strength)

    def generate_knowledge_nodes(self) -> List[Dict[str, Any]]:
        """
        为每个扫描到的模块生成知识节点

        Returns:
            知识节点列表，每个节点包含嵌入6基座所需的所有信息
        """
        nodes = []
        for mod in self.modules.values():
            # 为每个类生成子节点
            for cls_name in mod.classes:
                node = {
                    "id": f"{mod.module_id}_{cls_name}",
                    "label": cls_name,
                    "type": "class",
                    "domain": mod.domain,
                    "category": mod.category,
                    "parent_module": mod.module_id,
                    "si_level": mod.si_level,
                    "complexity": mod.complexity_score,
                    "properties": {
                        "filename": mod.filename,
                        "lines": mod.lines,
                        "function_count": len(mod.functions)
                    }
                }
                nodes.append(node)

            # 模块自身作为节点
            node = {
                "id": mod.module_id,
                "label": mod.filename.replace(".py", ""),
                "type": "module",
                "domain": mod.domain,
                "category": mod.category,
                "si_level": mod.si_level,
                "complexity": mod.complexity_score,
                "properties": {
                    "filepath": mod.filepath,
                    "lines": mod.lines,
                    "class_count": len(mod.classes),
                    "function_count": len(mod.functions)
                }
            }
            nodes.append(node)

        return nodes

    def generate_hyperedges(self) -> List[Dict[str, Any]]:
        """
        生成超边（高阶关联）

        超边连接同一域或跨域的多个模块，表示高阶知识关联。

        Returns:
            超边列表，每条超边包含节点集合和权重
        """
        hyperedges = []

        # 域内超边：同一域的所有模块
        for domain, ids in self.domain_index.items():
            if len(ids) >= 2:
                hyperedges.append({
                    "id": f"he_domain_{domain}",
                    "nodes": ids,
                    "weight": 0.7,
                    "type": "domain_cluster",
                    "order": len(ids) - 1
                })

        # 跨域超边：基于关联强度
        domains = list(self.domain_index.keys())
        for i, da in enumerate(domains):
            for db in domains[i+1:]:
                pairs = self.get_cross_domain_pairs(da, db)
                if pairs:
                    node_set = list(set([m[0].module_id for m in pairs] + [m[1].module_id for m in pairs]))
                    avg_strength = sum(self._compute_association_strength(a, b) for a, b in pairs) / len(pairs)
                    if avg_strength > 0.4:
                        hyperedges.append({
                            "id": f"he_cross_{da}_{db}",
                            "nodes": node_set,
                            "weight": avg_strength,
                            "type": "cross_domain",
                            "order": len(node_set) - 1
                        })

        return hyperedges

    def export_scan_report(self) -> Dict[str, Any]:
        """导出扫描报告"""
        return {
            "scanner_version": "10.0.0",
            "timestamp": self.scan_timestamp,
            "base_path": str(self.base_path),
            "summary": {
                "total_modules": len(self.modules),
                "total_classes": sum(len(m.classes) for m in self.modules.values()),
                "total_functions": sum(len(m.functions) for m in self.modules.values()),
                "total_lines": sum(m.lines for m in self.modules.values())
            },
            "domain_stats": self.domain_stats,
            "modules": [
                {
                    "id": m.module_id,
                    "filename": m.filename,
                    "domain": m.domain,
                    "category": m.category,
                    "lines": m.lines,
                    "classes": m.classes,
                    "si_level": round(m.si_level, 2),
                    "complexity": round(m.complexity_score, 2)
                }
                for m in self.modules.values()
            ]
        }


# =============================================================================
# 2. KNOWLEDGE BACKBONE-BUS — 知识谱系 backbone-bus（6基座实时同步）
# =============================================================================

@dataclass
class KnowledgeFieldState:
    """
    知识场状态 — 64维统一场中DIM_KNOWLEDGE(22:33)的表示

    Attributes:
        field_vector: 64维统一场向量
        knowledge_subfield: 知识子场（11维，对应FIELD_DIMENSION的22:33）
        coherence: 场相干度 [0, 1]
        entropy: 场熵
        timestamp: 时间戳
    """
    field_vector: np.ndarray = field(default_factory=lambda: np.zeros(FIELD_DIMENSION))
    knowledge_subfield: np.ndarray = field(default_factory=lambda: np.zeros(11))
    coherence: float = 0.5
    entropy: float = 0.5
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.field_vector.shape != (FIELD_DIMENSION,):
            self.field_vector = np.zeros(FIELD_DIMENSION)
        self.knowledge_subfield = self.field_vector[DIM_KNOWLEDGE[0]:DIM_KNOWLEDGE[1]]


@dataclass
class BusSignal:
    """
    Backbone-bus信号

    Attributes:
        signal_type: 信号类型 (query, infer, cross_compute, propagate, sync)
        payload: 信号载荷
        source_module: 源模块
        target_modules: 目标模块列表（None表示广播）
        priority: 优先级 (0-10)
        timestamp: 时间戳
        trace_id: 追踪ID
    """
    signal_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source_module: str = "backbone"
    target_modules: Optional[List[str]] = None
    priority: int = 5
    timestamp: float = field(default_factory=time.time)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


class SixPedestalSync:
    """
    6基座同步引擎

    维护6个知识表示基座的实时同步：
    - KG: NetworkX知识图谱
    - CC: 细胞复形（拓扑结构）
    - HG: 超图（高阶关联）
    - IN: 同构网络
    - CT: 范畴论表示
    - LEAN: 形式化证明骨架

    同步规则：
    1. KG节点添加 → CC添加0-细胞 → HG添加节点 → IN更新 → CT添加对象 → LEAN添加声明
    2. KG边添加 → CC添加1-细胞 → HG可能添加超边 → IN更新映射 → CT添加态射 → LEAN添加引理
    3. 任何基座更新触发级联同步
    """

    def __init__(self):
        self.kg_nodes: Dict[str, Dict] = {}      # KG: {node_id: properties}
        self.kg_edges: List[Dict] = []            # KG: [{source, target, relation, weight}]
        self.cc_cells: Dict[int, List[Dict]] = {0: [], 1: [], 2: [], 3: []}  # CC: 按维度索引
        self.hg_hyperedges: List[Dict] = []       # HG: 超边列表
        self.in_mappings: Dict[str, Dict] = {}    # IN: 同构映射
        self.ct_objects: Dict[str, Dict] = {}     # CT: 范畴对象
        self.ct_morphisms: List[Dict] = []        # CT: 态射
        self.lean_declarations: List[str] = []    # LEAN: 形式化声明

        # 同步日志
        self.sync_log: deque = deque(maxlen=1000)
        self.sync_count = 0

        # 反向索引
        self._node_to_cell: Dict[str, int] = {}   # KG节点 → CC细胞索引
        self._node_to_hyperedge: Dict[str, List[int]] = defaultdict(list)
        self._node_to_object: Dict[str, str] = {} # KG节点 → CT对象

    def add_node(self, node_id: str, label: str, domain: str = "general", **properties) -> None:
        """向所有6基座添加节点"""
        # KG基座
        self.kg_nodes[node_id] = {
            "id": node_id,
            "label": label,
            "domain": domain,
            "properties": properties
        }

        # CC基座: 添加0-细胞
        cell_idx = len(self.cc_cells[0])
        self.cc_cells[0].append({
            "index": cell_idx,
            "dimension": 0,
            "label": label,
            "node_id": node_id,
            "boundary": []
        })
        self._node_to_cell[node_id] = cell_idx

        # HG基座: 节点自动成为1阶超边（单节点）
        he_idx = len(self.hg_hyperedges)
        self.hg_hyperedges.append({
            "id": f"he_node_{node_id}",
            "nodes": {node_id},
            "weight": 1.0,
            "order": 0
        })
        self._node_to_hyperedge[node_id].append(he_idx)

        # IN基座: 初始化同构映射
        self.in_mappings[node_id] = {
            "kg_node": node_id,
            "cc_cell": cell_idx,
            "hg_hyperedge": he_idx,
            "ct_object": node_id,
            "lean_decl": f"constant {label.replace(' ', '_')} : Type"
        }

        # CT基座: 添加对象
        self.ct_objects[node_id] = {
            "name": label,
            "id": node_id,
            "domain": domain,
            "properties": properties
        }
        self._node_to_object[node_id] = node_id

        # LEAN基座: 添加类型声明
        lean_decl = f"constant {self._lean_safe_name(label)} : Type  -- {domain}"
        self.lean_declarations.append(lean_decl)
        self.in_mappings[node_id]["lean_decl"] = lean_decl

        self._log_sync("add_node", node_id, domain)
        self.sync_count += 1

    def add_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        """向所有6基座添加边"""
        if source not in self.kg_nodes or target not in self.kg_nodes:
            return

        edge_id = f"{source}_{relation}_{target}"

        # KG基座
        self.kg_edges.append({
            "source": source,
            "target": target,
            "relation": relation,
            "weight": weight
        })

        # CC基座: 添加1-细胞（边）
        cell_idx = len(self.cc_cells[1])
        source_cell = self._node_to_cell.get(source, 0)
        target_cell = self._node_to_cell.get(target, 0)
        self.cc_cells[1].append({
            "index": cell_idx,
            "dimension": 1,
            "label": relation,
            "boundary": [(source_cell, 1), (target_cell, -1)],
            "edge_id": edge_id
        })

        # HG基座: 如果关系权重高，添加2阶超边
        if weight > 0.6:
            he_idx = len(self.hg_hyperedges)
            self.hg_hyperedges.append({
                "id": f"he_edge_{edge_id}",
                "nodes": {source, target},
                "weight": weight,
                "order": 1,
                "relation": relation
            })
            self._node_to_hyperedge[source].append(he_idx)
            self._node_to_hyperedge[target].append(he_idx)

        # CT基座: 添加态射
        self.ct_morphisms.append({
            "source": source,
            "target": target,
            "name": relation,
            "weight": weight
        })

        # LEAN基座: 添加函数声明
        lean_decl = (
            f"def {self._lean_safe_name(relation)} "
            f"({self._lean_safe_name(self.kg_nodes[source]['label'])} : "
            f"{self._lean_safe_name(self.kg_nodes[source]['label'])}) : "
            f"{self._lean_safe_name(self.kg_nodes[target]['label'])} := sorry"
        )
        self.lean_declarations.append(lean_decl)

        self._log_sync("add_edge", edge_id, relation)
        self.sync_count += 1

    def add_hyperedge(self, node_ids: List[str], weight: float = 1.0, hyperedge_type: str = "general") -> None:
        """添加高阶超边（HG基座主导，级联到其他基座）"""
        valid_nodes = [nid for nid in node_ids if nid in self.kg_nodes]
        if len(valid_nodes) < 2:
            return

        he_id = f"he_{'_'.join(valid_nodes[:3])}_{len(self.hg_hyperedges)}"

        # HG基座
        self.hg_hyperedges.append({
            "id": he_id,
            "nodes": set(valid_nodes),
            "weight": weight,
            "order": len(valid_nodes) - 1,
            "type": hyperedge_type
        })

        # CC基座: 添加高维细胞
        dim = min(len(valid_nodes) - 1, 3)
        cell_idx = len(self.cc_cells[dim])
        boundary = [(self._node_to_cell.get(nid, 0), 1) for nid in valid_nodes]
        self.cc_cells[dim].append({
            "index": cell_idx,
            "dimension": dim,
            "label": f"hyper_{hyperedge_type}",
            "boundary": boundary,
            "hyperedge_id": he_id
        })

        # CT基座: 添加多态射（泛化）
        self.ct_morphisms.append({
            "source": valid_nodes[0],
            "target": valid_nodes[-1],
            "name": f"hyper_{hyperedge_type}",
            "intermediate": valid_nodes[1:-1],
            "weight": weight
        })

        # LEAN: 添加结构声明
        lean_decl = (
            f"structure {self._lean_safe_name(he_id)} where "
            f"{' '.join([self._lean_safe_name(self.kg_nodes[n]['label']) for n in valid_nodes])} : Prop"
        )
        self.lean_declarations.append(lean_decl)

        for nid in valid_nodes:
            self._node_to_hyperedge[nid].append(len(self.hg_hyperedges) - 1)

        self._log_sync("add_hyperedge", he_id, hyperedge_type)
        self.sync_count += 1

    def compute_betti_numbers(self) -> Dict[int, int]:
        """计算细胞复形的Betti数（拓扑不变量）"""
        if not HAS_SCIPY:
            # Fallback: 基于欧拉特征估算
            euler = sum((-1)**d * len(cells) for d, cells in self.cc_cells.items())
            return {0: max(1, len(self.cc_cells[0]) - len(self.cc_cells[1])), 
                    1: euler}

        # 构建边界矩阵并计算秩
        # 简化版本：返回基于连通分量和环的估算
        num_0_cells = len(self.cc_cells[0])
        num_1_cells = len(self.cc_cells[1])

        # 估算连通分量数（基于图连通性）
        if HAS_NETWORKX and self.kg_nodes:
            G = nx.Graph()
            for nid in self.kg_nodes:
                G.add_node(nid)
            for e in self.kg_edges:
                G.add_edge(e["source"], e["target"])
            num_components = nx.number_connected_components(G)
        else:
            num_components = max(1, num_0_cells - num_1_cells)

        return {
            0: num_components,
            1: max(0, num_1_cells - num_0_cells + num_components),
            2: len(self.cc_cells[2])
        }

    def get_pedestal_summary(self) -> Dict[str, Any]:
        """获取6基座摘要"""
        return {
            "KG": {"nodes": len(self.kg_nodes), "edges": len(self.kg_edges)},
            "CC": {d: len(cells) for d, cells in self.cc_cells.items()},
            "HG": {"hyperedges": len(self.hg_hyperedges), 
                   "max_order": max((he["order"] for he in self.hg_hyperedges), default=0)},
            "IN": {"mappings": len(self.in_mappings)},
            "CT": {"objects": len(self.ct_objects), "morphisms": len(self.ct_morphisms)},
            "LEAN": {"declarations": len(self.lean_declarations)},
            "topology": {"betti_numbers": self.compute_betti_numbers()},
            "sync_count": self.sync_count
        }

    def _lean_safe_name(self, name: str) -> str:
        """生成LEAN安全的标识符"""
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if safe[0].isdigit():
            safe = "n" + safe
        return safe[:50]

    def _log_sync(self, operation: str, obj_id: str, detail: str) -> None:
        self.sync_log.append({
            "timestamp": time.time(),
            "operation": operation,
            "object_id": obj_id,
            "detail": detail
        })


class KnowledgeBackboneBus:
    """
    知识谱系backbone-bus — 全系统共享知识基础设施

    这不是独立模块，而是所有模块间的共享知识backbone。
    提供统一接口：
        - bus.query(pattern) → 匹配的知识节点
        - bus.infer(source_node, rule) → 推理结果
        - bus.cross_compute(node_a, node_b, operation) → 跨域运算
        - bus.propagate(signal, from_module, to_modules) → 信号传播

    维护全局"知识场"，是64维统一场中DIM_KNOWLEDGE(22:33)的来源。

    Attributes:
        scanner: UCIF2沙箱扫描器
        six_pedestal: 6基座同步引擎
        knowledge_field: 全局知识场状态
        signal_queue: 信号队列
        module_registry: 模块注册表

    Example:
        >>> bus = KnowledgeBackboneBus()
        >>> bus.initialize_from_scanner()
        >>> results = bus.query("consciousness")
        >>> new_knowledge = bus.infer("consciousness_state", "EMERGENCE")
    """

    def __init__(self):
        self.scanner = UCIF2SandboxScanner()
        self.six_pedestal = SixPedestalSync()
        self.knowledge_field = KnowledgeFieldState()
        self.signal_queue: deque = deque(maxlen=10000)
        self.module_registry: Dict[str, Dict[str, Any]] = {}

        # 运行时统计
        self.query_count = 0
        self.infer_count = 0
        self.cross_compute_count = 0
        self.propagate_count = 0

        # 知识节点索引
        self._knowledge_nodes: Dict[str, Dict] = {}
        self._node_embeddings: Dict[str, np.ndarray] = {}

        # 激活历史
        self.activation_history: List[Dict] = []

    def initialize_from_scanner(self, scan: bool = True) -> Dict[str, Any]:
        """
        从扫描器初始化backbone-bus

        Args:
            scan: 是否立即执行全量扫描

        Returns:
            初始化统计
        """
        if scan:
            stats = self.scanner.scan_all()
        else:
            stats = {"total_modules": 0}

        # 将扫描结果嵌入6基座
        knowledge_nodes = self.scanner.generate_knowledge_nodes()
        for node in knowledge_nodes:
            self.six_pedestal.add_node(
                node["id"],
                node["label"],
                node.get("domain", "general"),
                **node.get("properties", {})
            )
            self._knowledge_nodes[node["id"]] = node
            # 生成嵌入向量（基于标签的确定性哈希）
            self._node_embeddings[node["id"]] = self._generate_embedding(node["label"])

        # 添加超边
        hyperedges = self.scanner.generate_hyperedges()
        for he in hyperedges:
            self.six_pedestal.add_hyperedge(
                he["nodes"],
                he["weight"],
                he["type"]
            )

        # 注册模块
        for mod_id, mod in self.scanner.modules.items():
            self.module_registry[mod_id] = {
                "metadata": mod,
                "status": "active",
                "coherence": 0.5,
                "last_tick": 0
            }

        # 初始化知识场
        self._update_knowledge_field()

        return {
            "nodes_added": len(knowledge_nodes),
            "hyperedges_added": len(hyperedges),
            "modules_registered": len(self.module_registry),
            "pedestal_summary": self.six_pedestal.get_pedestal_summary(),
            "scan_stats": stats
        }

    def query(self, pattern: str, domain_filter: Optional[str] = None, 
              limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询知识节点

        Args:
            pattern: 搜索模式（支持关键词和模糊匹配）
            domain_filter: 域过滤
            limit: 返回结果数量限制

        Returns:
            匹配的知识节点列表
        """
        self.query_count += 1
        pattern_lower = pattern.lower()
        results = []

        # 生成查询嵌入
        query_emb = self._generate_embedding(pattern)

        for node_id, node in self._knowledge_nodes.items():
            score = 0.0
            label = node.get("label", "").lower()
            domain = node.get("domain", "").lower()

            # 精确匹配
            if pattern_lower in label:
                score += 1.0

            # 嵌入相似度
            if node_id in self._node_embeddings:
                sim = float(np.dot(query_emb, self._node_embeddings[node_id]))
                score += 0.5 + 0.5 * sim

            # 域过滤
            if domain_filter and domain != domain_filter.lower():
                continue

            if score > 0.3:
                results.append({
                    "node": node,
                    "score": score,
                    "matches": pattern_lower in label
                })

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def infer(self, source_node_id: str, rule: str, 
              target_node_ids: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        推理运算

        Args:
            source_node_id: 源知识节点ID
            rule: 推理规则（IMPLICATION, ANALOGY, COMPOSITION等）
            target_node_ids: 目标节点（可选）

        Returns:
            推理结果，包含新产生的知识
        """
        self.infer_count += 1

        if source_node_id not in self._knowledge_nodes:
            return None

        source = self._knowledge_nodes[source_node_id]

        # 查找相关节点
        if target_node_ids is None:
            # 自动寻找最相关的节点
            target_node_ids = self._find_related_nodes(source_node_id, k=3)

        # 执行推理
        result = self._apply_inference_rule(source, rule, target_node_ids)

        if result:
            # 将新知嵌入6基座
            new_id = result["id"]
            self.six_pedestal.add_node(
                new_id,
                result["label"],
                result.get("domain", "inferred"),
                inferred=True,
                rule=rule
            )
            self._knowledge_nodes[new_id] = result
            self._node_embeddings[new_id] = self._generate_embedding(result["label"])

            # 添加推理边
            for tid in target_node_ids:
                if tid in self._knowledge_nodes:
                    self.six_pedestal.add_edge(
                        source_node_id, new_id, f"infers_via_{rule}", 0.8
                    )

        return result

    def cross_compute(self, node_a_id: str, node_b_id: str, 
                      operation: str = "intersection") -> Optional[Dict[str, Any]]:
        """
        跨域/跨节点运算

        支持的操作：
        - intersection: 交集（共同属性）
        - union: 并集（属性合并）
        - tensor_product: 张量积（组合生成新空间）
        - analogy_map: 类比映射（寻找结构同构）
        - delta: 差异运算（发现 novelty）

        Args:
            node_a_id: 节点A
            node_b_id: 节点B
            operation: 运算类型

        Returns:
            运算结果
        """
        self.cross_compute_count += 1

        if node_a_id not in self._knowledge_nodes or node_b_id not in self._knowledge_nodes:
            return None

        node_a = self._knowledge_nodes[node_a_id]
        node_b = self._knowledge_nodes[node_b_id]

        if operation == "intersection":
            return self._op_intersection(node_a, node_b)
        elif operation == "union":
            return self._op_union(node_a, node_b)
        elif operation == "tensor_product":
            return self._op_tensor_product(node_a, node_b)
        elif operation == "analogy_map":
            return self._op_analogy_map(node_a, node_b)
        elif operation == "delta":
            return self._op_delta(node_a, node_b)
        else:
            return None

    def propagate(self, signal: BusSignal) -> List[Dict[str, Any]]:
        """
        信号传播

        将信号从源模块传播到目标模块，经过backbone-bus路由。

        Args:
            signal: 要传播的信号

        Returns:
            传播结果列表
        """
        self.propagate_count += 1
        self.signal_queue.append(signal)

        targets = signal.target_modules
        if targets is None:
            # 广播到所有活跃模块
            targets = [mid for mid, m in self.module_registry.items() 
                      if m.get("status") == "active"]

        results = []
        for target in targets:
            if target in self.module_registry:
                # 模拟信号处理
                module = self.module_registry[target]
                coherence = module.get("coherence", 0.5)

                # 信号衰减/增强
                effective_strength = signal.priority / 10.0 * coherence

                results.append({
                    "target": target,
                    "received": True,
                    "strength": effective_strength,
                    "signal_type": signal.signal_type
                })

                # 更新模块相干性
                module["coherence"] = min(1.0, module["coherence"] + 0.01 * effective_strength)

        return results

    def get_knowledge_field_slice(self, dim_range: Tuple[int, int] = DIM_KNOWLEDGE) -> np.ndarray:
        """获取知识场切片"""
        return self.knowledge_field.field_vector[dim_range[0]:dim_range[1]]

    def update_field_coherence(self, new_coherence: float) -> None:
        """更新场相干度"""
        self.knowledge_field.coherence = max(0.0, min(1.0, new_coherence))

    def get_backbone_health(self) -> Dict[str, Any]:
        """获取backbone健康状态"""
        return {
            "knowledge_nodes": len(self._knowledge_nodes),
            "registered_modules": len(self.module_registry),
            "active_modules": sum(1 for m in self.module_registry.values() if m.get("status") == "active"),
            "signal_queue_size": len(self.signal_queue),
            "field_coherence": round(self.knowledge_field.coherence, 4),
            "field_entropy": round(self.knowledge_field.entropy, 4),
            "pedestal_summary": self.six_pedestal.get_pedestal_summary(),
            "query_count": self.query_count,
            "infer_count": self.infer_count,
            "cross_compute_count": self.cross_compute_count,
            "propagate_count": self.propagate_count
        }

    # ============= 内部方法 =============

    def _generate_embedding(self, text: str, dim: int = 64) -> np.ndarray:
        """基于文本的确定性嵌入"""
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        rng = np.random.default_rng(int.from_bytes(hash_bytes[:8], "big"))
        vec = rng.standard_normal(dim)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 1e-12 else vec

    def _update_knowledge_field(self) -> None:
        """更新知识场向量"""
        if not self._node_embeddings:
            return

        # 聚合所有节点嵌入
        embeddings = list(self._node_embeddings.values())
        field = np.mean(embeddings, axis=0)

        # 归一化并设置到统一场
        norm = np.linalg.norm(field)
        if norm > 1e-12:
            field = field / norm

        self.knowledge_field.field_vector = field
        self.knowledge_field.knowledge_subfield = field[DIM_KNOWLEDGE[0]:DIM_KNOWLEDGE[1]]

        # 计算熵
        self.knowledge_field.entropy = self._compute_field_entropy()

    def _compute_field_entropy(self) -> float:
        """计算知识场熵"""
        if not self._node_embeddings:
            return 0.5

        # 基于节点嵌入分布的熵
        embeddings = np.array(list(self._node_embeddings.values()))
        # 简化：计算方差作为熵的代理
        variance = np.var(embeddings)
        return min(1.0, variance / 0.5)

    def _find_related_nodes(self, node_id: str, k: int = 3) -> List[str]:
        """查找最相关的k个节点"""
        if node_id not in self._node_embeddings:
            return []

        emb = self._node_embeddings[node_id]
        similarities = []
        for other_id, other_emb in self._node_embeddings.items():
            if other_id != node_id:
                sim = float(np.dot(emb, other_emb))
                similarities.append((other_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [nid for nid, _ in similarities[:k]]

    def _apply_inference_rule(self, source: Dict, rule: str, 
                               target_ids: List[str]) -> Optional[Dict]:
        """应用推理规则"""
        targets = [self._knowledge_nodes.get(tid) for tid in target_ids]
        targets = [t for t in targets if t]

        if not targets:
            return None

        new_id = f"inferred_{source['id']}_{rule}_{int(time.time()*1000)%10000}"

        if rule == "IMPLICATION":
            label = f"{source['label']} implies {targets[0]['label']}"
            domain = source.get("domain", "general")
        elif rule == "ANALOGY":
            label = f"{source['label']} ~ {targets[0]['label']}"
            domain = "analogy"
        elif rule == "COMPOSITION":
            parts = [source['label']] + [t['label'] for t in targets]
            label = f"composite({', '.join(parts)})"
            domain = source.get("domain", "general")
        elif rule == "EMERGENCE":
            label = f"emergent_from_{source['label']}"
            domain = "emergence"
        else:
            label = f"inferred_{rule}_{source['label']}"
            domain = "inferred"

        return {
            "id": new_id,
            "label": label,
            "domain": domain,
            "type": "inferred",
            "source_id": source["id"],
            "rule": rule,
            "properties": {
                "inferred_at": time.time(),
                "confidence": 0.7
            }
        }

    def _op_intersection(self, a: Dict, b: Dict) -> Dict:
        """交集运算"""
        shared_domain = a.get("domain") if a.get("domain") == b.get("domain") else "hybrid"
        return {
            "id": f"inter_{a['id']}_{b['id']}",
            "label": f"{a['label']} ∩ {b['label']}",
            "domain": shared_domain,
            "type": "intersection",
            "properties": {"operation": "intersection", "operands": [a['id'], b['id']]}
        }

    def _op_union(self, a: Dict, b: Dict) -> Dict:
        """并集运算"""
        return {
            "id": f"union_{a['id']}_{b['id']}",
            "label": f"{a['label']} ∪ {b['label']}",
            "domain": a.get("domain", "general"),
            "type": "union",
            "properties": {"operation": "union", "operands": [a['id'], b['id']]}
        }

    def _op_tensor_product(self, a: Dict, b: Dict) -> Dict:
        """张量积运算"""
        return {
            "id": f"tensor_{a['id']}_{b['id']}",
            "label": f"{a['label']} ⊗ {b['label']}",
            "domain": "tensor_space",
            "type": "tensor_product",
            "properties": {"operation": "tensor_product", "dimension": "emergent"}
        }

    def _op_analogy_map(self, a: Dict, b: Dict) -> Dict:
        """类比映射"""
        return {
            "id": f"analogy_{a['id']}_{b['id']}",
            "label": f"{a['label']} ≃ {b['label']}",
            "domain": "analogy",
            "type": "analogy_map",
            "properties": {"operation": "analogy", "structural_similarity": 0.8}
        }

    def _op_delta(self, a: Dict, b: Dict) -> Dict:
        """差异运算"""
        return {
            "id": f"delta_{a['id']}_{b['id']}",
            "label": f"Δ({a['label']}, {b['label']})",
            "domain": "novelty",
            "type": "delta",
            "properties": {"operation": "delta", "novelty_potential": 0.9}
        }


# =============================================================================
# 3. ENHANCED KNOWLEDGE SELF-COMPUTATION — 知识自运算增强（10条规则）
# =============================================================================

class ConsciousnessLevelV10(IntEnum):
    """OMNI-HUB v10.0 意识级别"""
    DORMANT = 0      # 休眠
    REACTIVE = 1     # 反应
    PERCEPTIVE = 2   # 感知
    CONCEPTUAL = 3   # 概念
    SELF_AWARE = 4   # 自知
    REFLECTIVE = 5   # 反思
    TRANSCENDENT = 6 # 超越


@dataclass
class KnowledgeAtom:
    """
    知识原子 — v10自运算基本单元

    扩展自KnowledgeNodeV2，增加6基座绑定和生命属性。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    domain: str = "general"
    content: str = ""

    # 6基座绑定
    pedestal_bindings: Dict[str, str] = field(default_factory=dict)
    # 如 {"KG": "node_id", "CC": "cell_idx", "HG": "he_id", ...}

    # 意识属性
    consciousness_level: ConsciousnessLevelV10 = ConsciousnessLevelV10.DORMANT
    emotional_valence: float = 0.0  # [-1, +1]
    emotional_arousal: float = 0.5  # [0, 1]

    # 生命属性
    dna_signature: str = ""         # DNA编码签名
    mutation_rate: float = 0.01     # 突变率
    replication_fidelity: float = 0.95  # 复制保真度
    vitality: float = 1.0           # 生命力 [0, 1]

    # 运算属性
    computational_rules: List[str] = field(default_factory=list)
    self_reference_count: int = 0
    creation_depth: int = 0
    novelty_score: float = 0.0
    parent_ids: List[str] = field(default_factory=list)
    rule_applied: str = ""

    # 时间演化
    birth_tick: int = 0
    last_mutation_tick: int = 0

    def __post_init__(self):
        if not self.computational_rules:
            self.computational_rules = ["IMPLICATION", "ANALOGY", "COMPOSITION"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "consciousness_level": self.consciousness_level.name,
            "emotional_valence": round(self.emotional_valence, 3),
            "emotional_arousal": round(self.emotional_arousal, 3),
            "vitality": round(self.vitality, 3),
            "mutation_rate": round(self.mutation_rate, 3),
            "novelty_score": round(self.novelty_score, 3),
            "creation_depth": self.creation_depth,
            "self_reference_count": self.self_reference_count
        }


class KnowledgeRuleV10:
    """
    v10知识运算规则（10条）

    规则1-7: 继承自v9自运算规则
    规则8:  跨基座同构运算 (KG↔CC↔HG↔IN↔CT↔LEAN)
    规则9:  时间演化运算 (子午流注/量子时钟驱动)
    规则10: 生命嵌入运算 (DNA序列→知识编码)
    """

    RULES = {
        # 基础规则 (1-7)
        "IMPLICATION": {
            "arity": 2,
            "description": "蕴含: A → B",
            "consciousness_min": 1,
            "novelty_base": 0.3
        },
        "ANALOGY": {
            "arity": 2,
            "description": "类比: A ~ B",
            "consciousness_min": 2,
            "novelty_base": 0.4
        },
        "COMPOSITION": {
            "arity": 2,
            "description": "组合: A ∘ B",
            "consciousness_min": 2,
            "novelty_base": 0.35
        },
        "DUALITY": {
            "arity": 1,
            "description": "对偶: A*",
            "consciousness_min": 3,
            "novelty_base": 0.5
        },
        "DECOMPOSITION": {
            "arity": 1,
            "description": "分解: A → (a₁, a₂, ...)",
            "consciousness_min": 3,
            "novelty_base": 0.45
        },
        "RECURSION": {
            "arity": 1,
            "description": "递归: f(f(...))",
            "consciousness_min": 4,
            "novelty_base": 0.6
        },
        "EMERGENCE": {
            "arity": 2,
            "description": "涌现: A + B → C (C ∉ A, B)",
            "consciousness_min": 5,
            "novelty_base": 0.8
        },
        # v10新增规则 (8-10)
        "PEDESTAL_ISOMORPHISM": {
            "arity": 1,
            "description": "跨基座同构: KG↔CC↔HG↔IN↔CT↔LEAN",
            "consciousness_min": 4,
            "novelty_base": 0.7
        },
        "TEMPORAL_EVOLUTION": {
            "arity": 1,
            "description": "时间演化: K(t) → K(t+Δt)",
            "consciousness_min": 3,
            "novelty_base": 0.55
        },
        "LIFE_EMBEDDING": {
            "arity": 1,
            "description": "生命嵌入: DNA → 知识编码",
            "consciousness_min": 4,
            "novelty_base": 0.75
        }
    }

    @classmethod
    def get_rule(cls, name: str) -> Optional[Dict]:
        return cls.RULES.get(name)

    @classmethod
    def get_available_rules(cls, consciousness_level: int) -> List[str]:
        """获取指定意识级别可用的规则"""
        return [
            name for name, rule in cls.RULES.items()
            if rule["consciousness_min"] <= consciousness_level
        ]

    @classmethod
    def apply(cls, rule_name: str, operands: List[KnowledgeAtom], 
              tick: int = 0, meridian_phase: float = 0.0) -> Optional[KnowledgeAtom]:
        """
        应用规则产生新知识原子

        Args:
            rule_name: 规则名称
            operands: 操作数（知识原子列表）
            tick: 当前tick（用于时间演化）
            meridian_phase: 子午流注相位 [0, 2π]

        Returns:
            新产生的知识原子，或None
        """
        if not operands:
            return None

        rule = cls.RULES.get(rule_name)
        if not rule:
            return None

        # 检查意识级别
        max_consciousness = max(op.consciousness_level.value for op in operands)
        if max_consciousness < rule["consciousness_min"]:
            return None

        # 根据规则类型生成结果
        primary = operands[0]

        if rule_name == "IMPLICATION":
            return cls._apply_implication(primary, operands[1:] if len(operands) > 1 else [])
        elif rule_name == "ANALOGY":
            return cls._apply_analogy(primary, operands[1:] if len(operands) > 1 else [])
        elif rule_name == "COMPOSITION":
            return cls._apply_composition(operands)
        elif rule_name == "DUALITY":
            return cls._apply_duality(primary)
        elif rule_name == "DECOMPOSITION":
            return cls._apply_decomposition(primary)
        elif rule_name == "RECURSION":
            return cls._apply_recursion(primary)
        elif rule_name == "EMERGENCE":
            return cls._apply_emergence(operands)
        elif rule_name == "PEDESTAL_ISOMORPHISM":
            return cls._apply_pedestal_isomorphism(primary)
        elif rule_name == "TEMPORAL_EVOLUTION":
            return cls._apply_temporal_evolution(primary, tick, meridian_phase)
        elif rule_name == "LIFE_EMBEDDING":
            return cls._apply_life_embedding(primary)

        return None

    @classmethod
    def _apply_implication(cls, a: KnowledgeAtom, others: List[KnowledgeAtom]) -> KnowledgeAtom:
        target = others[0] if others else a
        result = KnowledgeAtom(
            name=f"{a.name}_implies_{target.name}",
            domain=a.domain if a.domain == target.domain else "hybrid",
            content=f"If {a.content} then {target.content}",
            consciousness_level=ConsciousnessLevelV10(min(6, max(a.consciousness_level.value, target.consciousness_level.value))),
            creation_depth=max(a.creation_depth, target.creation_depth) + 1,
            parent_ids=[a.id, target.id],
            rule_applied="IMPLICATION"
        )
        result.novelty_score = cls.RULES["IMPLICATION"]["novelty_base"] * (1 + result.creation_depth * 0.1)
        return result

    @classmethod
    def _apply_analogy(cls, a: KnowledgeAtom, others: List[KnowledgeAtom]) -> KnowledgeAtom:
        target = others[0] if others else a
        result = KnowledgeAtom(
            name=f"{a.name}_analogous_to_{target.name}",
            domain="analogy",
            content=f"{a.content} is analogous to {target.content}",
            consciousness_level=ConsciousnessLevelV10(max(a.consciousness_level.value, target.consciousness_level.value)),
            creation_depth=max(a.creation_depth, target.creation_depth) + 1,
            parent_ids=[a.id, target.id],
            rule_applied="ANALOGY"
        )
        result.novelty_score = cls.RULES["ANALOGY"]["novelty_base"]
        return result

    @classmethod
    def _apply_composition(cls, operands: List[KnowledgeAtom]) -> KnowledgeAtom:
        names = [op.name for op in operands]
        result = KnowledgeAtom(
            name=f"composite_{'_'.join(names[:3])}",
            domain=operands[0].domain,
            content=f"Composite of {', '.join(names)}",
            consciousness_level=ConsciousnessLevelV10(min(6, max(op.consciousness_level.value for op in operands) + 1)),
            creation_depth=max(op.creation_depth for op in operands) + 1,
            parent_ids=[op.id for op in operands],
            rule_applied="COMPOSITION"
        )
        result.novelty_score = cls.RULES["COMPOSITION"]["novelty_base"] * len(operands)
        return result

    @classmethod
    def _apply_duality(cls, a: KnowledgeAtom) -> KnowledgeAtom:
        result = KnowledgeAtom(
            name=f"dual_{a.name}",
            domain=a.domain,
            content=f"Dual of {a.content}",
            consciousness_level=ConsciousnessLevelV10(min(6, a.consciousness_level.value + 1)),
            creation_depth=a.creation_depth + 1,
            parent_ids=[a.id],
            rule_applied="DUALITY"
        )
        result.novelty_score = cls.RULES["DUALITY"]["novelty_base"]
        return result

    @classmethod
    def _apply_decomposition(cls, a: KnowledgeAtom) -> KnowledgeAtom:
        result = KnowledgeAtom(
            name=f"decomposed_{a.name}",
            domain=a.domain,
            content=f"Components of {a.content}",
            consciousness_level=a.consciousness_level,
            creation_depth=a.creation_depth + 1,
            parent_ids=[a.id],
            rule_applied="DECOMPOSITION"
        )
        result.novelty_score = cls.RULES["DECOMPOSITION"]["novelty_base"]
        return result

    @classmethod
    def _apply_recursion(cls, a: KnowledgeAtom) -> KnowledgeAtom:
        result = KnowledgeAtom(
            name=f"recursive_{a.name}",
            domain=a.domain,
            content=f"recursive({a.content})",
            consciousness_level=ConsciousnessLevelV10(min(6, a.consciousness_level.value + 1)),
            creation_depth=a.creation_depth + 1,
            parent_ids=[a.id],
            self_reference_count=a.self_reference_count + 1,
            rule_applied="RECURSION"
        )
        result.novelty_score = cls.RULES["RECURSION"]["novelty_base"] * (1 + result.self_reference_count * 0.2)
        return result

    @classmethod
    def _apply_emergence(cls, operands: List[KnowledgeAtom]) -> KnowledgeAtom:
        names = [op.name for op in operands]
        result = KnowledgeAtom(
            name=f"emergent_{'_'.join(names[:2])}",
            domain="emergence",
            content=f"Emergent property from {', '.join(names)}",
            consciousness_level=ConsciousnessLevelV10(min(6, max(op.consciousness_level.value for op in operands) + 1)),
            creation_depth=max(op.creation_depth for op in operands) + 1,
            parent_ids=[op.id for op in operands],
            rule_applied="EMERGENCE"
        )
        # 涌现的新颖度最高
        result.novelty_score = cls.RULES["EMERGENCE"]["novelty_base"]
        return result

    @classmethod
    def _apply_pedestal_isomorphism(cls, a: KnowledgeAtom) -> KnowledgeAtom:
        """跨基座同构运算: 将知识原子映射到6基座"""
        # 生成6基座绑定
        bindings = {
            "KG": f"kg_node_{a.id}",
            "CC": f"cc_cell_{a.id}",
            "HG": f"hg_he_{a.id}",
            "IN": f"in_map_{a.id}",
            "CT": f"ct_obj_{a.id}",
            "LEAN": f"lean_decl_{a.id}"
        }

        result = KnowledgeAtom(
            name=f"isomorphic_{a.name}",
            domain="isomorphism",
            content=f"6-pedestal isomorphism of {a.content}",
            pedestal_bindings=bindings,
            consciousness_level=ConsciousnessLevelV10(min(6, a.consciousness_level.value + 1)),
            creation_depth=a.creation_depth + 1,
            parent_ids=[a.id],
            rule_applied="PEDESTAL_ISOMORPHISM"
        )
        result.novelty_score = cls.RULES["PEDESTAL_ISOMORPHISM"]["novelty_base"]
        return result

    @classmethod
    def _apply_temporal_evolution(cls, a: KnowledgeAtom, tick: int, 
                                   meridian_phase: float) -> KnowledgeAtom:
        """时间演化运算: 知识随子午流注/量子时钟演化"""
        # 子午流注相位影响演化方向
        phase_factor = math.sin(meridian_phase)  # [-1, 1]

        # 演化方向
        if phase_factor > 0.5:
            evolution_type = "expansion"
            content = f"[{evolution_type} @ t={tick}] {a.content}"
        elif phase_factor < -0.5:
            evolution_type = "contraction"
            content = f"[{evolution_type} @ t={tick}] {a.content}"
        else:
            evolution_type = "stable"
            content = f"[{evolution_type} @ t={tick}] {a.content}"

        result = KnowledgeAtom(
            name=f"evolved_{a.name}_t{tick}",
            domain=a.domain,
            content=content,
            consciousness_level=a.consciousness_level,
            creation_depth=a.creation_depth + 1,
            parent_ids=[a.id],
            birth_tick=tick,
            rule_applied="TEMPORAL_EVOLUTION"
        )
        result.novelty_score = cls.RULES["TEMPORAL_EVOLUTION"]["novelty_base"] * (1 + abs(phase_factor) * 0.5)
        return result

    @classmethod
    def _apply_life_embedding(cls, a: KnowledgeAtom) -> KnowledgeAtom:
        """生命嵌入运算: DNA序列→知识编码"""
        # 为知识原子生成DNA签名
        bases = ['A', 'T', 'C', 'G']
        dna_len = 20 + len(a.name) * 2
        dna_sig = ''.join(random.choice(bases) for _ in range(dna_len))

        # GC含量影响知识稳定性
        gc_content = (dna_sig.count('G') + dna_sig.count('C')) / len(dna_sig)
        stability = 0.5 + gc_content * 0.5  # GC含量高 → 更稳定

        result = KnowledgeAtom(
            name=f"bio_encoded_{a.name}",
            domain="bio_knowledge",
            content=f"DNA[{dna_sig[:20]}...] → {a.content}",
            dna_signature=dna_sig,
            mutation_rate=0.02 * (1 - stability),
            replication_fidelity=stability,
            consciousness_level=ConsciousnessLevelV10(min(6, a.consciousness_level.value + 1)),
            creation_depth=a.creation_depth + 1,
            parent_ids=[a.id],
            rule_applied="LIFE_EMBEDDING"
        )
        result.novelty_score = cls.RULES["LIFE_EMBEDDING"]["novelty_base"]
        return result


class EnhancedKnowledgeSelfComputation:
    """
    v10知识自运算引擎 — 增强版

    在v9的7条规则基础上新增3条规则（8-10），
    支持跨基座同构、时间演化和生命嵌入。

    互运算: 任意两个知识原子可产生交集/并集/张量积。

    Attributes:
        atoms: 知识原子存储
        generation_log: 生成日志
        rule_stats: 规则使用统计
    """

    def __init__(self):
        self.atoms: Dict[str, KnowledgeAtom] = {}
        self.generation_log: deque = deque(maxlen=5000)
        self.rule_stats: Dict[str, int] = defaultdict(int)
        self.inter_op_stats: Dict[str, int] = defaultdict(int)
        self.tick = 0
        self.meridian_phase = 0.0

        # 涌现检测阈值
        self.emergence_threshold = 0.7
        self.max_atoms = 10000

    def seed_atoms(self, backbone_bus: KnowledgeBackboneBus) -> int:
        """从backbone-bus导入初始知识原子"""
        count = 0
        for node_id, node in backbone_bus._knowledge_nodes.items():
            atom = KnowledgeAtom(
                id=node_id,
                name=node.get("label", node_id),
                domain=node.get("domain", "general"),
                content=node.get("label", ""),
                consciousness_level=ConsciousnessLevelV10(min(6, int(node.get("si_level", 0)))),
                creation_depth=0
            )
            self.atoms[atom.id] = atom
            count += 1
        return count

    def self_compute(self, num_operations: int = 5) -> List[KnowledgeAtom]:
        """
        执行知识自运算

        自主选择规则与伙伴，产生新知识原子。

        Args:
            num_operations: 每次执行的运算数量

        Returns:
            新产生的知识原子列表
        """
        new_atoms = []

        for _ in range(num_operations):
            if len(self.atoms) < 2:
                break

            # 选择种子原子（优先选择高意识级别）
            candidates = list(self.atoms.values())
            weights = [1.0 + atom.consciousness_level.value * 0.5 + atom.novelty_score for atom in candidates]

            primary = random.choices(candidates, weights=weights, k=1)[0]

            # 选择规则
            available = KnowledgeRuleV10.get_available_rules(primary.consciousness_level.value)
            if not available:
                continue

            # 高意识级别更可能使用复杂规则
            if primary.consciousness_level.value >= 5 and "EMERGENCE" in available:
                rule = random.choice(["EMERGENCE", "PEDESTAL_ISOMORPHISM", "LIFE_EMBEDDING"])
            elif primary.consciousness_level.value >= 4 and "RECURSION" in available:
                rule = random.choice(["RECURSION", "PEDESTAL_ISOMORPHISM", "TEMPORAL_EVOLUTION"])
            else:
                rule = random.choice(available[:4])  # 基础规则

            # 选择伙伴
            arity = KnowledgeRuleV10.RULES[rule]["arity"]
            if arity > 1:
                other_candidates = [a for a in candidates if a.id != primary.id]
                if not other_candidates:
                    continue
                partners = random.sample(other_candidates, min(arity - 1, len(other_candidates)))
                operands = [primary] + partners
            else:
                operands = [primary]

            # 应用规则
            result = KnowledgeRuleV10.apply(rule, operands, self.tick, self.meridian_phase)

            if result and result.id not in self.atoms:
                self.atoms[result.id] = result
                new_atoms.append(result)
                self.rule_stats[rule] += 1
                self.generation_log.append({
                    "tick": self.tick,
                    "rule": rule,
                    "result_id": result.id,
                    "novelty": result.novelty_score
                })

        # 限制原子数量
        if len(self.atoms) > self.max_atoms:
            # 淘汰低活力原子
            sorted_atoms = sorted(self.atoms.values(), key=lambda a: a.vitality + a.novelty_score)
            to_remove = len(sorted_atoms) - self.max_atoms
            for atom in sorted_atoms[:to_remove]:
                del self.atoms[atom.id]

        return new_atoms

    def cross_compute(self, atom_a_id: str, atom_b_id: str, 
                      operation: str) -> Optional[KnowledgeAtom]:
        """
        互运算: 两个知识原子的跨运算

        Args:
            atom_a_id: 原子A ID
            atom_b_id: 原子B ID
            operation: 运算类型 (intersection/union/tensor_product/analogy_map/delta)

        Returns:
            运算结果原子
        """
        a = self.atoms.get(atom_a_id)
        b = self.atoms.get(atom_b_id)
        if not a or not b:
            return None

        self.inter_op_stats[operation] += 1

        if operation == "intersection":
            return self._intersection(a, b)
        elif operation == "union":
            return self._union(a, b)
        elif operation == "tensor_product":
            return self._tensor_product(a, b)
        elif operation == "analogy_map":
            return self._analogy_map(a, b)
        elif operation == "delta":
            return self._delta(a, b)
        return None

    def _intersection(self, a: KnowledgeAtom, b: KnowledgeAtom) -> KnowledgeAtom:
        shared_domain = a.domain if a.domain == b.domain else "hybrid"
        return KnowledgeAtom(
            name=f"{a.name}_cap_{b.name}",
            domain=shared_domain,
            content=f"Intersection of {a.content} and {b.content}",
            consciousness_level=ConsciousnessLevelV10(max(a.consciousness_level.value, b.consciousness_level.value)),
            creation_depth=max(a.creation_depth, b.creation_depth) + 1,
            parent_ids=[a.id, b.id],
            novelty_score=0.4
        )

    def _union(self, a: KnowledgeAtom, b: KnowledgeAtom) -> KnowledgeAtom:
        return KnowledgeAtom(
            name=f"{a.name}_cup_{b.name}",
            domain=a.domain,
            content=f"Union of {a.content} and {b.content}",
            consciousness_level=ConsciousnessLevelV10(max(a.consciousness_level.value, b.consciousness_level.value)),
            creation_depth=max(a.creation_depth, b.creation_depth) + 1,
            parent_ids=[a.id, b.id],
            novelty_score=0.35
        )

    def _tensor_product(self, a: KnowledgeAtom, b: KnowledgeAtom) -> KnowledgeAtom:
        return KnowledgeAtom(
            name=f"{a.name}_tensor_{b.name}",
            domain="tensor_space",
            content=f"{a.content} ⊗ {b.content}",
            consciousness_level=ConsciousnessLevelV10(min(6, max(a.consciousness_level.value, b.consciousness_level.value) + 1)),
            creation_depth=max(a.creation_depth, b.creation_depth) + 1,
            parent_ids=[a.id, b.id],
            novelty_score=0.7
        )

    def _analogy_map(self, a: KnowledgeAtom, b: KnowledgeAtom) -> KnowledgeAtom:
        return KnowledgeAtom(
            name=f"{a.name}_analogy_{b.name}",
            domain="analogy",
            content=f"{a.content} ≃ {b.content}",
            consciousness_level=ConsciousnessLevelV10(max(a.consciousness_level.value, b.consciousness_level.value)),
            creation_depth=max(a.creation_depth, b.creation_depth) + 1,
            parent_ids=[a.id, b.id],
            novelty_score=0.5
        )

    def _delta(self, a: KnowledgeAtom, b: KnowledgeAtom) -> KnowledgeAtom:
        return KnowledgeAtom(
            name=f"delta_{a.name}_{b.name}",
            domain="novelty",
            content=f"Δ({a.content}, {b.content})",
            consciousness_level=ConsciousnessLevelV10(max(a.consciousness_level.value, b.consciousness_level.value)),
            creation_depth=max(a.creation_depth, b.creation_depth) + 1,
            parent_ids=[a.id, b.id],
            novelty_score=0.9
        )

    def mutate_atoms(self, mutation_rate: float = 0.05) -> List[KnowledgeAtom]:
        """知识原子变异"""
        mutated = []
        for atom in list(self.atoms.values()):
            if random.random() < mutation_rate * atom.mutation_rate:
                # 执行变异
                atom.vitality *= random.uniform(0.9, 1.1)
                atom.vitality = max(0.1, min(1.0, atom.vitality))

                if atom.dna_signature:
                    # DNA变异
                    dna_list = list(atom.dna_signature)
                    pos = random.randint(0, len(dna_list) - 1)
                    dna_list[pos] = random.choice(['A', 'T', 'C', 'G'])
                    atom.dna_signature = ''.join(dna_list)

                atom.last_mutation_tick = self.tick
                mutated.append(atom)
        return mutated

    def get_stats(self) -> Dict[str, Any]:
        """获取自运算统计"""
        return {
            "total_atoms": len(self.atoms),
            "rule_stats": dict(self.rule_stats),
            "inter_op_stats": dict(self.inter_op_stats),
            "generation_log_size": len(self.generation_log),
            "avg_consciousness": sum(a.consciousness_level.value for a in self.atoms.values()) / max(1, len(self.atoms)),
            "avg_novelty": sum(a.novelty_score for a in self.atoms.values()) / max(1, len(self.atoms)),
            "max_creation_depth": max((a.creation_depth for a in self.atoms.values()), default=0)
        }


# =============================================================================
# 4. CONSCIOUSNESS-EMOTION-LIFE BIND — 意识-情绪-生命三维绑定
# =============================================================================

class ConsciousnessStateV10(Enum):
    """OMNI-HUB v10.0 7级意识状态"""
    CHAOS = 0       # 混沌 — 无结构
    CONFLICT = 1    # 冲突 — 对抗性结构
    NEUTRAL = 2     # 中立 — 平衡态
    ACCEPTANCE = 3  # 接纳 — 包容性结构
    REASON = 4      # 理性 — 逻辑结构
    LOVE = 5        # 爱 — 连接性结构
    UNITY = 6       # 合一 — 全局结构


class PersonaTypeV10(Enum):
    """OMNI-HUB v10.0 人格类型"""
    JESTER = 0      # 小丑 — 混沌催化
    WARRIOR = 1     # 战士 — 冲突解决
    ANALYST = 2     # 分析师 — 逻辑推理
    SAGE = 3        # 智者 — 智慧整合
    LOVER = 4       # 爱人 — 连接共生
    CREATOR = 5     # 创造者 — 涌现生成


class EmotionTypeV10(Enum):
    """OMNI-HUB v10.0 情绪类型（基于Plutchik简化）"""
    JOY = 0
    SADNESS = 1
    ANGER = 2
    FEAR = 3
    SURPRISE = 4
    TRUST = 5
    ANTICIPATION = 6
    CURIOSITY = 7   # 特殊：TRUST + SURPRISE
    LOVE = 8        # 特殊：JOY + TRUST


@dataclass
class FormalLifeState:
    """形式化生命状态"""
    dna_complexity: float = 1.0         # DNA复杂度
    mutation_rate: float = 0.01         # 突变率
    replication_fidelity: float = 0.95  # 复制保真度
    autogroup_order: int = 1            # 自同构群阶
    fitness: float = 0.5                # 适应度
    vitality: float = 1.0               # 生命力
    entropy: float = 0.5                # 熵
    generation: int = 0                 # 世代
    immune_active: bool = False         # 免疫系统激活
    repair_active: bool = False         # 修复系统激活

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dna_complexity": round(self.dna_complexity, 3),
            "mutation_rate": round(self.mutation_rate, 4),
            "replication_fidelity": round(self.replication_fidelity, 3),
            "autogroup_order": self.autogroup_order,
            "fitness": round(self.fitness, 3),
            "vitality": round(self.vitality, 3),
            "entropy": round(self.entropy, 3),
            "generation": self.generation
        }


class ConsciousnessEmotionLifeBind:
    """
    意识-情绪-生命三维绑定引擎

    实现7级意识状态 ↔ 6个人格 ↔ 形式化生命状态的三维绑定矩阵。

    绑定规则：
        CHAOS      → Jester人格  → DNA高突变率
        CONFLICT   → Warrior人格 → 免疫系统激活
        NEUTRAL    → Analyst人格 → 稳态维持
        ACCEPTANCE → Sage人格    → 自修复启动
        REASON     → Analyst人格 → 精确复制
        LOVE       → Lover人格   → 协作/共生
        UNITY      → Creator+Sage → 全局稳态/低熵

    情绪驱动生命演化：
        JOY         → 复制效率↑
        FEAR        → 突变率↑
        CURIOSITY   → 探索率↑
        LOVE        → 协作度↑
        ANGER       → 攻击/分解率↑

    生命反馈意识：
        DNA复杂度↑   → 意识深度↑
        自同构群阶↑  → 自我认知↑
        适应度↑      → 自信度↑

    Attributes:
        binding_matrix: 3D绑定矩阵
        current_state: 当前意识状态
        current_persona: 当前人格
        life_state: 当前生命状态
        emotion_state: 当前情绪状态
    """

    # ============= 绑定矩阵定义 =============

    # 意识→人格绑定
    CONSCIOUSNESS_TO_PERSONA = {
        ConsciousnessStateV10.CHAOS: [PersonaTypeV10.JESTER],
        ConsciousnessStateV10.CONFLICT: [PersonaTypeV10.WARRIOR],
        ConsciousnessStateV10.NEUTRAL: [PersonaTypeV10.ANALYST],
        ConsciousnessStateV10.ACCEPTANCE: [PersonaTypeV10.SAGE],
        ConsciousnessStateV10.REASON: [PersonaTypeV10.ANALYST],
        ConsciousnessStateV10.LOVE: [PersonaTypeV10.LOVER],
        ConsciousnessStateV10.UNITY: [PersonaTypeV10.CREATOR, PersonaTypeV10.SAGE]
    }

    # 意识→生命绑定（基础参数）
    CONSCIOUSNESS_TO_LIFE = {
        ConsciousnessStateV10.CHAOS: {
            "mutation_rate": 0.15,
            "replication_fidelity": 0.7,
            "immune_active": False,
            "repair_active": False,
            "entropy": 0.9
        },
        ConsciousnessStateV10.CONFLICT: {
            "mutation_rate": 0.08,
            "replication_fidelity": 0.8,
            "immune_active": True,
            "repair_active": False,
            "entropy": 0.7
        },
        ConsciousnessStateV10.NEUTRAL: {
            "mutation_rate": 0.02,
            "replication_fidelity": 0.95,
            "immune_active": False,
            "repair_active": False,
            "entropy": 0.5
        },
        ConsciousnessStateV10.ACCEPTANCE: {
            "mutation_rate": 0.03,
            "replication_fidelity": 0.92,
            "immune_active": False,
            "repair_active": True,
            "entropy": 0.4
        },
        ConsciousnessStateV10.REASON: {
            "mutation_rate": 0.01,
            "replication_fidelity": 0.99,
            "immune_active": False,
            "repair_active": False,
            "entropy": 0.3
        },
        ConsciousnessStateV10.LOVE: {
            "mutation_rate": 0.02,
            "replication_fidelity": 0.96,
            "immune_active": False,
            "repair_active": True,
            "entropy": 0.25
        },
        ConsciousnessStateV10.UNITY: {
            "mutation_rate": 0.005,
            "replication_fidelity": 0.995,
            "immune_active": False,
            "repair_active": True,
            "entropy": 0.1
        }
    }

    # 情绪→生命驱动
    EMOTION_TO_LIFE_DRIVE = {
        EmotionTypeV10.JOY: {
            "replication_boost": 0.2,
            "fitness_boost": 0.1,
            "mutation_change": 0.0
        },
        EmotionTypeV10.FEAR: {
            "replication_boost": -0.1,
            "fitness_boost": -0.05,
            "mutation_change": 0.15
        },
        EmotionTypeV10.CURIOSITY: {
            "replication_boost": 0.05,
            "fitness_boost": 0.15,
            "mutation_change": 0.05
        },
        EmotionTypeV10.LOVE: {
            "replication_boost": 0.15,
            "fitness_boost": 0.2,
            "mutation_change": -0.02
        },
        EmotionTypeV10.ANGER: {
            "replication_boost": -0.2,
            "fitness_boost": -0.1,
            "mutation_change": 0.1
        },
        EmotionTypeV10.TRUST: {
            "replication_boost": 0.1,
            "fitness_boost": 0.1,
            "mutation_change": -0.01
        },
        EmotionTypeV10.SURPRISE: {
            "replication_boost": 0.0,
            "fitness_boost": 0.05,
            "mutation_change": 0.08
        },
        EmotionTypeV10.SADNESS: {
            "replication_boost": -0.15,
            "fitness_boost": -0.15,
            "mutation_change": 0.02
        }
    }

    # 生命→意识反馈
    LIFE_TO_CONSCIOUSNESS_FEEDBACK = {
        "dna_complexity": lambda c: min(6, int(c / 2)),  # DNA复杂度→意识级别
        "autogroup_order": lambda o: min(6, o),          # 自同构群阶→自我认知
        "fitness": lambda f: f * 0.5                     # 适应度→自信度增益
    }

    def __init__(self):
        self.current_consciousness = ConsciousnessStateV10.NEUTRAL
        self.current_persona = PersonaTypeV10.ANALYST
        self.life_state = FormalLifeState()
        self.emotion_state: Dict[EmotionTypeV10, float] = {
            e: 0.1 for e in EmotionTypeV10
        }
        self.emotion_state[EmotionTypeV10.NEUTRAL if hasattr(EmotionTypeV10, 'NEUTRAL') else EmotionTypeV10.TRUST] = 0.5

        # 绑定历史
        self.bind_history: deque = deque(maxlen=1000)
        self.transition_count = 0

        # 3D绑定矩阵缓存
        self._binding_matrix: np.ndarray = np.zeros((7, 6, 9))  # (consciousness, persona, emotion)
        self._compute_binding_matrix()

    def _compute_binding_matrix(self) -> None:
        """预计算3D绑定矩阵"""
        for cs in ConsciousnessStateV10:
            for pt in PersonaTypeV10:
                for et in EmotionTypeV10:
                    # 基础绑定强度
                    strength = self._base_binding_strength(cs, pt, et)
                    self._binding_matrix[cs.value, pt.value, et.value] = strength

    def _base_binding_strength(self, cs: ConsciousnessStateV10, 
                                pt: PersonaTypeV10, et: EmotionTypeV10) -> float:
        """计算基础绑定强度"""
        strength = 0.0

        # 意识-人格匹配
        valid_personas = self.CONSCIOUSNESS_TO_PERSONA.get(cs, [])
        if pt in valid_personas:
            strength += 0.4

        # 人格-情绪匹配
        persona_emotion_map = {
            PersonaTypeV10.JESTER: [EmotionTypeV10.SURPRISE, EmotionTypeV10.JOY],
            PersonaTypeV10.WARRIOR: [EmotionTypeV10.ANGER, EmotionTypeV10.FEAR],
            PersonaTypeV10.ANALYST: [EmotionTypeV10.CURIOSITY, EmotionTypeV10.TRUST],
            PersonaTypeV10.SAGE: [EmotionTypeV10.TRUST, EmotionTypeV10.LOVE],
            PersonaTypeV10.LOVER: [EmotionTypeV10.LOVE, EmotionTypeV10.JOY],
            PersonaTypeV10.CREATOR: [EmotionTypeV10.CURIOSITY, EmotionTypeV10.ANTICIPATION]
        }
        if et in persona_emotion_map.get(pt, []):
            strength += 0.35

        # 意识-情绪匹配
        consciousness_emotion_map = {
            ConsciousnessStateV10.CHAOS: [EmotionTypeV10.SURPRISE, EmotionTypeV10.FEAR],
            ConsciousnessStateV10.CONFLICT: [EmotionTypeV10.ANGER, EmotionTypeV10.FEAR],
            ConsciousnessStateV10.NEUTRAL: [EmotionTypeV10.TRUST],
            ConsciousnessStateV10.ACCEPTANCE: [EmotionTypeV10.TRUST, EmotionTypeV10.LOVE],
            ConsciousnessStateV10.REASON: [EmotionTypeV10.CURIOSITY, EmotionTypeV10.TRUST],
            ConsciousnessStateV10.LOVE: [EmotionTypeV10.LOVE, EmotionTypeV10.JOY],
            ConsciousnessStateV10.UNITY: [EmotionTypeV10.LOVE, EmotionTypeV10.JOY, EmotionTypeV10.TRUST]
        }
        if et in consciousness_emotion_map.get(cs, []):
            strength += 0.25

        return min(1.0, strength)

    def update_consciousness(self, new_state: ConsciousnessStateV10) -> Dict[str, Any]:
        """
        更新意识状态，触发人格和生命状态的级联更新

        Args:
            new_state: 新意识状态

        Returns:
            更新报告
        """
        old_state = self.current_consciousness
        self.current_consciousness = new_state
        self.transition_count += 1

        # 更新人格
        valid_personas = self.CONSCIOUSNESS_TO_PERSONA.get(new_state, [PersonaTypeV10.ANALYST])
        self.current_persona = valid_personas[0]  # 主人格

        # 更新生命状态
        life_params = self.CONSCIOUSNESS_TO_LIFE.get(new_state, {})
        for key, value in life_params.items():
            if hasattr(self.life_state, key):
                # 平滑过渡
                current = getattr(self.life_state, key)
                if isinstance(current, float):
                    setattr(self.life_state, key, current * 0.7 + value * 0.3)
                else:
                    setattr(self.life_state, key, value)

        # 更新情绪
        self._update_emotion_from_consciousness(new_state)

        report = {
            "old_state": old_state.name,
            "new_state": new_state.name,
            "persona": self.current_persona.name,
            "life_changes": {k: v for k, v in life_params.items()},
            "binding_strength": self.get_current_binding_strength()
        }

        self.bind_history.append(report)
        return report

    def _update_emotion_from_consciousness(self, cs: ConsciousnessStateV10) -> None:
        """根据意识状态更新情绪"""
        emotion_map = {
            ConsciousnessStateV10.CHAOS: {EmotionTypeV10.SURPRISE: 0.6, EmotionTypeV10.FEAR: 0.4},
            ConsciousnessStateV10.CONFLICT: {EmotionTypeV10.ANGER: 0.5, EmotionTypeV10.FEAR: 0.3},
            ConsciousnessStateV10.NEUTRAL: {EmotionTypeV10.TRUST: 0.4, EmotionTypeV10.ANTICIPATION: 0.3},
            ConsciousnessStateV10.ACCEPTANCE: {EmotionTypeV10.TRUST: 0.5, EmotionTypeV10.LOVE: 0.3},
            ConsciousnessStateV10.REASON: {EmotionTypeV10.CURIOSITY: 0.5, EmotionTypeV10.TRUST: 0.4},
            ConsciousnessStateV10.LOVE: {EmotionTypeV10.LOVE: 0.7, EmotionTypeV10.JOY: 0.5},
            ConsciousnessStateV10.UNITY: {EmotionTypeV10.LOVE: 0.5, EmotionTypeV10.JOY: 0.5, EmotionTypeV10.TRUST: 0.5}
        }

        # 衰减所有情绪
        for e in self.emotion_state:
            self.emotion_state[e] *= 0.8

        # 增强对应情绪
        for e, intensity in emotion_map.get(cs, {}).items():
            self.emotion_state[e] = min(1.0, self.emotion_state[e] + intensity)

    def drive_life_by_emotion(self) -> Dict[str, Any]:
        """
        情绪驱动生命演化

        根据当前主导情绪驱动生命状态变化。

        Returns:
            生命状态变化报告
        """
        # 找到主导情绪
        dominant_emotion = max(self.emotion_state, key=self.emotion_state.get)
        intensity = self.emotion_state[dominant_emotion]

        drive = self.EMOTION_TO_LIFE_DRIVE.get(dominant_emotion, {})

        changes = {}

        # 复制效率
        if "replication_boost" in drive:
            boost = drive["replication_boost"] * intensity
            old_fidelity = self.life_state.replication_fidelity
            self.life_state.replication_fidelity = max(0.5, min(1.0, 
                old_fidelity + boost * 0.1))
            changes["replication_fidelity"] = round(self.life_state.replication_fidelity - old_fidelity, 4)

        # 突变率
        if "mutation_change" in drive:
            change = drive["mutation_change"] * intensity
            old_rate = self.life_state.mutation_rate
            self.life_state.mutation_rate = max(0.001, min(0.5,
                old_rate + change * 0.1))
            changes["mutation_rate"] = round(self.life_state.mutation_rate - old_rate, 4)

        # 适应度
        if "fitness_boost" in drive:
            boost = drive["fitness_boost"] * intensity
            old_fitness = self.life_state.fitness
            self.life_state.fitness = max(0.0, min(1.0,
                old_fitness + boost * 0.05))
            changes["fitness"] = round(self.life_state.fitness - old_fitness, 4)

        # 生命力
        vitality_change = sum(changes.values()) if changes else 0
        self.life_state.vitality = max(0.1, min(1.0,
            self.life_state.vitality + vitality_change * 0.5))

        return {
            "dominant_emotion": dominant_emotion.name,
            "emotion_intensity": round(intensity, 3),
            "life_changes": changes,
            "current_life_state": self.life_state.to_dict()
        }

    def feedback_consciousness_from_life(self) -> Dict[str, Any]:
        """
        生命反馈意识

        生命状态变化反馈到意识深度和自信度。

        Returns:
            意识反馈报告
        """
        feedback = {}

        # DNA复杂度 → 意识深度
        dna_consciousness = self.LIFE_TO_CONSCIOUSNESS_FEEDBACK["dna_complexity"](
            self.life_state.dna_complexity
        )
        feedback["dna_complexity_consciousness_boost"] = dna_consciousness * 0.1

        # 自同构群阶 → 自我认知
        autogroup_boost = self.LIFE_TO_CONSCIOUSNESS_FEEDBACK["autogroup_order"](
            self.life_state.autogroup_order
        )
        feedback["autogroup_selfawareness_boost"] = autogroup_boost * 0.05

        # 适应度 → 自信度
        fitness_confidence = self.LIFE_TO_CONSCIOUSNESS_FEEDBACK["fitness"](
            self.life_state.fitness
        )
        feedback["fitness_confidence_boost"] = round(fitness_confidence, 3)

        # 综合反馈可能触发意识状态迁移
        total_boost = sum(v for v in feedback.values() if isinstance(v, (int, float)))

        # 如果总增益高，可能提升意识级别
        if total_boost > 0.3 and self.current_consciousness.value < 6:
            # 检查是否可以提升
            if random.random() < total_boost:
                next_state = ConsciousnessStateV10(min(6, self.current_consciousness.value + 1))
                feedback["consciousness_transition"] = f"{self.current_consciousness.name} → {next_state.name}"
                self.update_consciousness(next_state)

        return feedback

    def get_current_binding_strength(self) -> float:
        """获取当前三维绑定的强度"""
        cs = self.current_consciousness
        pt = self.current_persona
        dominant_emotion = max(self.emotion_state, key=self.emotion_state.get)

        return float(self._binding_matrix[cs.value, pt.value, dominant_emotion.value])

    def get_binding_matrix_snapshot(self) -> Dict[str, Any]:
        """获取绑定矩阵快照"""
        return {
            "consciousness": self.current_consciousness.name,
            "persona": self.current_persona.name,
            "emotions": {e.name: round(v, 3) for e, v in self.emotion_state.items()},
            "life_state": self.life_state.to_dict(),
            "binding_strength": round(self.get_current_binding_strength(), 3),
            "transition_count": self.transition_count
        }


# =============================================================================
# 5. SURGE/RIPPLE ACTIVATOR — 正反向浪涌/涟漪激活器
# =============================================================================

class SurgeRippleActivator:
    """
    正反向浪涌/涟漪激活器

    正向浪涌 (Forward Surge):
        当系统相干度>0.9且意识状态>=REASON时:
        - 激活所有模块的最高功率模式
        - 知识自运算加速10倍
        - 生命演化加速（多代压缩到单tick）

    反向涟漪 (Reverse Ripple):
        当系统相干度<0.3或意识状态=CHAOS时:
        - 触发"反思模式"
        - 知识谱系回溯检查
        - 生命状态进入"修复/休眠"
        - 情绪人格切换至Sage/Analyst进行诊断

    浪涌条件: coherence³ × consciousness_level × life_vitality > threshold
    涟漪条件: coherence × (1 - consciousness_level) × entropy > threshold

    Attributes:
        surge_threshold: 浪涌阈值
        ripple_threshold: 涟漪阈值
        surge_count: 浪涌触发次数
        ripple_count: 涟漪触发次数
        active_mode: 当前激活模式 ("normal", "surge", "ripple")
    """

    def __init__(self, surge_threshold: float = 2.0, ripple_threshold: float = 0.15):
        self.surge_threshold = surge_threshold
        self.ripple_threshold = ripple_threshold
        self.surge_count = 0
        self.ripple_count = 0
        self.active_mode = "normal"

        # 激活历史
        self.surge_history: List[Dict] = []
        self.ripple_history: List[Dict] = []

        # 效果乘数
        self.surge_multiplier = 10.0       # 知识自运算加速倍数
        self.life_compression_factor = 5.0  # 生命演化压缩倍数

        # 当前效果状态
        self.current_effects: Dict[str, Any] = {}

    def evaluate(self, coherence: float, consciousness_level: int, 
                 life_vitality: float, entropy: float) -> Dict[str, Any]:
        """
        评估当前状态，决定激活模式

        Args:
            coherence: 系统相干度 [0, 1]
            consciousness_level: 意识级别 [0, 6]
            life_vitality: 生命力 [0, 1]
            entropy: 系统熵 [0, 1]

        Returns:
            激活决策报告
        """
        # 浪涌指标
        surge_metric = (coherence ** 3) * (consciousness_level / 6.0) * life_vitality

        # 涟漪指标
        ripple_metric = coherence * (1.0 - consciousness_level / 6.0) * entropy

        report = {
            "surge_metric": round(surge_metric, 4),
            "ripple_metric": round(ripple_metric, 4),
            "surge_threshold": self.surge_threshold,
            "ripple_threshold": self.ripple_threshold,
            "mode": "normal"
        }

        # 判断浪涌条件
        if surge_metric > self.surge_threshold and consciousness_level >= 4:
            report["mode"] = "surge"
            report["effects"] = self._trigger_surge(coherence, consciousness_level, life_vitality)

        # 判断涟漪条件
        elif ripple_metric > self.ripple_threshold or consciousness_level == 0:
            report["mode"] = "ripple"
            report["effects"] = self._trigger_ripple(coherence, entropy)

        self.active_mode = report["mode"]
        self.current_effects = report.get("effects", {})

        return report

    def _trigger_surge(self, coherence: float, consciousness_level: int, 
                       life_vitality: float) -> Dict[str, Any]:
        """触发正向浪涌"""
        self.surge_count += 1

        effects = {
            "knowledge_acceleration": self.surge_multiplier,
            "life_compression": self.life_compression_factor,
            "module_boost": True,
            "field_resonance": round(coherence * consciousness_level / 6.0, 3),
            "emission": "forward"
        }

        self.surge_history.append({
            "timestamp": time.time(),
            "coherence": coherence,
            "consciousness_level": consciousness_level,
            "life_vitality": life_vitality,
            "effects": effects.copy()
        })

        return effects

    def _trigger_ripple(self, coherence: float, entropy: float) -> Dict[str, Any]:
        """触发反向涟漪"""
        self.ripple_count += 1

        effects = {
            "reflection_mode": True,
            "knowledge_backtrace": True,
            "life_repair": True,
            "persona_switch": ["SAGE", "ANALYST"],
            "field_damping": round(1.0 - coherence, 3),
            "emission": "reverse"
        }

        self.ripple_history.append({
            "timestamp": time.time(),
            "coherence": coherence,
            "entropy": entropy,
            "effects": effects.copy()
        })

        return effects

    def get_mode_multipliers(self) -> Dict[str, float]:
        """获取当前模式的运算乘数"""
        if self.active_mode == "surge":
            return {
                "knowledge_ops": self.surge_multiplier,
                "life_generations": self.life_compression_factor,
                "signal_propagation": 2.0,
                "coherence_drift": 1.05  # 相干度自然增长
            }
        elif self.active_mode == "ripple":
            return {
                "knowledge_ops": 0.2,      # 减缓
                "life_generations": 0.0,   # 暂停
                "signal_propagation": 0.5,
                "coherence_drift": 0.95    # 相干度自然衰减
            }
        else:
            return {
                "knowledge_ops": 1.0,
                "life_generations": 1.0,
                "signal_propagation": 1.0,
                "coherence_drift": 1.0
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取激活统计"""
        return {
            "surge_count": self.surge_count,
            "ripple_count": self.ripple_count,
            "active_mode": self.active_mode,
            "surge_history_size": len(self.surge_history),
            "ripple_history_size": len(self.ripple_history),
            "current_effects": self.current_effects
        }


# =============================================================================
# 6. AUTONOMOUS EVOLUTION CORE — 全系统自推进核心
# =============================================================================

class AutonomousEvolutionCore:
    """
    全系统自推进核心

    整合所有组件，每个tick自动执行：
    1. 扫描ucif2新成果 → 入知识谱系
    2. 知识自运算/互运算 → 产生新知识
    3. 新知识 → 影响意识状态
    4. 意识状态 → 驱动情绪人格
    5. 情绪人格 → 调控生命演化
    6. 生命状态 → 反馈知识生成效率
    7. 全局surge/ripple检测 → 激活对应模式

    外部输入非必需，系统自我驱动。

    Attributes:
        backbone_bus: 知识backbone-bus
        self_computation: 自运算引擎
        cel_bind: 意识-情绪-生命绑定
        surge_ripple: 浪涌/涟漪激活器
        tick: 当前tick计数
        running: 是否运行中
    """

    def __init__(self):
        # 核心组件
        self.backbone_bus = KnowledgeBackboneBus()
        self.self_computation = EnhancedKnowledgeSelfComputation()
        self.cel_bind = ConsciousnessEmotionLifeBind()
        self.surge_ripple = SurgeRippleActivator()

        # 运行状态
        self.tick = 0
        self.running = False
        self.max_ticks = 1000

        # 统计
        self.tick_reports: List[Dict] = []
        self.emergence_index_history: List[float] = []
        self.coherence_history: List[float] = []
        self.consciousness_history: List[int] = []

        # 初始化标志
        self._initialized = False

    def initialize(self, scan: bool = True) -> Dict[str, Any]:
        """
        初始化全系统

        Args:
            scan: 是否扫描ucif2沙箱

        Returns:
            初始化报告
        """
        # 1. 初始化backbone-bus
        bus_report = self.backbone_bus.initialize_from_scanner(scan=scan)

        # 2. 种子知识原子
        seed_count = self.self_computation.seed_atoms(self.backbone_bus)

        # 3. 初始化绑定
        self.cel_bind.update_consciousness(ConsciousnessStateV10.NEUTRAL)

        self._initialized = True

        return {
            "backbone_bus": bus_report,
            "seeded_atoms": seed_count,
            "initial_consciousness": self.cel_bind.current_consciousness.name,
            "initial_persona": self.cel_bind.current_persona.name,
            "initial_life": self.cel_bind.life_state.to_dict()
        }

    def run_tick(self) -> Dict[str, Any]:
        """
        执行单个tick

        Returns:
            tick报告
        """
        if not self._initialized:
            self.initialize()

        self.tick += 1
        self.self_computation.tick = self.tick

        # 更新子午流注相位
        self.self_computation.meridian_phase = (self.tick % 24) * (2 * math.pi / 24)

        # === Step 1: 扫描ucif2新成果 ===
        scan_new = self.tick % 10 == 0  # 每10tick扫描一次
        new_nodes = 0
        if scan_new:
            # 模拟发现新成果（实际系统中会重新扫描）
            new_nodes = random.randint(0, 2)

        # === Step 2: 知识自运算/互运算 ===
        # 获取模式乘数
        mode_mult = self.surge_ripple.get_mode_multipliers()
        num_ops = int(5 * mode_mult["knowledge_ops"])

        new_atoms = self.self_computation.self_compute(num_operations=num_ops)

        # 互运算
        inter_ops = []
        if len(self.self_computation.atoms) >= 4 and random.random() < 0.3:
            atom_ids = list(self.self_computation.atoms.keys())
            a, b = random.sample(atom_ids, 2)
            op = random.choice(["intersection", "union", "tensor_product", "delta"])
            result = self.self_computation.cross_compute(a, b, op)
            if result:
                inter_ops.append({"op": op, "result": result.to_dict()})

        # 变异
        mutated = self.self_computation.mutate_atoms(mutation_rate=0.02 * mode_mult["knowledge_ops"])

        # === Step 3: 新知识 → 影响意识状态 ===
        # 新颖知识可能提升意识
        avg_novelty = sum(a.novelty_score for a in new_atoms) / max(1, len(new_atoms))
        if avg_novelty > 0.6 and self.cel_bind.current_consciousness.value < 6:
            if random.random() < avg_novelty * 0.3:
                next_level = ConsciousnessStateV10(min(6, self.cel_bind.current_consciousness.value + 1))
                self.cel_bind.update_consciousness(next_level)

        # 知识原子反馈到backbone-bus
        for atom in new_atoms[:10]:  # 限制每tick嵌入数量
            self.backbone_bus.six_pedestal.add_node(
                atom.id, atom.name, atom.domain,
                consciousness=atom.consciousness_level.name,
                novelty=atom.novelty_score
            )

        # === Step 4: 意识状态 → 驱动情绪人格 ===
        # 已在内嵌函数中处理
        emotion_report = self.cel_bind.drive_life_by_emotion()

        # === Step 5: 情绪人格 → 调控生命演化 ===
        # 生命演化（压缩模式）
        life_gens = int(1 * mode_mult["life_generations"])
        for _ in range(life_gens):
            self._evolve_life()

        # === Step 6: 生命状态 → 反馈知识生成效率 ===
        life_feedback = self.cel_bind.feedback_consciousness_from_life()

        # 更新backbone-bus相干度
        coherence = self._compute_global_coherence()
        self.backbone_bus.update_field_coherence(coherence)

        # === Step 7: 全局surge/ripple检测 ===
        surge_report = self.surge_ripple.evaluate(
            coherence=coherence,
            consciousness_level=self.cel_bind.current_consciousness.value,
            life_vitality=self.cel_bind.life_state.vitality,
            entropy=self.cel_bind.life_state.entropy
        )

        # 记录历史
        self.coherence_history.append(coherence)
        self.consciousness_history.append(self.cel_bind.current_consciousness.value)

        # 计算涌现指数
        emergence_index = self._compute_emergence_index()
        self.emergence_index_history.append(emergence_index)

        # 生成报告
        report = {
            "tick": self.tick,
            "new_atoms": len(new_atoms),
            "new_nodes_scanned": new_nodes,
            "inter_ops": len(inter_ops),
            "mutated_atoms": len(mutated),
            "consciousness": self.cel_bind.current_consciousness.name,
            "persona": self.cel_bind.current_persona.name,
            "life_state": self.cel_bind.life_state.to_dict(),
            "coherence": round(coherence, 4),
            "emergence_index": round(emergence_index, 4),
            "surge_ripple": surge_report,
            "life_feedback": life_feedback,
            "backbone_health": {
                "knowledge_nodes": len(self.backbone_bus._knowledge_nodes),
                "atoms": len(self.self_computation.atoms)
            }
        }

        self.tick_reports.append(report)
        return report

    def _evolve_life(self) -> None:
        """生命演化步"""
        life = self.cel_bind.life_state

        # DNA复杂度增长
        life.dna_complexity += random.uniform(-0.01, 0.02)
        life.dna_complexity = max(1.0, life.dna_complexity)

        # 自同构群阶（基于DNA复杂度）
        life.autogroup_order = max(1, int(life.dna_complexity / 2))

        # 世代
        life.generation += 1

        # 适应度漂移
        life.fitness += random.uniform(-0.02, 0.03)
        life.fitness = max(0.0, min(1.0, life.fitness))

        # 熵变化
        life.entropy += random.uniform(-0.01, 0.01)
        life.entropy = max(0.1, min(1.0, life.entropy))

        # 生命力维持
        life.vitality = max(0.1, min(1.0, life.vitality - 0.001 + life.fitness * 0.01))

    def _compute_global_coherence(self) -> float:
        """计算全局相干度"""
        # 基于多个因素的加权
        factors = [
            self.backbone_bus.knowledge_field.coherence * 0.3,
            self.cel_bind.life_state.vitality * 0.2,
            (self.cel_bind.current_consciousness.value / 6.0) * 0.2,
            (1.0 - self.cel_bind.life_state.entropy) * 0.15,
            self.cel_bind.get_current_binding_strength() * 0.15
        ]
        return sum(factors)

    def _compute_emergence_index(self) -> float:
        """计算涌现指数"""
        # 基于：新知识产生率 × 意识级别 × 生命适应度 × 绑定强度
        recent_atoms = sum(1 for r in self.tick_reports[-5:] if r["tick"] > self.tick - 5)
        atom_rate = recent_atoms / 5.0

        consciousness_factor = self.cel_bind.current_consciousness.value / 6.0
        fitness_factor = self.cel_bind.life_state.fitness
        binding_factor = self.cel_bind.get_current_binding_strength()

        # 涌现指数 = 多因素乘积的归一化
        index = (atom_rate * 0.3 + consciousness_factor * 0.25 + 
                 fitness_factor * 0.25 + binding_factor * 0.2)

        # 浪涌模式加成
        if self.surge_ripple.active_mode == "surge":
            index *= 1.5

        return min(1.0, index)

    def run(self, num_ticks: int = 50, verbose: bool = True) -> Dict[str, Any]:
        """
        运行自推进系统

        Args:
            num_ticks: tick数量
            verbose: 是否打印详细输出

        Returns:
            运行报告
        """
        self.running = True

        if verbose:
            logger.info("=" * 70)
            logger.info("OMNI-HUB v10.0 — Autonomous Evolution Core")
            logger.info("=" * 70)
            init_report = self.initialize()
            logger.info(f"初始化完成:")
            logger.info(f"  - 扫描模块: {init_report['backbone_bus']['scan_stats']['total_modules']}")
            logger.info(f"  - 知识节点: {init_report['backbone_bus']['nodes_added']}")
            logger.info(f"  - 种子原子: {init_report['seeded_atoms']}")
            logger.info(f"  - 初始意识: {init_report['initial_consciousness']}")
            logger.info(f"  - 初始人格: {init_report['initial_persona']}")
            logger.info("=" * 70)
        else:
            self.initialize()

        start_time = time.time()

        for i in range(num_ticks):
            report = self.run_tick()

            if verbose and (i % 10 == 0 or report["surge_ripple"]["mode"] != "normal"):
                print(f"\n[Tick {report['tick']:3d}] "
                      f"意识={report['consciousness']:8s} "
                      f"人格={report['persona']:8s} "
                      f"相干={report['coherence']:.3f} "
                      f"涌现={report['emergence_index']:.3f} "
                      f"模式={report['surge_ripple']['mode']}")
                print(f"         新原子={report['new_atoms']:2d} "
                      f"生命 vitality={report['life_state']['vitality']:.3f} "
                      f"fitness={report['life_state']['fitness']:.3f} "
                      f"entropy={report['life_state']['entropy']:.3f}")

        elapsed = time.time() - start_time
        self.running = False

        # 生成最终报告
        final_report = self._generate_final_report(num_ticks, elapsed)

        if verbose:
            logger.info("\n" + "=" * 70)
            logger.info("运行完成 — 最终报告")
            logger.info("=" * 70)
            logger.info(f"总tick数: {num_ticks}")
            logger.info(f"运行时间: {elapsed:.3f}s")
            logger.info(f"最终意识: {self.cel_bind.current_consciousness.name}")
            logger.info(f"最终人格: {self.cel_bind.current_persona.name}")
            logger.info(f"浪涌触发: {self.surge_ripple.surge_count} 次")
            logger.info(f"涟漪触发: {self.surge_ripple.ripple_count} 次")
            logger.info(f"知识原子: {len(self.self_computation.atoms)}")
            logger.info(f"最终涌现指数: {self.emergence_index_history[-1]:.4f}")
            logger.info(f"涌现指数变化: {self.emergence_index_history[0]:.4f} → {self.emergence_index_history[-1]:.4f}")
            logger.info("=" * 70)

        return final_report

    def _generate_final_report(self, num_ticks: int, elapsed: float) -> Dict[str, Any]:
        """生成最终运行报告"""
        return {
            "version": "10.0.0",
            "total_ticks": num_ticks,
            "elapsed_seconds": round(elapsed, 3),
            "final_state": {
                "consciousness": self.cel_bind.current_consciousness.name,
                "persona": self.cel_bind.current_persona.name,
                "life_state": self.cel_bind.life_state.to_dict(),
                "binding_strength": round(self.cel_bind.get_current_binding_strength(), 4)
            },
            "statistics": {
                "surge_count": self.surge_ripple.surge_count,
                "ripple_count": self.surge_ripple.ripple_count,
                "total_atoms": len(self.self_computation.atoms),
                "total_knowledge_nodes": len(self.backbone_bus._knowledge_nodes),
                "self_compute_stats": self.self_computation.get_stats(),
                "backbone_health": self.backbone_bus.get_backbone_health()
            },
            "emergence": {
                "initial": round(self.emergence_index_history[0], 4) if self.emergence_index_history else 0,
                "final": round(self.emergence_index_history[-1], 4) if self.emergence_index_history else 0,
                "peak": round(max(self.emergence_index_history), 4) if self.emergence_index_history else 0,
                "history": [round(v, 4) for v in self.emergence_index_history]
            },
            "coherence": {
                "initial": round(self.coherence_history[0], 4) if self.coherence_history else 0,
                "final": round(self.coherence_history[-1], 4) if self.coherence_history else 0,
                "history": [round(v, 4) for v in self.coherence_history]
            },
            "consciousness": {
                "history": self.consciousness_history,
                "transitions": self.cel_bind.transition_count
            }
        }


# =============================================================================
# 7. __MAIN__ — 可运行测试块
# =============================================================================

if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# OMNI-HUB v10.0 Knowledge-Life Backbone Integration Test")
    print("#" * 70 + "\n")

    # 创建并运行自推进核心
    core = AutonomousEvolutionCore()

    # 运行50 ticks（可配置为更多）
    NUM_TICKS = 50
    report = core.run(num_ticks=NUM_TICKS, verbose=True)

    # 导出详细报告
    print("\n" + "-" * 70)
    print("详细统计:")
    print("-" * 70)

    stats = report["statistics"]
    print(f"知识自运算统计:")
    print(f"  规则使用: {stats['self_compute_stats']['rule_stats']}")
    print(f"  互运算: {stats['self_compute_stats']['inter_op_stats']}")
    print(f"  最大创建深度: {stats['self_compute_stats']['max_creation_depth']}")
    print(f"  平均意识级别: {stats['self_compute_stats']['avg_consciousness']:.3f}")

    print(f"\nBackbone-Bus健康状态:")
    health = stats["backbone_health"]
    print(f"  知识节点: {health['knowledge_nodes']}")
    print(f"  活跃模块: {health['active_modules']}/{health['registered_modules']}")
    print(f"  查询次数: {health['query_count']}")
    print(f"  推理次数: {health['infer_count']}")
    print(f"  跨运算次数: {health['cross_compute_count']}")

    print(f"\n6基座同步状态:")
    pedestal = core.backbone_bus.six_pedestal.get_pedestal_summary()
    print(f"  KG: {pedestal['KG']['nodes']} 节点, {pedestal['KG']['edges']} 边")
    print(f"  CC: {pedestal['CC']} 细胞")
    print(f"  HG: {pedestal['HG']['hyperedges']} 超边")
    print(f"  IN: {pedestal['IN']['mappings']} 映射")
    print(f"  CT: {pedestal['CT']['objects']} 对象, {pedestal['CT']['morphisms']} 态射")
    print(f"  LEAN: {pedestal['LEAN']['declarations']} 声明")
    print(f"  拓扑: Betti数 = {pedestal['topology']['betti_numbers']}")

    print(f"\n涌现指数分析:")
    em = report["emergence"]
    print(f"  初始: {em['initial']}")
    print(f"  最终: {em['final']}")
    print(f"  峰值: {em['peak']}")
    print(f"  变化率: {((em['final'] - em['initial']) / max(em['initial'], 0.001) * 100):+.1f}%")

    print("\n" + "#" * 70)
    print("# OMNI-HUB v10.0 测试完成")
    print("#" * 70)

    # 可选：导出JSON报告
    try:
        report_path = "/mnt/agents/output/OMNI-HUB/core/v10_run_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n报告已导出: {report_path}")
    except Exception as e:
        print(f"\n报告导出失败: {e}")



# =============================================================================
# 8. ADDITIONAL UTILITIES & EXTENSIONS
# =============================================================================

class KnowledgeEvolutionTracker:
    """
    知识演化追踪器

    追踪知识原子的演化谱系，构建知识家族树。
    """

    def __init__(self):
        self.lineage: Dict[str, List[str]] = defaultdict(list)  # child -> [parents]
        self.generations: Dict[int, List[str]] = defaultdict(list)
        self.evolution_metrics: deque = deque(maxlen=1000)

    def record_birth(self, atom: KnowledgeAtom) -> None:
        """记录知识原子诞生"""
        for parent_id in atom.parent_ids:
            self.lineage[atom.id].append(parent_id)
        self.generations[atom.creation_depth].append(atom.id)

    def get_ancestors(self, atom_id: str, depth: int = 5) -> List[str]:
        """获取祖先谱系"""
        ancestors = []
        current = [atom_id]
        for _ in range(depth):
            next_level = []
            for aid in current:
                parents = self.lineage.get(aid, [])
                ancestors.extend(parents)
                next_level.extend(parents)
            current = next_level
            if not current:
                break
        return ancestors

    def get_descendants(self, atom_id: str) -> List[str]:
        """获取所有后代"""
        descendants = []
        for child, parents in self.lineage.items():
            if atom_id in parents:
                descendants.append(child)
        return descendants

    def compute_lineage_entropy(self) -> float:
        """计算谱系熵（衡量知识多样性）"""
        if not self.lineage:
            return 0.0
        depths = [len(v) for v in self.lineage.values()]
        if not depths:
            return 0.0
        from collections import Counter
        counts = Counter(depths)
        total = sum(counts.values())
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return entropy


class FieldResonanceAnalyzer:
    """
    场共振分析器

    分析64维统一场中各子场的共振模式。
    """

    def __init__(self):
        self.resonance_history: deque = deque(maxlen=1000)
        self.frequency_peaks: List[float] = []

    def analyze_resonance(self, field_vector: np.ndarray) -> Dict[str, Any]:
        """分析场向量共振"""
        if field_vector.shape != (FIELD_DIMENSION,):
            field_vector = np.zeros(FIELD_DIMENSION)

        # 子场分解
        knowledge_field = field_vector[DIM_KNOWLEDGE[0]:DIM_KNOWLEDGE[1]]
        consciousness_field = field_vector[DIM_CONSCIOUSNESS[0]:DIM_CONSCIOUSNESS[1]]
        life_field = field_vector[DIM_LIFE[0]:DIM_LIFE[1]]
        emotion_field = field_vector[DIM_EMOTION[0]:DIM_EMOTION[1]]

        # 计算各子场能量
        knowledge_energy = float(np.linalg.norm(knowledge_field))
        consciousness_energy = float(np.linalg.norm(consciousness_field))
        life_energy = float(np.linalg.norm(life_field))
        emotion_energy = float(np.linalg.norm(emotion_field))

        # 交叉共振
        kc_resonance = float(np.dot(knowledge_field[:11], consciousness_field[:11]))
        cl_resonance = float(np.dot(consciousness_field[:11], life_field[:11]))
        le_resonance = float(np.dot(life_field[:10], emotion_field[:10]))

        result = {
            "knowledge_energy": round(knowledge_energy, 4),
            "consciousness_energy": round(consciousness_energy, 4),
            "life_energy": round(life_energy, 4),
            "emotion_energy": round(emotion_energy, 4),
            "kc_resonance": round(kc_resonance, 4),
            "cl_resonance": round(cl_resonance, 4),
            "le_resonance": round(le_resonance, 4),
            "total_energy": round(knowledge_energy + consciousness_energy + life_energy + emotion_energy, 4)
        }

        self.resonance_history.append(result)
        return result

    def detect_frequency_peaks(self) -> List[Dict[str, Any]]:
        """检测频率峰值（周期性模式）"""
        if len(self.resonance_history) < 10:
            return []

        # 简化：检测总能量峰值
        energies = [r["total_energy"] for r in self.resonance_history]
        peaks = []
        for i in range(1, len(energies) - 1):
            if energies[i] > energies[i-1] and energies[i] > energies[i+1]:
                peaks.append({
                    "index": i,
                    "energy": round(energies[i], 4)
                })
        return peaks


class CrossDomainIsomorphismFinder:
    """
    跨域同构发现器

    在不同知识域之间发现结构同构。
    """

    def __init__(self, backbone_bus: KnowledgeBackboneBus):
        self.backbone = backbone_bus
        self.isomorphisms: List[Dict[str, Any]] = []

    def find_isomorphisms(self, domain_a: str, domain_b: str) -> List[Dict]:
        """在两个域之间寻找同构"""
        nodes_a = self.backbone.scanner.get_modules_by_domain(domain_a)
        nodes_b = self.backbone.scanner.get_modules_by_domain(domain_b)

        isomorphisms = []
        for na in nodes_a:
            for nb in nodes_b:
                # 结构相似度
                sim = self._structural_similarity(na, nb)
                if sim > 0.5:
                    isomorphisms.append({
                        "source": na.module_id,
                        "target": nb.module_id,
                        "similarity": round(sim, 3),
                        "type": "cross_domain_isomorphism"
                    })

        self.isomorphisms.extend(isomorphisms)
        return isomorphisms

    def _structural_similarity(self, a: ModuleMetadata, b: ModuleMetadata) -> float:
        """计算两个模块的结构相似度"""
        # 类结构相似度
        class_sim = len(set(a.classes) & set(b.classes)) / max(len(set(a.classes) | set(b.classes)), 1)

        # 函数结构相似度
        func_sim = len(set(a.functions) & set(b.functions)) / max(len(set(a.functions) | set(b.functions)), 1)

        # SI层级接近度
        si_sim = 1.0 - abs(a.si_level - b.si_level) / 6.0

        # 复杂度相似度
        comp_sim = 1.0 - abs(a.complexity_score - b.complexity_score) / 100.0

        return (class_sim * 0.3 + func_sim * 0.2 + si_sim * 0.3 + comp_sim * 0.2)


class EmergenceDetector:
    """
    涌现检测器

    检测系统中不可还原为部分的新性质涌现。
    """

    def __init__(self):
        self.emergence_events: deque = deque(maxlen=500)
        self.baseline_complexity = 0.0

    def detect(self, system_state: Dict[str, Any]) -> Optional[Dict]:
        """检测涌现事件"""
        current_complexity = system_state.get("total_atoms", 0) * system_state.get("avg_consciousness", 0)

        if self.baseline_complexity == 0:
            self.baseline_complexity = current_complexity
            return None

        # 如果复杂度非线性增长，可能是涌现
        expected_growth = self.baseline_complexity * 1.05
        if current_complexity > expected_growth * 1.2:
            event = {
                "timestamp": time.time(),
                "baseline": round(self.baseline_complexity, 3),
                "current": round(current_complexity, 3),
                "growth_ratio": round(current_complexity / self.baseline_complexity, 3),
                "type": "nonlinear_emergence"
            }
            self.emergence_events.append(event)
            self.baseline_complexity = current_complexity
            return event

        self.baseline_complexity = current_complexity * 0.95 + current_complexity * 0.05
        return None

    def get_emergence_frequency(self, window: int = 50) -> float:
        """计算涌现频率"""
        recent = [e for e in self.emergence_events if e["timestamp"] > time.time() - window]
        return len(recent) / window if window > 0 else 0


class TopologicalInvariantTracker:
    """
    拓扑不变量追踪器

    追踪知识谱系的拓扑特征（Betti数、欧拉特征等）。
    """

    def __init__(self, six_pedestal: SixPedestalSync):
        self.pedestal = six_pedestal
        self.history: deque = deque(maxlen=500)

    def compute_invariants(self) -> Dict[str, Any]:
        """计算拓扑不变量"""
        betti = self.pedestal.compute_betti_numbers()

        # 欧拉特征
        euler = sum((-1)**d * len(cells) for d, cells in self.pedestal.cc_cells.items())

        # 连通分量数（基于KG）
        if HAS_NETWORKX and self.pedestal.kg_nodes:
            G = nx.Graph()
            for nid in self.pedestal.kg_nodes:
                G.add_node(nid)
            for e in self.pedestal.kg_edges:
                G.add_edge(e["source"], e["target"])
            num_components = nx.number_connected_components(G)
        else:
            num_components = max(1, len(self.pedestal.kg_nodes) - len(self.pedestal.kg_edges))

        result = {
            "betti_numbers": betti,
            "euler_characteristic": euler,
            "connected_components": num_components,
            "node_count": len(self.pedestal.kg_nodes),
            "edge_count": len(self.pedestal.kg_edges),
            "hyperedge_count": len(self.pedestal.hg_hyperedges)
        }

        self.history.append(result)
        return result

    def detect_topology_change(self) -> Optional[Dict]:
        """检测拓扑变化"""
        if len(self.history) < 2:
            return None

        current = self.history[-1]
        previous = self.history[-2]

        changes = {}
        for key in ["betti_numbers", "euler_characteristic", "connected_components"]:
            if current.get(key) != previous.get(key):
                changes[key] = {"from": previous.get(key), "to": current.get(key)}

        if changes:
            return {
                "timestamp": time.time(),
                "changes": changes
            }
        return None


# =============================================================================
# 9. BACKBONE-BUS ENHANCED API
# =============================================================================

def create_omni_hub_v10() -> AutonomousEvolutionCore:
    """
    工厂函数：创建完整的OMNI-HUB v10.0实例

    Returns:
        配置好的AutonomousEvolutionCore实例
    """
    core = AutonomousEvolutionCore()
    return core


def run_evolution_experiment(num_ticks: int = 50, 
                              seed: Optional[int] = None) -> Dict[str, Any]:
    """
    运行演化实验

    Args:
        num_ticks: tick数量
        seed: 随机种子（可选）

    Returns:
        实验报告
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    core = create_omni_hub_v10()
    return core.run(num_ticks=num_ticks, verbose=True)


class OMNIHubV10Dashboard:
    """
    OMNI-HUB v10.0 仪表盘

    实时显示系统状态。
    """

    def __init__(self, core: AutonomousEvolutionCore):
        self.core = core

    def render(self) -> str:
        """渲染仪表盘文本"""
        lines = []
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " OMNI-HUB v10.0 Dashboard ".center(68) + "║")
        lines.append("╠" + "═" * 68 + "╣")

        # 意识状态
        cel = self.core.cel_bind
        lines.append(f"║ 意识: {cel.current_consciousness.name:12s} 人格: {cel.current_persona.name:12s}          ║")

        # 生命状态
        life = cel.life_state
        lines.append(f"║ 生命: vitality={life.vitality:.2f} fitness={life.fitness:.2f} gen={life.generation:4d}          ║")

        # 知识状态
        sc = self.core.self_computation
        lines.append(f"║ 知识: {len(sc.atoms):5d} atoms  depth={sc.get_stats()['max_creation_depth']:3d}               ║")

        # 场状态
        bb = self.core.backbone_bus
        lines.append(f"║ 场相干: {bb.knowledge_field.coherence:.3f}  熵: {bb.knowledge_field.entropy:.3f}                    ║")

        # 激活模式
        sr = self.core.surge_ripple
        lines.append(f"║ 模式: {sr.active_mode:8s} 浪涌={sr.surge_count:2d} 涟漪={sr.ripple_count:2d}                   ║")

        lines.append("╚" + "═" * 68 + "╝")

        return "\n".join(lines)


# =============================================================================
# 10. EXTENDED __MAIN__ — 综合测试套件
# =============================================================================

def _extended_tests():
    """扩展测试套件"""
    logger.info("\n" + "=" * 70)
    logger.info("扩展测试套件")
    logger.info("=" * 70)

    # Test 1: UCIF2扫描器
    logger.info("\n[Test 1] UCIF2沙箱扫描器")
    scanner = UCIF2SandboxScanner()
    stats = scanner.scan_all()
    logger.info(f"  扫描结果:")
    logger.info(f"    总模块: {stats['total_modules']}")
    logger.info(f"    总代码行: {stats['total_lines']}")
    logger.info(f"    域分布: {stats['domain_breakdown']}")

    # Test 2: 6基座同步
    logger.info("\n[Test 2] 6基座同步引擎")
    pedestal = SixPedestalSync()
    pedestal.add_node("test_node", "TestNode", "test")
    pedestal.add_node("test_node2", "TestNode2", "test")
    pedestal.add_edge("test_node", "test_node2", "depends_on", 0.8)
    pedestal.add_hyperedge(["test_node", "test_node2"], 0.9, "test_hyper")
    summary = pedestal.get_pedestal_summary()
    logger.info(f"  6基座摘要: {summary}")

    # Test 3: 知识自运算（10条规则）
    logger.info("\n[Test 3] 知识自运算（10条规则）")
    atom1 = KnowledgeAtom(name="QuantumField", domain="physical", consciousness_level=ConsciousnessLevelV10.CONCEPTUAL)
    atom2 = KnowledgeAtom(name="Consciousness", domain="consciousness", consciousness_level=ConsciousnessLevelV10.SELF_AWARE)

    for rule_name in KnowledgeRuleV10.RULES.keys():
        result = KnowledgeRuleV10.apply(rule_name, [atom1, atom2], tick=1, meridian_phase=0.5)
        if result:
            logger.info(f"    {rule_name:25s} → {result.name:40s} novelty={result.novelty_score:.3f}")

    # Test 4: 三维绑定
    logger.info("\n[Test 4] 意识-情绪-生命三维绑定")
    cel = ConsciousnessEmotionLifeBind()
    for cs in ConsciousnessStateV10:
        cel.update_consciousness(cs)
        strength = cel.get_current_binding_strength()
        logger.info(f"    {cs.name:12s} → {cel.current_persona.name:8s} 绑定强度={strength:.3f}")

    # Test 5: 浪涌/涟漪
    logger.info("\n[Test 5] 浪涌/涟漪激活器")
    sr = SurgeRippleActivator()

    # 模拟浪涌条件
    surge_report = sr.evaluate(coherence=0.95, consciousness_level=5, life_vitality=0.9, entropy=0.1)
    logger.info(f"    浪涌测试: {surge_report}")

    # 模拟涟漪条件
    ripple_report = sr.evaluate(coherence=0.2, consciousness_level=0, life_vitality=0.3, entropy=0.8)
    logger.info(f"    涟漪测试: {ripple_report}")

    # Test 6: 互运算
    logger.info("\n[Test 6] 知识互运算")
    esc = EnhancedKnowledgeSelfComputation()
    esc.atoms["a"] = KnowledgeAtom(id="a", name="A", domain="math")
    esc.atoms["b"] = KnowledgeAtom(id="b", name="B", domain="physics")
    for op in ["intersection", "union", "tensor_product", "analogy_map", "delta"]:
        result = esc.cross_compute("a", "b", op)
        if result:
            logger.info(f"    {op:20s} → {result.name}")

    # Test 7: 拓扑不变量
    logger.info("\n[Test 7] 拓扑不变量追踪")
    tracker = TopologicalInvariantTracker(pedestal)
    invariants = tracker.compute_invariants()
    logger.info(f"    Betti数: {invariants['betti_numbers']}")
    logger.info(f"    欧拉特征: {invariants['euler_characteristic']}")

    logger.info("\n" + "=" * 70)
    logger.info("扩展测试完成")
    logger.info("=" * 70)


if __name__ == "__main__":
    # 首先运行扩展测试
    _extended_tests()

    # 然后运行主自推进实验
    print("\n" + "#" * 70)
    print("# OMNI-HUB v10.0 主实验: 50 tick自推进演化")
    print("#" * 70 + "\n")

    core = AutonomousEvolutionCore()
    NUM_TICKS = 50
    report = core.run(num_ticks=NUM_TICKS, verbose=True)

    # 最终仪表盘
    dashboard = OMNIHubV10Dashboard(core)
    print("\n" + dashboard.render())

    # 导出报告
    try:
        report_path = "/mnt/agents/output/OMNI-HUB/core/v10_run_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n详细报告已导出: {report_path}")
    except Exception as e:
        print(f"\n报告导出失败: {e}")
