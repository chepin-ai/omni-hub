"""
OMNI-HUB Synchronicity Tests v121
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.synchronicity import Synchronicity, get_synchronicity


class TestSynchronicity:
    def test_initialization(self):
        sync = Synchronicity()
        assert sync.event_count == 0

    def test_record_event(self):
        sync = Synchronicity()
        sync.record_event({"phi": 0.8, "level": 5, "line_coherence": 0.9})
        assert sync.event_count == 1
        assert len(sync.events) == 1

    def test_detect_coincidences_empty(self):
        sync = Synchronicity()
        coincidences = sync.detect_coincidences()
        assert len(coincidences) == 0

    def test_detect_coincidences_phi_cluster(self):
        sync = Synchronicity()
        for _ in range(5):
            sync.record_event({"phi": 0.81, "level": 5, "line_coherence": 0.9})
        coincidences = sync.detect_coincidences()
        assert len(coincidences) >= 1
        assert any(c["type"] == "phi_cluster" for c in coincidences)

    def test_sense_no_coincidence(self):
        sync = Synchronicity()
        result = sync.sense({"phi": 0.5, "level": 1, "line_coherence": 0.5})
        assert result["sensed"] is False

    def test_sense_with_coincidence(self):
        sync = Synchronicity()
        for _ in range(5):
            sync.record_event({"phi": 0.81, "level": 5, "line_coherence": 0.9})
        result = sync.sense({"phi": 0.82, "level": 5, "line_coherence": 0.91})
        assert result["sensed"] is True
        assert result["significance"] in ["high", "medium"]

    def test_get_status(self):
        sync = Synchronicity()
        sync.sense({"phi": 0.5, "level": 1, "line_coherence": 0.5})
        status = sync.get_status()
        assert status["events"] == 1


class TestGlobalEngine:
    def test_get_synchronicity(self):
        g = get_synchronicity()
        assert g is not None
        assert isinstance(g, Synchronicity)
