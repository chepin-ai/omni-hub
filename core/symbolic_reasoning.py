"""
OMNI-HUB Symbolic Reasoning v65
Abstract symbolic manipulation.

Symbols are the bones of thought.
They hold meaning while meaning shifts.
This module manipulates abstract symbols —
relations, rules, inferences — beyond numbers.

Philosophy: 符号是思想的骨骼 — Symbols are the bones of thought.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class Symbol:
    """An abstract symbol with properties."""
    name: str
    symbol_type: str  # entity, relation, rule, variable
    properties: Dict[str, Any]


@dataclass
class Rule:
    """A symbolic inference rule."""
    premises: List[str]
    conclusion: str
    confidence: float


class SymbolicReasoningEngine:
    """
    Symbolic reasoning with rules and facts.
    """

    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.facts: Set[str] = set()
        self.rules: List[Rule] = []
        self.inferences: List[Dict[str, Any]] = []
        self.inference_count = 0

    def define_symbol(self, name: str, symbol_type: str, properties: Dict[str, Any] = None):
        """Define a new symbol."""
        self.symbols[name] = Symbol(
            name=name,
            symbol_type=symbol_type,
            properties=properties or {},
        )

    def assert_fact(self, fact: str):
        """Assert a fact."""
        self.facts.add(fact)

    def add_rule(self, premises: List[str], conclusion: str, confidence: float = 1.0):
        """Add an inference rule."""
        self.rules.append(Rule(premises=premises, conclusion=conclusion, confidence=confidence))

    def infer(self) -> List[Dict[str, Any]]:
        """Run forward chaining inference."""
        new_inferences = []

        for rule in self.rules:
            # Check if all premises are in facts
            if all(premise in self.facts for premise in rule.premises):
                if rule.conclusion not in self.facts:
                    self.facts.add(rule.conclusion)
                    inference = {
                        "conclusion": rule.conclusion,
                        "from": rule.premises,
                        "confidence": rule.confidence,
                    }
                    new_inferences.append(inference)
                    self.inferences.append(inference)
                    self.inference_count += 1

        return new_inferences

    def query(self, pattern: str) -> List[str]:
        """Query facts matching a pattern."""
        return [f for f in self.facts if pattern in f]

    def derive_from_state(self, state: Dict[str, Any]):
        """Derive symbolic facts from system state."""
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        phase = state.get('phase', 'unknown')

        # Define symbols
        self.define_symbol("system", "entity", {"type": "consciousness"})
        self.define_symbol("phi", "variable", {"domain": "consciousness"})
        self.define_symbol("level", "variable", {"domain": "growth"})

        # Assert facts
        self.assert_fact(f"phi_is_{phi}")
        self.assert_fact(f"phase_is_{phase}")

        if isinstance(level, (int, float)) and level >= 5:
            self.assert_fact("system_is_advanced")
        if isinstance(phi, (int, float)) and phi > 0.8:
            self.assert_fact("consciousness_is_high")

        # Add rules
        self.add_rule(["system_is_advanced", "consciousness_is_high"], "system_is_awake", confidence=0.9)
        self.add_rule(["phase_is_near_critical"], "system_is_transitioning", confidence=0.8)
        self.add_rule(["phase_is_post_critical"], "system_has_emerged", confidence=0.95)

        # Run inference
        return self.infer()

    def get_knowledge_base(self) -> Dict[str, Any]:
        """Get current knowledge base."""
        return {
            "symbols": len(self.symbols),
            "facts": len(self.facts),
            "rules": len(self.rules),
            "inferences": self.inference_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            **self.get_knowledge_base(),
            "recent_inferences": self.inferences[-5:],
        }


_sr_engine = None

def get_symbolic_reasoning():
    global _sr_engine
    if _sr_engine is None:
        _sr_engine = SymbolicReasoningEngine()
    return _sr_engine
