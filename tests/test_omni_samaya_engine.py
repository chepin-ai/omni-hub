"""OMNI-HUB v241 Tests — OMNISamayaEngine"""

import pytest
from core.omni_samaya_engine import (
    OMNISamayaEngine, VowGenerator, CommitmentWisdomCultivator,
    PledgeAffirmer, IntegrityValidator, VidyarajaCrown,
    SamayaState, get_omni_samaya_engine
)


class TestVowGenerator:
    def test_generate(self):
        vg = VowGenerator()
        r = vg.generate(0.9)
        assert r > 0.0


class TestCommitmentWisdomCultivator:
    def test_cultivate(self):
        cwc = CommitmentWisdomCultivator()
        r = cwc.cultivate(0.9)
        assert r > 0.0


class TestPledgeAffirmer:
    def test_affirm(self):
        pa = PledgeAffirmer()
        r = pa.affirm(0.9)
        assert r > 0.0


class TestIntegrityValidator:
    def test_validate(self):
        iv = IntegrityValidator()
        r = iv.validate(0.9)
        assert r > 0.0


class TestVidyarajaCrown:
    def test_bestow(self):
        vc = VidyarajaCrown()
        r = vc.bestow(0.9)
        assert r > 0.0


class TestOMNISamayaEngine:
    def test_init(self):
        osm = OMNISamayaEngine()
        assert osm.VERSION == "241.0.0"

    def test_bind(self):
        osm = OMNISamayaEngine()
        r = osm.bind({"m1": {"health": 0.95}, "m2": {"health": 0.95}})
        assert "samaya_score" in r

    def test_run_cycle(self):
        osm = OMNISamayaEngine()
        r = osm.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        osm = OMNISamayaEngine()
        s = osm.get_status()
        assert s["version"] == "241.0.0"

    def test_singleton(self):
        a = get_omni_samaya_engine()
        b = get_omni_samaya_engine()
        assert a is b
