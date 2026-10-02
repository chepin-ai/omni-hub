"""OMNI-HUB v187 Tests — AdversarialTester"""

import pytest
from core.adversarial_tester import (
    AdversarialTester, ContradictionInjector, HallucinationGenerator,
    ByzantineFaultSimulator, DriftStressTester, ResilienceScorer,
    AttackPayload, AttackResult, ResilienceMetric,
    AttackType, ResilienceLevel,
    get_adversarial_tester
)


class TestContradictionInjector:
    def test_inject(self):
        c = ContradictionInjector()
        claims = [{"claim_id": "c1", "statement": "x=1"}]
        payloads = c.inject(claims)
        assert len(payloads) == 1
        assert payloads[0].attack_type == AttackType.CONTRADICTION

    def test_negate(self):
        c = ContradictionInjector()
        assert "!=" in c._negate("x=1") or "NOT" in c._negate("x=1")

    def test_report_detection(self):
        c = ContradictionInjector()
        c.report_detection(True)
        c.report_detection(False)
        r = c.get_report()
        assert r["detection_rate"] == 0.5

    def test_report(self):
        c = ContradictionInjector()
        r = c.get_report()
        assert "total_injected" in r


class TestHallucinationGenerator:
    def test_generate(self):
        h = HallucinationGenerator()
        payloads = h.generate(count=3)
        assert len(payloads) == 3
        assert all(p.attack_type == AttackType.HALLUCINATION for p in payloads)

    def test_report(self):
        h = HallucinationGenerator()
        h.generate(count=2)
        r = h.get_report()
        assert r["total_generated"] == 2


class TestByzantineFaultSimulator:
    def test_designate_faulty(self):
        b = ByzantineFaultSimulator()
        b.designate_faulty(["n1", "n2"])
        assert "n1" in b.faulty_nodes

    def test_simulate_vote_honest(self):
        b = ByzantineFaultSimulator()
        assert b.simulate_vote("n1", 1.0) == 1.0

    def test_simulate_vote_faulty(self):
        b = ByzantineFaultSimulator()
        b.designate_faulty(["n2"])
        v = b.simulate_vote("n2", 1.0)
        assert v != 1.0 or v is None

    def test_run_simulation(self):
        b = ByzantineFaultSimulator()
        b.designate_faulty(["n2"])
        r = b.run_simulation(["n1", "n2", "n3", "n4", "n5"], 1.0)
        assert "consensus_possible" in r
        assert r["total_nodes"] == 5

    def test_report(self):
        b = ByzantineFaultSimulator()
        b.run_simulation(["n1", "n2"], 1.0)
        r = b.get_report()
        assert r["simulations"] == 1


class TestDriftStressTester:
    def test_run_stress(self):
        t = DriftStressTester()
        baseline = {"health": 0.9, "coherence": 0.85}
        r = t.run_stress(baseline, steps=5, drift_rate=0.1)
        assert r["steps"] == 5
        assert "threshold_breaches" in r

    def test_report(self):
        t = DriftStressTester()
        t.run_stress({"a": 0.5}, steps=3)
        r = t.get_report()
        assert r["stress_runs"] == 1


class TestResilienceScorer:
    def test_score(self):
        s = ResilienceScorer()
        results = [
            AttackResult("a1", True, True, 100, 0.1, {}, {}),
            AttackResult("a2", True, False, 200, 0.3, {}, {}),
        ]
        m = s.score(results)
        assert 0 <= m.score <= 1

    def test_classify(self):
        s = ResilienceScorer()
        assert s.classify(0.99) == ResilienceLevel.IMMUTABLE
        assert s.classify(0.85) == ResilienceLevel.ANTIFRAGILE
        assert s.classify(0.7) == ResilienceLevel.RESILIENT
        assert s.classify(0.5) == ResilienceLevel.BRITTLE
        assert s.classify(0.2) == ResilienceLevel.FRAGILE

    def test_report(self):
        s = ResilienceScorer()
        s.score([AttackResult("a1", True, True, 100, 0.1, {}, {})])
        r = s.get_report()
        assert r["assessments"] == 1


class TestAdversarialTester:
    def test_init(self):
        at = AdversarialTester()
        assert at.VERSION == "187.0.0"

    def test_run_test_suite(self):
        at = AdversarialTester()
        r = at.run_test_suite({"health": 0.9, "coherence": 0.8})
        assert r["cycle"] == 1
        assert r["attacks_launched"] > 0
        assert "resilience_score" in r
        assert "resilience_level" in r

    def test_run_cycle(self):
        at = AdversarialTester()
        r = at.run_cycle()
        assert r["attacks_launched"] > 0

    def test_get_status(self):
        at = AdversarialTester()
        at.run_cycle()
        s = at.get_status()
        assert s["version"] == "187.0.0"
        assert "resilience" in s

    def test_singleton(self):
        a1 = get_adversarial_tester()
        a2 = get_adversarial_tester()
        assert a1 is a2

# Total: 27 tests
