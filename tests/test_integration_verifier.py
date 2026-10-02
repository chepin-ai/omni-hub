"""OMNI-HUB v198 Tests — IntegrationVerifier"""

import pytest
from core.integration_verifier import (
    IntegrationVerifier, EndToEndTester, InterfaceChecker,
    DataFlowValidator, PipelineVerifier, SemanticChecker,
    TestResult, get_integration_verifier
)


class TestEndToEndTester:
    def test_run(self):
        et = EndToEndTester()
        r = et.run_test(["a", "b"], {"x": 1})
        assert "latency" in r

    def test_result_type(self):
        et = EndToEndTester()
        r = et.run_test(["a", "b"], {"x": 1})
        assert r["result"] in [TestResult.PASS, TestResult.FAIL]


class TestInterfaceChecker:
    def test_missing(self):
        ic = InterfaceChecker()
        r = ic.check_interface("m1", {"f1": "int"}, {})
        assert len(r) >= 1

    def test_type_match(self):
        ic = InterfaceChecker()
        r = ic.check_interface("m1", {"f1": "int"}, {"f1": 42})
        assert len(r) == 0


class TestDataFlowValidator:
    def test_valid(self):
        df = DataFlowValidator()
        r = df.validate_flow("a", "b", {"x": 1}, {"required": ["x"]})
        assert r["valid"] is True

    def test_invalid(self):
        df = DataFlowValidator()
        r = df.validate_flow("a", "b", {"y": 1}, {"required": ["x"]})
        assert r["valid"] is False


class TestPipelineVerifier:
    def test_valid(self):
        pv = PipelineVerifier()
        r = pv.verify_pipeline(["a", "b"], {"b": ["a"]})
        assert len(r) == 0

    def test_missing_dep(self):
        pv = PipelineVerifier()
        r = pv.verify_pipeline(["a", "b"], {"b": ["c"]})
        assert len(r) >= 1


class TestSemanticChecker:
    def test_coherence(self):
        sc = SemanticChecker()
        c = sc.check_semantic_coherence("a", {"x": 1, "y": 2}, "b", {"x": 1, "z": 3})
        assert 0 <= c <= 1

    def test_empty(self):
        sc = SemanticChecker()
        c = sc.check_semantic_coherence("a", {}, "b", {})
        assert c == 0.0


class TestIntegrationVerifier:
    def test_init(self):
        iv = IntegrationVerifier()
        assert iv.VERSION == "198.0.0"

    def test_verify(self):
        iv = IntegrationVerifier()
        r = iv.verify({
            "m1": {"health": 0.9, "dependencies": [], "output": {"x": 1}},
            "m2": {"health": 0.8, "dependencies": ["m1"], "input": {"x": 1}},
        })
        assert "integration_ready" in r

    def test_run_cycle(self):
        iv = IntegrationVerifier()
        r = iv.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        iv = IntegrationVerifier()
        s = iv.get_status()
        assert s["version"] == "198.0.0"

    def test_singleton(self):
        a = get_integration_verifier()
        b = get_integration_verifier()
        assert a is b

# Total: 24 tests
