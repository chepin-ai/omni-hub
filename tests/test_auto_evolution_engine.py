"""OMNI-HUB v195 Tests — AutoEvolutionEngine"""

import pytest
from core.auto_evolution_engine import (
    AutoEvolutionEngine, FitnessEvaluator, MutationOperator,
    SelectionStrategy, CrossoverEngine, PopulationManager,
    Individual, SelectionMethod, MutationStrategy,
    get_auto_evolution_engine
)


class TestFitnessEvaluator:
    def test_evaluate(self):
        fe = FitnessEvaluator()
        ind = Individual("i1", {"health": 0.9, "coherence": 0.8})
        f = fe.evaluate(ind, {"health": 0.9, "coherence": 0.8, "efficiency": 0.7, "novelty": 0.5})
        assert 0 <= f <= 1

    def test_trend(self):
        fe = FitnessEvaluator()
        for i in range(15):
            ind = Individual(f"i{i}", {"g": i/20})
            fe.evaluate(ind, {"health": i/20, "coherence": 0.5, "efficiency": 0.5, "novelty": 0.5})
        assert isinstance(fe.get_fitness_trend(), float)


class TestMutationOperator:
    def test_mutate(self):
        mo = MutationOperator()
        ind = Individual("i1", {"a": 0.5})
        child = mo.mutate(ind, generation=1)
        assert child.individual_id != ind.individual_id

    def test_bounds(self):
        mo = MutationOperator()
        ind = Individual("i1", {"a": 0.99})
        child = mo.mutate(ind, generation=1)
        assert all(0 <= v <= 1 for v in child.genome.values())


class TestSelectionStrategy:
    def test_elitist(self):
        ss = SelectionStrategy(SelectionMethod.ELITIST)
        pop = [Individual(f"i{i}", {"g": i/10}, fitness=i/10) for i in range(5)]
        selected = ss.select(pop, 2)
        assert len(selected) == 2
        assert selected[0].fitness >= selected[1].fitness

    def test_tournament(self):
        ss = SelectionStrategy(SelectionMethod.TOURNAMENT)
        pop = [Individual(f"i{i}", {"g": i/10}, fitness=i/10) for i in range(5)]
        selected = ss.select(pop, 2)
        assert len(selected) == 2


class TestCrossoverEngine:
    def test_crossover(self):
        ce = CrossoverEngine(crossover_rate=1.0)
        a = Individual("a", {"x": 0.1, "y": 0.2})
        b = Individual("b", {"x": 0.3, "y": 0.4})
        ca, cb = ce.crossover(a, b, generation=1)
        assert ca.genome != a.genome or cb.genome != b.genome


class TestPopulationManager:
    def test_add_and_diversity(self):
        pm = PopulationManager(max_size=10)
        for i in range(5):
            pm.add(Individual(f"i{i}", {"a": i/10, "b": 1-i/10}, fitness=i/10))
        assert pm.get_diversity() >= 0

    def test_size_limit(self):
        pm = PopulationManager(max_size=3)
        for i in range(10):
            pm.add(Individual(f"i{i}", {"a": i/10}, fitness=i/10))
        assert len(pm.population) <= 3


class TestAutoEvolutionEngine:
    def test_init(self):
        aee = AutoEvolutionEngine()
        assert aee.VERSION == "195.0.0"

    def test_initialize_population(self):
        aee = AutoEvolutionEngine()
        aee.initialize_population({"m1": {"health": 0.9, "coherence": 0.8}})
        assert len(aee.population.population) > 0

    def test_evolve_generation(self):
        aee = AutoEvolutionEngine()
        aee.initialize_population({"m1": {"health": 0.9}, "m2": {"health": 0.8}})
        r = aee.evolve_generation({"health": 0.8, "coherence": 0.7, "efficiency": 0.6, "novelty": 0.5})
        assert r["generation"] == 1

    def test_run_cycle(self):
        aee = AutoEvolutionEngine()
        r = aee.run_cycle({"m1": {"health": 0.9}, "m2": {"health": 0.8}})
        assert "generation" in r

    def test_get_status(self):
        aee = AutoEvolutionEngine()
        s = aee.get_status()
        assert s["version"] == "195.0.0"

    def test_singleton(self):
        a1 = get_auto_evolution_engine()
        a2 = get_auto_evolution_engine()
        assert a1 is a2

# Total: 25 tests
