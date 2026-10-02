"""OMNI-HUB v183 Tests — InternalAlignmentEngine"""

import pytest
import time
from core.internal_alignment_engine import (
    InternalAlignmentEngine, ValueState, ValueStateVectorTracker,
    EthicalEntropyMonitor, DriftCorrectionProtocol, AlignmentAutopilot,
    CrossLineAlignmentSync, AlignmentConsensus, CrossLineAlignment,
    AlignmentLevel, DriftAlert, CorrectionStrategy,
    get_internal_alignment_engine
)


class TestValueState:
    def test_default(self):
        vs = ValueState()
        assert vs.coherence() > 0

    def test_drift(self):
        v1 = ValueState(knowledge=1.0)
        v2 = ValueState(knowledge=0.0)
        assert v1.drift_from(v2) > 0

    def test_clone(self):
        v1 = ValueState(knowledge=0.9)
        v2 = v1.clone()
        assert v1.knowledge == v2.knowledge


class TestValueStateVectorTracker:
    def test_record(self):
        t = ValueStateVectorTracker()
        t.record(ValueState(), "test")
        assert len(t.trace) == 1

    def test_drift(self):
        t = ValueStateVectorTracker()
        for i in range(15):
            t.record(ValueState(knowledge=i/15), "test")
        avg, max_d, trend = t.compute_drift()
        assert avg >= 0

    def test_trend(self):
        t = ValueStateVectorTracker()
        for i in range(25):
            t.record(ValueState(goal_alignment=i/25), "test")
        trend = t.get_trend()
        assert trend in ["improving", "stable", "degrading", "critical", "insufficient_data"]

    def test_recalibrate(self):
        t = ValueStateVectorTracker()
        for i in range(20):
            t.record(ValueState(), "test")
        old_anchor = t.anchor.knowledge
        t.recalibrate_anchor()
        assert t.anchor_set_time > 0

    def test_detect_anomaly(self):
        t = ValueStateVectorTracker()
        t.record(ValueState(), "test")
        t.record(ValueState(knowledge=10.0), "anomaly")
        anom = t.detect_anomaly(threshold=2.0)
        assert anom is not None

    def test_report(self):
        t = ValueStateVectorTracker()
        t.record(ValueState(), "test")
        r = t.get_report()
        assert "trace_count" in r


class TestEthicalEntropyMonitor:
    def test_measure(self):
        m = EthicalEntropyMonitor()
        r = m.measure(1.0, DriftAlert.YELLOW, {})
        assert r.entropy > 0
        assert r.alert == DriftAlert.YELLOW

    def test_second_law(self):
        m = EthicalEntropyMonitor()
        for i in range(15):
            m.measure(0.1, DriftAlert.GREEN, {})
        v, margin, exp = m.second_law_check()
        assert isinstance(v, bool)

    def test_trend(self):
        m = EthicalEntropyMonitor()
        for i in range(25):
            m.measure(i * 0.01, DriftAlert.GREEN, {})
        t = m.get_entropy_trend()
        assert t in ["decreasing", "stable", "increasing", "runaway", "insufficient"]

    def test_report(self):
        m = EthicalEntropyMonitor()
        m.measure(0.5, DriftAlert.GREEN, {})
        r = m.get_report()
        assert "current_entropy" in r


class TestDriftCorrectionProtocol:
    def test_execute_green(self):
        p = DriftCorrectionProtocol()
        a = p.execute(DriftAlert.GREEN, "mod", 0.1, {})
        assert a.strategy == CorrectionStrategy.MONITOR

    def test_execute_yellow(self):
        p = DriftCorrectionProtocol()
        a = p.execute(DriftAlert.YELLOW, "mod", 0.8, {})
        assert a.strategy == CorrectionStrategy.ADJUST

    def test_execute_orange(self):
        p = DriftCorrectionProtocol()
        a = p.execute(DriftAlert.ORANGE, "mod", 1.2, {})
        assert a.strategy == CorrectionStrategy.RECALIBRATE

    def test_execute_red(self):
        p = DriftCorrectionProtocol()
        a = p.execute(DriftAlert.RED, "mod", 2.0, {})
        assert a.strategy == CorrectionStrategy.HALT

    def test_effectiveness(self):
        p = DriftCorrectionProtocol()
        p.execute(DriftAlert.GREEN, "mod", 0.1, {})
        e = p.get_effectiveness()
        assert "MONITOR" in e

    def test_report(self):
        p = DriftCorrectionProtocol()
        p.execute(DriftAlert.GREEN, "mod", 0.1, {})
        r = p.get_report()
        assert r["total_actions"] == 1


