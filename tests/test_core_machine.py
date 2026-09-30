"""
Tests for OMNI-HUB v179: CoreMachine (核心机统合)

Covers:
- register_subsystem
- unify_control_plane
- execute_unified_cycle
- resolve_cross_subsystem_conflict
- compute_system_coherence
- activate_all_architectures
- get_status
- get_core_machine singleton
"""

import pytest
from core.core_machine import (
    CoreMachine,
    get_core_machine,
    VALID_SUBSYSTEM_TYPES,
    COHERENCE_LEVELS,
    ARCHITECTURE_STATES,
    MODULE_COUNT,
)


# =========================================================================
# Fixture
# =========================================================================

@pytest.fixture
def fresh_machine():
    """Return a fresh CoreMachine instance for isolation."""
    return CoreMachine()


# =========================================================================
# register_subsystem
# =========================================================================

class TestRegisterSubsystem:
    def test_register_valid_subsystem(self, fresh_machine):
        result = fresh_machine.register_subsystem(
            name="tricore",
            subsystem_type="quantum",
            capabilities=["proof_generation", "certainty_anchor"],
            priority=90,
        )
        assert result["status"] == "registered"
        assert result["name"] == "tricore"
        assert result["type"] == "quantum"
        assert result["priority"] == 90
        assert result["total_subsystems"] == 1

    def test_register_multiple_subsystems(self, fresh_machine):
        fresh_machine.register_subsystem("alpha", "logic", ["deduction"], 70)
        fresh_machine.register_subsystem("beta", "swarm", ["consensus"], 60)
        assert len(fresh_machine.list_subsystems()) == 2

    def test_register_invalid_type(self, fresh_machine):
        result = fresh_machine.register_subsystem(
            "bad", "invalid_type", ["cap"], 50
        )
        assert result["status"] == "error"
        assert "Invalid type" in result["message"]

    def test_register_invalid_name(self, fresh_machine):
        result = fresh_machine.register_subsystem("", "logic", ["cap"], 50)
        assert result["status"] == "error"

    def test_register_invalid_priority_low(self, fresh_machine):
        result = fresh_machine.register_subsystem("x", "logic", ["cap"], -1)
        assert result["status"] == "error"

    def test_register_invalid_priority_high(self, fresh_machine):
        result = fresh_machine.register_subsystem("x", "logic", ["cap"], 101)
        assert result["status"] == "error"

    def test_register_non_list_capabilities(self, fresh_machine):
        result = fresh_machine.register_subsystem("x", "logic", "not_a_list", 50)
        assert result["status"] == "error"

    def test_all_valid_subsystem_types(self, fresh_machine):
        for st in VALID_SUBSYSTEM_TYPES:
            result = fresh_machine.register_subsystem(
                f"sub_{st}", st, ["cap"], 50
            )
            assert result["status"] == "registered", f"Failed for type {st}"


# =========================================================================
# unify_control_plane
# =========================================================================

class TestUnifyControlPlane:
    def test_unify_empty(self, fresh_machine):
        result = fresh_machine.unify_control_plane()
        assert result["status"] == "empty"

    def test_unify_with_subsystems(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["cap1", "cap2"], 80)
        fresh_machine.register_subsystem("b", "logic", ["cap2", "cap3"], 70)
        result = fresh_machine.unify_control_plane()
        assert result["status"] == "unified"
        assert result["subsystem_count"] == 2
        assert result["conflict_count"] == 1  # cap2 shared
        assert result["type_groups"]["quantum"] == 1
        assert result["type_groups"]["logic"] == 1

    def test_unify_no_conflicts(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["cap1"], 80)
        fresh_machine.register_subsystem("b", "logic", ["cap2"], 70)
        result = fresh_machine.unify_control_plane()
        assert result["status"] == "unified"
        assert result["conflict_count"] == 0


# =========================================================================
# execute_unified_cycle
# =========================================================================

class TestExecuteUnifiedCycle:
    def test_cycle_empty(self, fresh_machine):
        result = fresh_machine.execute_unified_cycle()
        assert result["status"] == "error"

    def test_cycle_success(self, fresh_machine):
        fresh_machine.register_subsystem("tri", "quantum", ["proof"], 90)
        fresh_machine.register_subsystem("pen", "logic", ["sense", "decide"], 80)
        fresh_machine.register_subsystem("qf", "meta", ["navigate"], 75)
        result = fresh_machine.execute_unified_cycle()
        assert result["status"] == "completed"
        assert result["cycle_number"] == 1
        assert result["phases_executed"] == 8
        assert "quantum_proof_strength" in result
        assert "penta_stage" in result
        assert "qfos_nav_ready" in result
        assert "field_sync_coverage" in result
        assert "circles_resolved" in result
        assert "circulation_flow_rate" in result
        assert "modules_active" in result
        assert "coherence_after" in result
        assert result["quantum_proof_strength"] > 0

    def test_cycle_increments_counter(self, fresh_machine):
        fresh_machine.register_subsystem("s", "quantum", ["c"], 50)
        fresh_machine.execute_unified_cycle()
        fresh_machine.execute_unified_cycle()
        status = fresh_machine.get_status()
        assert status["cycle_count"] == 2

    def test_cycle_all_phases_present(self, fresh_machine):
        fresh_machine.register_subsystem("s1", "quantum", ["a"], 50)
        fresh_machine.register_subsystem("s2", "logic", ["b"], 50)
        result = fresh_machine.execute_unified_cycle()
        assert result["penta_stage"] == "evolve"
        assert result["qfos_nav_ready"] in (True, False)
        assert 0 <= result["field_sync_coverage"] <= 1
        assert result["circles_resolved"] >= 0
        assert result["modules_active"] >= 1


