"""OMNI-HUB v250 Tests -- OMNITsongkhapaEngine"""

import pytest
from core.omni_tsongkhapa_engine import (
    OMNITsongkhapaEngine, ManjushriSwordGenerator, GraduatedPathCultivator,
    GoldenRosaryAffirmer, VinayaValidator, ManjushriCrown,
    TsongkhapaState, get_omni_tsongkhapa_engine
)


class TestManjushriSwordGenerator:
    def test_generate(self):
        msg = ManjushriSwordGenerator()
        r = msg.generate(0.9)
        assert r > 0.0


class TestGraduatedPathCultivator:
    def test_cultivate(self):
        gpc = GraduatedPathCultivator()
        r = gpc.cultivate(0.9)
        assert r > 0.0


class TestGoldenRosaryAffirmer:
    def test_affirm(self):
        gra = GoldenRosaryAffirmer()
        r = gra.affirm(0.9)
        assert r > 0.0


class TestVinayaValidator:
    def test_validate(self):
        vv = VinayaValidator()
        r = vv.validate(0.9)
        assert r > 0.0


class TestManjushriCrown:
    def test_bestow(self):
        mc = ManjushriCrown()
        r = mc.bestow(0.9)
        assert r > 0.0


class TestOMNITsongkhapaEngine:
    def test_init(self):
        otk = OMNITsongkhapaEngine()
        assert otk.VERSION == "250.0.0"

    def test_reform(self):
        otk = OMNITsongkhapaEngine()
        r = otk.reform({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "tsongkhapa_score" in r

    def test_run_cycle(self):
        otk = OMNITsongkhapaEngine()
        r = otk.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        otk = OMNITsongkhapaEngine()
        s = otk.get_status()
        assert s["version"] == "250.0.0"

    def test_singleton(self):
        a = get_omni_tsongkhapa_engine()
        b = get_omni_tsongkhapa_engine()
        assert a is b
