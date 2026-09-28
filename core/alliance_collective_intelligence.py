"""
Alliance Collective Intelligence Module (v159)
联盟集体智慧 — 33 interconnected repos as a super-organism.

Emergent intelligence: 1 + 1 > 2.
"""

import json
import math
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Event-bus integration (best-effort)
# ---------------------------------------------------------------------------

try:
    from core.event_bus import EventBus

    _event_bus: Optional[Any] = EventBus()
except Exception:
    _event_bus = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "alliance_repos.json")

PATTERN_TYPES = [
    "convergent_evolution",
    "complementary_capabilities",
    "shared_challenges",
    "synergistic_opportunities",
]

PROBLEM_TYPES = [
    "architecture_decision",
    "scaling_challenge",
    "integration_issue",
    "performance_bottleneck",
]

IQ_LEVELS = [
    (200, "superintelligence"),
    (150, "genius"),
    (120, "gifted"),
    (100, "bright"),
    (70, "average"),
]

# Topic-to-repo relevance mapping (synthetic expertise alignment)
_TOPIC_RELEVANCE: Dict[str, List[str]] = {
    "consciousness": ["ucif2", "vinf", "qfa", "usrm"],
    "logic": ["lgt", "qgl", "cfts", "grand-synthesis"],
    "quantum": ["qfa", "qgl", "qlv", "qtlv"],
    "scaling": ["omni", "ci-worker-01", "ci-worker-02", "ci-yard"],
    "integration": ["omni", "vci-bus", "vci-control", "inbox"],
    "performance": ["pytorch/pytorch", "huggingface/transformers", "qfos-autonomous-engine"],
    "ai": ["aiq", "langchain-ai/langchain", "openai/openai-python", "microsoft/semantic-kernel"],
    "value": ["vinf", "lvlu", "usrm", "prima-50-research"],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_repos() -> Dict[str, Dict[str, Any]]:
    """Load alliance repository metadata."""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as fh:
            data: Dict[str, Any] = json.load(fh)
    except Exception:
        data = {}

    flat: Dict[str, Dict[str, Any]] = {}
    for category, repos in data.items():
        for name, meta in repos.items():
            entry = dict(meta)
            entry["name"] = name
            entry["category"] = category
            flat[name] = entry
    return flat


def _repo_capability(repo: Dict[str, Any]) -> float:
    """Assign a synthetic capability score [50..120] to a repo."""
    base = 60.0
    # Language bonus
    lang = repo.get("lang")
    if lang == "Python":
        base += 15.0
    elif lang in ("C++", "C#", "Lean"):
        base += 12.0
    # Role/line bonus
    role = repo.get("role") or repo.get("line") or ""
    if role in ("omni", "synthesis", "control", "navigation"):
        base += 10.0
    elif role in ("worker", "library", "framework", "ml", "dl"):
        base += 8.0
    # Freshness bonus (more recently updated = more capable)
    updated = repo.get("updated", "")
    if updated:
        try:
            dt = datetime.strptime(updated, "%Y-%m-%d")
            days_old = (datetime(2026, 9, 27) - dt).days
            base += max(0.0, 10.0 - days_old * 0.1)
        except Exception:
            pass
    # Deterministic jitter per repo name
    rng = random.Random(repo.get("name", ""))
    base += rng.uniform(-5.0, 5.0)
    return round(max(50.0, min(120.0, base)), 2)


def _connectivity_density(repo_count: int, edge_count: int) -> float:
    """Graph density for an undirected simple graph."""
    if repo_count < 2:
        return 0.0
    max_edges = repo_count * (repo_count - 1) / 2.0
    return round(edge_count / max_edges, 4)


def _information_flow_rate(avg_capability: float, density: float) -> float:
    """Synthetic flow rate derived from capability and connectivity."""
    return round(math.sqrt(avg_capability) * (0.5 + 0.5 * density), 4)


def _collective_iq(avg_capability: float, density: float, flow_rate: float) -> float:
    """Collective IQ = avg_capability × density × flow_rate."""
    return round(avg_capability * density * flow_rate, 2)


def _iq_level(iq: float) -> str:
    for threshold, label in IQ_LEVELS:
        if iq > threshold:
            return label
    return "below_average"


def _notify(event_type: str, payload: Dict[str, Any]) -> None:
    if _event_bus is not None:
        try:
            _event_bus.publish(event_type, payload)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# AllianceCollectiveIntelligence
# ---------------------------------------------------------------------------

class AllianceCollectiveIntelligence:
    """
    联盟集体智慧 — Emergent intelligence across 33 interconnected repositories.
    """

    def __init__(self) -> None:
        self.repos: Dict[str, Dict[str, Any]] = _load_repos()
        self.collective_memory: Dict[str, Any] = {}
        self.insight_history: List[Dict[str, Any]] = []
        self._repo_capabilities: Dict[str, float] = {
            name: _repo_capability(meta) for name, meta in self.repos.items()
        }
        self._edges: int = self._compute_edges()
        self._avg_capability: float = self._compute_avg_capability()
        self._density: float = _connectivity_density(len(self.repos), self._edges)
        self._flow_rate: float = _information_flow_rate(self._avg_capability, self._density)
        self._collective_iq: float = _collective_iq(self._avg_capability, self._density, self._flow_rate)
        self._detected_patterns: List[Dict[str, Any]] = []
        self._aggregate_insights: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Internal graph / metrics
    # ------------------------------------------------------------------

    def _compute_edges(self) -> int:
        """Build a synthetic edge count based on shared attributes."""
        names = list(self.repos.keys())
        edges = 0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a = self.repos[names[i]]
                b = self.repos[names[j]]
                if a.get("lang") and a.get("lang") == b.get("lang"):
                    edges += 1
                if (a.get("role") or a.get("line")) == (b.get("role") or b.get("line")):
                    edges += 1
                if a.get("category") == b.get("category"):
                    edges += 1
        return edges

    def _compute_avg_capability(self) -> float:
        if not self._repo_capabilities:
            return 0.0
        return round(sum(self._repo_capabilities.values()) / len(self._repo_capabilities), 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def aggregate_perspectives(self, topic: str) -> Dict[str, Any]:
        """
        Aggregate perspectives from all repos on a topic.
        Each repo contributes based on its role and expertise.
        """
        topic_lower = topic.lower()
        relevant_lines = []
        for key, names in _TOPIC_RELEVANCE.items():
            if key in topic_lower:
                relevant_lines.extend(names)

        perspectives: List[Dict[str, Any]] = []
        for name, meta in self.repos.items():
            capability = self._repo_capabilities.get(name, 50.0)
            # Relevance score
            line_or_role = meta.get("line") or meta.get("role") or ""
            relevance = 0.3  # baseline
            if line_or_role in relevant_lines:
                relevance = 0.9
            elif any(r in name.lower() for r in relevant_lines):
                relevance = 0.7
            elif any(r in meta.get("desc", "").lower() for r in relevant_lines):
                relevance = 0.6
            elif not relevant_lines:
                relevance = 0.5  # generic topic → moderate contribution from all

            contribution = round(capability * relevance, 2)
            perspectives.append({
                "repo": name,
                "category": meta.get("category", "unknown"),
                "capability": capability,
                "relevance": round(relevance, 2),
                "contribution": contribution,
                "perspective": f"{name} views '{topic}' through its {line_or_role} lens",
            })

        # Sort by contribution descending
        perspectives.sort(key=lambda x: x["contribution"], reverse=True)
        total_contribution = round(sum(p["contribution"] for p in perspectives), 2)

        result = {
            "topic": topic,
            "repo_count": len(self.repos),
            "perspectives": perspectives,
            "total_contribution": total_contribution,
            "top_contributor": perspectives[0]["repo"] if perspectives else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._aggregate_insights[topic] = result
        self.insight_history.append({"type": "aggregate", "topic": topic, "total": total_contribution})
        _notify("aci.aggregate_perspectives", {"topic": topic, "repos": len(perspectives)})
        return result

    def detect_emergent_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect patterns that ONLY appear when viewing all repos together.
        Pattern types: convergent_evolution, complementary_capabilities,
        shared_challenges, synergistic_opportunities.
        """
        patterns: List[Dict[str, Any]] = []
        repo_list = list(self.repos.values())
        names = list(self.repos.keys())

        # 1. Convergent evolution — multiple repos independently tackling same domain
        lang_groups: Dict[str, List[str]] = {}
        for name, meta in self.repos.items():
            lang = meta.get("lang") or "unknown"
            lang_groups.setdefault(lang, []).append(name)
        for lang, group in lang_groups.items():
            if len(group) >= 3:
                patterns.append({
                    "type": "convergent_evolution",
                    "description": f"{len(group)} repos converge on language '{lang}'",
                    "repos": group,
                    "strength": round(len(group) / len(names), 4),
                })

        # 2. Complementary capabilities — repos with different roles in same category
        category_groups: Dict[str, List[str]] = {}
        for name, meta in self.repos.items():
            cat = meta.get("category", "unknown")
            category_groups.setdefault(cat, []).append(name)
        for cat, group in category_groups.items():
            if len(group) >= 2:
                roles = set()
                for g in group:
                    meta = self.repos[g]
                    roles.add(meta.get("role") or meta.get("line") or "unknown")
                if len(roles) > 1:
                    patterns.append({
                        "type": "complementary_capabilities",
                        "description": f"Category '{cat}' hosts {len(roles)} distinct roles across {len(group)} repos",
                        "repos": group,
                        "strength": round(len(roles) / len(group), 4),
                    })

        # 3. Shared challenges — repos with null language (documentation / meta)
        null_lang = [n for n, m in self.repos.items() if m.get("lang") is None]
        if len(null_lang) >= 2:
            patterns.append({
                "type": "shared_challenges",
                "description": f"{len(null_lang)} repos share language-agnostic/meta challenges",
                "repos": null_lang,
                "strength": round(len(null_lang) / len(names), 4),
            })

        # 4. Synergistic opportunities — high-capability pairs in different categories
        sorted_caps = sorted(self._repo_capabilities.items(), key=lambda x: x[1], reverse=True)
        top5 = [n for n, _ in sorted_caps[:5]]
        cats = {n: self.repos[n].get("category", "unknown") for n in top5}
        unique_cats = set(cats.values())
        if len(unique_cats) > 1:
            patterns.append({
                "type": "synergistic_opportunities",
                "description": f"Top-{len(top5)} capability repos span {len(unique_cats)} categories",
                "repos": top5,
                "strength": round(len(unique_cats) / 5.0, 4),
            })

        self._detected_patterns = patterns
        self.insight_history.append({"type": "detect_patterns", "count": len(patterns)})
        _notify("aci.detect_emergent_patterns", {"patterns": len(patterns)})
        return patterns

    def solve_collective_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use collective intelligence to solve a problem.
        Problem types: architecture_decision, scaling_challenge,
        integration_issue, performance_bottleneck.
        Solution quality = average expertise of relevant repos.
        """
        ptype = problem.get("type", "unknown")
        description = problem.get("description", "")
        if ptype not in PROBLEM_TYPES:
            ptype = "architecture_decision"

        # Map problem type to relevant repos via topics
        topic_map: Dict[str, str] = {
            "architecture_decision": "architecture",
            "scaling_challenge": "scaling",
            "integration_issue": "integration",
            "performance_bottleneck": "performance",
        }
        topic = topic_map.get(ptype, ptype)
        aggregate = self.aggregate_perspectives(topic)

        # Relevant repos = those with relevance >= 0.5
        relevant = [p for p in aggregate["perspectives"] if p["relevance"] >= 0.5]
        if not relevant:
            relevant = aggregate["perspectives"][:5]

        avg_expertise = round(
            sum(p["capability"] for p in relevant) / len(relevant), 2
        ) if relevant else 0.0

        # Solution quality bounded by 0..1
        solution_quality = round(min(1.0, avg_expertise / 120.0), 4)

        # Collective IQ boost factor
        boost = self._collective_iq / 200.0
        effective_quality = round(min(1.0, solution_quality * (1.0 + boost * 0.2)), 4)

        result = {
            "problem_type": ptype,
            "description": description,
            "relevant_repos": [p["repo"] for p in relevant],
            "repo_count": len(relevant),
            "avg_expertise": avg_expertise,
            "solution_quality": solution_quality,
            "collective_iq_boost": round(boost, 4),
            "effective_quality": effective_quality,
            "recommended_action": self._recommend_action(ptype, relevant),
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.collective_memory[description or ptype] = result
        self.insight_history.append({"type": "solve", "problem": ptype, "quality": effective_quality})
        _notify("aci.solve_collective_problem", {"type": ptype, "quality": effective_quality})
        return result

    def _recommend_action(self, ptype: str, relevant: List[Dict[str, Any]]) -> str:
        """Generate a synthetic recommendation."""
        top = relevant[0]["repo"] if relevant else "alliance"
        actions = {
            "architecture_decision": f"Convene architecture council led by {top} to evaluate trade-offs.",
            "scaling_challenge": f"Distribute load across workers; {top} provides orchestration.",
            "integration_issue": f"Standardise interfaces via {top}; deploy vci-bus as message backbone.",
            "performance_bottleneck": f"Profile hotspots in {top}; offload to pytorch/pytorch if compute-bound.",
        }
        return actions.get(ptype, "Consult collective memory and iterate.")

    def forecast_collective_trajectory(self) -> Dict[str, Any]:
        """Forecast where the alliance is heading."""
        repo_count = len(self.repos)
        avg_cap = self._avg_capability
        density = self._density
        iq = self._collective_iq

        # Trend vectors (synthetic but deterministic)
        growth_rate = round(math.log1p(repo_count) * 0.05, 4)
        capability_trend = round(avg_cap * (1.0 + growth_rate), 2)
        projected_iq = round(iq * (1.0 + growth_rate * density), 2)

        # Phase classification
        if projected_iq > 200:
            phase = "superintelligence_emergence"
        elif projected_iq > 150:
            phase = "genius_collective"
        elif projected_iq > 120:
            phase = "gifted_alliance"
        elif projected_iq > 100:
            phase = "bright_network"
        else:
            phase = "nascent_federation"

        # Key drivers
        top3 = sorted(self._repo_capabilities.items(), key=lambda x: x[1], reverse=True)[:3]
        drivers = [n for n, _ in top3]

        result = {
            "current_iq": iq,
            "current_level": _iq_level(iq),
            "projected_iq_6m": projected_iq,
            "projected_level": _iq_level(projected_iq),
            "growth_rate": growth_rate,
            "capability_trend": capability_trend,
            "phase": phase,
            "key_drivers": drivers,
            "recommendation": "Accelerate cross-repo integration to increase density and unlock emergent intelligence.",
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.insight_history.append({"type": "forecast", "projected_iq": projected_iq})
        _notify("aci.forecast_collective_trajectory", {"projected_iq": projected_iq})
        return result

    def get_status(self) -> Dict[str, Any]:
        """Return aggregated insights, detected patterns, collective IQ."""
        return {
            "collective_iq": self._collective_iq,
            "iq_level": _iq_level(self._collective_iq),
            "repo_count": len(self.repos),
            "avg_capability": self._avg_capability,
            "connectivity_density": self._density,
            "information_flow_rate": self._flow_rate,
            "aggregate_insights": self._aggregate_insights,
            "detected_patterns": self._detected_patterns,
            "insight_history_count": len(self.insight_history),
            "collective_memory_keys": list(self.collective_memory.keys()),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_module: Optional[AllianceCollectiveIntelligence] = None


def get_alliance_collective_intelligence() -> AllianceCollectiveIntelligence:
    """Return the global AllianceCollectiveIntelligence singleton."""
    global _module
    if _module is None:
        _module = AllianceCollectiveIntelligence()
    return _module
