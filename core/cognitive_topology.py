"""
OMNI-HUB v189 — CognitiveTopology
认知拓扑映射

核心功能：
1. TopologyMapper       — 拓扑映射器
2. DimensionReducer     — 降维器
3. SimilarityMatrix     — 相似度矩阵
4. ClusterAnalyzer      — 聚类分析器
5. ProjectionEngine     — 投影引擎
6. CognitiveTopology    — 统合引擎

映射：
- 拓扑 = maṇḍala（曼荼罗/坛城）
- 认知 = vijñāna（识）
- 空间 = ākāśa（空）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

ALLIANCE_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
    "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"
]


class ProjectionType(Enum):
    """投影类型"""
    CARTESIAN = 0
    POLAR = 1
    RADIAL = 2
    FORCE_DIRECTED = 3


class ClusterMethod(Enum):
    """聚类方法"""
    K_MEANS = 0
    HIERARCHICAL = 1
    DENSITY = 2
    SPECTRAL = 3


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class TopologyNode:
    """拓扑节点"""
    node_id: str
    coordinates: List[float]
    metadata: Dict[str, Any]
    connections: List[str]


@dataclass
class ReducedSpace:
    """降维空间"""
    space_id: str
    original_dim: int
    reduced_dim: int
    points: Dict[str, List[float]]
    variance_retained: float


@dataclass
class SimilarityPair:
    """相似度对"""
    pair_id: str
    entity_a: str
    entity_b: str
    similarity: float
    metric: str


@dataclass
class Cluster:
    """聚类"""
    cluster_id: str
    members: List[str]
    centroid: List[float]
    cohesion: float
    label: str = ""


@dataclass
class Projection:
    """投影"""
    projection_id: str
    projection_type: ProjectionType
    points: Dict[str, List[float]]
    bounds: Tuple[float, float, float, float]


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 拓扑映射器
# ═══════════════════════════════════════════════════════════════

class TopologyMapper:
    """拓扑映射器 — maṇḍala"""

    def __init__(self, dimensions: int = 12):
        self.dimensions = dimensions
        self.nodes: Dict[str, TopologyNode] = {}

    def map_from_state(self, state: Dict[str, Dict]) -> Dict[str, TopologyNode]:
        """从系统状态映射到拓扑节点"""
        for line_id, line_state in state.items():
            vec = self._state_to_vector(line_state)
            self.nodes[line_id] = TopologyNode(
                node_id=line_id,
                coordinates=vec,
                metadata=line_state,
                connections=[]
            )
        return self.nodes

    def _state_to_vector(self, state: Dict) -> List[float]:
        """将状态转换为向量"""
        keys = sorted(state.keys())
        vec = []
        for k in keys:
            v = state[k]
            if isinstance(v, (int, float)):
                vec.append(float(v))
            elif isinstance(v, bool):
                vec.append(1.0 if v else 0.0)
            elif isinstance(v, str):
                vec.append(sum(ord(c) for c in v) % 100 / 100.0)
            else:
                vec.append(0.5)
        # Pad or truncate to dimensions
        while len(vec) < self.dimensions:
            vec.append(0.0)
        return vec[:self.dimensions]

    def connect_by_similarity(self, threshold: float = 0.7):
        """基于相似度建立连接"""
        lines = list(self.nodes.keys())
        for i, a in enumerate(lines):
            self.nodes[a].connections = []
            for b in lines[i+1:]:
                sim = self._cosine_similarity(
                    self.nodes[a].coordinates,
                    self.nodes[b].coordinates
                )
                if sim >= threshold:
                    self.nodes[a].connections.append(b)
                    self.nodes[b].connections.append(a)

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1)) or 1.0
        norm2 = math.sqrt(sum(b * b for b in v2)) or 1.0
        return dot / (norm1 * norm2)

    def get_report(self) -> Dict:
        total_conn = sum(len(n.connections) for n in self.nodes.values())
        return {
            "nodes": len(self.nodes),
            "total_connections": total_conn,
            "avg_degree": total_conn / max(1, len(self.nodes)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 降维器
# ═══════════════════════════════════════════════════════════════

class DimensionReducer:
    """降维器 — 简化版PCA"""

    def __init__(self, target_dim: int = 3):
        self.target_dim = target_dim
        self.spaces: deque = deque(maxlen=100)

    def reduce(self, data: Dict[str, List[float]]) -> ReducedSpace:
        """降维到目标维度"""
        if not data:
            return ReducedSpace("empty", 0, self.target_dim, {}, 0.0)

        entities = list(data.keys())
        vectors = [data[e] for e in entities]
        original_dim = len(vectors[0])

        # 均值中心化
        means = [sum(v[i] for v in vectors) / len(vectors) for i in range(original_dim)]
        centered = [[v[i] - means[i] for i in range(original_dim)] for v in vectors]

        # 简化：直接取前target_dim个维度（实际应做SVD）
        reduced = {}
        for e, vec in zip(entities, centered):
            reduced[e] = vec[:self.target_dim]
            while len(reduced[e]) < self.target_dim:
                reduced[e].append(0.0)

        # 估算保留方差（简化）
        variance_retained = min(1.0, self.target_dim / max(1, original_dim))

        space = ReducedSpace(
            space_id=f"space_{int(time.time()*1000)}",
            original_dim=original_dim,
            reduced_dim=self.target_dim,
            points=reduced,
            variance_retained=variance_retained
        )
        self.spaces.append(space)
        return space

    def get_report(self) -> Dict:
        if not self.spaces:
            return {"spaces": 0}
        recent = list(self.spaces)[-10:]
        return {
            "spaces": len(self.spaces),
            "avg_variance_retained": sum(s.variance_retained for s in recent) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 相似度矩阵
# ═══════════════════════════════════════════════════════════════

class SimilarityMatrix:
    """相似度矩阵"""

    def __init__(self):
        self.matrix: Dict[Tuple[str, str], float] = {}
        self.pairs: deque = deque(maxlen=500)

    def compute(self, data: Dict[str, List[float]], metric: str = "cosine") -> Dict[Tuple[str, str], float]:
        """计算相似度矩阵"""
        entities = list(data.keys())
        for i, a in enumerate(entities):
            for b in entities[i:]:
                if metric == "cosine":
                    sim = self._cosine(data[a], data[b])
                elif metric == "euclidean":
                    sim = self._euclidean_similarity(data[a], data[b])
                else:
                    sim = self._pearson(data[a], data[b])

                self.matrix[(a, b)] = sim
                self.matrix[(b, a)] = sim
                self.pairs.append(SimilarityPair(
                    pair_id=f"pair_{a}_{b}",
                    entity_a=a,
                    entity_b=b,
                    similarity=sim,
                    metric=metric
                ))
        return self.matrix

    def _cosine(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1)) or 1.0
        n2 = math.sqrt(sum(b * b for b in v2)) or 1.0
        return dot / (n1 * n2)

    def _euclidean_similarity(self, v1: List[float], v2: List[float]) -> float:
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
        return 1.0 / (1.0 + dist)

    def _pearson(self, v1: List[float], v2: List[float]) -> float:
        if len(v1) != len(v2) or len(v1) == 0:
            return 0.0
        m1, m2 = sum(v1) / len(v1), sum(v2) / len(v2)
        num = sum((a - m1) * (b - m2) for a, b in zip(v1, v2))
        den = math.sqrt(sum((a - m1) ** 2 for a in v1)) * math.sqrt(sum((b - m2) ** 2 for b in v2))
        return num / den if den != 0 else 0.0

    def get_most_similar(self, entity: str, top_k: int = 3) -> List[Tuple[str, float]]:
        pairs = [(b, sim) for (a, b), sim in self.matrix.items() if a == entity and a != b]
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_k]

    def get_report(self) -> Dict:
        if not self.pairs:
            return {"pairs": 0}
        sims = [p.similarity for p in self.pairs]
        return {
            "pairs": len(self.pairs),
            "avg_similarity": sum(sims) / len(sims),
            "max_similarity": max(sims) if sims else 0,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 聚类分析器
# ═══════════════════════════════════════════════════════════════

class ClusterAnalyzer:
    """聚类分析器"""

    def __init__(self, method: ClusterMethod = ClusterMethod.K_MEANS):
        self.method = method
        self.clusters: deque = deque(maxlen=100)

    def cluster(self, data: Dict[str, List[float]], k: int = 3) -> List[Cluster]:
        """K-Means简化版聚类"""
        if not data or len(data) < k:
            return []

        entities = list(data.keys())
        vectors = [data[e] for e in entities]
        dim = len(vectors[0])

        # 随机初始化中心点
        centroids = vectors[:k]
        assignments = {}

        for iteration in range(10):
            # 分配
            new_assignments = {}
            for e, vec in zip(entities, vectors):
                best_c = min(range(k), key=lambda c: self._distance(vec, centroids[c]))
                new_assignments[e] = best_c

            # 更新中心
            for c in range(k):
                members = [vectors[i] for i, e in enumerate(entities) if new_assignments[e] == c]
                if members:
                    centroids[c] = [sum(m[i] for m in members) / len(members) for i in range(dim)]

            if new_assignments == assignments:
                break
            assignments = new_assignments

        # 构建Cluster对象
        result = []
        for c in range(k):
            members = [e for e in entities if assignments.get(e) == c]
            if members:
                cohesion = self._compute_cohesion([data[e] for e in members], centroids[c])
                cluster = Cluster(
                    cluster_id=f"cluster_{c}_{int(time.time()*1000)}",
                    members=members,
                    centroid=centroids[c],
                    cohesion=cohesion,
                    label=f"cluster_{c}"
                )
                result.append(cluster)
                self.clusters.append(cluster)

        return result

    def _distance(self, v1: List[float], v2: List[float]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    def _compute_cohesion(self, members: List[List[float]], centroid: List[float]) -> float:
        if not members:
            return 0.0
        avg_dist = sum(self._distance(m, centroid) for m in members) / len(members)
        return 1.0 / (1.0 + avg_dist)

    def get_report(self) -> Dict:
        if not self.clusters:
            return {"clusters": 0}
        recent = list(self.clusters)[-10:]
        return {
            "clusters": len(self.clusters),
            "avg_cohesion": sum(c.cohesion for c in recent) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 投影引擎
# ═══════════════════════════════════════════════════════════════

class ProjectionEngine:
    """投影引擎"""

    def __init__(self):
        self.projections: deque = deque(maxlen=100)

    def project(self, data: Dict[str, List[float]], ptype: ProjectionType = ProjectionType.CARTESIAN) -> Projection:
        """投影到2D空间"""
        points = {}
        for eid, vec in data.items():
            if ptype == ProjectionType.POLAR:
                r = math.sqrt(sum(v * v for v in vec[:2])) if len(vec) >= 2 else 0.5
                theta = math.atan2(vec[1], vec[0]) if len(vec) >= 2 else 0
                x, y = r * math.cos(theta), r * math.sin(theta)
            elif ptype == ProjectionType.RADIAL:
                angle = hash(eid) % 360 / 180.0 * math.pi
                r = sum(v for v in vec[:2]) / 2.0 if vec else 0.5
                x, y = r * math.cos(angle), r * math.sin(angle)
            else:
                x = vec[0] if len(vec) > 0 else 0.5
                y = vec[1] if len(vec) > 1 else 0.5
            points[eid] = [x, y]

        xs = [p[0] for p in points.values()]
        ys = [p[1] for p in points.values()]
        bounds = (min(xs), max(xs), min(ys), max(ys)) if xs else (0, 1, 0, 1)

        proj = Projection(
            projection_id=f"proj_{int(time.time()*1000)}",
            projection_type=ptype,
            points=points,
            bounds=bounds
        )
        self.projections.append(proj)
        return proj

    def get_report(self) -> Dict:
        return {
            "projections": len(self.projections),
            "types": list(set(p.projection_type.name for p in self.projections)),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — CognitiveTopology v189
# ═══════════════════════════════════════════════════════════════

class CognitiveTopology:
    """
    OMNI-HUB v189 认知拓扑映射

    maṇḍala · vijñāna · ākāśa — 坛城、识、空
    """

    VERSION = "189.0.0"

    def __init__(self):
        self.topology = TopologyMapper()
        self.reducer = DimensionReducer(target_dim=3)
        self.similarity = SimilarityMatrix()
        self.cluster = ClusterAnalyzer()
        self.projection = ProjectionEngine()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def map_alliance(self, alliance_state: Dict[str, Dict]) -> Dict:
        """映射整个联盟的认知拓扑"""
        # 1. 拓扑映射
        nodes = self.topology.map_from_state(alliance_state)
        self.topology.connect_by_similarity(threshold=0.6)

        # 2. 提取向量
        vectors = {nid: n.coordinates for nid, n in nodes.items()}

        # 3. 相似度矩阵
        sim_matrix = self.similarity.compute(vectors, metric="cosine")

        # 4. 降维
        reduced = self.reducer.reduce(vectors)

        # 5. 聚类
        clusters = self.cluster.cluster(reduced.points, k=3)

        # 6. 投影
        proj = self.projection.project(reduced.points, ProjectionType.POLAR)

        # 7. 找最相似的线对
        most_similar = {}
        for line in vectors:
            sims = self.similarity.get_most_similar(line, top_k=2)
            most_similar[line] = sims

        return {
            "nodes": len(nodes),
            "connections": self.topology.get_report()["total_connections"],
            "reduced_dim": reduced.reduced_dim,
            "variance_retained": reduced.variance_retained,
            "clusters": len(clusters),
            "cluster_cohesion_avg": sum(c.cohesion for c in clusters) / max(1, len(clusters)),
            "most_similar_pairs": most_similar,
            "projection_bounds": proj.bounds,
        }

    def run_cycle(self, alliance_state: Dict[str, Dict] = None) -> Dict:
        """运行完整映射周期"""
        self.cycle_count += 1
        alliance_state = alliance_state or {line: {"health": 0.7 + i * 0.02, "load": 0.5}
                                             for i, line in enumerate(ALLIANCE_LINES)}

        result = self.map_alliance(alliance_state)

        summary = {
            "cycle": self.cycle_count,
            "nodes_mapped": result["nodes"],
            "clusters_found": result["clusters"],
            "variance_retained": result["variance_retained"],
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "topology": self.topology.get_report(),
            "reducer": self.reducer.get_report(),
            "similarity": self.similarity.get_report(),
            "cluster": self.cluster.get_report(),
            "projection": self.projection.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ct_instance: Optional[CognitiveTopology] = None


def get_cognitive_topology() -> CognitiveTopology:
    global _ct_instance
    if _ct_instance is None:
        _ct_instance = CognitiveTopology()
    return _ct_instance


if __name__ == "__main__":
    ct = CognitiveTopology()
    print(f"CognitiveTopology v{ct.VERSION} initialized")
    print(f"Status: {json.dumps(ct.get_status(), indent=2, default=str)}")
