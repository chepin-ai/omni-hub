
__version__ = "11.0.0"
"""
OMNI-HUB v8.0 — External Knowledge Weaver (外部知识编织器)

将三篇微信公众号文章的知识融合入OMNI-HUB知识谱系：
1. 《由超图到p进因果性：离散决定论系统的非阿基米德框架》(黄岱永)
2. 《一个百年数论猜想的终极回答》(数学家)
3. 《刚性作为约束系统吸引子的本质》(Romani Isa)

Author: OMNI-HUB Architecture Team
Version: 8.0.0
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import networkx as nx
from numpy.typing import NDArray
import logging

# Suppress potential warnings from networkx / numpy
warnings.filterwarnings("ignore", category=FutureWarning)


# ═══════════════════════════════════════════════════════════════════════════
# 1. ExternalKnowledgeNode — 外部知识节点
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ExternalKnowledgeNode:
    """
    外部知识节点 — 封装单篇外部文章中的核心概念。

    Attributes
    ----------
    source : str
        来源标识，例如 "article_1", "article_2", "article_3"。
    concept : str
        概念名称（唯一标识符）。
    description : str
        概念的自然语言描述。
    mathematical_formulation : str
        概念的数学表述（LaTeX风格字符串）。
    omni_hub_mapping : str
        该概念映射到的 OMNI-HUB 内部知识节点名称。
    embedding : NDArray[np.float64]
        概念嵌入向量（默认 128 维，可扩展）。
    metadata : Dict[str, Any]
        附加元数据（作者、章节、引用次数等）。
    internal_links : List[str]
        已建立的内部知识节点链接列表。
    """

    source: str
    concept: str
    description: str
    mathematical_formulation: str
    omni_hub_mapping: str
    embedding: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros(128, dtype=np.float64)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)
    internal_links: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """初始化后处理：若 embedding 未设置，则基于概念文本生成确定性嵌入。"""
        if np.allclose(self.embedding, 0):
            self.embedding = self._generate_embedding()

    def _generate_embedding(self, dim: int = 128) -> NDArray[np.float64]:
        """
        基于 concept + description 的 SHA-256 哈希生成确定性嵌入向量。

        Parameters
        ----------
        dim : int
            嵌入维度。

        Returns
        -------
        NDArray[np.float64]
            单位化的嵌入向量。
        """
        text = f"{self.source}::{self.concept}::{self.description}"
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        # 使用哈希字节构建足够长的随机序列
        rng = np.random.default_rng(int.from_bytes(hash_bytes[:8], "big"))
        vec = rng.standard_normal(dim)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 1e-12 else vec

    def link_to_internal(self, internal_node: str) -> None:
        """
        将该外部知识节点链接到 OMNI-HUB 内部知识节点。

        Parameters
        ----------
        internal_node : str
            内部知识节点的名称。
        """
        if internal_node not in self.internal_links:
            self.internal_links.append(internal_node)

    def compute_similarity(
        self, other_node: ExternalKnowledgeNode, method: str = "cosine"
    ) -> float:
        """
        计算与另一知识节点的相似度。

        Parameters
        ----------
        other_node : ExternalKnowledgeNode
            待比较的另一节点。
        method : str
            相似度度量方法，可选 "cosine"（余弦）, "euclidean"（欧氏距离倒数）,
            "hybrid"（混合语义+结构）。

        Returns
        -------
        float
            相似度得分，范围 [0, 1]。
        """
        if method == "cosine":
            dot = float(np.dot(self.embedding, other_node.embedding))
            return 0.5 + 0.5 * dot  # 映射到 [0,1]

        if method == "euclidean":
            dist = float(np.linalg.norm(self.embedding - other_node.embedding))
            return 1.0 / (1.0 + dist)

        if method == "hybrid":
            cos_sim = 0.5 + 0.5 * float(np.dot(self.embedding, other_node.embedding))
            # 结构相似性：共享内部链接的比例
            set_a = set(self.internal_links)
            set_b = set(other_node.internal_links)
            if set_a or set_b:
                struct_sim = len(set_a & set_b) / max(len(set_a | set_b), 1)
            else:
                struct_sim = 0.0
            return 0.7 * cos_sim + 0.3 * struct_sim

        raise ValueError(f"Unknown similarity method: {method}")

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典。"""
        return {
            "source": self.source,
            "concept": self.concept,
            "description": self.description,
            "mathematical_formulation": self.mathematical_formulation,
            "omni_hub_mapping": self.omni_hub_mapping,
            "embedding": self.embedding.tolist(),
            "metadata": self.metadata,
            "internal_links": self.internal_links,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExternalKnowledgeNode:
        """从字典反序列化。"""
        data = dict(data)
        data["embedding"] = np.array(data.pop("embedding"), dtype=np.float64)
        return cls(**data)

    def __hash__(self) -> int:
        return hash((self.source, self.concept))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExternalKnowledgeNode):
            return NotImplemented
        return self.source == other.source and self.concept == other.concept


# ═══════════════════════════════════════════════════════════════════════════
# 2. PAdicCausalityWeaver — p-adic因果性编织器
# ═══════════════════════════════════════════════════════════════════════════

