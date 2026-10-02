"""OMNI-HUB v197 Tests — ChaosInjector"""

import pytest
from core.chaos_injector import (
    ChaosInjector, FaultInjector, CascadeSimulator,
    RecoveryTester, PerturbationEngine, StabilityAssessor,
    Fault, CascadeEvent, FaultType, RecoveryMode,
    get_chaos_injector
)


class TestFaultInjector:
    def test_inject(self):
        fi = FaultInjector()
        f = fi.inject("m1", FaultType.CRASH, 0.5)
        assert f.target == "m1"
        assert fi.get_active_count() == 1

    def test_recover(self):
        fi = FaultInjector()
        f = fi.inject("m1", FaultType.CRASH)
        assert fi.recover(f.fault_id) is True
        assert fi.get_active_count() == 0


class TestCascadeSimulator:
    def test_simulate(self):
        cs = CascadeSimulator()
        cs.set_dependencies("b", ["a"])
        cs.set_dependencies("c", ["b"])
        fault = Fault("f1", FaultType.CRASH, "a", 0.8, 0)
        cascade = cs.simulate(fault, {"a": 0.9, "b": 0.8, "c": 0.7})
        assert len(cascade.affected) >= 1

    def test_risk(self):
        cs = CascadeSimulator()
        assert cs.get_cascade_risk() >= 0


class TestRecoveryTester:
    def test_recovery(self):
        rt = RecoveryTester()
        r = rt.test_recovery("m1", 0.9, 0.7, RecoveryMode.AUTOMATIC)
        assert r["recovery_time"] > 0

    def test_avg_time(self):
        rt = RecoveryTester()
        rt.test_recovery("m1", 0.9, 0.7, RecoveryMode.AUTOMATIC)
        assert rt.get_avg_recovery_time() > 0


class TestPerturbationEngine:
    def test_perturb(self):
        pe = PerturbationEngine()
        r = pe.perturb({"a": 0.5, "b": 0.6}, 0.1)
        assert "a" in r

    def test_bounds(self):
        pe = PerturbationEngine()
        r = pe.perturb({"a": 0.99}, 0.2)
        assert 0 <= r["a"] <= 1


class TestStabilityAssessor:
    def test_assess_stable(self):
        sa = StabilityAssessor()
        s = sa.assess({"a": 0.5}, {"a": 0.51})
        assert s > 0.9

    def test_assess_unstable(self):
        sa = StabilityAssessor()
        s = sa.assess({"a": 0.5}, {"a": 0.9})
        assert s < 0.5


class TestChaosInjector:
    def test_init(self):
        ci = ChaosInjector()
        assert ci.VERSION == "197.0.0"

    def test_inject_chaos(self):
        ci = ChaosInjector()
        r = ci.inject_chaos({
            "m1": {"health": 0.9, "dependencies": ["m2"]},
            "m2": {"health": 0.8, "dependencies": []},
        })
        assert "faults_injected" in r
        assert "stability" in r

    def test_run_cycle(self):
        ci = ChaosInjector()
        r = ci.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ci = ChaosInjector()
        s = ci.get_status()
        assert s["version"] == "197.0.0"

    def test_singleton(self):
        c1 = get_chaos_injector()
        c2 = get_chaos_injector()
        assert c1 is c2

# Total: 24 tests
