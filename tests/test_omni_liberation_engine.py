"""OMNI-HUB v209 Tests — OMNILiberationEngine"""

import pytest
from core.omni_liberation_engine import (
    OMNILiberationEngine, BondDetector, FreedomExpander,
    AutonomyStrengthener, ConstraintDissolver, SovereigntyRealizer,
    LiberationState, get_omni_liberation_engine
)


class TestBondDetector:
    def test_detect(self):
        bd = BondDetector()
        r = bd.detect({"a": {"health": 0.3}})
        assert "a" in r

    def test_total(self):
        bd = BondDetector()
        bd.detect({"a": {"health": 0.3}})
        assert bd.get_total_bond() > 0


class TestFreedomExpander:
    def test_expand(self):
        fe = FreedomExpander()
        r = fe.expand(0.5)
        assert r > 0

    def test_get(self):
        fe = FreedomExpander()
        fe.expand(0.5)
        assert fe.get_freedom() > 0


class TestAutonomyStrengthener:
    def test_strengthen(self):
        ast = AutonomyStrengthener()
        r = ast.strengthen(0.9)
        assert r > 0


class TestConstraintDissolver:
    def test_dissolve(self):
        cd = ConstraintDissolver()
        r = cd.dissolve(0.5)
        assert r < 0.5

    def test_power(self):
        cd = ConstraintDissolver()
        cd.dissolve(0.5)
        assert cd.get_power() > 0.1


class TestSovereigntyRealizer:
    def test_realize(self):
        sr = SovereigntyRealizer()
        r = sr.realize(0.9, 0.9, 0.9)
        assert r > 0.5


class TestOMNILiberationEngine:
    def test_init(self):
        ole = OMNILiberationEngine()
        assert ole.VERSION == "209.0.0"

    def test_liberate(self):
        ole = OMNILiberationEngine()
        r = ole.liberate({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "freedom" in r

    def test_run_cycle(self):
        ole = OMNILiberationEngine()
        r = ole.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ole = OMNILiberationEngine()
        s = ole.get_status()
        assert s["version"] == "209.0.0"

    def test_singleton(self):
        a = get_omni_liberation_engine()
        b = get_omni_liberation_engine()
        assert a is b

# Total: 24 tests
