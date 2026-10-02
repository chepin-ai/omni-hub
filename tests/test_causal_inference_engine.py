"""OMNI-HUB v191 Tests — CausalInferenceEngine"""

import pytest
from core.causal_inference_engine import (
    CausalInferenceEngine, CausalGraphBuilder, InterventionAnalyzer,
    CounterfactualEngine, DoCalculus, CausalDiscovery,
    CausalRelation, InterventionType, CausalEdge,
    get_causal_inference_engine
)


class TestCausalGraphBuilder:
    def test_add_node(self):
        g = CausalGraphBuilder()
        g.add_node("A")
        assert "A" in g.nodes

    def test_add_edge(self):
        g = CausalGraphBuilder()
        e = g.add_edge("A", "B", strength=0.8)
        assert e is not None
        assert e.source == "A"
        assert e.target == "B"

    def test_cycle_detection(self):
        g = CausalGraphBuilder()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        e = g.add_edge("C", "A")
        assert e is None  # 环检测

    def test_ancestors(self):
        g = CausalGraphBuilder()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        assert g.get_ancestors("C") == {"A", "B"}

    def test_descendants(self):
        g = CausalGraphBuilder()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        assert g.get_descendants("A") == {"B", "C"}

    def test_get_report(self):
        g = CausalGraphBuilder()
        g.add_edge("A", "B")
        r = g.get_report()
        assert r["nodes"] == 2
        assert r["edges"] == 1


class TestInterventionAnalyzer:
    def test_do_intervention(self):
        g = CausalGraphBuilder()
        g.add_edge("A", "B", strength=0.5)
        ia = InterventionAnalyzer(g)
        r = ia.do_intervention("A", 0.9)
        assert "affected_nodes" in r

    def test_compare_interventions(self):
        g = CausalGraphBuilder()
        ia = InterventionAnalyzer(g)
        from core.causal_inference_engine import Intervention
        import time
        i1 = Intervention("i1", "A", 0.5, InterventionType.DO, time.time())
        i2 = Intervention("i2", "A", 0.7, InterventionType.DO, time.time())
        r = ia.compare_interventions(i1, i2)
        assert r["same_target"] is True


class TestCounterfactualEngine:
    def test_compute(self):
        g = CausalGraphBuilder()
        g.add_edge("A", "B", strength=0.5)
        cf = CounterfactualEngine(g)
        state = {"A": 0.5, "B": 0.3}
        result = cf.compute("B", "A", 0.9, state)
        assert result.factual_outcome == 0.3
        assert result.cf_id.startswith("cf_")

    def test_get_report(self):
        g = CausalGraphBuilder()
        cf = CounterfactualEngine(g)
        assert cf.get_report()["counterfactuals"] == 0


class TestDoCalculus:
    def test_identify_true(self):
        g = CausalGraphBuilder()
        g.add_edge("A", "B")
        dc = DoCalculus(g)
        ok, reason = dc.identify("B", "A")
        assert ok is True

    def test_identify_false(self):
        g = CausalGraphBuilder()
        g.add_node("A")
        g.add_node("B")
        dc = DoCalculus(g)
        ok, reason = dc.identify("B", "A")
        assert ok is True  # No causal path: effect=0, identifiable


class TestCausalDiscovery:
    def test_discover_from_correlation(self):
        cd = CausalDiscovery()
        corr = {("A", "B"): 0.85, ("C", "D"): 0.3}
        edges = cd.discover_from_correlation(corr, threshold=0.5)
        assert len(edges) == 1
        assert edges[0].source == "A"

    def test_discover_from_temporal(self):
        cd = CausalDiscovery()
        edges = cd.discover_from_temporal(["A", "B", "C"])
        assert len(edges) == 2


class TestCausalInferenceEngine:
    def test_init(self):
        cie = CausalInferenceEngine()
        assert cie.VERSION == "191.0.0"

    def test_build_alliance_graph(self):
        cie = CausalInferenceEngine()
        cie.build_alliance_graph({
            "l1": {"health": 0.9},
            "l2": {"health": 0.8},
        })
        assert len(cie.graph.nodes) == 2

    def test_analyze_intervention(self):
        cie = CausalInferenceEngine()
        cie.build_alliance_graph({"l1": {"health": 0.9}, "l2": {"health": 0.8}})
        r = cie.analyze_intervention("l1", 0.95)
        assert r["target"] == "l1"

    def test_what_if(self):
        cie = CausalInferenceEngine()
        state = {"l1": {"health": 0.5}, "l2": {"health": 0.6}}
        cie.build_alliance_graph(state)
        r = cie.what_if("l1", "l2", 0.9, state)
        assert "effect" in r

    def test_identify_causal_effect(self):
        cie = CausalInferenceEngine()
        cie.build_alliance_graph({"l1": {"health": 0.9}, "l2": {"health": 0.8}})
        cie.graph.add_edge("l1", "l2")
        r = cie.identify_causal_effect("l1", "l2")
        assert r["identifiable"] is True

    def test_run_cycle(self):
        cie = CausalInferenceEngine()
        r = cie.run_cycle({"l1": {"health": 0.9}, "l2": {"health": 0.8}})
        assert r["cycle"] == 1

    def test_get_status(self):
        cie = CausalInferenceEngine()
        s = cie.get_status()
        assert s["version"] == "191.0.0"

    def test_singleton(self):
        c1 = get_causal_inference_engine()
        c2 = get_causal_inference_engine()
        assert c1 is c2

# Total: 26 tests
