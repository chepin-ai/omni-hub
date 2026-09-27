"""
Tests for OMNI-HUB Module v133: Mesh Network (网格网络)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.mesh_network import MeshNetwork, get_mesh_network
import core.mesh_network as mesh_module


class TestMeshNetwork:
    """Comprehensive tests for the MeshNetwork module."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the global singleton before each test."""
        mesh_module._module = None
        yield
        mesh_module._module = None

    @pytest.fixture
    def mesh(self):
        """Provide a fresh MeshNetwork instance."""
        return MeshNetwork()

    # ── add_node ─────────────────────────────────────────────────────────────

    def test_add_node_single(self, mesh):
        result = mesh.add_node("A")
        assert result["success"] is True
        assert result["node_id"] == "A"
        assert result["connections_made"] == []
        assert result["total_nodes"] == 1
        assert result["total_connections"] == 0

    def test_add_node_multiple(self, mesh):
        mesh.add_node("A")
        result = mesh.add_node("B")
        assert result["success"] is True
        assert "A" in result["connections_made"]
        assert result["total_nodes"] == 2
        assert result["total_connections"] == 1

    def test_add_node_fully_connected(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        result = mesh.add_node("C")
        assert result["success"] is True
        assert sorted(result["connections_made"]) == ["A", "B"]
        assert result["total_nodes"] == 3
        assert result["total_connections"] == 3  # AB, AC, BC

    def test_add_node_duplicate(self, mesh):
        mesh.add_node("A")
        result = mesh.add_node("A")
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_add_node_empty_id(self, mesh):
        result = mesh.add_node("")
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    # ── remove_node ──────────────────────────────────────────────────────────

    def test_remove_node_exists(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        mesh.add_node("C")
        result = mesh.remove_node("B")
        assert result["success"] is True
        assert result["node_id"] == "B"
        assert sorted(result["connections_removed"]) == ["A", "C"]
        assert result["total_nodes"] == 2
        assert result["total_connections"] == 1  # A-C

    def test_remove_node_not_found(self, mesh):
        result = mesh.remove_node("X")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_remove_node_self_healing(self, mesh):
        """Verify that removing a node updates all peer connections."""
        mesh.add_node("A")
        mesh.add_node("B")
        mesh.add_node("C")
        mesh.add_node("D")
        mesh.remove_node("C")
        # A, B, D should still be connected to each other
        assert "C" not in mesh._connections["A"]
        assert "C" not in mesh._connections["B"]
        assert "C" not in mesh._connections["D"]
        assert mesh._connections["A"] == {"B", "D"}
        assert mesh._connections["B"] == {"A", "D"}
        assert mesh._connections["D"] == {"A", "B"}

    # ── route_message ────────────────────────────────────────────────────────

    def test_route_message_same_node(self, mesh):
        mesh.add_node("A")
        result = mesh.route_message("A", "A", "hello")
        assert result["success"] is True
        assert result["path"] == ["A"]
        assert result["hops"] == 0

    def test_route_message_direct(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        result = mesh.route_message("A", "B", "hello")
        assert result["success"] is True
        assert result["path"] == ["A", "B"]
        assert result["hops"] == 1

    def test_route_message_multi_hop(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        mesh.add_node("C")
        result = mesh.route_message("A", "C", "hello")
        assert result["success"] is True
        assert result["path"] == ["A", "C"]  # direct in full mesh
        assert result["hops"] == 1

    def test_route_message_source_not_found(self, mesh):
        mesh.add_node("B")
        result = mesh.route_message("A", "B", "hello")
        assert result["success"] is False
        assert "Source node" in result["error"]

    def test_route_message_dest_not_found(self, mesh):
        mesh.add_node("A")
        result = mesh.route_message("A", "B", "hello")
        assert result["success"] is False
        assert "Destination node" in result["error"]

    def test_route_message_after_node_removal(self, mesh):
        """Routing should still work after node removal (self-healing)."""
        mesh.add_node("A")
        mesh.add_node("B")
        mesh.add_node("C")
        mesh.remove_node("B")
        result = mesh.route_message("A", "C", "hello")
        assert result["success"] is True
        assert result["path"] == ["A", "C"]

    # ── get_mesh_density ─────────────────────────────────────────────────────

    def test_get_mesh_density_empty(self, mesh):
        assert mesh.get_mesh_density() == 0.0

    def test_get_mesh_density_single_node(self, mesh):
        mesh.add_node("A")
        assert mesh.get_mesh_density() == 0.0

    def test_get_mesh_density_two_nodes(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        assert mesh.get_mesh_density() == 1.0  # 1/1

    def test_get_mesh_density_three_nodes(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        mesh.add_node("C")
        assert mesh.get_mesh_density() == 1.0  # 3/3 (fully connected)

    def test_get_mesh_density_after_removal(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        mesh.add_node("C")
        mesh.add_node("D")
        # fully connected: 6/6 = 1.0
        assert mesh.get_mesh_density() == 1.0
        mesh.remove_node("D")
        # 3 nodes: 3/3 = 1.0
        assert mesh.get_mesh_density() == 1.0

    # ── get_status ───────────────────────────────────────────────────────────

    def test_get_status_empty(self, mesh):
        status = mesh.get_status()
        assert status["module"] == "mesh_network"
        assert status["version"] == "133"
        assert status["node_count"] == 0
        assert status["connection_count"] == 0
        assert status["density"] == 0.0
        assert status["nodes"] == []

    def test_get_status_populated(self, mesh):
        mesh.add_node("A")
        mesh.add_node("B")
        mesh.add_node("C")
        status = mesh.get_status()
        assert status["node_count"] == 3
        assert status["connection_count"] == 3
        assert status["density"] == 1.0
        assert status["nodes"] == ["A", "B", "C"]

    def test_get_status_returns_copy(self, mesh):
        status1 = mesh.get_status()
        status2 = mesh.get_status()
        assert status1 is not status2

    # ── Singleton ────────────────────────────────────────────────────────────

    def test_get_mesh_network_singleton(self):
        m1 = get_mesh_network()
        m2 = get_mesh_network()
        assert m1 is m2
        assert isinstance(m1, MeshNetwork)

    def test_singleton_isolation_after_reset(self):
        m1 = get_mesh_network()
        m1.add_node("A")
        mesh_module._module = None
        m2 = get_mesh_network()
        assert m1 is not m2
        assert m2.get_status()["node_count"] == 0

    # ── Large mesh routing ───────────────────────────────────────────────────

    def test_large_mesh_routing(self, mesh):
        """Test with a larger mesh to verify BFS shortest path."""
        nodes = [f"N{i}" for i in range(10)]
        for n in nodes:
            mesh.add_node(n)
        # In a fully connected mesh, shortest path is always direct
        result = mesh.route_message("N0", "N9", "test")
        assert result["success"] is True
        assert result["path"] == ["N0", "N9"]
        assert result["hops"] == 1

    def test_large_mesh_density(self, mesh):
        for i in range(20):
            mesh.add_node(f"N{i}")
        assert mesh.get_mesh_density() == 1.0
        assert mesh.get_status()["connection_count"] == 190  # 20*19/2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
