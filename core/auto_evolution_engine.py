"""
OMNI-HUB v195 — AutoEvolutionEngine
自动进化引擎

核心功能：
1. FitnessEvaluator    — 适应度评估器
2. MutationOperator    — 变异算子
3. SelectionStrategy   — 选择策略
4. CrossoverEngine     — 交叉引擎
5. PopulationManager   — 种群管理器
6. AutoEvolutionEngine — 统合引擎

映射：
- 进化 = vikāsa（开展）
- 适应 = anukūla（随顺）
- 选择 = vāraṇa（拣择）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class SelectionMethod(Enum):
    """选择方法"""
    ELITIST = "elitist"
    ROULETTE = "roulette"
    TOURNAMENT = "tournament"
    RANK = "rank"


class MutationStrategy(Enum):
    """变异策略"""
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    ADAPTIVE = "adaptive"


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class Individual:
    """个体"""
    individual_id: str
    genome: Dict[str, float]
    fitness: float = 0.0
    generation: int = 0
    age: int = 0


@dataclass
class GenerationStats:
    """世代统计"""
    generation: int
    best_fitness: float
    avg_fitness: float
    diversity: float
    population_size: int


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 适应度评估器
# ═══════════════════════════════════════════════════════════════

class FitnessEvaluator:
    """适应度评估器 — anukūla"""

    def __init__(self):
        self.evaluations: deque = deque(maxlen=500)
        self.fitness_history: deque = deque(maxlen=200)

    def evaluate(self, individual: Individual,
                 objectives: Dict[str, float]) -> float:
        """评估个体适应度"""
        # 多目标加权适应度
        weights = {
            "health": 0.3,
            "coherence": 0.3,
            "efficiency": 0.2,
            "novelty": 0.2,
        }

        fitness = 0.0
        for key, weight in weights.items():
            if key in objectives:
                fitness += objectives[key] * weight

        # 基因组多样性奖励
        genome_values = list(individual.genome.values())
        if genome_values:
            diversity_bonus = sum(abs(v1 - v2)
                                  for i, v1 in enumerate(genome_values)
                                  for v2 in genome_values[i+1:]) / max(1, len(genome_values) ** 2)
            fitness += diversity_bonus * 0.1

        individual.fitness = min(1.0, max(0.0, fitness))

        self.evaluations.append({
            "individual": individual.individual_id,
            "fitness": individual.fitness,
            "timestamp": time.time()
        })
        self.fitness_history.append(individual.fitness)
        return individual.fitness

    def get_fitness_trend(self) -> float:
        """获取适应度趋势"""
        if len(self.fitness_history) < 10:
            return 0.0
        recent = list(self.fitness_history)[-20:]
        if len(recent) < 2:
            return 0.0
        return (recent[-1] - recent[0]) / len(recent)

    def get_report(self) -> Dict:
        return {
            "evaluations": len(self.evaluations),
            "avg_fitness": sum(self.fitness_history) / max(1, len(self.fitness_history)),
            "trend": self.get_fitness_trend(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 变异算子
# ═══════════════════════════════════════════════════════════════

class MutationOperator:
    """变异算子"""

    def __init__(self, strategy: MutationStrategy = MutationStrategy.GAUSSIAN):
        self.strategy = strategy
        self.mutation_log: deque = deque(maxlen=300)
        self.mutation_rate = 0.1

    def mutate(self, individual: Individual,
               generation: int = 0) -> Individual:
        """变异个体"""
        new_genome = dict(individual.genome)

        # 适应性变异率
        adaptive_rate = self.mutation_rate * (1.0 - generation / 1000)
        adaptive_rate = max(0.01, adaptive_rate)

        for key in new_genome:
            if hash(key + str(generation)) % 100 < adaptive_rate * 100:
                if self.strategy == MutationStrategy.GAUSSIAN:
                    noise = math.sin(hash(key + str(time.time())) % 1000) * 0.1
                elif self.strategy == MutationStrategy.UNIFORM:
                    noise = (hash(key + str(generation)) % 100 - 50) / 500.0
                else:  # ADAPTIVE
                    noise = (individual.fitness - 0.5) * 0.05

                new_genome[key] = max(0.0, min(1.0, new_genome[key] + noise))

        new_ind = Individual(
            individual_id=f"mut_{individual.individual_id}_{generation}",
            genome=new_genome,
            generation=generation,
            age=0
        )

        self.mutation_log.append({
            "parent": individual.individual_id,
            "child": new_ind.individual_id,
            "rate": adaptive_rate,
        })
        return new_ind

    def get_report(self) -> Dict:
        return {
            "mutations": len(self.mutation_log),
            "current_rate": self.mutation_rate,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 选择策略
# ═══════════════════════════════════════════════════════════════

class SelectionStrategy:
    """选择策略 — vāraṇa"""

    def __init__(self, method: SelectionMethod = SelectionMethod.TOURNAMENT):
        self.method = method
        self.selections: deque = deque(maxlen=300)

    def select(self, population: List[Individual],
               count: int) -> List[Individual]:
        """选择个体"""
        if not population:
            return []

        if self.method == SelectionMethod.ELITIST:
            selected = sorted(population, key=lambda i: -i.fitness)[:count]

        elif self.method == SelectionMethod.ROULETTE:
            total_fitness = sum(i.fitness for i in population)
            selected = []
            for _ in range(count):
                if total_fitness == 0:
                    selected.append(population[hash(str(_)) % len(population)])
                else:
                    pick = (hash(str(_) + str(time.time())) % 1000) / 1000.0 * total_fitness
                    cumulative = 0
                    for ind in population:
                        cumulative += ind.fitness
                        if cumulative >= pick:
                            selected.append(ind)
                            break
                    else:
                        selected.append(population[-1])

        elif self.method == SelectionMethod.TOURNAMENT:
            selected = []
            for _ in range(count):
                tournament = [population[hash(str(_) + str(i)) % len(population)]
                             for i in range(min(3, len(population)))]
                winner = max(tournament, key=lambda i: i.fitness)
                selected.append(winner)

        else:  # RANK
            ranked = sorted(population, key=lambda i: -i.fitness)
            selected = ranked[:count]

        for s in selected:
            self.selections.append({
                "individual": s.individual_id,
                "fitness": s.fitness,
                "method": self.method.value,
            })
        return selected

    def get_report(self) -> Dict:
        return {
            "selections": len(self.selections),
            "method": self.method.value,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 交叉引擎
# ═══════════════════════════════════════════════════════════════

class CrossoverEngine:
    """交叉引擎"""

    def __init__(self, crossover_rate: float = 0.7):
        self.crossover_rate = crossover_rate
        self.crossovers: deque = deque(maxlen=300)

    def crossover(self, parent_a: Individual,
                  parent_b: Individual,
                  generation: int = 0) -> Tuple[Individual, Individual]:
        """执行交叉"""
        if hash(str(parent_a.individual_id) + str(parent_b.individual_id)) % 100 > self.crossover_rate * 100:
            # 不交叉，直接克隆
            return parent_a, parent_b

        keys = list(parent_a.genome.keys())
        if not keys:
            return parent_a, parent_b

        # 单点交叉
        crossover_point = hash(str(generation)) % max(1, len(keys))

        child_a_genome = {}
        child_b_genome = {}
        for i, key in enumerate(keys):
            if i < crossover_point:
                child_a_genome[key] = parent_a.genome[key]
                child_b_genome[key] = parent_b.genome[key]
            else:
                child_a_genome[key] = parent_b.genome[key]
                child_b_genome[key] = parent_a.genome[key]

        child_a = Individual(
            individual_id=f"cross_a_{generation}_{parent_a.individual_id}",
            genome=child_a_genome,
            generation=generation
        )
        child_b = Individual(
            individual_id=f"cross_b_{generation}_{parent_b.individual_id}",
            genome=child_b_genome,
            generation=generation
        )

        self.crossovers.append({
            "parent_a": parent_a.individual_id,
            "parent_b": parent_b.individual_id,
            "generation": generation,
        })
        return child_a, child_b

    def get_report(self) -> Dict:
        return {
            "crossovers": len(self.crossovers),
            "rate": self.crossover_rate,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 种群管理器
# ═══════════════════════════════════════════════════════════════

class PopulationManager:
    """种群管理器"""

    def __init__(self, max_size: int = 100):
        self.population: List[Individual] = []
        self.max_size = max_size
        self.generation_stats: deque = deque(maxlen=200)

    def add(self, individual: Individual):
        """添加个体"""
        self.population.append(individual)
        if len(self.population) > self.max_size:
            # 移除最老的低适应度个体
            self.population = sorted(
                self.population,
                key=lambda i: (i.fitness, -i.age)
            )[-self.max_size:]

    def get_diversity(self) -> float:
        """计算种群多样性"""
        if len(self.population) < 2:
            return 0.0

        genomes = [list(ind.genome.values()) for ind in self.population if ind.genome]
        if not genomes:
            return 0.0

        # 平均成对差异
        diffs = []
        for i in range(len(genomes)):
            for j in range(i + 1, len(genomes)):
                if len(genomes[i]) == len(genomes[j]):
                    d = sum(abs(a - b) for a, b in zip(genomes[i], genomes[j]))
                    diffs.append(d / len(genomes[i]))

        return sum(diffs) / len(diffs) if diffs else 0.0

    def record_generation(self, generation: int):
        """记录世代统计"""
        if not self.population:
            return
        fitnesses = [ind.fitness for ind in self.population]
        self.generation_stats.append(GenerationStats(
            generation=generation,
            best_fitness=max(fitnesses),
            avg_fitness=sum(fitnesses) / len(fitnesses),
            diversity=self.get_diversity(),
            population_size=len(self.population)
        ))

    def get_report(self) -> Dict:
        return {
            "population_size": len(self.population),
            "max_size": self.max_size,
            "diversity": self.get_diversity(),
            "generations": len(self.generation_stats),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — AutoEvolutionEngine v195
# ═══════════════════════════════════════════════════════════════

class AutoEvolutionEngine:
    """
    OMNI-HUB v195 自动进化引擎

    vikāsa · anukūla · vāraṇa — 开展、随顺、拣择
    """

    VERSION = "195.0.0"

    def __init__(self):
        self.evaluator = FitnessEvaluator()
        self.mutator = MutationOperator()
        self.selector = SelectionStrategy()
        self.crossover = CrossoverEngine()
        self.population = PopulationManager()

        self.generation = 0
        self.event_log: deque = deque(maxlen=10000)

    def initialize_population(self, module_states: Dict[str, Dict]):
        """从模块状态初始化种群"""
        for module, state in module_states.items():
            genome = {
                "health": state.get("health", 0.5),
                "coherence": state.get("coherence", 0.5),
                "efficiency": state.get("efficiency", 0.5),
                "adaptability": state.get("adaptability", 0.5),
            }
            individual = Individual(
                individual_id=f"ind_{module}_{self.generation}",
                genome=genome,
                generation=self.generation
            )
            self.population.add(individual)

    def evolve_generation(self, objectives: Dict[str, float]) -> Dict:
        """进化一代"""
        self.generation += 1

        # 1. 评估
        for ind in self.population.population:
            self.evaluator.evaluate(ind, objectives)

        # 2. 选择
        selected = self.selector.select(self.population.population,
                                        max(2, len(self.population.population) // 2))

        # 3. 交叉
        offspring = []
        for i in range(0, len(selected) - 1, 2):
            child_a, child_b = self.crossover.crossover(
                selected[i], selected[i+1], self.generation
            )
            offspring.extend([child_a, child_b])

        # 4. 变异
        mutated = []
        for child in offspring:
            mutated.append(self.mutator.mutate(child, self.generation))

        # 5. 重新评估后代
        for ind in mutated:
            self.evaluator.evaluate(ind, objectives)
            self.population.add(ind)

        # 6. 老化
        for ind in self.population.population:
            ind.age += 1

        self.population.record_generation(self.generation)

        stats = self.population.generation_stats[-1] if self.population.generation_stats else None
        return {
            "generation": self.generation,
            "best_fitness": stats.best_fitness if stats else 0.0,
            "avg_fitness": stats.avg_fitness if stats else 0.0,
            "diversity": stats.diversity if stats else 0.0,
            "population_size": len(self.population.population),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行进化周期"""
        module_states = module_states or {}

        if not self.population.population:
            self.initialize_population(module_states)

        objectives = {
            "health": sum(s.get("health", 0.5) for s in module_states.values()) / max(1, len(module_states)),
            "coherence": sum(s.get("coherence", 0.5) for s in module_states.values()) / max(1, len(module_states)),
            "efficiency": 0.7,
            "novelty": 0.5,
        }

        result = self.evolve_generation(objectives)
        self.event_log.append(result)
        return result

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "generation": self.generation,
            "evaluator": self.evaluator.get_report(),
            "mutator": self.mutator.get_report(),
            "selector": self.selector.get_report(),
            "crossover": self.crossover.get_report(),
            "population": self.population.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_aee_instance: Optional[AutoEvolutionEngine] = None


def get_auto_evolution_engine() -> AutoEvolutionEngine:
    global _aee_instance
    if _aee_instance is None:
        _aee_instance = AutoEvolutionEngine()
    return _aee_instance


if __name__ == "__main__":
    aee = AutoEvolutionEngine()
    print(f"AutoEvolutionEngine v{aee.VERSION} initialized")
    print(f"Status: {json.dumps(aee.get_status(), indent=2, default=str)}")
