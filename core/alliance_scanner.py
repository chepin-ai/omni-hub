"""
Alliance Scanner (联盟扫描器) — OMNI-HUB Module v151

Scans and categorizes repositories within and around the chepin-ai alliance.
Distinguishes 11-line core repos, other alliance repos, and external repos.
Builds a complete alliance repository graph.
"""

import json
import os
from typing import Dict, List, Any, Optional

# ---------------------------------------------------------------------------
# 11 Lines mapping: line_key → repo_name
# ---------------------------------------------------------------------------
LINE_MAPPING: Dict[str, str] = {
    "ucif2": "vci-ucif2",
    "lvlu": "vci-lvlu",
    "lgt": "vci-lgt",
    "qfa": "vci-qfa",
    "vinf": "vci-vinf",
    "qgl": "vci-qgl",
    "qlv": "vci-qlv",
    "qtlv": "vci-qtlv",
    "usrm": "vci-usrm",
    "cfts": "vci-cfts",
    "aiq": "vci-aiq",
}

# Non-line repos that are activation targets
NON_LINE_REPOS: List[str] = [
    "vci-inbox",
    "ci-worker-01",
    "qlv-lib",
    "lgt-worker-01",
    "ci-yard",
    "vci-control",
    "qfos-autonomous-engine",
    "grand-synthesis",
    "prima-50-research",
    "ci-worker-02",
    "vci-library",
    "vci-playground",
    "vci-root",
    "vci-logs",
    "vci-code",
    "vci-bus",
]

# External alliance repos
EXTERNAL_REPOS: List[str] = [
    "langchain-ai/langchain",
    "microsoft/semantic-kernel",
    "openai/openai-python",
    "huggingface/transformers",
    "pytorch/pytorch",
]

# Global singleton instance
_module: Optional["AllianceScanner"] = None


def get_alliance_scanner(data_path: Optional[str] = None) -> "AllianceScanner":
    """Return the global AllianceScanner singleton."""
    global _module
    if _module is None:
        _module = AllianceScanner(data_path=data_path)
    return _module


class AllianceScanner:
    """
    Alliance Scanner that loads alliance repository data and provides
    categorization and lookup utilities.
    """

    def __init__(self, data_path: Optional[str] = None) -> None:
        """
        Load alliance_repos.json into memory.

        Args:
            data_path: Path to the JSON data file. If None, use default.
        """
        if data_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base, "data", "alliance_repos.json")

        self._data_path = data_path
        self._data: Dict[str, Any] = {}
        self._core: Dict[str, Any] = {}
        self._other: Dict[str, Any] = {}
        self._external: Dict[str, Any] = {}
        self._all_repos: Dict[str, Any] = {}

        self._load_data()

    def _load_data(self) -> None:
        """Load and index the alliance repository data."""
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            self._data = {
                "alliance_core": {},
                "alliance_other": {},
                "external_alliance": {},
            }

        self._core = self._data.get("alliance_core", {})
        self._other = self._data.get("alliance_other", {})
        self._external = self._data.get("external_alliance", {})

        # Build unified lookup index
        self._all_repos = {}
        for repo_name, info in self._core.items():
            self._all_repos[repo_name] = {**info, "category": "core_lines"}
        for repo_name, info in self._other.items():
            self._all_repos[repo_name] = {**info, "category": "other_alliance"}
        for repo_name, info in self._external.items():
            self._all_repos[repo_name] = {**info, "category": "external"}

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def scan_alliance(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return all alliance repos categorized into three groups.

        Returns:
            Dict with keys 'core_lines', 'other_alliance', 'external'.
            Each value is a list of repo dicts with 'name' added.
        """
        result: Dict[str, List[Dict[str, Any]]] = {
            "core_lines": [],
            "other_alliance": [],
            "external": [],
        }
        for repo_name, info in self._core.items():
            result["core_lines"].append({"name": repo_name, **info})
        for repo_name, info in self._other.items():
            result["other_alliance"].append({"name": repo_name, **info})
        for repo_name, info in self._external.items():
            result["external"].append({"name": repo_name, **info})
        return result

    def find_line_repos(self) -> Dict[str, Dict[str, Any]]:
        """
        Return which repo belongs to which of the 11 lines.

        Returns:
            Dict mapping line_key → repo info dict (with 'name').
        """
        result: Dict[str, Dict[str, Any]] = {}
        for line_key, repo_name in LINE_MAPPING.items():
            info = self._core.get(repo_name, {})
            result[line_key] = {"name": repo_name, **info}
        return result

    def find_non_line_repos(self) -> List[Dict[str, Any]]:
        """
        Return all repos NOT part of the 11 lines (activation targets).

        Returns:
            List of repo dicts (with 'name') for non-line alliance repos.
        """
        result: List[Dict[str, Any]] = []
        for repo_name in NON_LINE_REPOS:
            info = self._other.get(repo_name, {})
            result.append({"name": repo_name, **info})
        return result

    def get_repo_info(self, repo_name: str) -> Dict[str, Any]:
        """
        Return detailed info for a specific repo.

        Args:
            repo_name: Name of the repository.

        Returns:
            Repo info dict with 'name' and 'category', or empty dict if not found.
        """
        info = self._all_repos.get(repo_name, {})
        if not info:
            return {}
        return {"name": repo_name, **info}

    def get_status(self) -> Dict[str, int]:
        """
        Return summary counts.

        Returns:
            Dict with keys:
                total_repos, line_repos, non_line_repos, external_repos.
        """
        return {
            "total_repos": len(self._all_repos),
            "line_repos": len(LINE_MAPPING),
            "non_line_repos": len(NON_LINE_REPOS),
            "external_repos": len(EXTERNAL_REPOS),
        }
