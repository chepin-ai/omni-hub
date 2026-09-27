"""
Tests for Alliance Scanner (联盟扫描器) — OMNI-HUB Module v151
"""

import os
import sys
import json
import pytest
from typing import Dict, List, Any

# Ensure core/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.alliance_scanner import (
    AllianceScanner,
    get_alliance_scanner,
    LINE_MAPPING,
    NON_LINE_REPOS,
    EXTERNAL_REPOS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scanner() -> AllianceScanner:
    """Provide a fresh AllianceScanner instance."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base, "data", "alliance_repos.json")
    return AllianceScanner(data_path=data_path)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    import core.alliance_scanner as _mod
    _mod._module = None
    yield
    _mod._module = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAllianceScanner:
    """Comprehensive tests for AllianceScanner."""

    # -- scan_alliance ------------------------------------------------------

    def test_scan_alliance_structure(self, scanner: AllianceScanner) -> None:
        """scan_alliance must return dict with the three expected keys."""
        result = scanner.scan_alliance()
        assert isinstance(result, dict)
        assert "core_lines" in result
        assert "other_alliance" in result
        assert "external" in result

    def test_scan_alliance_core_lines_count(self, scanner: AllianceScanner) -> None:
        """core_lines must contain the 11 line repos + omni-hub."""
        result = scanner.scan_alliance()
        core_names = [r["name"] for r in result["core_lines"]]
        for repo_name in LINE_MAPPING.values():
            assert repo_name in core_names
        assert "omni-hub" in core_names

    def test_scan_alliance_other_count(self, scanner: AllianceScanner) -> None:
        """other_alliance must contain all non-line repos."""
        result = scanner.scan_alliance()
        other_names = {r["name"] for r in result["other_alliance"]}
        for repo_name in NON_LINE_REPOS:
            assert repo_name in other_names

    def test_scan_alliance_external_count(self, scanner: AllianceScanner) -> None:
        """external must contain all external repos."""
        result = scanner.scan_alliance()
        ext_names = {r["name"] for r in result["external"]}
        for repo_name in EXTERNAL_REPOS:
            assert repo_name in ext_names

    def test_scan_alliance_repo_has_name(self, scanner: AllianceScanner) -> None:
        """Every returned repo dict must include a 'name' key."""
        result = scanner.scan_alliance()
        for category in ("core_lines", "other_alliance", "external"):
            for repo in result[category]:
                assert "name" in repo
                assert isinstance(repo["name"], str)

    # -- find_line_repos ----------------------------------------------------

    def test_find_line_repos_keys(self, scanner: AllianceScanner) -> None:
        """find_line_repos must return exactly the 11 line keys."""
        result = scanner.find_line_repos()
        assert set(result.keys()) == set(LINE_MAPPING.keys())

    def test_find_line_repos_values(self, scanner: AllianceScanner) -> None:
        """Each line key must map to the correct repo name."""
        result = scanner.find_line_repos()
        for line_key, repo_name in LINE_MAPPING.items():
            assert result[line_key]["name"] == repo_name

    def test_find_line_repos_has_desc(self, scanner: AllianceScanner) -> None:
        """Each line repo entry must have a description."""
        result = scanner.find_line_repos()
        for info in result.values():
            assert "desc" in info
            assert isinstance(info["desc"], str)

    # -- find_non_line_repos ------------------------------------------------

    def test_find_non_line_repos_count(self, scanner: AllianceScanner) -> None:
        """find_non_line_repos must return exactly the expected count."""
        result = scanner.find_non_line_repos()
        assert len(result) == len(NON_LINE_REPOS)

    def test_find_non_line_repos_names(self, scanner: AllianceScanner) -> None:
        """All returned non-line repos must match the expected list."""
        result = scanner.find_non_line_repos()
        names = [r["name"] for r in result]
        assert names == NON_LINE_REPOS

    def test_find_non_line_repos_no_line_overlap(self, scanner: AllianceScanner) -> None:
        """Non-line repos must not overlap with line repos."""
        result = scanner.find_non_line_repos()
        line_repo_names = set(LINE_MAPPING.values())
        for repo in result:
            assert repo["name"] not in line_repo_names

    def test_find_non_line_repos_activation_targets(self, scanner: AllianceScanner) -> None:
        """All known activation targets must be present in non-line repos."""
        result = scanner.find_non_line_repos()
        names = {r["name"] for r in result}
        activation_targets = set(NON_LINE_REPOS)
        assert activation_targets.issubset(names)

    # -- get_repo_info ------------------------------------------------------

    def test_get_repo_info_core(self, scanner: AllianceScanner) -> None:
        """get_repo_info must return correct data for a core line repo."""
        info = scanner.get_repo_info("vci-ucif2")
        assert info["name"] == "vci-ucif2"
        assert info["category"] == "core_lines"
        assert "line" in info

    def test_get_repo_info_other(self, scanner: AllianceScanner) -> None:
        """get_repo_info must return correct data for an other-alliance repo."""
        info = scanner.get_repo_info("vci-inbox")
        assert info["name"] == "vci-inbox"
        assert info["category"] == "other_alliance"
        assert "role" in info

    def test_get_repo_info_external(self, scanner: AllianceScanner) -> None:
        """get_repo_info must return correct data for an external repo."""
        info = scanner.get_repo_info("langchain-ai/langchain")
        assert info["name"] == "langchain-ai/langchain"
        assert info["category"] == "external"
        assert "role" in info

    def test_get_repo_info_missing(self, scanner: AllianceScanner) -> None:
        """get_repo_info must return empty dict for unknown repo."""
        info = scanner.get_repo_info("nonexistent-repo")
        assert info == {}

    # -- get_status ---------------------------------------------------------

    def test_get_status_keys(self, scanner: AllianceScanner) -> None:
        """get_status must return the four expected keys."""
        status = scanner.get_status()
        assert "total_repos" in status
        assert "line_repos" in status
        assert "non_line_repos" in status
        assert "external_repos" in status

    def test_get_status_values(self, scanner: AllianceScanner) -> None:
        """get_status must return correct numeric values."""
        status = scanner.get_status()
        assert status["line_repos"] == 11
        assert status["non_line_repos"] == len(NON_LINE_REPOS)
        assert status["external_repos"] == len(EXTERNAL_REPOS)
        # total_repos reflects actual data count (core includes omni-hub = 12)
        assert status["total_repos"] == 33

    def test_get_status_types(self, scanner: AllianceScanner) -> None:
        """All status values must be integers."""
        status = scanner.get_status()
        for v in status.values():
            assert isinstance(v, int)

    # -- singleton ----------------------------------------------------------

    def test_singleton_returns_same_instance(self) -> None:
        """get_alliance_scanner must return the same object on repeated calls."""
        s1 = get_alliance_scanner()
        s2 = get_alliance_scanner()
        assert s1 is s2

    def test_singleton_is_alliance_scanner(self) -> None:
        """get_alliance_scanner must return an AllianceScanner instance."""
        s = get_alliance_scanner()
        assert isinstance(s, AllianceScanner)

    # -- edge / defensive ---------------------------------------------------

    def test_load_missing_file(self, tmp_path) -> None:
        """Scanner must gracefully handle a missing data file."""
        missing = str(tmp_path / "missing.json")
        s = AllianceScanner(data_path=missing)
        assert s.get_status()["total_repos"] == 0
        assert s.get_repo_info("anything") == {}
