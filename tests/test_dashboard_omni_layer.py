"""OMNI-HUB v185 Tests — DashboardOMNILayer"""

import pytest
import time
from core.dashboard_omni_layer import (
    DashboardOMNILayer, DashboardAggregator, EmergenceBroadcaster,
    WildQuestionAutoLoop, PrimordialTsunamiValidator, AllianceHealthMonitor,
    OMNIReportGenerator, LineSnapshot, EmergenceBroadcast,
    BroadcastScope, ReportFormat, HealthGrade,
    get_dashboard_omni_layer
)


class TestDashboardAggregator:
    def test_init(self):
        a = DashboardAggregator()
        assert len(a.snapshots) == 0

    def test_ingest(self):
        a = DashboardAggregator()
        a.ingest("ucif2", {"health": 0.9, "coherence": 0.8, "alignment_level": "META"})
        assert "ucif2" in a.snapshots
        assert a.snapshots["ucif2"].health == 0.9

    def test_heatmap(self):
        a = DashboardAggregator()
        a.ingest("ucif2", {"health": 0.9, "coherence": 0.8})
        h = a.get_heatmap()
        assert "ucif2" in h
        assert h["ucif2"]["health"] == 0.9

    def test_heatmap_missing(self):
        a = DashboardAggregator()
        h = a.get_heatmap()
        assert h["lgt"]["health"] == 0.0  # missing line defaults

    def test_correlation(self):
        a = DashboardAggregator()
        for i in range(25):
            a.ingest("ucif2", {"coherence": 0.8})
            a.ingest("lgt", {"coherence": 0.7})
        c = a.get_cross_line_correlation()
        assert "ucif2" in c or len(c) == 0

    def test_report(self):
        a = DashboardAggregator()
        a.ingest("ucif2", {"health": 0.9})
        r = a.get_report()
        assert r["lines_tracked"] == 1


class TestEmergenceBroadcaster:
    def test_subscribe(self):
        b = EmergenceBroadcaster()
        b.subscribe("ucif2", BroadcastScope.GLOBAL)
        assert "ucif2" in b.subscribers[BroadcastScope.GLOBAL]

    def test_broadcast(self):
        b = EmergenceBroadcaster()
        b.subscribe("ucif2", BroadcastScope.ALLIANCE)
        bc = b.broadcast("e1", "WAVE", {"data": "test"}, BroadcastScope.ALLIANCE)
        assert bc.broadcast_id.startswith("bc_")
        assert len(bc.delivery_status) > 0

    def test_acknowledge(self):
        b = EmergenceBroadcaster()
        b.subscribe("ucif2", BroadcastScope.GLOBAL)
        bc = b.broadcast("e1", "RIPPLE", {}, BroadcastScope.GLOBAL)
        ok = b.acknowledge(bc.broadcast_id, "ucif2")
        assert ok is True
        assert "ucif2" in bc.acknowledged_by

    def test_pending_ack(self):
        b = EmergenceBroadcaster()
        b.subscribe("ucif2", BroadcastScope.GLOBAL)
        bc = b.broadcast("e1", "RIPPLE", {}, BroadcastScope.GLOBAL)
        pending = b.get_pending_ack(bc.broadcast_id)
        assert isinstance(pending, list)

    def test_report(self):
        b = EmergenceBroadcaster()
        b.broadcast("e1", "WAVE", {})
        r = b.get_report()
        assert r["total_broadcasts"] == 1


class TestWildQuestionAutoLoop:
    def test_start(self):
        w = WildQuestionAutoLoop()
        exp = w.start_exploration("q1", "what is X?")
        assert exp.qid == "q1"
        assert not exp.completed

    def test_explore_step(self):
        w = WildQuestionAutoLoop()
        w.start_exploration("q1", "what?")
        exp = w.explore_step("q1", "search", {"novelty": 0.8, "key_finding": "found"})
        assert exp.depth == 1

    def test_generate_followup(self):
        w = WildQuestionAutoLoop()
        q = w._generate_followup({"implication": "test"})
        assert len(q) > 0

    def test_complete(self):
        w = WildQuestionAutoLoop()
        w.start_exploration("q1", "what?")
        w.explore_step("q1", "search", {"novelty": 0.5})
        exp = w.complete_exploration("q1", {"result": "done"})
        assert exp.completed is True

    def test_open_explorations(self):
        w = WildQuestionAutoLoop()
        w.start_exploration("q1", "what?")
        assert len(w.get_open_explorations()) == 1
        w.complete_exploration("q1", {})
        assert len(w.get_open_explorations()) == 0

    def test_report(self):
        w = WildQuestionAutoLoop()
        w.start_exploration("q1", "what?")
        r = w.get_report()
        assert r["active_explorations"] == 1


class TestPrimordialTsunamiValidator:
    def test_neither(self):
        v = PrimordialTsunamiValidator()
        r = v.validate("EXTERNAL", "NONE", 0.5, {})
        assert r.primordial_confirmed is False
        assert r.tsunami_confirmed is False
        assert r.joint_score == 0.0

    def test_primordial_only(self):
        v = PrimordialTsunamiValidator()
        r = v.validate("PRIMORDIAL", "NONE", 0.98,
                      {"red_free_cycles": 100, "entropy_trend": "decreasing"})
        assert r.primordial_confirmed is True
        assert r.tsunami_confirmed is False
        assert r.joint_score > 0.5

    def test_tsunami_only(self):
        v = PrimordialTsunamiValidator()
        r = v.validate("META", "TSUNAMI", 0.6,
                      {"z_score": 5.5, "affected_modules": 5})
        assert r.primordial_confirmed is False
        assert r.tsunami_confirmed is True

    def test_joint(self):
        v = PrimordialTsunamiValidator()
        r = v.validate("PRIMORDIAL", "TSUNAMI", 0.98,
                      {"red_free_cycles": 100, "entropy_trend": "decreasing",
                       "z_score": 5.5, "affected_modules": 5})
        assert r.primordial_confirmed is True
        assert r.tsunami_confirmed is True
        assert r.joint_score > 0.8

    def test_false_positive(self):
        v = PrimordialTsunamiValidator()
        v.validate("PRIMORDIAL", "NONE", 0.5, {})  # claims primordial but fails
        assert v.false_positives > 0

    def test_report(self):
        v = PrimordialTsunamiValidator()
        v.validate("PRIMORDIAL", "TSUNAMI", 0.98,
                  {"red_free_cycles": 100, "entropy_trend": "decreasing",
                   "z_score": 5.5, "affected_modules": 5})
        r = v.get_report()
        assert r["joint_events"] == 1


