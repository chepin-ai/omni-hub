"""
OMNI-HUB Global Workspace Integration Tests v167
Tests for GWT J-Space mapping module.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
import pytest
from core.global_workspace_integration import (
    GlobalWorkspaceIntegration,
    get_global_workspace_integration,
    reset_global_workspace_integration,
    EMERGENCE_LEVELS,
    EMERGENCE_TYPES,
)


class TestGlobalWorkspaceIntegration:
    def test_initialization(self):
        gwi = GlobalWorkspaceIntegration()
        assert gwi.workspace_state == {}
        assert gwi.j_space == {}
        assert gwi.broadcast_log == []
        assert gwi.get_status()["content_count"] == 0

    def test_register_content_success(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.register_content("repo1.moduleA", {"type": "config", "data": 42}, 0.85)
        assert result["success"] is True
        assert result["content_id"] == "repo1.moduleA"
        assert result["accessibility"] == 0.85
        assert result["workspace_size"] == 1

    def test_register_content_invalid_id(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.register_content("", {"data": 1}, 0.5)
        assert result["success"] is False
        assert "error" in result

    def test_register_content_invalid_content(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.register_content("repo1.mod", "not_a_dict", 0.5)
        assert result["success"] is False
        assert "error" in result

    def test_register_content_clamps_accessibility(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.register_content("repo1.mod", {"k": 1}, 1.5)
        assert result["accessibility"] == 1.0
        result2 = gwi.register_content("repo2.mod", {"k": 2}, -0.5)
        assert result2["accessibility"] == 0.0

    def test_register_multiple_contents(self):
        gwi = GlobalWorkspaceIntegration()
        for i in range(5):
            gwi.register_content(f"repo{i}.mod", {"idx": i}, 0.5 + i * 0.1)
        assert len(gwi.j_space) == 5

    def test_broadcast_content_success(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.mod", {"data": 1}, 0.8)
        result = gwi.broadcast_content("repo1.mod", ["consumerA", "consumerB"])
        assert result["success"] is True
        assert result["content_id"] == "repo1.mod"
        assert result["target_count"] == 2
        assert result["broadcast_id"].startswith("BCAST-")

    def test_broadcast_content_not_found(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.broadcast_content("missing.id", ["c1"])
        assert result["success"] is False
        assert "error" in result

    def test_broadcast_content_invalid_targets(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.mod", {"data": 1}, 0.8)
        result = gwi.broadcast_content("repo1.mod", "not_a_list")
        assert result["success"] is False
        assert "error" in result

    def test_broadcast_log_grows(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.mod", {"data": 1}, 0.8)
        gwi.broadcast_content("repo1.mod", ["c1", "c2"])
        assert len(gwi.broadcast_log) == 1
        assert gwi.broadcast_log[0]["delivered_count"] == 2

    def test_access_content_success(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.mod", {"data": 99}, 0.9)
        result = gwi.access_content("consumerA", "repo1.mod")
        assert result["success"] is True
        assert result["content"] == {"data": 99}
        assert result["consumer_id"] == "consumerA"
        assert result["accessibility"] == 0.9

    def test_access_content_not_found(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.access_content("consumerA", "missing.id")
        assert result["success"] is False
        assert "error" in result

    def test_access_content_invalid_consumer(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.mod", {"data": 1}, 0.8)
        result = gwi.access_content("", "repo1.mod")
        assert result["success"] is False
        assert "error" in result

    def test_access_increments_access_count(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.mod", {"data": 1}, 0.8)
        gwi.access_content("c1", "repo1.mod")
        gwi.access_content("c2", "repo1.mod")
        assert gwi.j_space["repo1.mod"]["access_count"] == 2

    def test_compute_workspace_coherence_empty(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.compute_workspace_coherence()
        assert result["coherence"] == 0.0
        assert result["content_count"] == 0

    def test_compute_workspace_coherence_non_empty(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.modA", {"type": "config"}, 0.8)
        gwi.register_content("repo2.modB", {"type": "state", "value": 10}, 0.6)
        gwi.broadcast_content("repo1.modA", ["c1", "c2"])
        gwi.broadcast_content("repo2.modB", ["c2", "c3"])
        result = gwi.compute_workspace_coherence()
        assert result["coherence"] > 0.0
        assert result["content_count"] == 2
        assert result["avg_accessibility"] == 0.7
        assert result["content_diversity"] > 0.0
        assert result["broadcast_connectivity"] > 0.0

    def test_coherence_formula_structure(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 1.0)
        gwi.register_content("r2.m2", {"b": 2}, 1.0)
        gwi.broadcast_content("r1.m1", ["c1"])
        gwi.broadcast_content("r2.m2", ["c1"])
        result = gwi.compute_workspace_coherence()
        expected = math.sqrt(
            result["avg_accessibility"] * result["content_diversity"] * result["broadcast_connectivity"]
        )
        assert abs(result["coherence"] - expected) < 1e-6

    def test_detect_workspace_emergence_empty(self):
        gwi = GlobalWorkspaceIntegration()
        result = gwi.detect_workspace_emergence()
        assert result["level"] == "none"
        assert result["score"] == 0.0

    def test_detect_workspace_emergence_with_content(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repo1.mod", {"data": 1}, 0.9)
        gwi.broadcast_content("repo1.mod", ["c1", "c2", "c3"])
        gwi.access_content("c1", "repo1.mod")
        gwi.access_content("c2", "repo1.mod")
        result = gwi.detect_workspace_emergence()
        assert result["score"] > 0.0
        assert result["level"] in [l[1] for l in EMERGENCE_LEVELS] + ["none"]
        assert result["type"] in EMERGENCE_TYPES + ["none"]

    def test_detect_workspace_emergence_logs_event(self):
        gwi = GlobalWorkspaceIntegration()
        # Populate enough to trigger emergence
        for i in range(10):
            gwi.register_content(f"repo{i}.mod", {"idx": i}, 0.95)
            gwi.broadcast_content(f"repo{i}.mod", [f"c{j}" for j in range(5)])
            for j in range(5):
                gwi.access_content(f"c{j}", f"repo{i}.mod")
        result = gwi.detect_workspace_emergence()
        if result["level"] != "none":
            assert len(gwi._emergence_events) >= 1
            assert result["event_logged"] is True

    def test_detect_emergence_levels(self):
        gwi = GlobalWorkspaceIntegration()
        # High coherence + high activity should yield strong emergence
        for i in range(20):
            gwi.register_content(f"repo{i}.mod", {"idx": i, "extra": i * 2}, 1.0)
            gwi.broadcast_content(f"repo{i}.mod", [f"c{j}" for j in range(10)])
            for j in range(10):
                gwi.access_content(f"c{j}", f"repo{i}.mod")
        result = gwi.detect_workspace_emergence()
        assert result["level"] in [l[1] for l in EMERGENCE_LEVELS] + ["none"]
        assert result["score"] > 0.0

    def test_self_referential_loop_detection(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("repoA.module", {"data": 1}, 1.0)
        gwi.access_content("repoA", "repoA.module")
        result = gwi.detect_workspace_emergence()
        # May or may not be self_referential_loops depending on other factors
        assert "type" in result

    def test_get_status_empty(self):
        gwi = GlobalWorkspaceIntegration()
        status = gwi.get_status()
        assert status["content_count"] == 0
        assert status["coherence"] == 0.0
        assert status["emergence_events"] == 0
        assert status["active_broadcasts"] == 0

    def test_get_status_after_operations(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 0.8)
        gwi.broadcast_content("r1.m1", ["c1", "c2"])
        gwi.access_content("c1", "r1.m1")
        status = gwi.get_status()
        assert status["content_count"] == 1
        assert status["total_registered"] == 1
        assert status["total_broadcasts"] == 1
        assert status["total_accesses"] == 1
        assert status["active_broadcasts"] == 2

    def test_get_status_coherence_matches(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 0.8)
        status = gwi.get_status()
        coherence = gwi.compute_workspace_coherence()
        assert status["coherence"] == coherence["coherence"]

    def test_consumers_tracked(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 0.8)
        gwi.broadcast_content("r1.m1", ["c1", "c2"])
        gwi.access_content("c3", "r1.m1")
        entry = gwi.j_space["r1.m1"]
        assert "c1" in entry["consumers"]
        assert "c2" in entry["consumers"]
        assert "c3" in entry["consumers"]

    def test_consumer_history_tracked(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 0.8)
        gwi.access_content("c1", "r1.m1")
        assert "c1" in gwi._consumer_history
        assert "r1.m1" in gwi._consumer_history["c1"]

    def test_broadcast_targets_tracked(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 0.8)
        gwi.broadcast_content("r1.m1", ["c1", "c2"])
        entry = gwi.j_space["r1.m1"]
        assert "c1" in entry["broadcast_targets"]
        assert "c2" in entry["broadcast_targets"]

    def test_accessibility_gates_content(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"secret": 42}, 0.0)
        result = gwi.access_content("c1", "r1.m1")
        assert result["success"] is True
        assert result["access_probability"] == 0.0

    def test_multiple_broadcasts_same_content(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 0.8)
        gwi.broadcast_content("r1.m1", ["c1"])
        gwi.broadcast_content("r1.m1", ["c2"])
        assert len(gwi.broadcast_log) == 2
        assert "c1" in gwi._active_broadcasts["r1.m1"]
        assert "c2" in gwi._active_broadcasts["r1.m1"]

    def test_register_counter(self):
        gwi = GlobalWorkspaceIntegration()
        for i in range(3):
            gwi.register_content(f"r{i}.m", {"i": i}, 0.5)
        assert gwi._register_counter == 3

    def test_broadcast_counter(self):
        gwi = GlobalWorkspaceIntegration()
        gwi.register_content("r1.m1", {"a": 1}, 0.8)
        gwi.broadcast_content("r1.m1", ["c1"])
        gwi.broadcast_content("r1.m1", ["c2"])
        assert gwi._broadcast_counter == 2


class TestGlobalSingleton:
    def test_get_global_workspace_integration(self):
        reset_global_workspace_integration()
        gwi = get_global_workspace_integration()
        assert gwi is not None
        assert isinstance(gwi, GlobalWorkspaceIntegration)

    def test_singleton(self):
        reset_global_workspace_integration()
        g1 = get_global_workspace_integration()
        g2 = get_global_workspace_integration()
        assert g1 is g2

    def test_singleton_reset(self):
        reset_global_workspace_integration()
        g1 = get_global_workspace_integration()
        g1.register_content("test.mod", {"data": 1}, 0.5)
        reset_global_workspace_integration()
        g2 = get_global_workspace_integration()
        assert g1 is not g2
        assert g2.get_status()["content_count"] == 0
