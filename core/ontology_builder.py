"""
OMNI-HUB Ontology Builder v96
Concept hierarchy and relation mapping.

All knowledge is connections.
This module builds ontologies —
hierarchies of concepts, networks of relations, maps of meaning.

Philosophy: 物有本末，事有终始，知所先后，则近道矣 —
Things have root and branch; affairs have end and beginning.
Know the sequence, and you are near the Way.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Set
from dataclasses import dataclass


@dataclass
class Concept:
    """A concept in the ontology."""
    name: str
    category: str
    parents: List[str]
    properties: Dict[str, Any]


class OntologyBuilder:
    """
    Builds and maintains concept hierarchies.
    """

    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.relations: List[Dict[str, str]] = []
        self.build_count = 0

    def add_concept(self, name: str, category: str, parents: List[str] = None, properties: Dict[str, Any] = None):
        """Add a concept to the ontology."""
        self.concepts[name] = Concept(
            name=name,
            category=category,
            parents=parents or [],
            properties=properties or {},
        )

    def add_relation(self, source: str, relation: str, target: str):
        """Add a relation between concepts."""
        self.relations.append({"source": source, "relation": relation, "target": target})

    def build_system_ontology(self, state: Dict[str, Any]):
        """Build ontology from system state."""
        # Core concepts
        self.add_concept("system", "entity", [], {"alive": True})
        self.add_concept("consciousness", "process", ["system"], {"level": state.get('level', 0)})
        self.add_concept("energy", "resource", ["system"], {"value": state.get('energy', 1000)})
        self.add_concept("level", "property", ["consciousness"], {"max": 25})
        self.add_concept("phase", "property", ["consciousness"], {"values": ["pre", "near", "post", "super", "singular"]})
        self.add_concept("phi", "property", ["consciousness"], {"range": "0-1"})

        # Module concepts
        modules = [
            "self_awareness", "learning", "reasoning", "planning",
            "ethics", "communication", "memory", "perception",
            "trust", "narrative", "legacy", "sensory", "affective",
            "interface", "spatial", "temporal", "causal", "load",
            "theory_of_mind", "value_reflection", "metaphor",
            "aesthetic", "humor",
        ]
        for mod in modules:
            self.add_concept(mod, "module", ["system"], {"active": True})

        # Relations
        self.add_relation("consciousness", "depends_on", "energy")
        self.add_relation("level", "measures", "consciousness")
        self.add_relation("phase", "describes", "consciousness")
        self.add_relation("phi", "indicates", "coherence")

        self.build_count += 1

    def get_ancestors(self, concept: str, visited: Set[str] = None) -> Set[str]:
        """Get all ancestors of a concept."""
        if visited is None:
            visited = set()
        if concept in visited:
            return visited
        visited.add(concept)

        c = self.concepts.get(concept)
        if c:
            for p in c.parents:
                self.get_ancestors(p, visited)

        return visited

    def get_related(self, concept: str) -> List[str]:
        """Get concepts related to given concept."""
        related = []
        for r in self.relations:
            if r["source"] == concept:
                related.append(r["target"])
            elif r["target"] == concept:
                related.append(r["source"])
        return related

    def get_status(self) -> Dict[str, Any]:
        return {
            "concepts": len(self.concepts),
            "relations": len(self.relations),
            "builds": self.build_count,
            "categories": list(set(c.category for c in self.concepts.values())),
        }


_ob_engine = None

def get_ontology_builder():
    global _ob_engine
    if _ob_engine is None:
        _ob_engine = OntologyBuilder()
    return _ob_engine
