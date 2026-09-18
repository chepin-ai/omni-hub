
__version__ = "11.0.0"
"""
OMNI-HUB v5.0 - SelfEvolvingArchitecture
=====================================
自演化架构引擎 - 基于结构耦合理论的软件架构演化系统
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict
import random
from datetime import datetime
import logging


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class RefactoringPlan:
    plan_id: str
    type: str
    target: str
    description: str
    expected_improvement: Dict[str, float]
    risk: str
    details: Dict[str, Any] = field(default_factory=dict)
    status: str = "proposed"

    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id, "type": self.type,
            "target": self.target, "description": self.description,
            "expected_improvement": self.expected_improvement,
            "risk": self.risk, "details": self.details,
            "status": self.status
        }


@dataclass
class ModuleDesign:
    name: str
    purpose: str
    responsibilities: List[str]
    dependencies: List[str]
    si_level: int
    estimated_complexity: float
    rationale: str

    def to_dict(self) -> Dict:
        return {
            "name": self.name, "purpose": self.purpose,
            "responsibilities": self.responsibilities,
            "dependencies": self.dependencies,
            "si_level": self.si_level,
            "estimated_complexity": self.estimated_complexity,
            "rationale": self.rationale
        }


@dataclass
class EvolutionRecord:
    step: int
    timestamp: str
    action: str
    details: Dict[str, Any]
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]

    def to_dict(self) -> Dict:
        return {
            "step": self.step, "timestamp": self.timestamp,
            "action": self.action, "details": self.details,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after
        }


# ============================================================================
# ArchitectureGraph - 架构拓扑图
# ============================================================================

class ArchitectureGraph:
    """架构图 - 使用纯Python字典实现"""

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.edges: Dict[Tuple[str, str], Dict] = {}
        self.adj_out: Dict[str, Set[str]] = defaultdict(set)
        self.adj_in: Dict[str, Set[str]] = defaultdict(set)

    def add_module(self, name: str, metadata: Dict[str, Any]) -> None:
        self.nodes[name] = metadata
        if name not in self.adj_out:
            self.adj_out[name] = set()
        if name not in self.adj_in:
            self.adj_in[name] = set()

    def add_dependency(self, src: str, dst: str, weight: float = 1.0,
                       dependency_type: str = "import") -> None:
        if src not in self.nodes or dst not in self.nodes:
            return

        key = (src, dst)
        if key in self.edges:
            self.edges[key]["weight"] += weight
            self.edges[key]["interaction_count"] = self.edges[key].get("interaction_count", 0) + 1
        else:
            self.edges[key] = {
                "weight": weight, "interaction_count": 1,
                "dependency_type": dependency_type,
                "created_at": datetime.now().isoformat()
            }
            self.adj_out[src].add(dst)
            self.adj_in[dst].add(src)

    def record_message(self, src: str, dst: str, msg_size: float = 1.0) -> None:
        if src not in self.nodes or dst not in self.nodes:
            return
        if (src, dst) in self.edges:
            self.edges[(src, dst)]["weight"] += msg_size * 0.1
            self.edges[(src, dst)]["interaction_count"] = self.edges[(src, dst)].get("interaction_count", 0) + 1
        else:
            self.add_dependency(src, dst, weight=msg_size * 0.1)

    def get_coupling(self, module: str) -> Dict[str, float]:
        if module not in self.nodes:
            return {"in": 0, "out": 0, "total": 0, "efferent": 0, "afferent": 0, "instability": 0}

        out_weight = sum(self.edges[(module, dst)].get("weight", 1.0) 
                        for dst in self.adj_out[module] if (module, dst) in self.edges)
        in_weight = sum(self.edges[(src, module)].get("weight", 1.0) 
                       for src in self.adj_in[module] if (src, module) in self.edges)
        total = out_weight + in_weight

        return {
            "in": in_weight, "out": out_weight, "total": total,
            "efferent": out_weight, "afferent": in_weight,
            "instability": out_weight / total if total > 0 else 0
        }

    def get_centrality(self) -> Dict[str, float]:
        n = len(self.nodes)
        if n <= 1:
            return {name: 1.0 for name in self.nodes}

        centrality = {}
        for name in self.nodes:
            in_w = sum(self.edges[(src, name)].get("weight", 1.0) 
                      for src in self.adj_in[name] if (src, name) in self.edges)
            out_w = sum(self.edges[(name, dst)].get("weight", 1.0) 
                       for dst in self.adj_out[name] if (name, dst) in self.edges)
            centrality[name] = (in_w + out_w) / (2 * n) if n > 0 else 0

        max_c = max(centrality.values()) if centrality else 1
        if max_c > 0:
            centrality = {k: v / max_c for k, v in centrality.items()}
        return centrality

    def detect_cycles(self, max_cycles: int = 5) -> List[List[str]]:
        """使用DFS检测循环"""
        cycles = []

        for start_node in list(self.nodes.keys())[:20]:  # 限制起始节点数
            if len(cycles) >= max_cycles:
                break

            stack = [(start_node, [start_node], set([start_node]))]

            while stack and len(cycles) < max_cycles:
                node, path, path_set = stack.pop()

                for neighbor in list(self.adj_out.get(node, set()))[:10]:  # 限制邻居数
                    if neighbor in path_set:
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        if len(cycle) >= 3:
                            cycle_nodes = cycle[:-1]
                            is_new = True
                            for existing in cycles:
                                if set(existing) == set(cycle_nodes):
                                    is_new = False
                                    break
                            if is_new:
                                cycles.append(cycle_nodes)
                    elif len(path) < 8:
                        stack.append((neighbor, path + [neighbor], path_set | {neighbor}))

        return cycles[:max_cycles]

    def get_complexity(self) -> Dict[str, float]:
        n = len(self.nodes)
        e = len(self.edges)

        if n == 0:
            return {"total": 0, "cyclomatic": 0, "density": 0, 
                    "avg_coupling": 0, "modularity": 0, "edge_count": 0, "node_count": 0}

        cyclomatic = max(0, e - n + 2)
        max_edges = n * (n - 1)
        density = e / max_edges if max_edges > 0 else 0

        couplings = [self.get_coupling(m)["total"] for m in self.nodes]
        avg_coupling = np.mean(couplings) if couplings else 0

        modularity = self._approximate_modularity()

        total = cyclomatic * 0.3 + density * 100 * 0.2 + avg_coupling * 0.3 + max(0, 1 - modularity) * 50 * 0.2

        return {
            "total": total, "cyclomatic": cyclomatic, "density": density,
            "avg_coupling": avg_coupling, "modularity": modularity,
            "edge_count": e, "node_count": n
        }

    def _approximate_modularity(self) -> float:
        if len(self.nodes) < 3:
            return 0.0

        undirected_adj = defaultdict(set)
        for src, dst in self.edges:
            undirected_adj[src].add(dst)
            undirected_adj[dst].add(src)

        visited = set()
        communities = []

        for node in self.nodes:
            if node not in visited:
                community = set()
                queue = [node]
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        community.add(current)
                        queue.extend(undirected_adj[current] - visited)
                communities.append(community)

        if len(communities) <= 1:
            return 0.0

        total_edges = len(self.edges)
        if total_edges == 0:
            return 0.0

        modularity = 0.0
        for comm in communities:
            internal_edges = sum(1 for src, dst in self.edges if src in comm and dst in comm)
            comm_degree = sum(len(self.adj_out[node]) + len(self.adj_in[node]) for node in comm)

            expected = (comm_degree / (2 * total_edges)) ** 2 if total_edges > 0 else 0
            actual = internal_edges / total_edges if total_edges > 0 else 0
            modularity += actual - expected

        return max(0, modularity)

    def get_mutual_dependencies(self, top_n: int = 10) -> List[Tuple[str, str, float]]:
        mutual = []
        seen = set()
        for (u, v), d in self.edges.items():
            if (v, u) in seen:
                continue
            if (v, u) in self.edges:
                combined = d.get("weight", 1.0) + self.edges[(v, u)].get("weight", 1.0)
                mutual.append((u, v, combined))
                seen.add((u, v))

        mutual.sort(key=lambda x: x[2], reverse=True)
        return mutual[:top_n]

    def get_orphan_modules(self) -> List[str]:
        return [node for node in self.nodes 
                if len(self.adj_in[node]) == 0 and len(self.adj_out[node]) == 0]

    def get_communities(self) -> List[Set[str]]:
        undirected_adj = defaultdict(set)
        for src, dst in self.edges:
            undirected_adj[src].add(dst)
            undirected_adj[dst].add(src)

        visited = set()
        communities = []

        for node in self.nodes:
            if node not in visited:
                community = set()
                queue = [node]
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        community.add(current)
                        queue.extend(undirected_adj[current] - visited)
                communities.append(community)

        return communities

    def remove_module(self, name: str) -> None:
        if name in self.nodes:
            for dst in list(self.adj_out[name]):
                if (name, dst) in self.edges:
                    del self.edges[(name, dst)]
            for src in list(self.adj_in[name]):
                if (src, name) in self.edges:
                    del self.edges[(src, name)]

            del self.nodes[name]
            self.adj_out.pop(name, None)
            self.adj_in.pop(name, None)

            for src in self.adj_out:
                self.adj_out[src].discard(name)
            for dst in self.adj_in:
                self.adj_in[dst].discard(name)

    def merge_modules(self, m1: str, m2: str, new_name: str) -> None:
        if m1 not in self.nodes or m2 not in self.nodes:
            return

        meta1 = self.nodes[m1]
        meta2 = self.nodes[m2]
        new_meta = {
            "si_level": max(meta1.get("si_level", 1), meta2.get("si_level", 1)),
            "file_path": f"merged_{m1}_{m2}.py",
            "merged_from": [m1, m2],
            "created_at": datetime.now().isoformat(),
            "complexity": meta1.get("complexity", 1) + meta2.get("complexity", 1)
        }

        self.add_module(new_name, new_meta)

        for src in self.adj_in.get(m1, set()):
            if src != new_name and (src, m1) in self.edges:
                self.add_dependency(src, new_name, self.edges[(src, m1)].get("weight", 1.0))
        for dst in self.adj_out.get(m1, set()):
            if dst != new_name and (m1, dst) in self.edges:
                self.add_dependency(new_name, dst, self.edges[(m1, dst)].get("weight", 1.0))

        for src in self.adj_in.get(m2, set()):
            if src != new_name and (src, m2) in self.edges:
                self.add_dependency(src, new_name, self.edges[(src, m2)].get("weight", 1.0))
        for dst in self.adj_out.get(m2, set()):
            if dst != new_name and (m2, dst) in self.edges:
                self.add_dependency(new_name, dst, self.edges[(m2, dst)].get("weight", 1.0))

        self.remove_module(m1)
        self.remove_module(m2)

    def split_module(self, module: str, parts: List[Tuple[str, Dict]]) -> None:
        if module not in self.nodes:
            return

        old_meta = self.nodes[module]

        for part_name, part_meta in parts:
            full_meta = {**old_meta, **part_meta, "split_from": module}
            self.add_module(part_name, full_meta)

        for dst in list(self.adj_out.get(module, set())):
            if (module, dst) in self.edges:
                for part_name, _ in parts:
                    if dst != part_name:
                        self.add_dependency(part_name, dst, 
                                          self.edges[(module, dst)].get("weight", 1.0) / len(parts))

        for src in list(self.adj_in.get(module, set())):
            if (src, module) in self.edges:
                for part_name, _ in parts:
                    if src != part_name:
                        self.add_dependency(src, part_name, 
                                          self.edges[(src, module)].get("weight", 1.0) / len(parts))

        self.remove_module(module)


# ============================================================================
# SelfEvolvingArchitecture - 自演化架构引擎 (平衡版)
# ============================================================================

class SelfEvolvingArchitecture:
    """自演化架构引擎 - 平衡版"""

    def __init__(self, 
                 coupling_threshold: float = 15.0,
                 mutual_coupling_threshold: float = 20.0,
                 complexity_threshold: float = 50.0,
                 retirement_age: int = 12,
                 retirement_inactivity: int = 6,
                 max_modules: int = 60):
        self.arch_graph = ArchitectureGraph()
        self.modules: Dict[str, Dict] = {}
        self.refactoring_plans: List[RefactoringPlan] = []
        self.evolution_history: List[EvolutionRecord] = []
        self.current_step = 0

        self.coupling_threshold = coupling_threshold
        self.mutual_coupling_threshold = mutual_coupling_threshold
        self.complexity_threshold = complexity_threshold
        self.retirement_age = retirement_age
        self.retirement_inactivity = retirement_inactivity
        self.max_modules = max_modules

        self.stats = {
            "refactorings_applied": 0,
            "modules_incubated": 0,
            "modules_retired": 0,
            "cycles_resolved": 0,
            "splits": 0,
            "merges": 0,
            "extracts": 0
        }

        self.required_capabilities = {
            "intent_generation", "pattern_recognition", "self_modeling",
            "value_alignment", "temporal_reasoning", "causal_inference",
            "meta_learning", "uncertainty_quantification"
        }
        self.current_capabilities: Set[str] = set()

    def register_module(self, name: str, file_path: str, 
                        si_level: int = 1,
                        dependencies: List[str] = None,
                        capabilities: List[str] = None,
                        complexity: float = 1.0) -> None:
        metadata = {
            "file_path": file_path,
            "si_level": si_level,
            "complexity": complexity,
            "registered_at": self.current_step,
            "last_active": self.current_step,
            "call_count": 0,
            "capabilities": set(capabilities or [])
        }

        self.modules[name] = metadata
        self.arch_graph.add_module(name, metadata)
        self.current_capabilities.update(capabilities or [])

        if dependencies:
            for dep in dependencies:
                if dep in self.modules:
                    self.arch_graph.add_dependency(name, dep, weight=2.0)

    def simulate_interaction(self, src: str, dst: str, 
                           intensity: float = 1.0) -> None:
        if src in self.modules and dst in self.modules:
            self.arch_graph.record_message(src, dst, intensity)
            self.modules[src]["last_active"] = self.current_step
            self.modules[src]["call_count"] = self.modules[src].get("call_count", 0) + 1
            self.modules[dst]["last_active"] = self.current_step

    def analyze_topology(self) -> Dict[str, Any]:
        coupling_data = {}
        for module in self.arch_graph.nodes:
            coupling_data[module] = self.arch_graph.get_coupling(module)

        return {
            "coupling": coupling_data,
            "centrality": self.arch_graph.get_centrality(),
            "cycles": self.arch_graph.detect_cycles(max_cycles=5),
            "complexity": self.arch_graph.get_complexity(),
            "mutual_dependencies": self.arch_graph.get_mutual_dependencies(top_n=10),
            "orphans": self.arch_graph.get_orphan_modules(),
            "communities": self.arch_graph.get_communities(),
            "timestamp": datetime.now().isoformat()
        }

    def detect_architecture_smells(self) -> List[str]:
        smells = []
        analysis = self.analyze_topology()

        # 只检测前20%最高耦合的模块
        all_couplings = [(m, c["total"]) for m, c in analysis["coupling"].items()]
        all_couplings.sort(key=lambda x: x[1], reverse=True)
        top_coupled = set(m for m, _ in all_couplings[:max(1, len(all_couplings) // 5)])

        for module, coupling in analysis["coupling"].items():
            if module in top_coupled and coupling["total"] > self.coupling_threshold:
                smells.append(
                    f"模块'{module}'耦合度过高 (总耦合={coupling['total']:.2f})"
                )

        for cycle in analysis["cycles"]:
            cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
            smells.append(f"循环依赖: {cycle_str}")

        for m1, m2, weight in analysis["mutual_dependencies"]:
            if weight > self.mutual_coupling_threshold:
                smells.append(
                    f"模块'{m1}'与'{m2}'高度互依赖 (权重={weight:.2f})"
                )

        comp = analysis["complexity"]
        if comp["total"] > self.complexity_threshold:
            smells.append(f"架构复杂度过高 (总分={comp['total']:.2f})")

        for orphan in analysis["orphans"]:
            smells.append(f"模块'{orphan}'孤立无连接")

        for name, meta in self.modules.items():
            age = self.current_step - meta.get("registered_at", 0)
            inactive = self.current_step - meta.get("last_active", 0)
            if age > self.retirement_age and inactive > self.retirement_inactivity:
                smells.append(
                    f"模块'{name}'长期不活跃 (年龄={age}, 不活跃={inactive}步)"
                )

        missing_caps = self.required_capabilities - self.current_capabilities
        for cap in missing_caps:
            smells.append(f"缺少能力'{cap}'，需要孵化新模块")

        return smells

    def propose_refactoring(self) -> List[RefactoringPlan]:
        plans = []
        analysis = self.analyze_topology()

        # 拆分：只针对最耦合的模块
        all_couplings = [(m, c["total"]) for m, c in analysis["coupling"].items()]
        all_couplings.sort(key=lambda x: x[1], reverse=True)
        top_n = max(1, len(all_couplings) // 10)

        for module, coupling in all_couplings[:top_n]:
            if coupling > self.coupling_threshold:
                plans.append(RefactoringPlan(
                    plan_id=f"split_{module}_{self.current_step}",
                    type="split",
                    target=module,
                    description=f"将高耦合模块'{module}'拆分",
                    expected_improvement={
                        "coupling_reduction": coupling * 0.4,
                        "complexity_reduction": 3.0
                    },
                    risk="medium",
                    details={
                        "current_coupling": {"total": coupling},
                        "suggested_parts": [f"{module}_core", f"{module}_utils"]
                    }
                ))

        # 合并：高度互依赖
        for m1, m2, weight in analysis["mutual_dependencies"]:
            if weight > self.mutual_coupling_threshold:
                plans.append(RefactoringPlan(
                    plan_id=f"merge_{m1}_{m2}_{self.current_step}",
                    type="merge",
                    target=f"{m1}+{m2}",
                    description=f"合并高度互依赖的模块'{m1}'和'{m2}'",
                    expected_improvement={"coupling_reduction": weight * 0.5},
                    risk="low",
                    details={"mutual_weight": weight, "modules": [m1, m2]}
                ))

        # 提取接口打破循环
        for cycle in analysis["cycles"]:
            centrality = analysis["centrality"]
            cycle_centrality = {m: centrality.get(m, 0) for m in cycle}
            target_module = max(cycle_centrality, key=cycle_centrality.get)

            plans.append(RefactoringPlan(
                plan_id=f"extract_{target_module}_interface_{self.current_step}",
                type="extract",
                target=target_module,
                description=f"从'{target_module}'提取接口以打破循环依赖",
                expected_improvement={"cycles_resolved": 1, "coupling_reduction": 2.0},
                risk="low",
                details={"cycle": cycle, "extract_interface": True}
            ))

        # 简化
        comp = analysis["complexity"]
        if comp["total"] > self.complexity_threshold:
            plans.append(RefactoringPlan(
                plan_id=f"simplify_arch_{self.current_step}",
                type="inline",
                target="architecture",
                description="架构整体简化",
                expected_improvement={"complexity_reduction": comp["total"] * 0.2},
                risk="high",
                details={"current_complexity": comp}
            ))

        return plans

    def apply_refactoring(self, plan: RefactoringPlan) -> Dict[str, Any]:
        metrics_before = self.get_architecture_metrics()

        if plan.type == "split":
            return self._apply_split(plan, metrics_before)
        elif plan.type == "merge":
            return self._apply_merge(plan, metrics_before)
        elif plan.type == "extract":
            return self._apply_extract(plan, metrics_before)
        elif plan.type == "inline":
            return self._apply_inline(plan, metrics_before)
        else:
            return {"status": "unknown_type", "plan": plan.type}

    def _apply_split(self, plan: RefactoringPlan, metrics_before: Dict) -> Dict[str, Any]:
        module = plan.target
        if module not in self.modules:
            return {"status": "failed", "reason": "module_not_found"}

        # 如果模块数接近上限，不拆分
        if len(self.modules) >= self.max_modules * 0.9:
            return {"status": "blocked", "reason": "module_cap_reached"}

        parts = plan.details.get("suggested_parts", [f"{module}_part1", f"{module}_part2"])

        part_metas = []
        for part_name in parts:
            part_metas.append((part_name, {
                "si_level": self.modules[module].get("si_level", 1),
                "file_path": f"{part_name}.py",
                "complexity": self.modules[module].get("complexity", 1) / len(parts),
                "capabilities": self.modules[module].get("capabilities", set())
            }))

        self.arch_graph.split_module(module, part_metas)

        old_meta = self.modules.pop(module)
        for part_name, part_meta in part_metas:
            new_meta = {**old_meta, **part_meta, 
                       "split_from": module,
                       "registered_at": self.current_step,
                       "last_active": self.current_step,
                       "call_count": 0}
            self.modules[part_name] = new_meta

        self.stats["splits"] += 1
        self.stats["refactorings_applied"] += 1

        metrics_after = self.get_architecture_metrics()

        record = EvolutionRecord(
            step=self.current_step,
            timestamp=datetime.now().isoformat(),
            action="split_module",
            details={"module": module, "parts": [p[0] for p in part_metas]},
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )
        self.evolution_history.append(record)
        plan.status = "applied"

        return {"status": "success", "action": "split",
                "module": module, "parts": [p[0] for p in part_metas]}

    def _apply_merge(self, plan: RefactoringPlan, metrics_before: Dict) -> Dict[str, Any]:
        modules = plan.details.get("modules", [])
        if len(modules) != 2:
            return {"status": "failed", "reason": "invalid_modules"}

        m1, m2 = modules
        new_name = f"{m1}_{m2}_merged"

        self.arch_graph.merge_modules(m1, m2, new_name)

        meta1 = self.modules.pop(m1, {})
        meta2 = self.modules.pop(m2, {})
        self.modules[new_name] = {
            "si_level": max(meta1.get("si_level", 1), meta2.get("si_level", 1)),
            "file_path": f"{new_name}.py",
            "complexity": meta1.get("complexity", 1) + meta2.get("complexity", 1),
            "capabilities": meta1.get("capabilities", set()) | meta2.get("capabilities", set()),
            "merged_from": [m1, m2],
            "registered_at": self.current_step,
            "last_active": self.current_step,
            "call_count": 0
        }

        self.stats["merges"] += 1
        self.stats["refactorings_applied"] += 1

        metrics_after = self.get_architecture_metrics()

        record = EvolutionRecord(
            step=self.current_step,
            timestamp=datetime.now().isoformat(),
            action="merge_modules",
            details={"modules": [m1, m2], "new_name": new_name},
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )
        self.evolution_history.append(record)
        plan.status = "applied"

        return {"status": "success", "action": "merge",
                "modules": [m1, m2], "new_name": new_name}

    def _apply_extract(self, plan: RefactoringPlan, metrics_before: Dict) -> Dict[str, Any]:
        module = plan.target
        interface_name = f"{module}_interface"

        if module not in self.modules:
            return {"status": "failed", "reason": "module_not_found"}

        if len(self.modules) >= self.max_modules * 0.95:
            return {"status": "blocked", "reason": "module_cap_reached"}

        self.arch_graph.add_module(interface_name, {
            "si_level": self.modules[module].get("si_level", 1),
            "file_path": f"{interface_name}.py",
            "complexity": 0.5,
            "is_interface": True,
            "extracted_from": module
        })
        self.modules[interface_name] = {
            "si_level": self.modules[module].get("si_level", 1),
            "file_path": f"{interface_name}.py",
            "complexity": 0.5,
            "registered_at": self.current_step,
            "last_active": self.current_step,
            "call_count": 0,
            "extracted_from": module
        }

        for src in list(self.arch_graph.adj_in.get(module, set())):
            if src != interface_name and (src, module) in self.arch_graph.edges:
                self.arch_graph.add_dependency(src, interface_name, weight=0.5)

        self.stats["extracts"] += 1
        self.stats["refactorings_applied"] += 1

        metrics_after = self.get_architecture_metrics()

        record = EvolutionRecord(
            step=self.current_step,
            timestamp=datetime.now().isoformat(),
            action="extract_interface",
            details={"module": module, "interface": interface_name},
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )
        self.evolution_history.append(record)
        plan.status = "applied"

        return {"status": "success", "action": "extract",
                "module": module, "interface": interface_name}

    def _apply_inline(self, plan: RefactoringPlan, metrics_before: Dict) -> Dict[str, Any]:
        candidates = []
        for name, meta in self.modules.items():
            out_deg = len(self.arch_graph.adj_out.get(name, set()))
            in_deg = len(self.arch_graph.adj_in.get(name, set()))
            if out_deg == 0 and in_deg <= 1:
                candidates.append((name, meta.get("complexity", 1)))

        if candidates:
            to_inline = min(candidates, key=lambda x: x[1])[0]
            parents = list(self.arch_graph.adj_in.get(to_inline, set()))

            self.arch_graph.remove_module(to_inline)
            self.modules.pop(to_inline, None)

            self.stats["refactorings_applied"] += 1

            metrics_after = self.get_architecture_metrics()

            record = EvolutionRecord(
                step=self.current_step,
                timestamp=datetime.now().isoformat(),
                action="inline_module",
                details={"inlined": to_inline, "parents": parents},
                metrics_before=metrics_before,
                metrics_after=metrics_after
            )
            self.evolution_history.append(record)
            plan.status = "applied"

            return {"status": "success", "action": "inline", "inlined": to_inline}

        return {"status": "failed", "reason": "no_candidates"}


    def incubate_module(self, proposal: Dict[str, Any] = None) -> ModuleDesign:
        """孵化新模块"""
        if len(self.modules) >= self.max_modules:
            return ModuleDesign(
                name="blocked", purpose="Blocked by module cap",
                responsibilities=[], dependencies=[], si_level=1,
                estimated_complexity=0, rationale="Module cap reached"
            )

        missing_caps = self.required_capabilities - self.current_capabilities

        if proposal and "name" in proposal:
            design = ModuleDesign(
                name=proposal["name"],
                purpose=proposal.get("purpose", "New capability module"),
                responsibilities=proposal.get("responsibilities", []),
                dependencies=proposal.get("dependencies", []),
                si_level=proposal.get("si_level", 2),
                estimated_complexity=proposal.get("complexity", 2.0),
                rationale=proposal.get("rationale", "Addressing capability gap")
            )
        elif missing_caps:
            cap = random.choice(list(missing_caps))
            design = ModuleDesign(
                name=f"{cap}_module",
                purpose=f"Provide {cap} capability",
                responsibilities=[f"Handle {cap} operations"],
                dependencies=list(self.modules.keys())[:3],
                si_level=3,
                estimated_complexity=2.5,
                rationale=f"Missing required capability: {cap}"
            )
            self.current_capabilities.add(cap)
        else:
            design = ModuleDesign(
                name=f"emergent_{self.current_step}",
                purpose="Emergent capability from system evolution",
                responsibilities=["Cross-module integration"],
                dependencies=list(self.modules.keys())[:2],
                si_level=4,
                estimated_complexity=3.0,
                rationale="Emergent need from structural coupling"
            )

        self.register_module(
            name=design.name,
            file_path=f"{design.name}.py",
            si_level=design.si_level,
            dependencies=design.dependencies,
            capabilities=design.responsibilities,
            complexity=design.estimated_complexity
        )

        self.stats["modules_incubated"] += 1

        metrics_before = self.get_architecture_metrics()
        metrics_after = self.get_architecture_metrics()

        record = EvolutionRecord(
            step=self.current_step,
            timestamp=datetime.now().isoformat(),
            action="incubate_module",
            details={"design": design.to_dict()},
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )
        self.evolution_history.append(record)

        return design

    def retire_module(self, module_name: str) -> Dict[str, Any]:
        """退役模块"""
        if module_name not in self.modules:
            return {"status": "failed", "reason": "module_not_found"}

        dependents = list(self.arch_graph.adj_in.get(module_name, set()))
        if dependents:
            return {
                "status": "blocked", 
                "reason": "has_dependents",
                "dependents": dependents
            }

        coupling = self.arch_graph.get_coupling(module_name)
        if coupling["total"] > 5:
            return {
                "status": "blocked",
                "reason": "too_coupled",
                "coupling": coupling
            }

        meta = self.modules.pop(module_name)
        self.arch_graph.remove_module(module_name)

        for cap in meta.get("capabilities", set()):
            providers = [m for m, md in self.modules.items() 
                        if cap in md.get("capabilities", set())]
            if not providers:
                self.current_capabilities.discard(cap)

        self.stats["modules_retired"] += 1

        metrics_before = self.get_architecture_metrics()
        metrics_after = self.get_architecture_metrics()

        record = EvolutionRecord(
            step=self.current_step,
            timestamp=datetime.now().isoformat(),
            action="retire_module",
            details={"module": module_name, "reason": "redundant"},
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )
        self.evolution_history.append(record)

        return {
            "status": "success",
            "module": module_name,
            "reason": "redundant_or_inactive"
        }

    def evolution_step(self) -> Dict[str, Any]:
        """演化一步"""
        self.current_step += 1

        results = {
            "step": self.current_step,
            "smells": [],
            "plans_proposed": 0,
            "plans_applied": 0,
            "modules_incubated": 0,
            "modules_retired": 0,
            "metrics": {}
        }

        # Step 1: 模拟结构耦合
        self._simulate_structural_coupling()

        # Step 2: 检测架构异味
        smells = self.detect_architecture_smells()
        results["smells"] = smells

        # Step 3: 生成重构计划
        plans = self.propose_refactoring()
        results["plans_proposed"] = len(plans)
        self.refactoring_plans.extend(plans)

        # Step 4: 应用重构计划
        applied = 0

        # 强制周期性合并（每5步合并最互依赖的一对）
        if self.current_step % 5 == 0:
            analysis = self.analyze_topology()
            if analysis["mutual_dependencies"]:
                m1, m2, weight = analysis["mutual_dependencies"][0]
                plan = RefactoringPlan(
                    plan_id=f"forced_merge_{self.current_step}",
                    type="merge",
                    target=f"{m1}+{m2}",
                    description=f"强制合并互依赖模块'{m1}'和'{m2}'",
                    expected_improvement={"coupling_reduction": weight * 0.5},
                    risk="low",
                    details={"mutual_weight": weight, "modules": [m1, m2]}
                )
                result = self.apply_refactoring(plan)
                if result.get("status") == "success":
                    applied += 1

        # 强制周期性拆分（每8步拆分最耦合模块）
        if self.current_step % 8 == 0 and len(self.modules) < self.max_modules * 0.9:
            analysis = self.analyze_topology()
            all_couplings = [(m, c["total"]) for m, c in analysis["coupling"].items()]
            if all_couplings:
                all_couplings.sort(key=lambda x: x[1], reverse=True)
                module, coupling = all_couplings[0]
                if coupling > 3.0:
                    plan = RefactoringPlan(
                        plan_id=f"forced_split_{self.current_step}",
                        type="split",
                        target=module,
                        description=f"强制拆分高耦合模块'{module}'",
                        expected_improvement={"coupling_reduction": coupling * 0.4},
                        risk="medium",
                        details={
                            "current_coupling": {"total": coupling},
                            "suggested_parts": [f"{module}_core", f"{module}_utils"]
                        }
                    )
                    result = self.apply_refactoring(plan)
                    if result.get("status") == "success":
                        applied += 1

        # 应用生成的计划（合并优先）
        merge_plans = [p for p in plans if p.type == "merge"]
        for plan in merge_plans[:2]:
            result = self.apply_refactoring(plan)
            if result.get("status") == "success":
                applied += 1

        inline_plans = [p for p in plans if p.type == "inline"]
        for plan in inline_plans[:1]:
            result = self.apply_refactoring(plan)
            if result.get("status") == "success":
                applied += 1

        split_plans = [p for p in plans if p.type == "split"]
        for plan in split_plans[:1]:
            if len(self.modules) < self.max_modules * 0.85:
                result = self.apply_refactoring(plan)
                if result.get("status") == "success":
                    applied += 1

        # Step 5: 孵化新模块
        missing_caps = self.required_capabilities - self.current_capabilities
        if len(self.modules) < self.max_modules * 0.8 and missing_caps and random.random() > 0.8:
            design = self.incubate_module()
            results["modules_incubated"] = 1
            results["incubated_design"] = design.to_dict()

        # Step 6: 退役冗余模块
        retirement_candidates = []
        for name, meta in list(self.modules.items()):
            age = self.current_step - meta.get("registered_at", 0)
            inactive = self.current_step - meta.get("last_active", 0)
            if age > self.retirement_age and inactive > self.retirement_inactivity:
                retirement_candidates.append(name)

        if retirement_candidates:
            retire_prob = 0.9 if len(self.modules) > self.max_modules * 0.6 else 0.6
            if random.random() < retire_prob:
                to_retire = random.choice(retirement_candidates)
                result = self.retire_module(to_retire)
                if result.get("status") == "success":
                    results["modules_retired"] = 1
                    results["retired_module"] = to_retire

        results["plans_applied"] = applied
        results["metrics"] = self.get_architecture_metrics()
        results["module_count"] = len(self.modules)

        return results

    def _simulate_structural_coupling(self) -> None:
        """模拟结构耦合（极简版）"""
        modules = list(self.modules.keys())
        if len(modules) < 2:
            return

        # 仅2-3次随机交互
        n_interactions = random.randint(3, 5)
        for _ in range(n_interactions):
            src, dst = random.sample(modules, 2)
            intensity = random.uniform(0.8, 2.0)
            self.simulate_interaction(src, dst, intensity)

        # 极弱的连接强化
        for (src, dst), data in list(self.arch_graph.edges.items()):
            if random.random() > 0.95:
                weight = data.get("weight", 1.0)
                self.arch_graph.edges[(src, dst)]["weight"] += weight * 0.01

    def get_evolution_history(self) -> List[Dict]:
        """获取演化历史"""
        return [record.to_dict() for record in self.evolution_history]

    def get_architecture_metrics(self) -> Dict[str, float]:
        """获取当前架构指标"""
        analysis = self.analyze_topology()
        comp = analysis["complexity"]

        couplings = [c["total"] for c in analysis["coupling"].values()]
        avg_coupling = np.mean(couplings) if couplings else 0
        max_coupling = max(couplings) if couplings else 0

        centrality_values = list(analysis["centrality"].values())
        centrality_entropy = self._calculate_entropy(centrality_values) if centrality_values else 0

        return {
            "total_complexity": comp["total"],
            "cyclomatic": comp["cyclomatic"],
            "density": comp["density"],
            "avg_coupling": avg_coupling,
            "max_coupling": max_coupling,
            "modularity": comp["modularity"],
            "node_count": comp["node_count"],
            "edge_count": comp["edge_count"],
            "cycle_count": len(analysis["cycles"]),
            "centrality_entropy": centrality_entropy,
            "orphan_count": len(analysis["orphans"]),
            "community_count": len(analysis["communities"])
        }

    def _calculate_entropy(self, values: List[float]) -> float:
        """计算香农熵"""
        if not values or sum(values) == 0:
            return 0
        probs = np.array(values) / sum(values)
        probs = probs[probs > 0]
        return -np.sum(probs * np.log2(probs))

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "current_step": self.current_step,
            "module_count": len(self.modules),
            "current_capabilities": list(self.current_capabilities),
            "missing_capabilities": list(self.required_capabilities - self.current_capabilities)
        }


# ============================================================================
# 实验验证
# ============================================================================
"""
OMNI-HUB v11.0 — self_evolving_architecture
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

