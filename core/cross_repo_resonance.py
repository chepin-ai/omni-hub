"""
OMNI-HUB v153: Cross-Repo Resonance Engine (跨仓共振引擎)

Computes resonance frequencies between repositories based on real metadata.
Language match, update recency proximity, role complementarity, and line affinity
create a quantum resonance field across all alliance repositories.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

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

RESONANCE_LEVELS = [
    (0.9, "quantum"),
    (0.7, "entangled"),
    (0.5, "resonant"),
    (0.3, "weak"),
]

# Role complementarity pairs: (role_a, role_b) -> complementarity bonus applies
ROLE_COMPLEMENT_PAIRS: set = {
    ("framework", "library"),
    ("framework", "sdk"),
    ("framework", "worker"),
    ("ml", "library"),
    ("ml", "dl"),
    ("ml", "research"),
    ("dl", "framework"),
    ("navigation", "control"),
    ("navigation", "worker"),
    ("synthesis", "research"),
    ("synthesis", "ml"),
    ("worker", "yard"),
    ("worker", "inbox"),
    ("inbox", "control"),
    ("inbox", "worker"),
    ("root", "code"),
    ("root", "library"),
    ("bus", "logs"),
    ("bus", "control"),
    ("playground", "library"),
    ("playground", "framework"),
    ("code", "library"),
    ("control", "worker"),
    ("control", "navigation"),
    ("research", "ml"),
    ("research", "synthesis"),
    ("logs", "bus"),
    ("sdk", "framework"),
    ("sdk", "library"),
    ("library", "framework"),
    ("library", "ml"),
    ("library", "playground"),
    ("library", "root"),
    ("library", "code"),
    ("library", "sdk"),
    ("dl", "ml"),
    ("yard", "worker"),
}

WEIGHT_LANGUAGE = 0.4
WEIGHT_RECENCY = 0.3
WEIGHT_ROLE = 0.2
WEIGHT_LINE = 0.1

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _days_between(a: Optional[str], b: Optional[str]) -> Optional[float]:
    """Return absolute days between two date strings, or None."""
    da = _parse_date(a)
    db = _parse_date(b)
    if da is None or db is None:
        return None
    return abs((da - db).total_seconds()) / 86400.0


def _get_level(score: float) -> str:
    """Map resonance score to level name."""
    for threshold, name in RESONANCE_LEVELS:
        if score >= threshold:
            return name
    return "silent"


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------

class CrossRepoResonance:
    """
    Cross-Repository Resonance Engine.

    Loads real repository metadata and computes pairwise resonance scores.
    """

    def __init__(self, data_path: Optional[str] = None) -> None:
        self.data_path = data_path or REPO_DATA_PATH
        self.repos: Dict[str, Dict[str, Any]] = {}
        self._resonance_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._load_repos()

    def _load_repos(self) -> None:
        """Load repository metadata from alliance_repos.json."""
        try:
            with open(self.data_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            # Defensive: if data file is missing, start empty but log
            self.repos = {}
            self._emit_event("resonance_load_failed", {"error": str(exc)})
            return

        # Flatten all categories into a single repo map
        for category, repo_map in raw.items():
            if not isinstance(repo_map, dict):
                continue
            for repo_name, meta in repo_map.items():
                if isinstance(meta, dict):
                    self.repos[repo_name] = dict(meta)
                    self.repos[repo_name]["_category"] = category

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit event via event_bus if available."""
        if event_bus is not None:
            try:
                event_bus.emit(event_type, payload)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Resonance computation
    # ------------------------------------------------------------------

    def compute_resonance(self, repo_a: str, repo_b: str) -> Dict[str, Any]:
        """
        Compute resonance score (0-1) between two repositories.

        Factors:
        - Language match: +0.4 if same non-null language
        - Update recency proximity: +0.3 if updated within 7 days
        - Role complementarity: +0.2 if roles are complementary
        - Line affinity: +0.1 if both are 11-line repos (have 'line' field)
        """
        if repo_a == repo_b:
            return {
                "repo_a": repo_a,
                "repo_b": repo_b,
                "score": 1.0,
                "level": "quantum",
                "factors": {},
            }

        cache_key = tuple(sorted((repo_a, repo_b)))
        if cache_key in self._resonance_cache:
            return dict(self._resonance_cache[cache_key])

        meta_a = self.repos.get(repo_a, {})
        meta_b = self.repos.get(repo_b, {})

        # Guard against unknown repos
        if not meta_a or not meta_b:
            result = {
                "repo_a": repo_a,
                "repo_b": repo_b,
                "score": 0.0,
                "level": "silent",
                "factors": {"error": "unknown repository"},
            }
            self._resonance_cache[cache_key] = result
            return dict(result)

        factors: Dict[str, float] = {}

        # 1. Language match
        lang_a = meta_a.get("lang")
        lang_b = meta_b.get("lang")
        if lang_a and lang_b and lang_a == lang_b:
            factors["language_match"] = WEIGHT_LANGUAGE
        else:
            factors["language_match"] = 0.0

        # 2. Update recency proximity
        updated_a = meta_a.get("updated")
        updated_b = meta_b.get("updated")
        days = _days_between(updated_a, updated_b)
        if days is not None and days <= 7.0:
            factors["update_proximity"] = WEIGHT_RECENCY
        else:
            factors["update_proximity"] = 0.0

        # 3. Role complementarity
        role_a = meta_a.get("role")
        role_b = meta_b.get("role")
        if role_a and role_b:
            if (role_a, role_b) in ROLE_COMPLEMENT_PAIRS or (
                role_b,
                role_a,
            ) in ROLE_COMPLEMENT_PAIRS:
                factors["role_complementarity"] = WEIGHT_ROLE
            else:
                factors["role_complementarity"] = 0.0
        else:
            factors["role_complementarity"] = 0.0

        # 4. Line affinity (both have 'line' field => 11-line repos)
        line_a = meta_a.get("line")
        line_b = meta_b.get("line")
        if line_a is not None and line_b is not None:
            factors["line_affinity"] = WEIGHT_LINE
        else:
            factors["line_affinity"] = 0.0

        score = sum(factors.values())
        score = round(min(max(score, 0.0), 1.0), 4)
        level = _get_level(score)

        result = {
            "repo_a": repo_a,
            "repo_b": repo_b,
            "score": score,
            "level": level,
            "factors": factors,
        }
        self._resonance_cache[cache_key] = result
        return dict(result)

    # ------------------------------------------------------------------
    # Partner discovery
    # ------------------------------------------------------------------

    def find_resonant_partners(
        self, repo_name: str, threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find all repositories that resonate with *repo_name* above *threshold*.
        Returns list sorted by descending resonance score.
        """
        if repo_name not in self.repos:
            return []

        partners: List[Dict[str, Any]] = []
        for other_name in self.repos:
            if other_name == repo_name:
                continue
            resonance = self.compute_resonance(repo_name, other_name)
            if resonance["score"] >= threshold:
                partners.append(resonance)

        partners.sort(key=lambda x: x["score"], reverse=True)
        return partners

    # ------------------------------------------------------------------
    # Web builder
    # ------------------------------------------------------------------

    def build_resonance_web(self) -> Dict[str, Any]:
        """
        Build the full resonance web — a graph of all resonant pairs.
        """
        nodes = sorted(self.repos.keys())
        edges: List[Dict[str, Any]] = []
        scores: List[float] = []

        repo_list = list(nodes)
        n = len(repo_list)
        for i in range(n):
            for j in range(i + 1, n):
                resonance = self.compute_resonance(repo_list[i], repo_list[j])
                if resonance["score"] > 0.0:
                    edges.append(resonance)
                    scores.append(resonance["score"])

        # Count by level
        level_counts: Dict[str, int] = {
            "quantum": 0,
            "entangled": 0,
            "resonant": 0,
            "weak": 0,
            "silent": 0,
        }
        for edge in edges:
            level_counts[edge["level"]] = level_counts.get(edge["level"], 0) + 1

        avg_resonance = round(sum(scores) / len(scores), 4) if scores else 0.0

        # Strongest pair
        strongest: Optional[Dict[str, Any]] = None
        if edges:
            strongest = max(edges, key=lambda e: e["score"])

        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "level_distribution": level_counts,
            "avg_resonance": avg_resonance,
            "strongest_pair": strongest,
        }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """
        Return resonance pair count, average resonance, and strongest pair.
        """
        web = self.build_resonance_web()
        return {
            "repo_count": web["node_count"],
            "resonance_pair_count": web["edge_count"],
            "avg_resonance": web["avg_resonance"],
            "strongest_pair": web["strongest_pair"],
            "level_distribution": web["level_distribution"],
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_module: Optional[CrossRepoResonance] = None


def get_cross_repo_resonance() -> CrossRepoResonance:
    """Global singleton accessor for CrossRepoResonance."""
    global _module
    if _module is None:
        _module = CrossRepoResonance()
    return _module


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v153 CROSS-REPO RESONANCE ENGINE")
    print("=" * 70)

    engine = CrossRepoResonance()
    status = engine.get_status()
    print(f"\nResonance Web Status:")
    print(f"  Repositories: {status['repo_count']}")
    print(f"  Resonance pairs: {status['resonance_pair_count']}")
    print(f"  Average resonance: {status['avg_resonance']:.4f}")
    print(f"  Level distribution: {status['level_distribution']}")

    if status["strongest_pair"]:
        sp = status["strongest_pair"]
        print(f"\nStrongest Pair:")
        print(f"  {sp['repo_a']} <-> {sp['repo_b']}: {sp['score']:.4f} ({sp['level']})")

    # Sample: find partners for omni-hub
    partners = engine.find_resonant_partners("omni-hub", threshold=0.3)
    print(f"\nResonant partners of 'omni-hub' (threshold=0.3): {len(partners)}")
    for p in partners[:5]:
        print(f"  {p['repo_b']}: {p['score']:.4f} ({p['level']})")

    print(f"\n{'='*70}")
