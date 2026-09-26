"""
OMNI-HUB Decision Forest Tests v60
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.decision_forest import (
    DecisionPath, PathSimulator, DecisionForest, get_decision_forest,
)


class TestPathSimulator:
    def test_simulate_focus(self):
        ps = PathSimulator()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5, "line_coherence": 0.5}
        result = ps.simulate(state, ["focus"])
        assert result["level"] > 5
        assert result["phi"] > 0.5

    def test_simulate_rest(self):
        ps = PathSimulator()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5, "line_coherence": 0.5}
        result = ps.simulate(state, ["rest"])
        assert result["energy"] > 1000.0
        assert result["phi"] < 0.5

    def test_simulate_transcend(self):
        ps = PathSimulator()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5, "line_coherence": 0.5}
        result = ps.simulate(state, ["transcend"])
        assert result["level"] > 5
        assert result["phi"] > 0.5


class TestDecisionForest:
    def test_initialization(self):
        df = DecisionForest()
        assert len(df.paths) == 0

    def test_evaluate(self):
        df = DecisionForest()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5, "line_coherence": 0.5}
        paths = df.evaluate(state)
        assert len(paths) == 5
        assert paths[0].path_score >= paths[-1].path_score  # sorted

    def test_get_best_path(self):
        df = DecisionForest()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5, "line_coherence": 0.5}
        df.evaluate(state)
        best = df.get_best_path()
        assert best is not None
        assert best.path_score > 0

    def test_get_diverse_recommendations(self):
        df = DecisionForest()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5, "line_coherence": 0.5}
        df.evaluate(state)
        recs = df.get_diverse_recommendations(3)
        assert len(recs) == 3

    def test_get_status(self):
        df = DecisionForest()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5, "line_coherence": 0.5}
        df.evaluate(state)
        status = df.get_status()
        assert "best_path" in status
        assert "best_score" in status


class TestGlobalEngine:
    def test_get_decision_forest(self):
        g = get_decision_forest()
        assert g is not None
        assert isinstance(g, DecisionForest)