# =========================================================================
# resolve_cross_subsystem_conflict
# =========================================================================

class TestResolveConflict:
    def test_resolve_valid(self, fresh_machine):
        fresh_machine.register_subsystem("high", "quantum", ["shared", "exclusive_h"], 90)
        fresh_machine.register_subsystem("low", "logic", ["shared", "exclusive_l"], 40)
        result = fresh_machine.resolve_cross_subsystem_conflict("high", "low")
        assert result["status"] == "resolved"
        assert result["primary"] == "high"
        assert result["secondary"] == "low"
        assert "shared" in result["shared_capabilities"]
        assert result["resolution_strategy"] == "priority_then_health"

    def test_resolve_tie_breaker(self, fresh_machine):
        fresh_machine.register_subsystem("aaa", "quantum", ["cap"], 50)
        fresh_machine.register_subsystem("bbb", "logic", ["cap"], 50)
        result = fresh_machine.resolve_cross_subsystem_conflict("aaa", "bbb")
        assert result["status"] == "resolved"
        # Deterministic alphabetical tie-break
        assert result["primary"] == "aaa"
        assert result["secondary"] == "bbb"

    def test_resolve_unknown(self, fresh_machine):
        result = fresh_machine.resolve_cross_subsystem_conflict("ghost_a", "ghost_b")
        assert result["status"] == "error"
        assert "Unknown" in result["message"]

    def test_resolve_increases_counter(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["x"], 90)
        fresh_machine.register_subsystem("b", "logic", ["x"], 40)
        fresh_machine.resolve_cross_subsystem_conflict("a", "b")
        status = fresh_machine.get_status()
        assert status["conflicts_resolved"] >= 1


# =========================================================================
# compute_system_coherence
# =========================================================================

class TestComputeCoherence:
    def test_coherence_empty(self, fresh_machine):
        result = fresh_machine.compute_system_coherence()
        assert result["coherence"] == 0.0
        assert result["level"] == "chaotic"

    def test_coherence_with_subsystems(self, fresh_machine):
        fresh_machine.register_subsystem("s1", "quantum", ["a", "b"], 80)
        fresh_machine.register_subsystem("s2", "logic", ["c"], 70)
        result = fresh_machine.compute_system_coherence()
        assert 0.0 < result["coherence"] <= 1.0
        assert result["level"] in [name for _, name in COHERENCE_LEVELS]
        assert "components" in result
        comp = result["components"]
        assert "avg_health" in comp
        assert "consensus_rate" in comp
        assert "integration_density" in comp
        assert "evolution_rate" in comp
        assert "field_strength" in comp

    def test_coherence_components_bounded(self, fresh_machine):
        fresh_machine.register_subsystem("s1", "quantum", ["a"], 50)
        result = fresh_machine.compute_system_coherence()
        comp = result["components"]
        assert 0.0 <= comp["avg_health"] <= 1.0
        assert 0.0 <= comp["consensus_rate"] <= 1.0
        assert 0.0 <= comp["integration_density"] <= 1.0
        assert 0.0 <= comp["evolution_rate"] <= 1.0
        assert 0.0 <= comp["field_strength"] <= 1.0

    def test_coherence_levels_thresholds(self, fresh_machine):
        # High coherence scenario: many healthy, active, high-priority subsystems
        for i in range(10):
            fresh_machine.register_subsystem(
                f"sub_{i}", "quantum", [f"cap_{i}", "common"], 95
            )
        fresh_machine.activate_all_architectures()
        result = fresh_machine.compute_system_coherence()
        assert result["level"] in ("singularity", "unified", "coherent")


# =========================================================================
# activate_all_architectures
# =========================================================================

class TestActivateAllArchitectures:
    def test_activate_empty(self, fresh_machine):
        result = fresh_machine.activate_all_architectures()
        assert result["status"] == "empty"
        assert result["state"] == "dormant"

    def test_activate_all(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["c1", "c2"], 80)
        fresh_machine.register_subsystem("b", "logic", ["c3"], 70)
        result = fresh_machine.activate_all_architectures()
        assert result["status"] == "activated"
        assert result["activation_rate"] == 1.0
        assert result["state"] == "fully_active"
        assert result["subsystems_activated"] == 2
        assert result["total_architectures"] == 3  # 2 + 1 capabilities

    def test_activate_sets_initialized(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["c1"], 50)
        fresh_machine.activate_all_architectures()
        assert fresh_machine.get_status()["initialized"] is True

    def test_activate_partial(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["c1", "c2", "c3", "c4"], 50)
        fresh_machine.register_subsystem("b", "logic", ["c5"], 50)
        # Manually set one inactive to test partial
        fresh_machine._subsystems["a"].active = False
        result = fresh_machine.activate_all_architectures()
        # After activate_all, all become active
        assert result["activation_rate"] == 1.0
        assert result["state"] == "fully_active"

    def test_architecture_states(self, fresh_machine):
        # Test state thresholds
        fresh_machine.register_subsystem("a", "quantum", ["c1"], 50)
        result = fresh_machine.activate_all_architectures()
        assert result["state"] == "fully_active"


