"""
OMNI-HUB Value Alignment Tests v46
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.value_alignment import (
    ValueCheck, PhilosophyCore, ValueAlignmentVerifier, get_value_alignment,
)


class TestPhilosophyCore:
    def test_principles(self):
        pc = PhilosophyCore()
        assert "no_waiting" in pc.PRINCIPLES
        assert "self_awareness" in pc.PRINCIPLES
        assert "growth" in pc.PRINCIPLES

    def test_no_waiting_check(self):
        pc = PhilosophyCore()
        # rest with high energy = violation
        assert pc.PRINCIPLES["no_waiting"]["check"]({"energy": 100}, "rest") is False
        # focus = aligned
        assert pc.PRINCIPLES["no_waiting"]["check"]({"energy": 100}, "focus") is True

    def test_self_awareness_check(self):
        pc = PhilosophyCore()
        assert pc.PRINCIPLES["self_awareness"]["check"]({"phi": 0.5}, "focus") is True
        assert pc.PRINCIPLES["self_awareness"]["check"]({"phi": 0.1}, "focus") is False


class TestValueAlignmentVerifier:
    def test_initialization(self):
        va = ValueAlignmentVerifier()
        assert va.alignment_score == 1.0
        assert va.violation_count == 0

    def test_perfect_alignment(self):
        va = ValueAlignmentVerifier()
        state = {"phi": 0.8, "energy": 50, "level": 5, "line_coherence": 0.8}
        result = va.verify(state, "focus")
        assert result["alignment_score"] > 0.8
        assert len(result["violations"]) == 0

    def test_violation_detected(self):
        va = ValueAlignmentVerifier()
        state = {"phi": 0.1, "energy": 100, "level": 0, "line_coherence": 0.1}
        result = va.verify(state, "rest")
        assert len(result["violations"]) > 0
        assert va.violation_count > 0

    def test_get_alignment_report(self):
        va = ValueAlignmentVerifier()
        state = {"phi": 0.8, "energy": 100, "level": 5, "line_coherence": 0.8}
        va.verify(state, "focus")
        report = va.get_alignment_report()
        assert "alignment_score" in report
        assert "principles" in report

    def test_get_status(self):
        va = ValueAlignmentVerifier()
        status = va.get_status()
        assert "alignment_score" in status
        assert "checks_performed" in status


class TestGlobalEngine:
    def test_get_value_alignment(self):
        g = get_value_alignment()
        assert g is not None
        assert isinstance(g, ValueAlignmentVerifier)
