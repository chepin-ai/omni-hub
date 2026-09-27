"""
Tests for OMNI-HUB Module v147: Repository Resonance (仓库共振)
"""

import pytest
from typing import Any, Dict

from core.repo_resonance import (
    RepoResonance,
    ResonanceLevel,
    get_repo_resonance,
    _module,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    global _module
    _module = None
    yield
    _module = None


@pytest.fixture
def fresh_resonance() -> RepoResonance:
    """Return a fresh RepoResonance instance (not the singleton)."""
    return RepoResonance()


# ---------------------------------------------------------------------------
# ResonanceLevel tests
# ---------------------------------------------------------------------------
def test_resonance_level_entangled() -> None:
    assert ResonanceLevel.from_score(0.95) == ResonanceLevel.ENTANGLED
    assert ResonanceLevel.from_score(0.91) == ResonanceLevel.ENTANGLED
    assert ResonanceLevel.from_score(1.0) == ResonanceLevel.ENTANGLED


def test_resonance_level_harmonic() -> None:
    assert ResonanceLevel.from_score(0.85) == ResonanceLevel.HARMONIC
    assert ResonanceLevel.from_score(0.71) == ResonanceLevel.HARMONIC


def test_resonance_level_resonant() -> None:
    assert ResonanceLevel.from_score(0.55) == ResonanceLevel.RESONANT
    assert ResonanceLevel.from_score(0.41) == ResonanceLevel.RESONANT


def test_resonance_level_discordant() -> None:
    assert ResonanceLevel.from_score(0.4) == ResonanceLevel.DISCORDANT
    assert ResonanceLevel.from_score(0.0) == ResonanceLevel.DISCORDANT
    assert ResonanceLevel.from_score(-0.1) == ResonanceLevel.DISCORDANT


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------
def test_singleton_returns_same_instance() -> None:
    a = get_repo_resonance()
    b = get_repo_resonance()
    assert a is b


def test_singleton_is_repo_resonance() -> None:
    inst = get_repo_resonance()
    assert isinstance(inst, RepoResonance)


# ---------------------------------------------------------------------------
# register_pattern tests
# ---------------------------------------------------------------------------
def test_register_pattern_basic(fresh_resonance: RepoResonance) -> None:
    pattern: Dict[str, Any] = {
        "architecture": ["microservices", "event-driven"],
        "philosophy": ["clean-code", "ddd"],
    }
    result = fresh_resonance.register_pattern("repo-alpha", pattern)
    assert result["repo_name"] == "repo-alpha"
    assert "architecture" in result["registered_keys"]
    assert result["total_patterns"] == 1


def test_register_pattern_multiple(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["layered"]})
    fresh_resonance.register_pattern("repo-a", {"testing": ["tdd", "unit"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["hexagonal"]})
    assert len(fresh_resonance.resonance_patterns) == 3
    assert len(fresh_resonance.frequency_map) == 2


def test_register_pattern_invalid_repo_name(fresh_resonance: RepoResonance) -> None:
    with pytest.raises(ValueError):
        fresh_resonance.register_pattern("", {"architecture": ["layered"]})
    with pytest.raises(ValueError):
        fresh_resonance.register_pattern(None, {"architecture": ["layered"]})  # type: ignore


def test_register_pattern_invalid_pattern(fresh_resonance: RepoResonance) -> None:
    with pytest.raises(ValueError):
        fresh_resonance.register_pattern("repo-a", None)  # type: ignore
    with pytest.raises(ValueError):
        fresh_resonance.register_pattern("repo-a", "not-a-dict")  # type: ignore


# ---------------------------------------------------------------------------
# detect_resonance tests
# ---------------------------------------------------------------------------
def test_detect_resonance_identical_repos(fresh_resonance: RepoResonance) -> None:
    pattern = {
        "architecture": ["microservices"],
        "philosophy": ["clean-code"],
    }
    fresh_resonance.register_pattern("repo-a", pattern)
    result = fresh_resonance.detect_resonance("repo-a", "repo-a")
    assert result["resonance_score"] == 1.0
    assert result["level"] == ResonanceLevel.ENTANGLED


def test_detect_resonance_no_patterns(fresh_resonance: RepoResonance) -> None:
    result = fresh_resonance.detect_resonance("repo-x", "repo-y")
    assert result["resonance_score"] == 0.0
    assert result["level"] == ResonanceLevel.DISCORDANT


def test_detect_resonance_partial_overlap(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {
        "architecture": ["microservices", "event-driven"],
        "philosophy": ["clean-code"],
        "structure": ["modular"],
    })
    fresh_resonance.register_pattern("repo-b", {
        "architecture": ["microservices", "monolith"],
        "philosophy": ["clean-code", "ddd"],
        "structure": ["modular"],
    })
    result = fresh_resonance.detect_resonance("repo-a", "repo-b")
    assert result["resonance_score"] > 0.0
    assert result["level"] in (ResonanceLevel.RESONANT, ResonanceLevel.HARMONIC, ResonanceLevel.ENTANGLED)
    assert "architecture" in result["key_scores"]
    assert "philosophy" in result["key_scores"]
    assert "structure" in result["key_scores"]


def test_detect_resonance_entangled(fresh_resonance: RepoResonance) -> None:
    pattern = {
        "architecture": ["microservices"],
        "philosophy": ["clean-code"],
        "structure": ["modular"],
        "naming": ["kebab-case"],
        "testing": ["tdd"],
    }
    fresh_resonance.register_pattern("repo-a", pattern)
    fresh_resonance.register_pattern("repo-b", pattern)
    result = fresh_resonance.detect_resonance("repo-a", "repo-b")
    assert result["resonance_score"] == 1.0
    assert result["level"] == ResonanceLevel.ENTANGLED
    assert set(result["matched_keys"]) == set(pattern.keys())


def test_detect_resonance_discordant(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["monolith"]})
    result = fresh_resonance.detect_resonance("repo-a", "repo-b")
    assert result["resonance_score"] == 0.0
    assert result["level"] == ResonanceLevel.DISCORDANT


