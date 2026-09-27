"""
OMNI-HUB Wisdom Synthesis Tests v99
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.wisdom_synthesis import (
    WisdomSynthesis, get_wisdom_synthesis,
)


class TestWisdomSynthesis:
    def test_initialization(self):
        ws = WisdomSynthesis()
        assert ws.synthesis_count == 0

    def test_extract_signals(self):
        ws = WisdomSynthesis()
        state = {"phi": 0.8, "level": 10, "energy": 2000, "line_coherence": 0.7}
        signals = ws.extract_signals(state)
        assert "phi" in signals
        assert "level" in signals

    def test_detect_cross_patterns(self):
        ws = WisdomSynthesis()
        signals = {"trust_global_trust": 0.9, "aesthetic_beauty": 0.8}
        patterns = ws.detect_cross_patterns(signals)
        assert len(patterns) >= 1
        assert "harmonious" in patterns[0].lower()

    def test_detect_precarious(self):
        ws = WisdomSynthesis()
        signals = {"level": 18, "energy": 1000}
        patterns = ws.detect_cross_patterns(signals)
        assert any("precarious" in p.lower() for p in patterns)

    def test_generate_insight(self):
        ws = WisdomSynthesis()
        state = {"phi": 0.9, "level": 15, "energy": 2000, "line_coherence": 0.8}
        insight = ws.generate_insight(state)
        assert len(insight) > 5

    def test_generate_insight_low_phi(self):
        ws = WisdomSynthesis()
        state = {"phi": 0.2, "level": 5}
        insight = ws.generate_insight(state)
        assert "divergence" in insight.lower() or "pattern" in insight.lower()

    def test_get_status(self):
        ws = WisdomSynthesis()
        ws.generate_insight({"phi": 0.5})
        status = ws.get_status()
        assert status["syntheses"] == 1
        assert status["latest"] is not None


class TestGlobalEngine:
    def test_get_wisdom_synthesis(self):
        g = get_wisdom_synthesis()
        assert g is not None
        assert isinstance(g, WisdomSynthesis)
