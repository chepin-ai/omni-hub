"""
OMNI-HUB Architectural Evolution Tests v73
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.architectural_evolution import (
    StructuralChange, ArchitecturalEvolution, get_architectural_evolution,
)


class TestArchitecturalEvolution:
    def test_initialization(self):
        ae = ArchitecturalEvolution()
        assert len(ae.module_graph) > 0
        assert ae.change_count == 0

    def test_analyze_structure_new_module(self):
        ae = ArchitecturalEvolution()
        state = {"symbolic_reasoning": {"inferences": 5}}
        proposals = ae.analyze_structure(state)
        assert len(proposals) > 0
        assert any(p.change_type == "add_link" for p in proposals)

    def test_analyze_structure_strengthen(self):
        ae = ArchitecturalEvolution()
        state = {
            "capability_assessment": {
                "scores": {"self_awareness": 0.9}
            }
        }
        proposals = ae.analyze_structure(state)
        # Should propose strengthening for high capability
        assert any(p.change_type == "strengthen" for p in proposals)

    def test_capability_to_module(self):
        ae = ArchitecturalEvolution()
        assert ae._capability_to_module("learning") == "learning"
        assert ae._capability_to_module("memory") == "recursive_self_model"
        assert ae._capability_to_module("unknown") is None

    def test_get_graph_stats(self):
        ae = ArchitecturalEvolution()
        stats = ae.get_graph_stats()
        assert "nodes" in stats
        assert "edges" in stats
        assert stats["nodes"] > 0

    def test_get_status(self):
        ae = ArchitecturalEvolution()
        state = {"symbolic_reasoning": {"inferences": 5}}
        ae.analyze_structure(state)
        status = ae.get_status()
        assert "nodes" in status
        assert "changes_proposed" in status
        assert status["changes_proposed"] > 0


class TestGlobalEngine:
    def test_get_architectural_evolution(self):
        g = get_architectural_evolution()
        assert g is not None
        assert isinstance(g, ArchitecturalEvolution)
