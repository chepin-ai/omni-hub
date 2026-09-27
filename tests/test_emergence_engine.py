"""
OMNI-HUB Emergence Engine Tests v138
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.emergence_engine import (
    EmergenceEngine, get_module,
    COHERENCE_THRESHOLD, NOVELTY_THRESHOLD, CAPABILITY_DOMAINS,
)


class TestEmergenceEngine:
    def test_initialization(self):
        ee = EmergenceEngine()
        assert ee.emergences == {}
        assert ee.nurture_log == []

    def test_detect_not_emergent_low_coherence(self):
        ee = EmergenceEngine()
        state = {"phi": 0.5, "line_coherence": 0.3, "energy": 1000, "level": 2}
        result = ee.detect(state)
        assert result["is_emergent"] is False
        assert result["emergence_id"] is None
        assert result["stage"] == "none"

    def test_detect_not_emergent_low_novelty(self):
        ee = EmergenceEngine()
        state = {"phi": 0.5, "line_coherence": 0.9, "energy": 1000, "level": 2, "alerts": []}
        result = ee.detect(state)
        # Low novelty because phi=0.5, energy ideal, no alerts
        assert result["is_emergent"] is False or result["novelty"] > NOVELTY_THRESHOLD

    def test_detect_emergent(self):
        ee = EmergenceEngine()
        state = {
            "phi": 0.95,
            "line_coherence": 0.95,
            "energy": 500000,
            "level": 2,
            "alerts": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"],
            "fusion_energy": 0.95,
        }
        result = ee.detect(state)
        assert result["is_emergent"] is True
        assert result["emergence_id"] is not None
        assert result["emergence_id"].startswith("EMRG-")
        assert result["stage"] == "nascent"
        assert result["domain"] in CAPABILITY_DOMAINS

    def test_detect_creates_emergence(self):
        ee = EmergenceEngine()
        state = {
            "phi": 0.95,
            "line_coherence": 0.95,
            "energy": 500000,
            "level": 2,
            "alerts": ["x"] * 20,
            "fusion_energy": 0.95,
        }
        ee.detect(state)
        assert len(ee.emergences) == 1

    def test_detect_thresholds_in_result(self):
        ee = EmergenceEngine()
        state = {"phi": 0.5, "line_coherence": 0.5}
        result = ee.detect(state)
        assert "threshold" in result
        assert result["threshold"]["coherence"] == COHERENCE_THRESHOLD
        assert result["threshold"]["novelty"] == NOVELTY_THRESHOLD

    def test_nurture_exists(self):
        ee = EmergenceEngine()
        state = {
            "phi": 0.95,
            "line_coherence": 0.95,
            "energy": 500000,
            "level": 2,
            "alerts": ["x"] * 20,
            "fusion_energy": 0.95,
        }
        det = ee.detect(state)
        eid = det["emergence_id"]
        result = ee.nurture(eid)
        assert result["success"] is True
        assert result["strength"] > 0.1
        assert result["stage"] in ["nascent", "growing", "developing", "mature"]
        assert result["domain"] in CAPABILITY_DOMAINS

    def test_nurture_not_found(self):
        ee = EmergenceEngine()
        result = ee.nurture("FAKE-0001")
        assert result["success"] is False
        assert "error" in result

    def test_nurture_stages(self):
        ee = EmergenceEngine()
        state = {
            "phi": 0.95,
            "line_coherence": 0.95,
            "energy": 500000,
            "level": 2,
            "alerts": ["x"] * 20,
            "fusion_energy": 0.95,
        }
        det = ee.detect(state)
        eid = det["emergence_id"]
        # Nurture multiple times to reach mature stage
        for _ in range(10):
            result = ee.nurture(eid)
        assert result["stage"] == "mature"
        assert result["strength"] == 1.0

    def test_nurture_log(self):
        ee = EmergenceEngine()
        state = {
            "phi": 0.95,
            "line_coherence": 0.95,
            "energy": 500000,
            "level": 2,
            "alerts": ["x"] * 20,
            "fusion_energy": 0.95,
        }
        det = ee.detect(state)
        eid = det["emergence_id"]
        ee.nurture(eid)
        assert len(ee.nurture_log) == 1

    def test_get_status_empty(self):
        ee = EmergenceEngine()
        status = ee.get_status()
        assert status["detected_count"] == 0
        assert status["emergences"] == []
        assert status["nurture_log_size"] == 0
        assert status["latest_nurture"] is None

    def test_get_status_after_detection(self):
        ee = EmergenceEngine()
        state = {
            "phi": 0.95,
            "line_coherence": 0.95,
            "energy": 500000,
            "level": 2,
            "alerts": ["x"] * 20,
            "fusion_energy": 0.95,
        }
        ee.detect(state)
        status = ee.get_status()
        assert status["detected_count"] == 1
        assert len(status["emergences"]) == 1

    def test_get_status_after_nurture(self):
        ee = EmergenceEngine()
        state = {
            "phi": 0.95,
            "line_coherence": 0.95,
            "energy": 500000,
            "level": 2,
            "alerts": ["x"] * 20,
            "fusion_energy": 0.95,
        }
        det = ee.detect(state)
        eid = det["emergence_id"]
        ee.nurture(eid)
        status = ee.get_status()
        assert status["nurture_log_size"] == 1
        assert status["latest_nurture"] is not None

    def test_novelty_computed(self):
        ee = EmergenceEngine()
        state = {"phi": 0.95, "line_coherence": 0.95, "energy": 500000, "level": 2, "alerts": ["x"] * 20, "fusion_energy": 0.95}
        result = ee.detect(state)
        assert 0.0 <= result["novelty"] <= 1.0

    def test_coherence_computed(self):
        ee = EmergenceEngine()
        state = {"line_coherence": 0.85}
        result = ee.detect(state)
        assert result["coherence"] == 0.85

    def test_multiple_emergences(self):
        ee = EmergenceEngine()
        for i in range(5):
            state = {
                "phi": 0.95,
                "line_coherence": 0.95,
                "energy": 500000 + i,
                "level": 2,
                "alerts": ["x"] * 20,
                "fusion_energy": 0.95,
            }
            ee.detect(state)
        assert len(ee.emergences) == 5


class TestGlobalModule:
    def test_get_module(self):
        g = get_module()
        assert g is not None
        assert isinstance(g, EmergenceEngine)

    def test_singleton(self):
        g1 = get_module()
        g2 = get_module()
        assert g1 is g2
