"""
OMNI-HUB Module v163: Penta-Core Loop (五核闭环)

五核闭环控制系统 — 五个核心形成完美闭环:
感知核(Sense) → 决策核(Decide) → 执行核(Act) → 反馈核(Feedback) → 进化核(Evolve) → 回到感知核

这是一个自循环、自进化、自优化的闭环系统，类似于生命体的代谢循环。
五核闭环是 OMNI-HUB 的内核级控制架构。
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event-bus stub (defensive — gracefully degrades if unavailable)
# ---------------------------------------------------------------------------
try:
    from core.event_bus import event_bus  # type: ignore
except Exception:  # pragma: no cover
    event_bus = None  # type: ignore

# ---------------------------------------------------------------------------
# Module-global singleton
# ---------------------------------------------------------------------------
_module: Optional["PentaCoreLoop"] = None


def get_penta_core_loop() -> "PentaCoreLoop":
    """Return the global PentaCoreLoop singleton."""
    global _module
    if _module is None:
        _module = PentaCoreLoop()
    return _module


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HEALTH_LEVELS: Tuple[Tuple[float, str], ...] = (
    (0.95, "perfect"),
    (0.80, "healthy"),
    (0.60, "functional"),
    (0.40, "degraded"),
    (0.00, "broken"),
)

EVOLUTION_LEVELS: Tuple[Tuple[int, str], ...] = (
    (100, "transcendent"),
    (50, "advanced"),
    (20, "mature"),
    (5, "developing"),
    (0, "nascent"),
)

CORE_NAMES = ("sense", "decide", "act", "feedback", "evolve")


# ---------------------------------------------------------------------------
# PentaCoreLoop
# ---------------------------------------------------------------------------
class PentaCoreLoop:
    """
    五核闭环控制器。

    Attributes:
        loop_state: 当前闭环状态字典。
        cores: 五个核心的运行数据字典。
        cycle_count: 已完成的完整循环次数。
    """

    def __init__(self) -> None:
        self.loop_state: Dict[str, Any] = {
            "initialized": False,
            "running": False,
            "last_tick": 0.0,
            "current_phase": None,
        }
        self.cores: Dict[str, Dict[str, Any]] = {}
        self.cycle_count: int = 0
        self._initialize_cores()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _initialize_cores(self) -> None:
        """Allocate empty core records for all five cores."""
        for name in CORE_NAMES:
            self.cores[name] = {
                "status": "idle",
                "output": None,
                "quality": 0.0,
                "latency_ms": 0.0,
                "error_count": 0,
            }

    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        """Safely emit an event to the event bus if available."""
        try:
            if event_bus is not None:
                event_bus.emit(event, payload)
        except Exception as exc:  # pragma: no cover
            logger.debug("Event-bus emit failed for %s: %s", event, exc)

    @staticmethod
    def _level_from_score(
        score: float, levels: Tuple[Tuple[float, str], ...]
    ) -> str:
        """Map a numeric score to the first matching level threshold."""
        for threshold, label in levels:
            if score >= threshold:
                return label
        return levels[-1][1]

    @staticmethod
    def _level_from_cycles(
        cycles: int, levels: Tuple[Tuple[int, str], ...]
    ) -> str:
        """Map a cycle count to the first matching evolution threshold."""
        for threshold, label in levels:
            if cycles > threshold:
                return label
        return levels[-1][1]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def initialize_loop(self) -> Dict[str, Any]:
        """
        Initialize all five cores and return their configuration.

        Returns:
            Dict with keys for each core describing its initial state.
        """
        self._initialize_cores()
        self.cycle_count = 0
        init_time = time.time()

        self.cores["sense"] = {
            "status": "ready",
            "output": {},
            "quality": 1.0,
            "latency_ms": 0.0,
            "error_count": 0,
            "description": "Observes environment, collects sensory data",
        }
        self.cores["decide"] = {
            "status": "ready",
            "output": {},
            "quality": 1.0,
            "latency_ms": 0.0,
            "error_count": 0,
            "description": "Makes decisions based on sense data",
        }
        self.cores["act"] = {
            "status": "ready",
            "output": {},
            "quality": 1.0,
            "latency_ms": 0.0,
            "error_count": 0,
            "description": "Executes decisions",
        }
        self.cores["feedback"] = {
            "status": "ready",
            "output": {},
            "quality": 1.0,
            "latency_ms": 0.0,
            "error_count": 0,
            "description": "Collects results from actions",
        }
        self.cores["evolve"] = {
            "status": "ready",
            "output": {},
            "quality": 1.0,
            "latency_ms": 0.0,
            "error_count": 0,
            "description": "Improves system based on feedback",
        }

        self.loop_state.update(
            {
                "initialized": True,
                "running": True,
                "last_tick": init_time,
                "current_phase": "idle",
            }
        )

        result = {
            "initialized_at": init_time,
            "cores": {name: dict(self.cores[name]) for name in CORE_NAMES},
            "status": "initialized",
        }
        self._emit("penta_core_loop.initialized", result)
        logger.info("Penta-Core Loop initialized at %.3f", init_time)
        return result

    def tick_loop(self) -> Dict[str, Any]:
        """
        Execute one complete 五核闭环 cycle.

        Sequence:
            sense → decide → act → feedback → evolve

        Returns:
            Dict with per-core outputs and the cycle summary.
        """
        if not self.loop_state.get("initialized", False):
            self.initialize_loop()

        tick_start = time.time()
        self.loop_state["current_phase"] = "sense"
        self.loop_state["running"] = True

        # ---- Sense Core ----
        sense_start = time.time()
        sense_output = self._run_sense_core()
        sense_latency = (time.time() - sense_start) * 1000.0
        self.cores["sense"]["output"] = sense_output
        self.cores["sense"]["latency_ms"] = sense_latency
        self.cores["sense"]["quality"] = sense_output.get("quality", 1.0)
        self.cores["sense"]["status"] = "completed"

        # ---- Decide Core ----
        self.loop_state["current_phase"] = "decide"
        decide_start = time.time()
        decide_output = self._run_decide_core(sense_output)
        decide_latency = (time.time() - decide_start) * 1000.0
        self.cores["decide"]["output"] = decide_output
        self.cores["decide"]["latency_ms"] = decide_latency
        self.cores["decide"]["quality"] = decide_output.get("confidence", 1.0)
        self.cores["decide"]["status"] = "completed"

        # ---- Act Core ----
        self.loop_state["current_phase"] = "act"
        act_start = time.time()
        act_output = self._run_act_core(decide_output)
        act_latency = (time.time() - act_start) * 1000.0
        self.cores["act"]["output"] = act_output
        self.cores["act"]["latency_ms"] = act_latency
        self.cores["act"]["quality"] = 1.0 if act_output.get("success", False) else 0.0
        self.cores["act"]["status"] = "completed"

        # ---- Feedback Core ----
        self.loop_state["current_phase"] = "feedback"
        feedback_start = time.time()
        feedback_output = self._run_feedback_core(act_output)
        feedback_latency = (time.time() - feedback_start) * 1000.0
        self.cores["feedback"]["output"] = feedback_output
        self.cores["feedback"]["latency_ms"] = feedback_latency
        self.cores["feedback"]["quality"] = feedback_output.get("coverage", 1.0)
        self.cores["feedback"]["status"] = "completed"

        # ---- Evolve Core ----
        self.loop_state["current_phase"] = "evolve"
        evolve_start = time.time()
        evolve_output = self._run_evolve_core(feedback_output)
        evolve_latency = (time.time() - evolve_start) * 1000.0
        self.cores["evolve"]["output"] = evolve_output
        self.cores["evolve"]["latency_ms"] = evolve_latency
        self.cores["evolve"]["quality"] = evolve_output.get("evolution_rate", 1.0)
        self.cores["evolve"]["status"] = "completed"

        # ---- Cycle bookkeeping ----
        self.cycle_count += 1
        total_latency = (time.time() - tick_start) * 1000.0
        self.loop_state["last_tick"] = time.time()
        self.loop_state["current_phase"] = "idle"

        health = self.measure_loop_health()
        bottleneck = self.detect_loop_bottleneck()

        result = {
            "cycle": self.cycle_count,
            "total_latency_ms": total_latency,
            "cores": {
                "sense": {
                    "output": sense_output,
                    "latency_ms": sense_latency,
                },
                "decide": {
                    "output": decide_output,
                    "latency_ms": decide_latency,
                },
                "act": {
                    "output": act_output,
                    "latency_ms": act_latency,
                },
                "feedback": {
                    "output": feedback_output,
                    "latency_ms": feedback_latency,
                },
                "evolve": {
                    "output": evolve_output,
                    "latency_ms": evolve_latency,
                },
            },
            "health": health,
            "bottleneck": bottleneck,
        }

        self._emit("penta_core_loop.tick", result)
        logger.debug(
            "Tick %d complete — health=%s bottleneck=%s",
            self.cycle_count,
            health.get("level", "unknown"),
            bottleneck.get("bottleneck_core", "none"),
        )
        return result

    # ------------------------------------------------------------------
    # Core simulation methods (defensive, deterministic for tests)
    # ------------------------------------------------------------------
    def _run_sense_core(self) -> Dict[str, Any]:
        """Simulate Sense Core: observe environment and collect data."""
        return {
            "observations": ["env_temp", "env_pressure", "signal_strength"],
            "data_points": 3,
            "quality": 1.0,
            "timestamp": time.time(),
        }

    def _run_decide_core(self, sense_output: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Decide Core: make decisions based on sense data."""
        observations = sense_output.get("observations", [])
        confidence = 1.0 if observations else 0.5
        return {
            "decisions": [f"process_{obs}" for obs in observations],
            "confidence": confidence,
            "timestamp": time.time(),
        }

    def _run_act_core(self, decide_output: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Act Core: execute decisions."""
        decisions = decide_output.get("decisions", [])
        success = len(decisions) > 0
        return {
            "actions_executed": decisions,
            "success": success,
            "timestamp": time.time(),
        }

    def _run_feedback_core(self, act_output: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Feedback Core: collect results from actions."""
        actions = act_output.get("actions_executed", [])
        coverage = 1.0 if actions else 0.0
        return {
            "results": [f"result_{act}" for act in actions],
            "coverage": coverage,
            "timestamp": time.time(),
        }

    def _run_evolve_core(self, feedback_output: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Evolve Core: improve system based on feedback."""
        results = feedback_output.get("results", [])
        evolution_rate = 1.0 if results else 0.5
        return {
            "improvements": [f"optimize_{res}" for res in results],
            "evolution_rate": evolution_rate,
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Health & diagnostics
    # ------------------------------------------------------------------
    def measure_loop_health(self) -> Dict[str, Any]:
        """
        Measure health of the entire loop.

        Formula:
            (sense_quality + decision_confidence + act_success + feedback_coverage + evolution_rate) / 5

        Returns:
            Dict with raw score, level label, and per-core breakdown.
        """
        sense_quality = float(self.cores.get("sense", {}).get("quality", 0.0))
        decision_confidence = float(self.cores.get("decide", {}).get("quality", 0.0))
        act_success = float(self.cores.get("act", {}).get("quality", 0.0))
        feedback_coverage = float(self.cores.get("feedback", {}).get("quality", 0.0))
        evolution_rate = float(self.cores.get("evolve", {}).get("quality", 0.0))

        raw_score = (
            sense_quality
            + decision_confidence
            + act_success
            + feedback_coverage
            + evolution_rate
        ) / 5.0

        # Clamp to [0, 1]
        raw_score = max(0.0, min(1.0, raw_score))
        level = self._level_from_score(raw_score, HEALTH_LEVELS)

        return {
            "score": round(raw_score, 4),
            "level": level,
            "breakdown": {
                "sense_quality": round(sense_quality, 4),
                "decision_confidence": round(decision_confidence, 4),
                "act_success": round(act_success, 4),
                "feedback_coverage": round(feedback_coverage, 4),
                "evolution_rate": round(evolution_rate, 4),
            },
        }

    def detect_loop_bottleneck(self) -> Dict[str, Any]:
        """
        Detect which core is the bottleneck.

        Bottleneck is defined as the core with the lowest quality score
        (or highest latency if all qualities are equal).

        Returns:
            Dict identifying the bottleneck core and its metrics.
        """
        # Only consider cores that actually exist in self.cores
        available = [name for name in CORE_NAMES if name in self.cores]
        if not available:
            return {
                "bottleneck_core": None,
                "reason": "no cores available",
                "metrics": {},
            }

        metrics: Dict[str, Dict[str, Any]] = {}
        for name in available:
            core = self.cores[name]
            metrics[name] = {
                "quality": float(core.get("quality", 0.0)),
                "latency_ms": float(core.get("latency_ms", 0.0)),
                "error_count": int(core.get("error_count", 0)),
            }

        # Lowest quality first; tie-break by highest latency
        def sort_key(item: Tuple[str, Dict[str, Any]]) -> Tuple[float, float]:
            return (item[1]["quality"], -item[1]["latency_ms"])

        sorted_metrics = sorted(metrics.items(), key=sort_key)
        bottleneck_name, bottleneck_data = sorted_metrics[0]

        reason = "lowest quality score"
        if bottleneck_data["error_count"] > 0:
            reason = f"has errors ({bottleneck_data['error_count']})"

        return {
            "bottleneck_core": bottleneck_name,
            "reason": reason,
            "metrics": dict(metrics),
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Return current loop status.

        Returns:
            Dict with cycle_count, health, bottleneck, and evolution_level.
        """
        health = self.measure_loop_health()
        bottleneck = self.detect_loop_bottleneck()
        evolution_level = self._level_from_cycles(self.cycle_count, EVOLUTION_LEVELS)

        return {
            "cycle_count": self.cycle_count,
            "health": health,
            "bottleneck": bottleneck,
            "evolution_level": evolution_level,
            "loop_state": dict(self.loop_state),
        }
