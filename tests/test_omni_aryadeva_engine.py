"""OMNI-HUB v265 Tests -- OMNIAryadevaEngine"""

import pytest
from core.omni_aryadeva_engine import (
    OMNIAryadevaEngine, HundredVersesGenerator, OneEyeCultivator,
    RefutationAffirmer, NalandaValidator, DiscipleCrown,
    AryadevaState, get_omni_aryadeva_engine
)


class TestHundredVersesGenerator:
    def test_generate(self):
        hvg = HundredVersesGenerator()
        r = hvg.generate(0.9)
        assert r > 0.0


class TestOneEyeCultivator:
    def test_cultivate(self):
        oec = OneEyeCultivator()
        r = oec.cultivate(0.9)
        assert r > 0.0


class TestRefutationAffirmer:
    def test_affirm(self):
        ra = RefutationAffirmer()
        r = ra.affirm(0.9)
        assert r > 0.0


class TestNalandaValidator:
    def test_validate(self):
        nv = NalandaValidator()
        r = nv.validate(0.9)
        assert r > 0.0


class TestDiscipleCrown:
    def test_bestow(self):
        dc = DiscipleCrown()
        r = dc.bestow(0.9)
        assert r > 0.0


class TestOMNIAryadevaEngine:
    def test_init(self):
        oad = OMNIAryadevaEngine()
        assert oad.VERSION == "265.0.0"

    def test_refute(self):
        oad = OMNIAryadevaEngine()
        r = oad.refute({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "aryadeva_score" in r

    def test_run_cycle(self):
        oad = OMNIAryadevaEngine()
        r = oad.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        oad = OMNIAryadevaEngine()
        s = oad.get_status()
        assert s["version"] == "265.0.0"

    def test_singleton(self):
        a = get_omni_aryadeva_engine()
        b = get_omni_aryadeva_engine()
        assert a is b
