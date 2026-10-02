"""
OMNI-HUB v191 — CausalInferenceEngine
因果推理引擎

核心功能：
1. CausalGraphBuilder    — 因果图构建器
2. InterventionAnalyzer   — 干预分析器
3. CounterfactualEngine   — 反事实引擎
4. DoCalculus            — do-演算
5. CausalDiscovery       — 因果发现
6. CausalInferenceEngine  — 统合引擎

映射：
- 因果 = hetu-phala（因果）
- 干预 = prasaṅga（干预）
- 反事实 = viparīta（反面）
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

class CausalRelation(Enum):
    """因果关系类型"""
    DIRECT = 0          # 直接因果
    INDIRECT = 1        # 间接因果
    CONFOUNDED = 2      # 混杂
    COLLIDER = 3        # 对撞
    SPURIOUS = 4        # 虚假


class InterventionType(Enum):
    """干预类型"""
    DO = 0              # do(X=x)
    CONDITION = 1       # P(Y|X=x)
    SOFT = 2            # 软干预


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class CausalNode:
    """因果节点"""
    node_id: str
    name: str = ""
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    observed: bool = True


@dataclass
class CausalEdge:
    """因果边"""
    edge_id: str
    source: str
    target: str
    strength: float
    relation_type: CausalRelation


@dataclass
class Intervention:
    """干预"""
    intervention_id: str
    target: str
    value: Any
    int_type: InterventionType
    timestamp: float


@dataclass
class Counterfactual:
    """反事实"""
    cf_id: str
    factual: Dict[str, Any]
    counterfactual: Dict[str, Any]
    outcome_variable: str
    factual_outcome: Any
    cf_outcome: Any
    effect: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 因果图构建器
# ═══════════════════════════════════════════════════════════════

class CausalGraphBuilder:
    """因果图构建器 — 构建有向无环图(DAG)"""

    def __init__(self):
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: Dict[str, CausalEdge] = {}
        self.edge_counter = 0

    def add_node(self, node_id: str, name: str = ""):
        if node_id not in self.nodes:
            self.nodes[node_id] = CausalNode(
                node_id=node_id,
                name=name or node_id
            )

    def add_edge(self, source: str, target: str, strength: float = 1.0,
                 relation: CausalRelation = CausalRelation.DIRECT) -> Optional[CausalEdge]:
        """添加因果边，检测环"""
        if source == target:
            return None
        if self._would_create_cycle(source, target):
            return None

        self.add_node(source)
        self.add_node(target)

        self.edge_counter += 1
        eid = f"edge_{self.edge_counter}_{int(time.time()*1000)}"
        edge = CausalEdge(
            edge_id=eid,
            source=source,
            target=target,
            strength=strength,
            relation_type=relation
        )
        self.edges[eid] = edge
        self.nodes[source].children.append(target)
        self.nodes[target].parents.append(source)
        return edge

    def _would_create_cycle(self, source: str, target: str) -> bool:
        """检测是否会形成环"""
        visited = set()
        stack = [target]
        while stack:
            current = stack.pop()
            if current == source:
                return True
            if current in visited:
                continue
            visited.add(current)
            if current in self.nodes:
                stack.extend(self.nodes[current].children)
        return False

    def get_parents(self, node_id: str) -> List[str]:
        return self.nodes.get(node_id, CausalNode("")).parents

    def get_children(self, node_id: str) -> List[str]:
        return self.nodes.get(node_id, CausalNode("")).children

    def get_ancestors(self, node_id: str) -> Set[str]:
        """获取所有祖先"""
        ancestors = set()
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            for parent in self.get_parents(current):
                if parent not in ancestors:
                    ancestors.add(parent)
                    queue.append(parent)
        return ancestors

    def get_descendants(self, node_id: str) -> Set[str]:
        """获取所有后代"""
        descendants = set()
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            for child in self.get_children(current):
                if child not in descendants:
                    descendants.add(child)
                    queue.append(child)
        return descendants

    def get_report(self) -> Dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "avg_strength": sum(e.strength for e in self.edges.values()) / max(1, len(self.edges)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 干预分析器
# ═══════════════════════════════════════════════════════════════

class InterventionAnalyzer:
    """干预分析器 — prasaṅga"""

    def __init__(self, graph: CausalGraphBuilder):
        self.graph = graph
        self.interventions: deque = deque(maxlen=200)

    def do_intervention(self, target: str, value: float) -> Dict:
        """执行 do(X=x) 干预"""
        # do(X=x) = 移除X的所有入边，设置X=value
        intv = Intervention(
            intervention_id=f"do_{target}_{int(time.time()*1000)}",
            target=target,
            value=value,
            int_type=InterventionType.DO,
            timestamp=time.time()
        )
        self.interventions.append(intv)

        # 计算对后代的影响
        descendants = self.graph.get_descendants(target)
        effects = {}
        for desc in descendants:
            # 简化：影响 = 路径强度 × 干预值
            effect = self._compute_path_effect(target, desc) * value
            effects[desc] = effect

        return {
            "intervention": intv,
            "affected_nodes": list(descendants),
            "effects": effects,
        }

    def _compute_path_effect(self, source: str, target: str) -> float:
        """计算从source到target的所有路径的效应"""
        # BFS找所有路径，累加效应
        total_effect = 0.0
        queue = [(source, 1.0)]
        visited = set()

        while queue:
            current, strength = queue.pop(0)
            if current == target and current != source:
                total_effect += strength
                continue
            if current in visited:
                continue
            visited.add(current)

            for child in self.graph.get_children(current):
                edge = next((e for e in self.graph.edges.values()
                            if e.source == current and e.target == child), None)
                if edge:
                    queue.append((child, strength * edge.strength))

        return min(1.0, total_effect)

    def compare_interventions(self, intv_a: Intervention, intv_b: Intervention) -> Dict:
        """比较两种干预的效果"""
        return {
            "intervention_a": intv_a.target,
            "intervention_b": intv_b.target,
            "same_target": intv_a.target == intv_b.target,
            "value_diff": abs(float(intv_a.value) - float(intv_b.value)),
        }

    def get_report(self) -> Dict:
        return {
            "interventions": len(self.interventions),
            "unique_targets": len(set(i.target for i in self.interventions)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 反事实引擎
# ═══════════════════════════════════════════════════════════════

class CounterfactualEngine:
    """反事实引擎 — viparīta"""

    def __init__(self, graph: CausalGraphBuilder):
        self.graph = graph
        self.counterfactuals: deque = deque(maxlen=200)

    def compute(self, outcome_var: str, intervention_var: str,
                intervention_value: Any, factual_state: Dict[str, Any]) -> Counterfactual:
        """计算反事实：如果X=x'，Y会如何？"""
        # 事实结果
        factual_outcome = factual_state.get(outcome_var, 0.0)

        # 反事实状态：保持外生变量不变，改变干预变量
        cf_state = dict(factual_state)
        cf_state[intervention_var] = intervention_value

        # 简化：反事实结果 = 事实结果 + 干预效应
        # 实际应通过结构方程模型计算
        effect = self._estimate_effect(intervention_var, outcome_var, intervention_value, factual_state)
        cf_outcome = float(factual_outcome) + effect

        cf = Counterfactual(
            cf_id=f"cf_{int(time.time()*1000)}",
            factual=factual_state,
            counterfactual=cf_state,
            outcome_variable=outcome_var,
            factual_outcome=factual_outcome,
            cf_outcome=cf_outcome,
            effect=effect
        )
        self.counterfactuals.append(cf)
        return cf

    def _estimate_effect(self, iv: str, ov: str, iv_val: Any, state: Dict) -> float:
        """估计干预效应（简化版）"""
        # 如果有直接边，使用边强度
        direct_edge = next((e for e in self.graph.edges.values()
                           if e.source == iv and e.target == ov), None)
        if direct_edge:
            old_val = float(state.get(iv, 0))
            diff = float(iv_val) - old_val
            return diff * direct_edge.strength

        # 间接效应：找所有路径
        return self.graph.nodes.get(iv, CausalNode("")).children.count(ov) * 0.1

    def get_report(self) -> Dict:
        if not self.counterfactuals:
            return {"counterfactuals": 0}
        effects = [cf.effect for cf in self.counterfactuals]
        return {
            "counterfactuals": len(self.counterfactuals),
            "avg_effect": sum(abs(e) for e in effects) / len(effects),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: do-演算
# ═══════════════════════════════════════════════════════════════

class DoCalculus:
    """do-演算 — Pearl's do-calculus"""

    def __init__(self, graph: CausalGraphBuilder):
        self.graph = graph

    def rule1(self, y: str, z: str, x: str) -> bool:
        """规则1: P(y | do(x), z, w) = P(y | do(x), w) 如果 Y⊥Z | X,W in G_{do(X)}"""
        # 简化：如果Z不是Y的后代，则适用
        return z not in self.graph.get_descendants(y)

    def rule2(self, y: str, z: str, x: str) -> bool:
        """规则2: P(y | do(x), do(z), w) = P(y | do(x), z, w) 如果 Y⊥Z | X,W in G_{do(X),Z}"""
        # 简化检查
        return True

    def rule3(self, y: str, z: str, x: str) -> bool:
        """规则3: P(y | do(x), do(z), w) = P(y | do(x), w) 如果 Y⊥Z | X,W in G_{do(X),Z}"""
        return z not in self.graph.get_ancestors(y)

    def identify(self, y: str, x: str) -> Tuple[bool, str]:
        """识别 P(y | do(x)) 是否可识别"""
        # 简化：如果有从X到Y的有向路径，则可识别
        descendants = self.graph.get_descendants(x)
        if y in descendants:
            return True, f"Identifiable: {x} → ... → {y}"

        # 检查是否有后门路径
        backdoor_paths = self._find_backdoor_paths(x, y)
        if not backdoor_paths:
            return True, "Identifiable: no backdoor paths"

        return False, f"Not identifiable: backdoor paths exist: {backdoor_paths}"

    def _find_backdoor_paths(self, x: str, y: str) -> List[List[str]]:
        """查找从X到Y的后门路径（经过X的祖先）"""
        paths = []
        x_ancestors = self.graph.get_ancestors(x)
        for ancestor in x_ancestors:
            # 检查 ancestor → ... → y 的路径
            if y in self.graph.get_descendants(ancestor):
                paths.append([ancestor, x, y])
        return paths

    def get_report(self) -> Dict:
        return {"rules_available": 3}


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 因果发现
# ═══════════════════════════════════════════════════════════════

class CausalDiscovery:
    """因果发现 — 从数据中发现因果结构"""

    def __init__(self):
        self.discovered: deque = deque(maxlen=100)

    def discover_from_correlation(self, correlations: Dict[Tuple[str, str], float],
                                   threshold: float = 0.5) -> List[CausalEdge]:
        """从相关性中发现候选因果边（简化PC算法）"""
        edges = []
        for (a, b), corr in correlations.items():
            if abs(corr) >= threshold:
                # 方向启发：假设A导致B（需要外部知识）
                eid = f"disc_{a}_{b}_{int(time.time()*1000)}"
                edge = CausalEdge(
                    edge_id=eid,
                    source=a,
                    target=b,
                    strength=abs(corr),
                    relation_type=CausalRelation.DIRECT if abs(corr) > 0.8 else CausalRelation.CONFOUNDED
                )
                edges.append(edge)
                self.discovered.append(edge)
        return edges

    def discover_from_temporal(self, temporal_order: List[str]) -> List[CausalEdge]:
        """从时间顺序发现因果（先发生→后发生）"""
        edges = []
        for i in range(len(temporal_order) - 1):
            eid = f"temp_{temporal_order[i]}_{temporal_order[i+1]}_{int(time.time()*1000)}"
            edge = CausalEdge(
                edge_id=eid,
                source=temporal_order[i],
                target=temporal_order[i+1],
                strength=0.7,
                relation_type=CausalRelation.DIRECT
            )
            edges.append(edge)
            self.discovered.append(edge)
        return edges

    def get_report(self) -> Dict:
        return {"discovered_edges": len(self.discovered)}


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — CausalInferenceEngine v191
# ═══════════════════════════════════════════════════════════════

class CausalInferenceEngine:
    """
    OMNI-HUB v191 因果推理引擎

    hetu-phala · prasaṅga · viparīta — 因果、干预、反面
    """

    VERSION = "191.0.0"

    def __init__(self):
        self.graph = CausalGraphBuilder()
        self.intervention = InterventionAnalyzer(self.graph)
        self.counterfactual = CounterfactualEngine(self.graph)
        self.do_calculus = DoCalculus(self.graph)
        self.discovery = CausalDiscovery()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def build_alliance_graph(self, alliance_state: Dict[str, Dict]):
        """从联盟状态构建因果图"""
        lines = list(alliance_state.keys())
        for line in lines:
            self.graph.add_node(line)

        # 基于相关性添加边
        for i, a in enumerate(lines):
            for b in lines[i+1:]:
                ha = alliance_state[a].get("health", 0.5)
                hb = alliance_state[b].get("health", 0.5)
                corr = 1.0 - abs(ha - hb)  # 简化相关性
                if corr > 0.7:
                    self.graph.add_edge(a, b, strength=corr)

    def analyze_intervention(self, target_line: str, health_level: float) -> Dict:
        """分析对某线的干预效果"""
        result = self.intervention.do_intervention(target_line, health_level)
        return {
            "target": target_line,
            "intervention_value": health_level,
            "affected_lines": result["affected_nodes"],
            "predicted_effects": result["effects"],
        }

    def what_if(self, target_line: str, outcome_line: str,
                hypothetical_health: float, current_state: Dict[str, Dict]) -> Dict:
        """反事实推理：如果target_line的健康度是X，outcome_line会如何？"""
        factual = {line: s.get("health", 0.5) for line, s in current_state.items()}
        cf = self.counterfactual.compute(outcome_line, target_line, hypothetical_health, factual)
        return {
            "factual": cf.factual_outcome,
            "counterfactual": cf.cf_outcome,
            "effect": cf.effect,
            "intervention": f"{target_line}={hypothetical_health}",
        }

    def identify_causal_effect(self, cause: str, effect: str) -> Dict:
        """识别因果效应是否可估计"""
        identifiable, reason = self.do_calculus.identify(effect, cause)
        return {
            "cause": cause,
            "effect": effect,
            "identifiable": identifiable,
            "reason": reason,
        }

    def run_cycle(self, alliance_state: Dict[str, Dict] = None) -> Dict:
        """运行完整因果分析周期"""
        self.cycle_count += 1
        alliance_state = alliance_state or {}

        # 1. 构建因果图
        self.build_alliance_graph(alliance_state)

        # 2. 对每条线做干预分析
        interventions = []
        for line in list(alliance_state.keys())[:3]:  # 限制规模
            r = self.analyze_intervention(line, 0.9)
            interventions.append(r)

        # 3. 反事实分析（第一条线对最后一条线）
        what_if_result = None
        lines = list(alliance_state.keys())
        if len(lines) >= 2:
            what_if_result = self.what_if(lines[0], lines[-1], 0.95, alliance_state)

        summary = {
            "cycle": self.cycle_count,
            "nodes_in_graph": len(self.graph.nodes),
            "edges_in_graph": len(self.graph.edges),
            "interventions_analyzed": len(interventions),
            "what_if": what_if_result,
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "graph": self.graph.get_report(),
            "intervention": self.intervention.get_report(),
            "counterfactual": self.counterfactual.get_report(),
            "do_calculus": self.do_calculus.get_report(),
            "discovery": self.discovery.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_cie_instance: Optional[CausalInferenceEngine] = None


def get_causal_inference_engine() -> CausalInferenceEngine:
    global _cie_instance
    if _cie_instance is None:
        _cie_instance = CausalInferenceEngine()
    return _cie_instance


if __name__ == "__main__":
    cie = CausalInferenceEngine()
    print(f"CausalInferenceEngine v{cie.VERSION} initialized")
    print(f"Status: {json.dumps(cie.get_status(), indent=2, default=str)}")