def run_evolution_experiment():
    """运行演化实验"""
    logger.info("=" * 80)
    logger.info("OMNI-HUB v5.0 - SelfEvolvingArchitecture 实验")
    logger.info("=" * 80)

    engine = SelfEvolvingArchitecture(
        coupling_threshold=8.0,
        mutual_coupling_threshold=2.0,
        complexity_threshold=60.0,
        retirement_age=6,
        retirement_inactivity=3,
        max_modules=60
    )

    v4_modules = [
        ("self_drive_engine", "core/self_drive.py", 5,
         ["bidirectional_drive", "si_topology", "tensor_field"],
         ["autonomy", "self_modeling"], 3.5),
        ("bidirectional_drive", "core/bidirectional.py", 4,
         ["si_topology", "closed_loop"],
         ["bidirectional_communication"], 2.5),
        ("si_topology", "core/topology.py", 6,
         ["si_chain_reactor", "tensor_field", "quantum_field"],
         ["pattern_recognition", "self_modeling"], 4.0),
        ("si_chain_reactor", "core/chain_reactor.py", 5,
         ["si_topology", "field_entropy"],
         ["causal_inference"], 3.0),
        ("discussion_board", "comm/discussion.py", 2,
         ["inbox_outbox", "task_dispatcher"],
         ["communication"], 1.5),
        ("inbox_outbox", "comm/inbox.py", 2,
         ["task_dispatcher", "discussion_board"],
         ["communication"], 1.5),
        ("task_dispatcher", "core/dispatcher.py", 3,
         ["debt_cleanup", "debt_fuel_converter"],
         ["coordination"], 2.0),
        ("debt_cleanup", "finance/cleanup.py", 2,
         ["debt_fuel_converter"],
         ["resource_management"], 1.5),
        ("debt_fuel_converter", "finance/fuel.py", 3,
         ["debt_cleanup", "tensor_field"],
         ["resource_conversion"], 2.0),
        ("octave_scan", "sense/octave.py", 3,
         ["consciousness_harmony", "finding_recursion"],
         ["pattern_recognition"], 2.5),
        ("consciousness_harmony", "sense/harmony.py", 4,
         ["octave_scan", "quantum_field"],
         ["value_alignment"], 3.0),
        ("finding_recursion", "sense/recursion.py", 4,
         ["si_auto_protocol", "self_referential"],
         ["pattern_recognition", "self_modeling"], 3.0),
        ("si_auto_protocol", "protocol/auto.py", 5,
         ["si_topology", "closed_loop"],
         ["autonomy", "self_modeling"], 3.5),
        ("field_entropy", "field/entropy.py", 4,
         ["tensor_field", "quantum_field"],
         ["uncertainty_quantification"], 3.0),
        ("tensor_field", "field/tensor.py", 5,
         ["quantum_field", "field_transient"],
         ["pattern_recognition"], 4.0),
        ("quantum_field", "field/quantum.py", 6,
         ["tensor_field", "self_referential"],
         ["uncertainty_quantification", "causal_inference"], 4.5),
        ("closed_loop", "core/closed_loop.py", 5,
         ["self_referential", "meta_structure"],
         ["autonomy", "self_modeling"], 3.5),
        ("self_referential", "core/self_ref.py", 6,
         ["meta_structure", "strange_loop"],
         ["self_modeling", "meta_learning"], 4.0),
        ("meta_structure", "core/meta.py", 5,
         ["linguistic_field", "jing_wei_xin"],
         ["meta_learning"], 3.5),
        ("linguistic_field", "field/linguistic.py", 3,
         ["jing_wei_xin", "voice_melody"],
         ["communication"], 2.0),
        ("jing_wei_xin", "core/jingweixin.py", 4,
         ["linguistic_field", "quantum_base_v2"],
         ["value_alignment"], 2.5),
        ("quantum_base_v2", "core/quantum_base.py", 5,
         ["quantum_field", "field_transient"],
         ["uncertainty_quantification"], 3.5),
        ("field_transient", "field/transient.py", 4,
         ["tensor_field", "counterpoint_seats"],
         ["temporal_reasoning"], 3.0),
        ("counterpoint_seats", "music/counterpoint.py", 3,
         ["voice_melody", "cantus_firmus"],
         ["pattern_recognition"], 2.0),
        ("voice_melody", "music/voice.py", 2,
         ["cantus_firmus", "counterpoint_engine"],
         ["communication"], 1.5),
        ("cantus_firmus", "music/cantus.py", 3,
         ["counterpoint_engine", "counterpoint_seats"],
         ["pattern_recognition"], 2.0),
        ("counterpoint_engine", "music/engine.py", 4,
         ["strange_loop", "insight_detector"],
         ["causal_inference"], 3.0),
        ("strange_loop", "core/strange_loop.py", 6,
         ["insight_detector", "complexity_elevation"],
         ["self_modeling", "meta_learning"], 4.5),
        ("insight_detector", "sense/insight.py", 4,
         ["complexity_elevation", "finding_recursion"],
         ["pattern_recognition"], 3.0),
        ("complexity_elevation", "core/complexity.py", 5,
         ["strange_loop", "self_referential"],
         ["meta_learning"], 4.0),
    ]

    logger.info("\n[Phase 1] 注册 OMNI-HUB v4.1 模块 (30个)...")
    for name, path, si_level, deps, caps, complexity in v4_modules:
        engine.register_module(
            name=name, file_path=path, si_level=si_level,
            dependencies=deps, capabilities=caps, complexity=complexity
        )

    logger.info(f"  Registered {len(engine.modules)} modules")

    logger.info("\n[Phase 2] 初始架构分析...")
    initial_metrics = engine.get_architecture_metrics()
    initial_smells = engine.detect_architecture_smells()

    logger.info(f"  初始复杂度: {initial_metrics['total_complexity']:.2f}")
    logger.info(f"  模块数量: {initial_metrics['node_count']}")
    logger.info(f"  依赖边数: {initial_metrics['edge_count']}")
    logger.info(f"  循环依赖: {initial_metrics['cycle_count']}")
    logger.info(f"  架构异味: {len(initial_smells)} 个")

    logger.info("\n[Phase 3] 运行 50 个演化步骤...")
    logger.info("-" * 80)

    step_results = []
    metrics_history = [initial_metrics]

    for step in range(50):
        result = engine.evolution_step()
        step_results.append(result)
        metrics_history.append(result["metrics"])

        if step % 10 == 9:
            print(f"  Step {step+1:3d}: 模块={result['module_count']:3d}, "
                  f"复杂度={result['metrics']['total_complexity']:6.2f}, "
                  f"异味={len(result['smells']):2d}, "
                  f"应用={result['plans_applied']:2d}")

    logger.info("-" * 80)

    logger.info("\n[Phase 4] 最终架构分析...")
    final_metrics = engine.get_architecture_metrics()
    final_smells = engine.detect_architecture_smells()
    stats = engine.get_stats()

    logger.info(f"  最终复杂度: {final_metrics['total_complexity']:.2f}")
    logger.info(f"  模块数量: {final_metrics['node_count']}")
    logger.info(f"  依赖边数: {final_metrics['edge_count']}")
    logger.info(f"  循环依赖: {final_metrics['cycle_count']}")
    logger.info(f"  架构异味: {len(final_smells)} 个")

    logger.info("\n[Phase 5] 演化统计...")
    logger.info("-" * 80)
    logger.info(f"  总演化步骤: {stats['current_step']}")
    logger.info(f"  重构应用次数: {stats['refactorings_applied']}")
    logger.info(f"    - 拆分次数: {stats['splits']}")
    logger.info(f"    - 合并次数: {stats['merges']}")
    logger.info(f"    - 提取次数: {stats['extracts']}")
    logger.info(f"  新模块孵化: {stats['modules_incubated']}")
    logger.info(f"  模块退役: {stats['modules_retired']}")
    logger.info(f"  当前模块数: {stats['module_count']}")
    logger.info(f"  当前能力集: {len(stats['current_capabilities'])}/{len(engine.required_capabilities)}")
    logger.info(f"  缺失能力: {stats['missing_capabilities']}")

    logger.info("\n[Phase 6] 复杂度变化趋势...")
    logger.info("-" * 80)
    complexity_values = [m['total_complexity'] for m in metrics_history]
    logger.info(f"  初始: {complexity_values[0]:.2f}")
    logger.info(f"  最终: {complexity_values[-1]:.2f}")
    logger.info(f"  最大: {max(complexity_values):.2f} (Step {complexity_values.index(max(complexity_values))})")
    logger.info(f"  最小: {min(complexity_values):.2f} (Step {complexity_values.index(min(complexity_values))})")
    logger.info(f"  变化: {((complexity_values[-1] - complexity_values[0]) / complexity_values[0] * 100):+.1f}%")

    logger.info("\n[Phase 7] 架构腐化验证...")
    logger.info("-" * 80)
    smell_reduction = len(initial_smells) - len(final_smells)
    logger.info(f"  初始异味: {len(initial_smells)}")
    logger.info(f"  最终异味: {len(final_smells)}")
    logger.info(f"  异味变化: {smell_reduction:+d}")

    cycle_reduction = initial_metrics['cycle_count'] - final_metrics['cycle_count']
    logger.info(f"  循环依赖变化: {cycle_reduction:+d}")

    coupling_change = final_metrics['avg_coupling'] - initial_metrics['avg_coupling']
    logger.info(f"  平均耦合变化: {initial_metrics['avg_coupling']:.2f} -> {final_metrics['avg_coupling']:.2f} ({coupling_change:+.2f})")

    logger.info("\n[Phase 8] 演化效果评估...")
    logger.info("-" * 80)

    assessments = []
    if final_metrics['total_complexity'] < initial_metrics['total_complexity']:
        assessments.append("+ 架构复杂度降低")
    else:
        assessments.append("~ 架构复杂度增加（模块增长导致）")

    if len(final_smells) <= len(initial_smells):
        assessments.append("+ 架构异味减少或持平")
    else:
        assessments.append("~ 架构异味增加（需检查阈值）")

    if final_metrics['modularity'] >= initial_metrics['modularity']:
        assessments.append("+ 模块度改善")
    else:
        assessments.append("~ 模块度下降")

    for a in assessments:
        logger.info(f"  {a}")

    return {
        "engine": engine,
        "initial_metrics": initial_metrics,
        "final_metrics": final_metrics,
        "metrics_history": metrics_history,
        "step_results": step_results,
        "stats": stats,
        "initial_smells": initial_smells,
        "final_smells": final_smells
    }


if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    result = run_evolution_experiment()
