"""
OMNI-HUB Semantic Network v47
Knowledge graph from causal discoveries.

Knowledge is not a pile of facts. It is a web of connections.
This module builds a persistent graph from all system discoveries.

Philosophy: 知识即结构 — Knowledge is structure.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib


@dataclass
class ConceptNode:
    """A node in the semantic network."""
    id: str
    label: str
    node_type: str  # 'state', 'module', 'line', 'phase', 'concept'
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: int = 0


@dataclass
class RelationEdge:
    """An edge connecting two concepts."""
    source: str
    target: str
    relation_type: str  # 'causes', 'precedes', 'associates', 'activates', 'inhibits'
    strength: float = 0.5
    evidence_count: int = 1
    created_at: int = 0


class SemanticNetwork:
    """
    Persistent knowledge graph of system understanding.
    """

    def __init__(self):
        self.nodes: Dict[str, ConceptNode] = {}
        self.edges: Dict[str, List[RelationEdge]] = defaultdict(list)
        self.reverse_edges: Dict[str, List[RelationEdge]] = defaultdict(list)
        self.query_count = 0
        self.discovery_count = 0

    def _node_id(self, label: str, node_type: str) -> str:
        """Generate stable node ID."""
        return hashlib.md5(f"{node_type}:{label}".encode()).hexdigest()[:12]

    def add_concept(self, label: str, node_type: str, properties: Dict[str, Any] = None, cycle: int = 0) -> str:
        """Add a concept node."""
        nid = self._node_id(label, node_type)
        if nid not in self.nodes:
            self.nodes[nid] = ConceptNode(
                id=nid, label=label, node_type=node_type,
                properties=properties or {}, created_at=cycle,
            )
        return nid

    def add_relation(self, source_label: str, target_label: str, relation_type: str,
                     source_type: str = "state", target_type: str = "state",
                     strength: float = 0.5, cycle: int = 0) -> None:
        """Add a relation between two concepts."""
        sid = self.add_concept(source_label, source_type, cycle=cycle)
        tid = self.add_concept(target_label, target_type, cycle=cycle)

        edge = RelationEdge(source=sid, target=tid, relation_type=relation_type,
                           strength=strength, created_at=cycle)
        self.edges[sid].append(edge)
        self.reverse_edges[tid].append(edge)
        self.discovery_count += 1

    def ingest_causal_links(self, links: List[Any], cycle: int = 0) -> int:
        """Ingest causal links from the causal inference engine."""
        added = 0
        for link in links:
            if hasattr(link, 'cause') and hasattr(link, 'effect'):
                self.add_relation(
                    link.cause, link.effect, "causes",
                    source_type="state", target_type="state",
                    strength=getattr(link, 'strength', 0.5),
                    cycle=cycle,
                )
                # Also add bidirectional if strong
                if getattr(link, 'strength', 0) > 0.7:
                    self.add_relation(
                        link.effect, link.cause, "associates",
                        source_type="state", target_type="state",
                        strength=getattr(link, 'strength', 0.5) * 0.5,
                        cycle=cycle,
                    )
                added += 1
        return added

    def find_paths(self, source_label: str, target_label: str, max_depth: int = 3) -> List[List[str]]:
        """Find all paths between two concepts."""
        sid = self._node_id(source_label, "state")
        tid = self._node_id(target_label, "state")

        if sid not in self.nodes or tid not in self.nodes:
            return []

        paths = []
        visited = set()

        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current == tid and len(path) > 1:
                paths.append(path[:])
                return
            for edge in self.edges.get(current, []):
                if edge.target not in visited:
                    visited.add(edge.target)
                    node = self.nodes.get(edge.target)
                    if node:
                        path.append(node.label)
                        dfs(edge.target, path, depth + 1)
                        path.pop()
                    visited.remove(edge.target)

        visited.add(sid)
        dfs(sid, [self.nodes[sid].label], 0)
        self.query_count += 1
        return paths

    def get_neighbors(self, label: str, node_type: str = "state", relation_filter: str = None) -> List[Dict[str, Any]]:
        """Get neighbors of a concept."""
        nid = self._node_id(label, node_type)
        if nid not in self.nodes:
            return []

        result = []
        for edge in self.edges.get(nid, []):
            if relation_filter and edge.relation_type != relation_filter:
                continue
            target = self.nodes.get(edge.target)
            if target:
                result.append({
                    "label": target.label,
                    "type": target.node_type,
                    "relation": edge.relation_type,
                    "strength": edge.strength,
                })
        return result

    def get_central_concepts(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get most connected concepts (degree centrality)."""
        degrees = {}
        for nid, node in self.nodes.items():
            out_deg = len(self.edges.get(nid, []))
            in_deg = len(self.reverse_edges.get(nid, []))
            degrees[nid] = out_deg + in_deg

        sorted_nodes = sorted(degrees.items(), key=lambda x: -x[1])[:top_n]
        return [
            {"label": self.nodes[nid].label, "type": self.nodes[nid].node_type, "degree": deg}
            for nid, deg in sorted_nodes
        ]

    def get_status(self) -> Dict[str, Any]:
        return {
            "nodes": len(self.nodes),
            "edges": sum(len(e) for e in self.edges.values()),
            "discoveries": self.discovery_count,
            "queries": self.query_count,
            "central": self.get_central_concepts(3),
        }


_sn_engine = None

def get_semantic_network():
    global _sn_engine
    if _sn_engine is None:
        _sn_engine = SemanticNetwork()
    return _sn_engine
