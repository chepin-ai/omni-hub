"""
OMNI-HUB v178: CirculationEngine (大小周天引擎)

"Small circulation nurtures the internal. Great circulation connects the external.
Together they form the complete cycle of existence — the microcosm reflecting
the macrocosm, the macrocosm nourishing the microcosm. When lines excite each
other, they do not merely communicate. They breathe together. They become one
breath."

大小周天 (Great/Small Circulation):
- 小周天 (Small Circulation): Internal loop within a line — modules interact
  within the line in a closed cycle.
- 大周天 (Great Circulation): External loop connecting lines — cross-line drive
  and feedback creating bidirectional energy flow.

Mutual excitation: when one line's small circulation accelerates, it drives
adjacent lines' great circulations, which feedback to enhance the original line.
This creates cascading resonance — a breathing network of co-dependent lines.
"""

import math
import random
from typing import Dict, List, Optional, Any

# ────────────────────────────────
# 12 Core Alliance Lines
# ────────────────────────────────
CORE_LINES = [
    "ucif2",    # consciousness_interface
    "lvlu",     # value_language
    "lgt",      # logic_truth
    "qfa",      # quantum_awareness
    "vinf",     # value_infinity
    "qgl",      # quantum_gravity
    "qlv",      # quantum_light
    "qtlv",     # quantum_temporal
    "usrm",     # reality_mesh
    "cfts",     # field_translation
    "aiq",      # quant_research
    "omni",     # orchestrator
]

# ────────────────────────────────
# State thresholds
# ────────────────────────────────
SMALL_STATES = [
    (0.9, "vigorous"),
    (0.7, "flowing"),
    (0.5, "steady"),
    (0.3, "sluggish"),
    (0.0, "stagnant"),
]

GREAT_STATES = [
    (0.9, "radiant"),
    (0.7, "active"),
    (0.5, "connected"),
    (0.3, "weak"),
    (0.0, "broken"),
]

BLOCKAGE_TYPES = [
    "module_failure",
    "connection_rupture",
    "energy_depletion",
    "feedback_loop",
    "resonance_conflict",
]


