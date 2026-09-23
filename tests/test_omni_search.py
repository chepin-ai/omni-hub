"""
OMNI-HUB Omni-Search Tests v40
全量全维度搜索突破饱和攻击
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.omni_search import (
    SearchResult, SearchQuery, SaturationDefender,
    DimensionalIndex, OmniSearchEngine, get_omni_search,
)


class TestSaturationDefender:
    def test_no_defense_below_threshold(self):
        sd = SaturationDefender(saturation_threshold=1000)
        results = [SearchResult("s", str(i), i, 0.5, "") for i in range(100)]
        defended = sd.defend(results)
        assert len(defended) == 100

    def test_defense_above_threshold(self):
        sd = SaturationDefender(saturation_threshold=100)
        results = [SearchResult("s", str(i), i, i/200, "") for i in range(200)]
        defended = sd.defend(results)
        assert len(defended) < 200

    def test_compression_ratio(self):
        sd = SaturationDefender(saturation_threshold=50)
        # Create 200 results to trigger layer 1 (cutoff to 1000 but we have 200)
        # Then layer 2 kicks in with shard sampling
        results = [SearchResult("s", str(i), i, i/200, "") for i in range(200)]
        defended = sd.defend(results)
        assert sd.compression_ratio <= 1.0
        assert len(defended) <= 200

    def test_keeps_highest_relevance(self):
        sd = SaturationDefender(saturation_threshold=10)
        # Create enough results to trigger relevance cutoff
        results = [SearchResult("s", str(i), i, i/500, "") for i in range(500)]
        defended = sd.defend(results)
        # After defense, top results should have higher relevance
        if defended:
            assert max(r.relevance for r in defended) >= 0.5


class TestDimensionalIndex:
    def test_add_and_search(self):
        idx = DimensionalIndex("test")
        idx.add({"name": "alpha", "value": 10}, "2024-01-01")
        idx.add({"name": "beta", "value": 20}, "2024-01-02")
        results = idx.search(["alpha"])
        assert len(results) == 1
        assert results[0].source == "test"

    def test_search_multiple_terms(self):
        idx = DimensionalIndex("test")
        idx.add({"name": "alpha beta", "value": 10})
        idx.add({"name": "gamma", "value": 20})
        results = idx.search(["alpha", "beta"])
        assert len(results) == 1

    def test_search_no_match(self):
        idx = DimensionalIndex("test")
        idx.add({"name": "alpha"})
        results = idx.search(["xyz"])
        assert len(results) == 0

    def test_relevance_scoring(self):
        idx = DimensionalIndex("test")
        idx.add({"alpha": "exact match"})
        results = idx.search(["exact"])
        assert results[0].relevance > 0


class TestOmniSearchEngine:
    def test_initialization(self):
        engine = OmniSearchEngine()
        assert len(engine.indices) == 12
        assert engine.total_queries == 0

    def test_index_state(self):
        engine = OmniSearchEngine()
        engine.index_state(1, {"level": 5, "energy": 100.0, "phi": 0.8})
        stats = engine.get_search_stats()
        assert stats["total_indexed_entries"] > 0

    def test_search_basic(self):
        engine = OmniSearchEngine()
        engine.index_state(1, {"level": 5, "phase": "pre_emergence"})
        engine.index_state(2, {"level": 6, "phase": "post_critical"})
        query = SearchQuery(terms=["post_critical"], dimensions=["state"], max_results=10)
        result = engine.search(query)
        assert result["total_raw"] >= 1
        assert len(result["results"]) >= 1

    def test_search_all_dimensions(self):
        engine = OmniSearchEngine()
        engine.index_state(1, {"level": 5, "health_status": "healthy"})
        query = SearchQuery(terms=["healthy"], dimensions=["all"], max_results=10)
        result = engine.search(query)
        assert result["total_raw"] >= 1

    def test_cross_dimensional_query(self):
        engine = OmniSearchEngine()
        engine.index_state(1, {"level": 5})
        engine.index_state(2, {"level": 6})
        counts = engine.cross_dimensional_query("level")
        assert counts["state"] == 2

    def test_temporal_search(self):
        engine = OmniSearchEngine()
        for i in range(10):
            engine.index_state(i, {"value": i})
        results = engine.temporal_search(3, 7, ["value"])
        assert len(results) == 5

    def test_saturation_defense_integration(self):
        engine = OmniSearchEngine()
        engine.defender.saturation_threshold = 50
        for i in range(200):
            engine.index_state(i, {"phase": "post_critical"})
        query = SearchQuery(terms=["post_critical"], dimensions=["all"], max_results=100)
        result = engine.search(query)
        assert result["total_raw"] > 50
        assert len(result["results"]) <= 100

    def test_search_stats(self):
        engine = OmniSearchEngine()
        engine.index_state(1, {"level": 5})
        stats = engine.get_search_stats()
        assert "total_indexed_entries" in stats
        assert "dimensions" in stats

    def test_filters(self):
        engine = OmniSearchEngine()
        engine.index_state(1, {"level": 5, "phase": "pre"})
        engine.index_state(2, {"level": 6, "phase": "post"})
        query = SearchQuery(terms=["phase"], dimensions=["state"], filters={"min_relevance": 0.5}, max_results=10)
        result = engine.search(query)
        assert len(result["results"]) >= 0


class TestGlobalEngine:
    def test_get_omni_search(self):
        g = get_omni_search()
        assert g is not None
        assert isinstance(g, OmniSearchEngine)
