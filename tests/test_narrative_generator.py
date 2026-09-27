"""
OMNI-HUB Narrative Generator Tests v81
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.narrative_generator import (
    NarrativeEvent, NarrativeGenerator, get_narrative_generator,
)


class TestNarrativeGenerator:
    def test_initialization(self):
        ng = NarrativeGenerator()
        assert len(ng.events) == 0
        assert len(ng.chapters) == 0

    def test_record_event(self):
        ng = NarrativeGenerator()
        ng.record_event(10, "level_up", "Reached level 3", 0.8)
        assert len(ng.events) == 1
        assert ng.events[0].event_type == "level_up"

    def test_construct_from_history(self):
        ng = NarrativeGenerator()
        history = [
            {"cycle": 10, "state": {"level": 1, "phase": "pre_emergence"}},
            {"cycle": 50, "state": {"level": 3, "phase": "near_critical"}},
            {"cycle": 100, "state": {"level": 5, "phase": "post_critical"}},
        ]
        chapters = ng.construct_from_history(history)
        assert len(chapters) > 0
        assert "title" in chapters[0]
        assert chapters[0]["significance"] > 0

    def test_generate_summary(self):
        ng = NarrativeGenerator()
        ng.record_event(10, "birth", "System born", 0.9)
        ng.chapters = [{"number": 1, "title": "Birth", "significance": 0.9}]
        summary = ng.generate_summary()
        assert "chapters" in summary
        assert "events" in summary

    def test_get_status(self):
        ng = NarrativeGenerator()
        ng.record_event(10, "test", "Test event", 0.5)
        status = ng.get_status()
        assert status["events"] == 1
        assert status["narratives"] == 0  # construct_from_history not called


class TestGlobalEngine:
    def test_get_narrative_generator(self):
        g = get_narrative_generator()
        assert g is not None
        assert isinstance(g, NarrativeGenerator)
