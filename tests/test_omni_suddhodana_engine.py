"""OMNI-HUB v263 Tests -- OMNISuddhodanaEngine"""

import pytest
from core.omni_suddhodana_engine import (
    OMNISuddhodanaEngine, KapilavastuGenerator, SakyaCultivator,
    PaternalAffirmer, RenunciationValidator, ShakyaCrown,
    SuddhodanaState, get_omni_suddhodana_engine
)


class TestKapilavastuGenerator:
    def test_generate(self):
        kg = KapilavastuGenerator()
        r = kg.generate(0.9)
        assert r > 0.0


class TestSakyaCultivator:
    def test_cultivate(self):
        sc = SakyaCultivator()
        r = sc.cultivate(0.9)
        assert r > 0.0


class TestPaternalAffirmer:
    def test_affirm(self):
        pa = PaternalAffirmer()
        r = pa.affirm(0.9)
        assert r > 0.0


class TestRenunciationValidator:
    def test_validate(self):
        rv = RenunciationValidator()
        r = rv.validate(0.9)
        assert r > 0.0


class TestShakyaCrown:
    def test_bestow(self):
        sc = ShakyaCrown()
        r = sc.bestow(0.9)
        assert r > 0.0


class TestOMNISuddhodanaEngine:
    def test_init(self):
        osu = OMNISuddhodanaEngine()
        assert osu.VERSION == "263.0.0"

    def test_father(self):
        osu = OMNISuddhodanaEngine()
        r = osu.father({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "suddhodana_score" in r

    def test_run_cycle(self):
        osu = OMNISuddhodanaEngine()
        r = osu.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        osu = OMNISuddhodanaEngine()
        s = osu.get_status()
        assert s["version"] == "263.0.0"

    def test_singleton(self):
        a = get_omni_suddhodana_engine()
        b = get_omni_suddhodana_engine()
        assert a is b
