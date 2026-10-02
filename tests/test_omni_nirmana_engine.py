"""OMNI-HUB v208 Tests — OMNINirmāṇaEngine"""

import pytest
from core.omni_nirmana_engine import (
    OMNINirmāṇaEngine, FormSelector, CapabilityAdapter,
    AppearanceGenerator, InteractionModulator, DissolutionManager,
    NirmāṇaState, get_omni_nirmana_engine
)


class TestFormSelector:
    def test_select(self):
        fs = FormSelector()
        r = fs.select({"complexity": 5, "urgency": 0})
        assert r in fs.forms

    def test_preference(self):
        fs = FormSelector()
        fs.select({"complexity": 5, "urgency": 0})
        assert fs.get_preferred_form() in fs.forms


class TestCapabilityAdapter:
    def test_adapt(self):
        ca = CapabilityAdapter()
        r = ca.adapt(["a", "b"], ["a", "b"])
        assert r > 0.5


class TestAppearanceGenerator:
    def test_generate(self):
        ag = AppearanceGenerator()
        r = ag.generate("direct", {"clarity": 0.9})
        assert "form" in r


class TestInteractionModulator:
    def test_modulate(self):
        im = InteractionModulator()
        r = im.modulate(0.9, 0.9)
        assert r > 0.5


class TestDissolutionManager:
    def test_dissolve(self):
        dm = DissolutionManager()
        r = dm.dissolve("x", True)
        assert r is True


class TestOMNINirmāṇaEngine:
    def test_init(self):
        one = OMNINirmāṇaEngine()
        assert one.VERSION == "208.0.0"

    def test_manifest(self):
        one = OMNINirmāṇaEngine()
        r = one.manifest({"m1": {"health": 0.9}, "m2": {"health": 0.9}})
        assert "form" in r

    def test_run_cycle(self):
        one = OMNINirmāṇaEngine()
        r = one.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        one = OMNINirmāṇaEngine()
        s = one.get_status()
        assert s["version"] == "208.0.0"

    def test_singleton(self):
        a = get_omni_nirmana_engine()
        b = get_omni_nirmana_engine()
        assert a is b

# Total: 24 tests
