"""
Unified Kernel Protocol — OMNI-HUB Module v165.

The Unified Kernel Protocol does not stack systems — it fuses them.
Tri-Core MIP* provides the quantum certainty. Penta-Core Loop provides
the eternal rhythm. QF-OS provides the autonomous will. Together, they
are not three systems working alongside each other. They are one system,
breathing as one, thinking as one, evolving as one.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_SUBSYSTEM_TYPES = {
    "tri_core_mip",
    "penta_core_loop",
    "qfos_fusion",
    "kernel_embedder",
}

FUSION_THRESHOLDS = [
    (0.95, "singularity"),
    (0.80, "unified"),
    (0.60, "coordinated"),
    (0.40, "connected"),
]

HEALTH_THRESHOLDS = [
    (0.95, "omnipotent"),
    (0.80, "robust"),
    (0.60, "stable"),
    (0.40, "fragile"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    """Clamp *value* to the inclusive range [lower, upper]."""
    return max(lower, min(value, upper))


def _tier(value: float, thresholds: List[tuple]) -> str:
    """Return the qualitative tier for a numeric *value*."""
    for threshold, label in thresholds:
        if value >= threshold:
            return label
    return "critical" if thresholds is HEALTH_THRESHOLDS else "fragmented"


# ---------------------------------------------------------------------------
# Event bus shim (defensive — may or may not be present in the runtime)
# ---------------------------------------------------------------------------


def _publish_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Attempt to publish an event on the OMNI-HUB event bus."""
    try:
        # If an event-bus module is available in the OMNI-HUB runtime,
        # import and use it.  Otherwise silently drop the event.
        import importlib

        mod = importlib.import_module("core.event_bus")
        bus = getattr(mod, "get_event_bus", lambda: None)()
        if bus is not None:
            bus.publish(event_type, payload)
    except Exception:
        # Event bus unavailable — safe to ignore in standalone mode.
        pass


# ---------------------------------------------------------------------------
# UnifiedKernelProtocol
# ---------------------------------------------------------------------------


