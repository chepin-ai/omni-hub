"""
OMNI-HUB Module v133: Mesh Network (网格网络)

Fully connected mesh topology. Each node connects to all others.
Messages route through shortest path. Self-healing when nodes drop.
"""

from typing import Dict, List, Optional, Set
from collections import deque

try:
    from core.event_bus import get_event_bus
    from core.topics import Topics
    _EVENT_BUS_AVAILABLE = True
except ImportError:
    _EVENT_BUS_AVAILABLE = False

_module: Optional["MeshNetwork"] = None


class MeshNetwork:
    """Fully connected mesh network with shortest-path routing."""

    def __init__(self) -> None:
        self._nodes: Set[str] = set()
        self._connections: Dict[str, Set[str]] = {}
        self._status: Dict[str, any] = {
            "module": "mesh_network",
            "version": "133",
            "state": "initialized",
        }

    def _publish_state(self, state: str) -> None:
        self._status["state"] = state
        if _EVENT_BUS_AVAILABLE:
            try:
                bus = get_event_bus()
                bus.publish_simple(
                    Topics.STATE_CHANGE,
                    {
                        "module": "mesh_network",
                        "state": state,
                        "node_count": len(self._nodes),
                        "connection_count": self._count_connections(),
                    },
                )
            except Exception:
                pass

    def _count_connections(self) -> int:
        """Count unique undirected connections."""
        total = 0
        for node, peers in self._connections.items():
            total += len(peers)
        return total // 2

    def add_node(self, node_id: str) -> Dict:
        """Add a node to the mesh. Auto-connects to all existing nodes."""
        if not node_id:
            return {
                "success": False,
                "error": "node_id cannot be empty",
                "node_id": node_id,
            }

        if node_id in self._nodes:
            return {
                "success": False,
                "error": f"Node '{node_id}' already exists",
                "node_id": node_id,
            }

        self._nodes.add(node_id)
        self._connections[node_id] = set()

        # Auto-connect to all existing nodes (fully connected mesh)
        new_connections = []
        for existing_node in self._nodes:
            if existing_node != node_id:
                self._connections[node_id].add(existing_node)
                self._connections[existing_node].add(node_id)
                new_connections.append(existing_node)

        self._publish_state("node_added")

        return {
            "success": True,
            "node_id": node_id,
            "connections_made": new_connections,
            "total_nodes": len(self._nodes),
            "total_connections": self._count_connections(),
        }

    def remove_node(self, node_id: str) -> Dict:
        """Remove a node from the mesh. Self-heals by updating all peer connections."""
        if node_id not in self._nodes:
            return {
                "success": False,
                "error": f"Node '{node_id}' not found",
                "node_id": node_id,
            }

        # Remove this node from all peer connection lists
        peers = list(self._connections[node_id])
        for peer in peers:
            self._connections[peer].discard(node_id)

        del self._connections[node_id]
        self._nodes.discard(node_id)

        self._publish_state("node_removed")

        return {
            "success": True,
            "node_id": node_id,
            "connections_removed": peers,
            "total_nodes": len(self._nodes),
            "total_connections": self._count_connections(),
        }

    def route_message(self, from_id: str, to_id: str, message: str) -> Dict:
        """Find the shortest path between two nodes using BFS."""
        if from_id not in self._nodes:
            return {
                "success": False,
                "error": f"Source node '{from_id}' not found",
                "from": from_id,
                "to": to_id,
            }

        if to_id not in self._nodes:
            return {
                "success": False,
                "error": f"Destination node '{to_id}' not found",
                "from": from_id,
                "to": to_id,
            }

        # BFS for shortest path
        if from_id == to_id:
            path = [from_id]
        else:
            path = self._bfs_shortest_path(from_id, to_id)

        if path is None:
            return {
                "success": False,
                "error": f"No route found from '{from_id}' to '{to_id}'",
                "from": from_id,
                "to": to_id,
            }

        return {
            "success": True,
            "from": from_id,
            "to": to_id,
            "path": path,
            "hops": len(path) - 1,
            "message_length": len(message),
        }

    def _bfs_shortest_path(self, start: str, goal: str) -> Optional[List[str]]:
        """Breadth-first search for shortest path in unweighted graph."""
        if start == goal:
            return [start]

        queue: deque = deque([(start, [start])])
        visited: Set[str] = {start}

        while queue:
            current, path = queue.popleft()
            for neighbor in self._connections.get(current, set()):
                if neighbor == goal:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_mesh_density(self) -> float:
        """
        Return mesh density: actual connections / max possible connections.
        For N nodes, max connections = N*(N-1)/2.
        """
        n = len(self._nodes)
        if n < 2:
            return 0.0
        max_connections = n * (n - 1) // 2
        actual_connections = self._count_connections()
        return actual_connections / max_connections

    def get_status(self) -> Dict:
        """Return current mesh status."""
        self._status.update({
            "node_count": len(self._nodes),
            "connection_count": self._count_connections(),
            "density": self.get_mesh_density(),
            "nodes": sorted(list(self._nodes)),
        })
        return self._status.copy()


def get_mesh_network() -> MeshNetwork:
    """Global singleton accessor for MeshNetwork."""
    global _module
    if _module is None:
        _module = MeshNetwork()
    return _module
