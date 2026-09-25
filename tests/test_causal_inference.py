"""
OMNI-HUB Causal Inference Tests v45
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.causal_inference import (
    CausalLink, GrangerAnalyzer, CausalInferenceEngine, get_causal_inference,
)


class TestGrangerAnalyzer:
    def test_no_causality(self):
        ga = GrangerAnalyzer()
        # x and y are independent random-like sequences
        import math
        history = []
        for i in range(30):
            x_val = math.sin(i * 1.7) * 10
            y_val = math.cos(i * 2.3) * 10
            history.append({"x": x_val, "y": y_val})
        link = ga.analyze(history, "x", "y")
        assert link is None

    def test_causality_detected(self):
        ga = GrangerAnalyzer()
        # y = x[t-1] + noise — clear causal relationship
        history = []
        for i in range(30):
            x_val = i + (i % 3) * 0.5  # non-linear x
            y_val = (i - 1) * 2 + (i % 5) * 0.3 if i > 0 else 0
            history.append({"x": x_val, "y": y_val})
        link = ga.analyze(history, "x", "y")
        assert link is not None
        assert link.cause == "x"
        assert link.effect == "y"

    def test_insufficient_data(self):
        ga = GrangerAnalyzer()
        history = [{"x": i, "y": i} for i in range(3)]
        link = ga.analyze(history, "x", "y")
        assert link is None

    def test_lag_detection(self):
        ga = GrangerAnalyzer()
        # y follows x with lag 2
        history = []
        for i in range(30):
            x_val = i * 1.5 + (i % 4)
            y_val = ((i - 2) * 3 + (i % 7) * 0.2) if i > 2 else 0
            history.append({"x": x_val, "y": y_val})
        link = ga.analyze(history, "x", "y")
        assert link is not None
        assert link.lag >= 1
        assert link.lag <= 5

    def test_correlation(self):
        ga = GrangerAnalyzer()
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        corr = ga._correlation(x, y)
        assert abs(corr - 1.0) < 0.01


class TestCausalInferenceEngine:
    def test_initialization(self):
        ci = CausalInferenceEngine()
        assert len(ci.discovered_links) == 0

    def test_infer(self):
        ci = CausalInferenceEngine()
        # level causes energy with noise
        history = []
        for i in range(40):
            level = i + (i % 3) * 0.7
            energy = level * 2 + (i % 5) * 0.3
            phi = 0.5 + (i % 7) * 0.01
            history.append({"level": level, "energy": energy, "phi": phi})
        links = ci.infer(history)
        assert len(links) > 0

    def test_get_causal_graph(self):
        ci = CausalInferenceEngine()
        history = []
        for i in range(40):
            level = i + (i % 3) * 0.7
            energy = level * 2 + (i % 5) * 0.3
            history.append({"level": level, "energy": energy, "phi": 0.5})
        ci.infer(history)
        graph = ci.get_causal_graph()
        assert isinstance(graph, dict)

    def test_strongest_link(self):
        ci = CausalInferenceEngine()
        history = []
        for i in range(40):
            level = i + (i % 3) * 0.7
            energy = level * 2 + (i % 5) * 0.3
            history.append({"level": level, "energy": energy, "phi": 0.5})
        ci.infer(history)
        strongest = ci.get_strongest_link()
        assert strongest is not None

    def test_get_status(self):
        ci = CausalInferenceEngine()
        status = ci.get_status()
        assert "discovered_links" in status
        assert "causal_graph" in status


class TestGlobalEngine:
    def test_get_causal_inference(self):
        g = get_causal_inference()
        assert g is not None
        assert isinstance(g, CausalInferenceEngine)
