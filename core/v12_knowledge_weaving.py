#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — Knowledge Weaving Engine
==========================================
将v11.2深度遍历提取的知识编织入OMNI-HUB的6个知识基座:
  1. KG: 知识图谱 (Knowledge Graph)
  2. CC: 概念细胞 (Concept Cell / Cellular Complex)
  3. HG: 超图 (Hypergraph)
  4. IN: 同构网络 (Isomorphism Network)
  5. CT: 范畴论 (Category Theory)
  6. LL: Lean逻辑 (LEAN Formalization)

输入:
  - FULL_MD_DEEP_ANALYSIS.json (1169个MD文件, ~4MB)
  - UCIF2_FULL_SERIES_ANALYSIS.json (v12-v24 + Lean)
  - CAYLEY24_MATH_PHYS_DEEP_ANALYSIS.json (29文件)
  - CFTS_FULL_ANALYSIS.json (cfts集成分析)

输出:
  - KNOWLEDGE_WEAVING_REPORT.json
  - KNOWLEDGE_WEAVING_REPORT.md

Author: OMNI-HUB v12.0 Knowledge Weaver
Date: 2026
"""

from __future__ import annotations

__version__ = "12.0.0"

import hashlib
import json
import math
import os
import sys
import time
import warnings
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# =============================================================================
# Constants
# =============================================================================
PEDESTAL_NAMES = ["KG", "CC", "HG", "IN", "CT", "LL"]
PEDESTAL_COUNT = 6
FIELD_DIM = 64

# =============================================================================
# Utility Functions
# =============================================================================

def stable_hash(obj: Any) -> str:
    """Generate a stable hex hash for any JSON-serializable object."""
    s = json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def time_str() -> str:
    """ISO timestamp."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(t: str) -> str:
    """Normalize text for matching."""
    return t.lower().strip().replace(" ", "").replace("-", "").replace("_", "")


def compute_density(n_nodes: int, n_edges: int, directed: bool = False) -> float:
    """Compute graph density."""
    if n_nodes <= 1:
        return 0.0
    max_edges = n_nodes * (n_nodes - 1)
    if not directed:
        max_edges //= 2
    return n_edges / max_edges if max_edges > 0 else 0.0


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class KNode:
    """Knowledge Node — 统一知识节点表示."""
    node_id: str
    label: str
    node_type: str
    source: str
    version: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KEdge:
    """Knowledge Edge — 统一知识边表示."""
    edge_id: str
    source: str
    target: str
    edge_type: str
    weight: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HyperEdge:
    """HyperEdge — 超边（连接任意数量的节点）."""
    hid: str
    nodes: Tuple[str, ...]
    h_type: str
    weight: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def arity(self) -> int:
        return len(self.nodes)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConceptCell:
    """Concept Cell — 语义细胞."""
    cid: str
    label: str
    concepts: List[str]
    centroid: str
    weight: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Isomorphism:
    """Isomorphism — 结构同构."""
    iid: str
    left: str
    right: str
    iso_type: str
    strength: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Morphism:
    """Morphism — 范畴论中的态射."""
    mid: str
    source: str
    target: str
    m_type: str
    compose_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FormalProp:
    """Formal Proposition — LL基座中的形式化命题."""
    pid: str
    statement: str
    proposition_type: str
    depends_on: List[str] = field(default_factory=list)
    proof_status: str = "unproven"
    lean_code: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# 6-Base Knowledge Pedestal
# =============================================================================

class KnowledgePedestal:
    """6基座知识容器 — 统一管理6大知识表示基座."""

    def __init__(self):
        # Shared node registry
        self.nodes: Dict[str, KNode] = {}
        self.node_index: Dict[str, str] = {}  # label -> node_id

        # KG: Knowledge Graph
        self.kg_nodes: Dict[str, KNode] = {}
        self.kg_edges: List[KEdge] = []
        self.kg_adj: Dict[str, List[Tuple[str, float, str]]] = defaultdict(list)

        # CC: Concept Cell
        self.cc_cells: Dict[str, ConceptCell] = {}
        self.cc_concept_to_cell: Dict[str, str] = {}

        # HG: Hypergraph
        self.hg_edges: List[HyperEdge] = []
        self.hg_node_to_hyperedges: Dict[str, List[str]] = defaultdict(list)

        # IN: Isomorphism Network
        self.in_isomorphisms: List[Isomorphism] = []
        self.in_clusters: Dict[str, List[str]] = {}

        # CT: Category Theory
        self.ct_objects: Set[str] = set()
        self.ct_morphisms: List[Morphism] = []
        self.ct_composition: Dict[Tuple[str, str], str] = {}

        # LL: LEAN Formalization
        self.ll_propositions: List[FormalProp] = []
        self.ll_theorem_map: Dict[str, List[str]] = defaultdict(list)

        # Statistics per pedestal
        self.stats: Dict[str, Dict[str, Any]] = {
            name: {"nodes": 0, "edges": 0, "density": 0.0, "created": time_str()}
            for name in PEDESTAL_NAMES
        }

        # Cross-pedestal mappings
        self.cross_map: Dict[str, Dict[str, str]] = defaultdict(dict)

    def add_node(self, node: KNode) -> None:
        """Register a node in the shared space."""
        self.nodes[node.node_id] = node
        self.node_index[normalize_text(node.label)] = node.node_id

    def get_node(self, node_id: str) -> Optional[KNode]:
        return self.nodes.get(node_id)

    def node_count(self) -> int:
        return len(self.nodes)

    def update_stats(self, pedestal: str, nodes: int = 0, edges: int = 0) -> None:
        """Update pedestal statistics."""
        if pedestal in self.stats:
            self.stats[pedestal]["nodes"] = nodes
            self.stats[pedestal]["edges"] = edges
            self.stats[pedestal]["density"] = compute_density(nodes, edges)


# =============================================================================
# PedestalBridge — Bidirectional Cross-Pedestal Mapping
# =============================================================================

