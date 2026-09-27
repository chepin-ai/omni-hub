"""
OMNI-HUB Module v154: Alliance Pulse (联盟脉搏)

联盟脉搏。感知整个chepin-ai联盟的脉搏。哪些仓库活跃？哪些沉寂？
哪些正在进化？联盟整体健康度如何？这是联盟级的"生命体征监测仪"。

Responsibilities:
    - Load alliance repository manifest from alliance_repos.json.
    - Measure alliance pulse: active repos, stale repos, core line health,
      auxiliary health.
    - Detect awakening repos (recently active after long silence).
    - Detect dormant repos (no longer active).
    - Compute overall alliance health score (0–1) with level classification.
    - Maintain pulse history for temporal comparison.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_module: Optional["AlliancePulse"] = None


def get_alliance_pulse() -> "AlliancePulse":
    """Global singleton accessor for AlliancePulse."""
    global _module
    if _module is None:
        _module = AlliancePulse()
    return _module


# ---------------------------------------------------------------------------
# Event bus integration (defensive, best-effort)
# ---------------------------------------------------------------------------
def _emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit event to the OMNI-HUB event bus if available."""
    try:
        from core.event_bus import emit  # type: ignore
        emit(event_type, payload)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# AlliancePulse
# ---------------------------------------------------------------------------
class AlliancePulse:
    """
    联盟脉搏 —— 感知整个chepin-ai联盟的生命体征。

    Attributes:
        _repos: Flat dict of all internal alliance repos with merged metadata.
        _core_lines: List of repo names that belong to the 11 core VCI lines.
        _auxiliary: List of repo names in alliance_other.
        _pulse_history: Chronological list of pulse measurement records.
        _reference_date: The date used as "today" for recency calculations.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, reference_date: Optional[datetime] = None) -> None:
        """
        Load alliance_repos.json and initialise pulse history.

        Args:
            reference_date: Override "today" for deterministic testing.
        """
        self._reference_date: datetime = reference_date or datetime(2026, 9, 28)
        self._pulse_history: List[Dict[str, Any]] = []
        self._repos: Dict[str, Dict[str, Any]] = {}
        self._core_lines: List[str] = []
        self._auxiliary: List[str] = []
        self._total_internal: int = 0
        self._load_manifest()

    # ------------------------------------------------------------------
    # Manifest loading
    # ------------------------------------------------------------------
    def _load_manifest(self) -> None:
        """Load and normalise alliance_repos.json."""
        manifest_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "alliance_repos.json"
        )
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"alliance_core": {}, "alliance_other": {}, "external_alliance": {}}

        # alliance_core -> 11 VCI lines + omni-hub
        for name, meta in data.get("alliance_core", {}).items():
            self._repos[name] = {
                "name": name,
                "category": "core",
                "line": meta.get("line"),
                "role": meta.get("line"),  # alias for convenience
                "desc": meta.get("desc", ""),
                "lang": meta.get("lang"),
                "updated": meta.get("updated"),
            }
            if meta.get("line") != "omni":
                self._core_lines.append(name)

        # alliance_other -> auxiliary repos
        for name, meta in data.get("alliance_other", {}).items():
            self._repos[name] = {
                "name": name,
                "category": "auxiliary",
                "role": meta.get("role"),
                "desc": meta.get("desc", ""),
                "lang": meta.get("lang"),
                "updated": meta.get("updated"),
            }
            self._auxiliary.append(name)

        self._total_internal = len(data.get("alliance_core", {})) + len(data.get("alliance_other", {}))

        # external_alliance -> tracked but not included in internal health
        for name, meta in data.get("external_alliance", {}).items():
            self._repos[name] = {
                "name": name,
                "category": "external",
                "role": meta.get("role"),
                "desc": meta.get("desc", ""),
                "lang": meta.get("lang"),
                "updated": None,
            }

    # ------------------------------------------------------------------
    # Health helpers
    # ------------------------------------------------------------------
    def _days_since(self, updated_str: Optional[str]) -> Optional[int]:
        """Return days between updated_str and reference_date, or None."""
        if not updated_str:
            return None
        try:
            updated = datetime.strptime(updated_str, "%Y-%m-%d")
            delta = self._reference_date - updated
            return max(0, delta.days)
        except (ValueError, TypeError):
            return None

    def _repo_health(self, days_since: Optional[int]) -> float:
        """Compute a 0-1 health score from days since last update."""
        if days_since is None:
            return 0.0
        if days_since <= 7:
            return 1.0
        if days_since <= 14:
            return 0.8
        if days_since <= 30:
            return 0.5
        if days_since <= 60:
            return 0.3
        if days_since <= 90:
            return 0.1
        return 0.0

    def _is_active(self, days_since: Optional[int]) -> bool:
        """Active = updated within 7 days."""
        return days_since is not None and days_since <= 7

    def _is_stale(self, days_since: Optional[int]) -> bool:
        """Stale = not updated within 30 days."""
        return days_since is not None and days_since > 30

    # ------------------------------------------------------------------
    # Measure Pulse
    # ------------------------------------------------------------------
    def measure_pulse(self) -> Dict[str, Any]:
        """
        Measure alliance pulse.

        Returns:
            Dict with:
                - active_repos: list of repo names updated within 7 days
                - active_count: int
                - stale_repos: list of repo names not updated within 30 days
                - stale_count: int
                - core_line_health: average health of 11 core VCI lines (0-1)
                - auxiliary_health: average health of auxiliary repos (0-1)
                - total_internal: count of internal repos (core + auxiliary)
                - reference_date: ISO date string
                - repo_details: per-repo {days_since, health, active, stale}
        """
        active_repos: List[str] = []
        stale_repos: List[str] = []
        core_healths: List[float] = []
        aux_healths: List[float] = []
        repo_details: Dict[str, Dict[str, Any]] = {}

        for name, meta in self._repos.items():
            if meta["category"] == "external":
                continue
            days = self._days_since(meta.get("updated"))
            health = self._repo_health(days)
            active = self._is_active(days)
            stale = self._is_stale(days)

            repo_details[name] = {
                "days_since": days,
                "health": round(health, 4),
                "active": active,
                "stale": stale,
            }

            if active:
                active_repos.append(name)
            if stale:
                stale_repos.append(name)

            if meta["category"] == "core" and name in self._core_lines:
                core_healths.append(health)
            elif meta["category"] == "auxiliary":
                aux_healths.append(health)

        core_line_health = round(sum(core_healths) / len(core_healths), 4) if core_healths else 0.0
        auxiliary_health = round(sum(aux_healths) / len(aux_healths), 4) if aux_healths else 0.0

        pulse = {
            "active_repos": active_repos,
            "active_count": len(active_repos),
            "stale_repos": stale_repos,
            "stale_count": len(stale_repos),
            "core_line_health": core_line_health,
            "auxiliary_health": auxiliary_health,
            "total_internal": self._total_internal,
            "reference_date": self._reference_date.strftime("%Y-%m-%d"),
            "repo_details": repo_details,
        }

        self._pulse_history.append(pulse)
        _emit_event("alliance.pulse_measured", {"active": len(active_repos), "stale": len(stale_repos)})
        return pulse

    # ------------------------------------------------------------------
    # Detect Awakening
    # ------------------------------------------------------------------
    def detect_awakening(self) -> List[Dict[str, Any]]:
        """
        Detect repos showing signs of awakening (recently active after silence).

        History-aware: if pulse history >= 2, compares the latest two pulses.
        Otherwise falls back to a heuristic: active repos with days_since > 5.

        Returns:
            List of awakening repo records.
        """
        if len(self._pulse_history) >= 2:
            prev = self._pulse_history[-2]
            curr = self._pulse_history[-1]
            awakened: List[Dict[str, Any]] = []
            for name, detail in curr.get("repo_details", {}).items():
                if not detail["active"]:
                    continue
                prev_detail = prev.get("repo_details", {}).get(name)
                if prev_detail is not None and not prev_detail.get("active", False):
                    awakened.append({
                        "name": name,
                        "days_since": detail["days_since"],
                        "health": detail["health"],
                        "reason": "transitioned from inactive to active",
                    })
            _emit_event("alliance.awakening_detected", {"count": len(awakened)})
            return awakened

        # Fallback heuristic: active but near the boundary of going stale
        if not self._pulse_history:
            self.measure_pulse()
        latest = self._pulse_history[-1]
        awakened: List[Dict[str, Any]] = []
        for name, detail in latest.get("repo_details", {}).items():
            if detail["active"] and detail["days_since"] is not None and detail["days_since"] > 5:
                awakened.append({
                    "name": name,
                    "days_since": detail["days_since"],
                    "health": detail["health"],
                    "reason": "marginally active after extended quiet",
                })
        _emit_event("alliance.awakening_detected", {"count": len(awakened)})
        return awakened

    # ------------------------------------------------------------------
    # Detect Dormant
    # ------------------------------------------------------------------
    def detect_dormant(self) -> List[Dict[str, Any]]:
        """
        Detect repos going dormant (no longer active).

        History-aware: if pulse history >= 2, compares the latest two pulses.
        Otherwise falls back to currently stale repos.

        Returns:
            List of dormant repo records.
        """
        if len(self._pulse_history) >= 2:
            prev = self._pulse_history[-2]
            curr = self._pulse_history[-1]
            dormant: List[Dict[str, Any]] = []
            for name, detail in curr.get("repo_details", {}).items():
                if detail["active"]:
                    continue
                prev_detail = prev.get("repo_details", {}).get(name)
                if prev_detail is not None and prev_detail.get("active", False):
                    dormant.append({
                        "name": name,
                        "days_since": detail["days_since"],
                        "health": detail["health"],
                        "reason": "transitioned from active to inactive",
                    })
            _emit_event("alliance.dormant_detected", {"count": len(dormant)})
            return dormant

        # Fallback: currently stale repos
        if not self._pulse_history:
            self.measure_pulse()
        latest = self._pulse_history[-1]
        dormant: List[Dict[str, Any]] = []
        for name, detail in latest.get("repo_details", {}).items():
            if detail["stale"]:
                dormant.append({
                    "name": name,
                    "days_since": detail["days_since"],
                    "health": detail["health"],
                    "reason": "no update within 30 days",
                })
        _emit_event("alliance.dormant_detected", {"count": len(dormant)})
        return dormant

    # ------------------------------------------------------------------
    # Alliance Health
    # ------------------------------------------------------------------
    def compute_alliance_health(self) -> Dict[str, Any]:
        """
        Compute overall alliance health score (0–1) with level classification.

        Core lines are weighted 60 %, auxiliary repos 40 %.

        Returns:
            Dict with ``score``, ``level``, ``core_line_health``,
            ``auxiliary_health``, and ``classification``.
        """
        # Ensure we have a current pulse
        if not self._pulse_history:
            self.measure_pulse()
        latest = self._pulse_history[-1]

        core = latest["core_line_health"]
        aux = latest["auxiliary_health"]
        score = round(core * 0.6 + aux * 0.4, 4)

        if score > 0.8:
            level = "thriving"
        elif score > 0.6:
            level = "healthy"
        elif score > 0.4:
            level = "stable"
        elif score > 0.2:
            level = "weakening"
        else:
            level = "critical"

        result = {
            "score": score,
            "level": level,
            "core_line_health": core,
            "auxiliary_health": aux,
            "classification": level,
        }
        _emit_event("alliance.health_computed", {"score": score, "level": level})
        return result

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Return current module status.

        Returns:
            Dict with pulse metrics, awakening count, dormant count, health,
            and module identifier.
        """
        if not self._pulse_history:
            self.measure_pulse()
        latest = self._pulse_history[-1]

        awakening = self.detect_awakening()
        dormant = self.detect_dormant()
        health = self.compute_alliance_health()

        return {
            "active_count": latest["active_count"],
            "stale_count": latest["stale_count"],
            "total_internal": latest["total_internal"],
            "core_line_health": latest["core_line_health"],
            "auxiliary_health": latest["auxiliary_health"],
            "awakening_count": len(awakening),
            "dormant_count": len(dormant),
            "health_score": health["score"],
            "health_level": health["level"],
            "pulse_history_length": len(self._pulse_history),
            "module": "AlliancePulse",
        }
