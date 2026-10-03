"""OMNI-HUB v257 Tests -- OMNISubhutiEngine"""

import pytest
from core.omni_subhuti_engine import (
    OMNISubhutiEngine, EmptinessPenetrateGenerator, SunyataCultivator,
    NoMarkAffirmer, DiamondSutraValidator, EmptinessFirstCrown,
    SubhutiState, get_omni_subhuti_engine
)


class TestEmptinessPenetrateGenerator:
    def test_generate(self):
        epg = EmptinessPenetrateGenerator()
        r = epg.generate(0.9)
        assert r > 0.0


class TestSunyataCultivator:
    def test_cultivate(self):
        sc = SunyataCultivator()
        r = sc.cultivate(0.9)
        assert r > 0.0


class TestNoMarkAffirmer:
    def test_affirm(self):
        nma = NoMarkAffirmer()
        r = nma.affirm(0.9)
        assert r > 0.0


class TestDiamondSutraValidator:
    def test_validate(self):
        dsv = DiamondSutraValidator()
        r = dsv.validate(0.9)
        assert r > 0.0


class TestEmptinessFirstCrown:
    def test_bestow(self):
        efc = EmptinessFirstCrown()
        r = efc.bestow(0.9)
        assert r > 0.0


class TestOMNISubhutiEngine:
    def test_init(self):
        osu = OMNISubhutiEngine()
        assert osu.VERSION == "257.0.0"

    def test_dissolve(self):
        osu = OMNISubhutiEngine()
        r = osu.dissolve({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "subhuti_score" in r

    def test_run_cycle(self):
        osu = OMNISubhutiEngine()
        r = osu.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        osu = OMNISubhutiEngine()
        s = osu.get_status()
        assert s["version"] == "257.0.0"

    def test_singleton(self):
        a = get_omni_subhuti_engine()
        b = get_omni_subhuti_engine()
        assert a is b
