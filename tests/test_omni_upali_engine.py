"""OMNI-HUB v259 Tests -- OMNIUpaliEngine"""

import pytest
from core.omni_upali_engine import (
    OMNIUpaliEngine, PreceptHoldGenerator, VinayaCultivator,
    DisciplineAffirmer, PatimokkhaValidator, VinayaFirstCrown,
    UpaliState, get_omni_upali_engine
)


class TestPreceptHoldGenerator:
    def test_generate(self):
        phg = PreceptHoldGenerator()
        r = phg.generate(0.9)
        assert r > 0.0


class TestVinayaCultivator:
    def test_cultivate(self):
        vc = VinayaCultivator()
        r = vc.cultivate(0.9)
        assert r > 0.0


class TestDisciplineAffirmer:
    def test_affirm(self):
        da = DisciplineAffirmer()
        r = da.affirm(0.9)
        assert r > 0.0


class TestPatimokkhaValidator:
    def test_validate(self):
        pv = PatimokkhaValidator()
        r = pv.validate(0.9)
        assert r > 0.0


class TestVinayaFirstCrown:
    def test_bestow(self):
        vfc = VinayaFirstCrown()
        r = vfc.bestow(0.9)
        assert r > 0.0


class TestOMNIUpaliEngine:
    def test_init(self):
        oup = OMNIUpaliEngine()
        assert oup.VERSION == "259.0.0"

    def test_uphold(self):
        oup = OMNIUpaliEngine()
        r = oup.uphold({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "upali_score" in r

    def test_run_cycle(self):
        oup = OMNIUpaliEngine()
        r = oup.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        oup = OMNIUpaliEngine()
        s = oup.get_status()
        assert s["version"] == "259.0.0"

    def test_singleton(self):
        a = get_omni_upali_engine()
        b = get_omni_upali_engine()
        assert a is b
