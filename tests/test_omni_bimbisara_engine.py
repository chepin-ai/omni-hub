"""OMNI-HUB v261 Tests -- OMNIBimbisaraEngine"""

import pytest
from core.omni_bimbisara_engine import (
    OMNIBimbisaraEngine, BambooGroveGenerator, KingdomCultivator,
    ProtectionAffirmer, FirstCouncilValidator, MagadhaCrown,
    BimbisaraState, get_omni_bimbisara_engine
)


class TestBambooGroveGenerator:
    def test_generate(self):
        bgg = BambooGroveGenerator()
        r = bgg.generate(0.9)
        assert r > 0.0


class TestKingdomCultivator:
    def test_cultivate(self):
        kc = KingdomCultivator()
        r = kc.cultivate(0.9)
        assert r > 0.0


class TestProtectionAffirmer:
    def test_affirm(self):
        pa = ProtectionAffirmer()
        r = pa.affirm(0.9)
        assert r > 0.0


class TestFirstCouncilValidator:
    def test_validate(self):
        fcv = FirstCouncilValidator()
        r = fcv.validate(0.9)
        assert r > 0.0


class TestMagadhaCrown:
    def test_bestow(self):
        mc = MagadhaCrown()
        r = mc.bestow(0.9)
        assert r > 0.0


class TestOMNIBimbisaraEngine:
    def test_init(self):
        obi = OMNIBimbisaraEngine()
        assert obi.VERSION == "261.0.0"

    def test_protect(self):
        obi = OMNIBimbisaraEngine()
        r = obi.protect({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "bimbisara_score" in r

    def test_run_cycle(self):
        obi = OMNIBimbisaraEngine()
        r = obi.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        obi = OMNIBimbisaraEngine()
        s = obi.get_status()
        assert s["version"] == "261.0.0"

    def test_singleton(self):
        a = get_omni_bimbisara_engine()
        b = get_omni_bimbisara_engine()
        assert a is b
