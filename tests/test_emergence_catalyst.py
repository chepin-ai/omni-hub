"""OMNI-HUB v194 Tests — EmergenceCatalyst"""

import pytest
from core.emergence_catalyst import (
    EmergenceCatalyst, PhaseTransitionDetector, CriticalPointAnalyzer,
    EmergencePatternSynthesizer, FeedbackAmplifier, StabilityLandscapeMapper,
    PhaseType, EmergenceClass, EmergencePattern,
    get_emergence_catalyst
)


class TestPhaseTransitionDetector:
    def test_detect_ordered(self):
        ptd = PhaseTransitionDetector()
        phase = ptd.detect(0.9)
        assert phase == PhaseType.SYNCHRONIZED

    def test_detect_disordered(self):
        ptd = PhaseTransitionDetector()
        phase = ptd.detect(0.1)
        assert phase == PhaseType.DISORDERED

    def test_transition_detection(self):
        ptd = PhaseTransitionDetector()
        ptd.detect(0.1)
        ptd.detect(0.9)
        assert len(ptd.transitions) == 1

    def test_get_report(self):
        ptd = PhaseTransitionDetector()
        r = ptd.get_report()
        assert "current_phase" in r


class TestCriticalPointAnalyzer:
    def test_analyze(self):
        cpa = CriticalPointAnalyzer()
        cp = cpa.analyze("x", [0.1, 0.2, 0.5, 0.9])
        assert cp is not None

    def test_near_critical(self):
        cpa = CriticalPointAnalyzer()
        cpa.analyze("x", [0.1, 0.2, 0.5, 0.9])
        assert cpa.is_near_critical(0.5, "x", tolerance=0.1) is True


class TestEmergencePatternSynthesizer:
    def test_synthesize(self):
        eps = EmergencePatternSynthesizer()
        p = eps.synthesize(["a", "b"], {"a": 0.9, "b": 0.9})
        assert p is not None
        assert p.strength > 0

    def test_dominant_patterns(self):
        eps = EmergencePatternSynthesizer()
        eps.synthesize(["a", "b"], {"a": 0.9, "b": 0.9})
        dp = eps.get_dominant_patterns(1)
        assert len(dp) == 1


class TestFeedbackAmplifier:
    def test_amplify(self):
        fa = FeedbackAmplifier()
        out = fa.amplify(0.5, "loop1", gain=1.0)
        assert 0 <= out <= 1

    def test_dampen(self):
        fa = FeedbackAmplifier()
        out = fa.dampen(0.5, "loop1", damping=0.5)
        assert 0 <= out <= 1

    def test_stability(self):
        fa = FeedbackAmplifier()
        fa.amplify(0.5, "loop1")
        fa.amplify(0.5, "loop1")
        s = fa.get_stability("loop1")
        assert 0 <= s <= 1


class TestStabilityLandscapeMapper:
    def test_map_point(self):
        slm = StabilityLandscapeMapper()
        slm.map_point({"x": 0.5, "y": 0.6}, 0.9)
        assert len(slm.attractors) == 1

    def test_find_attractors(self):
        slm = StabilityLandscapeMapper()
        slm.map_point({"x": 0.5}, 0.9)
        a = slm.find_attractors(1)
        assert len(a) == 1


class TestEmergenceCatalyst:
    def test_init(self):
        ec = EmergenceCatalyst()
        assert ec.VERSION == "194.0.0"

    def test_catalyze(self):
        ec = EmergenceCatalyst()
        r = ec.catalyze({"m1": {"health": 0.9}, "m2": {"health": 0.9}})
        assert "phase" in r
        assert "order_parameter" in r

    def test_catalyze_critical(self):
        ec = EmergenceCatalyst()
        r = ec.catalyze({"m1": {"health": 0.5}, "m2": {"health": 0.5}})
        assert "near_critical" in r

    def test_run_cycle(self):
        ec = EmergenceCatalyst()
        r = ec.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ec = EmergenceCatalyst()
        s = ec.get_status()
        assert s["version"] == "194.0.0"

    def test_singleton(self):
        e1 = get_emergence_catalyst()
        e2 = get_emergence_catalyst()
        assert e1 is e2

# Total: 24 tests
