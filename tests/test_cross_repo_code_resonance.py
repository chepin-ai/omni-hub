"""
OMNI-HUB v156: Cross-Repo Code Resonance Tests (跨仓代码共振测试)
"""

import sys
sys.path.insert(0, "/mnt/agents/output/OMNI-HUB")

import pytest
from core.cross_repo_code_resonance import (
    CrossRepoCodeResonance,
    get_cross_repo_code_resonance,
    _get_level,
    _jaccard_similarity,
    _documentation_proximity,
    WEIGHT_ARCHITECTURE,
    WEIGHT_DESIGN_PATTERNS,
    WEIGHT_CODE_ORGANIZATION,
    WEIGHT_TESTING_STRATEGY,
    WEIGHT_DOCUMENTATION,
    SIMULATED_PATTERNS,
)


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_get_level_soulmate(self):
        assert _get_level(0.95) == "soulmate"

    def test_get_level_kindred(self):
        assert _get_level(0.85) == "kindred"

    def test_get_level_similar(self):
        assert _get_level(0.55) == "similar"

    def test_get_level_acquainted(self):
        assert _get_level(0.35) == "acquainted"

    def test_get_level_stranger(self):
        assert _get_level(0.15) == "stranger"

    def test_jaccard_both_empty(self):
        assert _jaccard_similarity(set(), set()) == 1.0

    def test_jaccard_one_empty(self):
        assert _jaccard_similarity({"a", "b"}, set()) == 0.0

    def test_jaccard_identical(self):
        assert _jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0

    def test_jaccard_partial(self):
        # intersection=1, union=3 => 1/3
        assert _jaccard_similarity({"a", "b"}, {"a", "c"}) == pytest.approx(1 / 3)

    def test_documentation_proximity_identical(self):
        assert _documentation_proximity(0.8, 0.8) == 1.0

    def test_documentation_proximity_max_diff(self):
        assert _documentation_proximity(0.0, 1.0) == 0.0

    def test_documentation_proximity_partial(self):
        assert _documentation_proximity(0.7, 0.9) == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# CrossRepoCodeResonance tests
# ---------------------------------------------------------------------------

