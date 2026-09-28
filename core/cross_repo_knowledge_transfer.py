"""
OMNI-HUB Module v158: Cross-Repo Knowledge Transfer (跨仓知识迁移)

When two repositories resonate deeply, knowledge flows automatically.
Best practices, architectural patterns, and design philosophies "infect"
one another through resonance-driven knowledge transfer.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Module-level constants & state
# ---------------------------------------------------------------------------
_MODULE: CrossRepoKnowledgeTransfer | None = None

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "alliance_repos.json"
)

# Knowledge types supported by the system
KNOWLEDGE_TYPES = [
    "architecture_pattern",
    "testing_strategy",
    "documentation_practice",
    "ci_cd_setup",
    "code_style",
]

# Capability scoring rubric (synthetic, deterministic)
_CAPABILITY_WEIGHTS: dict[str, float] = {
    "lang": 0.25,
    "role": 0.20,
    "updated": 0.25,
    "desc": 0.15,
    "line": 0.15,
}


def _parse_repo_data(path: str | None = None) -> dict[str, dict[str, Any]]:
    """Load repository metadata from the alliance JSON file."""
    path = path or _DATA_PATH
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}

    repos: dict[str, dict[str, Any]] = {}
    for group in ("alliance_core", "alliance_other", "external_alliance"):
        for name, meta in raw.get(group, {}).items():
            repos[name] = dict(meta)
    return repos


def _compute_capability(repo_name: str, meta: dict[str, Any]) -> float:
    """Return a synthetic capability score in [0.0, 1.0]."""
    score = 0.0
    # Language presence
    if meta.get("lang"):
        score += _CAPABILITY_WEIGHTS["lang"]
    # Role specificity
    if meta.get("role") or meta.get("line"):
        score += _CAPABILITY_WEIGHTS["role"]
    # Recency of update
    updated = meta.get("updated")
    if updated:
        try:
            upd_dt = datetime.strptime(updated, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - upd_dt).days
            recency = max(0.0, 1.0 - age_days / 365.0)
            score += recency * _CAPABILITY_WEIGHTS["updated"]
        except Exception:
            score += 0.5 * _CAPABILITY_WEIGHTS["updated"]
    else:
        score += 0.5 * _CAPABILITY_WEIGHTS["updated"]
    # Description richness
    desc = meta.get("desc", "")
    if desc and len(desc) > 10:
        score += _CAPABILITY_WEIGHTS["desc"]
    elif desc:
        score += 0.5 * _CAPABILITY_WEIGHTS["desc"]
    # Line / project identity
    if meta.get("line"):
        score += _CAPABILITY_WEIGHTS["line"]
    return min(1.0, max(0.0, score))


def _compute_resonance(
    repo_a: str, meta_a: dict[str, Any], repo_b: str, meta_b: dict[str, Any]
) -> float:
    """Compute a deterministic resonance score between two repos."""
    if repo_a == repo_b:
        return 1.0
    factors: list[float] = []
    # Language affinity
    lang_a = meta_a.get("lang") or "unknown"
    lang_b = meta_b.get("lang") or "unknown"
    factors.append(1.0 if lang_a == lang_b else 0.3)
    # Role / line affinity
    role_a = meta_a.get("role") or meta_a.get("line") or "unknown"
    role_b = meta_b.get("role") or meta_b.get("line") or "unknown"
    factors.append(1.0 if role_a == role_b else 0.5)
    # Group affinity (prefix heuristic)
    group_a = repo_a.split("-")[0] if "-" in repo_a else repo_a.split("/")[0]
    group_b = repo_b.split("-")[0] if "-" in repo_b else repo_b.split("/")[0]
    factors.append(1.0 if group_a == group_b else 0.4)
    # Description semantic overlap (simple token Jaccard)
    desc_a = set((meta_a.get("desc") or "").lower().split())
    desc_b = set((meta_b.get("desc") or "").lower().split())
    if desc_a or desc_b:
        inter = len(desc_a & desc_b)
        union = len(desc_a | desc_b)
        factors.append(inter / union if union else 0.0)
    else:
        factors.append(0.0)
    return round(sum(factors) / len(factors), 4)


# ---------------------------------------------------------------------------
# Event-bus helpers
# ---------------------------------------------------------------------------
def _emit_event(event_type: str, payload: dict[str, Any]) -> None:
    """Emit an event to the OMNI-HUB event bus if available."""
    try:
        # Deferred import avoids circular dependency at module load time
        from core.event_bus import get_event_bus  # type: ignore[import]

        bus = get_event_bus()
        bus.publish(event_type, payload)
    except Exception:
        pass  # Event bus is optional; fail silently.


# ---------------------------------------------------------------------------
# CrossRepoKnowledgeTransfer
# ---------------------------------------------------------------------------
class CrossRepoKnowledgeTransfer:
    """Orchestrates resonance-driven knowledge transfer across repositories."""

    def __init__(self, repo_data_path: str | None = None) -> None:
        self._repos = _parse_repo_data(repo_data_path)
        self._capabilities: dict[str, float] = {
            name: _compute_capability(name, meta)
            for name, meta in self._repos.items()
        }
        self._resonance_cache: dict[tuple[str, str], float] = {}
        self.knowledge_base: dict[str, dict[str, Any]] = {}
        self.transfer_history: list[dict[str, Any]] = []
        self._build_knowledge_base()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_resonance(self, a: str, b: str) -> float:
        key = tuple(sorted((a, b)))
        if key not in self._resonance_cache:
            meta_a = self._repos.get(a, {})
            meta_b = self._repos.get(b, {})
            self._resonance_cache[key] = _compute_resonance(a, meta_a, b, meta_b)
        return self._resonance_cache[key]

    def _build_knowledge_base(self) -> None:
        """Seed the knowledge base with deterministic synthetic knowledge per repo."""
        for name, meta in self._repos.items():
            cap = self._capabilities.get(name, 0.0)
            self.knowledge_base[name] = {
                "architecture_pattern": self._synth_architecture(name, cap, meta),
                "testing_strategy": self._synth_testing(name, cap, meta),
                "documentation_practice": self._synth_docs(name, cap, meta),
                "ci_cd_setup": self._synth_cicd(name, cap, meta),
                "code_style": self._synth_code_style(name, cap, meta),
            }

    @staticmethod
    def _synth_architecture(name: str, cap: float, meta: dict[str, Any]) -> dict[str, Any]:
        patterns = ["layered", "hexagonal", "microservices", "monolith", "event-driven"]
        idx = hash(name + "arch") % len(patterns)
        return {
            "primary_pattern": patterns[idx],
            "maturity_score": round(cap, 4),
            "layers": int(3 + cap * 4),
            "key_principles": ["separation_of_concerns", "single_responsibility"],
        }

    @staticmethod
    def _synth_testing(name: str, cap: float, meta: dict[str, Any]) -> dict[str, Any]:
        frameworks = ["pytest", "unittest", "jest", "mocha", "go-test"]
        idx = hash(name + "test") % len(frameworks)
        return {
            "framework": frameworks[idx],
            "coverage_target": int(70 + cap * 30),
            "test_types": ["unit", "integration"] if cap > 0.6 else ["unit"],
            "mutation_testing": cap > 0.8,
        }

    @staticmethod
    def _synth_docs(name: str, cap: float, meta: dict[str, Any]) -> dict[str, Any]:
        formats = ["sphinx", "mkdocs", "readme", "wiki", "docusaurus"]
        idx = hash(name + "docs") % len(formats)
        return {
            "format": formats[idx],
            "api_documentation": cap > 0.5,
            "architecture_decision_records": cap > 0.7,
            "contributing_guide": cap > 0.6,
        }

    @staticmethod
    def _synth_cicd(name: str, cap: float, meta: dict[str, Any]) -> dict[str, Any]:
        platforms = ["github-actions", "gitlab-ci", "jenkins", "circleci", "travis"]
        idx = hash(name + "cicd") % len(platforms)
        return {
            "platform": platforms[idx],
            "automated_tests": cap > 0.4,
            "deployment_stages": int(1 + cap * 3),
            "security_scanning": cap > 0.7,
        }

    @staticmethod
    def _synth_code_style(name: str, cap: float, meta: dict[str, Any]) -> dict[str, Any]:
        formatters = ["black", "prettier", "gofmt", "rustfmt", "autopep8"]
        idx = hash(name + "style") % len(formatters)
        return {
            "formatter": formatters[idx],
            "linting": cap > 0.5,
            "type_hints": cap > 0.6,
            "max_line_length": 88 if cap > 0.6 else 120,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def identify_transfer_opportunities(self) -> list[dict[str, Any]]:
        """Find repo pairs where knowledge can flow (high resonance + capability gap)."""
        opportunities: list[dict[str, Any]] = []
        repo_names = list(self._repos.keys())
        for i, from_repo in enumerate(repo_names):
            for to_repo in repo_names[i + 1 :]:
                resonance = self._get_resonance(from_repo, to_repo)
                cap_from = self._capabilities.get(from_repo, 0.0)
                cap_to = self._capabilities.get(to_repo, 0.0)
                gap = abs(cap_from - cap_to)
                # Only consider pairs with meaningful resonance and a capability gap
                if resonance >= 0.3 and gap >= 0.05:
                    # Direction: high -> low
                    if cap_from > cap_to:
                        source, target = from_repo, to_repo
                        source_cap, target_cap = cap_from, cap_to
                    else:
                        source, target = to_repo, from_repo
                        source_cap, target_cap = cap_to, cap_from
                    opportunities.append(
                        {
                            "source": source,
                            "target": target,
                            "resonance": resonance,
                            "capability_gap": round(gap, 4),
                            "source_capability": round(source_cap, 4),
                            "target_capability": round(target_cap, 4),
                        }
                    )
        # Sort by resonance descending, then gap descending
        opportunities.sort(key=lambda o: (-o["resonance"], -o["capability_gap"]))
        _emit_event(
            "knowledge.transfer.opportunities_identified",
            {"count": len(opportunities)},
        )
        return opportunities

    def extract_knowledge(self, repo_name: str, knowledge_type: str) -> dict[str, Any]:
        """Extract knowledge of a specific type from a repository."""
        if repo_name not in self._repos:
            return {"error": f"Repository '{repo_name}' not found"}
        if knowledge_type not in KNOWLEDGE_TYPES:
            return {
                "error": f"Unknown knowledge type '{knowledge_type}'",
                "supported_types": KNOWLEDGE_TYPES,
            }
        knowledge = self.knowledge_base.get(repo_name, {}).get(knowledge_type, {})
        result = {
            "repo": repo_name,
            "knowledge_type": knowledge_type,
            "capability": round(self._capabilities.get(repo_name, 0.0), 4),
            "data": knowledge,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }
        _emit_event(
            "knowledge.transfer.extracted",
            {"repo": repo_name, "type": knowledge_type},
        )
        return result

    def transfer_knowledge(
        self, from_repo: str, to_repo: str, knowledge: dict[str, Any]
    ) -> dict[str, Any]:
        """Transfer knowledge from source repository to target repository."""
        if from_repo not in self._repos:
            return {"error": f"Source repository '{from_repo}' not found"}
        if to_repo not in self._repos:
            return {"error": f"Target repository '{to_repo}' not found"}

        resonance = self._get_resonance(from_repo, to_repo)
        transfer_id = str(uuid.uuid4())

        # Determine success probability from resonance
        if resonance > 0.7:
            success_prob = 0.9
        elif resonance >= 0.5:
            success_prob = 0.6
        else:
            success_prob = 0.3

        record = {
            "transfer_id": transfer_id,
            "from_repo": from_repo,
            "to_repo": to_repo,
            "resonance": resonance,
            "success_probability": success_prob,
            "knowledge_type": knowledge.get("knowledge_type", "unknown"),
            "status": "pending",
            "transferred_at": datetime.now(timezone.utc).isoformat(),
            "verified_at": None,
            "adopted": None,
        }
        self.transfer_history.append(record)

        _emit_event(
            "knowledge.transfer.initiated",
            {
                "transfer_id": transfer_id,
                "from": from_repo,
                "to": to_repo,
                "resonance": resonance,
            },
        )
        return {
            "transfer_id": transfer_id,
            "from_repo": from_repo,
            "to_repo": to_repo,
            "resonance": resonance,
            "success_probability": success_prob,
            "status": "pending",
        }

    def verify_transfer(self, transfer_id: str) -> dict[str, Any]:
        """Verify whether a transferred knowledge item was successfully adopted."""
        for record in self.transfer_history:
            if record["transfer_id"] == transfer_id:
                if record["status"] == "verified":
                    return {
                        "transfer_id": transfer_id,
                        "status": "verified",
                        "adopted": record["adopted"],
                        "verified_at": record["verified_at"],
                    }
                # Deterministic simulation based on success probability
                prob = record["success_probability"]
                # Use hash of transfer_id to make outcome deterministic
                seed = int(hashlib.md5(transfer_id.encode()).hexdigest(), 16)
                adopted = (seed % 1000) / 1000.0 < prob
                record["adopted"] = adopted
                record["status"] = "verified"
                record["verified_at"] = datetime.now(timezone.utc).isoformat()
                _emit_event(
                    "knowledge.transfer.verified",
                    {"transfer_id": transfer_id, "adopted": adopted},
                )
                return {
                    "transfer_id": transfer_id,
                    "status": "verified",
                    "adopted": adopted,
                    "verified_at": record["verified_at"],
                }
        return {"error": f"Transfer '{transfer_id}' not found"}

    def get_transfer_metrics(self) -> dict[str, Any]:
        """Return aggregate metrics and the knowledge flow graph."""
        total = len(self.transfer_history)
        verified = [r for r in self.transfer_history if r["status"] == "verified"]
        adopted = [r for r in verified if r.get("adopted")]
        success_rate = round(len(adopted) / len(verified), 4) if verified else 0.0

        # Build flow graph
        flow_graph: dict[str, dict[str, Any]] = {}
        for record in self.transfer_history:
            src = record["from_repo"]
            tgt = record["to_repo"]
            if src not in flow_graph:
                flow_graph[src] = {"outgoing": [], "total_transfers": 0}
            flow_graph[src]["outgoing"].append(
                {
                    "target": tgt,
                    "knowledge_type": record.get("knowledge_type", "unknown"),
                    "status": record["status"],
                    "adopted": record.get("adopted"),
                }
            )
            flow_graph[src]["total_transfers"] += 1

        return {
            "total_transfers": total,
            "verified_transfers": len(verified),
            "successful_adoptions": len(adopted),
            "success_rate": success_rate,
            "knowledge_flow_graph": flow_graph,
            "pending_transfers": total - len(verified),
        }

    def get_status(self) -> dict[str, Any]:
        """Return high-level module status."""
        opportunities = self.identify_transfer_opportunities()
        metrics = self.get_transfer_metrics()
        return {
            "opportunity_count": len(opportunities),
            "transfer_count": metrics["total_transfers"],
            "success_rate": metrics["success_rate"],
            "pending_transfers": metrics["pending_transfers"],
            "verified_transfers": metrics["verified_transfers"],
            "repo_count": len(self._repos),
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
def get_cross_repo_knowledge_transfer() -> CrossRepoKnowledgeTransfer:
    """Return the global singleton instance of CrossRepoKnowledgeTransfer."""
    global _MODULE
    if _MODULE is None:
        _MODULE = CrossRepoKnowledgeTransfer()
    return _MODULE



