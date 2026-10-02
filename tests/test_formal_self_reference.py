"""OMNI-HUB v189 Tests — FormalSelfReference"""

import pytest
from core.formal_self_reference import (
    FormalSelfReference, TypeSystem, ProofEngine, SafetyChecker,
    AxiomBase, InferenceRule,
    TypeSignature, Theorem, SafetyReport, Axiom, InferenceStep,
    TypeRank, ProofStatus, SafetyLevel,
    get_formal_self_reference
)


class TestTypeSystem:
    def test_init(self):
        ts = TypeSystem()
        assert len(ts.signatures) == 4

    def test_register(self):
        ts = TypeSystem()
        sig = ts.register("custom", TypeRank.TYPE_1)
        assert ts.signatures["custom"].rank == TypeRank.TYPE_1

    def test_self_reference_same_rank(self):
        ts = TypeSystem()
        ts.register("a", TypeRank.TYPE_1)
        ts.register("b", TypeRank.TYPE_1)
        is_sr, reason = ts.check_self_reference("a", "b")
        assert is_sr is True

    def test_no_self_reference_different_rank(self):
        ts = TypeSystem()
        ts.register("a", TypeRank.TYPE_1)
        ts.register("b", TypeRank.TYPE_2)
        is_sr, reason = ts.check_self_reference("a", "b")
        assert is_sr is False

    def test_assign_rank(self):
        ts = TypeSystem()
        ts.register("ref", TypeRank.TYPE_2)
        rank = ts.assign_rank("new", ["ref"])
        assert rank == TypeRank.TYPE_3

    def test_get_report(self):
        ts = TypeSystem()
        r = ts.get_report()
        assert r["types"] == 4


class TestProofEngine:
    def test_propose(self):
        pe = ProofEngine()
        th = pe.propose("test", TypeRank.TYPE_1)
        assert th.status == ProofStatus.UNPROVEN

    def test_prove(self):
        pe = ProofEngine()
        th = pe.propose("test", TypeRank.TYPE_1)
        assert pe.prove(th.theorem_id, ["step1"], []) is True
        assert pe.theorems[th.theorem_id].status == ProofStatus.PROVABLE

    def test_disprove(self):
        pe = ProofEngine()
        th = pe.propose("test", TypeRank.TYPE_1)
        pe.disprove(th.theorem_id, "counter")
        assert pe.theorems[th.theorem_id].status == ProofStatus.DISPROVEN

    def test_paradox(self):
        pe = ProofEngine()
        th = pe.propose("self and not self", TypeRank.TYPE_0)
        assert pe.check_paradox(th.theorem_id) is True
        assert pe.theorems[th.theorem_id].status == ProofStatus.PARADOXICAL

    def test_get_report(self):
        pe = ProofEngine()
        pe.propose("t1", TypeRank.TYPE_1)
        r = pe.get_report()
        assert r["theorems"] == 1


class TestSafetyChecker:
    def test_safe_expression(self):
        sc = SafetyChecker()
        ts = TypeSystem()
        r = sc.check_expression("x = 1 + 2", ts)
        assert r.level == SafetyLevel.PROVEN_SAFE

    def test_self_reference_expression(self):
        sc = SafetyChecker()
        ts = TypeSystem()
        r = sc.check_expression("this references self", ts)
        assert r.level in (SafetyLevel.SAFE, SafetyLevel.CONDITIONAL, SafetyLevel.UNSAFE)

    def test_module_safe(self):
        sc = SafetyChecker()
        r = sc.check_module("mod1", {"mod1": ["mod2"], "mod2": []})
        assert r.level == SafetyLevel.PROVEN_SAFE

    def test_module_circular(self):
        sc = SafetyChecker()
        r = sc.check_module("mod1", {"mod1": ["mod2"], "mod2": ["mod1"]})
        assert r.level == SafetyLevel.UNSAFE

    def test_get_report(self):
        sc = SafetyChecker()
        sc.check_expression("safe", TypeSystem())
        r = sc.get_report()
        assert "reports" in r


class TestAxiomBase:
    def test_init(self):
        ab = AxiomBase()
        assert len(ab.axioms) == 6

    def test_verify(self):
        ab = AxiomBase()
        ok, matching = ab.verify("System exists and runs")
        assert ok is True
        assert "ax_existence" in matching

    def test_get_by_rank(self):
        ab = AxiomBase()
        axioms = ab.get_by_rank(TypeRank.TYPE_0)
        assert len(axioms) >= 2

    def test_get_report(self):
        ab = AxiomBase()
        r = ab.get_report()
        assert r["axioms"] == 6


class TestInferenceRule:
    def test_apply_mp(self):
        ir = InferenceRule()
        step = ir.apply("MP", ["A", "A→B"], "B", [TypeRank.TYPE_1, TypeRank.TYPE_1])
        assert step.valid is True

    def test_apply_unknown(self):
        ir = InferenceRule()
        step = ir.apply("UNKNOWN", [], "X", [])
        assert step.valid is False

    def test_chain(self):
        ir = InferenceRule()
        s1 = ir.apply("MP", ["A"], "B", [TypeRank.TYPE_1])
        s2 = ir.apply("MP", ["B"], "C", [TypeRank.TYPE_1])
        assert ir.chain([s1, s2]) is True

    def test_get_report(self):
        ir = InferenceRule()
        ir.apply("MP", ["A"], "B", [TypeRank.TYPE_1])
        r = ir.get_report()
        assert r["steps"] == 1


class TestFormalSelfReference:
    def test_init(self):
        fsr = FormalSelfReference()
        assert fsr.VERSION == "189.0.0"

    def test_analyze_module_safe(self):
        fsr = FormalSelfReference()
        r = fsr.analyze_module("mod1", {"mod1": ["mod2"], "mod2": []}, ["x=1"])
        assert r["safety_level"] == "PROVEN_SAFE"
        assert len(r["self_references"]) == 0

    def test_analyze_module_circular(self):
        fsr = FormalSelfReference()
        r = fsr.analyze_module("mod1", {"mod1": ["mod2"], "mod2": ["mod1"]}, [])
        assert len(r["self_references"]) > 0

    def test_verify_system(self):
        fsr = FormalSelfReference()
        r = fsr.verify_system({"mod1": {"mod2": []}, "mod2": {"mod3": []}})
        assert r["modules_checked"] == 2

    def test_run_cycle(self):
        fsr = FormalSelfReference()
        r = fsr.run_cycle({"mod1": {"mod2": []}})
        assert r["cycle"] == 1

    def test_get_status(self):
        fsr = FormalSelfReference()
        fsr.run_cycle()
        s = fsr.get_status()
        assert s["version"] == "189.0.0"

    def test_singleton(self):
        f1 = get_formal_self_reference()
        f2 = get_formal_self_reference()
        assert f1 is f2

# Total: 34 tests