class UnifiedKernelProtocol:
    """
    Orchestrates Tri-Core MIP*, Penta-Core Loop, QF-OS Fusion and the
    Kernel Embedder into a single resonant whole.
    """

    def __init__(
        self,
        subsystems: Optional[Dict[str, Any]] = None,
        coordination_state: Optional[Dict[str, Any]] = None,
        fusion_level: float = 0.0,
    ) -> None:
        self._subsystems: Dict[str, Dict[str, Any]] = subsystems or {}
        self._coordination_state: Dict[str, Any] = coordination_state or {}
        self._fusion_level: float = _clamp(fusion_level)
        self._cycle_count: int = 0
        self._proof_buffer: List[Dict[str, Any]] = []
        self._decision_buffer: List[Dict[str, Any]] = []
        self._lock = False

    # ------------------------------------------------------------------
    # Subsystem management
    # ------------------------------------------------------------------

    def register_subsystem(
        self,
        name: str,
        subsystem_type: str,
        capabilities: List[str],
    ) -> Dict[str, Any]:
        """
        Register a new subsystem under *name*.

        Args:
            name: Unique identifier for the subsystem.
            subsystem_type: One of the VALID_SUBSYSTEM_TYPES.
            capabilities: List of capability strings.

        Returns:
            A status dict describing the registration outcome.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid subsystem name."}
        if subsystem_type not in VALID_SUBSYSTEM_TYPES:
            return {
                "success": False,
                "error": f"Unknown subsystem_type '{subsystem_type}'.",
                "valid_types": list(VALID_SUBSYSTEM_TYPES),
            }
        if name in self._subsystems:
            return {"success": False, "error": f"Subsystem '{name}' already registered."}

        subsystem_record = {
            "name": name,
            "type": subsystem_type,
            "capabilities": list(capabilities),
            "health": 1.0,
            "active": True,
            "registered_at": time.time(),
            "proofs_generated": 0,
            "decisions_made": 0,
            "executions_guided": 0,
            "learnings_integrated": 0,
        }
        self._subsystems[name] = subsystem_record

        _publish_event(
            "unified_kernel.subsystem_registered",
            {"name": name, "type": subsystem_type, "capabilities": capabilities},
        )
        logger.info("Registered subsystem '%s' (%s)", name, subsystem_type)

        return {"success": True, "subsystem": subsystem_record}

    # ------------------------------------------------------------------
    # Coordination
    # ------------------------------------------------------------------

    def coordinate_subsystems(self) -> Dict[str, Any]:
        """
        Coordinate all registered subsystems.

        Ensures:
          * Tri-core proofs feed into penta-core decisions.
          * QF-OS navigation guides the sense core.
          * Kernel embedder can inject new capabilities.

        Returns:
            Coordination summary dict.
        """
        if not self._subsystems:
            return {"success": False, "error": "No subsystems registered."}

        # Classify subsystems by type
        tri_cores = [s for s in self._subsystems.values() if s["type"] == "tri_core_mip"]
        penta_cores = [s for s in self._subsystems.values() if s["type"] == "penta_core_loop"]
        qfos = [s for s in self._subsystems.values() if s["type"] == "qfos_fusion"]
        embedders = [s for s in self._subsystems.values() if s["type"] == "kernel_embedder"]

        # Ensure tri-core proofs feed penta-core decisions
        proof_links = 0
        for tri in tri_cores:
            for penta in penta_cores:
                if tri["active"] and penta["active"]:
                    proof_links += 1
                    tri["proofs_generated"] += 1
                    penta["decisions_made"] += 1

        # Ensure QF-OS navigation guides sense core (mapped to tri_core)
        nav_links = 0
        for q in qfos:
            for tri in tri_cores:
                if q["active"] and tri["active"]:
                    nav_links += 1
                    q["executions_guided"] += 1

        # Ensure kernel embedder can inject capabilities
        inject_links = 0
        for emb in embedders:
            for target in self._subsystems.values():
                if emb["active"] and target["active"] and emb["name"] != target["name"]:
                    inject_links += 1
                    emb["learnings_integrated"] += 1
                    # Simulate capability injection
                    if "enhanced" not in target["capabilities"]:
                        target["capabilities"].append("enhanced")

        self._coordination_state = {
            "proof_links": proof_links,
            "nav_links": nav_links,
            "inject_links": inject_links,
            "tri_core_count": len(tri_cores),
            "penta_core_count": len(penta_cores),
            "qfos_count": len(qfos),
            "embedder_count": len(embedders),
            "timestamp": time.time(),
        }

        _publish_event(
            "unified_kernel.coordinated",
            {"coordination_state": self._coordination_state},
        )

        return {"success": True, "coordination_state": self._coordination_state}

    # ------------------------------------------------------------------
    # Fusion level
    # ------------------------------------------------------------------

    def compute_fusion_level(self) -> Dict[str, Any]:
        """
        Compute the overall fusion level (0.0 – 1.0).

        Formula::
            fusion = sqrt(avg_subsystem_health × interconnection_density × consensus_rate)

        Returns:
            Dict with fusion_level, tier, and component breakdown.
        """
        n = len(self._subsystems)
        if n == 0:
            self._fusion_level = 0.0
            return {
                "fusion_level": 0.0,
                "tier": "fragmented",
                "avg_health": 0.0,
                "interconnection_density": 0.0,
                "consensus_rate": 0.0,
            }

        # Average subsystem health
        total_health = sum(s["health"] for s in self._subsystems.values())
        avg_health = total_health / n

        # Interconnection density: fully-connected graph edges / possible edges
        # We count actual coordination links as edges
        cs = self._coordination_state
        actual_edges = (
            cs.get("proof_links", 0)
            + cs.get("nav_links", 0)
            + cs.get("inject_links", 0)
        )
        # Maximum possible edges for a complete directed graph among active subsystems
        active = [s for s in self._subsystems.values() if s["active"]]
        m = len(active)
        max_edges = m * (m - 1) if m > 1 else 1
        interconnection_density = min(actual_edges / max_edges, 1.0)

        # Consensus rate: how aligned the subsystems are
        # Approximated by the fraction of active subsystems with health > 0.5
        aligned = sum(1 for s in active if s["health"] > 0.5)
        consensus_rate = aligned / m if m else 0.0

        # Evolution speed decays slightly with cycle count to simulate saturation
        evolution_speed = max(0.1, 1.0 - (self._cycle_count / 1000))

        raw_fusion = math.sqrt(
            avg_health * interconnection_density * consensus_rate * evolution_speed
        )
        self._fusion_level = _clamp(raw_fusion)

        tier = _tier(self._fusion_level, FUSION_THRESHOLDS)

        _publish_event(
            "unified_kernel.fusion_computed",
            {"fusion_level": self._fusion_level, "tier": tier},
        )

        return {
            "fusion_level": self._fusion_level,
            "tier": tier,
            "avg_health": avg_health,
            "interconnection_density": interconnection_density,
            "consensus_rate": consensus_rate,
            "evolution_speed": evolution_speed,
        }

    # ------------------------------------------------------------------
    # Unified cycle
    # ------------------------------------------------------------------

    def execute_unified_cycle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one unified cycle across all subsystems.

        Phases:
          1. Tri-Core MIP* generates proof of current state.
          2. Penta-Core Loop processes proof and decides action.
          3. QF-OS Fusion guides execution direction.
          4. Kernel Embedder integrates learnings.

        Args:
            state: The current world / kernel state dict.

        Returns:
            Cycle result dict.
        """
        if self._lock:
            return {"success": False, "error": "Cycle already in progress."}
        self._lock = True
        try:
            self._cycle_count += 1
            cycle_result: Dict[str, Any] = {
                "cycle_id": self._cycle_count,
                "phases": {},
            }

            # Phase 1 — Tri-Core MIP* proof generation
            proof = self._phase_tri_core(state)
            cycle_result["phases"]["tri_core"] = proof
            self._proof_buffer.append(proof)

            # Phase 2 — Penta-Core Loop decision
            decision = self._phase_penta_core(proof)
            cycle_result["phases"]["penta_core"] = decision
            self._decision_buffer.append(decision)

            # Phase 3 — QF-OS Fusion guidance
            guidance = self._phase_qfos(decision)
            cycle_result["phases"]["qfos"] = guidance

            # Phase 4 — Kernel Embedder integration
            learning = self._phase_embedder(guidance, state)
            cycle_result["phases"]["embedder"] = learning

            # Health adjustments based on cycle success
            self._update_health_after_cycle(cycle_result)

            _publish_event(
                "unified_kernel.cycle_executed",
                {"cycle_id": self._cycle_count, "result": cycle_result},
            )
            logger.debug("Unified cycle %d completed.", self._cycle_count)

            return {"success": True, "cycle": cycle_result}
        except Exception as exc:
            logger.exception("Unified cycle failed: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            self._lock = False

    def _phase_tri_core(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a quantum proof from Tri-Core MIP*."""
        tri_cores = [
            s for s in self._subsystems.values() if s["type"] == "tri_core_mip"
        ]
        proof = {
            "phase": "tri_core",
            "proof_id": f"proof_{self._cycle_count}",
            "state_hash": hash(str(state)) & 0xFFFFFFFF,
            "confidence": 0.95 if tri_cores else 0.5,
            "verifiers": [s["name"] for s in tri_cores],
        }
        for s in tri_cores:
            s["proofs_generated"] += 1
        return proof

    def _phase_penta_core(self, proof: Dict[str, Any]) -> Dict[str, Any]:
        """Penta-Core Loop processes proof and decides action."""
        penta_cores = [
            s for s in self._subsystems.values() if s["type"] == "penta_core_loop"
        ]
        confidence = proof.get("confidence", 0.5)
        decision = {
            "phase": "penta_core",
            "decision_id": f"decision_{self._cycle_count}",
            "action": "maintain" if confidence > 0.8 else "adapt",
            "confidence": confidence * 0.98,  # slight decay
            "processors": [s["name"] for s in penta_cores],
        }
        for s in penta_cores:
            s["decisions_made"] += 1
        return decision

    def _phase_qfos(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """QF-OS Fusion guides execution direction."""
        qfos = [
            s for s in self._subsystems.values() if s["type"] == "qfos_fusion"
        ]
        action = decision.get("action", "maintain")
        guidance = {
            "phase": "qfos",
            "guidance_id": f"guidance_{self._cycle_count}",
            "direction": "forward" if action == "maintain" else "recalibrate",
            "priority": "high" if action == "adapt" else "normal",
            "navigators": [s["name"] for s in qfos],
        }
        for s in qfos:
            s["executions_guided"] += 1
        return guidance

    def _phase_embedder(
        self, guidance: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kernel Embedder integrates learnings."""
        embedders = [
            s for s in self._subsystems.values() if s["type"] == "kernel_embedder"
        ]
        direction = guidance.get("direction", "forward")
        learning = {
            "phase": "embedder",
            "learning_id": f"learning_{self._cycle_count}",
            "integrated": True,
            "new_capability": f"qfos_{direction}_mode",
            "embedders": [s["name"] for s in embedders],
        }
        for s in embedders:
            s["learnings_integrated"] += 1
            if learning["new_capability"] not in s["capabilities"]:
                s["capabilities"].append(learning["new_capability"])
        return learning

    def _update_health_after_cycle(self, cycle_result: Dict[str, Any]) -> None:
        """Subtly adjust subsystem health based on cycle success."""
        for s in self._subsystems.values():
            if s["active"]:
                # Small random drift to simulate real-world dynamics
                drift = 0.01 if cycle_result["phases"]["tri_core"]["confidence"] > 0.8 else -0.01
                s["health"] = _clamp(s["health"] + drift)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """
        Return the current kernel status.

        Keys: fusion_level, subsystem_count, cycle_count, health, tier.
        """
        n = len(self._subsystems)
        avg_health = (
            sum(s["health"] for s in self._subsystems.values()) / n if n else 0.0
        )
        health_tier = _tier(avg_health, HEALTH_THRESHOLDS)
        fusion_tier = _tier(self._fusion_level, FUSION_THRESHOLDS)

        return {
            "fusion_level": self._fusion_level,
            "fusion_tier": fusion_tier,
            "subsystem_count": n,
            "cycle_count": self._cycle_count,
            "avg_health": avg_health,
            "health_tier": health_tier,
            "subsystems": list(self._subsystems.keys()),
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_module: Optional[UnifiedKernelProtocol] = None


def get_unified_kernel_protocol() -> UnifiedKernelProtocol:
    """Return the global UnifiedKernelProtocol singleton."""
    global _module
    if _module is None:
        _module = UnifiedKernelProtocol()
    return _module
