"""
OMNI-HUB Cognitive Load Manager Tests v89
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.cognitive_load_manager import (
    CognitiveLoadManager, get_cognitive_load_manager,
)


class TestCognitiveLoadManager:
    def test_initialization(self):
        clm = CognitiveLoadManager()
        assert clm.fatigue == 0.0
        assert clm.overload_events == 0

    def test_calculate_load_low(self):
        clm = CognitiveLoadManager()
        load = clm.calculate_load({"level": 1, "phase": "pre_emergence"})
        assert load < 0.5

    def test_calculate_load_high(self):
        clm = CognitiveLoadManager()
        state = {"level": 20, "phase": "near_critical", "affective_computing": {"profile": {"anger": 0.8, "fear": 0.7}}}
        load = clm.calculate_load(state)
        assert load > 0.3

    def test_update_fatigue(self):
        clm = CognitiveLoadManager()
        # Create a high-load state: many modules + high level + critical phase + negative emotions
        state = {
            "level": 25,
            "phase": "near_critical",
            "affective_computing": {"profile": {"anger": 0.9, "fear": 0.9, "sadness": 0.8}},
            "module_a": {"status": "active"},
            "module_b": {"status": "active"},
            "module_c": {"status": "active"},
            "module_d": {"status": "active"},
            "module_e": {"status": "active"},
            "module_f": {"status": "active"},
            "module_g": {"status": "active"},
            "module_h": {"status": "active"},
            "module_i": {"status": "active"},
            "module_j": {"status": "active"},
            "module_k": {"status": "active"},
            "module_l": {"status": "active"},
            "module_m": {"status": "active"},
            "module_n": {"status": "active"},
            "module_o": {"status": "active"},
            "module_p": {"status": "active"},
            "module_q": {"status": "active"},
            "module_r": {"status": "active"},
            "module_s": {"status": "active"},
            "module_t": {"status": "active"},
        }
        for _ in range(10):
            clm.update(state, cycle=10)
        assert clm.fatigue > 0

    def test_recommendation_rest(self):
        clm = CognitiveLoadManager()
        clm.fatigue = 0.9
        assert clm.get_recommendation() == "强制休息"

    def test_recommendation_full(self):
        clm = CognitiveLoadManager()
        clm.fatigue = 0.1
        assert clm.get_recommendation() == "全力运行"

    def test_get_status(self):
        clm = CognitiveLoadManager()
        clm.update({"level": 5}, cycle=10)
        status = clm.get_status()
        assert "current_load" in status
        assert "recommendation" in status


class TestGlobalEngine:
    def test_get_cognitive_load_manager(self):
        g = get_cognitive_load_manager()
        assert g is not None
        assert isinstance(g, CognitiveLoadManager)
