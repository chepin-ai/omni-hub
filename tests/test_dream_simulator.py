"""
OMNI-HUB Dream Simulator Tests v42
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.dream_simulator import (
    DreamScenario, VirtualCycleEngine, DreamSimulator, get_dream_simulator,
)


class TestVirtualCycleEngine:
    def test_simulate_basic(self):
        eng = VirtualCycleEngine()
        initial = {"level": 5, "energy": 1000.0, "phi": 0.5}
        result = eng.simulate(initial, cycles=50)
        assert "level" in result
        assert "phi" in result

    def test_energy_decay(self):
        eng = VirtualCycleEngine()
        initial = {"energy": 1000.0}
        result = eng.simulate(initial, cycles=100)
        assert result["energy"] < 1000.0

    def test_perturbation(self):
        eng = VirtualCycleEngine()
        initial = {"level": 5, "energy": 1000.0}
        perturbs = [{"at_cycle": 10, "changes": {"level": 99}}]
        result = eng.simulate(initial, cycles=20, perturbations=perturbs)
        assert result["level"] == 99

    def test_phase_transition(self):
        eng = VirtualCycleEngine()
        initial = {"level": 0, "energy": 1e6}
        result = eng.simulate(initial, cycles=100)
        assert "phase" in result


class TestDreamSimulator:
    def test_initialization(self):
        ds = DreamSimulator()
        assert ds.dream_count == 0

    def test_dream(self):
        ds = DreamSimulator()
        state = {"level": 10, "energy": 1e5, "phi": 0.8}
        dream = ds.dream(state, scenario_name="energy_crisis", cycles=50)
        assert dream.name == "energy_crisis"
        assert dream.cycles_simulated == 50
        assert dream.confidence >= 0.0
        assert dream.confidence <= 1.0

    def test_dream_auto_scenario(self):
        ds = DreamSimulator()
        state = {"level": 5, "energy": 100.0, "phi": 0.5}
        dream = ds.dream(state)
        assert dream.name in ds.SCENARIOS

    def test_worst_case(self):
        ds = DreamSimulator()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5}
        ds.dream(state, "phiCollapse")
        ds.dream(state, "rapid_evolution")
        worst = ds.get_worst_case()
        assert worst is not None

    def test_best_case(self):
        ds = DreamSimulator()
        state = {"level": 5, "energy": 1000.0, "phi": 0.5}
        ds.dream(state, "phiCollapse")
        ds.dream(state, "rapid_evolution")
        best = ds.get_best_case()
        assert best is not None

    def test_get_status(self):
        ds = DreamSimulator()
        ds.dream({"level": 5, "energy": 100.0, "phi": 0.5})
        status = ds.get_status()
        assert status["dream_count"] == 1
        assert "avg_confidence" in status


class TestGlobalEngine:
    def test_get_dream_simulator(self):
        g = get_dream_simulator()
        assert g is not None
        assert isinstance(g, DreamSimulator)
