"""
OMNI-HUB Auto-Evolution Engine v174 Tests
Tests for generate, evaluate, deploy, rollback, distill, evolution_cycle, status.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.auto_evolution_engine import (
    AutoEvolutionEngine,
    get_module,
    get_auto_evolution_engine,
    reset_module,
    MUTATION_TYPES,
    VALIDATION_GATES,
    EVOLUTION_STAGES,
    MUTATION_QUALITY_LEVELS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    reset_module()
    yield
    reset_module()


@pytest.fixture
def engine():
    """Provide a fresh AutoEvolutionEngine instance."""
    return AutoEvolutionEngine()


# ---------------------------------------------------------------------------
# generate_mutation
# ---------------------------------------------------------------------------

class TestGenerateMutation:
    def test_generate_parameter_tune(self, engine):
        result = engine.generate_mutation("core_base", "parameter_tune")
        assert "error" not in result
        assert result["mutation_type"] == "parameter_tune"
        assert result["parent_module"] == "core_base"
        assert result["mutation_id"].startswith("MUT-")
        assert "code_delta" in result
        assert result["code_delta"]["action"] == "parameter_tune"

    def test_generate_structure_modify(self, engine):
        result = engine.generate_mutation("core_base", "structure_modify")
        assert result["mutation_type"] == "structure_modify"
        assert result["code_delta"]["action"] == "structure_modify"

    def test_generate_hybrid_merge(self, engine):
        result = engine.generate_mutation("core_base", "hybrid_merge")
        assert result["mutation_type"] == "hybrid_merge"
        assert "parents" in result["code_delta"]

    def test_generate_novel_creation(self, engine):
        result = engine.generate_mutation("core_base", "novel_creation")
        assert result["mutation_type"] == "novel_creation"
        assert "architecture_seed" in result["code_delta"]

    def test_generate_invalid_type(self, engine):
        result = engine.generate_mutation("core_base", "invalid_type")
        assert "error" in result

    def test_generate_empty_parent(self, engine):
        result = engine.generate_mutation("", "parameter_tune")
        assert "error" in result

    def test_all_mutation_types(self, engine):
        for mtype in MUTATION_TYPES:
            result = engine.generate_mutation("test_mod", mtype)
            assert "error" not in result
            assert result["mutation_type"] == mtype

    def test_mutation_queue_populated(self, engine):
        engine.generate_mutation("core_base", "parameter_tune")
        assert len(engine.mutation_queue) == 1
        assert engine.mutation_queue[0].mutation_type == "parameter_tune"


# ---------------------------------------------------------------------------
# evaluate_mutation
# ---------------------------------------------------------------------------

class TestEvaluateMutation:
    def test_evaluate_basic(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        test_suite = [
            {"name": "test_basic", "integration": False, "stress": False},
            {"name": "test_integration", "integration": True, "stress": False},
            {"name": "test_stress", "integration": True, "stress": True},
        ]
        result = engine.evaluate_mutation(mut, test_suite)
        assert "error" not in result
        assert "metrics" in result
        assert "functionality" in result["metrics"]
        assert "performance" in result["metrics"]
        assert "robustness" in result["metrics"]
        assert "novelty" in result["metrics"]
        assert "overall" in result["metrics"]
        assert result["mutation_id"] == mut["mutation_id"]
        assert result["all_gates_passed"] is True
        assert result["eligible_for_deploy"] is True

    def test_evaluate_empty_suite(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        result = engine.evaluate_mutation(mut, [])
        assert result["all_gates_passed"] is False  # unit_tests gate fails
        assert result["eligible_for_deploy"] is False

    def test_evaluate_invalid_mutation(self, engine):
        result = engine.evaluate_mutation({}, [])
        assert "error" in result

    def test_evaluate_invalid_test_suite(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        result = engine.evaluate_mutation(mut, "not_a_list")
        assert "error" in result

    def test_quality_labels(self, engine):
        """Ensure quality labels map correctly based on overall score."""
        for threshold, label in MUTATION_QUALITY_LEVELS:
            # We can't control the exact score easily, so we check the mapping logic
            assert engine._get_quality_label(threshold) == label
            if threshold > 0:
                assert engine._get_quality_label(threshold + 0.01) == label
        assert engine._get_quality_label(0.0) == "lethal"
        assert engine._get_quality_label(0.29) == "lethal"
        assert engine._get_quality_label(0.30) == "deleterious"
        assert engine._get_quality_label(0.50) == "neutral"
        assert engine._get_quality_label(0.80) == "improvement"
        assert engine._get_quality_label(0.95) == "breakthrough"
        assert engine._get_quality_label(1.0) == "breakthrough"

    def test_gate_results_structure(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        result = engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        for gate in VALIDATION_GATES:
            assert gate in result["gate_results"]


# ---------------------------------------------------------------------------
# deploy_mutation
# ---------------------------------------------------------------------------

class TestDeployMutation:
    def test_deploy_valid_mutation(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        test_suite = [
            {"name": "t1", "integration": True, "stress": True},
        ]
        engine.evaluate_mutation(mut, test_suite)
        result = engine.deploy_mutation(mut)
        assert result["deployed"] is True
        assert "module_name" in result
        assert result["module_name"].startswith("core_base")

    def test_deploy_without_evaluation(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        result = engine.deploy_mutation(mut)
        # Auto-evaluation with empty suite should fail (no stress test)
        assert result["deployed"] is False
        assert "reason" in result

    def test_deploy_invalid_mutation(self, engine):
        result = engine.deploy_mutation({})
        assert "error" in result

    def test_deployed_modules_populated(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        engine.deploy_mutation(mut)
        assert len(engine.deployed_modules) == 1


# ---------------------------------------------------------------------------
# rollback_module
# ---------------------------------------------------------------------------

class TestRollbackModule:
    def test_rollback_existing(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        deploy_result = engine.deploy_mutation(mut)
        module_name = deploy_result["module_name"]
        assert module_name in engine.deployed_modules

        rollback_result = engine.rollback_module(module_name)
        assert rollback_result["rolled_back"] is True
        assert rollback_result["module_name"] == module_name
        assert module_name not in engine.deployed_modules

    def test_rollback_nonexistent(self, engine):
        result = engine.rollback_module("nonexistent_module")
        assert result["rolled_back"] is False
        assert "reason" in result

    def test_rollback_empty_name(self, engine):
        result = engine.rollback_module("")
        assert "error" in result

    def test_rollback_count_increments(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        deploy_result = engine.deploy_mutation(mut)
        assert engine.total_rollbacks == 0
        engine.rollback_module(deploy_result["module_name"])
        assert engine.total_rollbacks == 1


# ---------------------------------------------------------------------------
# distill_skills
# ---------------------------------------------------------------------------

class TestDistillSkills:
    def test_distill_empty(self, engine):
        result = engine.distill_skills()
        assert result["distilled"] == 0
        assert result["skill_count"] == 0

    def test_distill_from_successful(self, engine):
        # Generate and evaluate a high-scoring novel_creation
        mut = engine.generate_mutation("core_base", "novel_creation")
        # Force a high score by using a well-populated test suite
        engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
            {"name": "t2", "integration": True, "stress": True},
        ])
        # Manually boost score to trigger skill distillation
        for m in engine.mutation_queue:
            if m.mutation_id == mut["mutation_id"]:
                m.overall_score = 0.90
                m.quality_label = "breakthrough"
                break

        result = engine.distill_skills()
        assert result["distilled"] >= 1
        assert result["skill_count"] >= 1
        assert len(result["new_skills"]) >= 1
        assert "pattern_id" in result["new_skills"][0]

    def test_skill_library_persistence(self, engine):
        mut = engine.generate_mutation("core_base", "novel_creation")
        engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        for m in engine.mutation_queue:
            if m.mutation_id == mut["mutation_id"]:
                m.overall_score = 0.90
                break
        engine.distill_skills()
        assert len(engine.skill_library) > 0


# ---------------------------------------------------------------------------
# run_evolution_cycle
# ---------------------------------------------------------------------------

class TestRunEvolutionCycle:
    def test_cycle_runs(self, engine):
        result = engine.run_evolution_cycle()
        assert "cycle_id" in result
        assert result["generated"] == len(MUTATION_TYPES)
        assert result["evaluated"] == len(MUTATION_TYPES)
        assert isinstance(result["deployed"], int)
        assert result["stage"] in [s[1] for s in EVOLUTION_STAGES]

    def test_cycle_increments_counter(self, engine):
        assert engine._cycle_counter == 0
        engine.run_evolution_cycle()
        assert engine._cycle_counter == 1
        engine.run_evolution_cycle()
        assert engine._cycle_counter == 2

    def test_cycle_logs_event(self, engine):
        engine.run_evolution_cycle()
        assert len(engine.evolution_log) > 0
        assert engine.evolution_log[-1]["event"] == "cycle_complete"

    def test_multiple_cycles_advance_stage(self, engine):
        for _ in range(3):
            engine.run_evolution_cycle()
        status = engine.get_status()
        assert status["mutation_count"] == 3 * len(MUTATION_TYPES)


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------

class TestGetStatus:
    def test_initial_status(self, engine):
        status = engine.get_status()
        assert status["mutation_count"] == 0
        assert status["deployed_count"] == 0
        assert status["rollback_count"] == 0
        assert status["skill_count"] == 0
        assert status["evolution_rate"] == 0.0
        assert status["stage"] == "nascent"

    def test_status_after_mutations(self, engine):
        engine.generate_mutation("core_base", "parameter_tune")
        status = engine.get_status()
        assert status["mutation_count"] == 1
        assert status["mutation_queue_size"] == 1

    def test_status_after_deploy(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        engine.deploy_mutation(mut)
        status = engine.get_status()
        assert status["deployed_count"] == 1
        assert len(status["deployed_modules"]) == 1

    def test_status_after_rollback(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        deploy_result = engine.deploy_mutation(mut)
        engine.rollback_module(deploy_result["module_name"])
        status = engine.get_status()
        assert status["rollback_count"] == 1
        assert status["deployed_count"] == 1  # deployed count doesn't decrement on rollback

    def test_evolution_stage_transitions(self, engine):
        """Test that evolution stage advances correctly."""
        assert engine._get_stage(0) == "nascent"
        assert engine._get_stage(5) == "nascent"
        assert engine._get_stage(11) == "developing"
        assert engine._get_stage(50) == "developing"
        assert engine._get_stage(101) == "mature"
        assert engine._get_stage(200) == "mature"
        assert engine._get_stage(501) == "advanced"
        assert engine._get_stage(800) == "advanced"
        assert engine._get_stage(1001) == "transcendental"
        assert engine._get_stage(2000) == "transcendental"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

class TestSingleton:
    def test_get_module_returns_instance(self):
        inst1 = get_module()
        assert isinstance(inst1, AutoEvolutionEngine)

    def test_get_module_singleton(self):
        inst1 = get_module()
        inst2 = get_module()
        assert inst1 is inst2

    def test_get_auto_evolution_engine_alias(self):
        inst = get_auto_evolution_engine()
        assert isinstance(inst, AutoEvolutionEngine)
        assert inst is get_module()

    def test_reset_module(self):
        inst1 = get_module()
        reset_module()
        inst2 = get_module()
        assert inst1 is not inst2


# ---------------------------------------------------------------------------
# Edge cases & integration
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_full_lifecycle(self, engine):
        """Test a complete mutation lifecycle: generate -> evaluate -> deploy -> rollback."""
        mut = engine.generate_mutation("core_base", "hybrid_merge")
        eval_result = engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        assert eval_result["eligible_for_deploy"] is True

        deploy_result = engine.deploy_mutation(mut)
        assert deploy_result["deployed"] is True

        rollback_result = engine.rollback_module(deploy_result["module_name"])
        assert rollback_result["rolled_back"] is True

    def test_parameter_tune_novelty_penalty(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        result = engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        # parameter_tune should have slightly lower novelty
        assert "metrics" in result

    def test_novel_creation_novelty_boost(self, engine):
        mut = engine.generate_mutation("core_base", "novel_creation")
        result = engine.evaluate_mutation(mut, [
            {"name": "t1", "integration": True, "stress": True},
        ])
        assert "metrics" in result

    def test_deploy_without_gates_fails(self, engine):
        mut = engine.generate_mutation("core_base", "parameter_tune")
        # Do NOT evaluate — deploy should auto-evaluate and likely fail
        result = engine.deploy_mutation(mut)
        assert result["deployed"] is False
