"""
OMNI-HUB Temporal Reasoning Tests v87
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.temporal_reasoning import (
    TemporalEvent, TemporalReasoning, get_temporal_reasoning,
)


class TestTemporalReasoning:
    def test_initialization(self):
        tr = TemporalReasoning()
        assert len(tr.events) == 0

    def test_record_event(self):
        tr = TemporalReasoning()
        tr.record_event(10, "phase_change", 1, 0.8)
        assert len(tr.events) == 1
        assert tr.events[0].event_type == "phase_change"

    def test_detect_rhythms(self):
        tr = TemporalReasoning()
        for i in range(12):
            tr.record_event(i * 20, "heartbeat", 1, 0.5)
        rhythms = tr.detect_rhythms()
        assert "heartbeat" in rhythms
        assert rhythms["heartbeat"] == 20

    def test_predict_next(self):
        tr = TemporalReasoning()
        for i in range(12):
            tr.record_event(i * 20, "heartbeat", 1, 0.5)
        tr.detect_rhythms()
        next_c = tr.predict_next("heartbeat")
        assert next_c == 240

    def test_build_schedule(self):
        tr = TemporalReasoning()
        for i in range(12):
            tr.record_event(i * 20, "check", 1, 0.5)
        schedule = tr.build_schedule({"phase": "test"}, cycle=240)
        assert len(schedule) > 0
        assert "predicted_cycle" in schedule[0]

    def test_get_temporal_summary(self):
        tr = TemporalReasoning()
        tr.record_event(10, "a", 1, 0.5)
        tr.record_event(30, "b", 1, 0.5)
        summary = tr.get_temporal_summary()
        assert summary["events"] == 2
        assert summary["time_span"] == 20

    def test_get_status(self):
        tr = TemporalReasoning()
        tr.record_event(10, "a", 1, 0.5)
        status = tr.get_status()
        assert status["events"] == 1
        assert "summary" in status


class TestGlobalEngine:
    def test_get_temporal_reasoning(self):
        g = get_temporal_reasoning()
        assert g is not None
        assert isinstance(g, TemporalReasoning)
