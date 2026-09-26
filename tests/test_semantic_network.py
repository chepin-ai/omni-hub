"""
OMNI-HUB Semantic Network Tests v47
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.semantic_network import (
    ConceptNode, RelationEdge, SemanticNetwork, get_semantic_network,
)


class TestSemanticNetwork:
    def test_initialization(self):
        sn = SemanticNetwork()
        assert len(sn.nodes) == 0
        assert len(sn.edges) == 0

    def test_add_concept(self):
        sn = SemanticNetwork()
        nid = sn.add_concept("level", "state", {"range": "0-25"})
        assert nid in sn.nodes
        assert sn.nodes[nid].label == "level"

    def test_add_relation(self):
        sn = SemanticNetwork()
        sn.add_relation("level", "energy", "causes", strength=0.8)
        assert len(sn.edges) > 0

    def test_ingest_causal_links(self):
        sn = SemanticNetwork()

        class MockLink:
            def __init__(self, cause, effect, strength):
                self.cause = cause
                self.effect = effect
                self.strength = strength

        links = [MockLink("level", "energy", 0.8), MockLink("phi", "coherence", 0.6)]
        added = sn.ingest_causal_links(links, cycle=100)
        assert added == 2
        assert len(sn.nodes) >= 4

    def test_find_paths(self):
        sn = SemanticNetwork()
        sn.add_relation("a", "b", "causes")
        sn.add_relation("b", "c", "causes")
        paths = sn.find_paths("a", "c", max_depth=3)
        assert len(paths) > 0
        assert paths[0] == ["a", "b", "c"]

    def test_find_paths_no_path(self):
        sn = SemanticNetwork()
        sn.add_relation("a", "b", "causes")
        sn.add_relation("x", "y", "causes")
        paths = sn.find_paths("a", "y")
        assert len(paths) == 0

    def test_get_neighbors(self):
        sn = SemanticNetwork()
        sn.add_relation("level", "energy", "causes", strength=0.8)
        neighbors = sn.get_neighbors("level")
        assert len(neighbors) == 1
        assert neighbors[0]["label"] == "energy"

    def test_get_central_concepts(self):
        sn = SemanticNetwork()
        sn.add_relation("level", "energy", "causes")
        sn.add_relation("level", "phi", "causes")
        sn.add_relation("energy", "phi", "causes")
        central = sn.get_central_concepts(top_n=2)
        assert len(central) == 2
        assert central[0]["label"] == "level"

    def test_get_status(self):
        sn = SemanticNetwork()
        sn.add_concept("test", "state")
        status = sn.get_status()
        assert status["nodes"] == 1
        assert "discoveries" in status


class TestGlobalEngine:
    def test_get_semantic_network(self):
        g = get_semantic_network()
        assert g is not None
        assert isinstance(g, SemanticNetwork)