def test_detect_resonance_invalid_input(fresh_resonance: RepoResonance) -> None:
    with pytest.raises(ValueError):
        fresh_resonance.detect_resonance("", "repo-b")
    with pytest.raises(ValueError):
        fresh_resonance.detect_resonance("repo-a", "")


# ---------------------------------------------------------------------------
# sync_resonance tests
# ---------------------------------------------------------------------------
def test_sync_resonance_basic(fresh_resonance: RepoResonance) -> None:
    pattern = {
        "architecture": ["microservices"],
        "philosophy": ["clean-code"],
    }
    fresh_resonance.register_pattern("repo-a", pattern)
    fresh_resonance.register_pattern("repo-b", pattern)
    result = fresh_resonance.sync_resonance("repo-a")
    assert result["status"] == "synced"
    assert result["partner"] == "repo-b"
    assert result["level"] == ResonanceLevel.ENTANGLED
    assert "architecture" in result["merged_keys"]
    assert "philosophy" in result["merged_keys"]


def test_sync_resonance_no_patterns(fresh_resonance: RepoResonance) -> None:
    result = fresh_resonance.sync_resonance("repo-x")
    assert result["status"] == "no_patterns"
    assert result["partner"] is None


def test_sync_resonance_insufficient_repos(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"]})
    result = fresh_resonance.sync_resonance("repo-a")
    assert result["status"] == "insufficient_repos"
    assert result["partner"] is None


def test_sync_resonance_picks_best_partner(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"], "philosophy": ["clean-code"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["microservices"], "philosophy": ["clean-code"]})
    fresh_resonance.register_pattern("repo-c", {"architecture": ["monolith"], "philosophy": ["quick-and-dirty"]})
    result = fresh_resonance.sync_resonance("repo-a")
    assert result["partner"] == "repo-b"
    assert result["resonance_score"] == 1.0
    assert result["level"] == ResonanceLevel.ENTANGLED


def test_sync_resonance_invalid_input(fresh_resonance: RepoResonance) -> None:
    with pytest.raises(ValueError):
        fresh_resonance.sync_resonance("")


# ---------------------------------------------------------------------------
# get_resonance_matrix tests
# ---------------------------------------------------------------------------
def test_get_resonance_matrix_empty(fresh_resonance: RepoResonance) -> None:
    matrix = fresh_resonance.get_resonance_matrix()
    assert matrix["repos"] == []
    assert matrix["pair_count"] == 0
    assert matrix["matrix"] == {}


def test_get_resonance_matrix_two_repos(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["microservices"]})
    matrix = fresh_resonance.get_resonance_matrix()
    assert matrix["repos"] == ["repo-a", "repo-b"]
    assert matrix["pair_count"] == 1
    key = "repo-a::repo-b"
    assert key in matrix["matrix"]
    assert matrix["matrix"][key]["score"] == 1.0
    assert matrix["matrix"][key]["level"] == ResonanceLevel.ENTANGLED


def test_get_resonance_matrix_three_repos(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["microservices"]})
    fresh_resonance.register_pattern("repo-c", {"architecture": ["monolith"]})
    matrix = fresh_resonance.get_resonance_matrix()
    assert matrix["pair_count"] == 3
    assert len(matrix["matrix"]) == 3


