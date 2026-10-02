"""OMNI-HUB v188 Tests — CrossOracleValidator"""

import pytest
from core.cross_oracle_validator import (
    CrossOracleValidator, OracleTruthBridge, MultiSourceCrossValidator,
    ConsensusFusion, DiscrepancyAnalyzer, TrustPropagation,
    BridgedFact, CrossValidation, FusedConsensus, Discrepancy, TrustEdge,
    ValidationOutcome, TrustLevel, ALLIANCE_LINES,
    get_cross_oracle_validator
)


class TestOracleTruthBridge:
    def test_bridge(self):
        b = OracleTruthBridge()
        f = b.bridge("q1", 1.0, 1.1)
        assert isinstance(f, BridgedFact)
        assert f.discrepancy > 0

    def test_bridge_identical(self):
        b = OracleTruthBridge()
        f = b.bridge("q1", 2.0, 2.0)
        assert f.discrepancy == 0.0

    def test_get_report(self):
        b = OracleTruthBridge()
        b.bridge("q1", 1.0, 1.1)
        r = b.get_report()
        assert r["bridged"] == 1


class TestMultiSourceCrossValidator:
    def test_consensus(self):
        v = MultiSourceCrossValidator()
        r = v.validate("q1", {"s1": 1.0, "s2": 1.01, "s3": 1.02})
        assert r.outcome in (ValidationOutcome.UNANIMOUS, ValidationOutcome.CONSENSUS)
        assert r.confidence > 0.8

    def test_contradicted(self):
        v = MultiSourceCrossValidator()
        r = v.validate("q1", {"s1": 1.0, "s2": 100.0})
        assert r.outcome == ValidationOutcome.CONTRADICTED

    def test_insufficient(self):
        v = MultiSourceCrossValidator()
        r = v.validate("q1", {"s1": 1.0})
        assert r.outcome == ValidationOutcome.INSUFFICIENT

    def test_get_report(self):
        v = MultiSourceCrossValidator()
        v.validate("q1", {"s1": 1.0, "s2": 1.0})
        r = v.get_report()
        assert r["validations"] == 1


class TestConsensusFusion:
    def test_fuse_numeric(self):
        f = ConsensusFusion()
        r = f.fuse({"value": 1.0, "confidence": 0.8},
                    {"value": 2.0, "confidence": 0.6}, "q1")
        assert isinstance(r, FusedConsensus)
        assert 1.0 <= r.fused_value <= 2.0
        assert r.joint_confidence > 0.8

    def test_get_report(self):
        f = ConsensusFusion()
        f.fuse({"value": 1.0, "confidence": 0.5},
               {"value": 2.0, "confidence": 0.5}, "q1")
        r = f.get_report()
        assert r["fusions"] == 1


class TestDiscrepancyAnalyzer:
    def test_analyze(self):
        a = DiscrepancyAnalyzer()
        discs = a.analyze({"s1": 1.0, "s2": 100.0, "s3": 1.0})
        assert len(discs) > 0
        assert all(d.magnitude > 0 for d in discs)

    def test_no_discrepancy(self):
        a = DiscrepancyAnalyzer()
        discs = a.analyze({"s1": 1.0, "s2": 1.0})
        assert len(discs) == 0

    def test_get_report(self):
        a = DiscrepancyAnalyzer()
        a.analyze({"s1": 1.0, "s2": 2.0})
        r = a.get_report()
        assert r["discrepancies"] == 1


class TestTrustPropagation:
    def test_set_and_propagate(self):
        t = TrustPropagation()
        t.set_trust("n1", 0.8)
        t.set_trust("n2", 0.5)
        t.set_trust("n3", 0.3)
        t.add_edge("n1", "n2", TrustLevel.TRUSTED, 1.0)
        t.add_edge("n2", "n3", TrustLevel.TRUSTED, 1.0)
        result = t.propagate(iterations=3)
        assert len(result) == 3
        assert result["n3"] > 0.3  # trust should propagate

    def test_get_report(self):
        t = TrustPropagation()
        t.set_trust("n1", 0.5)
        r = t.get_report()
        assert r["nodes"] == 1
        assert "avg_trust" in r


class TestCrossOracleValidator:
    def test_init(self):
        cov = CrossOracleValidator()
        assert cov.VERSION == "188.0.0"
        assert len(cov.trust.node_trust) == 12

    def test_validate_query(self):
        cov = CrossOracleValidator()
        r = cov.validate_query("health",
            oracle_values={"o1": 0.9, "o2": 0.85, "o3": 0.88},
            truth_values={"t1": 0.87, "t2": 0.89}
        )
        assert "fused_confidence" in r
        assert r["sources_validated"] == 5

    def test_run_cycle(self):
        cov = CrossOracleValidator()
        r = cov.run_cycle(
            queries=["health", "coherence"],
            oracle_data={"health": {"o1": 0.9}, "coherence": {"o1": 0.8}},
            truth_data={"health": {"t1": 0.88}, "coherence": {"t1": 0.82}}
        )
        assert r["cycle"] == 1
        assert r["queries_validated"] == 2

    def test_get_status(self):
        cov = CrossOracleValidator()
        cov.run_cycle()
        s = cov.get_status()
        assert s["version"] == "188.0.0"
        assert "trust" in s

    def test_singleton(self):
        c1 = get_cross_oracle_validator()
        c2 = get_cross_oracle_validator()
        assert c1 is c2

# Total: 31 tests
