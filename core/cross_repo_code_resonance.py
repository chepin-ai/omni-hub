"""
OMNI-HUB v156: Cross-Repo Code Resonance (跨仓代码共振)

Detects DEEP code-level resonance between repositories based on architecture
patterns, design philosophy, and structural similarity. 不只是表面元数据匹配，
而是深层的代码结构、架构模式、设计哲学共振。
"""

import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from core.event_bus import event_bus
except ImportError:
    event_bus = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "alliance_repos.json"
)

# Resonance levels for deep code resonance
RESONANCE_LEVELS = [
    (0.9, "soulmate"),
    (0.7, "kindred"),
    (0.5, "similar"),
    (0.3, "acquainted"),
]

# Scoring weights for deep resonance components
WEIGHT_ARCHITECTURE = 0.30
WEIGHT_DESIGN_PATTERNS = 0.25
WEIGHT_CODE_ORGANIZATION = 0.20
WEIGHT_TESTING_STRATEGY = 0.15
WEIGHT_DOCUMENTATION = 0.10

# Simulated pattern data for alliance repos (跨仓代码共振模拟数据)
SIMULATED_PATTERNS: Dict[str, Dict[str, Any]] = {
    "omni-hub": {
        "architecture_style": "distributed",
        "design_patterns": ["singleton", "observer", "factory"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.9,
    },
    "langchain-ai/langchain": {
        "architecture_style": "framework",
        "design_patterns": ["chain_of_responsibility", "builder", "adapter"],
        "code_organization": "layered",
        "testing_strategy": "unit",
        "documentation_level": 0.8,
    },
    "vci-ucif2": {
        "architecture_style": "distributed",
        "design_patterns": ["singleton", "observer"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.7,
    },
    "huggingface/transformers": {
        "architecture_style": "framework",
        "design_patterns": ["factory", "strategy", "template_method"],
        "code_organization": "layered",
        "testing_strategy": "integration",
        "documentation_level": 0.85,
    },
    "pytorch/pytorch": {
        "architecture_style": "framework",
        "design_patterns": ["factory", "strategy", "singleton"],
        "code_organization": "layered",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.8,
    },
    "openai/openai-python": {
        "architecture_style": "sdk",
        "design_patterns": ["builder", "adapter", "facade"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.75,
    },
    "microsoft/semantic-kernel": {
        "architecture_style": "framework",
        "design_patterns": ["chain_of_responsibility", "observer", "adapter"],
        "code_organization": "layered",
        "testing_strategy": "integration",
        "documentation_level": 0.8,
    },
    "vci-lvlu": {
        "architecture_style": "distributed",
        "design_patterns": ["observer", "mediator"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.75,
    },
    "vci-lgt": {
        "architecture_style": "modular",
        "design_patterns": ["strategy", "factory"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.7,
    },
    "vci-qfa": {
        "architecture_style": "distributed",
        "design_patterns": ["singleton", "observer", "strategy"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.8,
    },
    "vci-vinf": {
        "architecture_style": "distributed",
        "design_patterns": ["observer", "chain_of_responsibility"],
        "code_organization": "modular",
        "testing_strategy": "integration",
        "documentation_level": 0.65,
    },
    "vci-qgl": {
        "architecture_style": "distributed",
        "design_patterns": ["singleton", "strategy"],
        "code_organization": "layered",
        "testing_strategy": "unit",
        "documentation_level": 0.7,
    },
    "vci-qlv": {
        "architecture_style": "distributed",
        "design_patterns": ["observer", "factory", "singleton"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.75,
    },
    "vci-qtlv": {
        "architecture_style": "distributed",
        "design_patterns": ["observer", "singleton", "template_method"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.72,
    },
    "vci-usrm": {
        "architecture_style": "distributed",
        "design_patterns": ["mediator", "observer"],
        "code_organization": "modular",
        "testing_strategy": "integration",
        "documentation_level": 0.68,
    },
    "vci-cfts": {
        "architecture_style": "distributed",
        "design_patterns": ["singleton", "factory", "observer"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.78,
    },
    "vci-aiq": {
        "architecture_style": "modular",
        "design_patterns": ["strategy", "template_method"],
        "code_organization": "layered",
        "testing_strategy": "unit",
        "documentation_level": 0.7,
    },
    "vci-inbox": {
        "architecture_style": "event_driven",
        "design_patterns": ["observer", "mediator"],
        "code_organization": "modular",
        "testing_strategy": "integration",
        "documentation_level": 0.6,
    },
    "ci-worker-01": {
        "architecture_style": "modular",
        "design_patterns": ["factory", "strategy"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.55,
    },
    "qlv-lib": {
        "architecture_style": "library",
        "design_patterns": ["facade", "adapter"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.65,
    },
    "lgt-worker-01": {
        "architecture_style": "modular",
        "design_patterns": ["factory", "builder"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.5,
    },
    "ci-yard": {
        "architecture_style": "event_driven",
        "design_patterns": ["observer", "singleton"],
        "code_organization": "modular",
        "testing_strategy": "integration",
        "documentation_level": 0.58,
    },
    "vci-control": {
        "architecture_style": "distributed",
        "design_patterns": ["singleton", "mediator"],
        "code_organization": "layered",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.62,
    },
    "qfos-autonomous-engine": {
        "architecture_style": "distributed",
        "design_patterns": ["strategy", "observer", "template_method"],
        "code_organization": "modular",
        "testing_strategy": "integration",
        "documentation_level": 0.7,
    },
    "grand-synthesis": {
        "architecture_style": "modular",
        "design_patterns": ["strategy", "template_method"],
        "code_organization": "layered",
        "testing_strategy": "unit",
        "documentation_level": 0.85,
    },
    "prima-50-research": {
        "architecture_style": "framework",
        "design_patterns": ["factory", "builder", "strategy"],
        "code_organization": "layered",
        "testing_strategy": "unit",
        "documentation_level": 0.72,
    },
    "ci-worker-02": {
        "architecture_style": "modular",
        "design_patterns": ["factory", "strategy"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.52,
    },
    "vci-library": {
        "architecture_style": "library",
        "design_patterns": ["facade", "adapter", "singleton"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.6,
    },
    "vci-playground": {
        "architecture_style": "modular",
        "design_patterns": ["factory", "builder"],
        "code_organization": "modular",
        "testing_strategy": "unit",
        "documentation_level": 0.55,
    },
    "vci-root": {
        "architecture_style": "distributed",
        "design_patterns": ["singleton", "observer", "mediator"],
        "code_organization": "modular",
        "testing_strategy": "comprehensive",
        "documentation_level": 0.65,
    },
    "vci-logs": {
        "architecture_style": "event_driven",
        "design_patterns": ["observer", "chain_of_responsibility"],
        "code_organization": "modular",
        "testing_strategy": "integration",
        "documentation_level": 0.5,
    },
    "vci-code": {
        "architecture_style": "modular",
        "design_patterns": ["factory", "strategy"],
        "code_organization": "layered",
        "testing_strategy": "unit",
        "documentation_level": 0.58,
    },
    "vci-bus": {
        "architecture_style": "event_driven",
        "design_patterns": ["observer", "mediator", "singleton"],
        "code_organization": "modular",
        "testing_strategy": "integration",
        "documentation_level": 0.6,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_level(score: float) -> str:
    """Map deep resonance score to level name."""
    for threshold, name in RESONANCE_LEVELS:
        if score >= threshold:
            return name
    return "stranger"


def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _documentation_proximity(doc_a: float, doc_b: float) -> float:
    """
    Compute documentation level proximity (0-1).
    Returns 1.0 when identical, decreases linearly with difference.
    """
    diff = abs(doc_a - doc_b)
    # Max difference is 1.0 (0.0 vs 1.0), so proximity = 1 - diff
    return max(0.0, 1.0 - diff)


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------

class CrossRepoCodeResonance:
    """
    Cross-Repository Code Resonance Engine (跨仓代码共振引擎).

    Detects deep code-level resonance between repositories based on
    architecture patterns, design philosophy, and structural similarity.
    """

    def __init__(self, data_path: Optional[str] = None) -> None:
        self.data_path = data_path or REPO_DATA_PATH
        self.repos: Dict[str, Dict[str, Any]] = {}
        self.code_pattern_index: Dict[str, Dict[str, Any]] = {}
        self._resonance_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._load_repos()
        self._initialize_simulated_patterns()

    def _load_repos(self) -> None:
        """Load repository metadata from alliance_repos.json."""
        try:
            with open(self.data_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            self.repos = {}
            self._emit_event("code_resonance_load_failed", {"error": str(exc)})
            return

        # Flatten all categories into a single repo map
        for category, repo_map in raw.items():
            if not isinstance(repo_map, dict):
                continue
            for repo_name, meta in repo_map.items():
                if isinstance(meta, dict):
                    self.repos[repo_name] = dict(meta)
                    self.repos[repo_name]["_category"] = category

    def _initialize_simulated_patterns(self) -> None:
        """Load simulated pattern data for known repos."""
        for repo_name, patterns in SIMULATED_PATTERNS.items():
            if repo_name in self.repos:
                self.code_pattern_index[repo_name] = dict(patterns)

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit event via event_bus if available."""
        if event_bus is not None:
            try:
                event_bus.emit(event_type, payload)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Pattern indexing
    # ------------------------------------------------------------------

    def index_repo_patterns(self, repo_name: str, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index architecture patterns for a repository.

        Expected pattern keys:
        - architecture_style: str
        - design_patterns: List[str]
        - code_organization: str
        - testing_strategy: str
        - documentation_level: float (0-1)

        Returns the indexed patterns dict.
        """
        if not repo_name:
            return {}

        # Defensive: normalize design_patterns to list of strings
        design_patterns = patterns.get("design_patterns", [])
        if not isinstance(design_patterns, list):
            design_patterns = []
        design_patterns = [str(p) for p in design_patterns]

        normalized: Dict[str, Any] = {
            "architecture_style": str(patterns.get("architecture_style", "")),
            "design_patterns": design_patterns,
            "code_organization": str(patterns.get("code_organization", "")),
            "testing_strategy": str(patterns.get("testing_strategy", "")),
            "documentation_level": float(patterns.get("documentation_level", 0.0)),
        }

        self.code_pattern_index[repo_name] = normalized
        self._emit_event("code_patterns_indexed", {"repo": repo_name, "patterns": normalized})

        # Invalidate cache for this repo
        keys_to_remove = [k for k in self._resonance_cache if repo_name in k]
        for key in keys_to_remove:
            del self._resonance_cache[key]

        return dict(normalized)

    # ------------------------------------------------------------------
    # Deep resonance computation
    # ------------------------------------------------------------------

    def compute_deep_resonance(self, repo_a: str, repo_b: str) -> Dict[str, Any]:
        """
        Compute deep code-level resonance (0-1) between two repositories.

        Components:
        - architecture_style match: +0.30
        - design_patterns overlap (Jaccard): +0.25
        - code_organization similarity: +0.20
        - testing_strategy match: +0.15
        - documentation_level proximity: +0.10
        """
        if repo_a == repo_b:
            return {
                "repo_a": repo_a,
                "repo_b": repo_b,
                "score": 1.0,
                "level": "soulmate",
                "components": {},
            }

        cache_key = tuple(sorted((repo_a, repo_b)))
        if cache_key in self._resonance_cache:
            return dict(self._resonance_cache[cache_key])

        patterns_a = self.code_pattern_index.get(repo_a, {})
        patterns_b = self.code_pattern_index.get(repo_b, {})

        # Guard against unknown repos
        if not patterns_a or not patterns_b:
            result = {
                "repo_a": repo_a,
                "repo_b": repo_b,
                "score": 0.0,
                "level": "stranger",
                "components": {"error": "unknown repository or no patterns indexed"},
            }
            self._resonance_cache[cache_key] = result
            return dict(result)

        components: Dict[str, float] = {}

        # 1. Architecture style match
        arch_a = patterns_a.get("architecture_style", "")
        arch_b = patterns_b.get("architecture_style", "")
        if arch_a and arch_b and arch_a == arch_b:
            components["architecture_match"] = WEIGHT_ARCHITECTURE
        else:
            components["architecture_match"] = 0.0

        # 2. Design patterns overlap (Jaccard similarity)
        dp_a = set(patterns_a.get("design_patterns", []))
        dp_b = set(patterns_b.get("design_patterns", []))
        jaccard = _jaccard_similarity(dp_a, dp_b)
        components["design_patterns_overlap"] = round(jaccard * WEIGHT_DESIGN_PATTERNS, 4)

        # 3. Code organization similarity
        org_a = patterns_a.get("code_organization", "")
        org_b = patterns_b.get("code_organization", "")
        if org_a and org_b and org_a == org_b:
            components["code_organization_match"] = WEIGHT_CODE_ORGANIZATION
        else:
            components["code_organization_match"] = 0.0

        # 4. Testing strategy match
        test_a = patterns_a.get("testing_strategy", "")
        test_b = patterns_b.get("testing_strategy", "")
        if test_a and test_b and test_a == test_b:
            components["testing_strategy_match"] = WEIGHT_TESTING_STRATEGY
        else:
            components["testing_strategy_match"] = 0.0

        # 5. Documentation level proximity
        doc_a = patterns_a.get("documentation_level", 0.0)
        doc_b = patterns_b.get("documentation_level", 0.0)
        doc_proximity = _documentation_proximity(doc_a, doc_b)
        components["documentation_proximity"] = round(doc_proximity * WEIGHT_DOCUMENTATION, 4)

        score = sum(components.values())
        score = round(min(max(score, 0.0), 1.0), 4)
        level = _get_level(score)

        result = {
            "repo_a": repo_a,
            "repo_b": repo_b,
            "score": score,
            "level": level,
            "components": components,
        }
        self._resonance_cache[cache_key] = result
        return dict(result)

    # ------------------------------------------------------------------
    # Architectural twin discovery
    # ------------------------------------------------------------------

    def find_architectural_twins(
        self, repo_name: str, threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find repositories with highest deep resonance (soul mates / architectural twins).

        Returns list sorted by descending resonance score.
        """
        if repo_name not in self.code_pattern_index:
            return []

        twins: List[Dict[str, Any]] = []
        for other_name in self.code_pattern_index:
            if other_name == repo_name:
                continue
            resonance = self.compute_deep_resonance(repo_name, other_name)
            if resonance["score"] >= threshold:
                twins.append(resonance)

        twins.sort(key=lambda x: x["score"], reverse=True)
        return twins

    # ------------------------------------------------------------------
    # Resonance map builder
    # ------------------------------------------------------------------

    def build_code_resonance_map(self) -> Dict[str, Any]:
        """
        Build full map of all deep resonant pairs.
        """
        nodes = sorted(self.code_pattern_index.keys())
        edges: List[Dict[str, Any]] = []
        scores: List[float] = []

        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                resonance = self.compute_deep_resonance(nodes[i], nodes[j])
                if resonance["score"] > 0.0:
                    edges.append(resonance)
                    scores.append(resonance["score"])

        # Count by level
        level_counts: Dict[str, int] = {
            "soulmate": 0,
            "kindred": 0,
            "similar": 0,
            "acquainted": 0,
            "stranger": 0,
        }
        for edge in edges:
            level_counts[edge["level"]] = level_counts.get(edge["level"], 0) + 1

        avg_resonance = round(sum(scores) / len(scores), 4) if scores else 0.0

        # Strongest pair
        strongest: Optional[Dict[str, Any]] = None
        if edges:
            strongest = max(edges, key=lambda e: e["score"])

        # Twin pairs (soulmate + kindred)
        twin_pairs = [e for e in edges if e["level"] in ("soulmate", "kindred")]

        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "level_distribution": level_counts,
            "avg_resonance": avg_resonance,
            "strongest_pair": strongest,
            "twin_pairs": twin_pairs,
        }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """
        Return indexed repos, twin pairs, average deep resonance.
        """
        resonance_map = self.build_code_resonance_map()
        return {
            "indexed_repo_count": len(self.code_pattern_index),
            "indexed_repos": sorted(self.code_pattern_index.keys()),
            "twin_pair_count": len(resonance_map["twin_pairs"]),
            "twin_pairs": resonance_map["twin_pairs"],
            "avg_deep_resonance": resonance_map["avg_resonance"],
            "level_distribution": resonance_map["level_distribution"],
            "strongest_pair": resonance_map["strongest_pair"],
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_module: Optional[CrossRepoCodeResonance] = None


def get_cross_repo_code_resonance() -> CrossRepoCodeResonance:
    """Global singleton accessor for CrossRepoCodeResonance."""
    global _module
    if _module is None:
        _module = CrossRepoCodeResonance()
    return _module


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v156 CROSS-REPO CODE RESONANCE (跨仓代码共振)")
    print("=" * 70)

    engine = CrossRepoCodeResonance()
    status = engine.get_status()
    print(f"\nCode Resonance Status:")
    print(f"  Indexed repos: {status['indexed_repo_count']}")
    print(f"  Twin pairs: {status['twin_pair_count']}")
    print(f"  Avg deep resonance: {status['avg_deep_resonance']:.4f}")
    print(f"  Level distribution: {status['level_distribution']}")

    if status["strongest_pair"]:
        sp = status["strongest_pair"]
        print(f"\nStrongest Pair:")
        print(f"  {sp['repo_a']} <-> {sp['repo_b']}: {sp['score']:.4f} ({sp['level']})")

    # Sample: find architectural twins for omni-hub
    twins = engine.find_architectural_twins("omni-hub", threshold=0.3)
    print(f"\nArchitectural twins of 'omni-hub' (threshold=0.3): {len(twins)}")
    for t in twins[:5]:
        print(f"  {t['repo_b']}: {t['score']:.4f} ({t['level']})")

    # Sample: deep resonance between omni-hub and vci-ucif2
    deep = engine.compute_deep_resonance("omni-hub", "vci-ucif2")
    print(f"\nDeep Resonance: omni-hub <-> vci-ucif2")
    print(f"  Score: {deep['score']:.4f} ({deep['level']})")
    print(f"  Components: {deep['components']}")

    print(f"\n{'='*70}")
