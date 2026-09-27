"""
OMNI-HUB Ontology Builder Tests v96
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.ontology_builder import (
    Concept, OntologyBuilder, get_ontology_builder,
)


class TestOntologyBuilder:
    def test_initialization(self):
        ob = OntologyBuilder()
        assert len(ob.concepts) == 0
        assert len(ob.relations) == 0

    def test_add_concept(self):
        ob = OntologyBuilder()
        ob.add_concept("system", "entity", [], {"alive": True})
        assert "system" in ob.concepts
        assert ob.concepts["system"].category == "entity"

    def test_add_relation(self):
        ob = OntologyBuilder()
        ob.add_relation("a", "depends_on", "b")
        assert len(ob.relations) == 1
        assert ob.relations[0]["source"] == "a"

    def test_build_system_ontology(self):
        ob = OntologyBuilder()
        ob.build_system_ontology({"level": 10, "energy": 2000})
        assert len(ob.concepts) > 20
        assert "system" in ob.concepts
        assert "consciousness" in ob.concepts

    def test_get_ancestors(self):
        ob = OntologyBuilder()
        ob.add_concept("root", "base", [])
        ob.add_concept("child", "derived", ["root"])
        ob.add_concept("grandchild", "derived", ["child"])
        ancestors = ob.get_ancestors("grandchild")
        assert "grandchild" in ancestors
        assert "child" in ancestors
        assert "root" in ancestors

    def test_get_related(self):
        ob = OntologyBuilder()
        ob.add_relation("a", "links", "b")
        ob.add_relation("c", "links", "a")
        related = ob.get_related("a")
        assert "b" in related
        assert "c" in related

    def test_get_status(self):
        ob = OntologyBuilder()
        ob.build_system_ontology({})
        status = ob.get_status()
        assert status["concepts"] > 20
        assert status["relations"] > 0
        assert "entity" in status["categories"]


class TestGlobalEngine:
    def test_get_ontology_builder(self):
        g = get_ontology_builder()
        assert g is not None
        assert isinstance(g, OntologyBuilder)
