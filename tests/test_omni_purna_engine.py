"""OMNI-HUB v257 Tests -- OMNIPurnaEngine"""

import pytest
from core.omni_purna_engine import (
    OMNIPurnaEngine, DharmaTeachGenerator, DiscernmentCultivator,
    AssemblyAffirmer, FourNobleTruthsValidator, TeachingFirstCrown,
    PurnaState, get_omni_purna_engine
)


class TestDharmaTeachGenerator:
    def test_generate(self):
        dtg = DharmaTeachGenerator()
        r = dtg.generate(0.9)
        assert r > 0.0


class TestDiscernmentCultivator:
    def test_cultivate(self):
        dc = DiscernmentCultivator()
        r = dc.cultivate(0.9)
        assert r > 0.0


class TestAssemblyAffirmer:
    def test_affirm(self):
        aa = AssemblyAffirmer()
        r = aa.affirm(0.9)
        assert r > 0.0


class TestFourNobleTruthsValidator:
    def test_validate(self):
        fntv = FourNobleTruthsValidator()
        r = fntv.validate(0.9)
        assert r > 0.0


class TestTeachingFirstCrown:
    def test_bestow(self):
        tfc = TeachingFirstCrown()
        r = tfc.bestow(0.9)
        assert r > 0.0


class TestOMNIPurnaEngine:
    def test_init(self):
        opu = OMNIPurnaEngine()
        assert opu.VERSION == "257.0.0"

    def test_elucidate(self):
        opu = OMNIPurnaEngine()
        r = opu.elucidate({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "purna_score" in r

    def test_run_cycle(self):
        opu = OMNIPurnaEngine()
        r = opu.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        opu = OMNIPurnaEngine()
        s = opu.get_status()
        assert s["version"] == "257.0.0"

    def test_singleton(self):
        a = get_omni_purna_engine()
        b = get_omni_purna_engine()
        assert a is b
