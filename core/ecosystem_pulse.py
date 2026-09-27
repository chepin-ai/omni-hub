"""
OMNI-HUB Module v148: Ecosystem Pulse (生态系统脉冲)

生态感知神经——感知整个代码宇宙的健康脉搏。
监控所有联动仓库的活跃度，检测生态级风险和机会。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import random

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_module: Optional["EcosystemPulse"] = None


def get_ecosystem_pulse() -> "EcosystemPulse":
    """Global singleton accessor for EcosystemPulse."""
    global _module
    if _module is None:
        _module = EcosystemPulse()
    return _module


# ---------------------------------------------------------------------------
# Event bus integration (defensive, best-effort)
# ---------------------------------------------------------------------------
def _emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit event to the OMNI-HUB event bus if available."""
    try:
        # Deferred import avoids hard dependency on the event bus package
        from core.event_bus import emit  # type: ignore
        emit(event_type, payload)
    except Exception:
        # Event bus is optional; silently degrade
        pass


# ---------------------------------------------------------------------------
# EcosystemPulse
# ---------------------------------------------------------------------------
class EcosystemPulse:
    """
    生态系统脉冲 —— 感知整个生态系统的健康状态。

    Responsibilities:
        - Register ecosystems with their constituent repositories.
        - Compute aggregate pulse metrics (health, activity, growth).
        - Detect ecosystem-level risks (decline, concentration, dependency).
        - Detect ecosystem-level opportunities (emerging repos, trends).
        - Maintain pulse history for temporal analysis.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._ecosystem_state: Dict[str, Dict[str, Any]] = {}
        self._pulse_history: List[Dict[str, Any]] = []
        self._risk_thresholds = {
            "stable": 0.3,
            "caution": 0.6,
            "warning": 0.8,
            "critical": 1.0,
        }

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_ecosystem(self, name: str, repos: List[str]) -> Dict[str, Any]:
        """
        Register a named ecosystem composed of repository identifiers.

        Args:
            name: Human-readable ecosystem name, e.g. "AI ecosystem".
            repos: List of repository identifiers (owner/repo or URL).

        Returns:
            Dict with ``success``, ``ecosystem``, and ``repo_count``.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid ecosystem name", "ecosystem": None}
        if not repos or not isinstance(repos, list):
            return {"success": False, "error": "Invalid repo list", "ecosystem": None}

        # Deduplicate repo list while preserving order
        seen: set = set()
        deduped: List[str] = []
        for r in repos:
            if isinstance(r, str) and r not in seen:
                seen.add(r)
                deduped.append(r)

        # Initialise per-repo health data with reasonable defaults
        repo_data: Dict[str, Dict[str, float]] = {}
        for repo in deduped:
            repo_data[repo] = self._generate_repo_metrics(repo)

        ecosystem_record = {
            "name": name,
            "repos": deduped,
            "repo_data": repo_data,
            "registered_at": datetime.utcnow().isoformat() + "Z",
        }
        self._ecosystem_state[name] = ecosystem_record

        _emit_event("ecosystem.registered", {"name": name, "repo_count": len(deduped)})

        return {
            "success": True,
            "ecosystem": ecosystem_record,
            "repo_count": len(deduped),
        }

    # ------------------------------------------------------------------
    # Pulse Check
    # ------------------------------------------------------------------
    def pulse_check(self) -> Dict[str, Any]:
        """
        Check the pulse of all registered ecosystems.

        Computes aggregate metrics across every ecosystem and every repo:
            - health: average of all repo health scores (0.0–1.0).
            - activity: commits per day across the whole ecosystem.
            - growth: trend indicator based on new repos / new contributors.

        Returns:
            Dict with ``ecosystems``, ``global``, and ``timestamp``.
        """
        if not self._ecosystem_state:
            return {
                "ecosystems": {},
                "global": {"health": 0.0, "activity": 0.0, "growth": 0.0},
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        ecosystem_summaries: Dict[str, Dict[str, float]] = {}
        all_healths: List[float] = []
        all_activities: List[float] = []
        all_growths: List[float] = []

        for eco_name, eco in self._ecosystem_state.items():
            healths = [d["health"] for d in eco["repo_data"].values()]
            activities = [d["activity"] for d in eco["repo_data"].values()]
            growths = [d["growth"] for d in eco["repo_data"].values()]

            avg_health = sum(healths) / len(healths) if healths else 0.0
            avg_activity = sum(activities) / len(activities) if activities else 0.0
            avg_growth = sum(growths) / len(growths) if growths else 0.0

            ecosystem_summaries[eco_name] = {
                "health": round(avg_health, 4),
                "activity": round(avg_activity, 4),
                "growth": round(avg_growth, 4),
                "repo_count": len(eco["repos"]),
            }

            all_healths.append(avg_health)
            all_activities.append(avg_activity)
            all_growths.append(avg_growth)

        global_health = sum(all_healths) / len(all_healths) if all_healths else 0.0
        global_activity = sum(all_activities) / len(all_activities) if all_activities else 0.0
        global_growth = sum(all_growths) / len(all_growths) if all_growths else 0.0

        pulse_record = {
            "ecosystems": ecosystem_summaries,
            "global": {
                "health": round(global_health, 4),
                "activity": round(global_activity, 4),
                "growth": round(global_growth, 4),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._pulse_history.append(pulse_record)

        _emit_event("ecosystem.pulse", pulse_record)
        return pulse_record

    # ------------------------------------------------------------------
    # Risk Detection
    # ------------------------------------------------------------------
    def detect_eco_risk(self) -> Dict[str, Any]:
        """
        Detect ecosystem-level risks.

        Risk categories:
            - declining_repos: repos with health < 0.4.
            - concentration_risk: single repo contributes > 60 % of activity.
            - dependency_risk: ecosystems with < 3 repos (fragile).
            - stagnation_risk: average growth < 0.1.

        Returns:
            Dict with ``risks``, ``risk_score``, ``risk_level``, and ``timestamp``.
        """
        if not self._ecosystem_state:
            return {
                "risks": [],
                "risk_score": 0.0,
                "risk_level": "stable",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        risks: List[Dict[str, Any]] = []
        total_repos = 0
        declining_count = 0
        concentration_flags = 0
        dependency_flags = 0
        stagnation_flags = 0

        for eco_name, eco in self._ecosystem_state.items():
            repo_data = eco["repo_data"]
            repo_count = len(repo_data)
            total_repos += repo_count

            # Declining repos
            for repo, metrics in repo_data.items():
                if metrics.get("health", 1.0) < 0.4:
                    declining_count += 1
                    risks.append({
                        "type": "declining_repo",
                        "ecosystem": eco_name,
                        "repo": repo,
                        "health": metrics["health"],
                    })

            # Concentration risk
            if repo_count > 0:
                activities = [m["activity"] for m in repo_data.values()]
                total_activity = sum(activities)
                max_activity = max(activities) if activities else 0.0
                if total_activity > 0 and (max_activity / total_activity) > 0.6:
                    concentration_flags += 1
                    risks.append({
                        "type": "concentration_risk",
                        "ecosystem": eco_name,
                        "max_activity_share": round(max_activity / total_activity, 4),
                    })

            # Dependency risk (fragile ecosystem)
            if repo_count < 3:
                dependency_flags += 1
                risks.append({
                    "type": "dependency_risk",
                    "ecosystem": eco_name,
                    "repo_count": repo_count,
                })

            # Stagnation risk
            avg_growth = sum(m["growth"] for m in repo_data.values()) / repo_count if repo_count else 0.0
            if avg_growth < 0.1:
                stagnation_flags += 1
                risks.append({
                    "type": "stagnation_risk",
                    "ecosystem": eco_name,
                    "avg_growth": round(avg_growth, 4),
                })

        # Compute composite risk score (0.0–1.0)
        risk_score = 0.0
        if total_repos > 0:
            risk_score += (declining_count / total_repos) * 0.4
        risk_score += min(concentration_flags / max(len(self._ecosystem_state), 1), 1.0) * 0.25
        risk_score += min(dependency_flags / max(len(self._ecosystem_state), 1), 1.0) * 0.20
        risk_score += min(stagnation_flags / max(len(self._ecosystem_state), 1), 1.0) * 0.15
        risk_score = min(round(risk_score, 4), 1.0)

        risk_level = self._classify_risk(risk_score)

        risk_report = {
            "risks": risks,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        _emit_event("ecosystem.risk_detected", risk_report)
        return risk_report

    # ------------------------------------------------------------------
    # Opportunity Detection
    # ------------------------------------------------------------------
    def detect_eco_opportunity(self) -> Dict[str, Any]:
        """
        Detect ecosystem-level opportunities.

        Opportunity categories:
            - emerging_repo: repos with growth > 0.7.
            - trending_ecosystem: ecosystem avg growth > 0.5.
            - high_activity_hub: ecosystem avg activity > 0.7.

        Returns:
            Dict with ``opportunities``, ``opportunity_count``, and ``timestamp``.
        """
        if not self._ecosystem_state:
            return {
                "opportunities": [],
                "opportunity_count": 0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        opportunities: List[Dict[str, Any]] = []

        for eco_name, eco in self._ecosystem_state.items():
            repo_data = eco["repo_data"]
            repo_count = len(repo_data)
            if repo_count == 0:
                continue

            avg_growth = sum(m["growth"] for m in repo_data.values()) / repo_count
            avg_activity = sum(m["activity"] for m in repo_data.values()) / repo_count

            # Emerging repos
            for repo, metrics in repo_data.items():
                if metrics.get("growth", 0.0) > 0.7:
                    opportunities.append({
                        "type": "emerging_repo",
                        "ecosystem": eco_name,
                        "repo": repo,
                        "growth": metrics["growth"],
                    })

            # Trending ecosystem
            if avg_growth > 0.5:
                opportunities.append({
                    "type": "trending_ecosystem",
                    "ecosystem": eco_name,
                    "avg_growth": round(avg_growth, 4),
                })

            # High-activity hub
            if avg_activity > 0.7:
                opportunities.append({
                    "type": "high_activity_hub",
                    "ecosystem": eco_name,
                    "avg_activity": round(avg_activity, 4),
                })

        opportunity_report = {
            "opportunities": opportunities,
            "opportunity_count": len(opportunities),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        _emit_event("ecosystem.opportunity_detected", opportunity_report)
        return opportunity_report

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Return current module status.

        Returns:
            Dict with ``ecosystem_count``, ``avg_health``, ``risk_level``,
            ``opportunity_count``, ``pulse_history_length``, and ``module``.
        """
        ecosystem_count = len(self._ecosystem_state)

        if ecosystem_count == 0:
            return {
                "ecosystem_count": 0,
                "avg_health": 0.0,
                "risk_level": "stable",
                "opportunity_count": 0,
                "pulse_history_length": len(self._pulse_history),
                "module": "EcosystemPulse",
            }

        # Compute average health across all ecosystems
        all_healths: List[float] = []
        for eco in self._ecosystem_state.values():
            healths = [d["health"] for d in eco["repo_data"].values()]
            if healths:
                all_healths.append(sum(healths) / len(healths))
        avg_health = round(sum(all_healths) / len(all_healths), 4) if all_healths else 0.0

        # Derive risk level from latest risk detection (if any)
        risk_report = self.detect_eco_risk()
        risk_level = risk_report.get("risk_level", "stable")

        # Derive opportunity count from latest opportunity detection
        opp_report = self.detect_eco_opportunity()
        opportunity_count = opp_report.get("opportunity_count", 0)

        return {
            "ecosystem_count": ecosystem_count,
            "avg_health": avg_health,
            "risk_level": risk_level,
            "opportunity_count": opportunity_count,
            "pulse_history_length": len(self._pulse_history),
            "module": "EcosystemPulse",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_repo_metrics(self, repo: str) -> Dict[str, float]:
        """
        Generate deterministic demo metrics for a repository.

        Uses the repo name hash to produce stable pseudo-random values so
        repeated calls for the same repo yield the same result.
        """
        seed = hash(repo) % (2**31)
        rng = random.Random(seed)
        return {
            "health": round(rng.uniform(0.2, 1.0), 4),
            "activity": round(rng.uniform(0.0, 1.0), 4),
            "growth": round(rng.uniform(0.0, 1.0), 4),
        }

    def _classify_risk(self, score: float) -> str:
        """Classify a numeric risk score into a textual risk level."""
        if score < self._risk_thresholds["stable"]:
            return "stable"
        if score < self._risk_thresholds["caution"]:
            return "caution"
        if score < self._risk_thresholds["warning"]:
            return "warning"
        return "critical"