class TestCrossRepoCodeResonance:
    def test_initialization_loads_repos(self):
        engine = CrossRepoCodeResonance()
        assert len(engine.repos) > 0
        assert "omni-hub" in engine.repos
        assert "vci-ucif2" in engine.repos

    def test_initialization_loads_simulated_patterns(self):
        engine = CrossRepoCodeResonance()
        assert len(engine.code_pattern_index) > 0
        assert "omni-hub" in engine.code_pattern_index
        assert "vci-ucif2" in engine.code_pattern_index

    def test_index_repo_patterns(self):
        engine = CrossRepoCodeResonance()
        patterns = {
            "architecture_style": "microservices",
            "design_patterns": ["circuit_breaker", "event_sourcing"],
            "code_organization": "domain_driven",
            "testing_strategy": "contract",
            "documentation_level": 0.85,
        }
        result = engine.index_repo_patterns("test-repo", patterns)
        assert result["architecture_style"] == "microservices"
        assert result["design_patterns"] == ["circuit_breaker", "event_sourcing"]
        assert result["code_organization"] == "domain_driven"
        assert result["testing_strategy"] == "contract"
        assert result["documentation_level"] == 0.85
        assert "test-repo" in engine.code_pattern_index

    def test_index_repo_patterns_empty_name(self):
        engine = CrossRepoCodeResonance()
        result = engine.index_repo_patterns("", {"architecture_style": "modular"})
        assert result == {}

    def test_index_repo_patterns_invalid_design_patterns(self):
        engine = CrossRepoCodeResonance()
        patterns = {
            "architecture_style": "modular",
            "design_patterns": "not-a-list",
            "code_organization": "layered",
            "testing_strategy": "unit",
            "documentation_level": 0.5,
        }
        result = engine.index_repo_patterns("test-repo-2", patterns)
        assert result["design_patterns"] == []

    def test_compute_deep_resonance_same_repo(self):
        engine = CrossRepoCodeResonance()
        result = engine.compute_deep_resonance("omni-hub", "omni-hub")
        assert result["score"] == 1.0
        assert result["level"] == "soulmate"

    def test_compute_deep_resonance_unknown_repo(self):
        engine = CrossRepoCodeResonance()
        result = engine.compute_deep_resonance("omni-hub", "nonexistent-repo")
        assert result["score"] == 0.0
        assert result["level"] == "stranger"
        assert "error" in result["components"]

    def test_compute_deep_resonance_known_pair(self):
        """omni-hub and vci-ucif2 share distributed, modular, comprehensive + patterns."""
        engine = CrossRepoCodeResonance()
        result = engine.compute_deep_resonance("omni-hub", "vci-ucif2")
        # architecture_match = 0.3 (both distributed)
        # design_patterns: {singleton, observer, factory} vs {singleton, observer}
        # jaccard = 2/3 => 0.25 * 2/3 = 0.1667
        # code_organization_match = 0.2 (both modular)
        # testing_strategy_match = 0.15 (both comprehensive)
        # documentation: |0.9 - 0.7| = 0.2 => proximity = 0.8 => 0.1 * 0.8 = 0.08
        # total = 0.3 + 0.1667 + 0.2 + 0.15 + 0.08 = 0.8967
        expected_score = round(
            WEIGHT_ARCHITECTURE
            + (2 / 3) * WEIGHT_DESIGN_PATTERNS
            + WEIGHT_CODE_ORGANIZATION
            + WEIGHT_TESTING_STRATEGY
            + 0.8 * WEIGHT_DOCUMENTATION,
            4,
        )
        assert result["score"] == pytest.approx(expected_score, abs=1e-4)
        assert result["level"] == "kindred"
        assert result["components"]["architecture_match"] == WEIGHT_ARCHITECTURE
        assert result["components"]["code_organization_match"] == WEIGHT_CODE_ORGANIZATION
        assert result["components"]["testing_strategy_match"] == WEIGHT_TESTING_STRATEGY

    def test_compute_deep_resonance_different_architecture(self):
        """omni-hub (distributed) vs langchain (framework) — different architecture."""
        engine = CrossRepoCodeResonance()
        result = engine.compute_deep_resonance("omni-hub", "langchain-ai/langchain")
        # architecture_match = 0
        # design_patterns jaccard: {singleton, observer, factory} vs {chain_of_responsibility, builder, adapter} => 0
        # code_organization: modular vs layered => 0
        # testing_strategy: comprehensive vs unit => 0
        # documentation: |0.9 - 0.8| = 0.1 => proximity = 0.9 => 0.1 * 0.9 = 0.09
        expected_score = round(0.9 * WEIGHT_DOCUMENTATION, 4)
        assert result["score"] == pytest.approx(expected_score, abs=1e-4)
        assert result["level"] == "stranger"

    def test_compute_deep_resonance_caching(self):
        engine = CrossRepoCodeResonance()
        r1 = engine.compute_deep_resonance("omni-hub", "vci-ucif2")
        r2 = engine.compute_deep_resonance("vci-ucif2", "omni-hub")
        assert r1["score"] == r2["score"]

    def test_find_architectural_twins(self):
        engine = CrossRepoCodeResonance()
        twins = engine.find_architectural_twins("omni-hub", threshold=0.3)
        assert len(twins) > 0
        # Should be sorted descending
        for i in range(len(twins) - 1):
            assert twins[i]["score"] >= twins[i + 1]["score"]
        # vci-ucif2 is a kindred twin (same architecture, org, testing)
        ucif2_twin = next((t for t in twins if t["repo_b"] == "vci-ucif2"), None)
        assert ucif2_twin is not None
        assert ucif2_twin["level"] == "kindred"

    def test_find_architectural_twins_no_self(self):
        engine = CrossRepoCodeResonance()
        twins = engine.find_architectural_twins("omni-hub", threshold=0.3)
        for t in twins:
            assert t["repo_b"] != "omni-hub"

    def test_find_architectural_twins_unknown_repo(self):
        engine = CrossRepoCodeResonance()
        twins = engine.find_architectural_twins("nonexistent-repo", threshold=0.3)
        assert twins == []

    def test_find_architectural_twins_high_threshold(self):
        engine = CrossRepoCodeResonance()
        twins = engine.find_architectural_twins("omni-hub", threshold=0.9)
        # Only soulmate-level twins
        for t in twins:
            assert t["score"] >= 0.9

    def test_build_code_resonance_map(self):
        engine = CrossRepoCodeResonance()
        resonance_map = engine.build_code_resonance_map()
        assert resonance_map["node_count"] > 0
        assert resonance_map["edge_count"] > 0
        assert "avg_resonance" in resonance_map
        assert "strongest_pair" in resonance_map
        assert "twin_pairs" in resonance_map
        assert "level_distribution" in resonance_map
        # Level distribution should sum to edge count
        level_sum = sum(resonance_map["level_distribution"].values())
        assert level_sum == resonance_map["edge_count"]

    def test_build_code_resonance_map_nodes_are_indexed(self):
        engine = CrossRepoCodeResonance()
        resonance_map = engine.build_code_resonance_map()
        for node in resonance_map["nodes"]:
            assert node in engine.code_pattern_index

    def test_get_status(self):
        engine = CrossRepoCodeResonance()
        status = engine.get_status()
        assert "indexed_repo_count" in status
        assert "indexed_repos" in status
        assert "twin_pair_count" in status
        assert "twin_pairs" in status
        assert "avg_deep_resonance" in status
        assert "level_distribution" in status
        assert "strongest_pair" in status
        assert status["indexed_repo_count"] == len(status["indexed_repos"])

    def test_get_status_strongest_pair_fields(self):
        engine = CrossRepoCodeResonance()
        status = engine.get_status()
        sp = status["strongest_pair"]
        assert sp is not None
        assert "repo_a" in sp
        assert "repo_b" in sp
        assert "score" in sp
        assert "level" in sp
        assert "components" in sp

    def test_singleton(self):
        engine1 = get_cross_repo_code_resonance()
        engine2 = get_cross_repo_code_resonance()
        assert engine1 is engine2

    def test_index_invalidates_cache(self):
        engine = CrossRepoCodeResonance()
        # First compute
        r1 = engine.compute_deep_resonance("omni-hub", "vci-ucif2")
        assert r1["score"] > 0
        # Re-index one repo with different patterns
        engine.index_repo_patterns(
            "vci-ucif2",
            {
                "architecture_style": "framework",  # changed from distributed
                "design_patterns": ["singleton", "observer"],
                "code_organization": "modular",
                "testing_strategy": "comprehensive",
                "documentation_level": 0.7,
            },
        )
        r2 = engine.compute_deep_resonance("omni-hub", "vci-ucif2")
        # Score should be lower now because architecture no longer matches
        assert r2["score"] < r1["score"]

    def test_simulated_patterns_coverage(self):
        """All simulated patterns should have required keys."""
        required_keys = [
            "architecture_style",
            "design_patterns",
            "code_organization",
            "testing_strategy",
            "documentation_level",
        ]
        for repo_name, patterns in SIMULATED_PATTERNS.items():
            for key in required_keys:
                assert key in patterns, f"Missing {key} in {repo_name}"

    def test_resonance_level_distribution_valid(self):
        engine = CrossRepoCodeResonance()
        resonance_map = engine.build_code_resonance_map()
        valid_levels = {"soulmate", "kindred", "similar", "acquainted", "stranger"}
        for level in resonance_map["level_distribution"]:
            assert level in valid_levels
