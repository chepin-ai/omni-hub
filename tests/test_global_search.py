"""
Tests for OMNI-HUB Module v141: Global Search Engine
"""

import pytest
from typing import Any, Dict, List

from core.global_search import (
    GlobalSearchEngine,
    get_global_search_engine,
    _module,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fresh_engine() -> GlobalSearchEngine:
    """Provide a fresh search engine instance."""
    return GlobalSearchEngine()


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the global singleton before each test."""
    global _module
    _module = None


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
class TestInitialization:
    def test_init_creates_empty_history(self, fresh_engine: GlobalSearchEngine) -> None:
        assert fresh_engine.search_history == []

    def test_init_creates_empty_result_index(self, fresh_engine: GlobalSearchEngine) -> None:
        assert fresh_engine.result_index == {}

    def test_init_creates_dimension_stats(self, fresh_engine: GlobalSearchEngine) -> None:
        expected_dims = [
            "web", "image", "academic", "code", "financial", "legal", "news"
        ]
        assert list(fresh_engine.dimension_stats.keys()) == expected_dims
        for dim in expected_dims:
            assert fresh_engine.dimension_stats[dim]["count"] == 0
            assert fresh_engine.dimension_stats[dim]["total_relevance"] == 0.0
            assert fresh_engine.dimension_stats[dim]["last_query"] is None

    def test_dimensions_constant(self, fresh_engine: GlobalSearchEngine) -> None:
        assert len(fresh_engine.DIMENSIONS) == 7
        assert "web" in fresh_engine.DIMENSIONS
        assert "financial" in fresh_engine.DIMENSIONS


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_returns_same_instance(self) -> None:
        a = get_global_search_engine()
        b = get_global_search_engine()
        assert a is b

    def test_singleton_is_global_search_engine(self) -> None:
        engine = get_global_search_engine()
        assert isinstance(engine, GlobalSearchEngine)


# ---------------------------------------------------------------------------
# Single-dimension search
# ---------------------------------------------------------------------------
class TestSingleSearch:
    def test_search_returns_results(self, fresh_engine: GlobalSearchEngine) -> None:
        result = fresh_engine.search("web", "artificial intelligence")
        assert result["dimension"] == "web"
        assert result["query"] == "artificial intelligence"
        assert result["count"] >= 3
        assert result["count"] <= 5
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_search_result_structure(self, fresh_engine: GlobalSearchEngine) -> None:
        result = fresh_engine.search("academic", "deep learning")
        first = result["results"][0]
        assert "id" in first
        assert "title" in first
        assert "source" in first
        assert "relevance" in first
        assert "confidence" in first
        assert "timestamp" in first
        assert "rank" in first
        assert 0.0 <= first["relevance"] <= 1.0
        assert 0.0 <= first["confidence"] <= 1.0

    def test_search_updates_history(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("code", "python decorators")
        assert len(fresh_engine.search_history) == 1
        record = fresh_engine.search_history[0]
        assert record["query"] == "python decorators"
        assert record["dimension"] == "code"

    def test_search_updates_stats(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("news", "stock market")
        assert fresh_engine.dimension_stats["news"]["count"] == 1
        assert fresh_engine.dimension_stats["news"]["last_query"] == "stock market"
        assert fresh_engine.dimension_stats["news"]["total_relevance"] > 0

    def test_search_invalid_dimension_raises(self, fresh_engine: GlobalSearchEngine) -> None:
        with pytest.raises(ValueError) as exc_info:
            fresh_engine.search("music", "beatles")
        assert "Unsupported dimension" in str(exc_info.value)

    def test_search_indexes_results(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("financial", "bitcoin")
        assert len(fresh_engine.result_index) >= 3
        for rid, r in fresh_engine.result_index.items():
            assert r["query"] == "bitcoin"


# ---------------------------------------------------------------------------
# Saturation search
# ---------------------------------------------------------------------------
class TestSaturationSearch:
    def test_saturation_search_covers_all_dimensions(self, fresh_engine: GlobalSearchEngine) -> None:
        report = fresh_engine.saturation_search("machine learning")
        assert report["dimensions_covered"] == 7
        assert len(report["dimension_reports"]) == 7
        for dim in fresh_engine.DIMENSIONS:
            assert dim in report["dimension_reports"]

    def test_saturation_search_returns_ranked_results(self, fresh_engine: GlobalSearchEngine) -> None:
        report = fresh_engine.saturation_search("neural networks")
        assert report["total_raw"] >= 7 * 3  # at least 3 per dimension
        assert report["total_unique"] <= report["total_raw"]
        ranked = report["ranked_results"]
        assert len(ranked) > 0
        # Verify descending composite_score order
        for i in range(len(ranked) - 1):
            assert ranked[i]["composite_score"] >= ranked[i + 1]["composite_score"]

    def test_saturation_search_has_top_result(self, fresh_engine: GlobalSearchEngine) -> None:
        report = fresh_engine.saturation_search("blockchain")
        assert report["top_result"] is not None
        assert "id" in report["top_result"]
        assert "composite_score" in report["top_result"]

    def test_saturation_search_creates_edges(self, fresh_engine: GlobalSearchEngine) -> None:
        report = fresh_engine.saturation_search("quantum computing")
        assert "intelligence_edges" in report
        assert isinstance(report["intelligence_edges"], list)

    def test_saturation_search_increments_history(self, fresh_engine: GlobalSearchEngine) -> None:
        before = len(fresh_engine.search_history)
        fresh_engine.saturation_search("climate change")
        after = len(fresh_engine.search_history)
        assert after == before + 7  # one search per dimension


# ---------------------------------------------------------------------------
# Intelligence graph
# ---------------------------------------------------------------------------
class TestIntelligenceGraph:
    def test_empty_graph(self, fresh_engine: GlobalSearchEngine) -> None:
        graph = fresh_engine.get_intelligence_graph()
        assert graph["node_count"] == 0
        assert graph["edge_count"] == 0
        assert graph["nodes"] == []
        assert graph["edges"] == []

    def test_graph_after_search(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("web", "python")
        graph = fresh_engine.get_intelligence_graph()
        assert graph["node_count"] >= 3
        assert graph["node_count"] <= 5
        assert graph["edge_count"] > 0
        assert "python" in graph["queries"]
        assert "web" in graph["dimensions"]

    def test_graph_nodes_have_required_fields(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("legal", "GDPR")
        graph = fresh_engine.get_intelligence_graph()
        for node in graph["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "dimension" in node
            assert "query" in node
            assert "relevance" in node
            assert "confidence" in node

    def test_graph_edges_have_required_fields(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("image", "cat photos")
        graph = fresh_engine.get_intelligence_graph()
        for edge in graph["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "weight" in edge
            assert "relation" in edge

    def test_graph_after_saturation(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.saturation_search("AI ethics")
        graph = fresh_engine.get_intelligence_graph()
        assert graph["node_count"] > 0
        assert len(graph["queries"]) >= 1
        # Should contain multiple dimensions
        assert len(graph["dimensions"]) >= 2


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
class TestStatus:
    def test_status_initial(self, fresh_engine: GlobalSearchEngine) -> None:
        status = fresh_engine.get_status()
        assert status["search_count"] == 0
        assert status["total_results_indexed"] == 0
        assert status["dimensions_covered"] == []
        assert status["dimensions_total"] == 7
        assert status["top_results"] == []

    def test_status_after_searches(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("web", "docker")
        fresh_engine.search("code", "docker")
        fresh_engine.search("news", "docker")
        status = fresh_engine.get_status()
        assert status["search_count"] == 3
        assert status["total_results_indexed"] >= 9
        assert set(status["dimensions_covered"]) == {"web", "code", "news"}
        assert len(status["top_results"]) <= 5
        for tr in status["top_results"]:
            assert "id" in tr
            assert "title" in tr
            assert "dimension" in tr
            assert "relevance" in tr
            assert "confidence" in tr

    def test_status_dimension_stats_present(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("financial", "inflation")
        status = fresh_engine.get_status()
        assert "dimension_stats" in status
        assert status["dimension_stats"]["financial"]["count"] == 1


# ---------------------------------------------------------------------------
# Cross-dimensional features
# ---------------------------------------------------------------------------
class TestCrossDimensional:
    def test_multiple_queries_tracked(self, fresh_engine: GlobalSearchEngine) -> None:
        fresh_engine.search("web", "A")
        fresh_engine.search("web", "B")
        fresh_engine.search("academic", "A")
        graph = fresh_engine.get_intelligence_graph()
        assert "A" in graph["queries"]
        assert "B" in graph["queries"]

    def test_global_rank_assigned(self, fresh_engine: GlobalSearchEngine) -> None:
        report = fresh_engine.saturation_search("robotics")
        for r in report["ranked_results"]:
            assert "global_rank" in r
            assert isinstance(r["global_rank"], int)

    def test_composite_score_in_range(self, fresh_engine: GlobalSearchEngine) -> None:
        report = fresh_engine.saturation_search("genomics")
        for r in report["ranked_results"]:
            assert 0.0 <= r["composite_score"] <= 1.0
