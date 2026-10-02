"""OMNI-HUB v196 Tests — ResonanceHarmonizer"""

import pytest
from core.resonance_harmonizer import (
    ResonanceHarmonizer, FrequencyAnalyzer, HarmonicResonator,
    CoupledOscillator, ResonanceDetector, ModeLocker,
    FrequencyProfile, ResonancePeak, ResonanceMode, LockStatus,
    get_resonance_harmonizer
)


class TestFrequencyAnalyzer:
    def test_register(self):
        fa = FrequencyAnalyzer()
        fa.register("m1", 1.0)
        assert "m1" in fa.profiles

    def test_analyze(self):
        fa = FrequencyAnalyzer()
        fa.register("m1")
        r = fa.analyze("m1", [0.5, 0.6, 0.5, 0.6])
        assert "dominant_freq" in r

    def test_spread(self):
        fa = FrequencyAnalyzer()
        fa.register("m1", 1.0)
        fa.register("m2", 2.0)
        assert fa.get_frequency_spread() > 0


class TestHarmonicResonator:
    def test_compute_harmonics(self):
        hr = HarmonicResonator()
        h = hr.compute_harmonics(1.0, 3)
        assert len(h) == 3
        assert h[0] == 1.0

    def test_find_resonance(self):
        hr = HarmonicResonator()
        p = hr.find_resonance(2.0, 1.0, tolerance=0.1)
        assert p is not None

    def test_no_resonance(self):
        hr = HarmonicResonator()
        p = hr.find_resonance(1.7, 1.0, tolerance=0.05)
        assert p is None


class TestCoupledOscillator:
    def test_coupling(self):
        co = CoupledOscillator()
        co.set_coupling("a", "b", 0.5)
        assert co.get_coupling("a", "b") == 0.5

    def test_step(self):
        co = CoupledOscillator()
        co.set_coupling("a", "b", 0.5)
        r = co.step({"a": 0.3, "b": 0.7})
        assert 0 <= r["a"] <= 1

    def test_sync_index(self):
        co = CoupledOscillator()
        idx = co.get_synchronization_index({"a": 0.5, "b": 0.5})
        assert idx > 0.9


class TestResonanceDetector:
    def test_detect(self):
        rd = ResonanceDetector()
        d = rd.detect({"a": 0.9, "b": 0.91})
        assert len(d) > 0

    def test_density(self):
        rd = ResonanceDetector()
        rd.detect({"a": 0.9, "b": 0.91})
        assert rd.get_resonance_density() >= 0


class TestModeLocker:
    def test_lock(self):
        ml = ModeLocker()
        ml.set_target("m1", 1.0)
        ml.update("m1", 1.005)
        assert ml.lock_status["m1"] == LockStatus.LOCKED

    def test_drift(self):
        ml = ModeLocker()
        ml.set_target("m1", 1.0)
        ml.update("m1", 1.5)
        assert ml.lock_status["m1"] == LockStatus.UNLOCKED


class TestResonanceHarmonizer:
    def test_init(self):
        rh = ResonanceHarmonizer()
        assert rh.VERSION == "196.0.0"

    def test_harmonize(self):
        rh = ResonanceHarmonizer()
        r = rh.harmonize({"m1": {"health": 0.9}, "m2": {"health": 0.8}})
        assert "sync_index" in r
        assert "lock_rate" in r

    def test_run_cycle(self):
        rh = ResonanceHarmonizer()
        r = rh.run_cycle({"m1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        rh = ResonanceHarmonizer()
        s = rh.get_status()
        assert s["version"] == "196.0.0"

    def test_singleton(self):
        r1 = get_resonance_harmonizer()
        r2 = get_resonance_harmonizer()
        assert r1 is r2

# Total: 25 tests
