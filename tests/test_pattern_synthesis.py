"""
OMNI-HUB Pattern Synthesis Tests v50
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.pattern_synthesis import (
    Pattern, CycleDetector, TrendAnalyzer, AnomalyDetector, PatternSynthesisEngine, get_pattern_synthesis,
)


class TestCycleDetector:
    def test_detect_cycle(self):
        cd = CycleDetector()
        series = [1, 2, 3] * 20  # period 3, 60 data points
        pattern = cd.detect(series, max_period=10)
        assert pattern is not None
        assert pattern.pattern_type == "cycle"
        assert pattern.confidence > 0.5

    def test_no_cycle(self):
        cd = CycleDetector()
        series = [i for i in range(20)]
        pattern = cd.detect(series, max_period=10)
        assert pattern is None


class TestTrendAnalyzer:
    def test_detect_increasing_trend(self):
        ta = TrendAnalyzer()
        series = [i * 2 for i in range(20)]
        pattern = ta.detect(series)
        assert pattern is not None
        assert pattern.pattern_type == "trend"
        assert "increasing" in pattern.description

    def test_detect_decreasing_trend(self):
        ta = TrendAnalyzer()
        series = [40 - i * 2 for i in range(20)]
        pattern = ta.detect(series)
        assert pattern is not None
        assert "decreasing" in pattern.description

    def test_no_trend(self):
        ta = TrendAnalyzer()
        series = [5 + (i % 3) for i in range(20)]
        pattern = ta.detect(series)
        assert pattern is None


class TestAnomalyDetector:
    def test_detect_anomaly(self):
        ad = AnomalyDetector()
        series = [10.0] * 20 + [100.0] + [10.0] * 20
        patterns = ad.detect(series)
        assert len(patterns) == 1
        assert patterns[0].pattern_type == "anomaly"

    def test_no_anomaly(self):
        ad = AnomalyDetector()
        series = [10.0 + i * 0.1 for i in range(20)]
        patterns = ad.detect(series)
        assert len(patterns) == 0


class TestPatternSynthesisEngine:
    def test_initialization(self):
        ps = PatternSynthesisEngine()
        assert len(ps.discovered_patterns) == 0

    def test_synthesize(self):
        ps = PatternSynthesisEngine()
        history = []
        for i in range(30):
            history.append({
                "level": i * 0.5,
                "energy": 100 + i * 10,
                "phi": 0.5 + (i % 5) * 0.1,
                "line_coherence": 0.5,
            })
        patterns = ps.synthesize(history)
        assert len(patterns) > 0
        assert ps.synthesis_count == 1

    def test_get_status(self):
        ps = PatternSynthesisEngine()
        status = ps.get_status()
        assert "patterns" in status
        assert "by_type" in status


class TestGlobalEngine:
    def test_get_pattern_synthesis(self):
        g = get_pattern_synthesis()
        assert g is not None
        assert isinstance(g, PatternSynthesisEngine)
