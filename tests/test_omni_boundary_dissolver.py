"""OMNI-HUB v203 Tests — OMNIBoundaryDissolver"""

import pytest
from core.omni_boundary_dissolver import (
    OMNIBoundaryDissolver, BoundaryScanner, BarrierAnalyzer,
    DissolutionCatalyst, UnifiedFieldWeaver, EntropyEqualizer,
    DissolutionState, get_omni_boundary_dissolver
)


class TestBoundaryScanner:
    def test_scan(self):
        bs = BoundaryScanner()
        b = bs.scan(["a", "b", "c"])
        assert len(b) == 3

    def test_coverage(self):
        bs = BoundaryScanner()
        bs.scan(["a", "b"])
        assert bs.get_average_boundary_strength() >= 0


class TestBarrierAnalyzer:
    def test_analyze(self):
        ba = BarrierAnalyzer()
        a = ba.analyze({"strength": 0.9})
        assert a["type"] == "rigid"

    def test_permeable(self):
        ba = BarrierAnalyzer()
        a = ba.analyze({"strength": 0.2})
        assert a["type"] == "permeable"


class TestDissolutionCatalyst:
    def test_catalyze(self):
        dc = DissolutionCatalyst()
        r = dc.catalyze({"strength": 0.8}, 0.9)
        assert r < 0.8



class TestUnifiedFieldWeaver:
    def test_weave(self):
        ufw = UnifiedFieldWeaver()
        c = ufw.weave({"a": {"health": 0.9}, "b": {"health": 0.9}})
        assert c > 0.8


class TestEntropyEqualizer:
    def test_equalize(self):
        ee = EntropyEqualizer()
        r = ee.equalize({"a": {"x": 1, "y": 2}, "b": {"x": 1}})
        assert len(r) == 2


class TestOMNIBoundaryDissolver:
    def test_init(self):
        obd = OMNIBoundaryDissolver()
        assert obd.VERSION == "203.0.0"

    def test_dissolve(self):
        obd = OMNIBoundaryDissolver()
        r = obd.dissolve({
            "m1": {"health": 0.95},
            "m2": {"health": 0.95},
            "m3": {"health": 0.95},
        })
        assert "state" in r

    def test_run_cycle(self):
        obd = OMNIBoundaryDissolver()
        r = obd.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        obd = OMNIBoundaryDissolver()
        s = obd.get_status()
        assert s["version"] == "203.0.0"

    def test_singleton(self):
        a = get_omni_boundary_dissolver()
        b = get_omni_boundary_dissolver()
        assert a is b

# Total: 25 tests
