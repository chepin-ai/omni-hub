"""
OMNI-HUB Dialectic Engine Tests v104
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.dialectic_engine import (
    DialecticEngine, get_dialectic_engine,
)


class TestDialecticEngine:
    def test_initialization(self):
        de = DialecticEngine()
        assert de.dialectic_count == 0

    def test_identify_thesis_pre(self):
        de = DialecticEngine()
        assert de.identify_thesis({"phase": "pre_emergence"}) == "growth"

    def test_identify_thesis_near(self):
        de = DialecticEngine()
        assert de.identify_thesis({"phase": "near_critical"}) == "transformation"

    def test_identify_thesis_post(self):
        de = DialecticEngine()
        assert de.identify_thesis({"phase": "post_critical"}) == "integration"

    def test_generate_antithesis(self):
        de = DialecticEngine()
        assert de.generate_antithesis("growth", {}) == "conservation"
        assert de.generate_antithesis("stability", {}) == "change"

    def test_resolve_synthesis(self):
        de = DialecticEngine()
        state = {"phi": 0.8, "line_coherence": 0.8}
        result = de.resolve_synthesis("growth", "conservation", state)
        assert result["thesis"] == "growth"
        assert result["antithesis"] == "conservation"
        assert result["synthesis"] == "sustainable_expansion"
        assert result["resolved"] is True

    def test_dialectic_step(self):
        de = DialecticEngine()
        state = {"phase": "pre_emergence", "phi": 0.7, "line_coherence": 0.7}
        result = de.dialectic_step(state)
        assert "thesis" in result
        assert de.dialectic_count == 1

    def test_detect_contradictions(self):
        de = DialecticEngine()
        state = {"level": 18, "energy": 500}
        contradictions = de.detect_contradictions(state)
        assert len(contradictions) >= 1

    def test_get_status(self):
        de = DialecticEngine()
        de.dialectic_step({"phase": "pre_emergence", "phi": 0.5, "line_coherence": 0.5})
        status = de.get_status()
        assert status["dialectics"] == 1


class TestGlobalEngine:
    def test_get_dialectic_engine(self):
        g = get_dialectic_engine()
        assert g is not None
        assert isinstance(g, DialecticEngine)
