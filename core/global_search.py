"""
OMNI-HUB Module v141: Global Search Engine (全域搜索引擎)

全量全维度饱和搜索突破。系统不等待用户输入，主动在所有维度进行搜索：
web搜索、图像搜索、学术搜索、代码搜索、金融数据搜索。
搜索结果被整合、去重、评分，形成全域情报图谱。
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# OMNI-HUB singleton pattern
# ---------------------------------------------------------------------------
_module = None


def get_global_search_engine() -> "GlobalSearchEngine":
    """Return the global singleton instance of GlobalSearchEngine."""
    global _module
    if _module is None:
        _module = GlobalSearchEngine()
    return _module


# ---------------------------------------------------------------------------
# Global Search Engine
# ---------------------------------------------------------------------------
class GlobalSearchEngine:
    """
    全域搜索引擎 — 在所有维度执行饱和搜索并构建情报图谱。

    Dimensions
    ----------
    - web      : 网页搜索
    - image    : 图像搜索
    - academic : 学术搜索
    - code     : 代码搜索
    - financial: 金融数据搜索
    - legal    : 法律搜索
    - news     : 新闻搜索
    """

    DIMENSIONS: List[str] = [
        "web",
        "image",
        "academic",
        "code",
        "financial",
        "legal",
        "news",
    ]

    MOCK_TITLES: Dict[str, List[str]] = {
        "web": [
            "Top 10 Resources on {query}",
            "Comprehensive Guide to {query}",
            "Latest Trends in {query}",
            "Expert Analysis: {query}",
            "Community Discussion on {query}",
        ],
        "image": [
            "Infographic: {query}",
            "Visual Guide to {query}",
            "Diagram of {query}",
            "Photo Gallery: {query}",
            "Chart Analysis: {query}",
        ],
        "academic": [
            "A Systematic Review of {query}",
            "Novel Approach to {query}",
            "Empirical Study on {query}",
            "Meta-Analysis: {query}",
        ],
        "code": [
            "GitHub Repository for {query}",
            "Stack Overflow: {query} Solutions",
            "Code Snippet for {query}",
            "Library Documentation: {query}",
            "Open Source Project: {query}",
        ],
        "financial": [
            "Market Report: {query}",
            "Investment Analysis on {query}",
            "Stock Performance and {query}",
            "Financial Forecast: {query}",
        ],
        "legal": [
            "Case Law Related to {query}",
            "Regulatory Framework for {query}",
            "Legal Precedent: {query}",
            "Compliance Guide: {query}",
        ],
        "news": [
            "Breaking: {query} Update",
            "Industry News on {query}",
            "Press Release: {query}",
            "Market Watch: {query}",
            "Exclusive Report on {query}",
        ],
    }

    MOCK_SOURCES: Dict[str, List[str]] = {
        "web": ["Google", "Bing", "DuckDuckGo", "Yahoo", "Baidu"],
        "image": ["Google Images", "Bing Images", "Pinterest", "Unsplash", "Shutterstock"],
        "academic": ["Google Scholar", "PubMed", "IEEE", "arXiv", "Nature"],
        "code": ["GitHub", "Stack Overflow", "GitLab", "Bitbucket", "PyPI"],
        "financial": ["Bloomberg", "Reuters", "Yahoo Finance", "SEC EDGAR", "TradingView"],
        "legal": ["Westlaw", "LexisNexis", "CourtListener", "Justia", "GovInfo"],
        "news": ["Reuters", "AP News", "BBC", "CNN", "Bloomberg"],
    }

    # ------------------------------------------------------------------
    def __init__(self) -> None:
        """Initialize the global search engine."""
        self.search_history: List[Dict[str, Any]] = []
        self.result_index: Dict[str, Dict[str, Any]] = {}
        self.dimension_stats: Dict[str, Dict[str, Any]] = {
            dim: {"count": 0, "total_relevance": 0.0, "last_query": None}
            for dim in self.DIMENSIONS
        }
        self._search_count: int = 0
        self._lock: Any = None  # Placeholder for threading lock if needed

    # ------------------------------------------------------------------
    def search(self, dimension: str, query: str) -> Dict[str, Any]:
        """
        Simulate a search in a single dimension.

        Parameters
        ----------
        dimension : str
            One of the supported dimensions.
        query : str
            The search query string.

        Returns
        -------
        dict
            Search result metadata and simulated hits.
        """
        if dimension not in self.DIMENSIONS:
            raise ValueError(
                f"Unsupported dimension '{dimension}'. "
                f"Supported: {self.DIMENSIONS}"
            )

        # Generate deterministic but varied mock results
        num_results = 3 + (hash(query + dimension) % 3)  # 3–5 results
        results: List[Dict[str, Any]] = []
        titles = self.MOCK_TITLES.get(dimension, ["Result on {query}"])
        sources = self.MOCK_SOURCES.get(dimension, ["Unknown"])

        for i in range(num_results):
            title_template = titles[i % len(titles)]
            source = sources[i % len(sources)]
            title = title_template.format(query=query)
            relevance = round(0.5 + ((hash(title + str(i)) % 100) / 200), 4)
            confidence = round(min(1.0, relevance * (1.0 + 0.1 * (i == 0))), 4)

            result_id = str(uuid.uuid4())
            result = {
                "id": result_id,
                "title": title,
                "source": source,
                "dimension": dimension,
                "query": query,
                "relevance": relevance,
                "confidence": confidence,
                "timestamp": time.time(),
                "rank": i + 1,
            }
            results.append(result)
            self.result_index[result_id] = result

        # Update stats
        self.dimension_stats[dimension]["count"] += 1
        self.dimension_stats[dimension]["last_query"] = query
        self.dimension_stats[dimension]["total_relevance"] += sum(
            r["relevance"] for r in results
        )

        search_record = {
            "query": query,
            "dimension": dimension,
            "timestamp": time.time(),
            "result_count": len(results),
            "results": [r["id"] for r in results],
        }
        self.search_history.append(search_record)
        self._search_count += 1

        return {
            "dimension": dimension,
            "query": query,
            "count": len(results),
            "results": results,
            "top_confidence": results[0]["confidence"] if results else 0.0,
        }

    # ------------------------------------------------------------------
    def saturation_search(self, query: str) -> Dict[str, Any]:
        """
        饱和搜索 — Search ALL dimensions simultaneously, merge, deduplicate, and rank.

        Parameters
        ----------
        query : str
            The search query string.

        Returns
        -------
        dict
            Unified search report with merged and ranked results.
        """
        all_results: List[Dict[str, Any]] = []
        dimension_reports: Dict[str, Any] = {}

        for dim in self.DIMENSIONS:
            try:
                report = self.search(dim, query)
                dimension_reports[dim] = {
                    "count": report["count"],
                    "top_confidence": report["top_confidence"],
                }
                all_results.extend(report["results"])
            except Exception:
                # Defensive: skip failing dimensions
                dimension_reports[dim] = {"count": 0, "top_confidence": 0.0}

        # Deduplicate by title similarity (exact match for mock data)
        seen_titles: Set[str] = set()
        unique_results: List[Dict[str, Any]] = []
        for r in all_results:
            if r["title"] not in seen_titles:
                seen_titles.add(r["title"])
                unique_results.append(r)

        # Rank by composite score: relevance * confidence
        for r in unique_results:
            r["composite_score"] = round(r["relevance"] * r["confidence"], 4)

        ranked = sorted(unique_results, key=lambda x: x["composite_score"], reverse=True)
        for idx, r in enumerate(ranked, start=1):
            r["global_rank"] = idx

        # Build intelligence edges (links between results across dimensions)
        edges: List[Dict[str, Any]] = []
        for i, a in enumerate(ranked):
            for b in ranked[i + 1 : i + 3]:  # link to next 2 neighbors
                edges.append(
                    {
                        "source": a["id"],
                        "target": b["id"],
                        "weight": round(
                            (a["composite_score"] + b["composite_score"]) / 2, 4
                        ),
                        "relation": "cross_reference",
                    }
                )

        return {
            "query": query,
            "dimensions_covered": len(self.DIMENSIONS),
            "total_raw": len(all_results),
            "total_unique": len(unique_results),
            "dimension_reports": dimension_reports,
            "ranked_results": ranked,
            "intelligence_edges": edges,
            "top_result": ranked[0] if ranked else None,
        }

    # ------------------------------------------------------------------
    def get_intelligence_graph(self) -> Dict[str, Any]:
        """
        Build a knowledge graph from all accumulated search history.

        Returns
        -------
        dict
            Nodes (results) and edges (cross-references) forming the intelligence graph.
        """
        nodes: List[Dict[str, Any]] = []
        node_ids: Set[str] = set()
        edges: List[Dict[str, Any]] = []

        # Group results by query to create query-level clusters
        query_clusters: Dict[str, List[str]] = {}
        for record in self.search_history:
            q = record["query"]
            query_clusters.setdefault(q, []).extend(record["results"])

        for result_id, result in self.result_index.items():
            if result_id not in node_ids:
                nodes.append(
                    {
                        "id": result_id,
                        "label": result["title"],
                        "dimension": result["dimension"],
                        "query": result["query"],
                        "relevance": result["relevance"],
                        "confidence": result["confidence"],
                    }
                )
                node_ids.add(result_id)

        # Create edges within same query cluster
        for q, result_ids in query_clusters.items():
            for i, a_id in enumerate(result_ids):
                for b_id in result_ids[i + 1 :]:
                    a = self.result_index.get(a_id)
                    b = self.result_index.get(b_id)
                    if a and b:
                        weight = round((a["relevance"] + b["relevance"]) / 2, 4)
                        edges.append(
                            {
                                "source": a_id,
                                "target": b_id,
                                "weight": weight,
                                "relation": "same_query",
                                "query": q,
                            }
                        )

        # Cross-query edges: same dimension
        dim_results: Dict[str, List[str]] = {
            dim: [] for dim in self.DIMENSIONS
        }
        for rid, r in self.result_index.items():
            dim_results[r["dimension"]].append(rid)

        for dim, rids in dim_results.items():
            for i, a_id in enumerate(rids[:5]):  # limit cross edges
                for b_id in rids[i + 1 : i + 3]:
                    edges.append(
                        {
                            "source": a_id,
                            "target": b_id,
                            "weight": 0.3,
                            "relation": "same_dimension",
                            "dimension": dim,
                        }
                    )

        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "queries": list(query_clusters.keys()),
            "dimensions": list({n["dimension"] for n in nodes}),
        }

    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Return current engine status.

        Returns
        -------
        dict
            Search count, dimensions covered, top results summary.
        """
        top_results = sorted(
            self.result_index.values(),
            key=lambda x: x.get("relevance", 0.0),
            reverse=True,
        )[:5]

        dimensions_covered = [
            dim for dim, stats in self.dimension_stats.items() if stats["count"] > 0
        ]

        return {
            "search_count": self._search_count,
            "total_results_indexed": len(self.result_index),
            "dimensions_covered": dimensions_covered,
            "dimensions_total": len(self.DIMENSIONS),
            "top_results": [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "dimension": r["dimension"],
                    "relevance": r["relevance"],
                    "confidence": r["confidence"],
                }
                for r in top_results
            ],
            "dimension_stats": self.dimension_stats,
        }
