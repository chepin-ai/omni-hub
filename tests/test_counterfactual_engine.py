"""
OMNI-HUB Counterfactual Engine Tests v51
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.counterfactual_engine import (
    Counterfactual, CounterfactualEngine, get_counterfactual_engine,
)


class TestCounterfactualEngine:
    def test_initialization(self):
        cf = CounterfactualEngine()
        assert len(cf.counterfactuals) == 0

    def test_generate_scenarios(self):
        cf = CounterfactualEngine()
        state = {"level": 5, "energy": 1000.0, "phi": 0.6, "line_coherence": 0.7, "cycle": 100}
        history = [{"last_self_drive_action": "focus"}]
        scenarios = cf.generate_scenarios(state, history)
        assert len(scenarios) == 3
        assert any("rest" in s.premise for s in scenarios)

    def test_regret_calculation(self):
        cf = CounterfactualEngine()
        state = {"level": 5, "energy": 1000.0, "phi": 0.6, "line_coherence": 0.7}
        history = [{"last_self_drive_action": "focus"}]
        scenarios = cf.generate_scenarios(state, history)
        for s in scenarios:
            assert s.regret_score >= 0

    def test_get_lessons(self):
        cf = CounterfactualEngine()
        state = {"level": 5, "energy": 1000.0, "phi": 0.6, "line_coherence": 0.7}
        history = [{"last_self_drive_action": "focus"}]
        cf.generate_scenarios(state, history)
        lessons = cf.get_lessons()
        assert len(lessons) > 0
        assert "premise" in lessons[0]

    def test_empty_history(self):
        cf = CounterfactualEngine()
        state = {"level": 5, "energy": 1000.0, "phi": 0.6}
        scenarios = cf.generate_scenarios(state, [])
        # Should still generate scenarios 2 and 3
        assert len(scenarios) >= 2

    def test_get_status(self):
        cf = CounterfactualEngine()
        status = cf.get_status()
        assert "scenarios" in status
        assert "avg_regret" in status


class TestGlobalEngine:
    def test_get_counterfactual_engine(self):
        g = get_counterfactual_engine()
        assert g is not None
        assert isinstance(g, CounterfactualEngine)