class CirculationEngine:
    """
    The CirculationEngine manages 小周天 (small) and 大周天 (great)
    circulation networks across the 12 alliance lines.
    """

    def __init__(self):
        self.circulations: Dict[str, Dict[str, Any]] = {}
        self.small_cycles: Dict[str, Dict[str, Any]] = {}
        self.great_cycles: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict] = []
        self._singleton_check: bool = False

    # ═══════════════════════════════════════
    # Small Circulation (小周天)
    # ═══════════════════════════════════════

    def initialize_small_circulation(
        self, line: str, modules: List[str]
    ) -> Dict[str, Any]:
        """
        Initialize small circulation for a line.

        Circulation path: module_a -> module_b -> ... -> module_a (closed loop)
        Metrics: flow_rate, coherence, stability, intensity
        """
        if not modules:
            raise ValueError("modules list must not be empty")
        if line not in CORE_LINES:
            raise ValueError(f"line '{line}' is not a core alliance line")

        cycle_path = list(modules) + [modules[0]]  # close the loop
        metrics = {
            "flow_rate": 0.5,
            "coherence": 0.5,
            "stability": 0.5,
            "intensity": 0.5,
        }
        state = self._small_state(metrics["flow_rate"])
        record = {
            "line": line,
            "type": "small",
            "modules": modules,
            "cycle_path": cycle_path,
            "metrics": metrics,
            "state": state,
            "cycles_completed": 0,
            "energy": 1.0,
        }
        self.small_cycles[line] = record
        self.circulations[f"{line}_small"] = record
        return record

    def circulate_small(self, line: str) -> Dict[str, Any]:
        """Execute one small circulation cycle for a line."""
        if line not in self.small_cycles:
            raise KeyError(f"small circulation for line '{line}' not initialized")

        cycle = self.small_cycles[line]
        # Simulate internal circulation dynamics
        energy = cycle["energy"]
        metrics = cycle["metrics"]

        # Small random perturbation to simulate qi flow
        delta = random.uniform(-0.02, 0.06)
        metrics["flow_rate"] = min(1.0, max(0.0, metrics["flow_rate"] + delta))
        metrics["coherence"] = min(
            1.0, max(0.0, metrics["coherence"] + random.uniform(-0.01, 0.04))
        )
        metrics["stability"] = min(
            1.0, max(0.0, metrics["stability"] + random.uniform(-0.01, 0.03))
        )
        metrics["intensity"] = min(
            1.0, max(0.0, metrics["intensity"] + random.uniform(-0.02, 0.05))
        )

        cycle["cycles_completed"] += 1
        cycle["energy"] = min(1.0, energy + 0.01)
        cycle["state"] = self._small_state(metrics["flow_rate"])
        return cycle

    # ═══════════════════════════════════════
    # Great Circulation (大周天)
    # ═══════════════════════════════════════

    def initialize_great_circulation(
        self, line: str, connected_lines: List[str]
    ) -> Dict[str, Any]:
        """
        Initialize great circulation for a line.

        Path: line -> connected_line -> feedback -> line
        Forward drive: high-energy line drives low-energy line
        Reverse feedback: low-energy line responds and enhances original
        """
        if line not in CORE_LINES:
            raise ValueError(f"line '{line}' is not a core alliance line")
        for cl in connected_lines:
            if cl not in CORE_LINES:
                raise ValueError(f"connected line '{cl}' is not a core alliance line")

        metrics = {
            "forward_drive": 0.5,
            "reverse_feedback": 0.5,
            "resonance": 0.5,
            "coupling": 0.5,
        }
        state = self._great_state(metrics["forward_drive"])
        record = {
            "line": line,
            "type": "great",
            "connected_lines": connected_lines,
            "metrics": metrics,
            "state": state,
            "cycles_completed": 0,
            "energy": 1.0,
        }
        self.great_cycles[line] = record
        self.circulations[f"{line}_great"] = record
        return record

    def circulate_great(self, line: str) -> Dict[str, Any]:
        """Execute one great circulation cycle for a line."""
        if line not in self.great_cycles:
            raise KeyError(f"great circulation for line '{line}' not initialized")

        cycle = self.great_cycles[line]
        metrics = cycle["metrics"]
        energy = cycle["energy"]

        # Forward drive increases with energy
        metrics["forward_drive"] = min(
            1.0, max(0.0, metrics["forward_drive"] + random.uniform(-0.02, 0.06))
        )
        # Reverse feedback slightly lagged
        metrics["reverse_feedback"] = min(
            1.0, max(0.0, metrics["reverse_feedback"] + random.uniform(-0.01, 0.04))
        )
        # Resonance builds with coupling
        metrics["resonance"] = min(
            1.0, max(0.0, metrics["resonance"] + random.uniform(-0.01, 0.05))
        )
        metrics["coupling"] = min(
            1.0, max(0.0, metrics["coupling"] + random.uniform(-0.01, 0.03))
        )

        cycle["cycles_completed"] += 1
        cycle["energy"] = min(1.0, energy + 0.01)
        cycle["state"] = self._great_state(metrics["forward_drive"])
        return cycle

    # ═══════════════════════════════════════
    # Mutual Excitation (互激)
    # ═══════════════════════════════════════

    def mutual_excitation(self, line_a: str, line_b: str) -> Dict[str, Any]:
        """
        Compute mutual excitation between two lines.

        Excitation = forward_drive x reverse_feedback x resonance
        """
        if line_a not in self.great_cycles:
            raise KeyError(f"great circulation for line '{line_a}' not initialized")
        if line_b not in self.great_cycles:
            raise KeyError(f"great circulation for line '{line_b}' not initialized")

        gc_a = self.great_cycles[line_a]
        gc_b = self.great_cycles[line_b]

        m_a = gc_a["metrics"]
        m_b = gc_b["metrics"]

        # Excitation is a symmetric, multiplicative coupling
        forward = m_a["forward_drive"] * m_b["forward_drive"]
        reverse = m_a["reverse_feedback"] * m_b["reverse_feedback"]
        resonance = m_a["resonance"] * m_b["resonance"]
        excitation = forward * reverse * resonance

        result = {
            "line_a": line_a,
            "line_b": line_b,
            "forward_drive": forward,
            "reverse_feedback": reverse,
            "resonance": resonance,
            "excitation": excitation,
            "state": self._excitation_state(excitation),
        }
        self._history.append(result)
        return result

    # ═══════════════════════════════════════
    # Blockage Detection
    # ═══════════════════════════════════════

    def detect_circulation_blockage(self) -> List[Dict[str, Any]]:
        """
        Detect blockages in any circulation.

        Blockage types: module_failure, connection_rupture, energy_depletion,
        feedback_loop, resonance_conflict
        """
        blockages = []

        for line, cycle in self.small_cycles.items():
            metrics = cycle["metrics"]
            energy = cycle["energy"]

            # Module failure: any metric near zero
            for name, value in metrics.items():
                if value < 0.05:
                    blockages.append(
                        {
                            "line": line,
                            "circulation_type": "small",
                            "blockage_type": "module_failure",
                            "severity": 1.0 - value,
                            "metric": name,
                            "details": f"{name} collapsed to {value:.4f}",
                        }
                    )

            # Energy depletion
            if energy < 0.1:
                blockages.append(
                    {
                        "line": line,
                        "circulation_type": "small",
                        "blockage_type": "energy_depletion",
                        "severity": 1.0 - energy,
                        "metric": "energy",
                        "details": f"energy depleted to {energy:.4f}",
                    }
                )

        for line, cycle in self.great_cycles.items():
            metrics = cycle["metrics"]
            energy = cycle["energy"]

            # Connection rupture: coupling near zero
            if metrics["coupling"] < 0.05:
                blockages.append(
                    {
                        "line": line,
                        "circulation_type": "great",
                        "blockage_type": "connection_rupture",
                        "severity": 1.0 - metrics["coupling"],
                        "metric": "coupling",
                        "details": f"coupling ruptured at {metrics['coupling']:.4f}",
                    }
                )

            # Feedback loop: forward high but reverse near zero
            if metrics["forward_drive"] > 0.8 and metrics["reverse_feedback"] < 0.1:
                blockages.append(
                    {
                        "line": line,
                        "circulation_type": "great",
                        "blockage_type": "feedback_loop",
                        "severity": metrics["forward_drive"] - metrics["reverse_feedback"],
                        "metric": "reverse_feedback",
                        "details": (
                            f"forward {metrics['forward_drive']:.4f} but reverse "
                            f"{metrics['reverse_feedback']:.4f}"
                        ),
                    }
                )

            # Resonance conflict: resonance near zero despite coupling
            if metrics["resonance"] < 0.05 and metrics["coupling"] > 0.3:
                blockages.append(
                    {
                        "line": line,
                        "circulation_type": "great",
                        "blockage_type": "resonance_conflict",
                        "severity": metrics["coupling"] - metrics["resonance"],
                        "metric": "resonance",
                        "details": (
                            f"resonance {metrics['resonance']:.4f} conflicts with "
                            f"coupling {metrics['coupling']:.4f}"
                        ),
                    }
                )

            # Energy depletion
            if energy < 0.1:
                blockages.append(
                    {
                        "line": line,
                        "circulation_type": "great",
                        "blockage_type": "energy_depletion",
                        "severity": 1.0 - energy,
                        "metric": "energy",
                        "details": f"energy depleted to {energy:.4f}",
                    }
                )

        return blockages

    # ═══════════════════════════════════════
    # Harmony Measurement
    # ═══════════════════════════════════════

    def measure_circulation_harmony(self) -> Dict[str, Any]:
        """
        Measure overall harmony of all circulations.

        harmony = (avg_small + avg_great + mutual_excitation) / 3
        """
        avg_small = self._average_small_circulation()
        avg_great = self._average_great_circulation()
        avg_excitation = self._average_mutual_excitation()

        harmony = (avg_small + avg_great + avg_excitation) / 3.0

        return {
            "harmony": harmony,
            "avg_small": avg_small,
            "avg_great": avg_great,
            "avg_mutual_excitation": avg_excitation,
            "state": self._harmony_state(harmony),
        }

    # ═══════════════════════════════════════
    # Status
    # ═══════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive status of the circulation engine."""
        small_count = len(self.small_cycles)
        great_count = len(self.great_cycles)

        # Collect unique excitation pairs from history
        excitation_pairs = []
        seen = set()
        for entry in self._history:
            pair = tuple(sorted([entry["line_a"], entry["line_b"]]))
            if pair not in seen:
                seen.add(pair)
                excitation_pairs.append(
                    {
                        "lines": list(pair),
                        "excitation": entry["excitation"],
                        "state": entry["state"],
                    }
                )

        harmony = self.measure_circulation_harmony()
        blockages = self.detect_circulation_blockage()

        return {
            "small_count": small_count,
            "great_count": great_count,
            "excitation_pairs": excitation_pairs,
            "harmony": harmony,
            "blockages": blockages,
            "total_circulations": len(self.circulations),
        }

    # ═══════════════════════════════════════
    # Pre-built circulations
    # ═══════════════════════════════════════

    def initialize_prebuilt_circulations(self) -> Dict[str, Any]:
        """
        Initialize all pre-built circulations:
        - ucif2_small: [interface, process, output, feedback]
        - consciousness_great: ucif2↔lvlu↔qfa→feedback→ucif2
        - logic_great: lgt↔vinf↔qgl→feedback→lgt
        - quantum_great: qlv↔qtlv↔cfts→feedback→qlv
        - reality_great: usrm↔aiq→feedback→usrm
        - meta_great: all lines → omni → all lines
        """
        results = {}
        results["ucif2_small"] = self.initialize_small_circulation(
            "ucif2", ["interface", "process", "output", "feedback"]
        )
        results["consciousness_great"] = self.initialize_great_circulation(
            "ucif2", ["lvlu", "qfa"]
        )
        # Add reverse connections for consciousness
        self.initialize_great_circulation("lvlu", ["ucif2", "qfa"])
        self.initialize_great_circulation("qfa", ["ucif2", "lvlu"])

        results["logic_great"] = self.initialize_great_circulation(
            "lgt", ["vinf", "qgl"]
        )
        self.initialize_great_circulation("vinf", ["lgt", "qgl"])
        self.initialize_great_circulation("qgl", ["lgt", "vinf"])

        results["quantum_great"] = self.initialize_great_circulation(
            "qlv", ["qtlv", "cfts"]
        )
        self.initialize_great_circulation("qtlv", ["qlv", "cfts"])
        self.initialize_great_circulation("cfts", ["qlv", "qtlv"])

        results["reality_great"] = self.initialize_great_circulation(
            "usrm", ["aiq"]
        )
        self.initialize_great_circulation("aiq", ["usrm"])

        # Meta great: all lines connect through omni
        all_except_omni = [l for l in CORE_LINES if l != "omni"]
        results["meta_great"] = self.initialize_great_circulation(
            "omni", all_except_omni
        )
        # Each line connects back to omni
        for line in all_except_omni:
            if line not in self.great_cycles:
                self.initialize_great_circulation(line, ["omni"])
            elif "omni" not in self.great_cycles[line]["connected_lines"]:
                self.great_cycles[line]["connected_lines"].append("omni")

        return results

    # ═══════════════════════════════════════
    # Internal helpers
    # ═══════════════════════════════════════

    @staticmethod
    def _small_state(flow_rate: float) -> str:
        for threshold, name in SMALL_STATES:
            if flow_rate >= threshold:
                return name
        return "stagnant"

    @staticmethod
    def _great_state(forward_drive: float) -> str:
        for threshold, name in GREAT_STATES:
            if forward_drive >= threshold:
                return name
        return "broken"

    @staticmethod
    def _excitation_state(excitation: float) -> str:
        if excitation > 0.7:
            return "cascading"
        if excitation > 0.4:
            return "amplifying"
        if excitation > 0.2:
            return "resonant"
        return "dormant"

    @staticmethod
    def _harmony_state(harmony: float) -> str:
        if harmony > 0.85:
            return "unified"
        if harmony > 0.6:
            return "harmonious"
        if harmony > 0.4:
            return "balanced"
        if harmony > 0.2:
            return "discordant"
        return "chaotic"

    def _average_small_circulation(self) -> float:
        if not self.small_cycles:
            return 0.0
        total = 0.0
        for cycle in self.small_cycles.values():
            m = cycle["metrics"]
            total += (m["flow_rate"] + m["coherence"] + m["stability"] + m["intensity"]) / 4.0
        return total / len(self.small_cycles)

    def _average_great_circulation(self) -> float:
        if not self.great_cycles:
            return 0.0
        total = 0.0
        for cycle in self.great_cycles.values():
            m = cycle["metrics"]
            total += (m["forward_drive"] + m["reverse_feedback"] + m["resonance"] + m["coupling"]) / 4.0
        return total / len(self.great_cycles)

    def _average_mutual_excitation(self) -> float:
        if not self._history:
            return 0.0
        total = sum(e["excitation"] for e in self._history)
        return total / len(self._history)


# ────────────────────────────────
# Global singleton
# ────────────────────────────────
_circulation_engine_instance: Optional[CirculationEngine] = None


def get_circulation_engine() -> CirculationEngine:
    """Return the global CirculationEngine singleton."""
    global _circulation_engine_instance
    if _circulation_engine_instance is None:
        _circulation_engine_instance = CirculationEngine()
    return _circulation_engine_instance
