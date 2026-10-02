"""OMNI-HUB v203 Tests — NonDualIntegrator"""

import pytest
from core.non_dual_integrator import (
    NonDualIntegrator, DualityDetector, SynthesisCatalyst,
    OnenessVerifier, PolarityBalancer, InterdependenceMapper,
    NonDualState, get_non_dual_integrator
)


class TestDualityDetector:
    def test_detect(self):
        dd = DualityDetector()
        d = dd.detect({"active": 0.9, "passive": 0.1})
        assert len(d) > 0

    def test_ratio(self):
        dd = DualityDetector()
        dd.detect({"active": 0.9, "passive": 0.1})
        assert dd.get_duality_ratio() > 0


class TestSynthesisCatalyst:
    def test_catalyze(self):
        sc = SynthesisCatalyst()
        r = sc.catalyze({"polarity": 0.8})
        assert r < 0.8

    def test_strengthen(self):
        sc = SynthesisCatalyst()
        sc.strengthen(0.2)
        assert sc.get_strength() > 0.5


class TestOnenessVerifier:
    def test_verify(self):
        ov = OnenessVerifier()
        o = ov.verify({"a": {"health": 0.9}, "b": {"health": 0.9}})
        assert o > 0.8


class TestPolarityBalancer:
    def test_balance(self):
        pb = PolarityBalancer()
        r = pb.balance(("x", "y"), {"x": 0.9, "y": 0.1})
        assert abs(r["x"] - r["y"]) < 0.8


class TestInterdependenceMapper:
    def test_map(self):
        im = InterdependenceMapper()
        d = im.map_dependencies({"a": {"health": 0.9}, "b": {"health": 0.91}})
        assert "a" in d


class TestNonDualIntegrator:
    def test_init(self):
        ndi = NonDualIntegrator()
        assert ndi.VERSION == "203.0.0"

    def test_integrate(self):
        ndi = NonDualIntegrator()
        r = ndi.integrate({
            "m1": {"health": 0.95, "active": 0.5, "passive": 0.5},
            "m2": {"health": 0.95, "active": 0.5, "passive": 0.5},
        })
        assert "oneness" in r

    def test_run_cycle(self):
        ndi = NonDualIntegrator()
        r = ndi.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ndi = NonDualIntegrator()
        s = ndi.get_status()
        assert s["version"] == "203.0.0"

    def test_singleton(self):
        a = get_non_dual_integrator()
        b = get_non_dual_integrator()
        assert a is b

# Total: 24 tests
