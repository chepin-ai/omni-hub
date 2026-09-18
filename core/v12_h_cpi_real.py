#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — Real H Concordance & CPI Cross-Project Integration Calculator
================================================================================
基于真实JSON数据（UCIF2、Cayley24、OMNI-HUB）计算H协和度和CPI跨项目整合指标。

输入文件:
  1. UCIF2_FULL_SERIES_ANALYSIS.json
  2. CAYLEY24_MATH_PHYS_DEEP_ANALYSIS.json
  3. FULL_MD_DEEP_ANALYSIS.json
  4. TRIANGLE_COUPLING_REPORT.json

输出:
  - H_CPI_REAL_COMPUTATION.json (计算结果)
  - H_CPI_REAL_COMPUTATION.md (报告)

Author: Cross-Project Coupling Analysis Expert
Date: 2026-09-17
Version: 1.0.0
"""

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

import numpy as np
from scipy.stats import entropy

# ───────────────────────────── 路径配置 ─────────────────────────────
BASE_DIR = Path("/mnt/agents/output/OMNI-HUB")
INPUT_DIR = BASE_DIR / "hub"
OUTPUT_DIR = BASE_DIR / "hub"
CORE_DIR = BASE_DIR / "core"

UCIF2_PATH = INPUT_DIR / "UCIF2_FULL_SERIES_ANALYSIS.json"
CAYLEY24_PATH = INPUT_DIR / "CAYLEY24_MATH_PHYS_DEEP_ANALYSIS.json"
OMNI_PATH = INPUT_DIR / "FULL_MD_DEEP_ANALYSIS.json"
TRIANGLE_PATH = INPUT_DIR / "TRIANGLE_COUPLING_REPORT.json"

# ───────────────────────────── 概念提取 ─────────────────────────────

def extract_ucif2_concepts(data: Dict) -> Set[str]:
    """从UCIF2分析数据中提取概念集合"""
    concepts = set()

    # mathematical_core_summary
    mcs = data.get("mathematical_core_summary", {})
    for item in mcs.get("central_objects", []):
        concepts.add(item.strip().lower())
    for item in mcs.get("category_equivalences", []):
        concepts.add(item.strip().lower())
    for item in mcs.get("physical_connections", []):
        concepts.add(item.strip().lower())
    for item in mcs.get("key_numerical_invariants", []):
        if isinstance(item, dict):
            val = item.get("value", "")
            meaning = item.get("meaning", "")
            concepts.add(f"{val}: {meaning}".lower()[:120])

    # axiomatic_system_evolution
    evolution = data.get("axiomatic_system_evolution", {})
    for version, vdata in evolution.items():
        for d in vdata.get("definitions", []):
            concepts.add(d.strip().lower())
        for ax in vdata.get("axioms", []):
            if isinstance(ax, dict):
                name = ax.get("name", "")
                stmt = ax.get("statement", "")
                if name:
                    concepts.add(name.strip().lower())
                if stmt:
                    concepts.add(stmt.strip().lower()[:120])
        for th in vdata.get("theorems", []):
            if isinstance(th, dict):
                name = th.get("name", "")
                if name:
                    concepts.add(name.strip().lower())

    return {c for c in concepts if len(c) > 2}


def extract_cayley24_concepts(data: Dict) -> Set[str]:
    """从Cayley24分析数据中提取概念集合"""
    concepts = set()

    file_analyses = data.get("file_analyses", {})
    for fname, fdata in file_analyses.items():
        for c in fdata.get("core_concepts", []):
            concepts.add(c.strip().lower())
        for th in fdata.get("theorems", []):
            if isinstance(th, dict):
                name = th.get("name", "")
                if name:
                    concepts.add(name.strip().lower())
        for op in fdata.get("open_problems", []):
            concepts.add(op.strip().lower()[:120])

    # knowledge_graph
    kg = data.get("knowledge_graph", {})
    for node in kg.get("nodes", []):
        concepts.add(node.strip().lower())

    # summary
    summary = data.get("summary", {})
    for item in summary.get("core_concepts", []):
        concepts.add(item.strip().lower())

    return {c for c in concepts if len(c) > 2}


def extract_omni_concepts(data: Dict) -> Set[str]:
    """从OMNI-HUB分析数据中提取概念集合"""
    concepts = set()
    omni_files = data.get("files", [])

    for fdata in omni_files:
        for key in ["title", "summary", "filename"]:
            val = fdata.get(key, "")
            if val:
                concepts.add(val.strip().lower()[:120])

        for th in fdata.get("theorems", []):
            if isinstance(th, dict):
                text = th.get("text", "")
                if text:
                    first_sent = text.split(".")[0][:120]
                    concepts.add(first_sent.strip().lower())

        for df in fdata.get("definitions", []):
            if isinstance(df, dict):
                text = df.get("text", "")
                if text:
                    first_sent = text.split(".")[0][:120]
                    concepts.add(first_sent.strip().lower())

        for domain in fdata.get("domains", []):
            concepts.add(domain.strip().lower())

        for op in fdata.get("open_problems", []):
            if isinstance(op, dict):
                text = op.get("text", "")
                if text:
                    concepts.add(text.strip().lower()[:120])

    # domain_classification
    summary_data = data.get("summary", {})
    for domain in summary_data.get("domain_classification", {}):
        concepts.add(domain.strip().lower())

    return {c for c in concepts if len(c) > 2}


# ───────────────────────────── H协和度计算 ─────────────────────────────

def compute_H_concordance(project_concepts: Dict[str, Set[str]], epsilon: float = 1e-12) -> Tuple[float, Dict]:
    """
    计算协和度 H = 1 - I(concept; project) / H_max

    其中:
      - I(concept; project) = H(C) + H(P) - H(C,P) 是互信息
      - H_max = ln(N_projects)
      - 高互信息 → 概念与项目强相关 → 低协和度
      - 低互信息 → 概念跨项目分布 → 高协和度
    """
    projects = list(project_concepts.keys())
    n_projects = len(projects)

    if n_projects < 2:
        return 1.0, {}

    all_concepts = set()
    for concepts in project_concepts.values():
        all_concepts.update(concepts)

    if not all_concepts:
        return 0.0, {}

    n_concepts = len(all_concepts)
    concept_list = sorted(all_concepts)

    # 构建共现矩阵
    cooccurrence = np.zeros((n_concepts, n_projects))
    for j, proj in enumerate(projects):
        for i, concept in enumerate(concept_list):
            if concept in project_concepts[proj]:
                cooccurrence[i, j] = 1.0

    # 边际分布
    p_concept = np.sum(cooccurrence, axis=1) / (np.sum(cooccurrence) + epsilon)
    p_project = np.sum(cooccurrence, axis=0) / (np.sum(cooccurrence) + epsilon)

    # 熵计算
    H_concept = -np.sum(p_concept[p_concept > 0] * np.log(p_concept[p_concept > 0] + epsilon))
    H_project = -np.sum(p_project[p_project > 0] * np.log(p_project[p_project > 0] + epsilon))

    # 联合熵
    p_joint = cooccurrence / (np.sum(cooccurrence) + epsilon)
    H_joint = -np.sum(p_joint[p_joint > 0] * np.log(p_joint[p_joint > 0] + epsilon))

    # 互信息
    mutual_info = H_concept + H_project - H_joint
    H_max = math.log(n_projects)

    concordance = 1.0 - min(1.0, mutual_info / H_max)

    details = {
        "H_concept": float(H_concept),
        "H_project": float(H_project),
        "H_joint": float(H_joint),
        "mutual_info": float(mutual_info),
        "H_max": float(H_max),
        "n_concepts": n_concepts,
        "n_projects": n_projects,
        "concept_distribution": {p: len(c) for p, c in project_concepts.items()}
    }

    return float(np.clip(concordance, 0.0, 1.0)), details


# ───────────────────────────── CPI计算 ─────────────────────────────

def compute_CPI(coupling_pairs: Dict[Tuple[str, str], float],
                cross_links: int = 159893,
                max_possible_links: int = 500000) -> Tuple[float, Dict]:
    """
    计算跨项目整合指数 CPI

    公式:
      CPI = avg_coupling × (0.5 + 0.5 × closure) × (0.5 + 0.5 × link_density)

    其中:
      - avg_coupling = 三边耦合的算术平均
      - closure = 几何平均 / 算术平均 (三角闭合度)
      - link_density = 实际链接数 / 最大可能链接数
    """
    couplings = list(coupling_pairs.values())
    avg_coupling = sum(couplings) / len(couplings) if couplings else 0.0

    # 三角闭合度
    if len(couplings) >= 3 and all(c > 0 for c in couplings):
        geo_mean = np.exp(np.mean([np.log(c) for c in couplings]))
        arith_mean = np.mean(couplings)
        closure = geo_mean / arith_mean if arith_mean > 0 else 0.0
    else:
        closure = 0.0

    link_density = min(1.0, cross_links / max_possible_links)

    cpi = avg_coupling * (0.5 + 0.5 * closure) * (0.5 + 0.5 * link_density)

    details = {
        "avg_coupling": float(avg_coupling),
        "closure": float(closure),
        "link_density": float(link_density),
        "cross_links": cross_links,
        "max_possible_links": max_possible_links,
        "coupling_pairs": {f"{k[0]}->{k[1]}": v for k, v in coupling_pairs.items()}
    }

    return float(np.clip(cpi, 0.0, 1.0)), details


# ───────────────────────────── E指数计算 ─────────────────────────────

def compute_E(components: Dict[str, float]) -> float:
    """
    计算涌现指数 E (v12公式)

    E = 10000 × (0.15·Φ + 0.15·EI + 0.10·S_λ + 0.10·λ₂ + 0.08·H_G
               + 0.12·FV + 0.08·CPI + 0.10·C_MIP + 0.08·H + 0.02·I + 0.02·D)
    """
    weights = {
        "Phi_IIT": 0.15,
        "EI_causal": 0.15,
        "Spectral_entropy": 0.10,
        "Algebraic_connectivity": 0.10,
        "Graph_entropy": 0.08,
        "FV_formal_verification": 0.12,
        "CPI": 0.08,
        "C_MIP": 0.10,
        "H": 0.08,
        "I_isomorphism": 0.02,
        "D_coupling_depth": 0.02,
    }
    total = sum(weights.get(k, 0) * components.get(k, 0) for k in weights)
    return 10000.0 * total


# ───────────────────────────── 主程序 ─────────────────────────────

def main():
    print("=" * 70)
    print("H CONCORDANCE & CPI CROSS-PROJECT INTEGRATION — REAL COMPUTATION")
    print("=" * 70)

    # 1. 加载数据
    print("\n[1/5] Loading JSON data...")
    with open(UCIF2_PATH, "r", encoding="utf-8") as f:
        ucif2_data = json.load(f)
    with open(CAYLEY24_PATH, "r", encoding="utf-8") as f:
        cayley24_data = json.load(f)
    with open(OMNI_PATH, "r", encoding="utf-8") as f:
        omni_data = json.load(f)
    with open(TRIANGLE_PATH, "r", encoding="utf-8") as f:
        triangle_data = json.load(f)
    print("  ✓ All 4 files loaded")

    # 2. 提取概念
    print("\n[2/5] Extracting concepts...")
    ucif2_concepts = extract_ucif2_concepts(ucif2_data)
    cayley24_concepts = extract_cayley24_concepts(cayley24_data)
    omni_concepts = extract_omni_concepts(omni_data)
    print(f"  UCIF2:     {len(ucif2_concepts)} concepts")
    print(f"  Cayley24:  {len(cayley24_concepts)} concepts")
    print(f"  OMNI-HUB:  {len(omni_concepts)} concepts")

    # 3. 计算H协和度
    print("\n[3/5] Computing H Concordance...")
    project_concepts = {
        "ucif2": ucif2_concepts,
        "cayley24": cayley24_concepts,
        "omni_hub": omni_concepts
    }
    H_real, H_details = compute_H_concordance(project_concepts)
    print(f"  H = {H_real:.6f}")
    print(f"  Mutual Information = {H_details['mutual_info']:.4f}")

    # 4. 计算CPI
    print("\n[4/5] Computing CPI...")

    # 从三角形报告获取Jaccard
    triangle_pairwise = triangle_data.get("pairwise_coupling", {})
    jaccard_coupling = {
        ("ucif2", "cayley24"): triangle_pairwise["ucif2_cayley24"]["jaccard_similarity"],
        ("ucif2", "omni"): triangle_pairwise["ucif2_omni"]["jaccard_similarity"],
        ("cayley24", "omni"): triangle_pairwise["cayley24_omni"]["jaccard_similarity"],
    }
    CPI_jaccard, CPI_jaccard_details = compute_CPI(jaccard_coupling, cross_links=159893)
    print(f"  CPI (from Jaccard) = {CPI_jaccard:.6f}")

    # 基线耦合
    baseline_coupling = {
        ("ucif2", "omni_hub"): 0.42,
        ("omni_hub", "cayley24"): 0.35,
        ("ucif2", "cayley24"): 0.28,
    }
    CPI_baseline, CPI_baseline_details = compute_CPI(baseline_coupling, cross_links=159893)
    print(f"  CPI (from baseline) = {CPI_baseline:.6f}")

    # 5. 计算涌现指数
    print("\n[5/5] Computing Emergence Index...")
    components_current = {
        "Phi_IIT": 0.6605,
        "EI_causal": 0.6839,
        "Spectral_entropy": 0.9941,
        "Algebraic_connectivity": 0.8786,
        "Graph_entropy": 0.9996,
        "FV_formal_verification": 0.4947,
        "C_MIP": 0.8686,
        "I_isomorphism": 0.0,
        "D_coupling_depth": 0.717,
        "CPI": 0.2294,
        "H": 0.2203,
    }
    E_current = compute_E(components_current)
    print(f"  Current E = {E_current:.2f}")

    # 提升方案
    H_target = 0.65
    CPI_target = 0.55

    # 保守方案
    comps_conservative = components_current.copy()
    comps_conservative["H"] = min(0.55, 0.2203 + 0.15)
    comps_conservative["CPI"] = min(0.45, 0.2294 + 0.15)
    E_conservative = compute_E(comps_conservative)

    # 现实方案
    comps_realistic = components_current.copy()
    comps_realistic["H"] = min(0.68, 0.2203 + 0.25)
    comps_realistic["CPI"] = min(0.58, 0.2294 + 0.25)
    E_realistic = compute_E(comps_realistic)

    # 目标方案
    comps_target = components_current.copy()
    comps_target["H"] = H_target
    comps_target["CPI"] = CPI_target
    E_target = compute_E(comps_target)

    print(f"  Conservative E = {E_conservative:.2f}")
    print(f"  Realistic E = {E_realistic:.2f}")
    print(f"  Target E = {E_target:.2f}")

    # 保存结果
    results = {
        "metadata": {
            "version": "1.0.0",
            "date": "2026-09-17",
            "source_files": [
                "UCIF2_FULL_SERIES_ANALYSIS.json",
                "CAYLEY24_MATH_PHYS_DEEP_ANALYSIS.json",
                "FULL_MD_DEEP_ANALYSIS.json",
                "TRIANGLE_COUPLING_REPORT.json"
            ]
        },
        "concept_counts": {
            "ucif2": len(ucif2_concepts),
            "cayley24": len(cayley24_concepts),
            "omni_hub": len(omni_concepts),
            "total": len(ucif2_concepts) + len(cayley24_concepts) + len(omni_concepts)
        },
        "H_concordance": {
            "current": 0.2203,
            "real_computed": round(H_real, 6),
            "mutual_info": round(H_details["mutual_info"], 6),
            "H_max": round(H_details["H_max"], 6),
            "target": 0.65,
            "gap_to_target": round(0.65 - H_real, 6)
        },
        "CPI": {
            "current": 0.2294,
            "from_jaccard": round(CPI_jaccard, 6),
            "from_baseline": round(CPI_baseline, 6),
            "target": 0.55,
            "gap_to_target": round(0.55 - CPI_jaccard, 6)
        },
        "jaccard_similarities": {
            "ucif2_cayley24": jaccard_coupling[("ucif2", "cayley24")],
            "ucif2_omni": jaccard_coupling[("ucif2", "omni")],
            "cayley24_omni": jaccard_coupling[("cayley24", "omni")]
        },
        "improvement_scenarios": {
            "conservative": {
                "H": round(comps_conservative["H"], 4),
                "CPI": round(comps_conservative["CPI"], 4),
                "E": round(E_conservative, 2),
                "delta_E": round(E_conservative - E_current, 2)
            },
            "realistic": {
                "H": round(comps_realistic["H"], 4),
                "CPI": round(comps_realistic["CPI"], 4),
                "E": round(E_realistic, 2),
                "delta_E": round(E_realistic - E_current, 2)
            },
            "target": {
                "H": H_target,
                "CPI": CPI_target,
                "E": round(E_target, 2),
                "delta_E": round(E_target - E_current, 2)
            }
        },
        "emergence_index": {
            "current": round(E_current, 2),
            "target": 7000.0,
            "gap_to_target": round(7000.0 - E_current, 2)
        }
    }

    output_json = OUTPUT_DIR / "H_CPI_REAL_COMPUTATION.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  ✓ Results saved to {output_json}")

    return results


if __name__ == "__main__":
    main()
