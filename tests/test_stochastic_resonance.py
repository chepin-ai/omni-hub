"""
OMNI-HUB Stochastic Resonance Tests v111
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.stochastic_resonance import (
    StochasticResonance, get_stochastic_resonance,
)


class TestStochasticResonance:
    def test_initialization(self):
        sr = StochasticResonance()
        assert sr.event_count == 0

    def test_inject_noise(self):
        sr = StochasticResonance()
        noisy = sr.inject_noise(0.5, noise_level=0.1)
        assert 0.4 <= noisy <= 0.6

    def test_detect_weak_signal(self):
        sr = StochasticResonance()
        state = {"phi": 0.4, "line_coherence": 0.3}
        weak = sr.detect_weak_signal(state)
        assert "phi" in weak
        assert "coherence" in weak

    def test_detect_no_weak_signal(self):
        sr = StochasticResonance()
        state = {"phi": 0.9, "line_coherence": 0.9, "trust_engine": {"global_trust": 0.9}, "aesthetic_judgment": {"beauty": 0.9}}
        weak = sr.detect_weak_signal(state)
        assert len(weak) == 0

    def test_resonate(self):
        sr = StochasticResonance()
        state = {"phi": 0.4, "line_coherence": 0.3}
        result = sr.resonate(state)
        assert result["amplified"] is True
        assert "amplified_signals" in result

    def test_resonate_no_weak(self):
        sr = StochasticResonance()
        state = {"phi": 0.9, "line_coherence": 0.9, "trust_engine": {"global_trust": 0.9}, "aesthetic_judgment": {"beauty": 0.9}}
        result = sr.resonate(state)
        assert result["amplified"] is False

    def test_get_status(self):
        sr = StochasticResonance()
        sr.resonate({"phi": 0.4, "line_coherence": 0.3})
        status = sr.get_status()
        assert status["resonances"] == 1


class TestGlobalEngine:
    def test_get_stochastic_resonance(self):
        g = get_stochastic_resonance()
        assert g is not None
        assert isinstance(g, StochasticResonance)
