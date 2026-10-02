"""OMNI-HUB v189 Tests — CognitiveTopology"""

import pytest
from core.cognitive_topology import (
    CognitiveTopology, TopologyMapper, DimensionReducer, SimilarityMatrix,
    ClusterAnalyzer, ProjectionEngine,
    TopologyNode, ReducedSpace, SimilarityPair, Cluster, Projection,
    ProjectionType, ClusterMethod, ALLIANCE_LINES,
    get_cognitive_topology
)


class TestTopologyMapper:
    def test_map_from_state(self):
        tm = TopologyMapper()
        nodes = tm.map_from_state({"l1": {"health": 0.9, "load": 0.5}})
        assert "l1" in nodes
        assert len(nodes["l1"].coordinates) == 12

    def test_connect_by_similarity(self):
        tm = TopologyMapper()
        tm.map_from_state({
            "l1": {"a": 1.0, "b": 0.0},
            "l2": {"a": 0.9, "b": 0.1},
            "l3": {"a": 0.1, "b": 0.9},
        })
        tm.connect_by_similarity(threshold=0.5)
        assert len(tm.nodes["l1"].connections) > 0

    def test_get_report(self):
        tm = TopologyMapper()
        tm.map_from_state({"l1": {"a": 1}})
        r = tm.get_report()
        assert r["nodes"] == 1


class TestDimensionReducer:
    def test_reduce(self):
        dr = DimensionReducer(target_dim=2)
        r = dr.reduce({"a": [1.0, 2.0, 3.0], "b": [2.0, 3.0, 4.0]})
        assert r.reduced_dim == 2
        assert len(r.points) == 2

    def test_empty(self):
        dr = DimensionReducer()
        r = dr.reduce({})
        assert r.reduced_dim == 3

    def test_get_report(self):
        dr = DimensionReducer()
        dr.reduce({"a": [1.0]})
        r = dr.get_report()
        assert r["spaces"] == 1


class TestSimilarityMatrix:
    def test_compute(self):
        sm = SimilarityMatrix()
        m = sm.compute({"a": [1.0, 0.0], "b": [0.9, 0.1]}, metric="cosine")
        assert ("a", "b") in m
        assert m[("a", "b")] > 0.9

    def test_most_similar(self):
        sm = SimilarityMatrix()
        sm.compute({"a": [1.0, 0], "b": [0.9, 0.1], "c": [0, 1.0]}, metric="cosine")
        sims = sm.get_most_similar("a", top_k=1)
        assert len(sims) == 1
        assert sims[0][0] == "b"

    def test_get_report(self):
        sm = SimilarityMatrix()
        sm.compute({"a": [1.0], "b": [1.0]})
        r = sm.get_report()
        assert r["pairs"] > 0


class TestClusterAnalyzer:
    def test_cluster(self):
        ca = ClusterAnalyzer()
        data = {
            "a": [0.0, 0.0], "b": [0.1, 0.1], "c": [0.2, 0.0],
            "x": [10.0, 10.0], "y": [10.1, 10.1], "z": [9.9, 10.0],
        }
        clusters = ca.cluster(data, k=2)
        assert len(clusters) == 2

    def test_insufficient_data(self):
        ca = ClusterAnalyzer()
        clusters = ca.cluster({"a": [1.0]}, k=2)
        assert len(clusters) == 0

    def test_get_report(self):
        ca = ClusterAnalyzer()
        ca.cluster({"a": [0.0], "b": [1.0], "c": [2.0]}, k=2)
        r = ca.get_report()
        assert "clusters" in r


class TestProjectionEngine:
    def test_project_cartesian(self):
        pe = ProjectionEngine()
        p = pe.project({"a": [1.0, 2.0], "b": [3.0, 4.0]}, ProjectionType.CARTESIAN)
        assert len(p.points) == 2
        assert "a" in p.points

    def test_project_polar(self):
        pe = ProjectionEngine()
        p = pe.project({"a": [1.0, 0.0]}, ProjectionType.POLAR)
        assert len(p.points) == 1

    def test_get_report(self):
        pe = ProjectionEngine()
        pe.project({"a": [1.0]}, ProjectionType.CARTESIAN)
        r = pe.get_report()
        assert r["projections"] == 1


class TestCognitiveTopology:
    def test_init(self):
        ct = CognitiveTopology()
        assert ct.VERSION == "189.0.0"

    def test_map_alliance(self):
        ct = CognitiveTopology()
        state = {line: {"health": 0.7 + i * 0.02, "active": True}
                 for i, line in enumerate(ALLIANCE_LINES[:4])}
        r = ct.map_alliance(state)
        assert r["nodes"] == 4
        assert "clusters" in r

    def test_run_cycle(self):
        ct = CognitiveTopology()
        r = ct.run_cycle()
        assert r["cycle"] == 1
        assert r["nodes_mapped"] == 12

    def test_get_status(self):
        ct = CognitiveTopology()
        ct.run_cycle()
        s = ct.get_status()
        assert s["version"] == "189.0.0"

    def test_singleton(self):
        c1 = get_cognitive_topology()
        c2 = get_cognitive_topology()
        assert c1 is c2

# Total: 29 tests