class PAdicCausalityWeaver:
    """
    p-adic 因果性编织器。

    将文章1《由超图到p进因果性》的核心概念映射到 OMNI-HUB 的事件管道：
    - p-adic 数的非阿基米德拓扑
    - 离散决定论系统 / Wolfram 的 Ruliad 模型
    - 超图重写规则
    - 因果性作为非阿基米德结构

    Attributes
    ----------
    prime : int
        选定的素数 p，默认 2。
    max_depth : int
        p-adic 展开的最大深度。
    hypergraph_rules : List[Dict[str, Any]]
        提取的超图重写规则。
    topology : Dict[str, Any]
        构建的 p-adic 拓扑结构。
    """

    def __init__(self, prime: int = 2, max_depth: int = 6):
        if not self._is_prime(prime):
            raise ValueError(f"{prime} is not a prime number.")
        self.prime: int = prime
        self.max_depth: int = max_depth
        self.hypergraph_rules: List[Dict[str, Any]] = []
        self.topology: Dict[str, Any] = {}
        self._causal_states: List[Dict[str, Any]] = []
        self._event_mappings: Dict[str, Any] = {}

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    # ── 2.1 提取超图重写规则 ─────────────────────────────────────────────

    def extract_hypergraph_rules(self) -> List[Dict[str, Any]]:
        """
        从 p-adic 因果性框架中提取超图重写规则。

        模拟 Wolfram 物理项目中的超图替换：将高阶关系（超边）
        按照局部模式匹配进行重写，产生新的超图状态。

        Returns
        -------
        List[Dict[str, Any]]
            重写规则列表，每条规则包含 pattern, replacement, arity。
        """
        rules = [
            {
                "name": "causal_fusion",
                "pattern": {"hyperedges": [["A", "B"], ["B", "C"]], "arity": 2},
                "replacement": {"hyperedges": [["A", "B", "C"]], "arity": 3},
                "description": "两个二元超边通过共享节点 B 融合为三元超边",
            },
            {
                "name": "branching_split",
                "pattern": {"hyperedges": [["A", "B", "C"]], "arity": 3},
                "replacement": {"hyperedges": [["A", "B"], ["B", "C"]], "arity": 2},
                "description": "三元超边分裂为两个二元超边，产生因果分支",
            },
            {
                "name": "p_adic_closure",
                "pattern": {"hyperedges": [["x_i", "x_{i+1}"] for i in range(self.prime - 1)], "arity": 2},
                "replacement": {
                    "hyperedges": [[f"x_{i}" for i in range(self.prime)]],
                    "arity": self.prime,
                },
                "description": f"{self.prime}个二元边闭合成一个{self.prime}元超边（p-adic 模结构）",
            },
            {
                "name": "ultrametric_merge",
                "pattern": {"hyperedges": [["a", "b"], ["a", "c"], ["b", "c"]], "arity": 2},
                "replacement": {"hyperedges": [["a", "b", "c", "Δ≤max(Δ_ab,Δ_ac)"]], "arity": 4},
                "description": "强三角不等式下的超边合并（ultrametric 特性）",
            },
            {
                "name": "event_causal_future",
                "pattern": {"hyperedges": [["e_t", "e_{t+1}"]], "arity": 2},
                "replacement": {
                    "hyperedges": [["e_t", "e_{t+1}", "CausalCone(e_t)"]],
                    "arity": 3,
                },
                "description": "事件 e_t 的因果未来锥展开",
            },
            {
                "name": "ruliad_branch",
                "pattern": {"hyperedges": [["S"]], "arity": 1},
                "replacement": {
                    "hyperedges": [["S→S₁"], ["S→S₂"], ["S→S₃"]],
                    "arity": 2,
                },
                "description": "Ruliad 中的多路系统分支：一个状态分裂为多个可能后继",
            },
        ]
        self.hypergraph_rules = rules
        return rules

    # ── 2.2 构建 p-adic 拓扑 ─────────────────────────────────────────────

    def build_padic_topology(self, p: Optional[int] = None) -> Dict[str, Any]:
        """
        构建 p-adic 数的非阿基米德拓扑结构。

        p-adic 度量定义为 |x-y|_p = p^{-v_p(x-y)}，其中 v_p 是 p-adic 赋值。
        该度量满足强三角不等式（ultrametric）：|x-z|_p ≤ max(|x-y|_p, |y-z|_p)。

        Parameters
        ----------
        p : int, optional
            素数，默认使用 self.prime。

        Returns
        -------
        Dict[str, Any]
            拓扑结构描述，包含 balls, branches, levels。
        """
        p = p or self.prime
        levels: List[Dict[str, Any]] = []

        for level in range(self.max_depth + 1):
            radius = p ** (-level)
            num_balls = p**level
            level_data = {
                "level": level,
                "radius": radius,
                "num_balls": num_balls,
                "balls": [
                    {
                        "center": self._padic_expansion(i, p, level),
                        "radius": radius,
                        "children_count": p,
                    }
                    for i in range(num_balls)
                ],
            }
            levels.append(level_data)

        topology = {
            "prime": p,
            "max_depth": self.max_depth,
            "metric": f"|x-y|_{p} = {p}^{{-v_{p}(x-y)}}",
            "ultrametric_property": "|x-z| ≤ max(|x-y|, |y-z|)",
            "levels": levels,
            "total_nodes": sum(l["num_balls"] for l in levels),
            "branching_factor": p,
        }
        self.topology = topology
        return topology

    def _padic_expansion(self, n: int, p: int, depth: int) -> str:
        """生成 n 的 p-adic 展开字符串表示（截断到 depth 位）。"""
        digits = []
        temp = n
        for _ in range(depth):
            digits.append(str(temp % p))
            temp //= p
        return f"{n} = ...{''.join(reversed(digits))} (mod {p}^{depth})"

    # ── 2.3 离散因果模型 ─────────────────────────────────────────────────

    def discrete_causality_model(self) -> Dict[str, Any]:
        """
        构建离散决定论因果模型。

        核心思想：在 p-adic 框架下，因果性不是连续的偏序关系，
        而是由超图重写步骤诱导的离散前序关系，
        每一步重写对应一个 p-adic "距离"的离散跳跃。

        Returns
        -------
        Dict[str, Any]
            因果模型包含 states, transitions, causal_order。
        """
        states = [f"S_{i}" for i in range(self.prime**self.max_depth)]
        transitions = []
        causal_order = []

        for i, s_from in enumerate(states):
            # 每个状态根据 p-adic 赋值决定其后继数量
            v_p = self._padic_valuation(i, self.prime)
            num_successors = max(1, self.prime - v_p)
            for j in range(num_successors):
                s_to = states[(i + j + 1) % len(states)]
                transitions.append(
                    {
                        "from": s_from,
                        "to": s_to,
                        "rule": random.choice([r["name"] for r in self.hypergraph_rules]),
                        "causal_strength": 1.0 / (1 + v_p),
                    }
                )
                causal_order.append((s_from, s_to, 1.0 / (1 + v_p)))

        model = {
            "states": states,
            "transitions": transitions,
            "causal_order": causal_order,
            "principle": "Discrete causality = p-adic distance jumps in hypergraph rewriting",
            "num_states": len(states),
            "num_transitions": len(transitions),
        }
        self._causal_states = states
        return model

    def _padic_valuation(self, n: int, p: int) -> int:
        """计算整数 n 的 p-adic 赋值 v_p(n)（n 中因子 p 的指数）。"""
        if n == 0:
            return self.max_depth
        count = 0
        while n % p == 0 and n > 0:
            n //= p
            count += 1
        return count

    # ── 2.4 映射到事件驱动系统 ───────────────────────────────────────────

    def map_to_event_drive(self) -> Dict[str, Any]:
        """
        将 p-adic 因果模型映射到 OMNI-HUB 事件驱动系统。

        映射关系：
        - p-adic 球 ↔ 事件管道中的事件类
        - 超图重写步 ↔ 事件触发器
        - 因果锥 ↔ 事件传播扇出
        - ultrametric 距离 ↔ 事件优先级层级

        Returns
        -------
        Dict[str, Any]
            事件驱动映射规范。
        """
        if not self.topology:
            self.build_padic_topology()

        event_classes = []
        for level_data in self.topology["levels"]:
            level = level_data["level"]
            for ball in level_data["balls"]:
                event_classes.append(
                    {
                        "class_name": f"Event_L{level}_C{ball['center'].split('=')[0].strip()}",
                        "padic_level": level,
                        "causal_radius": ball["radius"],
                        "priority": 1.0 - ball["radius"],  # 半径越小，优先级越高
                        "omni_hub_pipe": f"event_pipe::causal::level_{level}",
                    }
                )

        triggers = [
            {
                "trigger_name": f"HG_rewrite_{rule['name']}",
                "condition": f"pattern_match({rule['pattern']})",
                "action": f"emit_event({rule['replacement']})",
                "causal_depth_increment": 1,
            }
            for rule in self.hypergraph_rules
        ]

        mapping = {
            "mapping_type": "p-adic causality → OMNI-HUB event-driven system",
            "event_classes": event_classes,
            "event_triggers": triggers,
            "propagation_model": {
                "fanout": self.prime,
                "causal_cone_expansion": f"O({self.prime}^t)",
                "priority_metric": "1 - |x-y|_p",
            },
            "ultrametric_priority": True,
            "pipe_bindings": [
                {
                    "omni_pipe": "event_pipe::causal::root",
                    "padic_level": 0,
                    "description": "根事件管道接收所有 p-adic 级别 0 的因果事件",
                },
                {
                    "omni_pipe": "event_pipe::causal::fine",
                    "padic_level": self.max_depth,
                    "description": "精细事件管道处理最高分辨率的因果事件",
                },
            ],
        }
        self._event_mappings = mapping
        return mapping

    # ── 2.5 Ruliad 索引 ──────────────────────────────────────────────────

    def ruliad_index(self) -> Dict[str, Any]:
        """
        构建 Ruliad 索引 — 枚举所有可能的超图重写历史。

        Ruliad = 所有可能计算规则的纠缠极限。
        在 p-adic 框架下，Ruliad 被组织为一棵深度优先的 p 叉树，
        每个节点代表一个重写历史分支。

        Returns
        -------
        Dict[str, Any]
            Ruliad 树结构、分支计数、纠缠度量。
        """
        total_branches = sum(self.prime**d for d in range(self.max_depth + 1))
        entanglement = math.log(total_branches) / math.log(self.prime)

        return {
            "ruliad_definition": "Entangled limit of all possible hypergraph rewriting histories",
            "prime": self.prime,
            "tree_depth": self.max_depth,
            "branching_factor": self.prime,
            "total_branches": total_branches,
            "entanglement_measure": entanglement,
            "index_structure": "p-adic rooted tree where each node is a rewrite history",
            "omni_hub_equivalent": "knowledge_field::ruliad::entangled_computations",
            "coherence_metric": f"C = 1 / log_{self.prime}(branches) = {1.0/entanglement:.4f}",
        }

    # ── 辅助：生成知识节点 ───────────────────────────────────────────────

    def generate_knowledge_nodes(self) -> List[ExternalKnowledgeNode]:
        """生成文章1相关的所有外部知识节点（≥10个）。"""
        nodes = [
            ExternalKnowledgeNode(
                source="article_1",
                concept="p-adic_numbers",
                description="p-adic数是非阿基米德域，其拓扑由p-adic赋值诱导，满足强三角不等式",
                mathematical_formulation=r"\mathbb{Q}_p = \left\{ \sum_{k=-N}^{\infty} a_k p^k \mid a_k \in \{0,\dots,p-1\} \right\}, |x|_p = p^{-v_p(x)}",
                omni_hub_mapping="topology::non_archimedean_field",
                metadata={"author": "黄岱永", "section": "p-adic基础", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="ultrametric_property",
                description="超度量性质：任意三点中，至少有两点的距离相等（isosceles principle）",
                mathematical_formulation=r"|x-z|_p \leq \max(|x-y|_p, |y-z|_p)",
                omni_hub_mapping="metric_space::strong_triangle_inequality",
                metadata={"author": "黄岱永", "section": "拓扑性质", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="discrete_determinism",
                description="离散决定论：系统演化由离散的规则应用步骤决定，而非连续微分方程",
                mathematical_formulation=r"S_{t+1} = R(S_t), R \in \{\text{rewrite rules}\}",
                omni_hub_mapping="computation::discrete_dynamics",
                metadata={"author": "黄岱永", "section": "决定论框架", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="hypergraph_rewriting",
                description="超图重写：通过模式匹配替换超边，是Wolfram物理项目的基础计算原语",
                mathematical_formulation=r"G_{t+1} = G_t[\text{pattern}_i \to \text{replacement}_i]",
                omni_hub_mapping="graph_theory::hypergraph_transformation",
                metadata={"author": "黄岱永", "section": "重写系统", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="ruliad_model",
                description="Ruliad模型：所有可能计算规则的纠缠极限，宇宙状态即Ruliad中的路径",
                mathematical_formulation=r"\mathcal{R} = \lim_{n \to \infty} \bigotimes_{i=1}^{n} \{\text{rules}_i\}",
                omni_hub_mapping="meta_theory::computational_universe",
                metadata={"author": "黄岱永", "section": "Ruliad", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="causal_cone",
                description="因果锥：在超图重写中，一个事件的因果未来由所有可达重写状态组成",
                mathematical_formulation=r"C^+(e) = \{ e' \mid e \prec e' \text{ in rewrite history} \}",
                omni_hub_mapping="causality::future_cone",
                metadata={"author": "黄岱永", "section": "因果结构", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="non_archimedean_causality",
                description="非阿基米德因果性：因果关系由p-adic距离度量，非连续偏序",
                mathematical_formulation=r"d_{causal}(e_1, e_2) = |t_1 - t_2|_p, t_i \in \mathbb{Z}_p",
                omni_hub_mapping="causality::discrete_order",
                metadata={"author": "黄岱永", "section": "核心论题", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="information_flow",
                description="信息流动：超图重写中的信息沿着因果锥传播，受p-adic拓扑约束",
                mathematical_formulation=r"I(e \to e') = -\log_p |t_e - t_{e'}|_p",
                omni_hub_mapping="information_theory::causal_flow",
                metadata={"author": "黄岱永", "section": "信息论", "importance": 7},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="state_evolution",
                description="状态演化：系统状态在p-adic时间上的演化可建模为球面上的随机游走",
                mathematical_formulation=r"P(S_{t+1} | S_t) \propto \exp(-\alpha \cdot d_p(S_t, S_{t+1}))",
                omni_hub_mapping="dynamics::state_transition",
                metadata={"author": "黄岱永", "section": "演化方程", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="p_adic_time",
                description="p-adic时间：时间参数取值为p-adic整数，允许无限精细和无限粗粒化的因果层级",
                mathematical_formulation=r"t \in \mathbb{Z}_p = \varprojlim \mathbb{Z}/p^n\mathbb{Z}",
                omni_hub_mapping="time::discrete_hierarchy",
                metadata={"author": "黄岱永", "section": "时间模型", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="branching_history",
                description="分支历史：多路系统中的因果图允许分支与合并，形成非线性时间",
                mathematical_formulation=r"\mathcal{H} = \bigcup_{\gamma \in \Gamma} \gamma, \Gamma = \{\text{all rewrite paths}\}",
                omni_hub_mapping="time::branching_manifold",
                metadata={"author": "黄岱永", "section": "多路系统", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_1",
                concept="causal_invariance",
                description="因果不变性：若所有重写路径产生相同的因果图，则系统具有因果不变性",
                mathematical_formulation=r"\forall \gamma_1, \gamma_2: \text{CausalGraph}(\gamma_1) \cong \text{CausalGraph}(\gamma_2)",
                omni_hub_mapping="symmetry::causal_equivalence",
                metadata={"author": "黄岱永", "section": "对称性", "importance": 9},
            ),
        ]
        return nodes




# ═══════════════════════════════════════════════════════════════════════════
# 3. MordellLangWeaver — 莫德尔-朗编织器
# ═══════════════════════════════════════════════════════════════════════════

class MordellLangWeaver:
    """
    莫德尔-朗猜想编织器。

    将文章2《一个百年数论猜想的终极回答》的核心概念映射到 OMNI-HUB：
    - 丢番图几何中的有限性定理
    - 阿贝尔簇上的有理点
    - 法尔廷斯高度（Faltings height）
    - 一致性/统一控制
    - 间隙原理

    核心映射：有限性/一致性 ↔ 知识节点的有限覆盖。
    """

    def __init__(self, dimension: int = 2, field_degree: int = 1):
        self.dimension: int = dimension
        self.field_degree: int = field_degree
        self._finiteness_bounds: Dict[str, float] = {}
        self._uniform_data: Dict[str, Any] = {}

    # ── 3.1 有限性原理 ───────────────────────────────────────────────────

    def finiteness_principle(self) -> Dict[str, Any]:
        """
        莫德尔-朗猜想的有限性原理。

        核心命题：对于阿贝尔簇 A 上的子簇 V，
        V ∩ Γ（其中 Γ 是有限秩子群）不是 Zariski 稠密的，
        除非 V 本身是子群的平移。

        映射到 OMNI-HUB：知识节点在任何有限秩子空间中的交是有限的，
        除非该子空间本身被知识场"平移覆盖"。

        Returns
        -------
        Dict[str, Any]
            有限性原理的数学表述及 OMNI-HUB 映射。
        """
        return {
            "theorem": "Mordell-Lang Conjecture (proved by Faltings, Vojta, McQuillan)",
            "statement": (
                "Let A be an abelian variety, V ⊂ A a subvariety, "
                "Γ ⊂ A(ℚ̄) a finitely generated subgroup. "
                "Then V ∩ Γ is a finite union of cosets of subgroups of Γ."
            ),
            "finiteness_conclusion": "V ∩ Γ is NOT Zariski-dense in V unless V is a coset",
            "omni_hub_mapping": {
                "abelian_variety": "knowledge_space::smooth_complete_group",
                "subvariety": "knowledge_subspace::constrained_region",
                "finitely_generated_subgroup": "finite_rank_knowledge_basis",
                "intersection": "knowledge_nodes::covered_set",
                "finite_union_of_cosets": "finite_covering_by_translations",
            },
            "principle_for_omni_hub": (
                "Any knowledge subspace intersected with a finite-rank basis "
                "yields a finitely coverable set — enabling finite indexing."
            ),
        }

    # ── 3.2 一致性界限 ───────────────────────────────────────────────────

    def uniform_bound(self) -> Dict[str, Any]:
        """
        一致性/统一控制界限。

        核心思想：有限性不是存在性的，而是构造性的 ——
        存在一个统一的界，控制所有可能情况下的交的大小。

        映射到 OMNI-HUB：知识节点的覆盖数可以被一致地界定，
        与具体参数无关（仅依赖于秩和维度）。

        Returns
        -------
        Dict[str, Any]
            一致性界限的数学表述。
        """
        rank = self.dimension * self.field_degree + 1
        # 模拟一致界：指数依赖于秩和维度
        bound = math.exp(rank * math.log(2 * self.dimension + 1))

        self._uniform_data = {
            "rank": rank,
            "dimension": self.dimension,
            "uniform_bound": bound,
            "bound_formula": f"B(d, r) ≤ exp(r · log(2d+1)) ≈ {bound:.2e}",
        }

        return {
            "uniformity_principle": "There exists a uniform bound on the number of cosets, independent of the specific variety",
            "bound": bound,
            "depends_on": ["rank_of_Γ", "dimension_of_A", "degree_of_field_extension"],
            "independence": "Bound does NOT depend on the specific shape of V",
            "omni_hub_mapping": {
                "uniform_bound": "knowledge_index::max_covering_number",
                "independence_from_shape": "abstraction::shape_invariant_control",
            },
            "consequence": (
                "OMNI-HUB can pre-allocate finite index structures "
                "with guaranteed coverage for any knowledge subspace."
            ),
        }

    # ── 3.3 间隙原理 ─────────────────────────────────────────────────────

    def gap_principle(self) -> Dict[str, Any]:
        """
        间隙原理（Gap Principle）。

        在丢番图逼近中，若两个有理点过于接近，则它们必须位于
        某个低维子簇上。这产生了"间隙"——点之间必须保持最小距离。

        映射到 OMNI-HUB：知识节点之间若相似度过高，则它们必然属于
        同一"低维概念簇"，从而产生自然的分类间隙。

        Returns
        -------
        Dict[str, Any]
            间隙原理的数学表述及映射。
        """
        return {
            "principle_name": "Gap Principle",
            "statement": (
                "If two rational points P, Q on V are 'too close' (measured by height), "
                "then they must lie on a proper subvariety of V. "
                "Hence, points below a height bound are separated by a gap."
            ),
            "mathematical_formulation": (
                r"h(P), h(Q) < B \land d(P,Q) < ε \implies "
                r"\exists W \subsetneq V: P, Q \in W(ℚ̄)"
            ),
            "gap_measure": "Minimum height difference between independent points",
            "omni_hub_mapping": {
                "height_gap": "knowledge_distance::minimum_separation",
                "subvariety_containment": "clustering::low_dimensional_manifold",
                "independent_points": "orthogonal_knowledge_basis",
            },
            "application": (
                "Detect when two 'close' knowledge nodes should be merged "
                "into a higher-level concept cluster."
            ),
        }

    # ── 3.4 高度函数 ─────────────────────────────────────────────────────

    def height_function(self, point: Optional[NDArray[np.float64]] = None) -> Dict[str, Any]:
        """
        法尔廷斯高度函数（Faltings Height）。

        高度函数度量算术对象的"复杂性"。
        在 OMNI-HUB 中，高度对应知识节点的"信息复杂度"或"抽象层级"。

        Parameters
        ----------
        point : NDArray[np.float64], optional
            待计算高度的点（知识节点嵌入），若未提供则使用示例。

        Returns
        -------
        Dict[str, Any]
            高度值及 OMNI-HUB 映射。
        """
        if point is None:
            point = np.random.standard_normal(self.dimension)

        # 模拟 Faltings height 的组成部分
        archimedean_part = float(np.log(max(1.0, np.linalg.norm(point))))
        non_archimedean_part = sum(
            abs(float(x)) for x in point[: min(3, len(point))]
        ) / max(1, len(point))
        # 正规化高度
        height = archimedean_part + non_archimedean_part

        self._finiteness_bounds["height_example"] = height

        return {
            "height_type": "Faltings Height (arithmetic complexity measure)",
            "archimedean_part": archimedean_part,
            "non_archimedean_part": non_archimedean_part,
            "total_height": height,
            "omni_hub_mapping": {
                "height": "knowledge_node::information_complexity",
                "archimedean_part": "continuous_information_content",
                "non_archimedean_part": "discrete_structural_complexity",
                "normalized_height": "abstraction_level_index",
            },
            "interpretation": (
                "Higher height → more complex knowledge node → "
                "requires more computational resources to resolve."
            ),
        }

    # ── 辅助：生成知识节点 ───────────────────────────────────────────────

    def generate_knowledge_nodes(self) -> List[ExternalKnowledgeNode]:
        """生成文章2相关的所有外部知识节点（≥10个）。"""
        nodes = [
            ExternalKnowledgeNode(
                source="article_2",
                concept="mordell_lang_conjecture",
                description="莫德尔-朗猜想：阿贝尔簇子簇与有限秩子群的交是有限个陪集的并",
                mathematical_formulation=r"V \cap \Gamma = \bigcup_{i=1}^{N} (\gamma_i + H_i), H_i < \Gamma, N < \infty",
                omni_hub_mapping="theorem::finiteness_structure",
                metadata={"author": "数学家", "section": "核心定理", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="abelian_variety",
                description="阿贝尔簇：完备代数簇上的代数群结构，是椭圆曲线的高维推广",
                mathematical_formulation=r"A / \mathbb{Q}: \text{projective, } m: A \times A \to A, \text{inv}: A \to A",
                omni_hub_mapping="geometry::algebraic_group",
                metadata={"author": "数学家", "section": "代数几何", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="diophantine_geometry",
                description="丢番图几何：研究代数方程在有理数/整数上的解的几何方法",
                mathematical_formulation=r"X(\mathbb{Q}) = \{ x \in X \mid \text{coordinates in } \mathbb{Q} \}",
                omni_hub_mapping="number_theory::arithmetic_geometry",
                metadata={"author": "数学家", "section": "基础", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="faltings_height",
                description="法尔廷斯高度：度量阿贝尔簇的算术复杂性，连接几何与数论",
                mathematical_formulation=r"h_{Fal}(A) = \frac{1}{[K:\mathbb{Q}]} \left( \log |\Delta_{K/\mathbb{Q}}| - \sum_{\sigma} \log \|\omega\|_{\sigma}^2 \right)",
                omni_hub_mapping="invariant::arithmetic_complexity",
                metadata={"author": "数学家", "section": "高度理论", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="finite_rank_subgroup",
                description="有限秩子群：由有限个生成元生成的子群，秩是其线性独立生成元的个数",
                mathematical_formulation=r"\Gamma = \langle P_1, \dots, P_r \rangle, \text{rank}(\Gamma) = r < \infty",
                omni_hub_mapping="algebra::finite_generation",
                metadata={"author": "数学家", "section": "群论", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="zariski_topology",
                description="Zariski拓扑：代数几何中的粗拓扑，闭集由代数方程的零点集定义",
                mathematical_formulation=r"Z(I) = \{ x \in \mathbb{A}^n \mid f(x)=0, \forall f \in I \}, \tau_{Zar} = \{ \mathbb{A}^n \setminus Z(I) \}",
                omni_hub_mapping="topology::algebraic_closed_sets",
                metadata={"author": "数学家", "section": "拓扑", "importance": 7},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="uniformity_conjecture",
                description="一致性猜想：有限性常数可以被统一界定，不依赖于具体簇的选择",
                mathematical_formulation=r"\exists B(d, r): N(V, \Gamma) \leq B(d, r), \forall V, \Gamma \text{ with } \dim V=d, \text{rank}\Gamma=r",
                omni_hub_mapping="control_theory::uniform_bounds",
                metadata={"author": "数学家", "section": "一致性", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="gap_principle",
                description="间隙原理：丢番图方程的解之间存在最小间隙，由高度函数控制",
                mathematical_formulation=r"h(P_{n+1}) \geq h(P_n) + c \cdot \log h(P_n)",
                omni_hub_mapping="geometry::minimum_separation",
                metadata={"author": "数学家", "section": "逼近论", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="rational_points",
                description="有理点：代数簇上坐标为有理数的点，是丢番图方程的解",
                mathematical_formulation=r"P = [x_0 : x_1 : \dots : x_n] \in \mathbb{P}^n(\mathbb{Q}), x_i \in \mathbb{Q}",
                omni_hub_mapping="number_theory::rational_solutions",
                metadata={"author": "数学家", "section": "基础", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="subvariety_intersection",
                description="子簇交：两个代数簇的交集，其结构由Bézout定理和维度理论控制",
                mathematical_formulation=r"\dim(V \cap W) \geq \dim V + \dim W - \dim X",
                omni_hub_mapping="geometry::intersection_theory",
                metadata={"author": "数学家", "section": "交集", "importance": 7},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="bombieri_lang_conjecture",
                description="Bombieri-Lang猜想：一般类型代数簇上的有理点不是Zariski稠密的",
                mathematical_formulation=r"X \text{ of general type} \implies X(\mathbb{Q}) \text{ not Zariski-dense}",
                omni_hub_mapping="conjecture::sparse_rational_points",
                metadata={"author": "数学家", "section": "推广", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_2",
                concept="arithmetic_complexity",
                description="算术复杂度：由高度函数度量的算术对象内在复杂性，控制计算难度",
                mathematical_formulation=r"\text{Comp}_{arith}(P) = O(\exp(h(P)))",
                omni_hub_mapping="complexity::arithmetic_measure",
                metadata={"author": "数学家", "section": "复杂度", "importance": 8},
            ),
        ]
        return nodes


# ═══════════════════════════════════════════════════════════════════════════
# 4. RigidityWeaver — 约束刚性编织器
# ═══════════════════════════════════════════════════════════════════════════

class RigidityWeaver:
    """
    约束刚性编织器。

    将文章3《刚性作为约束系统吸引子的本质》的核心概念映射到 OMNI-HUB：
    - 约束本体论
    - 四种刚性：组合、几何、范畴、分析
    - 有限单群分类（魔群 Monster group）
    - Mostow 刚性定理
    - 刚性 = 约束系统的吸引子
    - 自由度坍缩

    核心映射：刚性 ↔ 系统吸引子 ↔ 自组织临界点。
    """

    def __init__(self, constraint_dimension: int = 3):
        self.constraint_dimension: int = constraint_dimension
        self._attractor_state: Dict[str, Any] = {}
        self._rigidity_types: Dict[str, Dict[str, Any]] = {}

    # ── 4.1 组合刚性 ─────────────────────────────────────────────────────

    def combinatorial_rigidity(self) -> Dict[str, Any]:
        """
        组合刚性 — 有限单群分类（Monster group）。

        有限单群是群论中的"原子"，其分类定理是数学史上最庞大的定理之一。
        魔群（Monster group）是最大的散在单群，具有惊人的对称性。

        映射到 OMNI-HUB：组合刚性 ↔ 知识系统的基本不可约单元。

        Returns
        -------
        Dict[str, Any]
            组合刚性的数学描述及映射。
        """
        monster_order = 808017424794512875886459904961710757005754368000000000
        return {
            "rigidity_type": "Combinatorial Rigidity",
            "foundation": "Classification of Finite Simple Groups",
            "monster_group": {
                "order": monster_order,
                "order_scientific": "8.08 × 10^53",
                "dimensions_of_irreducible_representations": [
                    1, 196883, 21296876, 842609326, ...
                ],
                "moonshine_connection": "j(τ) = q^{-1} + 744 + 196884q + ... ↔ Monster representations",
            },
            "principle": "Discrete symmetries have fundamental, indivisible building blocks",
            "omni_hub_mapping": {
                "finite_simple_group": "knowledge_atom::irreducible_unit",
                "monster_group": "symmetry::maximal_sporadic_attractor",
                "classification_theorem": "taxonomy::complete_enumeration",
            },
        }

    # ── 4.2 几何刚性 ─────────────────────────────────────────────────────

    def geometric_rigidity(self) -> Dict[str, Any]:
        """
        几何刚性 — Mostow 刚性定理。

        Mostow 刚性定理：对于 n ≥ 3 的紧双曲流形，其基本群决定了
        其等距类。即，拓扑等价意味着等距等价。

        映射到 OMNI-HUB：几何刚性 ↔ 知识空间的度量结构被拓扑完全确定。

        Returns
        -------
        Dict[str, Any]
            几何刚性的数学描述及映射。
        """
        return {
            "rigidity_type": "Geometric Rigidity",
            "theorem": "Mostow Rigidity Theorem",
            "statement": (
                "If M, N are compact hyperbolic n-manifolds (n ≥ 3) "
                "with isomorphic fundamental groups, then they are isometric."
            ),
            "mathematical_formulation": (
                r"\pi_1(M) \cong \pi_1(N) \implies M \cong_{isom} N, \text{ for } n \geq 3"
            ),
            "key_insight": "Topology determines geometry in high dimensions — no deformation possible",
            "omni_hub_mapping": {
                "fundamental_group": "knowledge_graph::connectivity_invariant",
                "isometry_class": "metric_structure::rigid_determination",
                "no_deformation": "stability::zero_modal_space",
            },
        }

    # ── 4.3 范畴刚性 ─────────────────────────────────────────────────────

    def categorical_rigidity(self) -> Dict[str, Any]:
        """
        范畴刚性 — 范畴等价下的结构保持。

        若两个范畴是等价的，则它们具有相同的"形状"。
        范畴刚性指：一旦确定了对象和态射的约束条件，
        整个范畴的结构就被刚性确定。

        映射到 OMNI-HUB：范畴刚性 ↔ 知识范畴的函子结构不可变形。

        Returns
        -------
        Dict[str, Any]
            范畴刚性的数学描述及映射。
        """
        return {
            "rigidity_type": "Categorical Rigidity",
            "principle": "Categorical equivalence preserves all structural relationships",
            "mathematical_formulation": (
                r"F: \mathcal{C} \to \mathcal{D} \text{ equivalence } "
                r"\implies \mathcal{C}(A,B) \cong \mathcal{D}(F(A), F(B))"
            ),
            "tannakian_duality": "Rep(G) ↔ G — representation category rigidly determines the group",
            "omni_hub_mapping": {
                "category_equivalence": "knowledge_functor::structure_preserving_map",
                "tannakian_duality": "duality::category_group_correspondence",
                "rigid_structure": "ontology::immutable_relationship_framework",
            },
        }

    # ── 4.4 分析刚性 ─────────────────────────────────────────────────────

    def analytic_rigidity(self) -> Dict[str, Any]:
        """
        分析刚性 — 解析函数和测度刚性。

        包括 Mostow 的拟共形刚性、Ratner 的测度刚性定理等。
        核心思想：在齐性空间上，不变测度必须具有代数结构。

        映射到 OMNI-HUB：分析刚性 ↔ 知识场中的概率分布必须服从约束流形。

        Returns
        -------
        Dict[str, Any]
            分析刚性的数学描述及映射。
        """
        return {
            "rigidity_type": "Analytic Rigidity",
            "theorems": [
                "Mostow quasiconformal rigidity",
                "Ratner measure rigidity",
                "Margulis superrigidity",
            ],
            "measure_rigidity_statement": (
                "Any ergodic invariant probability measure on G/Γ "
                "is homogeneous — supported on an orbit of a subgroup."
            ),
            "mathematical_formulation": (
                r"\mu \in \mathcal{P}(G/\Gamma), \mu \text{ ergodic, } U\text{-invariant} "
                r"\implies \exists H < G: \mu \text{ supported on } Hx"
            ),
            "omni_hub_mapping": {
                "invariant_measure": "knowledge_field::probability_distribution",
                "homogeneous_support": "attractor::algebraic_submanifold",
                "ergodic_decomposition": "knowledge_partition::invariant_cells",
            },
        }

    # ── 4.5 吸引子动力学 ─────────────────────────────────────────────────

    def attractor_dynamics(self) -> Dict[str, Any]:
        """
        刚性作为约束系统的吸引子动力学。

        核心命题：当一个动力系统受到足够强的约束时，
        其自由度坍缩，系统被"吸引"到一个刚性结构上。
        这个刚性结构就是约束系统的吸引子。

        映射到 OMNI-HUB：知识场的演化在强约束下收敛到刚性吸引子，
        即自组织临界点。

        Returns
        -------
        Dict[str, Any]
            吸引子动力学的数学描述及 OMNI-HUB 映射。
        """
        # 模拟自由度坍缩过程
        initial_dof = self.constraint_dimension ** 3
        constraints = [
            {"name": "combinatorial", "dof_reduction": 0.3},
            {"name": "geometric", "dof_reduction": 0.25},
            {"name": "categorical", "dof_reduction": 0.2},
            {"name": "analytic", "dof_reduction": 0.15},
        ]

        remaining_dof = initial_dof
        collapse_trajectory = []
        for c in constraints:
            remaining_dof *= (1 - c["dof_reduction"])
            collapse_trajectory.append({
                "constraint": c["name"],
                "remaining_dof": remaining_dof,
                "cumulative_reduction": 1 - remaining_dof / initial_dof,
            })

        self._attractor_state = {
            "initial_dof": initial_dof,
            "final_dof": remaining_dof,
            "collapse_ratio": remaining_dof / initial_dof,
            "attractor_dimension": max(1, int(round(remaining_dof))),
        }

        return {
            "dynamics_model": "Constraint-induced attractor formation",
            "initial_degrees_of_freedom": initial_dof,
            "constraints": constraints,
            "collapse_trajectory": collapse_trajectory,
            "final_attractor": {
                "dimension": self._attractor_state["attractor_dimension"],
                "description": "Low-dimensional manifold where all constraints are satisfied",
                "stability": "asymptotically stable (Lyapunov)",
            },
            "omni_hub_mapping": {
                "constraint_surface": "knowledge_manifold::feasible_region",
                "dof_collapse": "dimensionality_reduction::freedom_collapse",
                "attractor": "knowledge_attractor::self_organizing_critical_point",
                "lyapunov_stability": "convergence::guaranteed_settling",
            },
            "self_organized_criticality": {
                "description": "At the attractor, the system sits at a critical point where correlations are scale-free",
                "power_law": "P(avalanche) ~ s^{-τ}",
                "correlation_length": "diverges at criticality",
            },
        }

    # ── 辅助：生成知识节点 ───────────────────────────────────────────────

    def generate_knowledge_nodes(self) -> List[ExternalKnowledgeNode]:
        """生成文章3相关的所有外部知识节点（≥10个）。"""
        nodes = [
            ExternalKnowledgeNode(
                source="article_3",
                concept="constraint_ontology",
                description="约束本体论：系统的存在由约束定义，约束是存在的基础而非限制",
                mathematical_formulation=r"\mathcal{S} = \{ x \in X \mid C_i(x) = 0, i \in I \}, \text{constraints } C_i \text{ define } \mathcal{S}",
                omni_hub_mapping="ontology::constraint_defined_existence",
                metadata={"author": "Romani Isa", "section": "本体论", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="combinatorial_rigidity",
                description="组合刚性：离散结构在约束下的不可变形性，如有限单群的刚性分类",
                mathematical_formulation=r"|\text{Aut}(G)| < \infty \land G \text{ simple} \implies G \text{ combinatorially rigid}",
                omni_hub_mapping="algebra::discrete_rigidity",
                metadata={"author": "Romani Isa", "section": "组合刚性", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="geometric_rigidity",
                description="几何刚性：Mostow定理指出高维双曲流形的拓扑决定其几何，无变形空间",
                mathematical_formulation=r"\pi_1(M) \cong \pi_1(N) \implies M \cong_{isom} N, n \geq 3",
                omni_hub_mapping="geometry::topological_determination",
                metadata={"author": "Romani Isa", "section": "几何刚性", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="categorical_rigidity",
                description="范畴刚性：范畴的等价关系刚性保持所有结构，如Tannaka对偶",
                mathematical_formulation=r"\mathcal{C} \simeq \mathcal{D} \implies \text{structural invariants preserved}",
                omni_hub_mapping="category_theory::structure_preservation",
                metadata={"author": "Romani Isa", "section": "范畴刚性", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="analytic_rigidity",
                description="分析刚性：不变测度必须具有代数支撑，如Ratner测度刚性定理",
                mathematical_formulation=r"\mu \text{ ergodic } U\text{-invariant} \implies \mu \text{ supported on } Hx \subset G/\Gamma",
                omni_hub_mapping="analysis::measure_rigidity",
                metadata={"author": "Romani Isa", "section": "分析刚性", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="monster_group",
                description="魔群：最大的散在有限单群，与模函数的moonshine现象有深刻联系",
                mathematical_formulation=r"|\mathbb{M}| = 2^{46} \cdot 3^{20} \cdot 5^9 \cdot 7^6 \cdot 11^2 \cdot 13^3 \cdot 17 \cdot 19 \cdot 23 \cdot 29 \cdot 31 \cdot 41 \cdot 47 \cdot 59 \cdot 71",
                omni_hub_mapping="symmetry::maximal_sporadic_group",
                metadata={"author": "Romani Isa", "section": "魔群", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="rigidity_as_attractor",
                description="刚性=吸引子：约束系统的动力学演化收敛到低维刚性结构",
                mathematical_formulation=r"\dot{x} = F(x) + \lambda C(x), \lambda \to \infty \implies x \to \mathcal{M}_{rigid}",
                omni_hub_mapping="dynamics::constraint_attractor",
                metadata={"author": "Romani Isa", "section": "核心论题", "importance": 10},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="degree_of_freedom_collapse",
                description="自由度坍缩：约束累积导致系统自由度指数级减少，最终达到刚性状态",
                mathematical_formulation=r"\dim_{eff} = d_0 \cdot \prod_{i}(1 - \alpha_i), \alpha_i \in (0,1)",
                omni_hub_mapping="phase_transition::dimension_collapse",
                metadata={"author": "Romani Isa", "section": "坍缩动力学", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="self_organized_criticality",
                description="自组织临界点：刚性吸引子对应系统自组织到的临界状态，具有尺度自由关联",
                mathematical_formulation=r"P(s) \sim s^{-\tau}, \xi \to \infty \text{ at criticality}",
                omni_hub_mapping="criticality::self_organized_state",
                metadata={"author": "Romani Isa", "section": "SOC", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="moonshine_phenomenon",
                description="月光现象：魔群的表示维数与模函数的系数之间的神秘对应关系",
                mathematical_formulation=r"j(\tau) - 744 = q^{-1} + 196884q + 21493760q^2 + \dots, 196884 = 1 + 196883",
                omni_hub_mapping="duality::moonshine_correspondence",
                metadata={"author": "Romani Isa", "section": "月光", "importance": 8},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="mostow_theorem",
                description="Mostow刚性定理：高维双曲流形的基本群完全决定其等距结构",
                mathematical_formulation=r"\Gamma_1 \cong \Gamma_2 \implies \mathbb{H}^n/\Gamma_1 \cong_{isom} \mathbb{H}^n/\Gamma_2",
                omni_hub_mapping="geometry::mostow_rigidity",
                metadata={"author": "Romani Isa", "section": "Mostow", "importance": 9},
            ),
            ExternalKnowledgeNode(
                source="article_3",
                concept="constraint_accumulation",
                description="约束累积：多个独立约束的联合效应导致相空间急剧收缩",
                mathematical_formulation=r"\text{Vol}(\bigcap_i C_i) / \text{Vol}(X) \leq \prod_i (1 - \epsilon_i)",
                omni_hub_mapping="dynamics::constraint_accumulation",
                metadata={"author": "Romani Isa", "section": "累积效应", "importance": 8},
            ),
        ]
        return nodes




# ═══════════════════════════════════════════════════════════════════════════
# 5. LongRangeCorrelationDetector — 长程关联检测器
# ═══════════════════════════════════════════════════════════════════════════

class LongRangeCorrelationDetector:
    """
    长程关联检测器。

    检测三篇文章知识之间的跨文章长程关联：
    - p-adic 因果性 ↔ 莫德尔-朗有限性（非阿基米德度量 ↔ 高度函数）
    - 约束刚性 ↔ 离散决定论（吸引子 ↔ 重写规则收敛）
    - 范畴刚性 ↔ Ruliad（范畴等价 ↔ 纠缠极限）
    - 几何刚性 ↔ p-adic 拓扑（Mostow ↔ 非阿基米德球面）

    Attributes
    ----------
    knowledge_graph : nx.DiGraph
        存储所有知识节点及其关联的知识图谱。
    correlation_matrix : NDArray[np.float64]
        节点间的关联矩阵。
    """

    def __init__(self, similarity_threshold: float = 0.35):
        self.similarity_threshold: float = similarity_threshold
        self.knowledge_graph: nx.DiGraph = nx.DiGraph()
        self.correlation_matrix: Optional[NDArray[np.float64]] = None
        self._nodes: List[ExternalKnowledgeNode] = []
        self._bridges: List[Dict[str, Any]] = []

    # ── 5.1 检测跨文章关联 ───────────────────────────────────────────────

    def detect_across_articles(self) -> List[Dict[str, Any]]:
        """
        检测跨文章的知识关联。

        对于来自不同文章的知识节点对，计算其相似度，
        若超过阈值则标记为长程关联。

        Returns
        -------
        List[Dict[str, Any]]
            检测到的跨文章关联列表。
        """
        if len(self._nodes) < 2:
            return []

        correlations = []
        node_list = self._nodes

        for i, node_a in enumerate(node_list):
            for j, node_b in enumerate(node_list):
                if i >= j:
                    continue
                if node_a.source == node_b.source:
                    continue  # 只检测跨文章关联

                sim = node_a.compute_similarity(node_b, method="hybrid")
                if sim >= self.similarity_threshold:
                    correlation = {
                        "node_a": node_a.concept,
                        "source_a": node_a.source,
                        "node_b": node_b.concept,
                        "source_b": node_b.source,
                        "similarity": round(sim, 4),
                        "type": self._classify_correlation(node_a, node_b),
                        "omni_hub_implication": self._implication(node_a, node_b),
                    }
                    correlations.append(correlation)
                    # 添加到知识图谱
                    self.knowledge_graph.add_edge(
                        node_a.concept,
                        node_b.concept,
                        weight=sim,
                        **correlation,
                    )

        # 按相似度降序排列
        correlations.sort(key=lambda x: x["similarity"], reverse=True)
        return correlations

    def _classify_correlation(
        self, a: ExternalKnowledgeNode, b: ExternalKnowledgeNode
    ) -> str:
        """根据节点内容对关联类型进行分类。"""
        text = f"{a.concept} {a.description} {b.concept} {b.description}".lower()

        if any(w in text for w in ["topology", "metric", "ultrametric", "archimedean"]):
            return "topological_correspondence"
        if any(w in text for w in ["group", "symmetry", "monster", "algebraic"]):
            return "algebraic_correspondence"
        if any(w in text for w in ["dynamics", "attractor", "evolution", "causal"]):
            return "dynamical_correspondence"
        if any(w in text for w in ["finite", "finiteness", "bound", "classification"]):
            return "finiteness_correspondence"
        if any(w in text for w in ["category", "functor", "ruliad", "structure"]):
            return "structural_correspondence"
        return "semantic_correspondence"

    def _implication(
        self, a: ExternalKnowledgeNode, b: ExternalKnowledgeNode
    ) -> str:
        """生成 OMNI-HUB 层面的关联含义。"""
        mappings = {
            ("article_1", "article_2"): (
                f"p-adic topology of '{a.concept}' constrains the height bounds of '{b.concept}'"
            ),
            ("article_1", "article_3"): (
                f"Discrete causality in '{a.concept}' drives attractor formation in '{b.concept}'"
            ),
            ("article_2", "article_3"): (
                f"Finiteness of '{a.concept}' enables rigid classification of '{b.concept}'"
            ),
        }
        key = (a.source, b.source)
        reverse_key = (b.source, a.source)
        return mappings.get(key, mappings.get(reverse_key, "Cross-domain knowledge transfer"))

    # ── 5.2 构建知识图谱 ─────────────────────────────────────────────────

    def build_knowledge_graph(self, nodes: List[ExternalKnowledgeNode]) -> nx.DiGraph:
        """
        构建完整的知识图谱。

        Parameters
        ----------
        nodes : List[ExternalKnowledgeNode]
            所有外部知识节点。

        Returns
        -------
        nx.DiGraph
            知识图谱，节点为概念，边为相似度加权关联。
        """
        self._nodes = nodes
        self.knowledge_graph = nx.DiGraph()

        # 添加所有节点
        for node in nodes:
            self.knowledge_graph.add_node(
                node.concept,
                source=node.source,
                mapping=node.omni_hub_mapping,
                embedding=node.embedding.tolist(),
            )

        # 添加内部链接边
        for node in nodes:
            for link in node.internal_links:
                self.knowledge_graph.add_edge(
                    node.concept,
                    link,
                    relation="internal_link",
                    weight=0.9,
                )

        # 计算关联矩阵
        n = len(nodes)
        self.correlation_matrix = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(n):
                if i != j:
                    self.correlation_matrix[i, j] = nodes[i].compute_similarity(
                        nodes[j], method="cosine"
                    )

        return self.knowledge_graph

    # ── 5.3 找桥接概念 ───────────────────────────────────────────────────

    def find_bridges(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        找出跨文章的"桥接概念"——即与多个文章都有强关联的节点。

        Parameters
        ----------
        top_k : int
            返回前 k 个桥接概念。

        Returns
        -------
        List[Dict[str, Any]]
            桥接概念列表，按桥接强度排序。
        """
        if not self._nodes:
            return []

        bridges = []
        for node in self._nodes:
            # 统计该节点与其他文章的连接数
            cross_edges = []
            for neighbor in self.knowledge_graph.neighbors(node.concept):
                edge_data = self.knowledge_graph.get_edge_data(node.concept, neighbor)
                if edge_data and edge_data.get("source_a") != edge_data.get("source_b"):
                    cross_edges.append(edge_data)

            if len(cross_edges) >= 2:
                bridge_strength = sum(e.get("weight", 0) for e in cross_edges)
                bridges.append(
                    {
                        "concept": node.concept,
                        "source": node.source,
                        "bridge_strength": round(bridge_strength, 4),
                        "cross_connections": len(cross_edges),
                        "connected_to": [e.get("node_b", e.get("node_a", "")) for e in cross_edges],
                        "omni_hub_role": "knowledge_bridge::cross_article_integrator",
                    }
                )

        bridges.sort(key=lambda x: x["bridge_strength"], reverse=True)
        return bridges[:top_k]

    # ── 5.4 计算关联长度 ─────────────────────────────────────────────────

    def compute_correlation_length(self) -> Dict[str, Any]:
        """
        计算知识图谱的关联长度。

        关联长度定义为：在知识图谱中，信息/影响传播的平均最短路径长度，
        以及跨文章连接的"有效距离"。

        Returns
        -------
        Dict[str, Any]
            关联长度指标。
        """
        if self.knowledge_graph.number_of_nodes() == 0:
            return {"error": "Knowledge graph is empty"}

        # 将 DiGraph 转为无向图用于路径计算
        undirected = self.knowledge_graph.to_undirected()

        # 平均最短路径长度（仅对连通分量）
        try:
            avg_path_length = nx.average_shortest_path_length(undirected)
        except nx.NetworkXError:
            # 图不连通，计算各连通分量的平均
            components = list(nx.connected_components(undirected))
            avg_lengths = []
            for comp in components:
                if len(comp) > 1:
                    subgraph = undirected.subgraph(comp)
                    avg_lengths.append(nx.average_shortest_path_length(subgraph))
            avg_path_length = np.mean(avg_lengths) if avg_lengths else float("inf")

        # 直径
        try:
            diameter = nx.diameter(undirected)
        except nx.NetworkXError:
            diameter = max(
                nx.diameter(undirected.subgraph(c))
                for c in nx.connected_components(undirected)
                if len(c) > 1
            )

        # 聚类系数
        clustering = nx.average_clustering(undirected)

        # 跨文章关联的"有效关联长度"
        cross_edges = [
            (u, v, d)
            for u, v, d in self.knowledge_graph.edges(data=True)
            if d.get("source_a") != d.get("source_b")
        ]
        avg_cross_weight = (
            np.mean([d.get("weight", 0) for _, _, d in cross_edges])
            if cross_edges
            else 0.0
        )

        # 基于关联矩阵的关联长度（衰减长度）
        if self.correlation_matrix is not None:
            # 关联长度 ξ 定义为 C(r) ~ exp(-r/ξ) 的拟合参数
            # 简化：使用矩阵的奇异值衰减
            singular_values = np.linalg.svd(self.correlation_matrix, compute_uv=False)
            if len(singular_values) > 1 and singular_values[0] > 0:
                decay_rates = -np.log(singular_values[1:10] / singular_values[0] + 1e-12)
                correlation_length = 1.0 / np.mean(decay_rates[decay_rates > 0])
            else:
                correlation_length = float("inf")
        else:
            correlation_length = 0.0

        return {
            "average_path_length": round(avg_path_length, 4),
            "diameter": diameter,
            "average_clustering": round(clustering, 4),
            "cross_article_edges": len(cross_edges),
            "average_cross_article_weight": round(float(avg_cross_weight), 4),
            "correlation_length": round(float(correlation_length), 4),
            "interpretation": {
                "short_path": "Knowledge transfers efficiently across the graph",
                "high_clustering": "Local concepts form tightly knit communities",
                "long_correlation": "Long-range semantic coherence exists across articles",
            },
        }


# ═══════════════════════════════════════════════════════════════════════════
# 6. ExternalKnowledgeWeaver — 主类
# ═══════════════════════════════════════════════════════════════════════════

class ExternalKnowledgeWeaver:
    """
    外部知识编织器主类。

    整合所有编织组件，完成三篇文章知识到 OMNI-HUB 知识谱系的融合。

    Attributes
    ----------
    padic_weaver : PAdicCausalityWeaver
        p-adic 因果性编织器实例。
    mordell_lang_weaver : MordellLangWeaver
        莫德尔-朗编织器实例。
    rigidity_weaver : RigidityWeaver
        约束刚性编织器实例。
    correlation_detector : LongRangeCorrelationDetector
        长程关联检测器实例。
    knowledge_nodes : Dict[str, ExternalKnowledgeNode]
        所有知识节点，以 concept 为键。
    field_state : NDArray[np.float64]
        64 维知识场状态向量。
    """

    def __init__(
        self,
        padic_prime: int = 2,
        padic_depth: int = 6,
        ml_dimension: int = 2,
        rigidity_dim: int = 3,
        similarity_threshold: float = 0.35,
    ):
        self.padic_weaver = PAdicCausalityWeaver(prime=padic_prime, max_depth=padic_depth)
        self.mordell_lang_weaver = MordellLangWeaver(dimension=ml_dimension)
        self.rigidity_weaver = RigidityWeaver(constraint_dimension=rigidity_dim)
        self.correlation_detector = LongRangeCorrelationDetector(
            similarity_threshold=similarity_threshold
        )

        self.knowledge_nodes: Dict[str, ExternalKnowledgeNode] = {}
        self.field_state: NDArray[np.float64] = np.zeros(64, dtype=np.float64)
        self._weaved: bool = False
        self._long_range_correlations: List[Dict[str, Any]] = []

    # ── 6.1 摄入文章1 ────────────────────────────────────────────────────

    def ingest_article_1(self) -> List[ExternalKnowledgeNode]:
        """
        摄入文章1的知识节点。

        Returns
        -------
        List[ExternalKnowledgeNode]
            文章1的知识节点列表（≥10个）。
        """
        nodes = self.padic_weaver.generate_knowledge_nodes()
        for node in nodes:
            self.knowledge_nodes[node.concept] = node
        return nodes

    # ── 6.2 摄入文章2 ────────────────────────────────────────────────────

    def ingest_article_2(self) -> List[ExternalKnowledgeNode]:
        """
        摄入文章2的知识节点。

        Returns
        -------
        List[ExternalKnowledgeNode]
            文章2的知识节点列表（≥10个）。
        """
        nodes = self.mordell_lang_weaver.generate_knowledge_nodes()
        for node in nodes:
            self.knowledge_nodes[node.concept] = node
        return nodes

    # ── 6.3 摄入文章3 ────────────────────────────────────────────────────

    def ingest_article_3(self) -> List[ExternalKnowledgeNode]:
        """
        摄入文章3的知识节点。

        Returns
        -------
        List[ExternalKnowledgeNode]
            文章3的知识节点列表（≥10个）。
        """
        nodes = self.rigidity_weaver.generate_knowledge_nodes()
        for node in nodes:
            self.knowledge_nodes[node.concept] = node
        return nodes

    # ── 6.4 编织所有知识 ─────────────────────────────────────────────────

    def weave_all(self) -> Dict[str, Any]:
        """
        执行完整的知识编织流程。

        步骤：
        1. 初始化各编织器的内部结构
        2. 构建知识图谱
        3. 检测长程关联
        4. 计算知识场状态

        Returns
        -------
        Dict[str, Any]
            编织结果摘要。
        """
        # Step 1: 初始化各编织器
        self.padic_weaver.extract_hypergraph_rules()
        self.padic_weaver.build_padic_topology()
        self.padic_weaver.discrete_causality_model()
        self.padic_weaver.map_to_event_drive()
        self.padic_weaver.ruliad_index()

        self.mordell_lang_weaver.finiteness_principle()
        self.mordell_lang_weaver.uniform_bound()
        self.mordell_lang_weaver.gap_principle()
        self.mordell_lang_weaver.height_function()

        self.rigidity_weaver.combinatorial_rigidity()
        self.rigidity_weaver.geometric_rigidity()
        self.rigidity_weaver.categorical_rigidity()
        self.rigidity_weaver.analytic_rigidity()
        self.rigidity_weaver.attractor_dynamics()

        # Step 2: 构建知识图谱
        all_nodes = list(self.knowledge_nodes.values())
        self.correlation_detector.build_knowledge_graph(all_nodes)

        # Step 3: 检测长程关联
        self._long_range_correlations = self.correlation_detector.detect_across_articles()

        # Step 4: 计算知识场状态
        self._compute_field_state()

        self._weaved = True

        return {
            "status": "weaving_complete",
            "total_nodes": len(self.knowledge_nodes),
            "article_1_nodes": len([n for n in all_nodes if n.source == "article_1"]),
            "article_2_nodes": len([n for n in all_nodes if n.source == "article_2"]),
            "article_3_nodes": len([n for n in all_nodes if n.source == "article_3"]),
            "long_range_correlations": len(self._long_range_correlations),
            "correlation_length": self.correlation_detector.compute_correlation_length(),
        }

    def _compute_field_state(self) -> None:
        """
        计算 64 维知识场状态向量。

        向量由以下部分构成：
        - [0:16]   p-adic 因果性场分量
        - [16:32]  莫德尔-朗有限性场分量
        - [32:48]  约束刚性场分量
        - [48:56]  长程关联场分量
        - [56:64]  跨文章耦合场分量
        """
        state = np.zeros(64, dtype=np.float64)
        nodes = list(self.knowledge_nodes.values())

        if not nodes:
            self.field_state = state
            return

        # 计算每个文章的平均嵌入
        article_embeddings: Dict[str, List[NDArray[np.float64]]] = defaultdict(list)
        for node in nodes:
            article_embeddings[node.source].append(node.embedding)

        # [0:16] p-adic 场：文章1的平均嵌入前16维 + 拓扑指标
        if "article_1" in article_embeddings:
            emb = np.mean(article_embeddings["article_1"], axis=0)
            state[0:16] = emb[:16] if len(emb) >= 16 else np.pad(emb, (0, 16 - len(emb)))

        # [16:32] 莫德尔-朗场：文章2的平均嵌入前16维 + 高度指标
        if "article_2" in article_embeddings:
            emb = np.mean(article_embeddings["article_2"], axis=0)
            state[16:32] = emb[:16] if len(emb) >= 16 else np.pad(emb, (0, 16 - len(emb)))

        # [32:48] 刚性场：文章3的平均嵌入前16维 + 吸引子指标
        if "article_3" in article_embeddings:
            emb = np.mean(article_embeddings["article_3"], axis=0)
            state[32:48] = emb[:16] if len(emb) >= 16 else np.pad(emb, (0, 16 - len(emb)))

        # [48:56] 长程关联场：跨文章关联统计
        if self._long_range_correlations:
            sims = [c["similarity"] for c in self._long_range_correlations]
            state[48] = len(self._long_range_correlations) / 100.0
            state[49] = np.mean(sims)
            state[50] = np.std(sims) if len(sims) > 1 else 0.0
            state[51] = np.max(sims) if sims else 0.0
            state[52] = len(self.correlation_detector.find_bridges(10)) / 10.0
            state[53] = self.correlation_detector.compute_correlation_length().get(
                "average_clustering", 0.0
            )
            state[54] = self.correlation_detector.compute_correlation_length().get(
                "average_path_length", 0.0
            )
            state[55] = self.correlation_detector.compute_correlation_length().get(
                "correlation_length", 0.0
            )

        # [56:64] 跨文章耦合场：文章间耦合强度
        coupling = np.zeros(8, dtype=np.float64)
        for corr in self._long_range_correlations:
            pair = (corr["source_a"], corr["source_b"])
            if pair in [("article_1", "article_2"), ("article_2", "article_1")]:
                coupling[0] += corr["similarity"]
                coupling[1] += 1
            elif pair in [("article_1", "article_3"), ("article_3", "article_1")]:
                coupling[2] += corr["similarity"]
                coupling[3] += 1
            elif pair in [("article_2", "article_3"), ("article_3", "article_2")]:
                coupling[4] += corr["similarity"]
                coupling[5] += 1

        # 归一化
        for idx in [1, 3, 5]:
            if coupling[idx] > 0:
                coupling[idx - 1] /= coupling[idx]

        # 计算场的不平衡度和总能量
        coupling[6] = np.std([coupling[0], coupling[2], coupling[4]]) if any(
            [coupling[0], coupling[2], coupling[4]]
        ) else 0.0
        coupling[7] = np.sum([coupling[0], coupling[2], coupling[4]])

        state[56:64] = coupling
        self.field_state = state

    # ── 6.5 获取编织后的知识 ─────────────────────────────────────────────

    def get_weaved_knowledge(self) -> Dict[str, Any]:
        """
        获取编织后的完整知识结构。

        Returns
        -------
        Dict[str, Any]
            包含所有节点、关联和映射的知识结构。
        """
        if not self._weaved:
            self.weave_all()

        return {
            "nodes": {k: v.to_dict() for k, v in self.knowledge_nodes.items()},
            "long_range_correlations": self._long_range_correlations,
            "article_1_weaving": {
                "hypergraph_rules": self.padic_weaver.hypergraph_rules,
                "padic_topology_levels": len(self.padic_weaver.topology.get("levels", [])),
            },
            "article_2_weaving": {
                "finiteness_principle": self.mordell_lang_weaver.finiteness_principle(),
                "uniform_bound": self.mordell_lang_weaver.uniform_bound(),
            },
            "article_3_weaving": {
                "attractor_dynamics": self.rigidity_weaver.attractor_dynamics(),
                "rigidity_types": [
                    self.rigidity_weaver.combinatorial_rigidity()["rigidity_type"],
                    self.rigidity_weaver.geometric_rigidity()["rigidity_type"],
                    self.rigidity_weaver.categorical_rigidity()["rigidity_type"],
                    self.rigidity_weaver.analytic_rigidity()["rigidity_type"],
                ],
            },
        }

    # ── 6.6 获取长程关联 ─────────────────────────────────────────────────

    def get_long_range_correlations(self) -> List[Dict[str, Any]]:
        """
        获取检测到的长程关联。

        Returns
        -------
        List[Dict[str, Any]]
            长程关联列表。
        """
        if not self._weaved:
            self.weave_all()
        return self._long_range_correlations

    # ── 6.7 获取知识场状态 ───────────────────────────────────────────────

    def get_field_state(self) -> NDArray[np.float64]:
        """
        获取 64 维知识场状态向量。

        Returns
        -------
        NDArray[np.float64]
            64 维状态向量。
        """
        if not self._weaved:
            self.weave_all()
        return self.field_state

    # ── 6.8 建立内部-外部链接 ────────────────────────────────────────────

    def link_to_internal(
        self, concept: str, internal_node: str
    ) -> Optional[ExternalKnowledgeNode]:
        """
        将指定概念链接到 OMNI-HUB 内部节点。

        Parameters
        ----------
        concept : str
            外部知识概念名称。
        internal_node : str
            OMNI-HUB 内部节点名称。

        Returns
        -------
        ExternalKnowledgeNode or None
            更新后的节点，若概念不存在则返回 None。
        """
        node = self.knowledge_nodes.get(concept)
        if node:
            node.link_to_internal(internal_node)
            return node
        return None

    # ── 6.9 批量建立内部链接 ─────────────────────────────────────────────

    def batch_link_internal(self, links: List[Tuple[str, str]]) -> int:
        """
        批量建立内部-外部知识链接。

        Parameters
        ----------
        links : List[Tuple[str, str]]
            (concept, internal_node) 列表。

        Returns
        -------
        int
            成功建立的链接数量。
        """
        count = 0
        for concept, internal in links:
            if self.link_to_internal(concept, internal):
                count += 1
        return count




# ═══════════════════════════════════════════════════════════════════════════
# 7. 测试块
# ═══════════════════════════════════════════════════════════════════════════
"""
OMNI-HUB v11.0 — external_knowledge_weaver
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

if __name__ == "__main__":
    print("=" * 72)
    print("OMNI-HUB v8.0 — External Knowledge Weaver Test Suite")
    print("=" * 72)

    # ── 7.1 初始化编织器 ─────────────────────────────────────────────────
    print("\n[Phase 1] Initializing ExternalKnowledgeWeaver...")
    weaver = ExternalKnowledgeWeaver(
        padic_prime=2,
        padic_depth=4,
        ml_dimension=2,
        rigidity_dim=3,
        similarity_threshold=0.30,
    )
    print("  ✓ Weaver initialized with p=2, depth=4, threshold=0.30")

    # ── 7.2 摄入三篇文章 ─────────────────────────────────────────────────
    print("\n[Phase 2] Ingesting external knowledge from 3 articles...")

    nodes_1 = weaver.ingest_article_1()
    print(f"  ✓ Article 1 (p-adic causality): {len(nodes_1)} nodes ingested")
    for n in nodes_1[:3]:
        print(f"    - {n.concept} → {n.omni_hub_mapping}")

    nodes_2 = weaver.ingest_article_2()
    print(f"  ✓ Article 2 (Mordell-Lang): {len(nodes_2)} nodes ingested")
    for n in nodes_2[:3]:
        print(f"    - {n.concept} → {n.omni_hub_mapping}")

    nodes_3 = weaver.ingest_article_3()
    print(f"  ✓ Article 3 (Rigidity): {len(nodes_3)} nodes ingested")
    for n in nodes_3[:3]:
        print(f"    - {n.concept} → {n.omni_hub_mapping}")

    total_nodes = len(weaver.knowledge_nodes)
    print(f"\n  Total knowledge nodes: {total_nodes}")
    assert total_nodes >= 30, f"Expected ≥30 nodes, got {total_nodes}"

    # ── 7.3 建立内部-外部知识链接 ────────────────────────────────────────
    print("\n[Phase 3] Establishing internal-external knowledge links (≥15)...")
    internal_links = [
        ("p-adic_numbers", "omni_hub::topology::non_archimedean"),
        ("ultrametric_property", "omni_hub::metric::strong_triangle"),
        ("discrete_determinism", "omni_hub::computation::discrete_dynamics"),
        ("hypergraph_rewriting", "omni_hub::graph::hypergraph_transform"),
        ("ruliad_model", "omni_hub::meta::computational_universe"),
        ("causal_cone", "omni_hub::causality::future_cone"),
        ("non_archimedean_causality", "omni_hub::causality::discrete_order"),
        ("information_flow", "omni_hub::information::causal_flow"),
        ("mordell_lang_conjecture", "omni_hub::theorem::finiteness"),
        ("abelian_variety", "omni_hub::geometry::algebraic_group"),
        ("faltings_height", "omni_hub::invariant::complexity_measure"),
        ("uniformity_conjecture", "omni_hub::control::uniform_bounds"),
        ("gap_principle", "omni_hub::geometry::separation"),
        ("constraint_ontology", "omni_hub::ontology::constraints"),
        ("combinatorial_rigidity", "omni_hub::algebra::discrete_rigidity"),
        ("geometric_rigidity", "omni_hub::geometry::topological_determination"),
        ("rigidity_as_attractor", "omni_hub::dynamics::attractor"),
        ("self_organized_criticality", "omni_hub::criticality::soc"),
        ("monster_group", "omni_hub::symmetry::sporadic"),
        ("degree_of_freedom_collapse", "omni_hub::phase::dimension_collapse"),
    ]
    linked_count = weaver.batch_link_internal(internal_links)
    print(f"  ✓ {linked_count} internal-external links established")
    assert linked_count >= 15, f"Expected ≥15 links, got {linked_count}"

    # ── 7.4 执行完整编织 ─────────────────────────────────────────────────
    print("\n[Phase 4] Weaving all knowledge...")
    weave_result = weaver.weave_all()
    print(f"  ✓ Weaving complete")
    print(f"    - Total nodes: {weave_result['total_nodes']}")
    print(f"    - Article 1 nodes: {weave_result['article_1_nodes']}")
    print(f"    - Article 2 nodes: {weave_result['article_2_nodes']}")
    print(f"    - Article 3 nodes: {weave_result['article_3_nodes']}")
    print(f"    - Long-range correlations detected: {weave_result['long_range_correlations']}")

    # ── 7.5 检测跨文章长程关联 ───────────────────────────────────────────
    print("\n[Phase 5] Long-range correlation detection...")
    correlations = weaver.get_long_range_correlations()
    print(f"  ✓ Detected {len(correlations)} cross-article correlations")
    assert len(correlations) >= 5, f"Expected ≥5 correlations, got {len(correlations)}"

    print("\n  Top 8 correlations:")
    for i, corr in enumerate(correlations[:8], 1):
        print(
            f"    {i}. [{corr['source_a']}::{corr['node_a']}]"
            f" ↔ [{corr['source_b']}::{corr['node_b']}]"
            f" (sim={corr['similarity']:.4f}, type={corr['type']})"
        )

    # ── 7.6 计算关联长度 ─────────────────────────────────────────────────
    print("\n[Phase 6] Computing correlation length...")
    corr_length = weaver.correlation_detector.compute_correlation_length()
    print(f"  ✓ Correlation metrics:")
    for k, v in corr_length.items():
        if k != "interpretation":
            print(f"    - {k}: {v}")

    # ── 7.7 桥接概念 ─────────────────────────────────────────────────────
    print("\n[Phase 7] Bridge concepts (cross-article integrators)...")
    bridges = weaver.correlation_detector.find_bridges(top_k=5)
    print(f"  ✓ Found {len(bridges)} bridge concepts")
    for b in bridges:
        print(
            f"    - {b['concept']} ({b['source']}):"
            f" strength={b['bridge_strength']},"
            f" connections={b['cross_connections']}"
        )

    # ── 7.8 获取64维知识场状态 ──────────────────────────────────────────
    print("\n[Phase 8] Computing 64-dimensional knowledge field state...")
    field_state = weaver.get_field_state()
    print(f"  ✓ Field state shape: {field_state.shape}")
    print(f"  ✓ Field state dtype: {field_state.dtype}")

    # 分析场状态分量
    print("\n  Field components:")
    print(f"    [0:16]   p-adic causality field:     mean={field_state[0:16].mean():.4f}, std={field_state[0:16].std():.4f}")
    print(f"    [16:32]  Mordell-Lang field:         mean={field_state[16:32].mean():.4f}, std={field_state[16:32].std():.4f}")
    print(f"    [32:48]  Rigidity field:             mean={field_state[32:48].mean():.4f}, std={field_state[32:48].std():.4f}")
    print(f"    [48:56]  Long-range correlation:     mean={field_state[48:56].mean():.4f}, std={field_state[48:56].std():.4f}")
    print(f"    [56:64]  Cross-article coupling:     mean={field_state[56:64].mean():.4f}, std={field_state[56:64].std():.4f}")

    assert field_state.shape == (64,), f"Expected shape (64,), got {field_state.shape}"
    assert field_state.dtype == np.float64, f"Expected float64, got {field_state.dtype}"

    # ── 7.9 输出编织后的知识结构 ─────────────────────────────────────────
    print("\n[Phase 9] Weaved knowledge structure summary...")
    weaved = weaver.get_weaved_knowledge()
    print(f"  ✓ Total concepts in weaved structure: {len(weaved['nodes'])}")
    print(f"  ✓ Hypergraph rules: {len(weaved['article_1_weaving']['hypergraph_rules'])}")
    print(f"  ✓ p-adic topology levels: {weaved['article_1_weaving']['padic_topology_levels']}")
    print(f"  ✓ Rigidity types mapped: {weaved['article_3_weaving']['rigidity_types']}")

    # ── 7.10 各编织器内部状态验证 ────────────────────────────────────────
    print("\n[Phase 10] Per-weaver internal state verification...")

    # PAdic
    padic = weaver.padic_weaver
    print(f"  PAdicCausalityWeaver:")
    print(f"    - Hypergraph rules: {len(padic.hypergraph_rules)}")
    print(f"    - Topology levels: {len(padic.topology.get('levels', []))}")
    print(f"    - Causal states: {len(padic._causal_states)}")
    print(f"    - Event mappings: {len(padic._event_mappings.get('event_classes', []))} classes")

    # Mordell-Lang
    ml = weaver.mordell_lang_weaver
    print(f"  MordellLangWeaver:")
    print(f"    - Uniform bound: {ml._uniform_data.get('uniform_bound', 'N/A'):.2e}")
    print(f"    - Height example: {ml._finiteness_bounds.get('height_example', 'N/A'):.4f}")

    # Rigidity
    rig = weaver.rigidity_weaver
    print(f"  RigidityWeaver:")
    print(f"    - Initial DOF: {rig._attractor_state.get('initial_dof', 'N/A')}")
    print(f"    - Final DOF: {rig._attractor_state.get('final_dof', 'N/A'):.4f}")
    print(f"    - Attractor dimension: {rig._attractor_state.get('attractor_dimension', 'N/A')}")

    # ── 7.11 跨文章映射验证 ──────────────────────────────────────────────
    print("\n[Phase 11] Cross-article mapping verification...")
    print("  Core mappings:")
    print("    • p-adic causality ↔ Discrete determinism ↔ Event-driven:")
    print(f"      Event classes: {len(padic._event_mappings.get('event_classes', []))}")
    print("    • Mordell-Lang finiteness ↔ Knowledge node finite covering:")
    print(f"      Uniform bound ensures finite indexing")
    print("    • Rigidity ↔ System attractor ↔ Self-organized criticality:")
    print(f"      Attractor dimension = {rig._attractor_state.get('attractor_dimension', 'N/A')}")

    # ── 7.12 序列化测试 ──────────────────────────────────────────────────
    print("\n[Phase 12] Serialization test...")
    sample_node = nodes_1[0]
    node_dict = sample_node.to_dict()
    restored = ExternalKnowledgeNode.from_dict(node_dict)
    assert restored.concept == sample_node.concept
    assert np.allclose(restored.embedding, sample_node.embedding)
    print(f"  ✓ Serialization/deserialization verified for '{restored.concept}'")

    # ── 最终摘要 ─────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("TEST SUMMARY")
    print("=" * 72)
    print(f"✓ Total knowledge nodes:       {total_nodes} (requirement: ≥30)")
    print(f"✓ Internal-external links:     {linked_count} (requirement: ≥15)")
    print(f"✓ Long-range correlations:     {len(correlations)} (requirement: ≥5)")
    print(f"✓ Knowledge field state:       {field_state.shape} (requirement: 64-dim)")
    print(f"✓ Correlation length computed:  yes")
    print(f"✓ Bridge concepts found:        {len(bridges)}")
    print(f"✓ Weaved knowledge output:      yes")
    print("\nAll tests PASSED. External Knowledge Weaver is operational.")
    print("=" * 72)

