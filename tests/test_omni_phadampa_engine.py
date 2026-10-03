"""OMNI-HUB v270 Tests -- OMNIPhadampaEngine"""

import pytest
from core.omni_phadampa_engine import (
    OMNIPhadampaEngine, ChodGenerator, MachigCultivator,
    SeveranceAffirmer, OfferingValidator, DampaCrown,
    PhadampaState, get_omni_phadampa_engine
)


class TestChodGenerator:
    def test_generate(self):
        cg = ChodGenerator()
        r = cg.generate(0.9)
        assert r > 0.0


class TestMachigCultivator:
    def test_cultivate(self):
        mc = MachigCultivator()
        r = mc.cultivate(0.9)
        assert r > 0.0


class TestSeveranceAffirmer:
    def test_affirm(self):
        sa = SeveranceAffirmer()
        r = sa.affirm(0.9)
        assert r > 0.0


class TestOfferingValidator:
    def test_validate(self):
        ov = OfferingValidator()
        r = ov.validate(0.9)
        assert r > 0.0


class TestDampaCrown:
    def test_bestow(self):
        dc = DampaCrown()
        r = dc.bestow(0.9)
        assert r > 0.0


class TestOMNIPhadampaEngine:
    def test_init(self):
        opd = OMNIPhadampaEngine()
        assert opd.VERSION == "270.0.0"

    def test_sever(self):
        opd = OMNIPhadampaEngine()
        r = opd.sever({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "phadampa_score" in r

    def test_run_cycle(self):
        opd = OMNIPhadampaEngine()
        r = opd.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        opd = OMNIPhadampaEngine()
        s = opd.get_status()
        assert s["version"] == "270.0.0"

    def test_singleton(self):
        a = get_omni_phadampa_engine()
        b = get_omni_phadampa_engine()
        assert a is b