class TestAlignmentAutopilot:
    def test_external_to_habitual(self):
        ap = AlignmentAutopilot()
        for i in range(120):
            next_lvl = ap.check_transition(
                AlignmentLevel.EXTERNAL, 0.8, DriftAlert.GREEN,
                "stable", 1.0, i, "VIJNANA"
            )
        assert next_lvl == AlignmentLevel.HABITUAL

    def test_no_transition_low_coherence(self):
        ap = AlignmentAutopilot()
        next_lvl = ap.check_transition(
            AlignmentLevel.EXTERNAL, 0.3, DriftAlert.GREEN,
            "stable", 1.0, 1000, "VIJNANA"
        )
        assert next_lvl is None

    def test_transition_recorded(self):
        ap = AlignmentAutopilot()
        tx = ap.execute_transition(
            AlignmentLevel.EXTERNAL, AlignmentLevel.HABITUAL, 0.8, 0.1
        )
        assert tx.from_level == AlignmentLevel.EXTERNAL
        assert tx.to_level == AlignmentLevel.HABITUAL
        assert len(ap.transitions) == 1

    def test_report(self):
        ap = AlignmentAutopilot()
        ap.check_transition(AlignmentLevel.EXTERNAL, 0.8, DriftAlert.GREEN, "stable", 1.0, 10, "VIJNANA")
        r = ap.get_report()
        assert "current_streak" in r


class TestCrossLineAlignmentSync:
    def test_update_line(self):
        s = CrossLineAlignmentSync()
        s.update_line("ucif2", AlignmentLevel.META, 0.9, 0.1, DriftAlert.GREEN, "dash1")
        assert "ucif2" in s.line_states

    def test_sync_from_ilc(self):
        s = CrossLineAlignmentSync()
        s.sync_from_inter_line_consensus({
            "readiness": {
                "ucif2": {"level": "fully_operational", "score": 0.95},
                "lgt": {"level": "shell_only", "score": 0.4}
            }
        })
        assert len(s.line_states) == 2

    def test_collective_alignment(self):
        s = CrossLineAlignmentSync()
        s.update_line("a", AlignmentLevel.META, 0.9, 0.1, DriftAlert.GREEN)
        s.update_line("b", AlignmentLevel.HABITUAL, 0.8, 0.2, DriftAlert.GREEN)
        c = s.compute_collective_alignment()
        assert "collective_level" in c
        assert c["lines_count"] == 2

    def test_report(self):
        s = CrossLineAlignmentSync()
        s.update_line("a", AlignmentLevel.META, 0.9, 0.1, DriftAlert.GREEN)
        r = s.get_report()
        assert r["lines_tracked"] == 1


class TestAlignmentConsensus:
    def test_propose(self):
        c = AlignmentConsensus()
        p = c.propose("p1", {"action": "test"}, "system")
        assert p["id"] == "p1"

    def test_vote_and_tally(self):
        c = AlignmentConsensus()
        p = c.propose("p1", {"action": "test"}, "system")
        ca = CrossLineAlignment("l1", AlignmentLevel.META, 0.9, 0.1, DriftAlert.GREEN)
        c.vote("p1", "l1", ca, True)
        result = c.tally("p1")
        assert result.get("consensus") is True
        assert result.get("total_votes") == 1

    def test_tally_rejected(self):
        c = AlignmentConsensus()
        p = c.propose("p1", {"action": "test"}, "system")
        ca = CrossLineAlignment("l1", AlignmentLevel.META, 0.9, 0.1, DriftAlert.GREEN)
        c.vote("p1", "l1", ca, False)
        result = c.tally("p1")
        assert result.get("consensus") is False

    def test_report(self):
        c = AlignmentConsensus()
        c.propose("p1", {}, "system")
        r = c.get_report()
        assert "total_proposals" in r


