"""OMNI-HUB v206 Tests — OMNIPotentialityEngine"""

import pytest
from core.omni_potentiality_engine import (
    OMNIPotentialityEngine, LatentDetector, PossibilityExpander,
    SeedActivator, FutureProjector, EmbodimentCatalyst,
    PotentialityState, get_omni_potentiality_engine
)


class TestLatentDetector:
    def test_detect(self):
        ld = LatentDetector()
        p = ld.detect({"a": {"health": 0.5}})
        assert "a" in p

    def test_total(self):
        ld = LatentDetector()
        ld.detect({"a": {"health": 0.3}})
        assert ld.get_total_potential() > 0


class TestPossibilityExpander:
    def test_expand(self):
        pe = PossibilityExpander()
        r = pe.expand(0.5)
        assert r >= 0.5

    def test_factor(self):
        pe = PossibilityExpander()
        pe.expand(0.1)
        assert pe.get_factor() > 1.0


class TestSeedActivator:
    def test_activate(self):
        sa = SeedActivator()
        r = sa.activate("s1", 0.9)
        assert r > 0

    def test_rate(self):
        sa = SeedActivator()
        sa.activate("s1", 0.9)
        assert sa.get_activation_rate() >= 0


class TestFutureProjector:
    def test_project(self):
        fp = FutureProjector()
        r = fp.project(0.5, 0.01)
        assert r > 0.5


class TestEmbodimentCatalyst:
    def test_catalyze(self):
        ec = EmbodimentCatalyst()
        r = ec.catalyze(0.5, 0.5)
        assert r >= 0


class TestOMNIPotentialityEngine:
    def test_init(self):
        ope = OMNIPotentialityEngine()
        assert ope.VERSION == "206.0.0"

    def test_actualize(self):
        ope = OMNIPotentialityEngine()
        r = ope.actualize({"m1": {"health": 0.3}, "m2": {"health": 0.3}})
        assert "total_potential" in r

    def test_run_cycle(self):
        ope = OMNIPotentialityEngine()
        r = ope.run_cycle({"m1": {"health": 0.3}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ope = OMNIPotentialityEngine()
        s = ope.get_status()
        assert s["version"] == "206.0.0"

    def test_singleton(self):
        a = get_omni_potentiality_engine()
        b = get_omni_potentiality_engine()
        assert a is b

# Total: 24 tests
