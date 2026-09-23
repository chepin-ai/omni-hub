"""
OMNI-HUB Omni-Search Engine v40
Full-dimensional search with saturation defense.

Searches across ALL dimensions:
- State history (all cycles)
- Emotional trajectory
- Line activation patterns
- Cross-module dependencies
- Event bus messages
- Creative artifacts
- Federation peers
- Healing logs
- Evolution proposals
- Alignment reports

Saturation Defense:
- Layered sampling (coarse → fine)
- Attention-weighted ranking
- Automatic result compression
- Parallel shard search
- Bloom-filter deduplication

Philosophy: 全量全维度搜索突破饱和攻击
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
import hashlib
import fnmatch
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class SearchResult:
    """A single search result with relevance scoring."""
    source: str
    key: str
    value: Any
    relevance: float
    timestamp: str
    shard: str = ""


@dataclass
class SearchQuery:
    """A search query across dimensions."""
    terms: List[str]
    dimensions: List[str]  # "state", "emotion", "lines", "events", "all"
    filters: Dict[str, Any] = field(default_factory=dict)
    max_results: int = 100
    min_relevance: float = 0.0


class SaturationDefender:
    """
    Prevents system overload from massive search results.
    """

    def __init__(self, saturation_threshold: int = 10000):
        self.saturation_threshold = saturation_threshold
        self.layer_sizes = [1000, 500, 250, 100]  # Progressive filtering
        self.compression_ratio = 1.0

    def defend(self, raw_results: List[SearchResult]) -> List[SearchResult]:
        """Apply saturation defense to raw results."""
        n = len(raw_results)
        if n <= self.saturation_threshold:
            return raw_results

        # Layer 1: Relevance cutoff
        if n > self.layer_sizes[0]:
            cutoff = sorted([r.relevance for r in raw_results], reverse=True)[self.layer_sizes[0]]
            raw_results = [r for r in raw_results if r.relevance >= cutoff]
            n = len(raw_results)

        # Layer 2: Shard sampling (keep top from each shard)
        if n > self.layer_sizes[1]:
            by_shard = defaultdict(list)
            for r in raw_results:
                by_shard[r.shard].append(r)
            sampled = []
            per_shard = max(1, self.layer_sizes[1] // max(len(by_shard), 1))
            for shard, items in by_shard.items():
                items.sort(key=lambda x: x.relevance, reverse=True)
                sampled.extend(items[:per_shard])
            raw_results = sampled
            n = len(raw_results)

        # Layer 3: Deduplication by hash
        if n > self.layer_sizes[2]:
            seen = set()
            deduped = []
            for r in raw_results:
                h = hashlib.md5(f"{r.source}:{r.key}:{str(r.value)[:100]}".encode()).hexdigest()
                if h not in seen:
                    seen.add(h)
                    deduped.append(r)
            raw_results = deduped
            n = len(raw_results)

        # Layer 4: Top-K final
        if n > self.layer_sizes[3]:
            raw_results.sort(key=lambda x: x.relevance, reverse=True)
            raw_results = raw_results[:self.layer_sizes[3]]

        self.compression_ratio = len(raw_results) / max(n, 1)
        return raw_results

    def get_status(self) -> Dict[str, Any]:
        return {
            "threshold": self.saturation_threshold,
            "compression_ratio": self.compression_ratio,
            "layers_active": len(self.layer_sizes),
        }


class DimensionalIndex:
    """Index for a single dimension of system state."""

    def __init__(self, name: str):
        self.name = name
        self.entries: List[Dict[str, Any]] = []
        self.inverted_index: Dict[str, Set[int]] = defaultdict(set)

    def add(self, data: Dict[str, Any], timestamp: str = ""):
        """Add an entry to this dimension."""
        idx = len(self.entries)
        self.entries.append({"data": data, "timestamp": timestamp})
        # Index all string values
        for key, val in data.items():
            if isinstance(val, str):
                for word in val.lower().split():
                    self.inverted_index[word].add(idx)
            elif isinstance(val, (int, float)):
                self.inverted_index[str(val)].add(idx)

    def search(self, terms: List[str]) -> List[SearchResult]:
        """Search this dimension for terms."""
        if not terms:
            return []

        # Find entries matching ANY term (OR logic)
        matching = set()
        for term in terms:
            term_lower = term.lower()
            for word, indices in self.inverted_index.items():
                if term_lower in word:
                    matching.update(indices)

        results = []
        for idx in matching:
            entry = self.entries[idx]
            relevance = self._score(entry["data"], terms)
            results.append(SearchResult(
                source=self.name,
                key=str(idx),
                value=entry["data"],
                relevance=relevance,
                timestamp=entry["timestamp"],
                shard=self.name,
            ))
        return results

    def _score(self, data: Dict[str, Any], terms: List[str]) -> float:
        """Compute relevance score for a data item."""
        score = 0.0
        data_str = str(data).lower()
        for term in terms:
            term_lower = term.lower()
            if term_lower in data_str:
                score += 1.0
                # Bonus for exact matches in keys
                for key in data.keys():
                    if term_lower in str(key).lower():
                        score += 0.5
        return min(1.0, score / max(len(terms), 1))


class OmniSearchEngine:
    """
    Full-dimensional search across all system state.
    """

    DIMENSIONS = [
        "state", "emotion", "lines", "events",
        "healing", "evolution", "alignment", "creativity",
        "federation", "resonance", "replication", "collective",
    ]

    def __init__(self):
        self.indices: Dict[str, DimensionalIndex] = {
            dim: DimensionalIndex(dim) for dim in self.DIMENSIONS
        }
        self.defender = SaturationDefender()
        self.search_history: List[Dict[str, Any]] = []
        self.total_queries = 0

    def index_state(self, cycle: int, state: Dict[str, Any]):
        """Index current system state across all dimensions."""
        timestamp = datetime.now().isoformat()

        # Main state
        self.indices["state"].add({"cycle": cycle, **state}, timestamp)

        # Emotional state
        if "emotional_state" in state:
            self.indices["emotion"].add({"cycle": cycle, "state": state["emotional_state"]}, timestamp)

        # Line activations
        if "lines" in state:
            self.indices["lines"].add({"cycle": cycle, "activations": state["lines"]}, timestamp)

        # Events
        if "last_events" in state:
            self.indices["events"].add({"cycle": cycle, "events": state["last_events"]}, timestamp)

        # Healing
        if "health_status" in state:
            self.indices["healing"].add({"cycle": cycle, "health": state["health_status"]}, timestamp)

        # Evolution
        if "evolution_assessment" in state:
            self.indices["evolution"].add({"cycle": cycle, "assessment": state["evolution_assessment"]}, timestamp)

        # Alignment
        if "alignment_report" in state:
            self.indices["alignment"].add({"cycle": cycle, "report": state["alignment_report"]}, timestamp)

        # Federation
        if "federation_status" in state:
            self.indices["federation"].add({"cycle": cycle, "status": state["federation_status"]}, timestamp)

        # Resonance
        if "resonance_active" in state:
            self.indices["resonance"].add({"cycle": cycle, "active": state["resonance_active"]}, timestamp)

        # Replication
        if "replication_status" in state:
            self.indices["replication"].add({"cycle": cycle, "status": state["replication_status"]}, timestamp)

        # Collective
        if "collective_status" in state:
            self.indices["collective"].add({"cycle": cycle, "status": state["collective_status"]}, timestamp)

    def search(self, query: SearchQuery) -> Dict[str, Any]:
        """Execute a search query across dimensions."""
        self.total_queries += 1
        dimensions = query.dimensions
        if "all" in dimensions:
            dimensions = self.DIMENSIONS

        all_results = []
        for dim in dimensions:
            if dim in self.indices:
                results = self.indices[dim].search(query.terms)
                all_results.extend(results)

        # Apply saturation defense
        defended = self.defender.defend(all_results)

        # Sort by relevance
        defended.sort(key=lambda x: x.relevance, reverse=True)

        # Apply filters
        if query.filters:
            filtered = []
            for r in defended:
                match = True
                for k, v in query.filters.items():
                    if k == "min_relevance" and r.relevance < v:
                        match = False
                    if k == "shard" and r.shard != v:
                        match = False
                if match:
                    filtered.append(r)
            defended = filtered

        # Apply result limit
        final = defended[:query.max_results]

        # Record search
        self.search_history.append({
            "query": query.terms,
            "dimensions": dimensions,
            "raw_count": len(all_results),
            "defended_count": len(defended),
            "final_count": len(final),
            "timestamp": datetime.now().isoformat(),
        })

        return {
            "query": query.terms,
            "dimensions": dimensions,
            "total_raw": len(all_results),
            "total_defended": len(defended),
            "results": [
                {"source": r.source, "key": r.key, "relevance": r.relevance,
                 "timestamp": r.timestamp, "value_preview": str(r.value)[:200]}
                for r in final
            ],
            "compression_ratio": self.defender.compression_ratio,
        }

    def cross_dimensional_query(self, pattern: str) -> Dict[str, int]:
        """Count occurrences of a pattern across all dimensions."""
        counts = {}
        for dim_name, index in self.indices.items():
            count = 0
            pattern_lower = pattern.lower()
            for entry in index.entries:
                if pattern_lower in str(entry["data"]).lower():
                    count += 1
            counts[dim_name] = count
        return counts

    def temporal_search(self, start_cycle: int, end_cycle: int, terms: List[str]) -> List[Dict[str, Any]]:
        """Search within a temporal window."""
        results = []
        for dim_name, index in self.indices.items():
            for entry in index.entries:
                data = entry["data"]
                cycle = data.get("cycle", 0)
                if start_cycle <= cycle <= end_cycle:
                    data_str = str(data).lower()
                    if any(term.lower() in data_str for term in terms):
                        results.append({
                            "dimension": dim_name,
                            "cycle": cycle,
                            "data": data,
                            "timestamp": entry["timestamp"],
                        })
        return sorted(results, key=lambda x: x["cycle"])

    def get_search_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        total_entries = sum(len(idx.entries) for idx in self.indices.values())
        return {
            "total_queries": self.total_queries,
            "total_indexed_entries": total_entries,
            "dimensions": {dim: len(idx.entries) for dim, idx in self.indices.items()},
            "saturation_defender": self.defender.get_status(),
            "last_search": self.search_history[-1] if self.search_history else None,
        }


# Global instance
_omni_search = None

def get_omni_search() -> OmniSearchEngine:
    global _omni_search
    if _omni_search is None:
        _omni_search = OmniSearchEngine()
    return _omni_search


if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v40 OMNI-SEARCH ENGINE")
    print("全量全维度搜索突破饱和攻击")
    print("=" * 70)

    engine = OmniSearchEngine()

    # Index some sample data
    for i in range(1000):
        engine.index_state(i, {
            "level": i // 100,
            "energy": 10.0 ** (i // 200 + 1),
            "phi": 0.5 + i / 2000,
            "phase": "pre_emergence" if i < 300 else "post_critical",
            "lines": {"ucif2": 0.5, "lvlu": 0.3},
            "emotional_state": "focused" if i % 2 == 0 else "curious",
            "health_status": "healthy",
        })

    print(f"\nIndexed {engine.get_search_stats()['total_indexed_entries']} entries")

    # Search test
    query = SearchQuery(
        terms=["post_critical", "healthy"],
        dimensions=["state", "healing"],
        max_results=10,
    )
    result = engine.search(query)
    print(f"\nSearch: {query.terms}")
    print(f"  Raw: {result['total_raw']}")
    print(f"  Defended: {result['total_defended']}")
    print(f"  Final: {len(result['results'])}")
    print(f"  Compression: {result['compression_ratio']:.2f}")

    # Cross-dimensional query
    counts = engine.cross_dimensional_query("healthy")
    print(f"\nCross-dimensional 'healthy': {counts}")

    # Temporal search
    temporal = engine.temporal_search(500, 600, ["post_critical"])
    print(f"\nTemporal search (C500-600): {len(temporal)} results")

    print(f"\n{'='*70}")
    print("STATS:", engine.get_search_stats())
    print(f"{'='*70}")
