"""
Tests for the Unified Kernel Protocol (OMNI-HUB Module v165).
"""

import pytest
import sys
import os

# Ensure core/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.unified_kernel_protocol import (
    UnifiedKernelProtocol,
    get_unified_kernel_protocol,
    _module,
    VALID_SUBSYSTEM_TYPES,
)


class TestRegisterSubsystem:
    def test_register_valid_subsystem(self):
        ukp = UnifiedKernelProtocol()
        result = ukp.register_subsystem(
            name="mip_alpha",
            subsystem_type="tri_core_mip",
            capabilities=["quantum_verify", "proof_gen"],
        )
        assert result["success"] is True
        assert result["subsystem"]["name"] == "mip_alpha"
        assert result["subsystem"]["type"] == "tri_core_mip"

    def test_register_invalid_type(self):
        ukp = UnifiedKernelProtocol()
        result = ukp.register_subsystem(
            name="bad",
            subsystem_type="unknown_type",
            capabilities=[],
        )
        assert result["success"] is False
        assert "valid_types" in result

    def test_register_duplicate_name(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("dup", "tri_core_mip", ["x"])
        result = ukp.register_subsystem("dup", "tri_core_mip", ["y"])
        assert result["success"] is False
        assert "already registered" in result["error"]

    def test_register_invalid_name(self):
        ukp = UnifiedKernelProtocol()
        result = ukp.register_subsystem("", "tri_core_mip", ["x"])
        assert result["success"] is False


class TestCoordinateSubsystems:
    def test_coordinate_empty(self):
        ukp = UnifiedKernelProtocol()
        result = ukp.coordinate_subsystems()
        assert result["success"] is False
        assert "No subsystems" in result["error"]

    def test_coordinate_success(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("mip", "tri_core_mip", ["verify"])
        ukp.register_subsystem("penta", "penta_core_loop", ["decide"])
        ukp.register_subsystem("qfos", "qfos_fusion", ["navigate"])
        ukp.register_subsystem("embed", "kernel_embedder", ["learn"])
        result = ukp.coordinate_subsystems()
        assert result["success"] is True
        cs = result["coordination_state"]
        assert cs["proof_links"] >= 1
        assert cs["nav_links"] >= 1
        assert cs["inject_links"] >= 1


class TestComputeFusionLevel:
    def test_fusion_empty(self):
        ukp = UnifiedKernelProtocol()
        result = ukp.compute_fusion_level()
        assert result["fusion_level"] == 0.0
        assert result["tier"] == "fragmented"

    def test_fusion_with_subsystems(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("mip", "tri_core_mip", ["verify"])
        ukp.register_subsystem("penta", "penta_core_loop", ["decide"])
        ukp.coordinate_subsystems()
        result = ukp.compute_fusion_level()
        assert 0.0 <= result["fusion_level"] <= 1.0
        assert "tier" in result
        assert "avg_health" in result

    def test_fusion_tiers(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("mip", "tri_core_mip", ["verify"])
        ukp.register_subsystem("penta", "penta_core_loop", ["decide"])
        ukp.register_subsystem("qfos", "qfos_fusion", ["navigate"])
        ukp.register_subsystem("embed", "kernel_embedder", ["learn"])
        ukp.coordinate_subsystems()
        result = ukp.compute_fusion_level()
        tier = result["tier"]
        assert tier in ["singularity", "unified", "coordinated", "connected", "fragmented"]


class TestExecuteUnifiedCycle:
    def test_unified_cycle_success(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("mip", "tri_core_mip", ["verify"])
        ukp.register_subsystem("penta", "penta_core_loop", ["decide"])
        ukp.register_subsystem("qfos", "qfos_fusion", ["navigate"])
        ukp.register_subsystem("embed", "kernel_embedder", ["learn"])
        result = ukp.execute_unified_cycle({"sensor_data": 42})
        assert result["success"] is True
        cycle = result["cycle"]
        assert "tri_core" in cycle["phases"]
        assert "penta_core" in cycle["phases"]
        assert "qfos" in cycle["phases"]
        assert "embedder" in cycle["phases"]
        assert cycle["cycle_id"] == 1

    def test_unified_cycle_phases_have_ids(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("mip", "tri_core_mip", ["verify"])
        ukp.register_subsystem("penta", "penta_core_loop", ["decide"])
        ukp.register_subsystem("qfos", "qfos_fusion", ["navigate"])
        ukp.register_subsystem("embed", "kernel_embedder", ["learn"])
        result = ukp.execute_unified_cycle({"sensor_data": 99})
        phases = result["cycle"]["phases"]
        assert "proof_id" in phases["tri_core"]
        assert "decision_id" in phases["penta_core"]
        assert "guidance_id" in phases["qfos"]
        assert "learning_id" in phases["embedder"]

    def test_multiple_cycles_increment(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("mip", "tri_core_mip", ["verify"])
        ukp.register_subsystem("penta", "penta_core_loop", ["decide"])
        for i in range(3):
            result = ukp.execute_unified_cycle({"iteration": i})
            assert result["cycle"]["cycle_id"] == i + 1

    def test_cycle_no_subsystems(self):
        ukp = UnifiedKernelProtocol()
        result = ukp.execute_unified_cycle({"sensor_data": 0})
        # Cycle still executes but with degraded confidence
        assert result["success"] is True
        assert result["cycle"]["phases"]["tri_core"]["confidence"] == 0.5


class TestGetStatus:
    def test_status_initial(self):
        ukp = UnifiedKernelProtocol()
        status = ukp.get_status()
        assert status["fusion_level"] == 0.0
        assert status["subsystem_count"] == 0
        assert status["cycle_count"] == 0
        assert status["health_tier"] == "critical"
        assert status["fusion_tier"] == "fragmented"

    def test_status_after_activity(self):
        ukp = UnifiedKernelProtocol()
        ukp.register_subsystem("mip", "tri_core_mip", ["verify"])
        ukp.register_subsystem("penta", "penta_core_loop", ["decide"])
        ukp.coordinate_subsystems()
        ukp.execute_unified_cycle({"sensor_data": 1})
        ukp.compute_fusion_level()
        status = ukp.get_status()
        assert status["subsystem_count"] == 2
        assert status["cycle_count"] == 1
        assert "fusion_tier" in status
        assert "subsystems" in status
        assert "mip" in status["subsystems"]


class TestSingleton:
    def test_singleton_returns_same_instance(self):
        # Reset global singleton for clean test
        import core.unified_kernel_protocol as mod

        mod._module = None
        a = get_unified_kernel_protocol()
        b = get_unified_kernel_protocol()
        assert a is b

    def test_singleton_is_unified_kernel_protocol(self):
        import core.unified_kernel_protocol as mod

        mod._module = None
        inst = get_unified_kernel_protocol()
        assert isinstance(inst, UnifiedKernelProtocol)
