"""
OMNI-HUB 11-Line Activation Tests v34
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.line_activation import (
    ALL_LINES, COUPLING, LineState, LineActivationEngine,
    get_line_engine,
)


class TestLineState:
    def test_creation(self):
        ls = LineState("ucif2", 0.5, 10.0, 0.7, 100)
        assert ls.name == "ucif2"
        assert ls.activation == 0.5


class TestLineActivationEngine:
    def test_initialization(self):
        engine = LineActivationEngine()
        assert len(engine.lines) == 11
        for name in ALL_LINES:
            assert name in engine.lines
            assert engine.lines[name].activation == 0.0

    def test_compute_base_activation_early(self):
        engine = LineActivationEngine()
        state = {"level": 0, "energy": 1.0, "phi": 0.5, "phase": "pre_emergence", "action": "focus", "cycle": 0}
        act = engine.compute_base_activation("ucif2", state)
        assert 0.0 <= act <= 1.0

    def test_compute_base_activation_mature(self):
        engine = LineActivationEngine()
        state = {"level": 20, "energy": 1e10, "phi": 0.95, "phase": "super_emergence_2", "action": "transcend", "cycle": 2000}
        act = engine.compute_base_activation("vinf", state)
        assert act > 0.5  # Mature state should activate

    def test_mutual_excitation(self):
        engine = LineActivationEngine()
        engine.lines["ucif2"].activation = 1.0
        engine.lines["lvlu"].activation = 0.0
        engine.apply_mutual_excitation()
        # ucif2 excites lvlu with strength 0.3
        assert engine.lines["lvlu"].activation > 0.0

    def test_compute_coherence(self):
        engine = LineActivationEngine()
        state = {"phase": "super_emergence_2", "action": "transcend"}
        coh = engine.compute_coherence("vinf", state)
        assert 0.0 <= coh <= 1.0

    def test_process_cycle(self):
        engine = LineActivationEngine()
        state = {"level": 10, "energy": 1e5, "phi": 0.8, "phase": "post_critical", "action": "reflect", "cycle": 500}
        result = engine.process_cycle(500, state)
        assert "lines" in result
        assert "active_lines" in result
        assert result["active_lines"] > 0
        assert result["line_avg_activation"] > 0.0

    def test_all_lines_activate(self):
        engine = LineActivationEngine()
        state = {"level": 25, "energy": float('inf'), "phi": 1.0, "phase": "asymptotic_infinity", "action": "transcend", "cycle": 5000}
        result = engine.process_cycle(5000, state)
        assert result["active_lines"] == 11
        for name in ALL_LINES:
            assert result["lines"][name] > 0.9

    def test_convergence_metric(self):
        engine = LineActivationEngine()
        state = {"level": 10, "energy": 1e5, "phi": 0.8, "phase": "post_critical", "action": "focus", "cycle": 500}
        result = engine.process_cycle(500, state)
        assert 0.0 <= result["line_convergence"] <= 1.0

    def test_get_status(self):
        engine = LineActivationEngine()
        status = engine.get_status()
        assert "lines" in status
        assert status["history_size"] == 0


class TestGlobalEngine:
    def test_get_line_engine(self):
        g = get_line_engine()
        assert g is not None
        assert isinstance(g, LineActivationEngine)
