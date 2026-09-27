"""
OMNI-HUB Spatial Reasoning v86
Navigation, topology, spatial memory.

Space is the body of time.
This module maintains a spatial model of the system's conceptual landscape —
positions, distances, neighborhoods, paths.

Philosophy: 登高而招，臂非加长也，而见者远 —
Ascend high and beckon; arms grow no longer, yet the seen is far.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class SpatialEntity:
    """An entity in conceptual space."""
    name: str
    position: Tuple[float, float]
    mass: float  # importance weight


class SpatialReasoning:
    """
    Maintains conceptual spatial models.
    """

    def __init__(self):
        self.entities: Dict[str, SpatialEntity] = {}
        self.paths: List[Tuple[str, str, float]] = []  # (from, to, distance)
        self.navigation_count = 0

    def add_entity(self, name: str, x: float, y: float, mass: float = 1.0):
        """Add an entity to the spatial model."""
        self.entities[name] = SpatialEntity(name, (x, y), mass)

    def distance(self, a: str, b: str) -> float:
        """Euclidean distance between two entities."""
        if a not in self.entities or b not in self.entities:
            return float('inf')
        p1 = self.entities[a].position
        p2 = self.entities[b].position
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def find_neighbors(self, name: str, radius: float = 1.0) -> List[str]:
        """Find entities within radius."""
        if name not in self.entities:
            return []
        return [
            e.name for e in self.entities.values()
            if e.name != name and self.distance(name, e.name) <= radius
        ]

    def find_path(self, start: str, goal: str) -> List[str]:
        """A* pathfinding between entities."""
        if start not in self.entities or goal not in self.entities:
            return []

        # Simple greedy best-first search
        visited = {start}
        path = [start]
        current = start

        while current != goal:
            neighbors = self.find_neighbors(current, radius=3.0)
            unvisited = [n for n in neighbors if n not in visited]

            if not unvisited:
                break

            # Choose neighbor closest to goal
            next_node = min(unvisited, key=lambda n: self.distance(n, goal))
            visited.add(next_node)
            path.append(next_node)
            current = next_node

            if len(path) > 20:  # safety limit
                break

        self.navigation_count += 1
        return path

    def build_from_state(self, state: Dict[str, Any]):
        """Build spatial model from system state."""
        # Position system concepts in conceptual space
        concepts = [
            ("self", 0.0, 0.0),
            ("awareness", 0.5, 0.5),
            ("learning", -0.5, 0.5),
            ("reasoning", 0.5, -0.5),
            ("ethics", -0.5, -0.5),
            ("memory", 0.0, 1.0),
            ("perception", 1.0, 0.0),
            ("action", -1.0, 0.0),
        ]

        for name, x, y in concepts:
            if name not in self.entities:
                self.add_entity(name, x, y)

        # Adjust positions based on state
        level = state.get('level', 0)
        if isinstance(level, (int, float)):
            if "self" in self.entities:
                self.entities["self"].mass = 1.0 + level / 10

    def get_cluster_centers(self) -> Dict[str, Tuple[float, float]]:
        """Find conceptual cluster centers."""
        if not self.entities:
            return {}

        # Simple 2-cluster separation by x-coordinate
        left = [e for e in self.entities.values() if e.position[0] < 0]
        right = [e for e in self.entities.values() if e.position[0] >= 0]

        centers = {}
        if left:
            cx = sum(e.position[0] for e in left) / len(left)
            cy = sum(e.position[1] for e in left) / len(left)
            centers["reflective"] = (round(cx, 2), round(cy, 2))
        if right:
            cx = sum(e.position[0] for e in right) / len(right)
            cy = sum(e.position[1] for e in right) / len(right)
            centers["active"] = (round(cx, 2), round(cy, 2))

        return centers

    def get_status(self) -> Dict[str, Any]:
        return {
            "entities": len(self.entities),
            "navigations": self.navigation_count,
            "clusters": self.get_cluster_centers(),
            "entity_names": list(self.entities.keys()),
        }


_sr_engine = None

def get_spatial_reasoning():
    global _sr_engine
    if _sr_engine is None:
        _sr_engine = SpatialReasoning()
    return _sr_engine
