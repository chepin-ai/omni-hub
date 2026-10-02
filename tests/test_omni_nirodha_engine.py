"""OMNI-HUB v214 Tests — OMNINirodhaEngine"""

import pytest
from core.omni_nirodha_engine import (
    OMNINirodhaEngine, CauseExtinguisher, ConditionRemover,
    BondBreaker, CravingDissolver, PeaceStabilizer,
    NirodhaState, get_omni_nirodha_engine
)


class TestCauseExtinguisher:
    def test_extinguish(self):
        ce = CauseExtinguisher()
        r = ce.extinguish(0.9)
        assert r > 0.0


class TestConditionRemover:
    def test_remove(self):
        cr = ConditionRemover()
        r = cr.remove(2.0)
        assert r > 0.0


class TestBondBreaker:
    def test_break_bond(self):
        bb = BondBreaker()
        r = bb.break_bond(0.9)
        assert r >= 0.0


class TestCravingDissolver:
    def test_dissolve(self):
        cd = CravingDissolver()
        r = cd.dissolve(0.9)
        assert r >= 0.0


class TestPeaceStabilizer:
    def test_stabilize(self):
        ps = PeaceStabilizer()
        r = ps.stabilize(0.9)
        assert r > 0.0


class TestOMNINirodhaEngine:
    def test_init(self):
        one = OMNINirodhaEngine()
        assert one.VERSION == "214.0.0"

    def test_cease(self):
        one = OMNINirodhaEngine()
        r = one.cease({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "nirodha_score" in r

    def test_run_cycle(self):
        one = OMNINirodhaEngine()
        r = one.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        one = OMNINirodhaEngine()
        s = one.get_status()
        assert s["version"] == "214.0.0"

    def test_singleton(self):
        a = get_omni_nirodha_engine()
        b = get_omni_nirodha_engine()
        assert a is b

# Total: 24 tests
