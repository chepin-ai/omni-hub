#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v12_triangle_coupling.py

Triangle Deep Coupling Analyzer for UCIF2 <-> OMNI-HUB <-> Cayley24
Computes cross-project concept overlap, theorem sharing, formula association,
coupling strength matrix, and triangle consistency metrics.

Based on actual JSON extraction -- no estimation.
"""

import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any


class TriangleCouplingAnalyzer:
    """
    Analyzes deep triangular coupling among three mathematical physics projects:
    - UCIF2 (Unified Categorical Information Field v2)
    - Cayley24 (Cayley-24 Math-Physics Deep Analysis)
    - OMNI-HUB (Full MD Deep Analysis, math/physics filtered)
    """

    # Bilingual keyword map for semantic concept matching
    KEYWORD_MAP = {
        'moonshine': ['月光', 'moonshine', 'Moonshine'],
        'monster': ['Monster', 'monster', '怪兽', '魔群'],
        'leech': ['Leech', 'leech', '李奇'],
        'cayley': ['Cayley', 'cayley', '凯莱'],
        'calabi-yau': ['Calabi-Yau', '卡拉比-丘', 'CY'],
        'k3': ['K3', 'K3曲面'],
        'voA': ['VOA', '顶点算子代数', '顶点算代数'],
        'orbifold': ['轨形', 'orbifold'],
        'holographic': ['全息', 'holographic'],
        'ads': ['AdS', '反德西特'],
        'cft': ['CFT', '共形场论'],
        'black hole': ['黑洞', 'black hole'],
        'entropy': ['熵', 'entropy'],
        'symmetry': ['对称', 'symmetry'],
        'category': ['范畴', 'category'],
        'isomorphism': ['同构', 'isomorphism'],
        'cohomology': ['上同调', 'cohomology'],
        'derived': ['导出', 'derived'],
        'modular': ['模形式', 'modular'],
        'lattice': ['格', 'lattice'],
        'string': ['弦', 'string'],
        'quantum': ['量子', 'quantum'],
        'gravity': ['引力', 'gravity'],
        'geometry': ['几何', 'geometry'],
        'algebra': ['代数', 'algebra'],
        'topology': ['拓扑', 'topology'],
        'elliptic': ['椭圆', 'elliptic'],
        'fermat': ['Fermat', '费马'],
        'hilbert': ['Hilbert', '希尔伯特'],
        'e8': ['E8', 'E₈'],
        'cy24': ['Cayley-24', 'cy24', 'Cayley24'],
        'crystal': ['晶体', 'crystal'],
        'knot': ['扭结', 'knot'],
        'omega': ['Omega', 'Ω'],
        'ucif': ['UCIF', 'UCIF²'],
        'flm': ['FLM', 'FLM定理'],
        'borcherds': ['Borcherds', '博切兹'],
        'mirrorsymmetry': ['镜像对称', 'mirror symmetry'],
        'gromov-witten': ['Gromov-Witten', 'GW'],
        'bps': ['BPS'],
        'dbrane': ['D-膜', 'D-brane', 'D膜'],
        'page': ['Page', 'Page曲线'],
        'information paradox': ['信息悖论', 'information paradox'],
        'golay': ['Golay', '戈莱'],
        'conway': ['Conway', '康威'],
        'mathieu': ['Mathieu', '马蒂厄'],
        'mckay': ['McKay', '麦克凯'],
        'virasoro': ['Virasoro', '维拉索罗'],
        'heisenberg': ['Heisenberg', '海森堡'],
        'dedekind': ['Dedekind', '戴德金'],
        'eta': ['η函数', 'eta'],
        'jfunction': ['J函数', 'J(τ)'],
        'chiral': ['chiral', '手征'],
        'derham': ['de Rham', '德拉姆'],
        'spectral': ['谱', 'spectral'],
        'algebraic': ['代数', 'algebraic'],
        'instanton': ['瞬子', 'instanton'],
        'flux': ['通量', 'flux'],
        'superpotential': ['超势', 'superpotential'],
        'kahler': ['Kähler', 'Kahler', '凯勒'],
        'complex structure': ['复结构', 'complex structure'],
        'moduli': ['模空间', 'moduli'],
        'yoneda': ['Yoneda', '米田'],
        'ext': ['Ext'],
        'tor': ['Tor'],
        'hom': ['Hom'],
        'tensor': ['张量', 'tensor'],
        'dual': ['对偶', 'dual'],
        'bundle': ['丛', 'bundle'],
        'sheaf': ['层', 'sheaf'],
        'scheme': ['概形', 'scheme'],
        'stack': ['叠', 'stack'],
        'gerbe': [' gerbe'],
        'brane': ['膜', 'brane'],
        'ns5': ['NS5', 'NS5-膜'],
        'mtheory': ['M-理论', 'M-theory'],
        'f-theory': ['F-理论', 'F-theory'],
        'type ii': ['Type II', 'Type IIB', 'Type IIA'],
        'heterotic': ['Heterotic', '杂化'],
        'maldacena': ['Maldacena'],
        'witten': ['Witten'],
        'seiberg': ['Seiberg', '塞伯格'],
        'hawking': ['Hawking', '霍金'],
        'bekenstein': ['Bekenstein', '贝肯斯坦'],
    }

    MATH_PHYS_DOMAINS = {'physics', 'algebra', 'geometry', 'moonshine', 'topology', 'category_theory', 'number_theory', 'whitepaper', 'computational'}

    def __init__(self, ucif2_path: str, cayley_path: str, omni_path: str):
        self.ucif2_path = ucif2_path
        self.cayley_path = cayley_path
        self.omni_path = omni_path
        self.ucif2_concepts: Set[str] = set()
        self.ucif2_theorems: Set[str] = set()
        self.ucif2_formulas: Set[str] = set()
        self.ucif2_axioms: Set[str] = set()
        self.ucif2_axioms_full: List[Dict] = []
        self.ucif2_theorems_full: List[Dict] = []
        self.cayley_concepts: Set[str] = set()
        self.cayley_theorems: Set[str] = set()
        self.cayley_formulas: Set[str] = set()
        self.cayley_formulas_full: List[Dict] = []
        self.omni_concepts: Set[str] = set()
        self.omni_theorems: Set[str] = set()
        self.omni_formulas: Set[str] = set()
        self.coupling_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        self.pairwise_results: Dict[str, Any] = {}
        self.bridge_concepts: List[Dict] = []
        self.gap_concepts: List[Dict] = []
        self.cpi_current = 0.0
        self.cpi_triangle = 0.0
        self.cpi_improvement: Dict[str, Any] = {}

    def load_projects(self) -> None:
        """Load all three project JSON files and extract knowledge."""
        self._load_ucif2()
        self._load_cayley24()
        self._load_omni_hub()

    def _load_ucif2(self) -> None:
        with open(self.ucif2_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for version, vdata in data.get("axiomatic_system_evolution", {}).items():
            for ax in vdata.get("axioms", []):
                if isinstance(ax, dict):
                    name = ax.get("name", "")
                    if name:
                        self.ucif2_axioms.add(name)
                        self.ucif2_concepts.add(name)
                    self.ucif2_axioms_full.append({"version": version, "name": name, "statement": ax.get("statement", ""), "status": ax.get("status", "")})
                    stmt = ax.get("statement", "")
                    if stmt:
                        self._extract_formulas(stmt, "ucif2")
            for df in vdata.get("definitions", []):
                if isinstance(df, str):
                    self.ucif2_concepts.add(df)
                elif isinstance(df, dict):
                    n = df.get("name", df.get("term", ""))
                    if n:
                        self.ucif2_concepts.add(n)
            for th in vdata.get("theorems", []):
                if isinstance(th, dict):
                    name = th.get("name", "")
                    if name:
                        self.ucif2_theorems.add(name)
                    self.ucif2_theorems_full.append({"version": version, "name": name, "status": th.get("status", "")})
                    stmt = th.get("statement", "")
                    if stmt:
                        self._extract_formulas(stmt, "ucif2")
            cc = vdata.get("core_content", "")
            if isinstance(cc, str):
                self._extract_formulas(cc, "ucif2")
        mcs = data.get("mathematical_core_summary", {})
        for obj in mcs.get("central_objects", []):
            if isinstance(obj, str):
                self.ucif2_concepts.add(obj)
        for ce in mcs.get("category_equivalences", []):
            if isinstance(ce, str):
                self.ucif2_concepts.add(ce)
        for kn in mcs.get("key_numerical_invariants", []):
            if isinstance(kn, str):
                self.ucif2_concepts.add(kn)
            elif isinstance(kn, dict):
                for k in kn.keys():
                    self.ucif2_concepts.add(k)
        cva = data.get("cross_version_analysis", {})
        for key in ["axiom_stability", "theorem_growth", "definition_growth"]:
            if key in cva and isinstance(cva[key], dict):
                for k in cva[key].keys():
                    self.ucif2_concepts.add(k)
        osrc = data.get("ucif2_os_source_analysis", {})
        for cp in osrc.get("core_principles", []):
            if isinstance(cp, str):
                self.ucif2_concepts.add(cp)
        for et in data.get("evolution_timeline", []):
            milestone = et.get("milestone", "")
            if milestone:
                self.ucif2_concepts.add(milestone)
        for dep in data.get("key_dependencies", []):
            if isinstance(dep, str):
                for part in dep.split("→"):
                    self.ucif2_concepts.add(part.strip())

    def _load_cayley24(self) -> None:
        with open(self.cayley_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for fn, fdata in data.get("file_analyses", {}).items():
            for c in fdata.get("core_concepts", []):
                if isinstance(c, str):
                    self.cayley_concepts.add(c)
            for fm in fdata.get("formulas", []):
                if isinstance(fm, str) and len(fm) > 3:
                    self.cayley_formulas.add(fm)
                    self.cayley_formulas_full.append({"file": fn, "formula": fm})
            for th in fdata.get("theorems", []):
                if isinstance(th, dict):
                    name = th.get("name", "")
                    if name:
                        self.cayley_theorems.add(name)
                    stmt = th.get("statement", "")
                    if stmt:
                        self._extract_formulas(stmt, "cayley24")
            for op in fdata.get("open_problems", []):
                if isinstance(op, str):
                    self.cayley_concepts.add(op)
        kg = data.get("knowledge_graph", {})
        for node in kg.get("nodes", []):
            if isinstance(node, str):
                self.cayley_concepts.add(node)
            elif isinstance(node, dict):
                name = node.get("name", node.get("label", ""))
                if name:
                    self.cayley_concepts.add(name)
        ucp = data.get("ucif2_crosspoints", {})
        for cp in ucp.get("crosspoints", []):
            if isinstance(cp, dict):
                for k in ["cayley24_component", "ucif2_connection"]:
                    v = cp.get(k, "")
                    if v:
                        self.cayley_concepts.add(v)
                        self.ucif2_concepts.add(v)
                desc = cp.get("description", "")
                if desc:
                    for term in ["Monster", "V^♮", "AdS", "CFT", "Leech", "Golay", "Page", "SYK", "Calabi-Yau", "Yoneda", "Ext", "McKay"]:
                        if term in desc:
                            self.cayley_concepts.add(term)
            elif isinstance(cp, str):
                self.cayley_concepts.add(cp)
                self.ucif2_concepts.add(cp)
        npreds = data.get("numerical_predictions", {})
        for pred in npreds.get("predictions", []):
            if isinstance(pred, dict):
                for k in ["concept", "prediction_name", "description"]:
                    v = pred.get(k, "")
                    if v:
                        self.cayley_concepts.add(v)
        summary = data.get("summary", {})
        for insight in summary.get("key_insights", []):
            if isinstance(insight, str):
                self.cayley_concepts.add(insight)

    def _load_omni_hub(self) -> None:
        with open(self.omni_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        relevant_count = 0
        for fdata in data.get("files", []):
            domains = set(fdata.get("domains", []))
            if not (domains & self.MATH_PHYS_DOMAINS):
                continue
            relevant_count += 1
            for df in fdata.get("definitions", []):
                if isinstance(df, dict):
                    text = df.get("text", "")
                    if text:
                        term = text.split(":")[0].split("（")[0].split("(")[0].strip()
                        if term and len(term) < 100:
                            self.omni_concepts.add(term)
                elif isinstance(df, str):
                    self.omni_concepts.add(df)
            for th in fdata.get("theorems", []):
                if isinstance(th, dict):
                    text = th.get("text", "")
                    if text:
                        self.omni_theorems.add(text[:200])
                elif isinstance(th, str):
                    self.omni_theorems.add(th)
            for fm in fdata.get("formulas", []):
                if isinstance(fm, dict):
                    formula = fm.get("formula", "")
                    if formula and len(formula) > 3:
                        self.omni_formulas.add(formula)
                elif isinstance(fm, str) and len(fm) > 3:
                    self.omni_formulas.add(fm)
            title = fdata.get("title", "")
            if title:
                self.omni_concepts.add(title)
            summary = fdata.get("summary", "")
            if summary:
                for line in summary.split("\n"):
                    if "**" in line:
                        for m in re.findall(r"\*\*([^*]+)\*\*", line):
                            self.omni_concepts.add(m.strip())
            for op in fdata.get("open_problems", []):
                if isinstance(op, dict):
                    text = op.get("text", "")
                    if text:
                        self.omni_concepts.add(text[:150])
            for cj in fdata.get("conjectures", []):
                if isinstance(cj, dict):
                    text = cj.get("text", "")
                    if text:
                        self.omni_concepts.add(text[:150])
            for nr in fdata.get("numerical_results", []):
                if isinstance(nr, str):
                    self.omni_concepts.add(nr[:100])
        self.omni_relevant_files = relevant_count

    def _extract_formulas(self, text: str, project: str) -> None:
        patterns = [r"\$[^$]+\$", r"\\\[[^\]]+\\\]", r"\\\([^\)]+\\\)", r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^,;]+", r"\\[a-zA-Z]+\{[^}]*\}"]
        for pat in patterns:
            for m in re.findall(pat, text):
                if len(m) > 3:
                    if project == "ucif2":
                        self.ucif2_formulas.add(m.strip())
                    elif project == "cayley24":
                        self.cayley_formulas.add(m.strip())

    @staticmethod
    def normalize_concept(c: str) -> str:
        if not isinstance(c, str):
            return ""
        c = c.strip()
        if len(c) > 200:
            return ""
        if c.startswith('"""') or c.startswith("'''") or c.startswith("# "):
            return ""
        if c.startswith("import ") or c.startswith("def ") or c.startswith("class "):
            return ""
        special_ratio = sum(1 for ch in c if ch in "{}[]()<>/\\=@#$%^&*|~`") / max(len(c), 1)
        if special_ratio > 0.4 and len(c) > 30:
            return ""
        return c.strip('"\'.,;:!?')

    def clean_concept_set(self, concepts: Set[str]) -> Set[str]:
        cleaned = set()
        for c in concepts:
            nc = self.normalize_concept(c)
            if nc and len(nc) >= 2:
                cleaned.add(nc)
        return cleaned

    def concept_to_keywords(self, concept: str) -> Set[str]:
        concept_lower = concept.lower()
        matched = set()
        for group, variants in self.KEYWORD_MAP.items():
            for variant in variants:
                if variant.lower() in concept_lower:
                    matched.add(group)
                    break
        return matched

    def compute_keyword_matches(self, set_a: Set[str], set_b: Set[str]) -> Tuple[Set[str], Set[str], List[Tuple]]:
        a_keywords = {c: self.concept_to_keywords(c) for c in set_a}
        b_keywords = {c: self.concept_to_keywords(c) for c in set_b}
        matched_a, matched_b = set(), set()
        pairs = []
        for ca, kws_a in a_keywords.items():
            if not kws_a:
                continue
            for cb, kws_b in b_keywords.items():
                if not kws_b:
                    continue
                shared = kws_a & kws_b
                if len(shared) >= 2 or (len(shared) == 1 and len(kws_a) == 1 and len(kws_b) == 1):
                    matched_a.add(ca)
                    matched_b.add(cb)
                    pairs.append((ca, cb, shared))
                    break
        return matched_a, matched_b, pairs

    def compute_substring_matches(self, set_a: Set[str], set_b: Set[str]) -> Tuple[Set[str], Set[str], List[Tuple]]:
        matched_a, matched_b = set(), set()
        pairs = []
        for ca in set_a:
            ca_lower = ca.lower()
            for cb in set_b:
                cb_lower = cb.lower()
                if len(ca) >= 6 and len(cb) >= 6:
                    if ca_lower in cb_lower or cb_lower in ca_lower:
                        matched_a.add(ca)
                        matched_b.add(cb)
                        pairs.append((ca, cb))
                        break
        return matched_a, matched_b, pairs

    def combined_match(self, set_a: Set[str], set_b: Set[str], name_a: str = "A", name_b: str = "B") -> Dict:
        exact_inter = set_a & set_b
        kw_a, kw_b, kw_pairs = self.compute_keyword_matches(set_a, set_b)
        remaining_a = set_a - exact_inter - kw_a
        remaining_b = set_b - exact_inter - kw_b
        sub_a, sub_b, sub_pairs = self.compute_substring_matches(remaining_a, remaining_b)
        total_matched_a = exact_inter | kw_a | sub_a
        total_matched_b = exact_inter | kw_b | sub_b
        union = set_a | set_b
        jaccard = len(total_matched_a | total_matched_b) / len(union) if union else 0.0
        return {
            "exact_intersection": len(exact_inter),
            "keyword_matches": len(kw_pairs),
            "substring_matches": len(sub_pairs),
            f"{name_a}_matched_count": len(total_matched_a),
            f"{name_b}_matched_count": len(total_matched_b),
            "total_matched_unique": len(total_matched_a | total_matched_b),
            "union_count": len(union),
            "jaccard_similarity": round(jaccard, 6),
            "exact_items": sorted(list(exact_inter)),
            "keyword_match_samples": [(a, b, list(s)) for a, b, s in kw_pairs[:20]],
            "substring_match_samples": list(sub_pairs[:20])
        }

    def compute_pairwise_coupling(self) -> None:
        ucif2_c = self.clean_concept_set(self.ucif2_concepts)
        cayley_c = self.clean_concept_set(self.cayley_concepts)
        omni_c = self.clean_concept_set(self.omni_concepts)
        self.ucif2_concepts_clean = ucif2_c
        self.cayley_concepts_clean = cayley_c
        self.omni_concepts_clean = omni_c
        uc2_ca = self.combined_match(ucif2_c, cayley_c, "ucif2", "cayley24")
        uc2_om = self.combined_match(ucif2_c, omni_c, "ucif2", "omni")
        ca_om = self.combined_match(cayley_c, omni_c, "cayley24", "omni")
        self.pairwise_results = {
            "ucif2_cayley24_concepts": uc2_ca,
            "ucif2_omni_concepts": uc2_om,
            "cayley24_omni_concepts": ca_om
        }
        uc2_ca_formulas = len(self.ucif2_formulas & self.cayley_formulas)
        uc2_om_formulas = len(self.ucif2_formulas & self.omni_formulas)
        ca_om_formulas = len(self.cayley_formulas & self.omni_formulas)
        uc2_ca_theorems = len(self.ucif2_theorems & self.cayley_theorems)
        uc2_om_theorems = len(self.ucif2_theorems & self.omni_theorems)
        ca_om_theorems = len(self.cayley_theorems & self.omni_theorems)
        self.pairwise_results["formula_overlaps"] = {
            "ucif2_cayley24": uc2_ca_formulas,
            "ucif2_omni": uc2_om_formulas,
            "cayley24_omni": ca_om_formulas
        }
        self.pairwise_results["theorem_overlaps"] = {
            "ucif2_cayley24": uc2_ca_theorems,
            "ucif2_omni": uc2_om_theorems,
            "cayley24_omni": ca_om_theorems
        }
        def combined_score(concept_j, formula_inter, formula_union_denom):
            formula_j = formula_inter / formula_union_denom if formula_union_denom > 0 else 0.0
            return 0.60 * concept_j + 0.25 * formula_j + 0.15 * (formula_inter / 100.0 if formula_inter > 0 else 0.0)
        uc2_ca_score = combined_score(uc2_ca["jaccard_similarity"], uc2_ca_formulas, max(1, len(self.ucif2_formulas) + len(self.cayley_formulas) - uc2_ca_formulas))
        uc2_om_score = combined_score(uc2_om["jaccard_similarity"], uc2_om_formulas, max(1, len(self.ucif2_formulas) + len(self.omni_formulas) - uc2_om_formulas))
        ca_om_score = combined_score(ca_om["jaccard_similarity"], ca_om_formulas, max(1, len(self.cayley_formulas) + len(self.omni_formulas) - ca_om_formulas))
        self.pairwise_results["combined_scores"] = {
            "ucif2_cayley24": round(uc2_ca_score, 6),
            "ucif2_omni": round(uc2_om_score, 6),
            "cayley24_omni": round(ca_om_score, 6)
        }
        self.pairwise_results["raw_counts"] = {
            "ucif2": {"concepts": len(ucif2_c), "theorems": len(self.ucif2_theorems), "formulas": len(self.ucif2_formulas), "axioms": len(self.ucif2_axioms)},
            "cayley24": {"concepts": len(cayley_c), "theorems": len(self.cayley_theorems), "formulas": len(self.cayley_formulas)},
            "omni": {"concepts": len(omni_c), "theorems": len(self.omni_theorems), "formulas": len(self.omni_formulas), "relevant_files": getattr(self, "omni_relevant_files", 0)}
        }
        self.combined_scores = (uc2_ca_score, uc2_om_score, ca_om_score)

    def compute_triangle_matrix(self) -> None:
        s = self.combined_scores
        self.coupling_matrix = [
            [1.0, round(s[0], 6), round(s[1], 6)],
            [round(s[0], 6), 1.0, round(s[2], 6)],
            [round(s[1], 6), round(s[2], 6), 1.0]
        ]
        self.cpi_triangle = s[0] * s[1] * s[2]
        self.cpi_current = sum(s) / 3.0

    def find_bridge_concepts(self) -> None:
        bridges = []
        for ca in self.ucif2_concepts_clean:
            kws_a = self.concept_to_keywords(ca)
            if not kws_a:
                continue
            matched_b, matched_c = [], []
            for cb in self.cayley_concepts_clean:
                kws_b = self.concept_to_keywords(cb)
                shared = kws_a & kws_b
                if len(shared) >= 2 or (len(shared) == 1 and len(kws_a) == 1):
                    matched_b.append(cb)
            for cc in self.omni_concepts_clean:
                kws_c = self.concept_to_keywords(cc)
                shared = kws_a & kws_c
                if len(shared) >= 2 or (len(shared) == 1 and len(kws_a) == 1):
                    matched_c.append(cc)
            if matched_b and matched_c:
                bridges.append({"ucif2_concept": ca, "cayley24_matches": matched_b[:3], "omni_matches": matched_c[:3], "keyword_groups": list(kws_a)})
        self.bridge_concepts = bridges

    def find_gaps(self) -> None:
        with open(self.cayley_path, "r", encoding="utf-8") as f:
            cayley_data = json.load(f)
        gaps = []
        ucp = cayley_data.get("ucif2_crosspoints", {})
        for cp in ucp.get("crosspoints", []):
            if not isinstance(cp, dict):
                continue
            c24_comp = cp.get("cayley24_component", "")
            ucif2_conn = cp.get("ucif2_connection", "")
            found = False
            for oc in self.omni_concepts_clean:
                oc_lower = oc.lower()
                if c24_comp and len(c24_comp) > 3:
                    if c24_comp.lower() in oc_lower or oc_lower in c24_comp.lower():
                        found = True
                        break
                if ucif2_conn and len(ucif2_conn) > 3:
                    if ucif2_conn.lower() in oc_lower or oc_lower in ucif2_conn.lower():
                        found = True
                        break
            if not found:
                c24_kws = self.concept_to_keywords(c24_comp)
                ucif2_kws = self.concept_to_keywords(ucif2_conn)
                for oc in self.omni_concepts_clean:
                    oc_kws = self.concept_to_keywords(oc)
                    if (c24_kws & oc_kws) or (ucif2_kws & oc_kws):
                        found = True
                        break
            if not found:
                gaps.append({"cayley24_component": c24_comp, "ucif2_connection": ucif2_conn, "relevance": cp.get("relevance", "unknown")})
        self.gap_concepts = gaps

    def compute_cpi_improvement(self) -> None:
        s = self.combined_scores
        current_triangle = s[0] * s[1] * s[2]
        current_pairwise = sum(s) / 3.0
        target_cpi = 0.032
        s1 = (min(s[0] * 1.25, 1.0), min(s[1] * 1.4, 1.0), min(s[2] * 1.3, 1.0))
        t1 = s1[0] * s1[1] * s1[2]
        p1 = sum(s1) / 3.0
        s2 = (min(s[0] * 1.8, 1.0), min(s[1] * 2.2, 1.0), min(s[2] * 1.8, 1.0))
        t2 = s2[0] * s2[1] * s2[2]
        p2 = sum(s2) / 3.0
        target_pairwise = target_cpi ** (1.0 / 3.0)
        self.cpi_improvement = {
            "current": {"pairwise_cpi": round(current_pairwise, 6), "triangle_closure": round(current_triangle, 10)},
            "target_cpi": target_cpi,
            "gap_to_target": round(target_cpi - current_pairwise, 6),
            "gap_percent": round((target_cpi - current_pairwise) / target_cpi * 100, 1),
            "scenarios": {
                "bridge_gaps": {"pairwise_cpi": round(p1, 6), "triangle_closure": round(t1, 10), "improvement_factor": round(t1 / current_triangle, 1) if current_triangle > 0 else 0},
                "ideal_linkage": {"pairwise_cpi": round(p2, 6), "triangle_closure": round(t2, 10), "improvement_factor": round(t2 / current_triangle, 1) if current_triangle > 0 else 0},
                "target_cpi_032": {"required_pairwise": round(target_pairwise, 4), "triangle_closure": round(target_cpi, 10), "improvement_factor": round(target_cpi / current_triangle, 1) if current_triangle > 0 else 0}
            }
        }

    def report(self) -> Dict:
        """Generate the full analysis report as a dictionary."""
        return {
            "metadata": {
                "analysis_type": "Triangle Deep Coupling Analysis",
                "projects": ["UCIF2", "Cayley24", "OMNI-HUB"],
                "methodology": "Jaccard similarity on extracted concepts with bilingual keyword semantic matching",
                "current_cpi_reference": 0.032
            },
            "project_statistics": self.pairwise_results.get("raw_counts", {}),
            "pairwise_coupling": {
                "ucif2_cayley24": {
                    "shared_concepts_exact": self.pairwise_results["ucif2_cayley24_concepts"]["exact_intersection"],
                    "shared_concepts_keyword": self.pairwise_results["ucif2_cayley24_concepts"]["keyword_matches"],
                    "shared_concepts_substring": self.pairwise_results["ucif2_cayley24_concepts"]["substring_matches"],
                    "shared_theorems": self.pairwise_results["theorem_overlaps"]["ucif2_cayley24"],
                    "shared_formulas": self.pairwise_results["formula_overlaps"]["ucif2_cayley24"],
                    "jaccard_similarity": self.pairwise_results["ucif2_cayley24_concepts"]["jaccard_similarity"],
                    "combined_coupling_score": self.pairwise_results["combined_scores"]["ucif2_cayley24"]
                },
                "ucif2_omni": {
                    "shared_concepts_exact": self.pairwise_results["ucif2_omni_concepts"]["exact_intersection"],
                    "shared_concepts_keyword": self.pairwise_results["ucif2_omni_concepts"]["keyword_matches"],
                    "shared_concepts_substring": self.pairwise_results["ucif2_omni_concepts"]["substring_matches"],
                    "shared_theorems": self.pairwise_results["theorem_overlaps"]["ucif2_omni"],
                    "shared_formulas": self.pairwise_results["formula_overlaps"]["ucif2_omni"],
                    "jaccard_similarity": self.pairwise_results["ucif2_omni_concepts"]["jaccard_similarity"],
                    "combined_coupling_score": self.pairwise_results["combined_scores"]["ucif2_omni"]
                },
                "cayley24_omni": {
                    "shared_concepts_exact": self.pairwise_results["cayley24_omni_concepts"]["exact_intersection"],
                    "shared_concepts_keyword": self.pairwise_results["cayley24_omni_concepts"]["keyword_matches"],
                    "shared_concepts_substring": self.pairwise_results["cayley24_omni_concepts"]["substring_matches"],
                    "shared_theorems": self.pairwise_results["theorem_overlaps"]["cayley24_omni"],
                    "shared_formulas": self.pairwise_results["formula_overlaps"]["cayley24_omni"],
                    "jaccard_similarity": self.pairwise_results["cayley24_omni_concepts"]["jaccard_similarity"],
                    "combined_coupling_score": self.pairwise_results["combined_scores"]["cayley24_omni"]
                }
            },
            "coupling_matrix_3x3": {"labels": ["UCIF2", "Cayley24", "OMNI-HUB"], "matrix": self.coupling_matrix},
            "triangle_consistency": {
                "triangle_closure_C_abc": round(self.cpi_triangle, 10),
                "global_triangle_coupling_index_CPI_triangle": round(self.cpi_triangle, 10),
                "current_pairwise_CPI": round(self.cpi_current, 6),
                "target_CPI": 0.032,
                "gap_to_target": round(0.032 - self.cpi_current, 6)
            },
            "bridge_concepts": {"total_bridges_found": len(self.bridge_concepts), "bridges": self.bridge_concepts[:30]},
            "gap_analysis": {"total_gaps": len(self.gap_concepts), "gaps": self.gap_concepts},
            "cpi_improvement_scenarios": self.cpi_improvement
        }

