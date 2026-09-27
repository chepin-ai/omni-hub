"""
OMNI-HUB v153: Cross-Repo Resonance Tests (跨仓共振引擎测试)
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.cross_repo_resonance import (
    CrossRepoResonance,
    get_cross_repo_resonance,
    _parse_date,
    _days_between,
    _get_level,
    WEIGHT_LANGUAGE,
    WEIGHT_RECENCY,
    WEIGHT_ROLE,
    WEIGHT_LINE,
)


class TestHelpers:
    def test_parse_date_valid(self):
        dt = _parse_date("2026-09-27")
        assert dt is not None
        assert dt.year == 2026

    def test_parse_date_none(self):
        assert _parse_date(None) is None

    def test_parse_date_invalid(self):
        assert _parse_date("not-a-date") is None

    def test_days_between_same(self):
        assert _days_between("2026-09-27", "2026-09-27") == 0.0

    def test_days_between_different(self):
        days = _days_between("2026-09-20", "2026-09-27")
        assert days == 7.0

    def test_days_between_none(self):
        assert _days_between("2026-09-27", None) is None

    def test_get_level_quantum(self):
        assert _get_level(0.95) == "quantum"

    def test_get_level_entangled(self):
        assert _get_level(0.85) == "entangled"

    def test_get_level_resonant(self):
        assert _get_level(0.55) == "resonant"

    def test_get_level_weak(self):
        assert _get_level(0.35) == "weak"

    def test_get_level_silent(self):
        assert _get_level(0.15) == "silent"


class TestCrossRepoResonance:
    def test_initialization_loads_repos(self):
        engine = CrossRepoResonance()
        assert len(engine.repos) > 0
        assert "omni-hub" in engine.repos
        assert "vci-ucif2" in engine.repos

    def test_compute_resonance_same_repo(self):
        engine = CrossRepoResonance()
        result = engine.compute_resonance("omni-hub", "omni-hub")
        assert result["score"] == 1.0
        assert result["level"] == "quantum"

    def test_compute_resonance_unknown_repo(self):
        engine = CrossRepoResonance()
        result = engine.compute_resonance("omni-hub", "nonexistent-repo")
        assert result["score"] == 0.0
        assert result["level"] == "silent"

    def test_compute_resonance_core_pair(self):
        """Two alliance_core repos: same lang, same update, both have line."""
        engine = CrossRepoResonance()
        result = engine.compute_resonance("vci-ucif2", "vci-lvlu")
        expected = WEIGHT_LANGUAGE + WEIGHT_RECENCY + WEIGHT_LINE
        assert result["score"] == pytest.approx(expected, abs=0.001)
        assert result["level"] == "entangled"
        assert result["factors"]["language_match"] == WEIGHT_LANGUAGE
        assert result["factors"]["update_proximity"] == WEIGHT_RECENCY
        assert result["factors"]["line_affinity"] == WEIGHT_LINE
        assert result["factors"]["role_complementarity"] == 0.0

    def test_compute_resonance_core_omni_hub(self):
        """omni-hub + vci-ucif2 should be high resonance (core pair)."""
        engine = CrossRepoResonance()
        result = engine.compute_resonance("omni-hub", "vci-ucif2")
        expected = WEIGHT_LANGUAGE + WEIGHT_RECENCY + WEIGHT_LINE
        assert result["score"] == pytest.approx(expected, abs=0.001)
        assert result["level"] == "entangled"

    def test_compute_resonance_complementary_roles(self):
        """vci-inbox (inbox) + ci-worker-01 (worker): same lang, same date, complementary roles."""
        engine = CrossRepoResonance()
        result = engine.compute_resonance("vci-inbox", "ci-worker-01")
        expected = WEIGHT_LANGUAGE + WEIGHT_RECENCY + WEIGHT_ROLE
        assert result["score"] == pytest.approx(expected, abs=0.001)
        assert result["level"] == "quantum"

    def test_compute_resonance_different_lang(self):
        """grand-synthesis (Lean) + vci-inbox (Python) -> no lang match."""
        engine = CrossRepoResonance()
        result = engine.compute_resonance("grand-synthesis", "vci-inbox")
        # Different languages, dates 8 days apart -> no proximity
        assert result["factors"]["language_match"] == 0.0
        assert result["factors"]["update_proximity"] == 0.0

    def test_compute_resonance_far_dates(self):
        """ci-worker-02 (2026-09-10) + vci-control (2026-09-25): >7 days apart."""
        engine = CrossRepoResonance()
        result = engine.compute_resonance("ci-worker-02", "vci-control")
        # Both have no lang (null), dates 15 days apart -> no proximity
        assert result["factors"]["update_proximity"] == 0.0

    def test_compute_resonance_caching(self):
        engine = CrossRepoResonance()
        r1 = engine.compute_resonance("vci-ucif2", "vci-lvlu")
        r2 = engine.compute_resonance("vci-lvlu", "vci-ucif2")
        assert r1["score"] == r2["score"]

    def test_find_resonant_partners_high_threshold(self):
        engine = CrossRepoResonance()
        partners = engine.find_resonant_partners("omni-hub", threshold=0.7)
        assert isinstance(partners, list)
        # omni-hub (core, Python, 2026-09-27) resonates with:
        # - all core repos at 0.8 (lang + date + line)
        # - alliance_other Python repos within 7 days at 0.7 (lang + date)
        # Compute expected count dynamically
        omni_meta = engine.repos["omni-hub"]
        expected_count = 0
        for name, meta in engine.repos.items():
            if name == "omni-hub":
                continue
            # same lang
            if meta.get("lang") == omni_meta.get("lang"):
                # within 7 days
                days = _days_between(meta.get("updated"), omni_meta.get("updated"))
                if days is not None and days <= 7.0:
                    expected_count += 1
        assert len(partners) == expected_count
        for p in partners:
            assert p["score"] >= 0.7

    def test_find_resonant_partners_low_threshold(self):
        engine = CrossRepoResonance()
        partners = engine.find_resonant_partners("omni-hub", threshold=0.3)
        assert len(partners) >= 0
        for p in partners:
            assert p["score"] >= 0.3

    def test_find_resonant_partners_sorted(self):
        engine = CrossRepoResonance()
        partners = engine.find_resonant_partners("omni-hub", threshold=0.3)
        scores = [p["score"] for p in partners]
        assert scores == sorted(scores, reverse=True)

    def test_find_resonant_partners_unknown_repo(self):
        engine = CrossRepoResonance()
        partners = engine.find_resonant_partners("unknown-repo-xyz")
        assert partners == []

    def test_build_resonance_web_structure(self):
        engine = CrossRepoResonance()
        web = engine.build_resonance_web()
        assert "node_count" in web
        assert "edge_count" in web
        assert "nodes" in web
        assert "edges" in web
        assert "avg_resonance" in web
        assert "strongest_pair" in web
        assert "level_distribution" in web
        assert web["node_count"] == len(engine.repos)
        assert web["edge_count"] == len(web["edges"])
        assert web["avg_resonance"] >= 0.0

    def test_build_resonance_web_strongest_pair(self):
        engine = CrossRepoResonance()
        web = engine.build_resonance_web()
        if web["strongest_pair"]:
            sp = web["strongest_pair"]
            assert "repo_a" in sp
            assert "repo_b" in sp
            assert "score" in sp
            assert sp["score"] > 0.0

    def test_build_resonance_web_level_distribution(self):
        engine = CrossRepoResonance()
        web = engine.build_resonance_web()
        dist = web["level_distribution"]
        total = sum(dist.values())
        assert total == web["edge_count"]

    def test_get_status(self):
        engine = CrossRepoResonance()
        status = engine.get_status()
        assert "repo_count" in status
        assert "resonance_pair_count" in status
        assert "avg_resonance" in status
        assert "strongest_pair" in status
        assert "level_distribution" in status
        assert status["repo_count"] > 0

    def test_status_and_web_consistent(self):
        engine = CrossRepoResonance()
        status = engine.get_status()
        web = engine.build_resonance_web()
        assert status["repo_count"] == web["node_count"]
        assert status["resonance_pair_count"] == web["edge_count"]
        assert status["avg_resonance"] == web["avg_resonance"]
        assert status["strongest_pair"] == web["strongest_pair"]


class TestGlobalSingleton:
    def test_get_cross_repo_resonance(self):
        g1 = get_cross_repo_resonance()
        g2 = get_cross_repo_resonance()
        assert g1 is g2
        assert isinstance(g1, CrossRepoResonance)
