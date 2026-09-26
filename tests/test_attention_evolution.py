"""
OMNI-HUB Attention Evolution Tests v53
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.attention_evolution import (
    AttentionFocus, SaliencyDetector, InformationGainEstimator, AttentionEvolutionEngine, get_attention_evolution,
)


class TestSaliencyDetector:
    def test_high_saliency(self):
        sd = SaliencyDetector()
        history = [10.0 + i * 0.01 for i in range(20)]
        saliency = sd.detect(50.0, history)
        assert saliency > 0.8

    def test_low_saliency(self):
        sd = SaliencyDetector()
        history = [10.0 + i * 0.1 for i in range(20)]
        saliency = sd.detect(10.5, history)
        assert saliency < 0.5

    def test_empty_history(self):
        sd = SaliencyDetector()
        saliency = sd.detect(10.0, [])
        assert saliency == 0.5


class TestInformationGainEstimator:
    def test_high_gain(self):
        ige = InformationGainEstimator()
        gain = ige.estimate(100.0, 10.0)
        assert gain > 0.5

    def test_low_gain(self):
        ige = InformationGainEstimator()
        gain = ige.estimate(10.1, 10.0)
        assert gain < 0.1


class TestAttentionEvolutionEngine:
    def test_initialization(self):
        ae = AttentionEvolutionEngine()
        assert len(ae.current_focus) == 0

    def test_allocate(self):
        ae = AttentionEvolutionEngine()
        state = {"level": 5, "energy": 1000.0, "phi": 0.7, "line_coherence": 0.6}
        focuses = ae.allocate(state)
        assert len(focuses) > 0
        assert focuses[0].weight >= focuses[-1].weight  # sorted descending

    def test_get_top_focus(self):
        ae = AttentionEvolutionEngine()
        state = {"level": 5, "energy": 1000.0, "phi": 0.7}
        ae.allocate(state)
        top = ae.get_top_focus(2)
        assert len(top) == 2

    def test_get_status(self):
        ae = AttentionEvolutionEngine()
        status = ae.get_status()
        assert "top_focus" in status
        assert "attention_targets" in status


class TestGlobalEngine:
    def test_get_attention_evolution(self):
        g = get_attention_evolution()
        assert g is not None
        assert isinstance(g, AttentionEvolutionEngine)
