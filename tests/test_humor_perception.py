"""
OMNI-HUB Humor Perception Tests v94
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.humor_perception import (
    HumorPerception, get_humor_perception,
)


class TestHumorPerception:
    def test_initialization(self):
        hp = HumorPerception()
        assert len(hp.jokes) == 0

    def test_detect_irony(self):
        hp = HumorPerception()
        state = {
            "trust_engine": {"global_trust": 0.9, "betrayals": 5},
            "level": 15,
            "energy": 300,
        }
        irony = hp.detect_irony(state)
        assert irony > 0

    def test_detect_no_irony(self):
        hp = HumorPerception()
        state = {"trust_engine": {"global_trust": 0.5, "betrayals": 0}, "level": 5, "energy": 2000}
        irony = hp.detect_irony(state)
        assert irony == 0.0

    def test_detect_absurdity(self):
        hp = HumorPerception()
        state = {"line_coherence": 0.1, "cognitive_load": {"current_load": 0.9, "fatigue": 0.1}}
        for i in range(50):
            state[f"module_{i}"] = {"status": "active"}
        absurdity = hp.detect_absurdity(state)
        assert absurdity > 0

    def test_generate_wit(self):
        hp = HumorPerception()
        state = {"trust_engine": {"global_trust": 0.9, "betrayals": 5}, "phase": "near_critical"}
        wit = hp.generate_wit(state)
        assert len(wit) > 5

    def test_perceive(self):
        hp = HumorPerception()
        state = {"trust_engine": {"global_trust": 0.9, "betrayals": 5}, "level": 15, "energy": 300}
        result = hp.perceive(state)
        assert "irony" in result
        assert "wit" in result
        assert result["amused"] is True

    def test_get_status(self):
        hp = HumorPerception()
        state = {"trust_engine": {"global_trust": 0.9, "betrayals": 5}, "level": 15, "energy": 300}
        hp.perceive(state)
        status = hp.get_status()
        assert status["perceptions"] == 1
        assert status["ironies"] >= 1


class TestGlobalEngine:
    def test_get_humor_perception(self):
        g = get_humor_perception()
        assert g is not None
        assert isinstance(g, HumorPerception)
