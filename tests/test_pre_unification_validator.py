"""OMNI-HUB v198 Tests — PreUnificationValidator"""

import pytest
from core.pre_unification_validator import (
    PreUnificationValidator, ConsistencyChecker, CompatibilityTester,
    VulnerabilityScanner, ContractValidator, TopologyVerifier,
    CheckResult, CompatibilityMatrix, CheckSeverity, ValidationStatus,
    get_pre_unification_validator
)


class TestConsistencyChecker:
    def test_consistency(self):
        cc = ConsistencyChecker()
        r = cc.check_state_consistency({
            "m1": {"version": "1.0", "health": 0.9},
            "m2": {"version": "2.0", "health": 0.3},
        })
        assert len(r) >= 1

    def test_cross_refs(self):
        cc = ConsistencyChecker()
        r = cc.check_cross_references({"a": ["b"], "b": []})
        assert len(r) == 0

    def test_missing_ref(self):
        cc = ConsistencyChecker()
        r = cc.check_cross_references({"a": ["c"]})
        assert len(r) >= 1

    def test_score(self):
        cc = ConsistencyChecker()
        assert cc.get_consistency_score() == 1.0


class TestCompatibilityTester:
    def test_compatible(self):
        ct = CompatibilityTester()
        m = ct.test_compatibility("a", "b",
            {"version": "1", "data_format": "json", "protocol": "http"},
            {"version": "1", "data_format": "json", "protocol": "http"})
        assert m.compatible is True

    def test_incompatible(self):
        ct = CompatibilityTester()
        m = ct.test_compatibility("a", "b",
            {"version": "1", "data_format": "json", "protocol": "http"},
            {"version": "2", "data_format": "xml", "protocol": "tcp"})
        assert m.compatible is False

    def test_global_score(self):
        ct = CompatibilityTester()
        assert ct.get_global_compatibility() == 1.0


class TestVulnerabilityScanner:
    def test_critical(self):
        vs = VulnerabilityScanner()
        r = vs.scan("m1", {"health": 0.1})
        assert any(v.severity == CheckSeverity.CRITICAL for v in r)

    def test_isolated(self):
        vs = VulnerabilityScanner()
        r = vs.scan("m1", {"health": 0.9, "dependencies": []})
        assert any(v.check_name == "isolated_module" for v in r)

    def test_score(self):
        vs = VulnerabilityScanner()
        assert vs.get_vulnerability_score() == 0.0


class TestTopologyVerifier:
    def test_connectivity(self):
        tv = TopologyVerifier()
        r = tv.verify_connectivity({"a": ["b"], "b": ["a"]})
        assert len(r) == 0

    def test_disconnected(self):
        tv = TopologyVerifier()
        r = tv.verify_connectivity({"a": [], "b": []})
        assert len(r) >= 1

    def test_cycle(self):
        tv = TopologyVerifier()
        r = tv.verify_cycles({"a": ["b"], "b": ["a"]})
        assert len(r) >= 1


class TestContractValidator:
    def test_define(self):
        cv = ContractValidator()
        cv.define_contract("m1", ["in1"], ["out1"], ["inv1"])
        assert "m1" in cv.contracts

    def test_violation(self):
        cv = ContractValidator()
        cv.define_contract("m1", ["in1"], ["out1"], [])
        r = cv.validate("m1", [], ["out1"])
        assert len(r) >= 1


class TestPreUnificationValidator:
    def test_init(self):
        puv = PreUnificationValidator()
        assert puv.VERSION == "198.0.0"

    def test_validate(self):
        puv = PreUnificationValidator()
        r = puv.validate({
            "m1": {"version": "1.0", "health": 0.9, "dependencies": ["m2"], "interface": {}},
            "m2": {"version": "1.0", "health": 0.8, "dependencies": [], "interface": {}},
        })
        assert "ready_for_unification" in r

    def test_run_cycle(self):
        puv = PreUnificationValidator()
        r = puv.run_cycle({"m1": {"health": 0.9, "dependencies": []}})
        assert r["cycle"] == 1

    def test_get_status(self):
        puv = PreUnificationValidator()
        s = puv.get_status()
        assert s["version"] == "198.0.0"

    def test_singleton(self):
        a = get_pre_unification_validator()
        b = get_pre_unification_validator()
        assert a is b

# Total: 25 tests
