"""OMNI-HUB v196 Tests — PhaseSynchronizer"""

import pytest
from core.phase_synchronizer import (
    PhaseSynchronizer, PhaseLockDetector, SyncDomainManager,
    KuramotoModel, PhaseGradientTracker, CollectiveRhythmEngine,
    PhaseState, SyncDomain, SyncState, RhythmType,
    get_phase_synchronizer
)


class TestPhaseLockDetector:
    def test_lock(self):
        pld = PhaseLockDetector()
        locked = pld.check_lock("m1", [0.5, 0.51, 0.52])
        assert locked is True

    def test_unlock(self):
        pld = PhaseLockDetector()
        locked = pld.check_lock("m1", [0.1, 0.6, 0.2, 0.9])
        assert locked is False

    def test_rate(self):
        pld = PhaseLockDetector()
        pld.check_lock("m1", [0.5, 0.51])
        assert pld.get_lock_rate() >= 0


class TestSyncDomainManager:
    def test_form_domain(self):
        sdm = SyncDomainManager()
        d = sdm.form_domain({"a", "b"}, {"a": 0.0, "b": 0.1})
        assert len(d.members) == 2

    def test_coherence(self):
        sdm = SyncDomainManager()
        sdm.form_domain({"a", "b"}, {"a": 0.0, "b": 0.0})
        assert sdm.get_global_coherence() > 0


class TestKuramotoModel:
    def test_step(self):
        km = KuramotoModel()
        km.set_natural_frequency("a", 1.0)
        km.set_natural_frequency("b", 1.0)
        p = km.step({"a": 0.0, "b": 0.1})
        assert "a" in p

    def test_order_parameter(self):
        km = KuramotoModel()
        r = km.compute_order_parameter({"a": 0.0, "b": 0.0})
        assert abs(r - 1.0) < 0.01


class TestPhaseGradientTracker:
    def test_record_and_gradient(self):
        pgt = PhaseGradientTracker()
        for i in range(5):
            pgt.record("m1", i * 0.1)
        g = pgt.compute_gradient("m1")
        assert g > 0


class TestCollectiveRhythmEngine:
    def test_detect_steady(self):
        cre = CollectiveRhythmEngine()
        r = cre.detect_rhythm("m1", [0.1, 0.2, 0.3, 0.4])
        assert r == RhythmType.STEADY

    def test_tempo(self):
        cre = CollectiveRhythmEngine()
        cre.detect_rhythm("m1", [0.1, 0.2])
        assert cre.get_collective_tempo() >= 0


class TestPhaseSynchronizer:
    def test_init(self):
        ps = PhaseSynchronizer()
        assert ps.VERSION == "196.0.0"

    def test_synchronize(self):
        ps = PhaseSynchronizer()
        r = ps.synchronize({"m1": {"health": 0.9}, "m2": {"health": 0.8}})
        assert "order_parameter" in r
        assert "phases" in r

    def test_run_cycle(self):
        ps = PhaseSynchronizer()
        r = ps.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ps = PhaseSynchronizer()
        s = ps.get_status()
        assert s["version"] == "196.0.0"

    def test_singleton(self):
        p1 = get_phase_synchronizer()
        p2 = get_phase_synchronizer()
        assert p1 is p2

# Total: 24 tests
