"""
OMNI-HUB Spatial Reasoning Tests v86
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.spatial_reasoning import (
    SpatialEntity, SpatialReasoning, get_spatial_reasoning,
)


class TestSpatialReasoning:
    def test_initialization(self):
        sr = SpatialReasoning()
        assert len(sr.entities) == 0

    def test_add_entity(self):
        sr = SpatialReasoning()
        sr.add_entity("a", 0.0, 0.0, 1.0)
        assert "a" in sr.entities
        assert sr.entities["a"].position == (0.0, 0.0)

    def test_distance(self):
        sr = SpatialReasoning()
        sr.add_entity("a", 0.0, 0.0)
        sr.add_entity("b", 3.0, 4.0)
        assert sr.distance("a", "b") == 5.0

    def test_find_neighbors(self):
        sr = SpatialReasoning()
        sr.add_entity("a", 0.0, 0.0)
        sr.add_entity("b", 0.5, 0.5)
        sr.add_entity("c", 5.0, 5.0)
        neighbors = sr.find_neighbors("a", radius=1.0)
        assert "b" in neighbors
        assert "c" not in neighbors

    def test_find_path(self):
        sr = SpatialReasoning()
        sr.add_entity("start", 0.0, 0.0)
        sr.add_entity("mid", 1.0, 0.0)
        sr.add_entity("goal", 2.0, 0.0)
        path = sr.find_path("start", "goal")
        assert len(path) >= 2
        assert path[0] == "start"

    def test_build_from_state(self):
        sr = SpatialReasoning()
        sr.build_from_state({"level": 10})
        assert len(sr.entities) >= 8
        assert "self" in sr.entities

    def test_get_cluster_centers(self):
        sr = SpatialReasoning()
        sr.add_entity("a", -1.0, 0.0)
        sr.add_entity("b", 1.0, 0.0)
        centers = sr.get_cluster_centers()
        assert len(centers) == 2

    def test_get_status(self):
        sr = SpatialReasoning()
        sr.add_entity("a", 0.0, 0.0)
        status = sr.get_status()
        assert status["entities"] == 1


class TestGlobalEngine:
    def test_get_spatial_reasoning(self):
        g = get_spatial_reasoning()
        assert g is not None
        assert isinstance(g, SpatialReasoning)
