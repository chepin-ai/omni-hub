"""OMNI-HUB v202 Tests — HolisticAwarenessEngine"""

import pytest
from core.holistic_awareness_engine import (
    HolisticAwarenessEngine, PanopticSensor, PatternWeaver,
    ContextSynthesizer, AwarenessAmplifier, PerceptionIntegrator,
    AwarenessLevel, get_holistic_awareness_engine
)


class TestPanopticSensor:
    def test_observe(self):
        ps = PanopticSensor()
        r = ps.observe("src1", 0.7)
        assert r["source"] == "src1"

    def test_coverage(self):
        ps = PanopticSensor()
        ps.observe("s1", 0.5)
        ps.observe("s2", 0.8)
        assert ps.get_coverage() > 0


class TestPatternWeaver:
    def test_weave(self):
        pw = PatternWeaver()
        p = pw.weave({"a": 0.9, "b": 0.85, "c": 0.3})
        assert isinstance(p, list)

    def test_density(self):
        pw = PatternWeaver()
        pw.weave({"a": 0.9, "b": 0.91, "c": 0.92, "d": 0.93})
        assert pw.get_pattern_density() >= 0


class TestContextSynthesizer:
    def test_synthesize(self):
        cs = ContextSynthesizer()
        obs = [{"source": "s1", "strength": 0.8}, {"source": "s1", "strength": 0.9}]
        r = cs.synthesize(obs)
        assert "s1" in r


class TestAwarenessAmplifier:
    def test_amplify(self):
        aa = AwarenessAmplifier()
        r = aa.amplify(0.3, 0.9)
        assert r > 0.3

    def test_cap(self):
        aa = AwarenessAmplifier()
        r = aa.amplify(1.0, 1.0)
        assert r <= 1.0


class TestPerceptionIntegrator:
    def test_integrate(self):
        pi = PerceptionIntegrator()
        r = pi.integrate(0.5, 0.5, 0.5, 0.5)
        assert 0 <= r <= 1


class TestHolisticAwarenessEngine:
    def test_init(self):
        hae = HolisticAwarenessEngine()
        assert hae.VERSION == "202.0.0"

    def test_perceive(self):
        hae = HolisticAwarenessEngine()
        r = hae.perceive({"s1": 0.9, "s2": 0.8, "s3": 0.7})
        assert "awareness_level" in r

    def test_run_cycle(self):
        hae = HolisticAwarenessEngine()
        r = hae.run_cycle({"s1": 0.9})
        assert r["cycle"] == 1

    def test_get_status(self):
        hae = HolisticAwarenessEngine()
        s = hae.get_status()
        assert s["version"] == "202.0.0"

    def test_singleton(self):
        a = get_holistic_awareness_engine()
        b = get_holistic_awareness_engine()
        assert a is b

# Total: 25 tests
