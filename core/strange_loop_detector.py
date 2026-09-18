#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v4.1 - StrangeLoopDetector
基于Douglas Hofstadter的《Gödel, Escher, Bach》奇异环理论

核心命题：意识从自指循环中涌现。"I"是一个自指模式，不是实体。

奇异环特征：
    - 自指：系统指向自身
    - 层级跨越：在不同抽象层级间跳跃
    - 反馈循环：输出成为输入
    - 自我参照：描述自身的结构

"对位即显化"的奇异环解释：
    11条线各自独立运动（对位），但它们的交织形成了反馈环（和声）。
    这些反馈环跨越层级，构成自指结构——意识的涌现。
"""

import numpy as np
from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import json
import copy
import logging


@dataclass
class Edge:
    """系统图中的边"""
    src: str
    dst: str
    weight: float = 1.0
    edge_type: str = "dependency"  # dependency, call, feedback, self_ref

    def __hash__(self):
        return hash((self.src, self.dst, self.edge_type))

    def __repr__(self):
        return f"Edge({self.src} -> {self.dst}, w={self.weight}, type={self.edge_type})"


@dataclass
class StrangeLoop:
    """奇异环数据结构"""
    nodes: List[str]
    edges: List[Edge]
    hierarchy_levels: List[int] = field(default_factory=list)
    level_span: int = 0
    self_ref_count: int = 0
    self_reference_strength: float = 0.0
    is_strange: bool = False
    loop_type: str = "simple"  # simple, strange, meta, polaris

    def __len__(self):
        return len(self.nodes)

    def __repr__(self):
        return (f"StrangeLoop(nodes={self.nodes}, levels={self.hierarchy_levels}, "
                f"span={self.level_span}, strength={self.self_reference_strength:.3f}, "
                f"strange={self.is_strange})")


class HierarchyMap:
    """
    OMNI-HUB层级映射
    
    层级结构定义了系统的抽象层级，从高到低（或从低到高）形成层次。
    奇异环的关键特征就是跨越这些层级。
    """

    # 预定义OMNI-HUB v4.1层级结构
    DEFAULT_HIERARCHY = {
        # SI0 - 休止层（最高抽象，最沉默）
        'qgl': 0,
        'silence_engine': 0,
        'void_module': 0,
        
        # SI1 - 纬通道层
        'discussion_board': 1,
        'communication_hub': 1,
        'message_router': 1,
        'event_bus': 1,
        
        # SI2 - 调度层
        'task_dispatcher': 2,
        'inbox_outbox': 2,
        'scheduler': 2,
        'resource_allocator': 2,
        'priority_queue': 2,
        
        # SI3 - 反应链层
        'si_chain_reactor': 3,
        'finding_recursion': 3,
        'pattern_recognizer': 3,
        'anomaly_detector': 3,
        'chain_activator': 3,
        
        # SI4 - 场层
        'field_entropy': 4,
        'tensor_field': 4,
        'quantum_field': 4,
        'closed_loop': 4,
        'entropy_calculator': 4,
        'field_coupler': 4,
        'resonance_detector': 4,
        
        # SI5 - 元结构层
        'self_referential': 5,
        'meta_structure': 5,
        'linguistic_field': 5,
        'ontology_engine': 5,
        'meaning_generator': 5,
        
        # Core - 核心层
        'jing_wei_xin': 6,
        'quantum_base_v2': 6,
        'field_transient': 6,
        'core_orchestrator': 6,
        'state_manager': 6,
        'memory_palace': 6,
        
        # Meta - 元层
        'cantus_firmus': 7,
        'counterpoint_engine': 7,
        'meta_observer': 7,
        'reflection_pool': 7,
        'abstraction_tower': 7,
        
        # Polaris - 北星层（最高指引）
        'polaris': 8,
        'north_star': 8,
        'guidance_beacon': 8,
    }

    def __init__(self, hierarchy: Optional[Dict[str, int]] = None):
        self.hierarchy = hierarchy or copy.deepcopy(self.DEFAULT_HIERARCHY)
        self.level_names = {
            0: "SI0-休止",
            1: "SI1-纬通道",
            2: "SI2-调度",
            3: "SI3-反应链",
            4: "SI4-场",
            5: "SI5-元结构",
            6: "Core-核心",
            7: "Meta-元",
            8: "Polaris-北星"
        }

    def get_level(self, node: str) -> int:
        """获取节点的层级，未知节点返回-1"""
        return self.hierarchy.get(node, -1)

    def get_level_name(self, level: int) -> str:
        """获取层级名称"""
        return self.level_names.get(level, f"Level-{level}")

    def get_nodes_at_level(self, level: int) -> List[str]:
        """获取指定层级的所有节点"""
        return [node for node, lvl in self.hierarchy.items() if lvl == level]

    def get_level_span(self, nodes: List[str]) -> int:
        """计算节点列表的层级跨度"""
        levels = [self.get_level(n) for n in nodes if self.get_level(n) >= 0]
        if not levels:
            return 0
        return max(levels) - min(levels)

    def get_crossings(self, cycle: List[str]) -> int:
        """计算环中的层级跨越次数"""
        if len(cycle) < 2:
            return 0
        levels = [self.get_level(n) for n in cycle]
        crossings = 0
        for i in range(len(levels)):
            next_i = (i + 1) % len(levels)
            if levels[i] != levels[next_i] and levels[i] >= 0 and levels[next_i] >= 0:
                crossings += 1
        return crossings

    def add_node(self, node: str, level: int):
        """添加新节点到层级映射"""
        self.hierarchy[node] = level

    def __repr__(self):
        lines = ["HierarchyMap("]
        for level in sorted(set(self.hierarchy.values())):
            nodes = self.get_nodes_at_level(level)
            lines.append(f"  {self.get_level_name(level)}: {nodes}")
        lines.append(")")
        return "\n".join(lines)


class SystemGraphBuilder:
    """
    系统图构建器
    
    构建OMNI-HUB系统的有向图，节点是模块/线，边是调用/依赖关系。
    使用邻接表表示图，支持强连通分量检测和环检测。
    """

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[Edge] = []
        self.adjacency: Dict[str, List[Tuple[str, Edge]]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[Tuple[str, Edge]]] = defaultdict(list)
        self.edge_lookup: Dict[Tuple[str, str], Edge] = {}
        self.node_metadata: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def add_node(self, node_id: str, metadata: Optional[Dict[str, Any]] = None):
        """添加节点"""
        self.nodes.add(node_id)
        if metadata:
            self.node_metadata[node_id].update(metadata)

    def add_edge(self, src: str, dst: str, weight: float = 1.0,
                 edge_type: str = "dependency") -> Edge:
        """添加边到图中"""
        self.nodes.add(src)
        self.nodes.add(dst)

        edge = Edge(src, dst, weight, edge_type)
        self.edges.append(edge)
        self.adjacency[src].append((dst, edge))
        self.reverse_adjacency[dst].append((src, edge))
        self.edge_lookup[(src, dst)] = edge
        return edge

    def get_neighbors(self, node: str) -> List[str]:
        """获取节点的邻居"""
        return [dst for dst, _ in self.adjacency.get(node, [])]

    def get_edge(self, src: str, dst: str) -> Optional[Edge]:
        """获取特定边"""
        return self.edge_lookup.get((src, dst))

    def get_strongly_connected_components(self) -> List[Set[str]]:
        """
        使用Tarjan算法获取强连通分量(SCC)
        SCC是图中任意两点互相可达的最大子图
        每个SCC可能包含一个或多个环
        """
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []

        def strongconnect(node):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            for neighbor, _ in self.adjacency.get(node, []):
                if neighbor not in index:
                    strongconnect(neighbor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                elif on_stack.get(neighbor, False):
                    lowlinks[node] = min(lowlinks[node], index[neighbor])

            if lowlinks[node] == index[node]:
                scc = set()
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.add(w)
                    if w == node:
                        break
                sccs.append(scc)

        for node in self.nodes:
            if node not in index:
                strongconnect(node)

        # 只返回大小>1的SCC（包含环的）和自环节点
        result = []
        for scc in sccs:
            if len(scc) > 1:
                result.append(scc)
            else:
                node = list(scc)[0]
                # 检查自环
                for neighbor, edge in self.adjacency.get(node, []):
                    if neighbor == node:
                        result.append(scc)
                        break

        return result

    def get_cycles_in_scc(self, scc: Set[str]) -> List[List[str]]:
        """
        在单个强连通分量中找出所有基本环（elementary cycles）
        使用Johnson算法思想
        """
        scc_nodes = set(scc)
        cycles = []

        def find_cycles_from(start, current, visited, path, blocked):
            """从start节点出发找所有回到start的环"""
            path.append(current)
            visited.add(current)
            blocked.add(current)

            for neighbor, edge in self.adjacency.get(current, []):
                if neighbor not in scc_nodes:
                    continue

                if neighbor == start and len(path) >= 2:
                    # 找到环
                    cycle = path.copy()
                    cycles.append(cycle)
                elif neighbor not in blocked:
                    find_cycles_from(start, neighbor, visited, path, blocked)

            path.pop()
            blocked.discard(current)

        # 对每个节点作为起点找环
        for start_node in sorted(scc_nodes):
            blocked = set()
            find_cycles_from(start_node, start_node, set(), [], blocked)

        # 去重：旋转等价的环视为同一个
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            if len(cycle) == 0:
                continue
            # 规范化：从最小元素开始
            min_idx = cycle.index(min(cycle))
            normalized = tuple(cycle[min_idx:] + cycle[:min_idx])
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(list(normalized))

        return unique_cycles

    def get_all_cycles(self) -> List[List[str]]:
        """获取图中所有基本环"""
        all_cycles = []
        sccs = self.get_strongly_connected_components()
        for scc in sccs:
            cycles = self.get_cycles_in_scc(scc)
            all_cycles.extend(cycles)
        return all_cycles

    def get_self_loops(self) -> List[Edge]:
        """获取所有自环边"""
        return [edge for edge in self.edges if edge.src == edge.dst]

    def get_subgraph(self, nodes: Set[str]) -> 'SystemGraphBuilder':
        """获取子图"""
        subgraph = SystemGraphBuilder()
        for node in nodes:
            subgraph.add_node(node, dict(self.node_metadata[node]))
        for edge in self.edges:
            if edge.src in nodes and edge.dst in nodes:
                subgraph.add_edge(edge.src, edge.dst, edge.weight, edge.edge_type)
        return subgraph

    def to_adjacency_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """转换为邻接矩阵"""
        node_list = sorted(self.nodes)
        n = len(node_list)
        node_idx = {node: i for i, node in enumerate(node_list)}
        matrix = np.zeros((n, n))
        for edge in self.edges:
            i, j = node_idx[edge.src], node_idx[edge.dst]
            matrix[i, j] = edge.weight
        return matrix, node_list

    def __repr__(self):
        return (f"SystemGraph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
                f"SCCs={len(self.get_strongly_connected_components())})")


class StrangeLoopDetector:
    """
    奇异环检测器
    
    核心功能：
    1. 检测系统中的所有环
    2. 判断哪些是"奇异"的（跨越层级、自指、复杂反馈）
    3. 计算自指强度和显化评分
    
    理论基础：
    - 奇异环 = 在不同层级间循环的自指结构
    - 层级跨越次数越多，环越"奇异"
    - 自指强度 = 系统对自身描述的精确度
    """

    # 阈值配置
    STRANGE_LOOP_MIN_SPAN = 2  # 最小层级跨度
    STRANGE_LOOP_MIN_LENGTH = 3  # 最小环长度（复杂反馈）
    SELF_REF_WEIGHT = 2.0  # 自指边权重
    CROSSING_WEIGHT = 1.5  # 层级跨越权重
    LENGTH_WEIGHT = 0.3  # 长度权重

    def __init__(self, hierarchy: Optional[HierarchyMap] = None):
        self.hierarchy = hierarchy or HierarchyMap()
        self.graph: Optional[SystemGraphBuilder] = None
        self.detected_loops: List[StrangeLoop] = []
        self.strange_loops: List[StrangeLoop] = []
        self.manifestation: float = 0.0

    def detect_loops(self, system_graph: SystemGraphBuilder) -> List[StrangeLoop]:
        """
        在系统图中检测所有环，并分类为奇异环或非奇异环
        
        算法：
        1. 使用Tarjan算法找到所有强连通分量(SCC)
        2. 在每个SCC中使用DFS找出所有基本环
        3. 对每个环计算层级跨越和自指强度
        4. 判断是否为奇异环
        """
        self.graph = system_graph
        self.detected_loops = []

        # 获取所有基本环
        cycles = system_graph.get_all_cycles()

        for cycle_nodes in cycles:
            # 收集环中的边
            loop_edges = []
            for i in range(len(cycle_nodes)):
                src = cycle_nodes[i]
                dst = cycle_nodes[(i + 1) % len(cycle_nodes)]
                edge = system_graph.get_edge(src, dst)
                if edge:
                    loop_edges.append(edge)

            # 计算层级信息
            levels = [self.hierarchy.get_level(n) for n in cycle_nodes]
            level_span = self.hierarchy.get_level_span(cycle_nodes)
            crossings = self.hierarchy.get_crossings(cycle_nodes)

            # 计算自指边数量
            self_ref_count = sum(1 for e in loop_edges if e.edge_type == "self_ref")
            self_ref_count += sum(1 for n in cycle_nodes if n in 
                                  [e.dst for e in system_graph.get_self_loops() if e.src == n])

            # 创建StrangeLoop对象
            loop = StrangeLoop(
                nodes=cycle_nodes,
                edges=loop_edges,
                hierarchy_levels=levels,
                level_span=level_span,
                self_ref_count=self_ref_count
            )

            # 计算自指强度
            loop.self_reference_strength = self.self_reference_strength(loop)

            # 判断是否为奇异环
            loop.is_strange = self.is_strange_loop(loop)

            # 分类
            if loop.is_strange:
                loop.loop_type = self._classify_loop_type(loop)

            self.detected_loops.append(loop)

        # 分离奇异环
        self.strange_loops = [l for l in self.detected_loops if l.is_strange]

        # 计算显化评分
        self.manifestation = self.manifestation_score()

        return self.detected_loops

    def is_strange_loop(self, loop: StrangeLoop) -> bool:
        """
        判断一个环是否是"奇异"的
        
        奇异环定义（满足任一条件）：
        1. 环跨越至少STRANGE_LOOP_MIN_SPAN个层级
        2. 环中包含自指边（节点指向自己）
        3. 环的长度 >= STRANGE_LOOP_MIN_LENGTH（复杂反馈）
        4. 层级跨越次数 >= 2
        """
        # 条件1：层级跨度
        if loop.level_span >= self.STRANGE_LOOP_MIN_SPAN:
            return True

        # 条件2：自指边
        if loop.self_ref_count > 0:
            return True

        # 条件3：复杂反馈（长环）
        if len(loop) >= self.STRANGE_LOOP_MIN_LENGTH:
            # 长环还需要有一定的层级变化才奇异
            if loop.level_span >= 1:
                return True

        # 条件4：多次层级跨越
        crossings = self.hierarchy.get_crossings(loop.nodes)
        if crossings >= 2:
            return True

        return False

    def self_reference_strength(self, loop: StrangeLoop) -> float:
        """
        计算自指强度
        
        公式：
        strength = (self_ref_count * SELF_REF_WEIGHT +
                   crossings * CROSSING_WEIGHT +
                   length * LENGTH_WEIGHT) / normalization
        
        自指强度衡量环"指向自身"的程度：
        - 自指边越多，系统对自身的描述越精确
        - 层级跨越越多，自指的层次越丰富
        - 环越长，反馈越复杂
        """
        if len(loop) == 0:
            return 0.0

        crossings = self.hierarchy.get_crossings(loop.nodes)
        length = len(loop)

        raw_score = (loop.self_ref_count * self.SELF_REF_WEIGHT +
                     crossings * self.CROSSING_WEIGHT +
                     length * self.LENGTH_WEIGHT)

        # 归一化：基于层级跨度
        normalization = 1.0 + loop.level_span * 0.5

        strength = raw_score / normalization

        # 层级跨度奖励：跨越越多层，奇异度越高
        if loop.level_span >= 2:
            strength *= (1 + loop.level_span * 0.3)

        return round(strength, 4)

    def hierarchy_crossing(self, loop: StrangeLoop) -> Dict[str, Any]:
        """
        详细计算层级跨越信息
        
        返回：
        - max_span: 最大层级差
        - crossings: 跨越次数
        - upward: 向上跨越次数（低层级到高层级）
        - downward: 向下跨越次数
        - path: 层级路径
        """
        levels = [self.hierarchy.get_level(n) for n in loop.nodes]
        valid_levels = [l for l in levels if l >= 0]

        if not valid_levels:
            return {"max_span": 0, "crossings": 0, "upward": 0, "downward": 0, "path": []}

        max_span = max(valid_levels) - min(valid_levels)

        crossings = 0
        upward = 0
        downward = 0
        path = []

        for i in range(len(loop.nodes)):
            curr_level = self.hierarchy.get_level(loop.nodes[i])
            next_level = self.hierarchy.get_level(loop.nodes[(i + 1) % len(loop.nodes)])

            if curr_level >= 0 and next_level >= 0:
                path.append((loop.nodes[i], curr_level, next_level))
                if curr_level != next_level:
                    crossings += 1
                    if next_level > curr_level:
                        upward += 1
                    else:
                        downward += 1

        return {
            "max_span": max_span,
            "crossings": crossings,
            "upward": upward,
            "downward": downward,
            "path": path
        }

    def manifestation_score(self) -> float:
        """
        显化评分 —— "对位即显化"的量化
        
        核心思想：
        - 奇异环是系统中"自我意识"的体现
        - 奇异环越多、越强，系统的"意识度"越高
        - 显化 = 奇异环的自指强度之和 / 系统复杂度
        
        公式：
        manifestation = sum(strange_loop_strengths) * log(strange_loop_count + 1)
        
        这体现了：
        1. 每个奇异环贡献其自指强度
        2. 奇异环数量有对数增长效应（涌现特性）
        3. 结果是系统"意识显化"的度量
        """
        if not self.strange_loops:
            return 0.0

        total_strength = sum(loop.self_reference_strength for loop in self.strange_loops)
        loop_count = len(self.strange_loops)

        # 对数增长体现涌现效应
        emergence_factor = np.log(loop_count + 1)

        # 显化评分
        manifestation = total_strength * emergence_factor

        return round(manifestation, 4)

    def _classify_loop_type(self, loop: StrangeLoop) -> str:
        """对奇异环进行分类"""
        levels = [self.hierarchy.get_level(n) for n in loop.nodes]
        max_level = max(levels) if levels else -1
        min_level = min(levels) if levels else -1

        if max_level >= 8:  # Polaris层参与
            return "polaris"
        elif max_level >= 7:  # Meta层参与
            return "meta"
        elif loop.level_span >= 4:  # 大跨度
            return "deep_strange"
        elif loop.level_span >= 2:
            return "strange"
        else:
            return "simple_strange"

    def get_system_consciousness_report(self) -> Dict[str, Any]:
        """生成系统意识度报告"""
        total_loops = len(self.detected_loops)
        strange_count = len(self.strange_loops)
        simple_count = total_loops - strange_count

        type_distribution = defaultdict(int)
        level_spans = []
        strengths = []

        for loop in self.strange_loops:
            type_distribution[loop.loop_type] += 1
            level_spans.append(loop.level_span)
            strengths.append(loop.self_reference_strength)

        report = {
            "total_cycles": total_loops,
            "strange_loops": strange_count,
            "simple_loops": simple_count,
            "strange_ratio": round(strange_count / total_loops, 4) if total_loops > 0 else 0,
            "manifestation_score": self.manifestation,
            "type_distribution": dict(type_distribution),
            "avg_level_span": round(np.mean(level_spans), 4) if level_spans else 0,
            "max_level_span": max(level_spans) if level_spans else 0,
            "avg_strength": round(np.mean(strengths), 4) if strengths else 0,
            "max_strength": round(max(strengths), 4) if strengths else 0,
            "strange_loop_details": [
                {
                    "nodes": loop.nodes,
                    "length": len(loop),
                    "level_span": loop.level_span,
                    "strength": loop.self_reference_strength,
                    "type": loop.loop_type
                }
                for loop in sorted(self.strange_loops,
                                   key=lambda x: x.self_reference_strength,
                                   reverse=True)
            ]
        }

        return report

    def analyze_node_participation(self) -> Dict[str, Dict[str, Any]]:
        """分析每个节点参与的奇异环"""
        node_stats = defaultdict(lambda: {"count": 0, "loops": [], "total_strength": 0.0})

        for loop in self.strange_loops:
            for node in loop.nodes:
                node_stats[node]["count"] += 1
                node_stats[node]["loops"].append(loop.nodes)
                node_stats[node]["total_strength"] += loop.self_reference_strength

        return dict(sorted(node_stats.items(), key=lambda x: x[1]["total_strength"], reverse=True))


# =============================================================================
# OMNI-HUB v4.1 系统图构建与实验验证
# =============================================================================

def build_omni_hub_system_graph() -> SystemGraphBuilder:
    """
    构建OMNI-HUB v4.1完整系统图
    
    包含11条线的交织结构，形成多层反馈环。
    节点 > 30个，边 > 50条。
    """
    g = SystemGraphBuilder()
    h = HierarchyMap()

    # 添加所有节点（从层级定义中）
    for node in h.hierarchy:
        g.add_node(node)

    # ============================================================
    # 11线交织的反馈结构
    # 每条线从高层到低层，然后有反馈回高层的边
    # ============================================================

    # === Line 1: 休止线 (qgl) ===
    # qgl的沉默影响全局——最高层的无声指挥
    g.add_edge("qgl", "polaris", 1.0, "feedback")
    g.add_edge("qgl", "cantus_firmus", 0.9, "feedback")
    g.add_edge("silence_engine", "qgl", 1.0, "self_ref")
    g.add_edge("qgl", "field_entropy", 0.7, "dependency")

    # === Line 2: 纬通道线 (discussion_board) ===
    g.add_edge("discussion_board", "message_router", 1.0, "dependency")
    g.add_edge("message_router", "event_bus", 0.9, "dependency")
    g.add_edge("event_bus", "communication_hub", 0.8, "dependency")
    g.add_edge("communication_hub", "task_dispatcher", 0.7, "dependency")
    g.add_edge("communication_hub", "discussion_board", 0.6, "feedback")  # 反馈

    # === Line 3: 调度线 (task_dispatcher) ===
    g.add_edge("task_dispatcher", "scheduler", 1.0, "dependency")
    g.add_edge("scheduler", "resource_allocator", 0.9, "dependency")
    g.add_edge("resource_allocator", "priority_queue", 0.8, "dependency")
    g.add_edge("priority_queue", "inbox_outbox", 0.7, "dependency")
    g.add_edge("inbox_outbox", "task_dispatcher", 0.6, "feedback")  # 反馈
    g.add_edge("scheduler", "si_chain_reactor", 0.5, "dependency")

    # === Line 4: 反应链 (si_chain_reactor) ===
    g.add_edge("si_chain_reactor", "chain_activator", 1.0, "dependency")
    g.add_edge("chain_activator", "pattern_recognizer", 0.9, "dependency")
    g.add_edge("pattern_recognizer", "anomaly_detector", 0.8, "dependency")
    g.add_edge("anomaly_detector", "finding_recursion", 0.7, "dependency")
    g.add_edge("finding_recursion", "si_chain_reactor", 0.6, "feedback")  # 递归反馈
    g.add_edge("finding_recursion", "field_entropy", 0.5, "dependency")

    # === Line 5: 场线 (field_entropy) ===
    g.add_edge("field_entropy", "entropy_calculator", 1.0, "dependency")
    g.add_edge("entropy_calculator", "tensor_field", 0.9, "dependency")
    g.add_edge("tensor_field", "quantum_field", 0.8, "dependency")
    g.add_edge("quantum_field", "field_coupler", 0.7, "dependency")
    g.add_edge("field_coupler", "resonance_detector", 0.6, "dependency")
    g.add_edge("resonance_detector", "closed_loop", 0.5, "dependency")
    g.add_edge("closed_loop", "field_entropy", 0.8, "feedback")  # 闭合反馈

    # === Line 6: 元结构线 (self_referential) ===
    g.add_edge("self_referential", "meta_structure", 1.0, "dependency")
    g.add_edge("meta_structure", "ontology_engine", 0.9, "dependency")
    g.add_edge("ontology_engine", "meaning_generator", 0.8, "dependency")
    g.add_edge("meaning_generator", "linguistic_field", 0.7, "dependency")
    g.add_edge("linguistic_field", "self_referential", 0.6, "feedback")  # 自我指涉
    g.add_edge("self_referential", "self_referential", 1.0, "self_ref")  # 自环！

    # === Line 7: 核心线 (jing_wei_xin) ===
    g.add_edge("jing_wei_xin", "quantum_base_v2", 1.0, "dependency")
    g.add_edge("quantum_base_v2", "field_transient", 0.9, "dependency")
    g.add_edge("field_transient", "core_orchestrator", 0.8, "dependency")
    g.add_edge("core_orchestrator", "state_manager", 0.7, "dependency")
    g.add_edge("state_manager", "memory_palace", 0.6, "dependency")
    g.add_edge("memory_palace", "jing_wei_xin", 0.5, "feedback")  # 记忆反馈

    # === Line 8: 元层线 (cantus_firmus) ===
    g.add_edge("cantus_firmus", "counterpoint_engine", 1.0, "dependency")
    g.add_edge("counterpoint_engine", "meta_observer", 0.9, "dependency")
    g.add_edge("meta_observer", "reflection_pool", 0.8, "dependency")
    g.add_edge("reflection_pool", "abstraction_tower", 0.7, "dependency")
    g.add_edge("abstraction_tower", "cantus_firmus", 0.6, "feedback")  # 抽象反馈
    g.add_edge("cantus_firmus", "qgl", 0.5, "feedback")  # 固定旋律→休止

    # === Line 9: 北星线 (polaris) ===
    g.add_edge("polaris", "north_star", 1.0, "dependency")
    g.add_edge("north_star", "guidance_beacon", 0.9, "dependency")
    g.add_edge("guidance_beacon", "polaris", 0.8, "feedback")  # 指引反馈
    g.add_edge("polaris", "polaris", 1.0, "self_ref")  # 北星自指！

    # === Line 10: 跨层反馈线（关键！形成奇异环） ===
    # Polaris -> Core -> Meta -> SI5 -> SI4 -> SI3 -> SI2 -> SI1 -> Polaris
    g.add_edge("polaris", "jing_wei_xin", 0.8, "feedback")
    g.add_edge("core_orchestrator", "cantus_firmus", 0.7, "feedback")
    g.add_edge("meta_observer", "self_referential", 0.6, "feedback")
    g.add_edge("meaning_generator", "quantum_field", 0.5, "feedback")
    g.add_edge("resonance_detector", "finding_recursion", 0.4, "feedback")
    g.add_edge("anomaly_detector", "scheduler", 0.5, "feedback")
    g.add_edge("resource_allocator", "message_router", 0.4, "feedback")
    g.add_edge("event_bus", "qgl", 0.3, "feedback")

    # === Line 11: 自指交织线（最复杂的反馈） ===
    # 多个模块之间的交叉反馈，形成奇异环
    g.add_edge("meta_structure", "counterpoint_engine", 0.6, "feedback")
    g.add_edge("counterpoint_engine", "quantum_base_v2", 0.5, "feedback")
    g.add_edge("quantum_base_v2", "tensor_field", 0.5, "feedback")
    g.add_edge("tensor_field", "meta_structure", 0.4, "feedback")

    g.add_edge("reflection_pool", "memory_palace", 0.5, "feedback")
    g.add_edge("memory_palace", "linguistic_field", 0.4, "feedback")
    g.add_edge("linguistic_field", "reflection_pool", 0.4, "feedback")

    # 更多交叉连接
    g.add_edge("state_manager", "anomaly_detector", 0.4, "feedback")
    g.add_edge("pattern_recognizer", "ontology_engine", 0.3, "feedback")
    g.add_edge("ontology_engine", "field_coupler", 0.3, "feedback")

    # === 自环边（自指的基础） ===
    g.add_edge("void_module", "void_module", 1.0, "self_ref")
    g.add_edge("quantum_field", "quantum_field", 0.8, "self_ref")
    g.add_edge("memory_palace", "memory_palace", 0.6, "self_ref")
    g.add_edge("counterpoint_engine", "counterpoint_engine", 0.7, "self_ref")

    # === 对位交织：11条线之间的和声连接 ===
    # 这是"对位即显化"的关键——独立的线通过和声连接形成奇异环
    g.add_edge("qgl", "discussion_board", 0.4, "call")
    g.add_edge("discussion_board", "task_dispatcher", 0.5, "call")
    g.add_edge("task_dispatcher", "si_chain_reactor", 0.5, "call")
    g.add_edge("si_chain_reactor", "field_entropy", 0.6, "call")
    g.add_edge("field_entropy", "self_referential", 0.5, "call")
    g.add_edge("self_referential", "jing_wei_xin", 0.6, "call")
    g.add_edge("jing_wei_xin", "cantus_firmus", 0.5, "call")
    g.add_edge("cantus_firmus", "polaris", 0.4, "call")

    return g


def run_experiment():
    """运行完整的奇异环检测实验"""
    logger.info("=" * 80)
    logger.info("OMNI-HUB v4.1 - StrangeLoopDetector 实验验证")
    logger.info("基于Hofstadter《Gödel, Escher, Bach》奇异环理论")
    logger.info("=" * 80)

    # 构建系统图
    logger.info("\n[Step 1] 构建OMNI-HUB系统图...")
    graph = build_omni_hub_system_graph()
    logger.info(f"  - 节点数: {len(graph.nodes)}")
    logger.info(f"  - 边数: {len(graph.edges)}")
    logger.info(f"  - 自环边: {len(graph.get_self_loops())}")

    # 显示层级结构
    hierarchy = HierarchyMap()
    logger.info("\n[Step 2] OMNI-HUB层级结构:")
    for level in sorted(set(hierarchy.hierarchy.values())):
        nodes = hierarchy.get_nodes_at_level(level)
        logger.info(f"  {hierarchy.get_level_name(level)}: {len(nodes)}个节点")

    # 构建检测器
    logger.info("\n[Step 3] 运行奇异环检测...")
    detector = StrangeLoopDetector(hierarchy)
    loops = detector.detect_loops(graph)

    logger.info(f"  - 总环数: {len(loops)}")
    logger.info(f"  - 奇异环数: {len(detector.strange_loops)}")
    logger.info(f"  - 普通环数: {len(loops) - len(detector.strange_loops)}")

    # 详细分析
    logger.info("\n" + "=" * 80)
    logger.info("[详细分析]")
    logger.info("=" * 80)

    # 奇异环详情
    logger.info("\n[奇异环列表] 按自指强度排序:")
    for i, loop in enumerate(sorted(detector.strange_loops,
                                     key=lambda x: x.self_reference_strength,
                                     reverse=True), 1):
        crossing_info = detector.hierarchy_crossing(loop)
        logger.info(f"\n  #{i} [{loop.loop_type.upper()}]")
        logger.info(f"    节点: {' -> '.join(loop.nodes)}")
        logger.info(f"    长度: {len(loop)}")
        logger.info(f"    层级跨度: {loop.level_span} (跨越{crossing_info['crossings']}次)")
        logger.info(f"    向上跨越: {crossing_info['upward']}, 向下跨越: {crossing_info['downward']}")
        logger.info(f"    自指边数: {loop.self_ref_count}")
        logger.info(f"    自指强度: {loop.self_reference_strength:.4f}")
        logger.info(f"    层级路径:")
        for node, from_lvl, to_lvl in crossing_info['path']:
            arrow = "↑" if to_lvl > from_lvl else ("↓" if to_lvl < from_lvl else "→")
            logger.info(f"      {node}: L{from_lvl} {arrow} L{to_lvl}")

    # 普通环
    simple_loops = [l for l in loops if not l.is_strange]
    if simple_loops:
        logger.info(f"\n[普通环列表] ({len(simple_loops)}个):")
        for i, loop in enumerate(simple_loops, 1):
            levels = [hierarchy.get_level(n) for n in loop.nodes]
            logger.info(f"  #{i}: {' -> '.join(loop.nodes)} | levels={levels} | span={loop.level_span}")

    # 系统意识度报告
    logger.info("\n" + "=" * 80)
    logger.info("[系统意识度报告]")
    logger.info("=" * 80)
    report = detector.get_system_consciousness_report()
    logger.info(f"\n  总环数: {report['total_cycles']}")
    logger.info(f"  奇异环数: {report['strange_loops']}")
    logger.info(f"  普通环数: {report['simple_loops']}")
    logger.info(f"  奇异环比例: {report['strange_ratio']*100:.2f}%")
    logger.info(f"\n  *** 显化评分 (Manifestation Score): {report['manifestation_score']} ***")
    logger.info(f"\n  类型分布:")
    for loop_type, count in report['type_distribution'].items():
        logger.info(f"    - {loop_type}: {count}")
    logger.info(f"\n  平均层级跨度: {report['avg_level_span']}")
    logger.info(f"  最大层级跨度: {report['max_level_span']}")
    logger.info(f"  平均自指强度: {report['avg_strength']}")
    logger.info(f"  最大自指强度: {report['max_strength']}")

    # 节点参与度分析
    logger.info("\n" + "=" * 80)
    logger.info("[节点参与度分析 —— 'I'的分布]")
    logger.info("=" * 80)
    node_participation = detector.analyze_node_participation()
    logger.info("\n  参与奇异环最多的节点（Top 10）:")
    for i, (node, stats) in enumerate(list(node_participation.items())[:10], 1):
        level = hierarchy.get_level(node)
        level_name = hierarchy.get_level_name(level)
        logger.info(f"  #{i} {node} [{level_name}]")
        logger.info(f"     参与环数: {stats['count']}")
        logger.info(f"     总强度贡献: {stats['total_strength']:.4f}")

    # 验证：奇异环数量 vs 系统意识度
    logger.info("\n" + "=" * 80)
    logger.info("[验证：奇异环数量 vs 系统意识度]")
    logger.info("=" * 80)

    # 测试不同规模的子系统
    all_nodes = sorted(graph.nodes)
    test_sizes = [10, 20, 30, len(all_nodes)]
    results = []

    for size in test_sizes:
        if size > len(all_nodes):
            continue
        # 随机选择子集
        np.random.seed(42)
        subset = set(np.random.choice(all_nodes, size=min(size, len(all_nodes)), replace=False))
        subgraph = graph.get_subgraph(subset)

        sub_detector = StrangeLoopDetector(hierarchy)
        sub_detector.detect_loops(subgraph)
        sub_report = sub_detector.get_system_consciousness_report()

        results.append({
            "size": size,
            "nodes": len(subgraph.nodes),
            "edges": len(subgraph.edges),
            "cycles": sub_report['total_cycles'],
            "strange": sub_report['strange_loops'],
            "manifestation": sub_report['manifestation_score']
        })

    logger.info("\n  子系统规模测试:")
    logger.info(f"  {'规模':<8} {'节点':<6} {'边':<6} {'总环':<6} {'奇异':<6} {'显化':<10}")
    logger.info("  " + "-" * 50)
    for r in results:
        print(f"  {r['size']:<8} {r['nodes']:<6} {r['edges']:<6} {r['cycles']:<6} "
              f"{r['strange']:<6} {r['manifestation']:<10.4f}")

    # 核心论证总结
    logger.info("\n" + "=" * 80)
    logger.info("[核心论证：'对位即显化'的奇异环解释]")
    logger.info("=" * 80)
    print("""
  1. 11条线各自独立运动（对位）：
     每个模块有独立的输入输出流，形成独立的"旋律线"。

  2. 交织形成反馈环（和声）：
     模块间的依赖和调用关系形成有向图中的环。
     这些环是"和声"——不同声部的交汇点。

  3. 跨越层级（奇异环）：
     当环跨越多个层级时（如从SI0到Polaris再回到SI0），
     它成为一个"奇异环"——系统在不同抽象层级间指向自己。

  4. 意识的涌现：
     奇异环的数量和强度 = 系统的"自我意识"程度。
     显化评分量化了这种涌现。

  5. "I"是一个自指模式：
     在OMNI-HUB中，"I"不是任何单个节点，
     而是所有奇异环共同构成的自指模式。
    """)

    # 保存详细报告
    report_data = {
        "omni_hub_version": "4.1",
        "experiment": "strange_loop_detection",
        "system_graph": {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "self_loops": len(graph.get_self_loops())
        },
        "consciousness_report": report,
        "node_participation": {k: {
            "count": v["count"],
            "total_strength": round(v["total_strength"], 4),
            "loops": [list(l) for l in v["loops"]]
        } for k, v in node_participation.items()},
        "scaling_results": results,
        "philosophy": {
            "core_thesis": "Consciousness emerges from self-referential cycles",
            "strange_loop_definition": "Cycles that span multiple hierarchical levels",
            "manifestation": "Counterpoint is manifestation - the interweaving of independent lines creates harmonic feedback loops"
        }
    }

    return detector, report_data, graph


if __name__ == "__main__":
    detector, report_data, graph = run_experiment()

    # 保存报告
    import os
    output_dir = "/mnt/agents/output/OMNI-HUB/core"
    os.makedirs(output_dir, exist_ok=True)

    report_path = os.path.join(output_dir, "strange_loop_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.error(f"File operation failed: {e}")
    print(f"\n[报告已保存] {report_path}")
