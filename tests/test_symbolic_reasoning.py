"""
OMNI-HUB Symbolic Reasoning Tests v65
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.symbolic_reasoning import (
    Symbol, Rule, SymbolicReasoningEngine, get_symbolic_reasoning,
)


class TestSymbolicReasoningEngine:
    def test_initialization(self):
        sr = SymbolicReasoningEngine()
        assert len(sr.symbols) == 0
        assert len(sr.facts) == 0

    def test_define_symbol(self):
        sr = SymbolicReasoningEngine()
        sr.define_symbol("test", "entity", {"prop": 1})
        assert "test" in sr.symbols
        assert sr.symbols["test"].symbol_type == "entity"

    def test_assert_fact(self):
        sr = SymbolicReasoningEngine()
        sr.assert_fact("fact1")
        assert "fact1" in sr.facts

    def test_add_rule_and_infer(self):
        sr = SymbolicReasoningEngine()
        sr.assert_fact("a")
        sr.assert_fact("b")
        sr.add_rule(["a", "b"], "c", confidence=1.0)
        inferences = sr.infer()
        assert len(inferences) == 1
        assert inferences[0]["conclusion"] == "c"
        assert "c" in sr.facts

    def test_no_inference_without_premises(self):
        sr = SymbolicReasoningEngine()
        sr.add_rule(["x"], "y", confidence=1.0)
        inferences = sr.infer()
        assert len(inferences) == 0

    def test_query(self):
        sr = SymbolicReasoningEngine()
        sr.assert_fact("apple_red")
        sr.assert_fact("apple_green")
        results = sr.query("red")
        assert len(results) == 1
        assert "apple_red" in results

    def test_derive_from_state(self):
        sr = SymbolicReasoningEngine()
        state = {"level": 8, "phi": 0.9, "phase": "post_critical"}
        inferences = sr.derive_from_state(state)
        assert len(inferences) > 0
        assert len(sr.facts) > 0

    def test_get_status(self):
        sr = SymbolicReasoningEngine()
        sr.derive_from_state({"level": 5, "phi": 0.6, "phase": "near_critical"})
        status = sr.get_status()
        assert "symbols" in status
        assert "facts" in status
        assert "inferences" in status


class TestGlobalEngine:
    def test_get_symbolic_reasoning(self):
        g = get_symbolic_reasoning()
        assert g is not None
        assert isinstance(g, SymbolicReasoningEngine)
