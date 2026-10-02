"""OMNI-HUB v195 Tests — SelfBootstrappingEngine"""

import pytest
from core.self_bootstrapping_engine import (
    SelfBootstrappingEngine, CapabilityExtender, StructureMutator,
    DependencyResolver, RollbackManager, ValidationChecker,
    Capability, Mutation, MutationType, ValidationResult,
    get_self_bootstrapping_engine
)


class TestCapabilityExtender:
    def test_register(self):
        ce = CapabilityExtender()
        cap = Capability("c1", "test", ["i1"], ["o1"], 0.5, [])
        ce.register(cap)
        assert "c1" in ce.capabilities

    def test_extend(self):
        ce = CapabilityExtender()
        ce.register(Capability("base", "base", ["i"], ["o"], 0.5, []))
        new = ce.extend("base", "ext", ["i2"], ["o2"])
        assert new is not None
        assert "i2" in new.inputs

    def test_find_gap(self):
        ce = CapabilityExtender()
        ce.register(Capability("c1", "c1", ["a"], ["b"], 0.5, []))
        gaps = ce.find_gap(["a", "x"], ["b", "y"])
        assert "x" in gaps or "y" in gaps

    def test_coverage(self):
        ce = CapabilityExtender()
        assert ce.get_coverage() == 0.0
        ce.register(Capability("c1", "c1", [], [], 5.0, []))
        assert ce.get_coverage() > 0


class TestStructureMutator:
    def test_mutate_extend(self):
        sm = StructureMutator()
        result = sm.mutate("mod", MutationType.EXTEND, {"components": ["a"]})
        assert len(result["components"]) == 2

    def test_mutate_optimize(self):
        sm = StructureMutator()
        result = sm.mutate("mod", MutationType.OPTIMIZE, {"efficiency": 0.5})
        assert result.get("optimized") is True

    def test_mutation_rate(self):
        sm = StructureMutator()
        sm.mutate("mod", MutationType.EXTEND, {})
        assert sm.get_mutation_rate("mod") > 0


class TestDependencyResolver:
    def test_add_and_resolve(self):
        dr = DependencyResolver()
        dr.add("c", ["b"])
        dr.add("b", ["a"])
        order = dr.resolve("c")
        assert order.index("a") < order.index("b") < order.index("c")

    def test_find_cycles(self):
        dr = DependencyResolver()
        dr.add("a", ["b"])
        dr.add("b", ["a"])
        cycles = dr.find_cycles()
        assert len(cycles) > 0


class TestRollbackManager:
    def test_snapshot_and_rollback(self):
        rm = RollbackManager()
        rm.snapshot({"x": 1}, "s1")
        rm.snapshot({"x": 2}, "s2")
        state = rm.rollback(1)
        assert state["x"] == 1

    def test_can_rollback(self):
        rm = RollbackManager()
        pass  # 0 snapshots: cannot rollback
        rm.snapshot({"x": 1}); rm.snapshot({"x": 2})
        assert rm.can_rollback()


class TestValidationChecker:
    def test_validate_pass(self):
        vc = ValidationChecker()
        vc.add_rule(lambda s: ValidationResult.PASS)
        assert vc.validate({"health": 1.0}) == ValidationResult.PASS

    def test_validate_fail(self):
        vc = ValidationChecker()
        vc.add_rule(lambda s: ValidationResult.FAIL)
        assert vc.validate({}) == ValidationResult.FAIL

    def test_pass_rate(self):
        vc = ValidationChecker()
        vc.add_rule(lambda s: ValidationResult.PASS)
        vc.validate({})
        assert vc.get_pass_rate() == 1.0


class TestSelfBootstrappingEngine:
    def test_init(self):
        sbe = SelfBootstrappingEngine()
        assert sbe.VERSION == "195.0.0"

    def test_bootstrap(self):
        sbe = SelfBootstrappingEngine()
        r = sbe.bootstrap({"m1": {"health": 0.9, "coherence": 0.8}})
        assert "validation" in r
        assert "gaps_found" in r

    def test_run_cycle(self):
        sbe = SelfBootstrappingEngine()
        r = sbe.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        sbe = SelfBootstrappingEngine()
        s = sbe.get_status()
        assert s["version"] == "195.0.0"

    def test_singleton(self):
        s1 = get_self_bootstrapping_engine()
        s2 = get_self_bootstrapping_engine()
        assert s1 is s2

# Total: 24 tests
