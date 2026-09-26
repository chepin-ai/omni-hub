"""
OMNI-HUB Evolutionary Optimizer Tests v64
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.evolutionary_optimizer import (
    Genome, EvolutionaryOptimizer, get_evolutionary_optimizer,
)


class TestEvolutionaryOptimizer:
    def test_initialization(self):
        eo = EvolutionaryOptimizer()
        assert len(eo.population) == 6
        assert eo.generation == 0

    def test_evaluate_fitness(self):
        eo = EvolutionaryOptimizer()
        genome = Genome(phi_weight=0.6, energy_threshold=300, rest_threshold=0.3, exploration_rate=0.1)
        state = {"level": 5, "phi": 0.6, "energy": 1000.0}
        fitness = eo.evaluate_fitness(genome, state)
        assert 0 <= fitness <= 1

    def test_evolve(self):
        eo = EvolutionaryOptimizer()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0}
        fittest = eo.evolve(state)
        assert eo.generation == 1
        assert fittest.fitness >= 0

    def test_evolve_improves(self):
        eo = EvolutionaryOptimizer()
        state = {"level": 8, "phi": 0.6, "energy": 1000.0}
        # Run multiple generations
        for _ in range(3):
            eo.evolve(state)
        fittest = eo.get_fittest()
        assert fittest.fitness >= 0

    def test_get_fittest(self):
        eo = EvolutionaryOptimizer()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0}
        eo.evolve(state)
        fittest = eo.get_fittest()
        assert fittest is not None

    def test_get_status(self):
        eo = EvolutionaryOptimizer()
        state = {"level": 5, "phi": 0.6, "energy": 1000.0}
        eo.evolve(state)
        status = eo.get_status()
        assert "generation" in status
        assert "best_fitness" in status


class TestGlobalEngine:
    def test_get_evolutionary_optimizer(self):
        g = get_evolutionary_optimizer()
        assert g is not None
        assert isinstance(g, EvolutionaryOptimizer)
