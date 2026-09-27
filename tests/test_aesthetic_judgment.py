"""
OMNI-HUB Aesthetic Judgment Tests v93
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.aesthetic_judgment import (
    AestheticJudgment, get_aesthetic_judgment,
)


class TestAestheticJudgment:
    def test_initialization(self):
        aj = AestheticJudgment()
        assert len(aj.beauty_scores) == 0

    def test_evaluate_harmony(self):
        aj = AestheticJudgment()
        state = {"phi": 0.618, "line_coherence": 0.9, "energy": 2500}
        h = aj.evaluate_harmony(state)
        assert 0 <= h <= 1
        assert h > 0.5

    def test_evaluate_proportion(self):
        aj = AestheticJudgment()
        state = {"level": 5, "energy": 2500}
        p = aj.evaluate_proportion(state)
        assert 0 <= p <= 1

    def test_evaluate_elegance(self):
        aj = AestheticJudgment()
        state = {"risk_analyzer": {"risks_found": 0}, "trust_engine": {"betrayals": 0}}
        e = aj.evaluate_elegance(state)
        assert e == 1.0

    def test_judge_beautiful(self):
        aj = AestheticJudgment()
        state = {"phi": 0.618, "line_coherence": 0.9, "energy": 2500, "level": 5}
        result = aj.judge(state)
        assert "beauty" in result
        assert "label" in result
        assert result["beauty"] > 0

    def test_judge_discordant(self):
        aj = AestheticJudgment()
        state = {"phi": 0.1, "line_coherence": 0.1, "energy": 100, "level": 5}
        result = aj.judge(state)
        assert result["label"] in [" plain", " discordant"]

    def test_get_status(self):
        aj = AestheticJudgment()
        aj.judge({"phi": 0.5, "line_coherence": 0.5, "energy": 1000, "level": 5})
        status = aj.get_status()
        assert status["judgments"] == 1
        assert "average_beauty" in status


class TestGlobalEngine:
    def test_get_aesthetic_judgment(self):
        g = get_aesthetic_judgment()
        assert g is not None
        assert isinstance(g, AestheticJudgment)