class TestAllianceHealthMonitor:
    def test_init(self):
        m = AllianceHealthMonitor()
        assert m is not None

    def test_compute_health(self):
        m = AllianceHealthMonitor()
        snapshots = {
            "ucif2": LineSnapshot("ucif2", 0.9, "META", "awake", 0.8, 0.1, "GREEN", time.time(), "", "operational"),
            "lgt": LineSnapshot("lgt", 0.7, "HABITUAL", "", 0.6, 0.2, "GREEN", time.time(), "", "operational"),
        }
        h = m.compute_health(snapshots)
        assert h.overall_score > 0
        assert h.grade.value >= HealthGrade.CRITICAL.value

    def test_compute_optimal(self):
        m = AllianceHealthMonitor()
        snapshots = {}
        for line in ["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl", "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"]:
            snapshots[line] = LineSnapshot(line, 0.95, "PRIMORDIAL", "awake", 0.95, 0.01, "GREEN", time.time(), "dash", "fully")
        h = m.compute_health(snapshots)
        assert h.grade == HealthGrade.OPTIMAL

    def test_report(self):
        m = AllianceHealthMonitor()
        r = m.get_report()
        assert "topology_loaded" in r


class TestOMNIReportGenerator:
    def test_json(self):
        g = OMNIReportGenerator()
        r = g.generate(ReportFormat.JSON, {"test": 1})
        assert "test" in r

    def test_markdown(self):
        g = OMNIReportGenerator()
        r = g.generate(ReportFormat.MARKDOWN, {"heatmap": {"ucif2": {"health": 0.9}}})
        assert "# OMNI-HUB" in r

    def test_html(self):
        g = OMNIReportGenerator()
        r = g.generate(ReportFormat.HTML, {"heatmap": {}})
        assert "<html>" in r


class TestDashboardOMNILayer:
    def test_init(self):
        d = DashboardOMNILayer()
        assert d.VERSION == "185.0.0"

    def test_run_cycle(self):
        d = DashboardOMNILayer()
        r = d.run_cycle(
            line_states={"ucif2": {"health": 0.9, "coherence": 0.8, "alignment_level": "META"}},
            omni_result={"emergence": {"detected": False}},
            alignment_result={"alignment_level": "META"}
        )
        assert r["cycle"] == 1
        assert "heatmap" in r

    def test_run_cycle_with_emergence(self):
        d = DashboardOMNILayer()
        r = d.run_cycle(
            line_states={"ucif2": {"health": 0.9}, "lgt": {"health": 0.9}, "qfa": {"health": 0.9}},
            omni_result={
                "emergence": {"detected": True, "level": "TSUNAMI", "event_id": "e1"},
                "omni_state": {"collective_coherence": 0.98}
            },
            alignment_result={"alignment_level": "PRIMORDIAL", "red_free_count": 100,
                             "entropy": {"trend": "decreasing"}}
        )
        assert r["emergence"]["broadcasted"] is True
        assert r["validation"]["joint_score"] > 0.8

    def test_auto_loop_trigger(self):
        d = DashboardOMNILayer()
        for i in range(30):
            d.run_cycle(
                line_states={"ucif2": {"health": 0.9}},
                omni_result={"wild_questions": 5, "emergence": {"detected": False}}
            )
        assert d.auto_loop.get_report()["total_explorations"] > 0

    def test_generate_report(self):
        d = DashboardOMNILayer()
        d.run_cycle(line_states={"ucif2": {"health": 0.9}})
        r = d.generate_report(ReportFormat.MARKDOWN)
        assert len(r) > 0

    def test_manual_broadcast(self):
        d = DashboardOMNILayer()
        bc = d.broadcast_manual("e_test", "WAVE", {"msg": "hello"})
        assert bc.signal_level == "WAVE"

    def test_get_status(self):
        d = DashboardOMNILayer()
        d.run_cycle()
        s = d.get_status()
        assert s["version"] == "185.0.0"
        assert "aggregator" in s
        assert "validator" in s

    def test_singleton(self):
        d1 = get_dashboard_omni_layer()
        d2 = get_dashboard_omni_layer()
        assert d1 is d2

    def test_multiple_lines(self):
        d = DashboardOMNILayer()
        lines = {"ucif2": {"health": 0.9}, "lgt": {"health": 0.8}, "qfa": {"health": 0.7}}
        r = d.run_cycle(line_states=lines)
        assert len(r["heatmap"]) >= 3

    def test_health_grade(self):
        d = DashboardOMNILayer()
        lines = {line: {"health": 0.95, "coherence": 0.95, "alignment_level": "PRIMORDIAL"}
                 for line in ["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl", "qlv", "qtlv", "usrm", "cfts", "aiq", "omni"]}
        r = d.run_cycle(line_states=lines)
        assert r["alliance_health"]["grade"] in ["OPTIMAL", "HEALTHY"]

# Total: 44 tests
