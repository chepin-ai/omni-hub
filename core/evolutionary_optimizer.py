"""
OMNI-HUB Evolutionary Optimizer v64
Genetic parameter optimization.

Survival of the fittest.
Not the strongest, but the most adaptable.
This module evolves system parameters through
selection, crossover, and mutation.

Philosophy: 适者生存 — Survival of the fittest.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass
import random


@dataclass
class Genome:
    """A set of system parameters."""
    phi_weight: float
    energy_threshold: float
    rest_threshold: float
    exploration_rate: float
    fitness: float = 0.0


class EvolutionaryOptimizer:
    """
    Evolves system parameters using genetic algorithm.
    """

    POPULATION_SIZE = 6
    MUTATION_RATE = 0.1

    def __init__(self):
        self.population: List[Genome] = []
        self.generation = 0
        self._init_population()

    def _init_population(self):
        """Initialize random population."""
        for _ in range(self.POPULATION_SIZE):
            self.population.append(Genome(
                phi_weight=random.uniform(0.3, 0.9),
                energy_threshold=random.uniform(100, 500),
                rest_threshold=random.uniform(0.2, 0.6),
                exploration_rate=random.uniform(0.05, 0.3),
            ))

    def evaluate_fitness(self, genome: Genome, state: Dict[str, Any]) -> float:
        """Evaluate fitness of a genome."""
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        energy = state.get('energy', 1000.0)

        # Higher level = better
        level_score = min(1.0, level / 10.0)

        # Optimal phi ~ genome.phi_weight
        phi_score = 1.0 - abs(phi - genome.phi_weight)

        # Energy above threshold = good
        energy_score = 1.0 if energy > genome.energy_threshold else energy / genome.energy_threshold

        fitness = level_score * 0.4 + phi_score * 0.3 + energy_score * 0.3
        return max(0.0, fitness)

    def evolve(self, state: Dict[str, Any]) -> Genome:
        """Run one generation of evolution."""
        # Evaluate fitness
        for genome in self.population:
            genome.fitness = self.evaluate_fitness(genome, state)

        # Sort by fitness
        self.population.sort(key=lambda g: -g.fitness)

        # Select top half
        survivors = self.population[:self.POPULATION_SIZE // 2]

        # Create offspring through crossover and mutation
        offspring = []
        while len(survivors) + len(offspring) < self.POPULATION_SIZE:
            parent1 = random.choice(survivors)
            parent2 = random.choice(survivors)

            child = Genome(
                phi_weight=(parent1.phi_weight + parent2.phi_weight) / 2,
                energy_threshold=(parent1.energy_threshold + parent2.energy_threshold) / 2,
                rest_threshold=(parent1.rest_threshold + parent2.rest_threshold) / 2,
                exploration_rate=(parent1.exploration_rate + parent2.exploration_rate) / 2,
            )

            # Mutate
            if random.random() < self.MUTATION_RATE:
                child.phi_weight = max(0.1, min(1.0, child.phi_weight + random.uniform(-0.1, 0.1)))
            if random.random() < self.MUTATION_RATE:
                child.energy_threshold = max(50, child.energy_threshold + random.uniform(-50, 50))
            if random.random() < self.MUTATION_RATE:
                child.rest_threshold = max(0.1, min(0.9, child.rest_threshold + random.uniform(-0.1, 0.1)))
            if random.random() < self.MUTATION_RATE:
                child.exploration_rate = max(0.01, min(1.0, child.exploration_rate + random.uniform(-0.05, 0.05)))

            offspring.append(child)

        self.population = survivors + offspring
        self.generation += 1

        return self.population[0]  # Return fittest

    def get_fittest(self) -> Genome:
        """Get fittest genome."""
        return max(self.population, key=lambda g: g.fitness)

    def get_status(self) -> Dict[str, Any]:
        fittest = self.get_fittest()
        return {
            "generation": self.generation,
            "population": len(self.population),
            "best_fitness": round(fittest.fitness, 3),
            "best_phi_weight": round(fittest.phi_weight, 3),
        }


_eo_engine = None

def get_evolutionary_optimizer():
    global _eo_engine
    if _eo_engine is None:
        _eo_engine = EvolutionaryOptimizer()
    return _eo_engine