def main():
    ucif2_path = "/mnt/agents/output/OMNI-HUB/hub/UCIF2_FULL_SERIES_ANALYSIS.json"
    cayley_path = "/mnt/agents/output/OMNI-HUB/hub/CAYLEY24_MATH_PHYS_DEEP_ANALYSIS.json"
    omni_path = "/mnt/agents/output/OMNI-HUB/hub/FULL_MD_DEEP_ANALYSIS.json"
    analyzer = TriangleCouplingAnalyzer(ucif2_path, cayley_path, omni_path)
    analyzer.load_projects()
    analyzer.compute_pairwise_coupling()
    analyzer.compute_triangle_matrix()
    analyzer.find_bridge_concepts()
    analyzer.find_gaps()
    analyzer.compute_cpi_improvement()
    report = analyzer.report()
    os.makedirs("/mnt/agents/output/OMNI-HUB/hub", exist_ok=True)
    with open("/mnt/agents/output/OMNI-HUB/hub/TRIANGLE_COUPLING_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    md = generate_markdown_report(report)
    with open("/mnt/agents/output/OMNI-HUB/hub/TRIANGLE_COUPLING_REPORT.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("Triangle coupling analysis complete.")
    print("  JSON: /mnt/agents/output/OMNI-HUB/hub/TRIANGLE_COUPLING_REPORT.json")
    print("  MD:   /mnt/agents/output/OMNI-HUB/hub/TRIANGLE_COUPLING_REPORT.md")
    return report

def generate_markdown_report(r: Dict) -> str:
    lines = []
    lines.append("# Triangle Deep Coupling Report: UCIF2 <-> OMNI-HUB <-> Cayley24")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    stats = r["project_statistics"]
    lines.append("| Project | Concepts | Theorems | Formulas | Axioms |")
    lines.append("|---------|----------|----------|----------|--------|")
    lines.append(f"| UCIF2 | {stats['ucif2']['concepts']} | {stats['ucif2']['theorems']} | {stats['ucif2']['formulas']} | {stats['ucif2']['axioms']} |")
    lines.append(f"| Cayley24 | {stats['cayley24']['concepts']} | {stats['cayley24']['theorems']} | {stats['cayley24']['formulas']} | — |")
    lines.append(f"| OMNI-HUB | {stats['omni']['concepts']} | {stats['omni']['theorems']} | {stats['omni']['formulas']} | — |")
    lines.append("")
    lines.append("## Pairwise Coupling Results")
    lines.append("")
    pw = r["pairwise_coupling"]
    for pair, data in pw.items():
        lines.append(f"### {pair}")
        lines.append(f"- **Exact concept matches**: {data['shared_concepts_exact']}")
        lines.append(f"- **Keyword semantic matches**: {data['shared_concepts_keyword']}")
        lines.append(f"- **Substring matches**: {data['shared_concepts_substring']}")
        lines.append(f"- **Shared theorems**: {data['shared_theorems']}")
        lines.append(f"- **Shared formulas**: {data['shared_formulas']}")
        lines.append(f"- **Jaccard similarity**: {data['jaccard_similarity']}")
        lines.append(f"- **Combined coupling score**: {data['combined_coupling_score']}")
        lines.append("")
    lines.append("## 3x3 Coupling Strength Matrix")
    lines.append("")
    mat = r["coupling_matrix_3x3"]
    labels = mat["labels"]
    matrix = mat["matrix"]
    lines.append(f"| | {labels[0]} | {labels[1]} | {labels[2]} |")
    lines.append(f"|---|---|---|---|")
    for i, label in enumerate(labels):
        row = matrix[i]
        lines.append(f"| **{label}** | {row[0]} | {row[1]} | {row[2]} |")
    lines.append("")
    tc = r["triangle_consistency"]
    lines.append("## Triangle Consistency Metrics")
    lines.append("")
    lines.append(f"- **Triangle closure C_abc**: `{tc['triangle_closure_C_abc']}`")
    lines.append(f"- **Global triangle CPI**: `{tc['global_triangle_coupling_index_CPI_triangle']}`")
    lines.append(f"- **Current pairwise CPI**: `{tc['current_pairwise_CPI']}`")
    lines.append(f"- **Target CPI**: `{tc['target_CPI']}`")
    lines.append(f"- **Gap to target**: `{tc['gap_to_target']}`")
    lines.append("")
    bc = r["bridge_concepts"]
    lines.append(f"## Bridge Concepts (n={bc['total_bridges_found']})")
    lines.append("")
    for b in bc["bridges"][:20]:
        lines.append(f"- **UCIF2**: `{b['ucif2_concept']}`")
        lines.append(f"  - Cayley24: {', '.join(b['cayley24_matches'][:2])}")
        lines.append(f"  - OMNI-HUB: {', '.join(b['omni_matches'][:2])}")
        lines.append(f"  - Keywords: {', '.join(b['keyword_groups'])}")
        lines.append("")
    ga = r["gap_analysis"]
    lines.append(f"## Gap Analysis (n={ga['total_gaps']})")
    lines.append("")
    for g in ga["gaps"]:
        lines.append(f"- [{g['relevance']}] `{g['cayley24_component']}` <-> `{g['ucif2_connection']}`")
    lines.append("")
    ci = r["cpi_improvement_scenarios"]
    lines.append("## CPI Improvement Scenarios")
    lines.append("")
    lines.append("| Scenario | Pairwise CPI | Triangle Closure | Improvement Factor |")
    lines.append("|----------|-------------|------------------|-------------------|")
    lines.append(f"| Current | {ci['current']['pairwise_cpi']} | {ci['current']['triangle_closure']} | 1.0x |")
    for name, data in ci["scenarios"].items():
        ppi = data.get('pairwise_cpi', data.get('required_pairwise', 'N/A'))
        lines.append(f"| {name} | {ppi} | {data['triangle_closure']} | {data['improvement_factor']}x |")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by TriangleCouplingAnalyzer based on actual JSON data.*")
    return "\n".join(lines)

if __name__ == "__main__":
    main()