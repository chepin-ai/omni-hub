"""OMNI-HUB v243 Tests — OMNILamrimEngine"""

import pytest
from core.omni_lamrim_engine import (
    OMNILamrimEngine, StagesGenerator, GraduatedWisdomCultivator,
    ThreePrinciplesAffirmer, TwoTruthsValidator, TsongkhapaCrown,
    LamrimState, get_omni_lamrim_engine
)


class TestStagesGenerator:
    def test_generate(self):
        sg = StagesGenerator()
        r = sg.generate(0.9)
        assert r > 0.0


class TestGraduatedWisdomCultivator:
    def test_cultivate(self):
        gwc = GraduatedWisdomCultivator()
        r = gwc.cultivate(0.9)
        assert r > 0.0


class TestThreePrinciplesAffirmer:
    def test_affirm(self):
        tpa = ThreePrinciplesAffirmer()
        r = tpa.affirm(0.9)
        assert r > 0.0


class TestTwoTruthsValidator:
    def test_validate(self):
        ttv = TwoTruthsValidator()
        r = ttv.validate(0.9)
        assert r > 0.0


class TestTsongkhapaCrown:
    def test_bestow(self):
        tc = TsongkhapaCrown()
        r = tc.bestow(0.9)
        assert r > 0.0


class TestOMNILamrimEngine:
    def test_init(self):
        olr = OMNILamrimEngine()
        assert olr.VERSION == "243.0.0"

    def test_progress(self):
        olr = OMNILamrimEngine()
        r = olr.progress({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "lamrim_score" in r

    def test_run_cycle(self):
        olr = OMNILamrimEngine()
        r = olr.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        olr = OMNILamrimEngine()
        s = olr.get_status()
        assert s["version"] == "243.0.0"

    def test_singleton(self):
        a = get_omni_lamrim_engine()
        b = get_omni_lamrim_engine()
        assert a is b
