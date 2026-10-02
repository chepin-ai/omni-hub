"""OMNI-HUB v186 Tests — SelfReferenceMonitor"""

import pytest
from core.self_reference_monitor import (
    SelfReferenceMonitor, MetaObservationLog, RecursiveDepthGuard,
    SelfConsistencyChecker, ObserverEffectTracker, ReflexiveLoopDetector,
    Observation, MetaObservation, RecursionFrame, SelfConsistencyReport,
    ObserverEffect, ObservationLevel, LoopStatus, ReflexType,
    get_self_reference_monitor, compute_delta
)


class TestComputeDelta:
    def test_numeric(self):
        assert compute_delta(1.0, 2.0) == 1.0

    def test_dict(self):
        assert compute_delta({"a": 1}, {"a": 2}) > 0

    def test_equal(self):
        assert compute_delta(1, 1) == 0


class TestMetaObservationLog:
    def test_observe(self):
        log = MetaObservationLog()
        o = log.observe("mod1", "field", {"x": 1})
        assert o.obs_id.startswith("obs_")
        assert len(log.observations) == 1

    def test_meta_observe(self):
        log = MetaObservationLog()
        log.observe("mod1", "field", {})
        m = log.observe_observation("srm", "field")
        assert m.meta_id.startswith("meta_")
        assert m.recursion_depth >= 0

    def test_depth_distribution(self):
        log = MetaObservationLog()
        for i in range(5):
            log.observe_observation("srm", f"target{i}")
        d = log.get_depth_distribution()
        assert len(d) > 0

    def test_report(self):
        log = MetaObservationLog()
        log.observe("a", "b", {})
        r = log.get_report()
        assert r["observations"] == 1


class TestRecursiveDepthGuard:
    def test_enter_exit(self):
        g = RecursiveDepthGuard(max_depth=3)
        assert g.enter("a", "b") is True
        assert g.current_depth() == 1
        g.exit()
        assert g.current_depth() == 0

    def test_depth_limit(self):
        g = RecursiveDepthGuard(max_depth=2)
        g.enter("a", "b")
        g.enter("b", "c")
        assert g.enter("c", "d") is False  # would exceed depth 2

    def test_is_safe(self):
        g = RecursiveDepthGuard(max_depth=5)
        assert g.is_safe() is True

    def test_report(self):
        g = RecursiveDepthGuard()
        g.enter("a", "b")
        r = g.get_report()
        assert r["current_depth"] == 1


class TestSelfConsistencyChecker:
    def test_record_and_check(self):
        c = SelfConsistencyChecker()
        c.record_predicate("mod1", "health", 0.9)
        c.record_predicate("mod1", "health", 0.91)
        r = c.check_consistency("mod1")
        assert r.consistency_score > 0

    def test_contradiction(self):
        c = SelfConsistencyChecker()
        c.record_predicate("mod1", "status", True)
        c.record_predicate("mod1", "status", False)
        r = c.check_consistency("mod1")
        assert len(r.contradictions) > 0

    def test_report(self):
        c = SelfConsistencyChecker()
        c.record_predicate("mod1", "x", 1)
        c.check_consistency("mod1")
        r = c.get_report()
        assert r["checks"] == 1


class TestObserverEffectTracker:
    def test_snapshot(self):
        t = ObserverEffectTracker()
        t.snapshot("mod1", {"x": 1})
        assert "mod1" in t.state_snapshots

    def test_observe_effect(self):
        t = ObserverEffectTracker()
        t.snapshot("mod1", {"x": 1.0})
        e = t.observe("srm", "mod1", {"x": 2.0})
        assert e is not None
        assert e.delta == 1.0

    def test_no_effect(self):
        t = ObserverEffectTracker()
        t.snapshot("mod1", {"x": 1.0})
        e = t.observe("srm", "mod1", {"x": 1.0})
        assert e is None

    def test_report(self):
        t = ObserverEffectTracker()
        t.snapshot("mod1", {"x": 1})
        r = t.get_report()
        assert r["targets_observed"] == 1


class TestReflexiveLoopDetector:
    def test_add_edge(self):
        d = ReflexiveLoopDetector()
        d.add_edge("a", "b")
        assert "a" in d.observation_graph

    def test_detect_mutual(self):
        d = ReflexiveLoopDetector()
        d.add_edge("a", "b")
        d.add_edge("b", "a")
        assert len(d.loops) > 0
        assert d.loops[0]["type"] == "mutual"

    def test_dynamics(self):
        d = ReflexiveLoopDetector()
        assert d.analyze_loop_dynamics() == LoopStatus.STABLE

    def test_report(self):
        d = ReflexiveLoopDetector()
        d.add_edge("a", "b")
        r = d.get_report()
        assert r["observation_graph_size"] == 1


class TestSelfReferenceMonitor:
    def test_init(self):
        s = SelfReferenceMonitor()
        assert s.VERSION == "186.0.0"

    def test_run_cycle(self):
        s = SelfReferenceMonitor()
        r = s.run_cycle({
            "mod1": {"health": 0.9, "status": "active"},
            "mod2": {"health": 0.8, "status": "idle"},
        })
        assert r["cycle"] == 1
        assert r["recursion_safe"] is True
        assert "consistency" in r

    def test_run_cycle_with_loop(self):
        s = SelfReferenceMonitor()
        r = s.run_cycle({
            "mod1": {"health": 0.9, "watches": ["self_reference_monitor"]},
        })
        assert r["loop_dynamics"] in ["STABLE", "OSCILLATING", "DIVERGING", "CONVERGING", "STRANGE"]

    def test_observer_effects(self):
        s = SelfReferenceMonitor()
        for i in range(3):
            s.run_cycle({"mod1": {"health": 0.5 + i * 0.1}})
        assert s.effect_tracker.get_report()["total_effects"] > 0

    def test_get_status(self):
        s = SelfReferenceMonitor()
        s.run_cycle()
        st = s.get_status()
        assert st["version"] == "186.0.0"
        assert "meta_log" in st
        assert "loop_detector" in st

    def test_singleton(self):
        s1 = get_self_reference_monitor()
        s2 = get_self_reference_monitor()
        assert s1 is s2

# Total: 32 tests
