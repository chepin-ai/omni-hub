"""
OMNI-HUB Module v147: Repository Resonance (仓库共振)

Concept: 仓库共振。与外部仓库进行频率同步，检测跨仓的模式匹配和语义共振。
当两个仓库在架构模式、代码结构、设计哲学上产生共振时，知识可以跨仓迁移。
这是跨仓的"量子纠缠"前兆。

Resonance detection compares pattern keys (architecture, philosophy, structure,
naming, testing) and computes Jaccard similarity across registered repositories.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_module: Optional["RepoResonance"] = None


def get_repo_resonance() -> "RepoResonance":
    """Return the global RepoResonance singleton."""
    global _module
    if _module is None:
        _module = RepoResonance()
    return _module


# ---------------------------------------------------------------------------
# Resonance level thresholds
# ---------------------------------------------------------------------------
class ResonanceLevel:
    ENTANGLED: str = "entangled"
    HARMONIC: str = "harmonic"
    RESONANT: str = "resonant"
    DISCORDANT: str = "discordant"

    @classmethod
    def from_score(cls, score: float) -> str:
        if score > 0.9:
            return cls.ENTANGLED
        if score > 0.7:
            return cls.HARMONIC
        if score > 0.4:
            return cls.RESONANT
        return cls.DISCORDANT


# ---------------------------------------------------------------------------
# RepoResonance class
# ---------------------------------------------------------------------------
class RepoResonance:
    """
    Detects cross-repository pattern resonance using Jaccard similarity.

    Attributes:
        resonance_patterns: List of registered pattern dicts with repo metadata.
        frequency_map: Dict mapping repo_name -> aggregated pattern dict.
    """

    def __init__(self) -> None:
        self.resonance_patterns: List[Dict[str, Any]] = []
        self.frequency_map: Dict[str, Dict[str, Any]] = {}
        self._resonance_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _jaccard(a: Set[str], b: Set[str]) -> float:
        """Compute Jaccard similarity between two sets."""
        if not a and not b:
            return 1.0
        intersection = len(a & b)
        union = len(a | b)
        return intersection / union if union else 0.0

    @staticmethod
    def _to_set(value: Any) -> Set[str]:
        """Coerce a value to a set of strings for comparison."""
        if isinstance(value, set):
            return {str(v) for v in value}
        if isinstance(value, (list, tuple)):
            return {str(v) for v in value}
        if value is None:
            return set()
        return {str(value)}

    def _invalidate_cache(self) -> None:
        """Clear cached resonance computations when data changes."""
        self._resonance_cache.clear()

    def _aggregate_repo_patterns(self, repo_name: str) -> Dict[str, Set[str]]:
        """Aggregate all registered patterns for a repo into per-key sets."""
        aggregated: Dict[str, Set[str]] = {}
        for entry in self.resonance_patterns:
            if entry.get("repo_name") == repo_name:
                pattern = entry.get("pattern", {})
                for key, value in pattern.items():
                    if key not in aggregated:
                        aggregated[key] = set()
                    aggregated[key].update(self._to_set(value))
        return aggregated

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def register_pattern(self, repo_name: str, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a pattern from a repository.

        Args:
            repo_name: Name of the source repository.
            pattern: Dict with keys like architecture, philosophy, structure, naming, testing.

        Returns:
            Result dict with registered pattern summary.
        """
        if not repo_name or not isinstance(repo_name, str):
            raise ValueError("repo_name must be a non-empty string")
        if not isinstance(pattern, dict):
            raise ValueError("pattern must be a dict")

        entry = {"repo_name": repo_name, "pattern": dict(pattern)}
        self.resonance_patterns.append(entry)

        # Update frequency_map
        if repo_name not in self.frequency_map:
            self.frequency_map[repo_name] = {}
        repo_map = self.frequency_map[repo_name]
        for key, value in pattern.items():
            if key not in repo_map:
                repo_map[key] = set()
            repo_map[key].update(self._to_set(value))

        self._invalidate_cache()

        # Emit event if event bus is available
        try:
            # pylint: disable=import-outside-toplevel
            from core.event_bus import emit_event  # type: ignore
            emit_event("repo_resonance:pattern_registered", {"repo": repo_name, "keys": list(pattern.keys())})
        except Exception:
            pass  # Event bus optional

        return {
            "repo_name": repo_name,
            "registered_keys": list(pattern.keys()),
            "total_patterns": len(self.resonance_patterns),
        }

    def detect_resonance(self, repo_a: str, repo_b: str) -> Dict[str, Any]:
        """
        Detect resonance between two repositories by comparing their patterns.

        Uses Jaccard similarity across all pattern keys.

        Args:
            repo_a: First repository name.
            repo_b: Second repository name.

        Returns:
            Dict with resonance score, level, key-level similarities, and matched keys.
        """
        if not repo_a or not repo_b:
            raise ValueError("repo names must be non-empty strings")
        if repo_a == repo_b:
            return {
                "repo_a": repo_a,
                "repo_b": repo_b,
                "resonance_score": 1.0,
                "level": ResonanceLevel.ENTANGLED,
                "key_scores": {},
                "matched_keys": [],
                "message": "Self-resonance is always entangled",
            }

        cache_key = tuple(sorted((repo_a, repo_b)))
        if cache_key in self._resonance_cache:
            cached = dict(self._resonance_cache[cache_key])
            cached["repo_a"] = repo_a
            cached["repo_b"] = repo_b
            return cached

        patterns_a = self._aggregate_repo_patterns(repo_a)
        patterns_b = self._aggregate_repo_patterns(repo_b)

        if not patterns_a or not patterns_b:
            return {
                "repo_a": repo_a,
                "repo_b": repo_b,
                "resonance_score": 0.0,
                "level": ResonanceLevel.DISCORDANT,
                "key_scores": {},
                "matched_keys": [],
                "message": "One or both repositories have no registered patterns",
            }

        all_keys = set(patterns_a.keys()) | set(patterns_b.keys())
        key_scores: Dict[str, float] = {}
        matched_keys: List[str] = []
        total_score = 0.0

        for key in all_keys:
            set_a = patterns_a.get(key, set())
            set_b = patterns_b.get(key, set())
            score = self._jaccard(set_a, set_b)
            key_scores[key] = round(score, 4)
            total_score += score
            if score > 0.0:
                matched_keys.append(key)

        avg_score = total_score / len(all_keys) if all_keys else 0.0
        avg_score = round(avg_score, 4)
        level = ResonanceLevel.from_score(avg_score)

        result = {
            "repo_a": repo_a,
            "repo_b": repo_b,
            "resonance_score": avg_score,
            "level": level,
            "key_scores": key_scores,
            "matched_keys": matched_keys,
        }
        self._resonance_cache[cache_key] = result
        return result

    def sync_resonance(self, repo_name: str) -> Dict[str, Any]:
        """
        Synchronize a repository with its highest-resonance partner.

        Args:
            repo_name: Repository to sync.

        Returns:
            Dict with sync results, including partner and merged knowledge.
        """
        if not repo_name:
            raise ValueError("repo_name must be a non-empty string")

        all_repos = self._get_all_repo_names()
        if repo_name not in all_repos:
            return {
                "repo_name": repo_name,
                "status": "no_patterns",
                "partner": None,
                "resonance_score": 0.0,
                "level": ResonanceLevel.DISCORDANT,
                "merged_keys": [],
                "message": f"Repository '{repo_name}' has no registered patterns",
            }

        if len(all_repos) < 2:
            return {
                "repo_name": repo_name,
                "status": "insufficient_repos",
                "partner": None,
                "resonance_score": 0.0,
                "level": ResonanceLevel.DISCORDANT,
                "merged_keys": [],
                "message": "Need at least two repositories to sync",
            }

        best_partner: Optional[str] = None
        best_score = -1.0
        best_result: Optional[Dict[str, Any]] = None

        for other in all_repos:
            if other == repo_name:
                continue
            result = self.detect_resonance(repo_name, other)
            score = result["resonance_score"]
            if score > best_score:
                best_score = score
                best_partner = other
                best_result = result

        if best_partner is None or best_result is None:
            return {
                "repo_name": repo_name,
                "status": "error",
                "partner": None,
                "resonance_score": 0.0,
                "level": ResonanceLevel.DISCORDANT,
                "merged_keys": [],
                "message": "Could not determine best resonance partner",
            }

        # Compute merged knowledge keys
        patterns_a = self._aggregate_repo_patterns(repo_name)
        patterns_b = self._aggregate_repo_patterns(best_partner)
        merged_keys = list(set(patterns_a.keys()) | set(patterns_b.keys()))

        sync_result = {
            "repo_name": repo_name,
            "status": "synced",
            "partner": best_partner,
            "resonance_score": best_result["resonance_score"],
            "level": best_result["level"],
            "merged_keys": merged_keys,
            "key_scores": best_result.get("key_scores", {}),
            "message": f"Synced with '{best_partner}' at {best_result['level']} level",
        }

        try:
            from core.event_bus import emit_event  # type: ignore
            emit_event("repo_resonance:synced", sync_result)
        except Exception:
            pass

        return sync_result

    def get_resonance_matrix(self) -> Dict[str, Any]:
        """
        Return the full matrix of all repo-pair resonance scores.

        Returns:
            Dict with repos list and pairwise resonance scores.
        """
        repos = sorted(self._get_all_repo_names())
        matrix: Dict[str, Dict[str, Any]] = {}

        for i, repo_a in enumerate(repos):
            for repo_b in repos[i + 1 :]:
                result = self.detect_resonance(repo_a, repo_b)
                key = f"{repo_a}::{repo_b}"
                matrix[key] = {
                    "repo_a": repo_a,
                    "repo_b": repo_b,
                    "score": result["resonance_score"],
                    "level": result["level"],
                }

        return {
            "repos": repos,
            "pair_count": len(matrix),
            "matrix": matrix,
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Return current module status.

        Returns:
            Dict with pattern count, resonance pairs, and strongest resonance.
        """
        repos = self._get_all_repo_names()
        total_patterns = len(self.resonance_patterns)

        # Compute strongest resonance
        strongest_score = -1.0
        strongest_pair: Optional[Tuple[str, str]] = None
        strongest_level = ResonanceLevel.DISCORDANT

        repo_list = sorted(repos)
        for i, repo_a in enumerate(repo_list):
            for repo_b in repo_list[i + 1 :]:
                result = self.detect_resonance(repo_a, repo_b)
                score = result["resonance_score"]
                if score > strongest_score:
                    strongest_score = score
                    strongest_pair = (repo_a, repo_b)
                    strongest_level = result["level"]

        return {
            "pattern_count": total_patterns,
            "repo_count": len(repos),
            "resonance_pairs": (len(repo_list) * (len(repo_list) - 1)) // 2 if len(repo_list) >= 2 else 0,
            "strongest_resonance": {
                "pair": strongest_pair,
                "score": round(strongest_score, 4) if strongest_score >= 0 else None,
                "level": strongest_level,
            }
            if strongest_pair
            else None,
            "module": "repo_resonance",
            "version": 147,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_all_repo_names(self) -> Set[str]:
        """Return the set of all registered repository names."""
        return {entry["repo_name"] for entry in self.resonance_patterns}
