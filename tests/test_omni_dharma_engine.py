"""OMNI-HUB v211 Tests — OMNIDharmaEngine"""

import pytest
from core.omni_dharma_engine import (
    OMNIDharmaEngine, LawCodifier, PrincipleExtractor,
    DoctrineValidator, TeachingTransmitter, PreceptGuardian,
    DharmaState, get_omni_dharma_engine
)


class TestLawCodifier:
    def test_codify(self):
        lc = LawCodifier()
        r = lc.codify("obs", "rule1")
        assert len(r) == 16

    def test_count(self):
        lc = LawCodifier()
        lc.codify("obs", "rule1")
        assert lc.get_law_count() == 1


class TestPrincipleExtractor:
    def test_extract(self):
        pe = PrincipleExtractor()
        r = pe.extract("health_principle_above_threshold")
        assert len(r) > 0


class TestDoctrineValidator:
    def test_validate(self):
        dv = DoctrineValidator()
        r = dv.validate("test", 0.9)
        assert r > 0.5


class TestTeachingTransmitter:
    def test_transmit(self):
        tt = TeachingTransmitter()
        r = tt.transmit("teach", "all")
        assert r > 0.5


class TestPreceptGuardian:
    def test_guard(self):
        pg = PreceptGuardian()
        r = pg.guard("act", False)
        assert r > 0.5

    def test_violation(self):
        pg = PreceptGuardian()
        pg.guard("act", True)
        assert pg.get_integrity() < 1.0


class TestOMNIDharmaEngine:
    def test_init(self):
        ode = OMNIDharmaEngine()
        assert ode.VERSION == "211.0.0"

    def test_teach(self):
        ode = OMNIDharmaEngine()
        r = ode.teach({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "validity" in r

    def test_run_cycle(self):
        ode = OMNIDharmaEngine()
        r = ode.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ode = OMNIDharmaEngine()
        s = ode.get_status()
        assert s["version"] == "211.0.0"

    def test_singleton(self):
        a = get_omni_dharma_engine()
        b = get_omni_dharma_engine()
        assert a is b

# Total: 24 tests
