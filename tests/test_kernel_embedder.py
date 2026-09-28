"""
Tests for OMNI-HUB Kernel Embedder v164.

Tests cover: analyze, extract, embed, activate, deactivate, status,
and the three simulated kernels (qfos, linux, react).
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from typing import Dict, Any

from core.kernel_embedder import (
    KernelEmbedder,
    get_kernel_embedder,
    reset_kernel_embedder,
    EMBEDDING_STAGE_NATIVE,
    EMBEDDING_STAGE_EMBEDDED,
    EMBEDDING_STAGE_TRANSLATING,
    EMBEDDING_STAGE_ANALYZING,
    EMBEDDING_STAGE_FAILED,
)


# Simulated kernel specifications
QFOS_SPEC = {"type": "autonomous_navigation", "loops": ["perception", "planning", "control"], "lang": "Python"}
LINUX_SPEC = {"type": "operating_system", "loops": ["scheduler", "memory", "io"], "lang": "C"}
REACT_SPEC = {"type": "ui_framework", "loops": ["render", "diff", "commit"], "lang": "JavaScript"}


@pytest.fixture(autouse=True)
def fresh_embedder():
    """Provide a fresh KernelEmbedder for each test."""
    reset_kernel_embedder()
    yield get_kernel_embedder()


class TestAnalyzeKernel:
    """Tests for analyze_kernel method."""

    def test_analyze_qfos(self, fresh_embedder):
        result = fresh_embedder.analyze_kernel("qfos", QFOS_SPEC)
        assert result["success"] is True
        analysis = result["analysis"]
        assert analysis["kernel_name"] == "qfos"
        assert analysis["kernel_type"] == "autonomous_navigation"
        assert analysis["language"] == "Python"
        assert "core_loops" in analysis
        assert "data_structures" in analysis
        assert "control_flow" in analysis
        assert "interfaces" in analysis
        assert "dependencies" in analysis
        assert analysis["loop_count"] == 3

    def test_analyze_linux(self, fresh_embedder):
        result = fresh_embedder.analyze_kernel("linux", LINUX_SPEC)
        assert result["success"] is True
        analysis = result["analysis"]
        assert analysis["kernel_type"] == "operating_system"
        assert analysis["language"] == "C"
        assert analysis["loop_count"] == 3
        assert analysis["control_flow"]["pattern"] == "interrupt_driven"

    def test_analyze_react(self, fresh_embedder):
        result = fresh_embedder.analyze_kernel("react", REACT_SPEC)
        assert result["success"] is True
        analysis = result["analysis"]
        assert analysis["kernel_type"] == "ui_framework"
        assert analysis["language"] == "JavaScript"
        assert analysis["control_flow"]["pattern"] == "event_reactive"

    def test_analyze_invalid_name(self, fresh_embedder):
        result = fresh_embedder.analyze_kernel("", QFOS_SPEC)
        assert result["success"] is False
        result2 = fresh_embedder.analyze_kernel(None, QFOS_SPEC)
        assert result2["success"] is False

    def test_analyze_invalid_spec(self, fresh_embedder):
        result = fresh_embedder.analyze_kernel("test", None)
        assert result["success"] is False
        result2 = fresh_embedder.analyze_kernel("test", "not_a_dict")
        assert result2["success"] is False


class TestExtractCoreLoop:
    """Tests for extract_core_loop method."""

    def test_extract_qfos(self, fresh_embedder):
        result = fresh_embedder.extract_core_loop(QFOS_SPEC)
        assert result["success"] is True
        core = result["core_loop"]
        assert core["primary_loop"] == "perception"
        assert core["secondary_loops"] == ["planning", "control"]
        assert core["loop_count"] == 3
        assert core["execution_pattern"] == "sense_plan_act"
        assert len(core["loop_graph"]) == 3

    def test_extract_linux(self, fresh_embedder):
        result = fresh_embedder.extract_core_loop(LINUX_SPEC)
        assert result["success"] is True
        core = result["core_loop"]
        assert core["primary_loop"] == "scheduler"
        assert core["execution_pattern"] == "interrupt_driven"

    def test_extract_react(self, fresh_embedder):
        result = fresh_embedder.extract_core_loop(REACT_SPEC)
        assert result["success"] is True
        core = result["core_loop"]
        assert core["primary_loop"] == "render"
        assert core["execution_pattern"] == "event_reactive"

    def test_extract_empty_loops(self, fresh_embedder):
        result = fresh_embedder.extract_core_loop({"type": "empty", "loops": [], "lang": "Python"})
        assert result["success"] is False
        assert "error" in result

    def test_extract_invalid_spec(self, fresh_embedder):
        result = fresh_embedder.extract_core_loop(None)
        assert result["success"] is False


class TestEmbedKernel:
    """Tests for embed_kernel full pipeline."""

    def test_embed_qfos(self, fresh_embedder):
        result = fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        assert result["success"] is True
        assert result["kernel_name"] == "qfos"
        assert result["stage"] == EMBEDDING_STAGE_NATIVE
        assert result["active"] is True
        assert "analysis" in result
        assert "core_loop" in result

    def test_embed_linux(self, fresh_embedder):
        result = fresh_embedder.embed_kernel("linux", LINUX_SPEC)
        assert result["success"] is True
        assert result["stage"] == EMBEDDING_STAGE_NATIVE
        assert result["active"] is True

    def test_embed_react(self, fresh_embedder):
        result = fresh_embedder.embed_kernel("react", REACT_SPEC)
        assert result["success"] is True
        assert result["stage"] == EMBEDDING_STAGE_NATIVE
        assert result["active"] is True

    def test_embed_duplicate_fails(self, fresh_embedder):
        r1 = fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        assert r1["success"] is True
        r2 = fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        assert r2["success"] is False
        assert "already embedded" in r2["error"]

    def test_embed_invalid_name(self, fresh_embedder):
        result = fresh_embedder.embed_kernel("", QFOS_SPEC)
        assert result["success"] is False

    def test_embed_invalid_spec(self, fresh_embedder):
        result = fresh_embedder.embed_kernel("test", None)
        assert result["success"] is False


class TestActivateEmbeddedKernel:
    """Tests for activate_embedded_kernel method."""

    def test_activate_existing(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        # Deactivate first so we can test activation
        fresh_embedder.deactivate_kernel("qfos")
        result = fresh_embedder.activate_embedded_kernel("qfos")
        assert result["success"] is True
        assert result["status"] == "activated"

    def test_activate_already_active(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        result = fresh_embedder.activate_embedded_kernel("qfos")
        assert result["success"] is True
        assert result["status"] == "already_active"

    def test_activate_not_found(self, fresh_embedder):
        result = fresh_embedder.activate_embedded_kernel("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_activate_invalid_name(self, fresh_embedder):
        result = fresh_embedder.activate_embedded_kernel("")
        assert result["success"] is False


class TestDeactivateKernel:
    """Tests for deactivate_kernel method."""

    def test_deactivate_active(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        result = fresh_embedder.deactivate_kernel("qfos")
        assert result["success"] is True
        assert result["status"] == "deactivated"
        assert "deactivated_at" in result

    def test_deactivate_already_inactive(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        fresh_embedder.deactivate_kernel("qfos")
        result = fresh_embedder.deactivate_kernel("qfos")
        assert result["success"] is True
        assert result["status"] == "already_inactive"

    def test_deactivate_not_found(self, fresh_embedder):
        result = fresh_embedder.deactivate_kernel("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_deactivate_invalid_name(self, fresh_embedder):
        result = fresh_embedder.deactivate_kernel("")
        assert result["success"] is False


class TestGetKernelStatus:
    """Tests for get_kernel_status method."""

    def test_status_embedded(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        result = fresh_embedder.get_kernel_status("qfos")
        assert result["success"] is True
        assert result["kernel_name"] == "qfos"
        assert result["kernel_type"] == "autonomous_navigation"
        assert result["language"] == "Python"
        assert result["stage"] == EMBEDDING_STAGE_NATIVE
        assert result["active"] is True
        assert result["loop_count"] == 3
        assert result["loops"] == ["perception", "planning", "control"]

    def test_status_not_found(self, fresh_embedder):
        result = fresh_embedder.get_kernel_status("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_status_invalid_name(self, fresh_embedder):
        result = fresh_embedder.get_kernel_status("")
        assert result["success"] is False


class TestGetStatus:
    """Tests for get_status method."""

    def test_empty_status(self, fresh_embedder):
        status = fresh_embedder.get_status()
        assert status["embedded_count"] == 0
        assert status["active_count"] == 0
        assert status["inactive_count"] == 0
        assert status["embedding_history_count"] >= 0
        assert status["embedded_kernels"] == []

    def test_with_embedded_kernels(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        fresh_embedder.embed_kernel("linux", LINUX_SPEC)
        status = fresh_embedder.get_status()
        assert status["embedded_count"] == 2
        assert status["active_count"] == 2
        assert status["inactive_count"] == 0
        assert len(status["embedded_kernels"]) == 2
        assert status["stage_distribution"].get(EMBEDDING_STAGE_NATIVE, 0) == 2

    def test_after_deactivation(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        fresh_embedder.deactivate_kernel("qfos")
        status = fresh_embedder.get_status()
        assert status["embedded_count"] == 1
        assert status["active_count"] == 0
        assert status["inactive_count"] == 1


class TestSingleton:
    """Tests for global singleton."""

    def test_singleton_returns_same_instance(self):
        reset_kernel_embedder()
        e1 = get_kernel_embedder()
        e2 = get_kernel_embedder()
        assert e1 is e2
        assert isinstance(e1, KernelEmbedder)

    def test_reset_creates_new_instance(self):
        e1 = get_kernel_embedder()
        reset_kernel_embedder()
        e2 = get_kernel_embedder()
        assert e1 is not e2
        assert isinstance(e2, KernelEmbedder)


class TestEdgeCases:
    """Edge case and defensive programming tests."""

    def test_none_kernel_name(self, fresh_embedder):
        assert fresh_embedder.embed_kernel(None, QFOS_SPEC)["success"] is False
        assert fresh_embedder.activate_embedded_kernel(None)["success"] is False
        assert fresh_embedder.deactivate_kernel(None)["success"] is False
        assert fresh_embedder.get_kernel_status(None)["success"] is False

    def test_list_kernels(self, fresh_embedder):
        assert fresh_embedder.list_kernels() == []
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        assert fresh_embedder.list_kernels() == ["qfos"]

    def test_remove_kernel(self, fresh_embedder):
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        result = fresh_embedder.remove_kernel("qfos")
        assert result["success"] is True
        assert result["status"] == "removed"
        assert "qfos" not in fresh_embedder.list_kernels()

    def test_remove_not_found(self, fresh_embedder):
        result = fresh_embedder.remove_kernel("nonexistent")
        assert result["success"] is False

    def test_remove_invalid_name(self, fresh_embedder):
        result = fresh_embedder.remove_kernel("")
        assert result["success"] is False

    def test_all_three_kernels(self, fresh_embedder):
        """Embed all three simulated kernels and verify global status."""
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)
        fresh_embedder.embed_kernel("linux", LINUX_SPEC)
        fresh_embedder.embed_kernel("react", REACT_SPEC)

        status = fresh_embedder.get_status()
        assert status["embedded_count"] == 3
        assert status["active_count"] == 3

        # Verify individual statuses
        qfos = fresh_embedder.get_kernel_status("qfos")
        assert qfos["kernel_type"] == "autonomous_navigation"
        assert qfos["language"] == "Python"

        linux = fresh_embedder.get_kernel_status("linux")
        assert linux["kernel_type"] == "operating_system"
        assert linux["language"] == "C"

        react = fresh_embedder.get_kernel_status("react")
        assert react["kernel_type"] == "ui_framework"
        assert react["language"] == "JavaScript"

    def test_activate_deactivate_cycle(self, fresh_embedder):
        """Test activate -> deactivate -> activate cycle."""
        fresh_embedder.embed_kernel("qfos", QFOS_SPEC)

        # Should be active after embed
        status = fresh_embedder.get_kernel_status("qfos")
        assert status["active"] is True

        # Deactivate
        r1 = fresh_embedder.deactivate_kernel("qfos")
        assert r1["status"] == "deactivated"
        status = fresh_embedder.get_kernel_status("qfos")
        assert status["active"] is False
        assert status["stage"] == EMBEDDING_STAGE_EMBEDDED

        # Activate again
        r2 = fresh_embedder.activate_embedded_kernel("qfos")
        assert r2["status"] == "activated"
        status = fresh_embedder.get_kernel_status("qfos")
        assert status["active"] is True
        assert status["stage"] == EMBEDDING_STAGE_NATIVE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
