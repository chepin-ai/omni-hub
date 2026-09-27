"""
OMNI-HUB Antifragile Growth Tests v106
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.antifragile_growth import (
    AntifragileGrowth, get_antifragile_growth,
)


class TestAntifragileGrowth:
    def test_initialization(self):
        ag = AntifragileGrowth()
        assert ag.antifragility_index == 0.5

    def test_measure_shock(self):
        ag = AntifragileGrowth()
        prev = {"phi": 0.5, "level": 5, "energy": 1000}
        curr = {"phi": 0.8, "level": 8, "energy": 2000}
        shock = ag.measure_shock(prev, curr)
        assert shock > 0

    def test_assess_antifragility(self):
        ag = AntifragileGrowth()
        state = {
            "self_healing": {"repairs": 5},
            "transcendence": {"potential": 0.8},
            "trust_engine": {"global_trust": 0.9},
        }
        for i in range(30):
            state[f"mod_{i}"] = {"status": "ok"}
        af = ag.assess_antifragility(state)
        assert 0 <= af <= 1
        assert af > 0.3

    def test_grow_from_shock(self):
        ag = AntifragileGrowth()
        state = {"transcendence": {"potential": 0.8}, "trust_engine": {"global_trust": 0.9}}
        result = ag.grow_from_shock(0.8, state)
        assert "shock" in result
        assert "growth" in result
        assert "index" in result
        assert result["growth"] > 0

    def test_grow_from_small_shock(self):
        ag = AntifragileGrowth()
        state = {"transcendence": {"potential": 0.5}, "trust_engine": {"global_trust": 0.5}}
        result = ag.grow_from_shock(0.2, state)
        assert result["growth"] >= 0

    def test_get_status(self):
        ag = AntifragileGrowth()
        state = {"transcendence": {"potential": 0.8}, "trust_engine": {"global_trust": 0.9}}
        ag.grow_from_shock(0.5, state)
        status = ag.get_status()
        assert status["shocks_survived"] == 1
        assert status["total_growth"] > 0


class TestGlobalEngine:
    def test_get_antifragile_growth(self):
        g = get_antifragile_growth()
        assert g is not None
        assert isinstance(g, AntifragileGrowth)
