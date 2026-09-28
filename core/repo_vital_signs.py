"""
OMNI-HUB Module v157: Repository Vital Signs (仓库生命体征)

仓库生命体征。为每个仓库建立完整的生命体征仪表盘：
- 心跳（提交频率 / commit frequency）
- 血压（issue/PR压力 / issue & PR pressure）
- 体温（代码活跃度 / code activity heat）
- 呼吸（贡献者流动 / contributor flow）
- 脑电波（创新指数 / innovation index）

这是仓库的"医学诊断系统"。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
import hashlib

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_module: Optional["RepoVitalSigns"] = None


def get_repo_vital_signs() -> "RepoVitalSigns":
    """Global singleton accessor for RepoVitalSigns."""
    global _module
    if _module is None:
        _module = RepoVitalSigns()
    return _module


# ---------------------------------------------------------------------------
# Event bus integration (defensive, best-effort)
# ---------------------------------------------------------------------------
def _emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit event to the OMNI-HUB event bus if available."""
    try:
        from core.event_bus import get_bus  # type: ignore
        bus = get_bus()
        bus.publish_simple(event_type, payload, source="repo_vital_signs")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# RepoVitalSigns
# ---------------------------------------------------------------------------
class RepoVitalSigns:
    """
    仓库生命体征 —— 为每个仓库建立完整的医学诊断仪表盘。

    Attributes:
        _repos: Flat dict of all repos with merged metadata.
        _vitals: Cache of per-repo vital signs measurements.
        _reference_date: The date used as "today" for recency calculations.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, reference_date: Optional[datetime] = None) -> None:
        """
        Load alliance_repos.json and initialise vitals cache.

        Args:
            reference_date: Override "today" for deterministic testing.
        """
        self._reference_date: datetime = reference_date or datetime(2026, 9, 28)
        self._repos: Dict[str, Dict[str, Any]] = {}
        self._vitals: Dict[str, Dict[str, Any]] = {}
        self._monitored_count: int = 0
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

        # alliance_core -> core VCI lines + omni-hub
        for name, meta in data.get("alliance_core", {}).items():
            self._repos[name] = {
                "name": name,
                "category": "core",
                "role": meta.get("line", "core"),
                "desc": meta.get("desc", ""),
                "lang": meta.get("lang"),
                "updated": meta.get("updated"),
            }

        # alliance_other -> auxiliary repos
        for name, meta in data.get("alliance_other", {}).items():
            self._repos[name] = {
                "name": name,
                "category": "auxiliary",
                "role": meta.get("role", "unknown"),
                "desc": meta.get("desc", ""),
                "lang": meta.get("lang"),
                "updated": meta.get("updated"),
            }

        # external_alliance -> tracked external repos
        for name, meta in data.get("external_alliance", {}).items():
            self._repos[name] = {
                "name": name,
                "category": "external",
                "role": meta.get("role", "external"),
                "desc": meta.get("desc", ""),
                "lang": meta.get("lang"),
                "updated": None,
            }

        self._monitored_count = len(self._repos)

    # ------------------------------------------------------------------
    # Helpers
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

    def _deterministic_int(self, repo_name: str, key: str, max_val: int) -> int:
        """Generate a deterministic pseudo-random integer for a repo."""
        h = hashlib.md5(f"{repo_name}:{key}".encode("utf-8")).hexdigest()
        return int(h, 16) % (max_val + 1)

    def _classify_health(self, score: float) -> str:
        """Classify an overall health score into a level."""
        if score > 0.9:
            return "excellent"
        if score > 0.7:
            return "good"
        if score > 0.5:
            return "fair"
        if score > 0.3:
            return "poor"
        return "critical"

    # ------------------------------------------------------------------
    # Heartbeat — commit frequency
    # ------------------------------------------------------------------
    def measure_heartbeat(self, repo_name: str) -> Dict[str, Any]:
        """
        Measure commit frequency (heartbeat) of a repository.

        Returns:
            Dict with bpm, category, and days_since_update.
        """
        meta = self._repos.get(repo_name)
        if meta is None:
            return {"repo": repo_name, "bpm": 0, "category": "unknown", "days_since": None}

        days = self._days_since(meta.get("updated"))

        if days is None:
            bpm = 20
            category = "dormant"
        elif days == 0:
            bpm = 120
            category = "very_active"
        elif days <= 7:
            bpm = 80
            category = "active"
        elif days <= 30:
            bpm = 50
            category = "moderate"
        else:
            bpm = 20
            category = "dormant"

        result = {
            "repo": repo_name,
            "bpm": bpm,
            "category": category,
            "days_since": days,
        }
        _emit_event("repo.heartbeat_measured", {"repo": repo_name, "bpm": bpm})
        return result

    # ------------------------------------------------------------------
    # Blood Pressure — issue/PR pressure
    # ------------------------------------------------------------------
    def measure_blood_pressure(self, repo_name: str) -> Dict[str, Any]:
        """
        Measure issue/PR pressure (blood pressure) of a repository.

        Simulated deterministically from repo name hash:
        - systolic: open issues count (0-20)
        - diastolic: open PRs count (0-10)
        - status: normal (<10) · elevated (10-15) · high (>15)

        Returns:
            Dict with systolic, diastolic, status, and normalized_pressure.
        """
        meta = self._repos.get(repo_name)
        if meta is None:
            return {
                "repo": repo_name,
                "systolic": 0,
                "diastolic": 0,
                "status": "unknown",
                "normalized": 0.0,
            }

        # Deterministic simulation based on repo name hash
        systolic = self._deterministic_int(repo_name, "issues", 20)
        diastolic = self._deterministic_int(repo_name, "prs", 10)

        if systolic < 10:
            status = "normal"
        elif systolic <= 15:
            status = "elevated"
        else:
            status = "high"

        # Normalized: lower pressure is healthier (0=high pressure, 1=no pressure)
        normalized = 1.0 - (systolic / 20.0)

        result = {
            "repo": repo_name,
            "systolic": systolic,
            "diastolic": diastolic,
            "status": status,
            "normalized": round(normalized, 4),
        }
        _emit_event("repo.blood_pressure_measured", {"repo": repo_name, "status": status})
        return result

    # ------------------------------------------------------------------
    # Temperature — code activity heat
    # ------------------------------------------------------------------
    def measure_temperature(self, repo_name: str) -> Dict[str, Any]:
        """
        Measure code activity heat (temperature) of a repository.

        Based on language and update recency:
        - Python + recent = hot (38-40°C)
        - Lean + old = cold (20-25°C)

        Returns:
            Dict with celsius, category, and normalized_temp.
        """
        meta = self._repos.get(repo_name)
        if meta is None:
            return {
                "repo": repo_name,
                "celsius": 20.0,
                "category": "unknown",
                "normalized": 0.0,
            }

        days = self._days_since(meta.get("updated"))
        lang = meta.get("lang")

        # Base temperature by recency
        if days is None:
            base_temp = 22.0
        elif days == 0:
            base_temp = 38.0
        elif days <= 7:
            base_temp = 35.0
        elif days <= 30:
            base_temp = 30.0
        elif days <= 60:
            base_temp = 25.0
        else:
            base_temp = 20.0

        # Language modifier
        if lang == "Python":
            lang_boost = 2.0
        elif lang == "Lean":
            lang_boost = -2.0
        elif lang in ("C++", "C#"):
            lang_boost = 0.0
        else:
            lang_boost = -1.0

        celsius = base_temp + lang_boost
        celsius = max(20.0, min(42.0, celsius))

        if celsius >= 38.0:
            category = "hot"
        elif celsius >= 30.0:
            category = "warm"
        elif celsius >= 25.0:
            category = "cool"
        else:
            category = "cold"

        # Normalized: 20°C -> 0, 40°C -> 1
        normalized = (celsius - 20.0) / 20.0

        result = {
            "repo": repo_name,
            "celsius": round(celsius, 2),
            "category": category,
            "normalized": round(normalized, 4),
        }
        _emit_event("repo.temperature_measured", {"repo": repo_name, "celsius": celsius})
        return result

    # ------------------------------------------------------------------
    # Brainwaves — innovation index
    # ------------------------------------------------------------------
    def measure_brainwaves(self, repo_name: str) -> Dict[str, Any]:
        """
        Measure innovation index (brainwaves) of a repository.

        Based on role type:
        - research / synthesis = high (0.8-1.0)
        - worker / framework / ml / dl / sdk / navigation = medium (0.4-0.6)
        - control / logs / bus / code / root / yard / playground = low (0.1-0.3)
        - core VCI lines = high (0.8-1.0)

        Returns:
            Dict with innovation_index, category, and description.
        """
        meta = self._repos.get(repo_name)
        if meta is None:
            return {
                "repo": repo_name,
                "innovation_index": 0.0,
                "category": "unknown",
                "description": "unknown",
            }

        role = meta.get("role", "unknown")
        category = meta.get("category", "unknown")

        high_roles = {"research", "synthesis", "framework", "ml", "dl", "sdk", "navigation"}
        medium_roles = {"worker", "inbox", "library", "playground", "yard"}
        low_roles = {"control", "logs", "bus", "code", "root"}

        if category == "core" or role in high_roles:
            idx = 0.85
            cat = "high"
            desc = "high innovation"
        elif role in medium_roles:
            idx = 0.5
            cat = "medium"
            desc = "moderate innovation"
        elif role in low_roles:
            idx = 0.2
            cat = "low"
            desc = "low innovation"
        else:
            idx = 0.5
            cat = "medium"
            desc = "moderate innovation"

        result = {
            "repo": repo_name,
            "innovation_index": idx,
            "category": cat,
            "description": desc,
        }
        _emit_event("repo.brainwaves_measured", {"repo": repo_name, "index": idx})
        return result

    # ------------------------------------------------------------------
    # Full Vitals — complete diagnostic
    # ------------------------------------------------------------------
    def get_full_vitals(self, repo_name: str) -> Dict[str, Any]:
        """
        Get all vital signs combined with an overall health score.

        Overall health is the average of:
        - normalized heartbeat (bpm / 120)
        - normalized blood pressure (1 - systolic/20)
        - normalized temperature (celsius - 20) / 20
        - brainwave innovation index (already 0-1)

        Health levels:
        - excellent (>0.9) · good (>0.7) · fair (>0.5) · poor (>0.3) · critical

        Returns:
            Dict with all four vitals and overall health score + level.
        """
        heartbeat = self.measure_heartbeat(repo_name)
        bp = self.measure_blood_pressure(repo_name)
        temp = self.measure_temperature(repo_name)
        brain = self.measure_brainwaves(repo_name)

        # Normalise each metric to 0-1
        norm_heartbeat = heartbeat["bpm"] / 120.0
        norm_bp = bp["normalized"]
        norm_temp = temp["normalized"]
        norm_brain = brain["innovation_index"]

        overall = round((norm_heartbeat + norm_bp + norm_temp + norm_brain) / 4.0, 4)
        level = self._classify_health(overall)

        result = {
            "repo": repo_name,
            "heartbeat": heartbeat,
            "blood_pressure": bp,
            "temperature": temp,
            "brainwaves": brain,
            "overall_health": overall,
            "health_level": level,
        }
        _emit_event("repo.full_vitals_measured", {"repo": repo_name, "health": overall, "level": level})
        return result

    # ------------------------------------------------------------------
    # Respiration — contributor flow
    # ------------------------------------------------------------------
    def measure_respiration(self, repo_name: str) -> Dict[str, Any]:
        """
        Measure contributor flow (respiration) of a repository.

        Simulated deterministically:
        - contributor_count: 1-20
        - turnover_rate: 0.0-1.0
        - flow_status: steady · growing · declining

        Returns:
            Dict with contributor_count, turnover_rate, and flow_status.
        """
        meta = self._repos.get(repo_name)
        if meta is None:
            return {
                "repo": repo_name,
                "contributor_count": 0,
                "turnover_rate": 0.0,
                "flow_status": "unknown",
            }

        contributor_count = self._deterministic_int(repo_name, "contributors", 20)
        turnover_rate = self._deterministic_int(repo_name, "turnover", 100) / 100.0

        if turnover_rate < 0.3:
            flow_status = "steady"
        elif turnover_rate < 0.7:
            flow_status = "growing"
        else:
            flow_status = "declining"

        result = {
            "repo": repo_name,
            "contributor_count": contributor_count,
            "turnover_rate": round(turnover_rate, 4),
            "flow_status": flow_status,
        }
        _emit_event("repo.respiration_measured", {"repo": repo_name, "contributors": contributor_count})
        return result

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Return aggregate status across all monitored repositories.

        Returns:
            Dict with monitored_count, avg_heartbeat, critical_count,
            health_distribution, and module identifier.
        """
        if not self._repos:
            return {
                "module": "RepoVitalSigns",
                "monitored_count": 0,
                "avg_heartbeat": 0.0,
                "critical_count": 0,
                "health_distribution": {},
            }

        total_bpm = 0
        critical_count = 0
        health_distribution: Dict[str, int] = {
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "poor": 0,
            "critical": 0,
        }

        for name in self._repos:
            vitals = self.get_full_vitals(name)
            total_bpm += vitals["heartbeat"]["bpm"]
            level = vitals["health_level"]
            health_distribution[level] = health_distribution.get(level, 0) + 1
            if level == "critical":
                critical_count += 1

        avg_heartbeat = round(total_bpm / len(self._repos), 2)

        status = {
            "module": "RepoVitalSigns",
            "monitored_count": len(self._repos),
            "avg_heartbeat": avg_heartbeat,
            "critical_count": critical_count,
            "health_distribution": health_distribution,
            "reference_date": self._reference_date.strftime("%Y-%m-%d"),
        }
        _emit_event("repo_vital_signs.status", status)
        return status