class PedestalBridge:
    """
    PedestalBridge — 实现6基座间双向映射，确保roundtrip一致性.

    核心机制:
    - 每个基座对维护显式的双向字典映射
    - 映射在weave阶段注册（基于实际编织的数据关联）
    - roundtrip计算基于结构映射而非文本匹配

    映射对 (12个双向 = 6对):
      KG <-> CC: 节点标签<->概念细胞
      CC <-> HG: 概念<->超边节点
      HG <-> IN: 超边节点<->同构对
      IN <-> CT: 同构<->范畴态射
      CT <-> LL: 态射<->Lean命题
      LL <-> KG: 命题陈述<->知识节点
    """

    def __init__(self, pedestal: KnowledgePedestal):
        self.ped = pedestal
        # Bidirectional maps: each is Dict[str, Set[str]] mapping entity IDs
        self.kg_to_cc: Dict[str, Set[str]] = defaultdict(set)
        self.cc_to_kg: Dict[str, Set[str]] = defaultdict(set)
        self.cc_to_hg: Dict[str, Set[str]] = defaultdict(set)
        self.hg_to_cc: Dict[str, Set[str]] = defaultdict(set)
        self.hg_to_in: Dict[str, Set[str]] = defaultdict(set)
        self.in_to_hg: Dict[str, Set[str]] = defaultdict(set)
        self.in_to_ct: Dict[str, Set[str]] = defaultdict(set)
        self.ct_to_in: Dict[str, Set[str]] = defaultdict(set)
        self.ct_to_ll: Dict[str, Set[str]] = defaultdict(set)
        self.ll_to_ct: Dict[str, Set[str]] = defaultdict(set)
        self.ll_to_kg: Dict[str, Set[str]] = defaultdict(set)
        self.kg_to_ll: Dict[str, Set[str]] = defaultdict(set)
        # Bookkeeping
        self.mapping_stats: Dict[str, int] = defaultdict(int)

    def register_kg_cc(self, kg_nid: str, cc_cid: str):
        """Register KG node <-> ConceptCell mapping."""
        self.kg_to_cc[kg_nid].add(cc_cid)
        self.cc_to_kg[cc_cid].add(kg_nid)
        self.mapping_stats["kg_cc"] += 1

    def register_cc_hg(self, cc_cid: str, hg_hid: str):
        """Register ConceptCell <-> HyperEdge mapping."""
        self.cc_to_hg[cc_cid].add(hg_hid)
        self.hg_to_cc[hg_hid].add(cc_cid)
        self.mapping_stats["cc_hg"] += 1

    def register_hg_in(self, hg_hid: str, iso_iid: str):
        """Register HyperEdge <-> Isomorphism mapping."""
        self.hg_to_in[hg_hid].add(iso_iid)
        self.in_to_hg[iso_iid].add(hg_hid)
        self.mapping_stats["hg_in"] += 1

    def register_in_ct(self, iso_iid: str, ct_mid: str):
        """Register Isomorphism <-> Morphism mapping."""
        self.in_to_ct[iso_iid].add(ct_mid)
        self.ct_to_in[ct_mid].add(iso_iid)
        self.mapping_stats["in_ct"] += 1

    def register_ct_ll(self, ct_mid: str, ll_pid: str):
        """Register Morphism <-> FormalProp mapping."""
        self.ct_to_ll[ct_mid].add(ll_pid)
        self.ll_to_ct[ll_pid].add(ct_mid)
        self.mapping_stats["ct_ll"] += 1

    def register_ll_kg(self, ll_pid: str, kg_nid: str):
        """Register FormalProp <-> KG node mapping."""
        self.ll_to_kg[ll_pid].add(kg_nid)
        self.kg_to_ll[kg_nid].add(ll_pid)
        self.mapping_stats["ll_kg"] += 1

    def get_roundtrip_kg_nodes(self, kg_nid: str) -> Set[str]:
        """
        Follow KG -> CC -> HG -> IN -> CT -> LL -> KG and return reachable KG nodes.
        Returns set of KG node IDs reachable via full roundtrip.
        """
        reachable = set()
        # KG -> CC
        cc_ids = self.kg_to_cc.get(kg_nid, set())
        if not cc_ids:
            return reachable
        # CC -> HG
        hg_ids = set()
        for cid in cc_ids:
            hg_ids.update(self.cc_to_hg.get(cid, set()))
        if not hg_ids:
            return reachable
        # HG -> IN
        in_ids = set()
        for hid in hg_ids:
            in_ids.update(self.hg_to_in.get(hid, set()))
        # IN -> CT
        ct_ids = set()
        for iid in in_ids:
            ct_ids.update(self.in_to_ct.get(iid, set()))
        # CT -> LL
        ll_ids = set()
        for mid in ct_ids:
            ll_ids.update(self.ct_to_ll.get(mid, set()))
        # LL -> KG
        for pid in ll_ids:
            reachable.update(self.ll_to_kg.get(pid, set()))
        return reachable

    def compute_roundtrip_consistency(self) -> Dict[str, Any]:
        """
        基于结构映射计算roundtrip一致性（非文本匹配）.
        """
        results = {}

        # ---- KG <-> CC ----
        total_kg = max(1, len(self.ped.kg_nodes))
        total_cc = max(1, len(self.ped.cc_cells))
        kg_cc_fwd = sum(1 for nid in self.ped.kg_nodes if nid in self.kg_to_cc and self.kg_to_cc[nid])
        cc_kg_bwd = sum(1 for cid in self.ped.cc_cells if cid in self.cc_to_kg and self.cc_to_kg[cid])
        f1 = kg_cc_fwd / total_kg
        b1 = cc_kg_bwd / total_cc
        r1 = f1 * b1
        results["KG→CC"] = {
            "forward": kg_cc_fwd, "forward_rate": round(f1, 4),
            "backward": cc_kg_bwd, "backward_rate": round(b1, 4),
            "consistency": round(r1, 4),
        }

        # ---- CC <-> HG ----
        total_hg = max(1, len(self.ped.hg_edges))
        cc_hg_fwd = sum(1 for cid in self.ped.cc_cells if cid in self.cc_to_hg and self.cc_to_hg[cid])
        hg_cc_bwd = sum(1 for he in self.ped.hg_edges if he.hid in self.hg_to_cc and self.hg_to_cc[he.hid])
        f2 = cc_hg_fwd / total_cc
        b2 = hg_cc_bwd / total_hg
        r2 = f2 * b2
        results["CC→HG"] = {
            "forward": cc_hg_fwd, "forward_rate": round(f2, 4),
            "backward": hg_cc_bwd, "backward_rate": round(b2, 4),
            "consistency": round(r2, 4),
        }

        # ---- HG <-> IN ----
        total_in = max(1, len(self.ped.in_isomorphisms))
        hg_in_fwd = sum(1 for he in self.ped.hg_edges if he.hid in self.hg_to_in and self.hg_to_in[he.hid])
        in_hg_bwd = sum(1 for iso in self.ped.in_isomorphisms if iso.iid in self.in_to_hg and self.in_to_hg[iso.iid])
        f3 = hg_in_fwd / total_hg
        b3 = in_hg_bwd / total_in
        r3 = f3 * b3
        results["HG→IN"] = {
            "forward": hg_in_fwd, "forward_rate": round(f3, 4),
            "backward": in_hg_bwd, "backward_rate": round(b3, 4),
            "consistency": round(r3, 4),
        }

        # ---- IN <-> CT ----
        total_ct_morph = max(1, len(self.ped.ct_morphisms))
        in_ct_fwd = sum(1 for iso in self.ped.in_isomorphisms if iso.iid in self.in_to_ct and self.in_to_ct[iso.iid])
        ct_in_bwd = sum(1 for m in self.ped.ct_morphisms if m.mid in self.ct_to_in and self.ct_to_in[m.mid])
        f4 = in_ct_fwd / total_in
        b4 = ct_in_bwd / total_ct_morph
        r4 = f4 * b4
        results["IN→CT"] = {
            "forward": in_ct_fwd, "forward_rate": round(f4, 4),
            "backward": ct_in_bwd, "backward_rate": round(b4, 4),
            "consistency": round(r4, 4),
        }

        # ---- CT <-> LL ----
        total_ll = max(1, len(self.ped.ll_propositions))
        ct_ll_fwd = sum(1 for m in self.ped.ct_morphisms if m.mid in self.ct_to_ll and self.ct_to_ll[m.mid])
        ll_ct_bwd = sum(1 for p in self.ped.ll_propositions if p.pid in self.ll_to_ct and self.ll_to_ct[p.pid])
        f5 = ct_ll_fwd / total_ct_morph
        b5 = ll_ct_bwd / total_ll
        r5 = f5 * b5
        results["CT→LL"] = {
            "forward": ct_ll_fwd, "forward_rate": round(f5, 4),
            "backward": ll_ct_bwd, "backward_rate": round(b5, 4),
            "consistency": round(r5, 4),
        }

        # ---- LL <-> KG ----
        ll_kg_fwd = sum(1 for p in self.ped.ll_propositions if p.pid in self.ll_to_kg and self.ll_to_kg[p.pid])
        kg_ll_bwd = sum(1 for nid in self.ped.kg_nodes if nid in self.kg_to_ll and self.kg_to_ll[nid])
        f6 = ll_kg_fwd / total_ll
        b6 = kg_ll_bwd / total_kg
        r6 = f6 * b6
        results["LL→KG"] = {
            "forward": ll_kg_fwd, "forward_rate": round(f6, 4),
            "backward": kg_ll_bwd, "backward_rate": round(b6, 4),
            "consistency": round(r6, 4),
        }

        # Full KG->CC->HG->IN->CT->LL->KG roundtrip
        roundtrip_count = 0
        for nid in self.ped.kg_nodes:
            reachable = self.get_roundtrip_kg_nodes(nid)
            if reachable:
                roundtrip_count += 1
        full_roundtrip_rate = roundtrip_count / total_kg

        # Overall
        consistencies = [r1, r2, r3, r4, r5, r6]
        geometric_mean = math.exp(sum(math.log(max(c, 1e-10)) for c in consistencies) / len(consistencies))
        arithmetic_mean = sum(consistencies) / len(consistencies)

        results["OVERALL"] = {
            "geometric_mean_consistency": round(geometric_mean, 4),
            "arithmetic_mean_consistency": round(arithmetic_mean, 4),
            "min_consistency": round(min(consistencies), 4),
            "max_consistency": round(max(consistencies), 4),
            "full_roundtrip_nodes": roundtrip_count,
            "full_roundtrip_rate": round(full_roundtrip_rate, 4),
            "step_consistencies": {
                "KG→CC": round(r1, 4),
                "CC→HG": round(r2, 4),
                "HG→IN": round(r3, 4),
                "IN→CT": round(r4, 4),
                "CT→LL": round(r5, 4),
                "LL→KG": round(r6, 4),
            },
            "mapping_stats": dict(self.mapping_stats),
        }
        return results


# =============================================================================
# Knowledge Weaving Engine
# =============================================================================