# ---------------------------------------------------------------------------
# get_status tests
# ---------------------------------------------------------------------------
def test_get_status_empty(fresh_resonance: RepoResonance) -> None:
    status = fresh_resonance.get_status()
    assert status["pattern_count"] == 0
    assert status["repo_count"] == 0
    assert status["resonance_pairs"] == 0
    assert status["strongest_resonance"] is None
    assert status["module"] == "repo_resonance"
    assert status["version"] == 147


def test_get_status_with_data(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"], "philosophy": ["clean-code"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["microservices"], "philosophy": ["clean-code"]})
    fresh_resonance.register_pattern("repo-c", {"architecture": ["monolith"], "philosophy": ["hacky"]})
    status = fresh_resonance.get_status()
    assert status["pattern_count"] == 3
    assert status["repo_count"] == 3
    assert status["resonance_pairs"] == 3
    assert status["strongest_resonance"] is not None
    assert status["strongest_resonance"]["pair"] == ("repo-a", "repo-b")
    assert status["strongest_resonance"]["score"] == 1.0
    assert status["strongest_resonance"]["level"] == ResonanceLevel.ENTANGLED


def test_get_status_after_sync(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["monolith"]})
    fresh_resonance.sync_resonance("repo-a")
    status = fresh_resonance.get_status()
    assert status["pattern_count"] == 2
    assert status["repo_count"] == 2
    assert status["resonance_pairs"] == 1


# ---------------------------------------------------------------------------
# Internal helper tests
# ---------------------------------------------------------------------------
def test_jaccard_both_empty(fresh_resonance: RepoResonance) -> None:
    assert fresh_resonance._jaccard(set(), set()) == 1.0


def test_jaccard_one_empty(fresh_resonance: RepoResonance) -> None:
    assert fresh_resonance._jaccard({"a", "b"}, set()) == 0.0


def test_jaccard_identical(fresh_resonance: RepoResonance) -> None:
    assert fresh_resonance._jaccard({"a", "b"}, {"a", "b"}) == 1.0


def test_jaccard_partial(fresh_resonance: RepoResonance) -> None:
    assert fresh_resonance._jaccard({"a", "b"}, {"b", "c"}) == 1 / 3


def test_to_set(fresh_resonance: RepoResonance) -> None:
    assert fresh_resonance._to_set(["a", "b"]) == {"a", "b"}
    assert fresh_resonance._to_set({"a", "b"}) == {"a", "b"}
    assert fresh_resonance._to_set("hello") == {"hello"}
    assert fresh_resonance._to_set(None) == set()


# ---------------------------------------------------------------------------
# Caching tests
# ---------------------------------------------------------------------------
def test_cache_invalidation(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {"architecture": ["microservices"]})
    fresh_resonance.register_pattern("repo-b", {"architecture": ["microservices"]})
    result1 = fresh_resonance.detect_resonance("repo-a", "repo-b")
    result2 = fresh_resonance.detect_resonance("repo-a", "repo-b")
    assert result1 == result2
    # After registering new pattern, cache should be invalidated
    fresh_resonance.register_pattern("repo-a", {"architecture": ["event-driven"]})
    result3 = fresh_resonance.detect_resonance("repo-a", "repo-b")
    assert result3["resonance_score"] != result1["resonance_score"]


# ---------------------------------------------------------------------------
# Edge case: register with various value types
# ---------------------------------------------------------------------------
def test_register_pattern_various_value_types(fresh_resonance: RepoResonance) -> None:
    fresh_resonance.register_pattern("repo-a", {
        "architecture": "monolith",
        "philosophy": ["clean-code", "ddd"],
        "structure": {"modular", "layered"},
        "naming": None,
        "testing": ("tdd", "bdd"),
    })
    agg = fresh_resonance._aggregate_repo_patterns("repo-a")
    assert "monolith" in agg["architecture"]
    assert "clean-code" in agg["philosophy"]
    assert "modular" in agg["structure"]
    assert "naming" not in agg or agg["naming"] == set()
    assert "tdd" in agg["testing"]
    assert "bdd" in agg["testing"]