# =========================================================================
# get_status
# =========================================================================

class TestGetStatus:
    def test_status_empty(self, fresh_machine):
        status = fresh_machine.get_status()
        assert status["subsystem_count"] == 0
        assert status["coherence"] == 0.0
        assert status["cycle_count"] == 0
        assert status["active_architectures"] == 0
        assert status["initialized"] is False
        assert "instance_id" in status

    def test_status_after_registration(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["c"], 80)
        status = fresh_machine.get_status()
        assert status["subsystem_count"] == 1
        assert status["coherence"] > 0

    def test_status_after_cycle(self, fresh_machine):
        fresh_machine.register_subsystem("a", "quantum", ["c"], 80)
        fresh_machine.execute_unified_cycle()
        status = fresh_machine.get_status()
        assert status["cycle_count"] == 1
        assert status["total_cycles"] == 1
        assert status["coherence"] > 0


# =========================================================================
# Singleton
# =========================================================================

class TestSingleton:
    def test_singleton_same_instance(self):
        cm1 = get_core_machine()
        cm2 = get_core_machine()
        assert cm1 is cm2

    def test_singleton_has_instance_id(self):
        cm = get_core_machine()
        assert len(cm.get_status()["instance_id"]) == 8


# =========================================================================
# Integration / End-to-end
# =========================================================================

class TestIntegration:
    def test_full_workflow(self, fresh_machine):
        # 1. Register diverse subsystems
        fresh_machine.register_subsystem("tricore", "quantum", ["proof", "anchor"], 95)
        fresh_machine.register_subsystem("penta", "logic", ["sense", "decide", "act"], 90)
        fresh_machine.register_subsystem("qfos", "meta", ["navigate", "will"], 85)
        fresh_machine.register_subsystem("field", "field", ["sync", "breathe"], 80)
        fresh_machine.register_subsystem("circles", "circle", ["resolve", "form"], 75)
        fresh_machine.register_subsystem("circulation", "circulation", ["flow", "drive"], 70)
        fresh_machine.register_subsystem("swarm", "swarm", ["consensus", "emerge"], 65)

        # 2. Unify
        unify = fresh_machine.unify_control_plane()
        assert unify["status"] == "unified"
        assert unify["subsystem_count"] == 7

        # 3. Activate all
        activation = fresh_machine.activate_all_architectures()
        assert activation["status"] == "activated"
        assert activation["state"] == "fully_active"

        # 4. Execute multiple cycles
        for _ in range(3):
            cycle = fresh_machine.execute_unified_cycle()
            assert cycle["status"] == "completed"

        # 5. Resolve a conflict
        conflict = fresh_machine.resolve_cross_subsystem_conflict("tricore", "penta")
        assert conflict["status"] == "resolved"
        assert conflict["primary"] == "tricore"  # higher priority

        # 6. Check coherence
        coherence = fresh_machine.compute_system_coherence()
        assert 0 < coherence["coherence"] <= 1.0

        # 7. Final status
        status = fresh_machine.get_status()
        assert status["subsystem_count"] == 7
        assert status["cycle_count"] == 3
        assert status["coherence"] > 0
        assert status["initialized"] is True

    def test_coherence_formula_properties(self, fresh_machine):
        """
        The coherence formula is:
        (avg_health * consensus_rate * integration_density *
         evolution_rate * field_strength) ^ 0.2

        Verify it stays in [0, 1] and responds to subsystem changes.
        """
        fresh_machine.register_subsystem("s1", "quantum", ["a"], 50)
        c1 = fresh_machine.compute_system_coherence()["coherence"]

        fresh_machine.register_subsystem("s2", "logic", ["b"], 50)
        c2 = fresh_machine.compute_system_coherence()["coherence"]

        # More subsystems should generally not decrease coherence
        assert 0 <= c1 <= 1
        assert 0 <= c2 <= 1

        # All-active should give better consensus than mixed
        fresh_machine.activate_all_architectures()
        c3 = fresh_machine.compute_system_coherence()["coherence"]
        assert c3 >= c2  # activating all improves consensus_rate

    def test_cycle_phases_have_expected_keys(self, fresh_machine):
        fresh_machine.register_subsystem("s", "quantum", ["c"], 50)
        result = fresh_machine.execute_unified_cycle()
        expected_keys = [
            "status", "cycle_number", "duration", "phases_executed",
            "quantum_proof_strength", "penta_stage", "qfos_nav_ready",
            "field_sync_coverage", "circles_resolved",
            "circulation_flow_rate", "modules_active", "coherence_after",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
