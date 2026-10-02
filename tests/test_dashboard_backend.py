"""OMNI-HUB v190 Tests — DashboardBackend"""

import pytest
from core.dashboard_backend import (
    DashboardBackend, StateAggregator, SnapshotEngine, MetricStreamer,
    AlertManager, ControlProxy,
    StateSnapshot, Alert, MetricSeries, ControlCommand,
    AlertSeverity, ControlAction,
    get_dashboard_backend
)


class TestStateAggregator:
    def test_aggregate(self):
        a = StateAggregator()
        r = a.aggregate({"mod1": {"health": 0.9, "coherence": 0.8}})
        assert r["modules_total"] == 1
        assert r["avg_health"] == 0.9

    def test_multiple(self):
        a = StateAggregator()
        r = a.aggregate({
            "m1": {"health": 1.0},
            "m2": {"health": 0.0},
        })
        assert r["avg_health"] == 0.5
        assert r["modules_online"] == 1

    def test_get_report(self):
        a = StateAggregator()
        a.aggregate({"m1": {"health": 0.5}})
        r = a.get_report()
        assert r["snapshots_stored"] == 1


class TestSnapshotEngine:
    def test_capture(self):
        se = SnapshotEngine()
        s = se.capture({"l1": {}}, {"m1": {}}, {"metric": 1.0})
        assert s.snapshot_id.startswith("snap_")

    def test_get_latest(self):
        se = SnapshotEngine()
        se.capture({}, {}, {})
        latest = se.get_latest()
        assert latest is not None

    def test_compare(self):
        se = SnapshotEngine()
        s1 = se.capture({}, {}, {"a": 1.0})
        s2 = se.capture({}, {}, {"a": 2.0})
        diff = se.compare(s1.snapshot_id, s2.snapshot_id)
        assert diff["metric_diffs"]["a"]["delta"] == 1.0

    def test_get_report(self):
        se = SnapshotEngine()
        se.capture({}, {}, {})
        r = se.get_report()
        assert r["snapshots"] == 1


class TestMetricStreamer:
    def test_push_and_get(self):
        ms = MetricStreamer()
        ms.push("m1", 1.0)
        ms.push("m1", 2.0)
        assert ms.get_current("m1") == 2.0

    def test_series(self):
        ms = MetricStreamer()
        ms.push("m1", 1.0)
        series = ms.get_series("m1")
        assert len(series) == 1

    def test_trend_rising(self):
        ms = MetricStreamer()
        for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
            ms.push("m1", v)
        assert ms.get_trend("m1") == "RISING"

    def test_trend_falling(self):
        ms = MetricStreamer()
        for v in [5.0, 4.0, 3.0, 2.0, 1.0]:
            ms.push("m1", v)
        assert ms.get_trend("m1") == "FALLING"

    def test_get_report(self):
        ms = MetricStreamer()
        ms.push("x", 1.0)
        r = ms.get_report()
        assert r["streams"] == 1


class TestAlertManager:
    def test_raise(self):
        am = AlertManager()
        a = am.raise_alert(AlertSeverity.CRITICAL, "mod1", "test")
        assert a.severity == AlertSeverity.CRITICAL

    def test_check_thresholds(self):
        am = AlertManager()
        triggered = am.check_thresholds("mod1", {"health": 0.1})
        assert len(triggered) == 1

    def test_acknowledge(self):
        am = AlertManager()
        a = am.raise_alert(AlertSeverity.INFO, "m1", "msg")
        assert am.acknowledge(a.alert_id) is True
        assert len(am.get_active()) == 0

    def test_get_report(self):
        am = AlertManager()
        am.raise_alert(AlertSeverity.WARNING, "m1", "w")
        r = am.get_report()
        assert r["total_alerts"] == 1


class TestControlProxy:
    def test_issue(self):
        cp = ControlProxy()
        c = cp.issue(ControlAction.TRIGGER_TEST, "mod1")
        assert c.action == ControlAction.TRIGGER_TEST

    def test_execute_no_handler(self):
        cp = ControlProxy()
        c = cp.issue(ControlAction.TRIGGER_TEST, "mod1")
        r = cp.execute(c.command_id)
        assert r["success"] is False

    def test_execute_with_handler(self):
        cp = ControlProxy()
        cp.register_handler(ControlAction.TRIGGER_TEST, lambda t, p: "done")
        c = cp.issue(ControlAction.TRIGGER_TEST, "mod1")
        r = cp.execute(c.command_id)
        assert r["success"] is True

    def test_get_report(self):
        cp = ControlProxy()
        cp.issue(ControlAction.TRIGGER_TEST, "m1")
        r = cp.get_report()
        assert r["commands"] == 1


class TestDashboardBackend:
    def test_init(self):
        db = DashboardBackend()
        assert db.VERSION == "190.0.0"
        assert len(db.streamer.streams) == 24  # 12 lines × 2 metrics

    def test_update(self):
        db = DashboardBackend()
        r = db.update({"mod1": {"health": 0.9, "coherence": 0.8}})
        assert r["cycle"] == 1
        assert r["avg_health"] == 0.9

    def test_get_dashboard_data(self):
        db = DashboardBackend()
        db.update({"mod1": {"health": 0.9}})
        d = db.get_dashboard_data()
        assert d["version"] == "190.0.0"
        assert "alliance" in d
        assert "alerts" in d

    def test_get_status(self):
        db = DashboardBackend()
        db.update({"mod1": {"health": 0.5}})
        s = db.get_status()
        assert s["version"] == "190.0.0"

    def test_singleton(self):
        d1 = get_dashboard_backend()
        d2 = get_dashboard_backend()
        assert d1 is d2

# Total: 33 tests
