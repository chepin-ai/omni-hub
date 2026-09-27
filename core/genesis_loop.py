"""
Genesis Loop (创世循环) — OMNI-HUB v140
Self-bootstrapping autonomous loop. System starts, runs, evolves without external trigger.
The final module that ties everything together.
"""

import time
from typing import Dict, Any, Optional, List

# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_module: Optional["GenesisLoop"] = None


def get_genesis_loop() -> "GenesisLoop":
    """Return the global GenesisLoop singleton instance."""
    global _module
    if _module is None:
        _module = GenesisLoop()
    return _module


# ---------------------------------------------------------------------------
# Optional event-bus integration
# ---------------------------------------------------------------------------
try:
    from core.event_bus import get_bus  # type: ignore
    from core.topics import Topics       # type: ignore
    _BUS_AVAILABLE = True
except Exception:
    _BUS_AVAILABLE = False


def _publish_state_change(payload: Dict[str, Any]) -> None:
    """Publish a STATE_CHANGE event if the event bus is available."""
    if not _BUS_AVAILABLE:
        return
    try:
        bus = get_bus()
        bus.publish_simple(Topics.STATE_CHANGE, payload)  # type: ignore
    except Exception:
        pass


# ---------------------------------------------------------------------------
# GenesisLoop
# ---------------------------------------------------------------------------
class GenesisLoop:
    """
    Self-bootstrapping autonomous loop.

    Attributes
    ----------
    initialized : bool
        Whether the boot sequence has completed.
    running : bool
        Whether the loop is currently running.
    cycle_count : int
        Number of completed autonomous cycles.
    boot_time : Optional[float]
        Unix timestamp recorded at boot completion.
    _next_evolution : str
        Cached evolution suggestion from the last tick / evolve call.
    _modules_present : List[str]
        Names of modules confirmed present during boot.
    """

    def __init__(self) -> None:
        self.initialized: bool = False
        self.running: bool = False
        self.cycle_count: int = 0
        self.boot_time: Optional[float] = None
        self._next_evolution: str = "none"
        self._modules_present: List[str] = []

    # ------------------------------------------------------------------
    # Boot
    # ------------------------------------------------------------------
    def boot(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the boot sequence.

        1. Scan the provided *state* for known module keys.
        2. If all critical modules are present, mark ``initialized``.
        3. Set ``boot_time`` and flip ``running`` to True.
        4. Return a boot-status dictionary.

        Parameters
        ----------
        state : dict
            System state dictionary expected to contain a ``modules`` key
            mapping module names to their health / coherence scores.

        Returns
        -------
        dict
            Boot result with keys ``success``, ``initialized``, ``running``,
            ``modules_present``, ``boot_time``.
        """
        try:
            modules = state.get("modules", {})
            critical = state.get("critical_modules", list(modules.keys()))

            self._modules_present = [
                name for name in critical
                if name in modules or name == "genesis_loop"
            ]

            all_present = all(
                name in modules or name == "genesis_loop"
                for name in critical
            )

            if all_present or not critical:
                self.initialized = True
                self.running = True
                self.boot_time = time.time()
                self.cycle_count = 0
                self._next_evolution = self._suggest_evolution(state)
            else:
                self.initialized = False
                self.running = False

            result = {
                "success": self.initialized,
                "initialized": self.initialized,
                "running": self.running,
                "modules_present": self._modules_present,
                "boot_time": self.boot_time,
            }

            _publish_state_change({
                "source": "genesis_loop",
                "event": "boot",
                "data": result,
            })

            return result

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "initialized": False,
                "running": False,
            }

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------
    def tick(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one autonomous cycle.

        1. Increment ``cycle_count``.
        2. Assess system health from *state*.
        3. Generate an evolution suggestion.
        4. Publish a STATE_CHANGE event.

        Parameters
        ----------
        state : dict
            Current system state (same shape as ``boot``).

        Returns
        -------
        dict
            Tick result with ``cycle_count``, ``health``, ``suggestion``.
        """
        try:
            if not self.initialized:
                return {
                    "cycle_count": self.cycle_count,
                    "health": 0.0,
                    "suggestion": "boot_required",
                    "error": "System not initialized — call boot() first.",
                }

            self.cycle_count += 1
            health = self._assess_health(state)
            self._next_evolution = self._suggest_evolution(state)

            result = {
                "cycle_count": self.cycle_count,
                "health": health,
                "suggestion": self._next_evolution,
            }

            _publish_state_change({
                "source": "genesis_loop",
                "event": "tick",
                "data": result,
            })

            return result

        except Exception as exc:
            return {
                "cycle_count": self.cycle_count,
                "health": 0.0,
                "suggestion": "error_recovery",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Evolve
    # ------------------------------------------------------------------
    def evolve(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Propose the next evolution step based on system state.

        The suggestion targets the weakest module or the module with the
        lowest line coherence score.

        Parameters
        ----------
        state : dict
            Current system state.

        Returns
        -------
        dict
            Evolution proposal with ``target_module``, ``action``,
            ``priority``.
        """
        try:
            suggestion = self._suggest_evolution(state)
            self._next_evolution = suggestion

            target = suggestion.replace("strengthen_", "").replace("coherence_", "")

            result = {
                "target_module": target,
                "action": suggestion,
                "priority": "high" if "coherence" in suggestion else "normal",
            }

            _publish_state_change({
                "source": "genesis_loop",
                "event": "evolve",
                "data": result,
            })

            return result

        except Exception as exc:
            return {
                "target_module": "unknown",
                "action": "error_recovery",
                "priority": "critical",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Return the current loop status.

        Returns
        -------
        dict
            Keys: ``running``, ``cycle_count``, ``uptime``, ``next_evolution``.
        """
        uptime: Optional[float] = None
        if self.boot_time is not None:
            uptime = time.time() - self.boot_time

        return {
            "running": self.running,
            "cycle_count": self.cycle_count,
            "uptime": uptime,
            "next_evolution": self._next_evolution,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _assess_health(self, state: Dict[str, Any]) -> float:
        """Compute average module health score (0.0–1.0)."""
        modules = state.get("modules", {})
        if not modules:
            return 0.0

        scores: List[float] = []
        for info in modules.values():
            if isinstance(info, dict):
                score = info.get("health", info.get("coherence", 0.5))
            elif isinstance(info, (int, float)):
                score = float(info)
            else:
                score = 0.5
            scores.append(score)

        return round(sum(scores) / len(scores), 4) if scores else 0.0

    def _suggest_evolution(self, state: Dict[str, Any]) -> str:
        """
        Identify the weakest module and return an evolution action string.

        Priority:
        1. Lowest ``coherence`` score.
        2. Lowest ``health`` score.
        3. Fallback to ``system_expansion`` if no modules listed.
        """
        modules = state.get("modules", {})
        if not modules:
            return "system_expansion"

        weakest_module: Optional[str] = None
        weakest_score: float = float("inf")

        for name, info in modules.items():
            if isinstance(info, dict):
                score = info.get("coherence", info.get("health", 0.5))
            elif isinstance(info, (int, float)):
                score = float(info)
            else:
                score = 0.5

            if score < weakest_score:
                weakest_score = score
                weakest_module = name

        if weakest_module is None:
            return "system_expansion"

        if weakest_score < 0.3:
            return f"coherence_{weakest_module}"
        return f"strengthen_{weakest_module}"
