"""OMNI-HUB v254 Tests -- OMNIKsitigarbhaEngine"""

import pytest
from core.omni_ksitigarbha_engine import (
    OMNIKsitigarbhaEngine, GreatVowGenerator, EarthCultivator,
    KhakkharaAffirmer, HellGateValidator, MountJiuhuaCrown,
    KsitigarbhaState, get_omni_ksitigarbha_engine
)


class TestGreatVowGenerator:
    def test_generate(self):
        gvg = GreatVowGenerator()
        r = gvg.generate(0.9)
        assert r > 0.0


class TestEarthCultivator:
    def test_cultivate(self):
        ec = EarthCultivator()
        r = ec.cultivate(0.9)
        assert r > 0.0


class TestKhakkharaAffirmer:
    def test_affirm(self):
        ka = KhakkharaAffirmer()
        r = ka.affirm(0.9)
        assert r > 0.0


class TestHellGateValidator:
    def test_validate(self):
        hgv = HellGateValidator()
        r = hgv.validate(0.9)
        assert r > 0.0


class TestMountJiuhuaCrown:
    def test_bestow(self):
        mjc = MountJiuhuaCrown()
        r = mjc.bestow(0.9)
        assert r > 0.0


class TestOMNIKsitigarbhaEngine:
    def test_init(self):
        okg = OMNIKsitigarbhaEngine()
        assert okg.VERSION == "254.0.0"

    def test_liberate(self):
        okg = OMNIKsitigarbhaEngine()
        r = okg.liberate({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "ksitigarbha_score" in r

    def test_run_cycle(self):
        okg = OMNIKsitigarbhaEngine()
        r = okg.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        okg = OMNIKsitigarbhaEngine()
        s = okg.get_status()
        assert s["version"] == "254.0.0"

    def test_singleton(self):
        a = get_omni_ksitigarbha_engine()
        b = get_omni_ksitigarbha_engine()
        assert a is b
