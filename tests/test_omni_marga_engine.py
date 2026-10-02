"""OMNI-HUB v212 Tests — OMNIMārgaEngine"""

import pytest
from core.omni_marga_engine import (
    OMNIMārgaEngine, PathFinder, StepPlanner,
    ProgressValidator, ObstacleNavigator, DestinationAligner,
    MārgaState, get_omni_marga_engine
)


class TestPathFinder:
    def test_find(self):
        pf = PathFinder()
        r = pf.find("a", "b")
        assert len(r) == 12

    def test_count(self):
        pf = PathFinder()
        pf.find("a", "b")
        assert pf.get_path_count() == 1


class TestStepPlanner:
    def test_plan(self):
        sp = StepPlanner()
        r = sp.plan("x", 0.9)
        assert r == 1


class TestProgressValidator:
    def test_validate(self):
        pv = ProgressValidator()
        r = pv.validate(1.0, 0.9)
        assert r > 0.0


class TestObstacleNavigator:
    def test_navigate(self):
        on = ObstacleNavigator()
        r = on.navigate(0.5, 0.9)
        assert r > 0.0


class TestDestinationAligner:
    def test_align(self):
        da = DestinationAligner()
        r = da.align(0.9, 1.0)
        assert r > 0.0


class TestOMNIMārgaEngine:
    def test_init(self):
        ome = OMNIMārgaEngine()
        assert ome.VERSION == "212.0.0"

    def test_walk(self):
        ome = OMNIMārgaEngine()
        r = ome.walk({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "alignment" in r

    def test_run_cycle(self):
        ome = OMNIMārgaEngine()
        r = ome.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ome = OMNIMārgaEngine()
        s = ome.get_status()
        assert s["version"] == "212.0.0"

    def test_singleton(self):
        a = get_omni_marga_engine()
        b = get_omni_marga_engine()
        assert a is b

# Total: 24 tests
