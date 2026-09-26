"""
OMNI-HUB Creative Synthesis Tests v58
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.creative_synthesis import (
    CreativeIdea, RecombinationEngine, HypothesisGenerator, CreativeSynthesisEngine, get_creative_synthesis,
)


class TestRecombinationEngine:
    def test_recombine(self):
        re = RecombinationEngine()
        combos = re.recombine(["a", "b"], ["x", "y"])
        assert len(combos) == 4
        assert "a + x" in combos


class TestHypothesisGenerator:
    def test_cycle_plus_trend(self):
        hg = HypothesisGenerator()
        hyp = hg.generate({"type": "cycle"}, {"type": "trend"})
        assert hyp is not None
        assert "cyclical" in hyp

    def test_anomaly_plus_anomaly(self):
        hg = HypothesisGenerator()
        hyp = hg.generate({"type": "anomaly"}, {"type": "anomaly"})
        assert hyp is not None
        assert "common cause" in hyp

    def test_unknown_combination(self):
        hg = HypothesisGenerator()
        hyp = hg.generate({"type": "unknown"}, {"type": "unknown"})
        assert hyp is None


class TestCreativeSynthesisEngine:
    def test_initialization(self):
        cs = CreativeSynthesisEngine()
        assert len(cs.ideas) == 0

    def test_synthesize_insufficient_sources(self):
        cs = CreativeSynthesisEngine()
        state = {"level": 5}
        ideas = cs.synthesize(state)
        assert len(ideas) == 0

    def test_synthesize_with_patterns(self):
        cs = CreativeSynthesisEngine()
        state = {
            "discovered_patterns": [{"type": "cycle"}, {"type": "trend"}],
            "counterfactuals": [{"premise": "test"}],
        }
        ideas = cs.synthesize(state)
        assert len(ideas) > 0

    def test_get_bridges(self):
        cs = CreativeSynthesisEngine()
        state = {
            "discovered_patterns": [{"type": "cycle"}],
            "counterfactuals": [{"premise": "test"}],
        }
        cs.synthesize(state)
        bridges = cs.get_bridges()
        assert len(bridges) > 0

    def test_get_status(self):
        cs = CreativeSynthesisEngine()
        status = cs.get_status()
        assert "ideas" in status
        assert "avg_novelty" in status


class TestGlobalEngine:
    def test_get_creative_synthesis(self):
        g = get_creative_synthesis()
        assert g is not None
        assert isinstance(g, CreativeSynthesisEngine)