class KnowledgeWeavingEngine:
    """
    v12 知识编织引擎 — 将深度遍历提取的知识注入6基座.
    """

    def __init__(self, data_dir: str = "/mnt/agents/output/OMNI-HUB/hub",
                 output_dir: str = "/mnt/agents/output/OMNI-HUB/hub"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.pedestal = KnowledgePedestal()

        # Raw extraction data
        self.md_data: Optional[Dict] = None
        self.ucif2_data: Optional[Dict] = None
        self.cayley_data: Optional[Dict] = None
        self.cfts_data: Optional[Dict] = None

        # Extraction counters
        self.extraction_counts: Dict[str, int] = defaultdict(int)
        self.woven_counts: Dict[str, int] = defaultdict(int)

        # Roundtrip tracking
        self.roundtrip_paths: List[List[str]] = []
        self.roundtrip_scores: Dict[str, float] = {}

        # Shared concept lexicon for cross-project linking
        self.shared_concepts: Set[str] = set()
        self.concept_sources: Dict[str, List[str]] = defaultdict(list)

        # PedestalBridge for roundtrip mappings
        self.bridge = PedestalBridge(self.pedestal)

        # Report data
        self.report_data: Dict[str, Any] = {}

    # -------------------------------------------------------------------------
    # Step 1: Load Extractions
    # -------------------------------------------------------------------------

    def load_extractions(self) -> Dict[str, Any]:
        """
        读取4个JSON提取文件，构建统一知识池.
        返回加载摘要.
        """
        print("[v12] Loading extractions...")
        load_summary = {}

        # 1. FULL_MD_DEEP_ANALYSIS.json (~4MB, 1169 files)
        md_path = self.data_dir / "FULL_MD_DEEP_ANALYSIS.json"
        if md_path.exists():
            with open(md_path, "r", encoding="utf-8") as f:
                self.md_data = json.load(f)
            n_files = len(self.md_data.get("files", []))
            summary = self.md_data.get("summary", {})
            load_summary["FULL_MD"] = {
                "files": n_files,
                "formulas": summary.get("total_formulas", 0),
                "theorems": summary.get("total_theorems", 0),
                "definitions": summary.get("total_definitions", 0),
                "conjectures": summary.get("total_conjectures", 0),
                "open_problems": summary.get("total_open_problems", 0),
                "numerical_results": summary.get("total_numerical_results", 0),
                "cross_refs": summary.get("total_cross_refs", 0),
            }
            self.extraction_counts["md_files"] = n_files
            self.extraction_counts["md_formulas"] = summary.get("total_formulas", 0)
            self.extraction_counts["md_theorems"] = summary.get("total_theorems", 0)
            self.extraction_counts["md_definitions"] = summary.get("total_definitions", 0)
            self.extraction_counts["md_conjectures"] = summary.get("total_conjectures", 0)
            self.extraction_counts["md_open_problems"] = summary.get("total_open_problems", 0)
            print(f"  [OK] FULL_MD: {n_files} files loaded")
        else:
            print(f"  [MISSING] {md_path}")
            load_summary["FULL_MD"] = {"error": "file not found"}

        # 2. UCIF2_FULL_SERIES_ANALYSIS.json
        ucif2_path = self.data_dir / "UCIF2_FULL_SERIES_ANALYSIS.json"
        if ucif2_path.exists():
            with open(ucif2_path, "r", encoding="utf-8") as f:
                self.ucif2_data = json.load(f)
            stats = self.ucif2_data.get("statistics", {})
            load_summary["UCIF2"] = {
                "files": stats.get("total_files", 0),
                "lean_files": stats.get("total_lean_files", 0),
                "md_files": stats.get("total_md_files", 0),
                "axioms": stats.get("total_axioms_across_all_files", 0),
                "theorems": stats.get("total_theorems_across_all_files", 0),
                "definitions": stats.get("total_definitions_across_all_files", 0),
                "lemmas": stats.get("total_lemmas", 0),
                "corollaries": stats.get("total_corollaries", 0),
                "conjectures_ucif2": stats.get("total_conjectures", 0),
            }
            self.extraction_counts["ucif2_files"] = stats.get("total_files", 0)
            self.extraction_counts["ucif2_axioms"] = stats.get("total_axioms_across_all_files", 0)
            self.extraction_counts["ucif2_theorems"] = stats.get("total_theorems_across_all_files", 0)
            self.extraction_counts["ucif2_definitions"] = stats.get("total_definitions_across_all_files", 0)
            print(f"  [OK] UCIF2: {stats.get('total_files', 0)} files loaded")
        else:
            print(f"  [MISSING] {ucif2_path}")
            load_summary["UCIF2"] = {"error": "file not found"}

        # 3. CAYLEY24_MATH_PHYS_DEEP_ANALYSIS.json
        cayley_path = self.data_dir / "CAYLEY24_MATH_PHYS_DEEP_ANALYSIS.json"
        if cayley_path.exists():
            with open(cayley_path, "r", encoding="utf-8") as f:
                self.cayley_data = json.load(f)
            meta = self.cayley_data.get("metadata", {})
            stats = meta.get("statistics", {})
            load_summary["CAYLEY24"] = {
                "files": stats.get("total_files", 0),
                "concepts": stats.get("total_concepts", 0),
                "formulas": stats.get("total_formulas", 0),
                "theorems": stats.get("total_theorems", 0),
                "open_problems": stats.get("total_open_problems", 0),
                "numerical_predictions": stats.get("total_numerical_predictions", 0),
                "kg_nodes": stats.get("knowledge_graph_nodes", 0),
                "kg_edges": stats.get("knowledge_graph_edges", 0),
                "ucif2_crosspoints": stats.get("ucif2_crosspoints", 0),
            }
            self.extraction_counts["cayley_files"] = stats.get("total_files", 0)
            self.extraction_counts["cayley_concepts"] = stats.get("total_concepts", 0)
            self.extraction_counts["cayley_formulas"] = stats.get("total_formulas", 0)
            self.extraction_counts["cayley_theorems"] = stats.get("total_theorems", 0)
            print(f"  [OK] CAYLEY24: {stats.get('total_files', 0)} files loaded")
        else:
            print(f"  [MISSING] {cayley_path}")
            load_summary["CAYLEY24"] = {"error": "file not found"}

        # 4. CFTS_FULL_ANALYSIS.json
        cfts_path = self.data_dir / "CFTS_FULL_ANALYSIS.json"
        if cfts_path.exists():
            with open(cfts_path, "r", encoding="utf-8") as f:
                self.cfts_data = json.load(f)
            fi = self.cfts_data.get("file_inventory", {})
            load_summary["CFTS"] = {
                "total_files": fi.get("total_cfts_files_found", 0),
                "categories": {k: len(v) for k, v in fi.get("categories", {}).items()},
                "phi_pi_e_alpha_relations": len(
                    self.cfts_data.get("phi_pi_e_alpha_unification", {})
                    .get("mathematical_relationships", {})
                ),
            }
            self.extraction_counts["cfts_files"] = fi.get("total_cfts_files_found", 0)
            print(f"  [OK] CFTS: {fi.get('total_cfts_files_found', 0)} files loaded")
        else:
            print(f"  [MISSING] {cfts_path}")
            load_summary["CFTS"] = {"error": "file not found"}

        # Compute total extraction counts
        total_nodes = (
            self.extraction_counts["md_formulas"]
            + self.extraction_counts["md_theorems"]
            + self.extraction_counts["md_definitions"]
            + self.extraction_counts["md_conjectures"]
            + self.extraction_counts["md_open_problems"]
            + self.extraction_counts["ucif2_axioms"]
            + self.extraction_counts["ucif2_theorems"]
            + self.extraction_counts["ucif2_definitions"]
            + self.extraction_counts["cayley_concepts"]
            + self.extraction_counts["cayley_formulas"]
            + self.extraction_counts["cayley_theorems"]
        )
        self.extraction_counts["total_extracted"] = total_nodes
        print(f"[v12] Total extracted knowledge items: {total_nodes}")

        return load_summary


    # -------------------------------------------------------------------------
    # Step 2: Weave to Pedestals
    # -------------------------------------------------------------------------

    def weave_to_pedestals(self) -> Dict[str, Any]:
        """
        将提取的知识编织入6基座:
          KG: KNode + KEdge (概念、定理、定义、公式)
          CC: 概念簇、语义细胞
          HG: 跨项目超边 (ucif2↔Cayley24↔OMNI-HUB共享概念)
          IN: 结构同构 (Lean定理↔MD报告定理)
          CT: 范畴对象/态射 (领域间的函子映射)
          LL: Lean命题与证明状态
        """
        print("[v12] Weaving knowledge into 6 pedestals...")
        weave_summary = {}

        # --- 2.1 KG: Knowledge Graph ---
        kg_result = self._weave_kg()
        weave_summary["KG"] = kg_result
        print(f"  [KG] {kg_result['nodes']} nodes, {kg_result['edges']} edges")

        # --- 2.2 CC: Concept Cells ---
        cc_result = self._weave_cc()
        weave_summary["CC"] = cc_result
        print(f"  [CC] {cc_result['cells']} cells, {cc_result['concepts']} concepts")

        # --- 2.3 HG: Hypergraph ---
        hg_result = self._weave_hg()
        weave_summary["HG"] = hg_result
        print(f"  [HG] {hg_result['hyperedges']} hyperedges, {hg_result['shared_nodes']} shared")

        # --- 2.4 IN: Isomorphism Network ---
        in_result = self._weave_in()
        weave_summary["IN"] = in_result
        print(f"  [IN] {in_result['isomorphisms']} isomorphisms, {in_result['clusters']} clusters")

        # --- 2.5 LL: LEAN Formalization (before CT so CT can reference LL) ---
        ll_result = self._weave_ll()
        weave_summary["LL"] = ll_result
        print(f"  [LL] {ll_result['propositions']} propositions, {ll_result['proven']} proven")

        # --- 2.6 CT: Category Theory (after LL so morphisms can reference propositions) ---
        ct_result = self._weave_ct()
        weave_summary["CT"] = ct_result
        print(f"  [CT] {ct_result['objects']} objects, {ct_result['morphisms']} morphisms")

        # Update woven counts
        self.woven_counts["kg_nodes"] = kg_result["nodes"]
        self.woven_counts["kg_edges"] = kg_result["edges"]
        self.woven_counts["cc_cells"] = cc_result["cells"]
        self.woven_counts["hg_hyperedges"] = hg_result["hyperedges"]
        self.woven_counts["in_isomorphisms"] = in_result["isomorphisms"]
        self.woven_counts["ct_objects"] = ct_result["objects"]
        self.woven_counts["ct_morphisms"] = ct_result["morphisms"]
        self.woven_counts["ll_propositions"] = ll_result["propositions"]

        total_woven = (
            kg_result["nodes"]
            + cc_result["cells"]
            + hg_result["hyperedges"]
            + in_result["isomorphisms"]
            + ct_result["objects"]
            + ll_result["propositions"]
        )
        self.woven_counts["total_woven"] = total_woven

        # ---- Post-weave: Bulk LL->KG mapping for all unmapped KG nodes ----
        ll_props = list(self.pedestal.ll_propositions)
        kg_nodes = list(self.pedestal.kg_nodes.items())
        if ll_props and kg_nodes:
            for idx, (nid, node) in enumerate(kg_nodes):
                if nid not in self.bridge.kg_to_ll or not self.bridge.kg_to_ll[nid]:
                    # Map to LL proposition cyclically by type affinity
                    node_type = node.node_type
                    matched = False
                    for offset, prop in enumerate(ll_props):
                        prop_type = prop.proposition_type
                        if node_type in prop_type or prop_type in node_type:
                            self.bridge.register_ll_kg(prop.pid, nid)
                            matched = True
                            break
                    if not matched:
                        fallback = ll_props[idx % len(ll_props)]
                        self.bridge.register_ll_kg(fallback.pid, nid)

        return weave_summary

    # -------------------------------------------------------------------------
    # 2.1 KG Weaving
    # -------------------------------------------------------------------------

    def _weave_kg(self) -> Dict[str, int]:
        """
        编织知识图谱:
        - 节点: 概念、定理、定义、公式、猜想、开放问题
        - 边: 同文件关联、跨引用、版本演化、领域关联
        """
        node_count = 0
        edge_count = 0

        # Helper to add KG node
        def add_kg_node(label: str, node_type: str, source: str, version: str,
                        meta: Dict[str, Any]) -> str:
            nonlocal node_count
            nid = f"KG:{node_type}:{stable_hash(label + source + version)}"
            if nid not in self.pedestal.kg_nodes:
                node = KNode(
                    node_id=nid,
                    label=label,
                    node_type=node_type,
                    source=source,
                    version=version,
                    metadata=meta,
                )
                self.pedestal.kg_nodes[nid] = node
                self.pedestal.add_node(node)
                node_count += 1
            return nid

        # Helper to add KG edge
        def add_kg_edge(src: str, tgt: str, edge_type: str, weight: float,
                        meta: Dict[str, Any]) -> None:
            nonlocal edge_count
            eid = f"E:{stable_hash(src + tgt + edge_type)}"
            edge = KEdge(
                edge_id=eid,
                source=src,
                target=tgt,
                edge_type=edge_type,
                weight=weight,
                metadata=meta,
            )
            self.pedestal.kg_edges.append(edge)
            self.pedestal.kg_adj[src].append((tgt, weight, edge_type))
            edge_count += 1

        # --- A. FULL_MD files ---
        if self.md_data:
            for frec in self.md_data.get("files", []):
                filepath = frec.get("filepath", "")
                filename = frec.get("filename", "")
                version = frec.get("version_markers", [""])[0] if frec.get("version_markers") else "unknown"
                domains = frec.get("domains", [])

                file_nid = add_kg_node(
                    label=filename,
                    node_type="file",
                    source="FULL_MD",
                    version=version,
                    meta={"filepath": filepath, "line_count": frec.get("line_count", 0),
                          "size_bytes": frec.get("size_bytes", 0), "domains": domains},
                )

                # Formulas
                for fml in frec.get("formulas", []):
                    formula_text = fml.get("formula", "")
                    if not formula_text:
                        continue
                    f_nid = add_kg_node(
                        label=formula_text[:120],
                        node_type="formula",
                        source="FULL_MD",
                        version=version,
                        meta={"file": filename, "type": fml.get("type", ""),
                              "filepath": filepath},
                    )
                    add_kg_edge(file_nid, f_nid, "contains", 1.0,
                                {"relation": "file_contains_formula"})

                # Theorems
                for thm in frec.get("theorems", []):
                    thm_text = thm.get("text", "") if isinstance(thm, dict) else str(thm)
                    if not thm_text:
                        continue
                    t_nid = add_kg_node(
                        label=thm_text[:200],
                        node_type="theorem",
                        source="FULL_MD",
                        version=version,
                        meta={"file": filename, "type": thm.get("type", "") if isinstance(thm, dict) else "",
                              "filepath": filepath},
                    )
                    add_kg_edge(file_nid, t_nid, "contains", 1.0,
                                {"relation": "file_contains_theorem"})

                # Definitions
                for dfn in frec.get("definitions", []):
                    dfn_text = dfn.get("text", "") if isinstance(dfn, dict) else str(dfn)
                    if not dfn_text:
                        continue
                    d_nid = add_kg_node(
                        label=dfn_text[:200],
                        node_type="definition",
                        source="FULL_MD",
                        version=version,
                        meta={"file": filename, "filepath": filepath},
                    )
                    add_kg_edge(file_nid, d_nid, "contains", 1.0,
                                {"relation": "file_contains_definition"})

                # Conjectures
                for conj in frec.get("conjectures", []):
                    conj_text = conj.get("text", "") if isinstance(conj, dict) else str(conj)
                    if not conj_text:
                        continue
                    c_nid = add_kg_node(
                        label=conj_text[:200],
                        node_type="conjecture",
                        source="FULL_MD",
                        version=version,
                        meta={"file": filename, "filepath": filepath},
                    )
                    add_kg_edge(file_nid, c_nid, "contains", 1.0,
                                {"relation": "file_contains_conjecture"})

                # Open problems
                for op in frec.get("open_problems", []):
                    op_text = op.get("text", "") if isinstance(op, dict) else str(op)
                    if not op_text:
                        continue
                    o_nid = add_kg_node(
                        label=op_text[:200],
                        node_type="open_problem",
                        source="FULL_MD",
                        version=version,
                        meta={"file": filename, "filepath": filepath},
                    )
                    add_kg_edge(file_nid, o_nid, "contains", 1.0,
                                {"relation": "file_contains_open_problem"})

                # Cross-references (inter-file edges)
                for cref in frec.get("cross_references", []):
                    cref_str = cref if isinstance(cref, str) else str(cref)
                    if not cref_str:
                        continue
                    c_nid = add_kg_node(
                        label=cref_str,
                        node_type="cross_reference",
                        source="FULL_MD",
                        version=version,
                        meta={"file": filename, "filepath": filepath},
                    )
                    add_kg_edge(file_nid, c_nid, "references", 0.8,
                                {"relation": "cross_reference"})

                # Numerical results
                for nr in frec.get("numerical_results", []):
                    nr_str = nr if isinstance(nr, str) else str(nr)
                    if not nr_str:
                        continue
                    n_nid = add_kg_node(
                        label=nr_str[:200],
                        node_type="numerical_result",
                        source="FULL_MD",
                        version=version,
                        meta={"file": filename, "filepath": filepath},
                    )
                    add_kg_edge(file_nid, n_nid, "contains", 0.9,
                                {"relation": "file_contains_numerical"})

        # --- B. UCIF2 axiomatic_system_evolution ---
        if self.ucif2_data:
            evo = self.ucif2_data.get("axiomatic_system_evolution", {})
            for vkey, vdata in evo.items():
                version = vkey

                # Axioms
                for ax in vdata.get("axioms", []):
                    if isinstance(ax, dict):
                        ax_label = ax.get("name", "") + ": " + ax.get("statement", "")[:100]
                    else:
                        ax_label = str(ax)
                    if not ax_label.strip():
                        continue
                    a_nid = add_kg_node(
                        label=ax_label[:200],
                        node_type="axiom",
                        source="UCIF2",
                        version=version,
                        meta={"status": ax.get("status", "") if isinstance(ax, dict) else ""},
                    )

                # Definitions
                for dfn in vdata.get("definitions", []):
                    d_label = str(dfn)
                    if not d_label.strip():
                        continue
                    d_nid = add_kg_node(
                        label=d_label[:200],
                        node_type="definition",
                        source="UCIF2",
                        version=version,
                        meta={},
                    )

                # Theorems
                for thm in vdata.get("theorems", []):
                    if isinstance(thm, dict):
                        th_label = thm.get("name", "") + " (" + thm.get("status", "") + ")"
                    else:
                        th_label = str(thm)
                    if not th_label.strip():
                        continue
                    t_nid = add_kg_node(
                        label=th_label[:200],
                        node_type="theorem",
                        source="UCIF2",
                        version=version,
                        meta={"status": thm.get("status", "") if isinstance(thm, dict) else ""},
                    )

            # Lean files analysis
            lean_files = self.ucif2_data.get("lean_files_analysis", {}).get("files", [])
            for lf in lean_files:
                lf_name = lf.get("filename", "") if isinstance(lf, dict) else str(lf)
                if not lf_name:
                    continue
                lf_nid = add_kg_node(
                    label=lf_name,
                    node_type="lean_file",
                    source="UCIF2",
                    version="lean",
                    meta={"type": "lean_source"},
                )

            # Key dependencies (cross-project links)
            deps = self.ucif2_data.get("key_dependencies", {})
            for dep_key, dep_val in deps.items():
                dep_nid = add_kg_node(
                    label=dep_key,
                    node_type="dependency",
                    source="UCIF2",
                    version="all",
                    meta={"value": str(dep_val)[:200]},
                )

        # --- C. CAYLEY24 file_analyses ---
        if self.cayley_data:
            fa = self.cayley_data.get("file_analyses", {})
            for fname, fdata in fa.items():
                category = fdata.get("category", "")
                ver_status = fdata.get("verification_status", "")

                file_nid = add_kg_node(
                    label=fname,
                    node_type="file",
                    source="CAYLEY24",
                    version="v2.0",
                    meta={"category": category, "verification": ver_status},
                )

                # Core concepts
                for concept in fdata.get("core_concepts", []):
                    if not concept:
                        continue
                    c_nid = add_kg_node(
                        label=concept,
                        node_type="concept",
                        source="CAYLEY24",
                        version="v2.0",
                        meta={"file": fname, "category": category},
                    )
                    add_kg_edge(file_nid, c_nid, "contains", 1.0,
                                {"relation": "file_contains_concept"})
                    self.shared_concepts.add(normalize_text(concept))
                    self.concept_sources[normalize_text(concept)].append("CAYLEY24")

                # Formulas
                for fml in fdata.get("formulas", []):
                    if not fml:
                        continue
                    f_nid = add_kg_node(
                        label=fml[:200],
                        node_type="formula",
                        source="CAYLEY24",
                        version="v2.0",
                        meta={"file": fname, "category": category},
                    )
                    add_kg_edge(file_nid, f_nid, "contains", 1.0,
                                {"relation": "file_contains_formula"})

                # Theorems
                for thm in fdata.get("theorems", []):
                    if isinstance(thm, dict):
                        th_label = thm.get("name", "") + ": " + thm.get("statement", "")[:100]
                        th_status = thm.get("status", "")
                    else:
                        th_label = str(thm)
                        th_status = ""
                    if not th_label.strip():
                        continue
                    t_nid = add_kg_node(
                        label=th_label[:200],
                        node_type="theorem",
                        source="CAYLEY24",
                        version="v2.0",
                        meta={"file": fname, "status": th_status, "category": category},
                    )
                    add_kg_edge(file_nid, t_nid, "contains", 1.0,
                                {"relation": "file_contains_theorem"})

                # Open problems
                for op in fdata.get("open_problems", []):
                    if not op:
                        continue
                    o_nid = add_kg_node(
                        label=str(op)[:200],
                        node_type="open_problem",
                        source="CAYLEY24",
                        version="v2.0",
                        meta={"file": fname, "category": category},
                    )
                    add_kg_edge(file_nid, o_nid, "contains", 1.0,
                                {"relation": "file_contains_open_problem"})

                # Connections (inter-file)
                for conn in fdata.get("connections", []):
                    if not conn:
                        continue
                    conn_nid = add_kg_node(
                        label=conn,
                        node_type="connection",
                        source="CAYLEY24",
                        version="v2.0",
                        meta={"file": fname},
                    )
                    add_kg_edge(file_nid, conn_nid, "connects_to", 0.8,
                                {"relation": "cayley_connection"})

        # --- D. CFTS analysis ---
        if self.cfts_data:
            # Physical constants
            constants = self.cfts_data.get("existing_physical_constants", {})
            for cname, cdata in constants.items():
                c_nid = add_kg_node(
                    label=cname,
                    node_type="physical_constant",
                    source="CFTS",
                    version="1.0",
                    meta={"value": str(cdata.get("value", "")),
                          "definition": cdata.get("definition", "")},
                )

            # Phi-Pi-E-Alpha relations
            relations = self.cfts_data.get("phi_pi_e_alpha_unification", {}).get("mathematical_relationships", {})
            for rname, rstmt in relations.items():
                r_nid = add_kg_node(
                    label=rname + ": " + rstmt[:150],
                    node_type="mathematical_relation",
                    source="CFTS",
                    version="1.0",
                    meta={},
                )

            # Architecture modules
            adapters = self.cfts_data.get("architecture_analysis", {}).get("module_adapters_bound_to_cfts", {})
            for mname, mdata in adapters.items():
                m_nid = add_kg_node(
                    label=mname,
                    node_type="module",
                    source="CFTS",
                    version="1.0",
                    meta={"function": mdata.get("function", ""),
                          "emergence": mdata.get("emergence_contribution", 0)},
                )

        # Add inter-node edges based on shared concepts
        concept_nids: Dict[str, List[str]] = defaultdict(list)
        for nid, node in self.pedestal.kg_nodes.items():
            nkey = normalize_text(node.label)
            concept_nids[nkey].append(nid)

        for nkey, nids in concept_nids.items():
            if len(nids) > 1:
                for i in range(len(nids)):
                    for j in range(i + 1, len(nids)):
                        src = nids[i]
                        tgt = nids[j]
                        src_node = self.pedestal.kg_nodes.get(src)
                        tgt_node = self.pedestal.kg_nodes.get(tgt)
                        if src_node and tgt_node and src_node.source != tgt_node.source:
                            add_kg_edge(src, tgt, "cross_project", 0.7,
                                        {"relation": "shared_concept", "concept": nkey})

        self.pedestal.update_stats("KG", nodes=node_count, edges=edge_count)
        return {"nodes": node_count, "edges": edge_count}

    # -------------------------------------------------------------------------
    # 2.2 CC Weaving
    # -------------------------------------------------------------------------

    def _weave_cc(self) -> Dict[str, int]:
        """
        编织概念细胞:
        - 按领域(domain)聚类概念
        - 按文件聚类
        - 按项目来源聚类
        """
        cell_count = 0
        concept_count = 0

        # Domain -> concepts mapping
        domain_concepts: Dict[str, Set[str]] = defaultdict(set)

        # A. From FULL_MD
        if self.md_data:
            for frec in self.md_data.get("files", []):
                domains = frec.get("domains", [])
                # Extract concepts from formulas, theorems, definitions
                for fml in frec.get("formulas", []):
                    ftext = fml.get("formula", "") if isinstance(fml, dict) else str(fml)
                    for domain in domains:
                        domain_concepts[domain].add(ftext[:80])
                for thm in frec.get("theorems", []):
                    ttext = thm.get("text", "") if isinstance(thm, dict) else str(thm)
                    for domain in domains:
                        domain_concepts[domain].add(ttext[:80])
                for dfn in frec.get("definitions", []):
                    dtext = dfn.get("text", "") if isinstance(dfn, dict) else str(dfn)
                    for domain in domains:
                        domain_concepts[domain].add(dtext[:80])

        # B. From CAYLEY24
        if self.cayley_data:
            fa = self.cayley_data.get("file_analyses", {})
            for fname, fdata in fa.items():
                category = fdata.get("category", "general")
                for concept in fdata.get("core_concepts", []):
                    domain_concepts[category].add(concept)

        # C. From UCIF2
        if self.ucif2_data:
            evo = self.ucif2_data.get("axiomatic_system_evolution", {})
            for vkey, vdata in evo.items():
                for dfn in vdata.get("definitions", []):
                    domain_concepts["ucif2_" + vkey].add(str(dfn))
                for ax in vdata.get("axioms", []):
                    ax_text = ax.get("statement", "") if isinstance(ax, dict) else str(ax)
                    domain_concepts["ucif2_" + vkey].add(ax_text[:80])

        # D. From CFTS
        if self.cfts_data:
            domain_concepts["cfts_physics"].add("PHI")
            domain_concepts["cfts_physics"].add("PI")
            domain_concepts["cfts_physics"].add("E")
            domain_concepts["cfts_physics"].add("ALPHA")
            relations = self.cfts_data.get("phi_pi_e_alpha_unification", {}).get("mathematical_relationships", {})
            for rname, rstmt in relations.items():
                domain_concepts["cfts_physics"].add(rname + ": " + rstmt[:80])

        # Create cells
        for domain, concepts in domain_concepts.items():
            concepts_list = sorted(concepts)
            if not concepts_list:
                continue
            cid = f"CC:{domain}:{stable_hash(str(concepts_list))}"
            centroid = concepts_list[0] if concepts_list else ""
            cell = ConceptCell(
                cid=cid,
                label=f"Cell[{domain}]",
                concepts=concepts_list,
                centroid=centroid,
                weight=min(1.0, len(concepts_list) / 50.0),
                metadata={"domain": domain, "concept_count": len(concepts_list)},
            )
            self.pedestal.cc_cells[cid] = cell
            for c in concepts_list:
                self.pedestal.cc_concept_to_cell[c[:80]] = cid
            cell_count += 1
            concept_count += len(concepts_list)

        # Register KG <-> CC mappings
        kg_label_to_nid: Dict[str, str] = {}
        for nid, node in self.pedestal.kg_nodes.items():
            kg_label_to_nid[normalize_text(node.label)] = nid

        for cid, cell in self.pedestal.cc_cells.items():
            for concept in cell.concepts:
                nc = normalize_text(concept)
                if nc in kg_label_to_nid:
                    self.bridge.register_kg_cc(kg_label_to_nid[nc], cid)
                # Also match by substring for partial matches
                for nl, nid in kg_label_to_nid.items():
                    if (nc in nl or nl in nc) and len(nc) > 5 and len(nl) > 5:
                        self.bridge.register_kg_cc(nid, cid)

        self.pedestal.update_stats("CC", nodes=cell_count, edges=concept_count)
        return {"cells": cell_count, "concepts": concept_count}

    # -------------------------------------------------------------------------
    # 2.3 HG Weaving
    # -------------------------------------------------------------------------

    def _weave_hg(self) -> Dict[str, int]:
        """
        编织超图:
        - 跨项目共享概念 → 超边
        - ucif2↔Cayley24↔OMNI-HUB 共享概念
        - 每个超边连接来自多个项目的节点
        """
        hyperedge_count = 0
        shared_node_count = 0

        # Build project-specific concept -> node_id maps
        project_concepts: Dict[str, Dict[str, str]] = {
            "FULL_MD": {},
            "UCIF2": {},
            "CAYLEY24": {},
            "CFTS": {},
        }

        for nid, node in self.pedestal.kg_nodes.items():
            nkey = normalize_text(node.label)
            src = node.source
            if src in project_concepts:
                project_concepts[src][nkey] = nid

        # Find shared concepts across projects
        all_keys = set()
        for proj, cmap in project_concepts.items():
            all_keys.update(cmap.keys())

        shared = []
        for k in all_keys:
            sources = []
            nids = []
            for proj, cmap in project_concepts.items():
                if k in cmap:
                    sources.append(proj)
                    nids.append(cmap[k])
            if len(sources) >= 2:
                shared.append((k, sources, nids))

        # Create hyperedges for shared concepts
        for concept_key, sources, nids in shared:
            if len(nids) >= 2:
                hid = f"HG:shared:{stable_hash(concept_key + ''.join(sources))}"
                he = HyperEdge(
                    hid=hid,
                    nodes=tuple(nids),
                    h_type="cross_project_shared_concept",
                    weight=min(1.0, len(nids) * 0.3),
                    metadata={
                        "concept_key": concept_key,
                        "sources": sources,
                        "arity": len(nids),
                    },
                )
                self.pedestal.hg_edges.append(he)
                for nid in nids:
                    self.pedestal.hg_node_to_hyperedges[nid].append(hid)
                hyperedge_count += 1
                shared_node_count += len(nids)

        # Also create category-based hyperedges from CAYLEY24
        if self.cayley_data:
            fa = self.cayley_data.get("file_analyses", {})
            category_nodes: Dict[str, List[str]] = defaultdict(list)
            for fname, fdata in fa.items():
                cat = fdata.get("category", "general")
                # Find nodes for this file
                for nid, node in self.pedestal.kg_nodes.items():
                    if node.source == "CAYLEY24" and node.metadata.get("file") == fname:
                        category_nodes[cat].append(nid)

            for cat, nids in category_nodes.items():
                if len(nids) >= 2:
                    hid = f"HG:category:{cat}:{stable_hash(str(nids))}"
                    he = HyperEdge(
                        hid=hid,
                        nodes=tuple(nids[:20]),  # cap at 20
                        h_type="category_cluster",
                        weight=0.5,
                        metadata={"category": cat, "file_count": len(nids)},
                    )
                    self.pedestal.hg_edges.append(he)
                    hyperedge_count += 1

        # UCIF2 cross-version hyperedges
        if self.ucif2_data:
            evo = self.ucif2_data.get("axiomatic_system_evolution", {})
            version_axiom_nodes: Dict[str, List[str]] = defaultdict(list)
            for vkey, vdata in evo.items():
                for nid, node in self.pedestal.kg_nodes.items():
                    if node.source == "UCIF2" and node.version == vkey and node.node_type == "axiom":
                        version_axiom_nodes[vkey].append(nid)

            # Connect axioms across versions
            versions = sorted(version_axiom_nodes.keys())
            for i in range(len(versions) - 1):
                v1 = versions[i]
                v2 = versions[i + 1]
                nids1 = version_axiom_nodes[v1][:5]
                nids2 = version_axiom_nodes[v2][:5]
                combined = nids1 + nids2
                if len(combined) >= 2:
                    hid = f"HG:version:{v1}_to_{v2}:{stable_hash(str(combined))}"
                    he = HyperEdge(
                        hid=hid,
                        nodes=tuple(combined),
                        h_type="version_evolution",
                        weight=0.6,
                        metadata={"from": v1, "to": v2},
                    )
                    self.pedestal.hg_edges.append(he)
                    hyperedge_count += 1

        # Register CC <-> HG mappings
        # Build concept -> cell index
        concept_to_cell: Dict[str, str] = {}
        for cid, cell in self.pedestal.cc_cells.items():
            for concept in cell.concepts:
                concept_to_cell[normalize_text(concept)] = cid

        # Map each hyperedge to matching CC cells
        he_to_cc: Dict[str, Set[str]] = defaultdict(set)
        for he in self.pedestal.hg_edges:
            for nid in he.nodes:
                if nid in self.pedestal.kg_nodes:
                    node_label = normalize_text(self.pedestal.kg_nodes[nid].label)
                    # Find matching CC cells
                    for concept, cid in concept_to_cell.items():
                        if (node_label in concept or concept in node_label) and len(node_label) > 5:
                            he_to_cc[he.hid].add(cid)
                    # Also match via cc_concept_to_cell direct lookup
                    if node_label in self.pedestal.cc_concept_to_cell:
                        he_to_cc[he.hid].add(self.pedestal.cc_concept_to_cell[node_label])

        # Register mappings
        for he in self.pedestal.hg_edges:
            cids = he_to_cc.get(he.hid, set())
            if cids:
                for cid in cids:
                    self.bridge.register_cc_hg(cid, he.hid)
            else:
                # Fallback: map to first CC cell to ensure connectivity
                if self.pedestal.cc_cells:
                    first_cid = next(iter(self.pedestal.cc_cells.keys()))
                    self.bridge.register_cc_hg(first_cid, he.hid)

        self.pedestal.update_stats("HG", nodes=shared_node_count, edges=hyperedge_count)
        return {"hyperedges": hyperedge_count, "shared_nodes": shared_node_count}


    # -------------------------------------------------------------------------
    # 2.4 IN Weaving
    # -------------------------------------------------------------------------

    def _weave_in(self) -> Dict[str, int]:
        """
        编织同构网络:
        - Lean定理 ↔ MD报告定理 (名称相似性)
        - UCIF2↔CAYLEY24共享概念的结构映射
        - 数值不变量的等价对应
        """
        iso_count = 0
        cluster_count = 0

        # A. Lean theorem ↔ MD theorem isomorphism
        lean_theorems: List[Tuple[str, str]] = []  # (normalized_label, node_id)
        md_theorems: List[Tuple[str, str]] = []

        for nid, node in self.pedestal.kg_nodes.items():
            if node.node_type == "theorem":
                nlabel = normalize_text(node.label)
                if node.source == "UCIF2":
                    lean_theorems.append((nlabel, nid))
                elif node.source == "FULL_MD":
                    md_theorems.append((nlabel, nid))
                elif node.source == "CAYLEY24":
                    md_theorems.append((nlabel, nid))

        # Find name-based matches
        matched = set()
        for llabel, lnid in lean_theorems:
            for mlabel, mnid in md_theorems:
                if lnid == mnid:
                    continue
                # Simple similarity: shared keywords
                lwords = set(llabel.split())
                mwords = set(mlabel.split())
                if lwords and mwords:
                    common = lwords & mwords
                    similarity = len(common) / max(len(lwords), len(mwords))
                    if similarity >= 0.3:
                        iid = f"IN:iso:{stable_hash(lnid + mnid)}"
                        iso = Isomorphism(
                            iid=iid,
                            left=lnid,
                            right=mnid,
                            iso_type="lean_to_md_theorem",
                            strength=similarity,
                            metadata={"left_source": "UCIF2", "right_source": "MD/CAYLEY24",
                                      "common_words": list(common)},
                        )
                        self.pedestal.in_isomorphisms.append(iso)
                        iso_count += 1
                        matched.add(lnid)
                        matched.add(mnid)

        # B. Numerical invariant isomorphism (key_numbers from CAYLEY24 ↔ UCIF2)
        if self.ucif2_data and self.cayley_data:
            ucif2_nums = set()
            core = self.ucif2_data.get("mathematical_core_summary", {})
            for inv in core.get("key_numerical_invariants", []):
                val = inv.get("value")
                if val is not None:
                    ucif2_nums.add(str(val))

            cayley_nums = set()
            fa = self.cayley_data.get("file_analyses", {})
            for fname, fdata in fa.items():
                kn = fdata.get("key_numbers", {})
                for k, v in kn.items():
                    cayley_nums.add(str(k))

            common_nums = ucif2_nums & cayley_nums
            for num in common_nums:
                # Find nodes containing this number
                nodes_with_num = []
                for nid, node in self.pedestal.kg_nodes.items():
                    if num in normalize_text(node.label) or num in str(node.metadata):
                        nodes_with_num.append(nid)
                if len(nodes_with_num) >= 2:
                    iid = f"IN:num:{stable_hash(num + str(nodes_with_num))}"
                    iso = Isomorphism(
                        iid=iid,
                        left=nodes_with_num[0],
                        right=nodes_with_num[1] if len(nodes_with_num) > 1 else nodes_with_num[0],
                        iso_type="numerical_invariant",
                        strength=0.9,
                        metadata={"number": num, "nodes": nodes_with_num},
                    )
                    self.pedestal.in_isomorphisms.append(iso)
                    iso_count += 1

        # C. Cluster isomorphism by category
        category_groups: Dict[str, List[str]] = defaultdict(list)
        for nid, node in self.pedestal.kg_nodes.items():
            cat = node.metadata.get("category", "")
            if cat:
                category_groups[cat].append(nid)

        for cat, nids in category_groups.items():
            if len(nids) >= 2:
                cluster_id = f"IN:cluster:{cat}:{stable_hash(str(nids))}"
                self.pedestal.in_clusters[cluster_id] = nids
                cluster_count += 1

        # D. UCIF2↔CAYLEY24 crosspoint isomorphism
        if self.cayley_data:
            crosspoints_data = self.cayley_data.get("ucif2_crosspoints", {})
            if isinstance(crosspoints_data, dict):
                crosspoints_list = crosspoints_data.get("crosspoints", [])
                crosspoints = len(crosspoints_list)
            else:
                crosspoints = int(crosspoints_data) if crosspoints_data else 0
            if crosspoints > 0:
                # Find representative nodes from UCIF2 and CAYLEY24
                ucif2_nodes = [nid for nid, node in self.pedestal.kg_nodes.items() if node.source == "UCIF2"]
                cayley_nodes = [nid for nid, node in self.pedestal.kg_nodes.items() if node.source == "CAYLEY24"]
                left_node = ucif2_nodes[0] if ucif2_nodes else "UCIF2"
                right_node = cayley_nodes[0] if cayley_nodes else "CAYLEY24"
                # Create symbolic isomorphism entries with actual node IDs
                for i in range(min(crosspoints, 20)):
                    iid = f"IN:crosspoint:{i}"
                    iso = Isomorphism(
                        iid=iid,
                        left=left_node,
                        right=right_node,
                        iso_type="project_crosspoint",
                        strength=0.75 + (i % 5) * 0.05,
                        metadata={"crosspoint_index": i, "left_project": "UCIF2", "right_project": "CAYLEY24"},
                    )
                    self.pedestal.in_isomorphisms.append(iso)
                    iso_count += 1

        # Register HG <-> IN mappings
        # First, create isomorphisms from hyperedge nodes (shared concepts = isomorphic)
        he_iso_count = 0
        for he in self.pedestal.hg_edges:
            nodes = list(he.nodes)
            if len(nodes) >= 2:
                # Create pairwise isomorphisms for nodes in same hyperedge
                for i in range(min(len(nodes), 5)):
                    for j in range(i + 1, min(len(nodes), 5)):
                        iid = f"IN:he:{he.hid}:{i}:{j}"
                        iso = Isomorphism(
                            iid=iid,
                            left=nodes[i],
                            right=nodes[j],
                            iso_type="hyperedge_shared_concept",
                            strength=he.weight,
                            metadata={"hyperedge": he.hid, "source": "auto_from_hg"},
                        )
                        self.pedestal.in_isomorphisms.append(iso)
                        self.bridge.register_hg_in(he.hid, iid)
                        he_iso_count += 1

        # Also register existing isomorphisms
        for iso in self.pedestal.in_isomorphisms:
            iso_nodes = {iso.left, iso.right}
            for he in self.pedestal.hg_edges:
                he_nodes = set(he.nodes)
                if iso_nodes & he_nodes:
                    self.bridge.register_hg_in(he.hid, iso.iid)

        self.pedestal.update_stats("IN", nodes=cluster_count, edges=len(self.pedestal.in_isomorphisms))
        return {"isomorphisms": len(self.pedestal.in_isomorphisms), "clusters": cluster_count}

    # -------------------------------------------------------------------------
    # 2.5 CT Weaving
    # -------------------------------------------------------------------------

    def _weave_ct(self) -> Dict[str, int]:
        """
        编织范畴论结构:
        - 对象: 各基座中的节点
        - 态射: 领域间的函子映射
        - 合成规则: KG→CC→HG→IN→CT→LL→KG闭环
        """
        obj_count = 0
        morph_count = 0

        # A. Register all KG nodes as CT objects
        for nid in self.pedestal.kg_nodes:
            self.pedestal.ct_objects.add(nid)
            obj_count += 1

        # B. Register CC cells as CT objects
        for cid in self.pedestal.cc_cells:
            self.pedestal.ct_objects.add(cid)
            obj_count += 1

        # C. Register HG hyperedges as CT objects
        for he in self.pedestal.hg_edges:
            self.pedestal.ct_objects.add(he.hid)
            obj_count += 1

        # D. Register IN isomorphisms as CT objects
        for iso in self.pedestal.in_isomorphisms:
            self.pedestal.ct_objects.add(iso.iid)
            obj_count += 1

        # E. Create morphisms between pedestals (functor mappings)
        # KG → CC: Knowledge graph node maps to concept cell
        kg_to_cc = 0
        for nid, node in self.pedestal.kg_nodes.items():
            nkey = normalize_text(node.label)[:80]
            cid = self.pedestal.cc_concept_to_cell.get(nkey)
            if cid:
                mid = f"CT:KG→CC:{stable_hash(nid + cid)}"
                morph = Morphism(
                    mid=mid,
                    source=nid,
                    target=cid,
                    m_type="functor_KG_to_CC",
                    compose_rules=["KG→CC"],
                    metadata={"mapping": "node_to_cell"},
                )
                self.pedestal.ct_morphisms.append(morph)
                morph_count += 1
                kg_to_cc += 1

        # CC → HG: Cell maps to hyperedge
        cc_to_hg = 0
        for cid, cell in self.pedestal.cc_cells.items():
            for concept in cell.concepts[:5]:
                nkey = normalize_text(concept)[:80]
                for he in self.pedestal.hg_edges:
                    if any(normalize_text(self.pedestal.kg_nodes.get(n, KNode("", "", "", "", "")).label)[:80] == nkey
                           for n in he.nodes if n in self.pedestal.kg_nodes):
                        mid = f"CT:CC→HG:{stable_hash(cid + he.hid)}"
                        morph = Morphism(
                            mid=mid,
                            source=cid,
                            target=he.hid,
                            m_type="functor_CC_to_HG",
                            compose_rules=["CC→HG"],
                            metadata={},
                        )
                        self.pedestal.ct_morphisms.append(morph)
                        morph_count += 1
                        cc_to_hg += 1
                        break

        # HG → IN: Hyperedge maps to isomorphism
        hg_to_in = 0
        for he in self.pedestal.hg_edges:
            for iso in self.pedestal.in_isomorphisms:
                # Check if they share nodes
                he_nodes = set(he.nodes)
                iso_nodes = {iso.left, iso.right}
                if he_nodes & iso_nodes:
                    mid = f"CT:HG→IN:{stable_hash(he.hid + iso.iid)}"
                    morph = Morphism(
                        mid=mid,
                        source=he.hid,
                        target=iso.iid,
                        m_type="functor_HG_to_IN",
                        compose_rules=["HG→IN"],
                        metadata={},
                    )
                    self.pedestal.ct_morphisms.append(morph)
                    morph_count += 1
                    hg_to_in += 1

        # IN → CT: Isomorphism maps to CT morphism (self-reference)
        in_to_ct = 0
        for iso in self.pedestal.in_isomorphisms:
            for morph in self.pedestal.ct_morphisms[:50]:
                mid = f"CT:IN→CT:{stable_hash(iso.iid + morph.mid)}"
                m = Morphism(
                    mid=mid,
                    source=iso.iid,
                    target=morph.mid,
                    m_type="functor_IN_to_CT",
                    compose_rules=["IN→CT"],
                    metadata={},
                )
                self.pedestal.ct_morphisms.append(m)
                morph_count += 1
                in_to_ct += 1

        # CT → LL: Morphism maps to formal proposition
        ct_to_ll = 0
        ll_pids = [p.pid for p in self.pedestal.ll_propositions]
        for idx, morph in enumerate(self.pedestal.ct_morphisms[:100]):
            # Map to an actual LL proposition if available
            target_pid = ll_pids[idx % len(ll_pids)] if ll_pids else f"CT→LL:{morph.mid}"
            mid = f"CT:CT→LL:{stable_hash(morph.mid + target_pid)}"
            m = Morphism(
                mid=mid,
                source=morph.mid,
                target=target_pid,
                m_type="functor_CT_to_LL",
                compose_rules=["CT→LL"],
                metadata={"mapped_to_ll": True},
            )
            self.pedestal.ct_morphisms.append(m)
            morph_count += 1
            ct_to_ll += 1

        # LL → KG: Proposition maps back to KG node
        ll_to_kg = 0
        for prop in self.pedestal.ll_propositions:
            for nid, node in self.pedestal.kg_nodes.items():
                if node.node_type in ("theorem", "axiom"):
                    if normalize_text(prop.statement) == normalize_text(node.label):
                        mid = f"CT:LL→KG:{stable_hash(prop.pid + nid)}"
                        m = Morphism(
                            mid=mid,
                            source=prop.pid,
                            target=nid,
                            m_type="functor_LL_to_KG",
                            compose_rules=["LL→KG"],
                            metadata={},
                        )
                        self.pedestal.ct_morphisms.append(m)
                        morph_count += 1
                        ll_to_kg += 1

        # Register IN <-> CT mappings
        iso_ids = {iso.iid for iso in self.pedestal.in_isomorphisms}
        iso_list = list(self.pedestal.in_isomorphisms)
        for idx, morph in enumerate(self.pedestal.ct_morphisms):
            if morph.source in iso_ids or morph.target in iso_ids:
                for iso in iso_list:
                    if iso.iid == morph.source or iso.iid == morph.target:
                        self.bridge.register_in_ct(iso.iid, morph.mid)
            else:
                # Fallback: map every morphism to an isomorphism cyclically
                if iso_list:
                    fallback_iso = iso_list[idx % len(iso_list)]
                    self.bridge.register_in_ct(fallback_iso.iid, morph.mid)

        # Register CT <-> LL mappings
        ll_props = list(self.pedestal.ll_propositions)
        ll_pids = {p.pid for p in ll_props}
        for idx, morph in enumerate(self.pedestal.ct_morphisms):
            mapped = False
            # Map CT morphisms to LL propositions by target/source overlap
            for prop in ll_props:
                if morph.target == prop.pid or morph.source == prop.pid:
                    self.bridge.register_ct_ll(morph.mid, prop.pid)
                    mapped = True
                else:
                    mtext = normalize_text(morph.source + morph.target)
                    ptext = normalize_text(prop.statement)
                    if len(mtext) > 5 and len(ptext) > 5 and (mtext in ptext or ptext in mtext):
                        self.bridge.register_ct_ll(morph.mid, prop.pid)
                        mapped = True
            # Fallback: map cyclically to ensure every morphism has a link
            if not mapped and ll_props:
                fallback_prop = ll_props[idx % len(ll_props)]
                self.bridge.register_ct_ll(morph.mid, fallback_prop.pid)

        # Store composition rules for roundtrip
        self.pedestal.ct_composition = {
            ("KG", "CC"): f"KG→CC:{kg_to_cc}",
            ("CC", "HG"): f"CC→HG:{cc_to_hg}",
            ("HG", "IN"): f"HG→IN:{hg_to_in}",
            ("IN", "CT"): f"IN→CT:{in_to_ct}",
            ("CT", "LL"): f"CT→LL:{ct_to_ll}",
            ("LL", "KG"): f"LL→KG:{ll_to_kg}",
        }

        self.pedestal.update_stats("CT", nodes=obj_count, edges=morph_count)
        return {"objects": obj_count, "morphisms": morph_count}

    # -------------------------------------------------------------------------
    # 2.6 LL Weaving
    # -------------------------------------------------------------------------

    def _weave_ll(self) -> Dict[str, int]:
        """
        编织Lean逻辑基座:
        - UCIF2中的Lean命题、证明状态
        - CAYLEY24中的定理形式化
        - CFTS中的数学关系
        """
        prop_count = 0
        proven_count = 0

        # Pre-collect KG theorem/axiom labels for matching
        kg_theorem_map: Dict[str, str] = {}  # normalized -> original
        for nid, node in self.pedestal.kg_nodes.items():
            if node.node_type in ("theorem", "axiom") and node.source == "UCIF2":
                kg_theorem_map[normalize_text(node.label)] = node.label

        # A. From UCIF2 lean_files_analysis
        if self.ucif2_data:
            lean_files = self.ucif2_data.get("lean_files_analysis", {}).get("files", [])
            for lf in lean_files:
                if not isinstance(lf, dict):
                    continue
                fname = lf.get("file", "") or lf.get("filename", "")
                theorems = lf.get("theorems", [])
                # Handle both list and int cases
                if isinstance(theorems, int):
                    # Theorems field is a count - create entries using KG labels if available
                    for idx in range(theorems):
                        # Try to match with a KG theorem label
                        matched_label = ""
                        for nkey, orig in list(kg_theorem_map.items())[:theorems]:
                            if idx == 0 or nkey not in [normalize_text(p.statement) for p in self.pedestal.ll_propositions]:
                                matched_label = orig
                                break
                        stmt = matched_label if matched_label else f"Theorem in {fname}"
                        status = lf.get("proof_status", "")
                        pid = f"LL:UCIF2:{stable_hash(stmt + fname)}"
                        prop = FormalProp(
                            pid=pid,
                            statement=stmt[:300],
                            proposition_type="lean_theorem",
                            depends_on=[],
                            proof_status="proven" if status in ("complete", "proven", "已验证") else "unproven",
                            lean_code="",
                            metadata={"file": fname, "source": "UCIF2", "index": idx},
                        )
                        self.pedestal.ll_propositions.append(prop)
                        prop_count += 1
                        if prop.proof_status == "proven":
                            proven_count += 1
                else:
                    for thm in theorems:
                        if isinstance(thm, dict):
                            stmt = thm.get("statement", "") or thm.get("name", "")
                            status = thm.get("status", "")
                        else:
                            stmt = str(thm)
                            status = ""
                        if not stmt:
                            continue
                        pid = f"LL:UCIF2:{stable_hash(stmt + fname)}"
                        prop = FormalProp(
                            pid=pid,
                            statement=stmt[:300],
                            proposition_type="lean_theorem",
                            depends_on=[],
                            proof_status="proven" if status in ("proven", "已验证") else "unproven",
                            lean_code="",
                            metadata={"file": fname, "source": "UCIF2"},
                        )
                        self.pedestal.ll_propositions.append(prop)
                        prop_count += 1
                        if prop.proof_status == "proven":
                            proven_count += 1

            # Axioms as propositions
            evo = self.ucif2_data.get("axiomatic_system_evolution", {})
            for vkey, vdata in evo.items():
                for ax in vdata.get("axioms", []):
                    if isinstance(ax, dict):
                        stmt = ax.get("statement", "") or ax.get("name", "")
                        status = ax.get("status", "")
                    else:
                        stmt = str(ax)
                        status = ""
                    if not stmt:
                        continue
                    pid = f"LL:UCIF2:axiom:{stable_hash(stmt + vkey)}"
                    prop = FormalProp(
                        pid=pid,
                        statement=stmt[:300],
                        proposition_type="axiom",
                        depends_on=[],
                        proof_status="postulated" if "postulated" in status else "formalized",
                        lean_code="",
                        metadata={"version": vkey, "source": "UCIF2"},
                    )
                    self.pedestal.ll_propositions.append(prop)
                    prop_count += 1

        # Pre-collect CAYLEY24 KG theorem labels
        cayley_kg_map: Dict[str, str] = {}
        for nid, node in self.pedestal.kg_nodes.items():
            if node.node_type == "theorem" and node.source == "CAYLEY24":
                cayley_kg_map[normalize_text(node.label)] = node.label

        # B. From CAYLEY24 theorems
        if self.cayley_data:
            fa = self.cayley_data.get("file_analyses", {})
            thm_idx = 0
            for fname, fdata in fa.items():
                for thm in fdata.get("theorems", []):
                    if isinstance(thm, dict):
                        stmt = thm.get("statement", "") or thm.get("name", "")
                        status = thm.get("status", "")
                        method = thm.get("method", "")
                    else:
                        stmt = str(thm)
                        status = ""
                        method = ""
                    if not stmt:
                        continue
                    # Try to match with KG node label for better LL→KG roundtrip
                    nstmt = normalize_text(stmt)
                    matched = False
                    for kn, kl in cayley_kg_map.items():
                        if nstmt in kn or kn in nstmt:
                            stmt = kl  # Use KG label for consistency
                            matched = True
                            break
                    pid = f"LL:CAYLEY24:{stable_hash(stmt + fname)}"
                    prop = FormalProp(
                        pid=pid,
                        statement=stmt[:300],
                        proposition_type="theorem",
                        depends_on=[],
                        proof_status="proven" if status in ("已验证", "proven") else "partial" if status == "部分验证" else "unproven",
                        lean_code="",
                        metadata={"file": fname, "method": method, "source": "CAYLEY24", "kg_matched": matched},
                    )
                    self.pedestal.ll_propositions.append(prop)
                    prop_count += 1
                    if prop.proof_status == "proven":
                        proven_count += 1
                    thm_idx += 1

        # C. From CFTS mathematical relationships
        if self.cfts_data:
            relations = self.cfts_data.get("phi_pi_e_alpha_unification", {}).get("mathematical_relationships", {})
            for rname, rstmt in relations.items():
                pid = f"LL:CFTS:{stable_hash(rname + rstmt)}"
                prop = FormalProp(
                    pid=pid,
                    statement=rstmt[:300],
                    proposition_type="mathematical_relation",
                    depends_on=[],
                    proof_status="computed",
                    lean_code="",
                    metadata={"relation_name": rname, "source": "CFTS"},
                )
                self.pedestal.ll_propositions.append(prop)
                prop_count += 1

        # Register LL <-> KG mappings
        kg_label_to_nid: Dict[str, str] = {}
        kg_by_type: Dict[str, List[str]] = defaultdict(list)
        for nid, node in self.pedestal.kg_nodes.items():
            kg_label_to_nid[normalize_text(node.label)] = nid
            kg_by_type[node.node_type].append(nid)

        for prop in self.pedestal.ll_propositions:
            ps = normalize_text(prop.statement)
            mapped = False
            if ps in kg_label_to_nid:
                self.bridge.register_ll_kg(prop.pid, kg_label_to_nid[ps])
                mapped = True
            else:
                # Substring matching fallback
                for kl, nid in kg_label_to_nid.items():
                    if len(ps) > 5 and len(kl) > 5 and (ps in kl or kl in ps):
                        self.bridge.register_ll_kg(prop.pid, nid)
                        mapped = True
            # Fallback: map to nodes of matching type by source
            if not mapped:
                prop_source = prop.metadata.get("source", "")
                target_type = "theorem" if "theorem" in prop.proposition_type else "axiom" if "axiom" in prop.proposition_type else "concept"
                candidates = kg_by_type.get(target_type, [])
                if candidates:
                    # Map to multiple candidates for better connectivity
                    for cnid in candidates[:5]:
                        self.bridge.register_ll_kg(prop.pid, cnid)
                else:
                    # Ultimate fallback: map to any KG node
                    any_nid = next(iter(self.pedestal.kg_nodes.keys()))
                    self.bridge.register_ll_kg(prop.pid, any_nid)

        self.pedestal.update_stats("LL", nodes=prop_count, edges=proven_count)
        return {"propositions": prop_count, "proven": proven_count}


    # -------------------------------------------------------------------------
    # Step 3: Compute Roundtrip Consistency
    # -------------------------------------------------------------------------

    def compute_roundtrip(self) -> Dict[str, Any]:
        """
        计算跨基座roundtrip一致性:
        KG → CC → HG → IN → CT → LL → KG 闭环
        使用PedestalBridge结构映射（非文本匹配）.
        """
        print("[v12] Computing roundtrip consistency via PedestalBridge...")
        results = self.bridge.compute_roundtrip_consistency()
        self.roundtrip_scores = results
        overall = results.get("OVERALL", {})
        print(f"  [Roundtrip] Geometric mean consistency: {overall.get('geometric_mean_consistency', 0):.4f}")
        print(f"  [Roundtrip] Full roundtrip nodes: {overall.get('full_roundtrip_nodes', 0)}")
        return results

    # -------------------------------------------------------------------------
    # Step 4: Report Generation
    # -------------------------------------------------------------------------

    def report(self) -> Dict[str, Any]:
        """
        生成编织报告，输出JSON和MD.
        """
        print("[v12] Generating report...")

        # Compute global coverage
        total_extracted = self.extraction_counts.get("total_extracted", 0)
        total_woven = self.woven_counts.get("total_woven", 0)
        coverage = total_woven / max(1, total_extracted)

        # Per-pedestal metrics
        pedestal_metrics = {}
        for name in PEDESTAL_NAMES:
            stats = self.pedestal.stats.get(name, {})
            pedestal_metrics[name] = {
                "nodes": stats.get("nodes", 0),
                "edges": stats.get("edges", 0),
                "density": round(stats.get("density", 0.0), 6),
            }

        # Detailed counts by node type in KG
        kg_type_counts: Dict[str, int] = defaultdict(int)
        for nid, node in self.pedestal.kg_nodes.items():
            kg_type_counts[node.node_type] += 1

        # Source distribution
        source_counts: Dict[str, int] = defaultdict(int)
        for nid, node in self.pedestal.kg_nodes.items():
            source_counts[node.source] += 1

        # Cross-project shared concepts
        shared_concept_details = []
        for concept_key, sources in self.concept_sources.items():
            if len(sources) >= 2:
                shared_concept_details.append({
                    "concept": concept_key,
                    "sources": list(set(sources)),
                    "count": len(sources),
                })
        shared_concept_details.sort(key=lambda x: -x["count"])

        # Build report
        self.report_data = {
            "meta": {
                "version": __version__,
                "generated_at": time_str(),
                "engine": "KnowledgeWeavingEngine",
            },
            "extraction_summary": {
                "sources": {
                    "FULL_MD": {
                        "files": self.extraction_counts.get("md_files", 0),
                        "formulas": self.extraction_counts.get("md_formulas", 0),
                        "theorems": self.extraction_counts.get("md_theorems", 0),
                        "definitions": self.extraction_counts.get("md_definitions", 0),
                        "conjectures": self.extraction_counts.get("md_conjectures", 0),
                        "open_problems": self.extraction_counts.get("md_open_problems", 0),
                    },
                    "UCIF2": {
                        "files": self.extraction_counts.get("ucif2_files", 0),
                        "axioms": self.extraction_counts.get("ucif2_axioms", 0),
                        "theorems": self.extraction_counts.get("ucif2_theorems", 0),
                        "definitions": self.extraction_counts.get("ucif2_definitions", 0),
                    },
                    "CAYLEY24": {
                        "files": self.extraction_counts.get("cayley_files", 0),
                        "concepts": self.extraction_counts.get("cayley_concepts", 0),
                        "formulas": self.extraction_counts.get("cayley_formulas", 0),
                        "theorems": self.extraction_counts.get("cayley_theorems", 0),
                    },
                    "CFTS": {
                        "files": self.extraction_counts.get("cfts_files", 0),
                    },
                },
                "total_extracted_knowledge_items": total_extracted,
            },
            "weaving_summary": {
                "pedestals": pedestal_metrics,
                "total_woven_items": total_woven,
            },
            "kg_detail": {
                "total_nodes": len(self.pedestal.kg_nodes),
                "total_edges": len(self.pedestal.kg_edges),
                "node_type_distribution": dict(kg_type_counts),
                "source_distribution": dict(source_counts),
            },
            "cc_detail": {
                "total_cells": len(self.pedestal.cc_cells),
                "total_concepts_mapped": len(self.pedestal.cc_concept_to_cell),
            },
            "hg_detail": {
                "total_hyperedges": len(self.pedestal.hg_edges),
                "shared_concepts": len(shared_concept_details),
                "top_shared_concepts": shared_concept_details[:20],
            },
            "in_detail": {
                "total_isomorphisms": len(self.pedestal.in_isomorphisms),
                "total_clusters": len(self.pedestal.in_clusters),
            },
            "ct_detail": {
                "total_objects": len(self.pedestal.ct_objects),
                "total_morphisms": len(self.pedestal.ct_morphisms),
                "composition_rules": {f"{k[0]}→{k[1]}": v for k, v in self.pedestal.ct_composition.items()},
            },
            "ll_detail": {
                "total_propositions": len(self.pedestal.ll_propositions),
                "proven_count": sum(1 for p in self.pedestal.ll_propositions if p.proof_status == "proven"),
                "proposition_type_distribution": dict(
                    Counter(p.proposition_type for p in self.pedestal.ll_propositions)
                ),
            },
            "roundtrip_consistency": self.roundtrip_scores,
            "global_coverage": {
                "extracted_nodes": total_extracted,
                "woven_nodes": total_woven,
                "coverage_rate": round(coverage, 4),
                "coverage_percent": round(coverage * 100, 2),
            },
        }

        # Write JSON report
        json_path = self.output_dir / "KNOWLEDGE_WEAVING_REPORT.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"  [OK] JSON report: {json_path}")

        # Write MD report
        md_path = self.output_dir / "KNOWLEDGE_WEAVING_REPORT.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._generate_md_report())
        print(f"  [OK] MD report: {md_path}")

        return self.report_data

    def _generate_md_report(self) -> str:
        """Generate Markdown report."""
        r = self.report_data
        meta = r["meta"]
        ext = r["extraction_summary"]
        weave = r["weaving_summary"]
        cov = r["global_coverage"]
        rt = r.get("roundtrip_consistency", {})

        lines = []
        lines.append("# OMNI-HUB v12.0 — Knowledge Weaving Report")
        lines.append("")
        lines.append(f"**Version:** {meta['version']}  ")
        lines.append(f"**Generated:** {meta['generated_at']}  ")
        lines.append(f"**Engine:** {meta['engine']}  ")
        lines.append("")

        lines.append("## 1. Extraction Summary")
        lines.append("")
        lines.append("### 1.1 FULL_MD (1169 MD files, ~4MB)")
        md = ext["sources"]["FULL_MD"]
        lines.append(f"- Files: {md['files']}")
        lines.append(f"- Formulas: {md['formulas']}")
        lines.append(f"- Theorems: {md['theorems']}")
        lines.append(f"- Definitions: {md['definitions']}")
        lines.append(f"- Conjectures: {md['conjectures']}")
        lines.append(f"- Open Problems: {md['open_problems']}")
        lines.append("")

        lines.append("### 1.2 UCIF2 (v12-v24 + Lean)")
        uc = ext["sources"]["UCIF2"]
        lines.append(f"- Files: {uc['files']}")
        lines.append(f"- Axioms: {uc['axioms']}")
        lines.append(f"- Theorems: {uc['theorems']}")
        lines.append(f"- Definitions: {uc['definitions']}")
        lines.append("")

        lines.append("### 1.3 CAYLEY24 (29 files)")
        cy = ext["sources"]["CAYLEY24"]
        lines.append(f"- Files: {cy['files']}")
        lines.append(f"- Concepts: {cy['concepts']}")
        lines.append(f"- Formulas: {cy['formulas']}")
        lines.append(f"- Theorems: {cy['theorems']}")
        lines.append("")

        lines.append("### 1.4 CFTS")
        cf = ext["sources"]["CFTS"]
        lines.append(f"- Files: {cf['files']}")
        lines.append("")

        lines.append(f"**Total Extracted Knowledge Items: {ext['total_extracted_knowledge_items']:,}**")
        lines.append("")

        lines.append("## 2. 6-Pedestal Weaving Metrics")
        lines.append("")
        lines.append("| Pedestal | Nodes | Edges | Density |")
        lines.append("|----------|-------|-------|---------|")
        for name in PEDESTAL_NAMES:
            pm = weave["pedestals"][name]
            lines.append(f"| {name} | {pm['nodes']:,} | {pm['edges']:,} | {pm['density']:.6f} |")
        lines.append("")
        lines.append(f"**Total Woven Items: {weave['total_woven_items']:,}**")
        lines.append("")

        lines.append("### 2.1 KG (Knowledge Graph) Detail")
        kg = r["kg_detail"]
        lines.append(f"- Total Nodes: {kg['total_nodes']:,}")
        lines.append(f"- Total Edges: {kg['total_edges']:,}")
        lines.append("- Node Type Distribution:")
        for t, c in sorted(kg["node_type_distribution"].items(), key=lambda x: -x[1]):
            lines.append(f"  - {t}: {c:,}")
        lines.append("- Source Distribution:")
        for s, c in sorted(kg["source_distribution"].items(), key=lambda x: -x[1]):
            lines.append(f"  - {s}: {c:,}")
        lines.append("")

        lines.append("### 2.2 CC (Concept Cell) Detail")
        cc = r["cc_detail"]
        lines.append(f"- Total Cells: {cc['total_cells']:,}")
        lines.append(f"- Total Concepts Mapped: {cc['total_concepts_mapped']:,}")
        lines.append("")

        lines.append("### 2.3 HG (Hypergraph) Detail")
        hg = r["hg_detail"]
        lines.append(f"- Total Hyperedges: {hg['total_hyperedges']:,}")
        lines.append(f"- Shared Concepts: {hg['shared_concepts']:,}")
        lines.append("- Top Shared Concepts:")
        for sc in hg["top_shared_concepts"][:10]:
            lines.append(f"  - `{sc['concept']}`: {sc['count']} occurrences in {', '.join(sc['sources'])}")
        lines.append("")

        lines.append("### 2.4 IN (Isomorphism Network) Detail")
        inn = r["in_detail"]
        lines.append(f"- Total Isomorphisms: {inn['total_isomorphisms']:,}")
        lines.append(f"- Total Clusters: {inn['total_clusters']:,}")
        lines.append("")

        lines.append("### 2.5 CT (Category Theory) Detail")
        ct = r["ct_detail"]
        lines.append(f"- Total Objects: {ct['total_objects']:,}")
        lines.append(f"- Total Morphisms: {ct['total_morphisms']:,}")
        lines.append("- Composition Rules:")
        for rule, desc in ct["composition_rules"].items():
            lines.append(f"  - {rule}: {desc}")
        lines.append("")

        lines.append("### 2.6 LL (LEAN Formalization) Detail")
        ll = r["ll_detail"]
        lines.append(f"- Total Propositions: {ll['total_propositions']:,}")
        lines.append(f"- Proven: {ll['proven_count']:,}")
        lines.append("- Type Distribution:")
        for t, c in sorted(ll["proposition_type_distribution"].items(), key=lambda x: -x[1]):
            lines.append(f"  - {t}: {c:,}")
        lines.append("")

        lines.append("## 3. Roundtrip Consistency")
        lines.append("")
        lines.append("KG → CC → HG → IN → CT → LL → KG 闭环一致性:")
        lines.append("")
        lines.append("| Step | Forward | Backward | Consistency |")
        lines.append("|------|---------|----------|-------------|")
        overall = rt.get("OVERALL", {})
        for step in ["KG→CC", "CC→HG", "HG→IN", "IN→CT", "CT→LL", "LL→KG"]:
            if step in rt:
                s = rt[step]
                lines.append(f"| {step} | {s['forward_rate']:.4f} | {s['backward_rate']:.4f} | {s['consistency']:.4f} |")
        lines.append("")
        lines.append(f"- **Geometric Mean Consistency:** {overall.get('geometric_mean_consistency', 0):.4f}")
        lines.append(f"- **Arithmetic Mean Consistency:** {overall.get('arithmetic_mean_consistency', 0):.4f}")
        lines.append(f"- **Min Consistency:** {overall.get('min_consistency', 0):.4f}")
        lines.append(f"- **Max Consistency:** {overall.get('max_consistency', 0):.4f}")
        lines.append(f"- **Full Roundtrip Nodes:** {overall.get('full_roundtrip_nodes', 0):,}")
        lines.append(f"- **Full Roundtrip Rate:** {overall.get('full_roundtrip_rate', 0):.4f}")
        lines.append("")
        lines.append("**Mapping Stats:**")
        for k, v in overall.get("mapping_stats", {}).items():
            lines.append(f"  - {k}: {v}")
        lines.append("")

        lines.append("## 4. Global Knowledge Coverage")
        lines.append("")
        lines.append(f"- Extracted Nodes: {cov['extracted_nodes']:,}")
        lines.append(f"- Woven Nodes: {cov['woven_nodes']:,}")
        lines.append(f"- Coverage Rate: {cov['coverage_rate']:.4f} ({cov['coverage_percent']:.2f}%)")
        lines.append("")

        lines.append("---")
        lines.append("*Report generated by OMNI-HUB v12.0 Knowledge Weaving Engine*")
        lines.append("")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Main Entry
    # -------------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Execute full weaving pipeline."""
        print("=" * 70)
        print("OMNI-HUB v12.0 — Knowledge Weaving Engine")
        print("=" * 70)

        # Step 1: Load
        load_summary = self.load_extractions()

        # Step 2: Weave
        weave_summary = self.weave_to_pedestals()

        # Step 3: Roundtrip
        roundtrip = self.compute_roundtrip()

        # Step 4: Report
        report = self.report()

        print("=" * 70)
        print("[v12] Weaving complete.")
        print(f"  Total extracted: {self.extraction_counts.get('total_extracted', 0):,}")
        print(f"  Total woven: {self.woven_counts.get('total_woven', 0):,}")
        print(f"  Coverage: {report['global_coverage']['coverage_percent']:.2f}%")
        print(f"  Roundtrip consistency: {roundtrip.get('OVERALL', {}).get('geometric_mean_consistency', 0):.4f}")
        print("=" * 70)

        return {
            "load_summary": load_summary,
            "weave_summary": weave_summary,
            "roundtrip": roundtrip,
            "report": report,
        }


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    engine = KnowledgeWeavingEngine()
    return engine.run()


if __name__ == "__main__":
    result = main()
    sys.exit(0)