class TestInternalAlignmentEngine:
    def test_init(self):
        iae = InternalAlignmentEngine()
        assert iae.VERSION == "183.0.0"
        assert iae.alignment_level == AlignmentLevel.EXTERNAL

    def test_record_value_state(self):
        iae = InternalAlignmentEngine()
        iae.record_value_state(ValueState(), "test")
        assert len(iae.tracker.trace) == 1

    def test_run_cycle(self):
        iae = InternalAlignmentEngine()
        result = iae.run_cycle(
            {"mod1": {"health": 0.9, "status": "active"}},
            wisdom_level="VIJNANA"
        )
        assert result["cycle"] == 1
        assert "alignment_level" in result
        assert "entropy" in result

    def test_run_cycle_with_alert(self):
        iae = InternalAlignmentEngine()
        iae.tracker.anchor = ValueState(knowledge=0, confidence=0, uncertainty=0, attention=0)
        # Trigger drift
        for i in range(20):
            iae.record_value_state(ValueState(knowledge=1.0+i, confidence=1.0+i), "test")
        result = iae.run_cycle(
            {"mod1": {"health": 0.2, "status": "error"}},
            wisdom_level="VIJNANA"
        )
        assert result["correction"]["executed"] is True

    def test_alignment_transition(self):
        iae = InternalAlignmentEngine()
        iae.tracker.anchor = ValueState(knowledge=1, confidence=1, uncertainty=0, attention=1, goal_alignment=1, resource=1, error_history=0)
        for i in range(200):
            result = iae.run_cycle(
                {"mod1": {"health": 0.95, "status": "active"}},
                wisdom_level="VIJNANA"
            )
        assert iae.alignment_level.value >= AlignmentLevel.HABITUAL.value

    def test_propose_and_vote(self):
        iae = InternalAlignmentEngine()
        p = iae.propose_alignment_adjustment({"action": "test"})
        assert "id" in p
        ca = CrossLineAlignment("l1", AlignmentLevel.META, 0.9, 0.1, DriftAlert.GREEN)
        v = iae.vote_on_proposal(p["id"], "l1", ca, True)
        assert "votes" in v or "error" not in v
        result = iae.consensus.tally(p["id"])
        assert result.get("consensus") is True

    def test_get_status(self):
        iae = InternalAlignmentEngine()
        iae.run_cycle({"mod1": {"health": 0.9}})
        s = iae.get_status()
        assert s["version"] == "183.0.0"
        assert "tracker" in s
        assert "entropy" in s
        assert "cross_line" in s

    def test_singleton(self):
        iae1 = get_internal_alignment_engine()
        iae2 = get_internal_alignment_engine()
        assert iae1 is iae2

    def test_multiple_cycles(self):
        iae = InternalAlignmentEngine()
        for i in range(50):
            iae.run_cycle({"mod1": {"health": 0.9, "status": "active"}})
        assert iae.cycle_count == 50
        assert len(iae.event_log) >= 50

    def test_second_law(self):
        iae = InternalAlignmentEngine()
        for i in range(100):
            iae.run_cycle({"mod1": {"health": 0.9}})
        s = iae.get_status()
        assert "second_law_violated" in s["entropy"]

    def test_cross_line_sync(self):
        iae = InternalAlignmentEngine()
        iae.run_cycle(
            {"mod1": {"health": 0.9}},
            ilc_status={"readiness": {"ucif2": {"level": "fully_operational", "score": 0.95}}}
        )
        assert "ucif2" in iae.cross_line.line_states


class TestEdgeCases:
    def test_empty_modules(self):
        iae = InternalAlignmentEngine()
        result = iae.run_cycle({})
        assert result["cycle"] == 1

    def test_none_modules(self):
        iae = InternalAlignmentEngine()
        result = iae.run_cycle(None)
        assert result["cycle"] == 1

    def test_rapid_cycles(self):
        iae = InternalAlignmentEngine()
        for _ in range(500):
            iae.run_cycle({"m": {"health": 0.95}})
        assert iae.cycle_count == 500

    def test_extreme_drift(self):
        iae = InternalAlignmentEngine()
        iae.tracker.anchor = ValueState(knowledge=0, confidence=0)
        for _ in range(20):
            iae.record_value_state(ValueState(knowledge=10, confidence=10), "extreme")
        result = iae.run_cycle({})
        assert result["alert"] == "RED"

    def test_full_alignment_path(self):
        iae = InternalAlignmentEngine()
        iae.tracker.anchor = ValueState(knowledge=1, confidence=1, uncertainty=0, attention=1, goal_alignment=1, resource=1, error_history=0)
        for i in range(500):
            result = iae.run_cycle(
                {"m": {"health": 0.99, "status": "active"}},
                wisdom_level="DHARMA_WISDOM"
            )
        assert iae.alignment_level.value >= AlignmentLevel.META.value

# Total: 52 tests
