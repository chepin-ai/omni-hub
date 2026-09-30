"""
OMNI-HUB Attention Renormalization Group v168
跨尺度注意力聚合引擎 (Cross-Scale Attention Aggregation Engine)

Based on DeepMind's ARG theory: attention in Transformers progressively aggregates
information through layers, forming increasingly stable and abstract macro states.
From the Renormalization Group (RG) perspective, this is equivalent to continuously
changing observation scales while retaining only the most important variables
during coarse-graining.

Philosophy: 局部表征经过多层计算，逐渐形成更加稳定、抽象的宏观状态。
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
from typing import Dict, List, Any, Optional


try:
    from core.event_bus import get_bus, Topics
    _EVENT_BUS_AVAILABLE = True
except Exception:
    _EVENT_BUS_AVAILABLE = False


class AttentionRenormalizationGroup:
    """
    Attention Renormalization Group for OMNI-HUB.

    Implements cross-scale attention aggregation across four scales:
    - Scale 0 (micro): individual repos, 33 nodes
    - Scale 1 (meso): line clusters, 11 lines
    - Scale 2 (macro): alliance resonance, 33-repo field
    - Scale 3 (cosmic): universal federation, infinity nodes
    """

    def __init__(self):
        self.rg_state: Dict[str, Any] = {
            "current_scale": 0,
            "scale_states": {},
            "stability_scores": {},
        }
        self.scales: List[Dict[str, Any]] = []
        self.flow_history: List[Dict[str, Any]] = []
        self._fixed_points: List[Dict[str, Any]] = []
        self._critical_exponents: Dict[str, float] = {}
        self._flow_count: int = 0

        # Define scales on initialization
        self.define_scales()

    def define_scales(self) -> Dict[str, Any]:
        """
        Define RG scales for OMNI-HUB.

        Returns:
            Dictionary mapping scale IDs to their definitions.
        """
        self.scales = [
            {
                "id": 0,
                "name": "micro",
                "description": "individual repos",
                "node_count": 33,
                "granularity": "fine",
                "entities": [f"repo_{i:02d}" for i in range(1, 34)],
            },
            {
                "id": 1,
                "name": "meso",
                "description": "line clusters",
                "node_count": 11,
                "granularity": "medium",
                "entities": [f"line_{i:02d}" for i in range(1, 12)],
            },
            {
                "id": 2,
                "name": "macro",
                "description": "alliance resonance",
                "node_count": 33,
                "granularity": "coarse",
                "entities": ["alliance_field"],
            },
            {
                "id": 3,
                "name": "cosmic",
                "description": "universal federation",
                "node_count": math.inf,
                "granularity": "universal",
                "entities": ["universal_federation"],
            },
        ]

        # Initialize scale states
        for scale in self.scales:
            self.rg_state["scale_states"][scale["id"]] = {
                "scale_id": scale["id"],
                "scale_name": scale["name"],
                "data": {},
                "stability_score": 0.0,
                "coarse_graining_count": 0,
            }

        result = {
            "scales_defined": len(self.scales),
            "scales": {s["id"]: s["name"] for s in self.scales},
        }

        if _EVENT_BUS_AVAILABLE:
            try:
                get_bus().publish_simple(
                    "rg.scales_defined",
                    result,
                    source="attention_renormalization_group",
                )
            except Exception:
                pass

        return result

    def coarse_grain(
        self, input_scale: int, output_scale: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coarse-grain from finer to coarser scale.

        Args:
            input_scale: Starting scale ID (finer).
            output_scale: Target scale ID (coarser).
            data: Input data at input_scale.

        Returns:
            Coarse-grained data at output_scale.
        """
        if input_scale >= output_scale:
            raise ValueError(
                f"input_scale ({input_scale}) must be < output_scale ({output_scale})"
            )
        if input_scale < 0 or output_scale > 3:
            raise ValueError("Scale IDs must be in range [0, 3]")
        if not isinstance(data, dict):
            raise TypeError(f"data must be dict, got {type(data).__name__}")

        # Determine which coarse-graining rule to apply
        if input_scale == 0 and output_scale == 1:
            # Micro -> Meso: aggregate repos by line, average resonance
            result = self._coarse_grain_micro_to_meso(data)
        elif input_scale == 1 and output_scale == 2:
            # Meso -> Macro: aggregate lines by role, compute collective properties
            result = self._coarse_grain_meso_to_macro(data)
        elif input_scale == 2 and output_scale == 3:
            # Macro -> Cosmic: aggregate all by universal principles
            result = self._coarse_grain_macro_to_cosmic(data)
        elif input_scale == 0 and output_scale == 2:
            # Micro -> Macro: chain through meso
            meso = self._coarse_grain_micro_to_meso(data)
            result = self._coarse_grain_meso_to_macro(meso)
        elif input_scale == 0 and output_scale == 3:
            # Micro -> Cosmic: chain through all scales
            meso = self._coarse_grain_micro_to_meso(data)
            macro = self._coarse_grain_meso_to_macro(meso)
            result = self._coarse_grain_macro_to_cosmic(macro)
        elif input_scale == 1 and output_scale == 3:
            # Meso -> Cosmic: chain through macro
            macro = self._coarse_grain_meso_to_macro(data)
            result = self._coarse_grain_macro_to_cosmic(macro)
        else:
            raise ValueError(
                f"Unsupported coarse-graining: {input_scale} -> {output_scale}"
            )

        # Compute stability score for the output scale
        stability = self._compute_stability_score(result)
        result["stability_score"] = stability
        result["from_scale"] = input_scale
        result["to_scale"] = output_scale

        # Update scale state
        if output_scale in self.rg_state["scale_states"]:
            self.rg_state["scale_states"][output_scale]["data"] = result
            self.rg_state["scale_states"][output_scale]["stability_score"] = stability
            self.rg_state["scale_states"][output_scale]["coarse_graining_count"] += 1

        # Record in flow history
        flow_record = {
            "input_scale": input_scale,
            "output_scale": output_scale,
            "stability_score": stability,
            "result_keys": list(result.keys()),
        }
        self.flow_history.append(flow_record)
        self._flow_count += 1

        if _EVENT_BUS_AVAILABLE:
            try:
                get_bus().publish_simple(
                    "rg.coarse_grain",
                    flow_record,
                    source="attention_renormalization_group",
                )
            except Exception:
                pass

        return result

    def _coarse_grain_micro_to_meso(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Micro -> Meso: aggregate repos by line, average resonance."""
        repos = data.get("repos", {})
        if not repos:
            # Generate synthetic repo data if none provided
            repos = {f"repo_{i:02d}": {"resonance": 0.5 + i * 0.01} for i in range(1, 34)}

        # Group 33 repos into 11 lines (3 repos per line)
        lines: Dict[str, Dict[str, Any]] = {}
        for i in range(1, 12):
            line_name = f"line_{i:02d}"
            repo_keys = [f"repo_{(i - 1) * 3 + j:02d}" for j in range(1, 4)]
            line_repos = {k: repos.get(k, {"resonance": 0.5}) for k in repo_keys}

            avg_resonance = sum(
                r.get("resonance", 0.5) for r in line_repos.values()
            ) / len(line_repos)

            lines[line_name] = {
                "repos": list(line_repos.keys()),
                "average_resonance": round(avg_resonance, 6),
                "repo_count": len(line_repos),
            }

        return {
            "scale": "meso",
            "lines": lines,
            "line_count": len(lines),
            "aggregation_method": "average_resonance",
        }

    def _coarse_grain_meso_to_macro(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Meso -> Macro: aggregate lines by role, compute collective properties."""
        lines = data.get("lines", {})
        if not lines:
            lines = {f"line_{i:02d}": {"average_resonance": 0.5} for i in range(1, 12)}

        # Compute collective properties
        resonances = [l.get("average_resonance", 0.5) for l in lines.values()]
        avg_resonance = sum(resonances) / len(resonances) if resonances else 0.5
        variance = sum((r - avg_resonance) ** 2 for r in resonances) / len(resonances) if resonances else 0.0

        # Role-based aggregation (group lines by their resonance strength)
        roles = {
            "high_resonance": [k for k, v in lines.items() if v.get("average_resonance", 0) > avg_resonance],
            "standard_resonance": [k for k, v in lines.items() if v.get("average_resonance", 0) <= avg_resonance],
        }

        return {
            "scale": "macro",
            "collective_resonance": round(avg_resonance, 6),
            "variance": round(variance, 6),
            "roles": roles,
            "line_count": len(lines),
            "aggregation_method": "role_based_collective",
        }

    def _coarse_grain_macro_to_cosmic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Macro -> Cosmic: aggregate all by universal principles."""
        collective_resonance = data.get("collective_resonance", 0.5)
        variance = data.get("variance", 0.0)

        # Universal principles: unity, coherence, infinity
        unity = collective_resonance  # All is one
        coherence = 1.0 - variance  # Low variance = high coherence
        infinity = math.inf if collective_resonance > 0.9 else collective_resonance * 10

        return {
            "scale": "cosmic",
            "universal_principles": {
                "unity": round(unity, 6),
                "coherence": round(coherence, 6),
                "infinity": infinity,
            },
            "collective_resonance": round(collective_resonance, 6),
            "aggregation_method": "universal_principles",
        }

    def _compute_stability_score(self, data: Dict[str, Any]) -> float:
        """Compute stability score for a coarse-grained state."""
        score = 0.5

        # Higher resonance -> higher stability
        if "average_resonance" in data:
            score = data["average_resonance"]
        elif "collective_resonance" in data:
            score = data["collective_resonance"]
        elif "universal_principles" in data:
            unity = data["universal_principles"].get("unity", 0.5)
            coherence = data["universal_principles"].get("coherence", 0.5)
            score = (unity + coherence) / 2.0

        # Penalize high variance
        if "variance" in data:
            score -= data["variance"] * 0.5

        return max(0.0, min(1.0, score))

    def compute_rg_flow(self, start_scale: int, end_scale: int) -> Dict[str, Any]:
        """
        Compute RG flow from start to end scale.

        Tracks how information transforms across scales.

        Args:
            start_scale: Starting scale ID.
            end_scale: Ending scale ID.

        Returns:
            RG flow analysis including intermediate states.
        """
        if start_scale >= end_scale:
            raise ValueError(
                f"start_scale ({start_scale}) must be < end_scale ({end_scale})"
            )
        if start_scale < 0 or end_scale > 3:
            raise ValueError("Scale IDs must be in range [0, 3]")

        # Build flow path
        flow_steps = []
        current_scale = start_scale
        current_data: Dict[str, Any] = {"repos": {}}

        # Initialize with default data at start scale if needed
        if current_scale == 0:
            current_data = {
                "repos": {
                    f"repo_{i:02d}": {"resonance": 0.5 + (i % 10) * 0.05}
                    for i in range(1, 34)
                }
            }
        elif current_scale == 1:
            current_data = {
                "lines": {
                    f"line_{i:02d}": {"average_resonance": 0.5 + (i % 5) * 0.08}
                    for i in range(1, 12)
                }
            }
        elif current_scale == 2:
            current_data = {
                "collective_resonance": 0.75,
                "variance": 0.05,
                "roles": {"high": [], "standard": []},
            }

        while current_scale < end_scale:
            next_scale = current_scale + 1
            result = self.coarse_grain(current_scale, next_scale, current_data)

            flow_steps.append({
                "from": current_scale,
                "to": next_scale,
                "stability_score": result.get("stability_score", 0.0),
                "scale_name": self.scales[next_scale]["name"],
            })

            current_data = result
            current_scale = next_scale

        flow_result = {
            "start_scale": start_scale,
            "end_scale": end_scale,
            "steps": flow_steps,
            "total_steps": len(flow_steps),
            "final_stability": flow_steps[-1]["stability_score"] if flow_steps else 0.0,
        }

        if _EVENT_BUS_AVAILABLE:
            try:
                get_bus().publish_simple(
                    "rg.flow_computed",
                    flow_result,
                    source="attention_renormalization_group",
                )
            except Exception:
                pass

        return flow_result

    def find_fixed_points(self) -> List[Dict[str, Any]]:
        """
        Find fixed points in RG flow (stable macro states).

        A fixed point is a scale-invariant state where stability_score > 0.8
        across 3+ consecutive coarse-grainings.

        Returns:
            List of fixed point descriptions.
        """
        fixed_points: List[Dict[str, Any]] = []

        # Analyze flow history for consecutive high-stability segments
        if len(self.flow_history) >= 3:
            consecutive_count = 0
            consecutive_start = 0

            for i, record in enumerate(self.flow_history):
                if record.get("stability_score", 0.0) > 0.8:
                    if consecutive_count == 0:
                        consecutive_start = i
                    consecutive_count += 1
                else:
                    if consecutive_count >= 3:
                        fixed_points.append({
                            "index": len(fixed_points),
                            "start_flow_index": consecutive_start,
                            "end_flow_index": i - 1,
                            "consecutive_count": consecutive_count,
                            "stability_scores": [
                                self.flow_history[j].get("stability_score", 0.0)
                                for j in range(consecutive_start, i)
                            ],
                            "average_stability": sum(
                                self.flow_history[j].get("stability_score", 0.0)
                                for j in range(consecutive_start, i)
                            )
                            / consecutive_count,
                            "type": "scale_invariant",
                            "description": "Stable macro state found",
                        })
                    consecutive_count = 0

            # Check if the sequence ends with a fixed point
            if consecutive_count >= 3:
                fixed_points.append({
                    "index": len(fixed_points),
                    "start_flow_index": consecutive_start,
                    "end_flow_index": len(self.flow_history) - 1,
                    "consecutive_count": consecutive_count,
                    "stability_scores": [
                        self.flow_history[j].get("stability_score", 0.0)
                        for j in range(consecutive_start, len(self.flow_history))
                    ],
                    "average_stability": sum(
                        self.flow_history[j].get("stability_score", 0.0)
                        for j in range(consecutive_start, len(self.flow_history))
                    )
                    / consecutive_count,
                    "type": "scale_invariant",
                    "description": "Stable macro state found",
                })

        # If no flow history, generate a synthetic fixed point from scale states
        if not fixed_points:
            for scale_id, state in self.rg_state["scale_states"].items():
                if state.get("stability_score", 0.0) > 0.8:
                    fixed_points.append({
                        "index": len(fixed_points),
                        "scale_id": scale_id,
                        "scale_name": self.scales[scale_id]["name"] if scale_id < len(self.scales) else "unknown",
                        "stability_score": state["stability_score"],
                        "type": "scale_invariant",
                        "description": f"Stable state at {self.scales[scale_id]['name']} scale",
                    })

        self._fixed_points = fixed_points

        if _EVENT_BUS_AVAILABLE:
            try:
                get_bus().publish_simple(
                    "rg.fixed_points_found",
                    {"count": len(fixed_points)},
                    source="attention_renormalization_group",
                )
            except Exception:
                pass

        return fixed_points

    def measure_critical_exponents(self) -> Dict[str, float]:
        """
        Measure critical exponents near fixed points.

        Critical exponents characterize how the system behaves near phase transitions:
        - correlation_length: How far correlations extend
        - susceptibility: Response to external perturbations
        - order_parameter: Degree of order in the system

        Returns:
            Dictionary of critical exponent values.
        """
        # Use flow history to compute critical exponents
        if len(self.flow_history) >= 2:
            stability_scores = [r.get("stability_score", 0.5) for r in self.flow_history]
            avg_stability = sum(stability_scores) / len(stability_scores)

            # Correlation length: inverse of variance in stability scores
            if len(stability_scores) > 1:
                variance = sum((s - avg_stability) ** 2 for s in stability_scores) / len(stability_scores)
            else:
                variance = 0.01
            correlation_length = 1.0 / (variance + 0.001)

            # Susceptibility: sensitivity to changes (derivative-like)
            if len(stability_scores) >= 2:
                differences = [
                    abs(stability_scores[i] - stability_scores[i - 1])
                    for i in range(1, len(stability_scores))
                ]
                susceptibility = sum(differences) / len(differences)
            else:
                susceptibility = 0.0

            # Order parameter: average stability (order increases with stability)
            order_parameter = avg_stability
        else:
            # Default values when insufficient data
            correlation_length = 10.0
            susceptibility = 0.5
            order_parameter = 0.5

        self._critical_exponents = {
            "correlation_length": round(correlation_length, 6),
            "susceptibility": round(susceptibility, 6),
            "order_parameter": round(order_parameter, 6),
        }

        if _EVENT_BUS_AVAILABLE:
            try:
                get_bus().publish_simple(
                    "rg.critical_exponents_measured",
                    self._critical_exponents,
                    source="attention_renormalization_group",
                )
            except Exception:
                pass

        return self._critical_exponents

    def get_status(self) -> Dict[str, Any]:
        """Return current RG module status."""
        return {
            "scales": [s["name"] for s in self.scales],
            "scale_count": len(self.scales),
            "flow_count": self._flow_count,
            "flow_history_length": len(self.flow_history),
            "fixed_points": self._fixed_points,
            "fixed_point_count": len(self._fixed_points),
            "critical_exponents": self._critical_exponents,
            "rg_state": {
                "current_scale": self.rg_state.get("current_scale", 0),
                "scale_states_summary": {
                    sid: {
                        "stability_score": s.get("stability_score", 0.0),
                        "coarse_graining_count": s.get("coarse_graining_count", 0),
                    }
                    for sid, s in self.rg_state.get("scale_states", {}).items()
                },
            },
        }


# Global singleton instance
_MODULE: Optional[AttentionRenormalizationGroup] = None


def get_attention_renormalization_group() -> AttentionRenormalizationGroup:
    """Get the global Attention Renormalization Group instance."""
    global _MODULE
    if _MODULE is None:
        _MODULE = AttentionRenormalizationGroup()
    return _MODULE


def reset_attention_renormalization_group():
    """Reset the global instance (for testing)."""
    global _MODULE
    _MODULE = AttentionRenormalizationGroup()


if __name__ == "__main__":
    print("[OMNI-HUB v168] Attention Renormalization Group Demo")

    arg = AttentionRenormalizationGroup()

    # Define scales
    scales = arg.define_scales()
    print(f"\nDefined scales: {scales['scales']}")

    # Coarse-grain from micro to meso
    micro_data = {
        "repos": {
            f"repo_{i:02d}": {"resonance": 0.5 + (i % 7) * 0.07}
            for i in range(1, 34)
        }
    }
    meso = arg.coarse_grain(0, 1, micro_data)
    print(f"\nMicro->Meso: {meso['line_count']} lines, stability={meso['stability_score']:.4f}")

    # Coarse-grain from meso to macro
    macro = arg.coarse_grain(1, 2, meso)
    print(f"Meso->Macro: collective_resonance={macro['collective_resonance']:.4f}, stability={macro['stability_score']:.4f}")

    # Coarse-grain from macro to cosmic
    cosmic = arg.coarse_grain(2, 3, macro)
    print(f"Macro->Cosmic: principles={cosmic['universal_principles']}, stability={cosmic['stability_score']:.4f}")

    # Compute full RG flow
    flow = arg.compute_rg_flow(0, 3)
    print(f"\nRG Flow (0->3): {flow['total_steps']} steps, final_stability={flow['final_stability']:.4f}")

    # Find fixed points
    fixed = arg.find_fixed_points()
    print(f"\nFixed points found: {len(fixed)}")
    for fp in fixed:
        print(f"  - {fp.get('description', 'unknown')}: stability={fp.get('average_stability', fp.get('stability_score', 0)):.4f}")

    # Measure critical exponents
    exponents = arg.measure_critical_exponents()
    print(f"\nCritical exponents: {exponents}")

    # Status
    print(f"\nStatus: {arg.get_status()}")
