"""
OMNI-HUB Adaptive Thresholds v23
Dynamic parameter self-tuning based on runtime performance.

The system monitors its own effectiveness and adjusts key parameters
when performance stagnates. Changes are conservative, tracked, and
reversible.

Philosophy: 候即违规 — static parameters in a dynamic system are a violation.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class ParameterAdjustment:
    """Record of a single parameter change."""
    param: str
    old_value: float
    new_value: float
    reason: str
    cycle: int
    timestamp: float = field(default_factory=time.time)


class AdaptiveThresholds:
    """Self-tuning parameter engine."""

    # Parameters that can be adjusted and their constraints
    TUNABLE_PARAMETERS = {
        "SELF_DRIVE_PHI_MIN": {"min": 0.05, "max": 0.3, "step": 0.01, "default": 0.15},
        "SELF_DRIVE_PLATEAU_THRESHOLD": {"min": 10, "max": 100, "step": 5, "default": 50},
        "SELF_DRIVE_CHECKPOINT_INTERVAL": {"min": 50, "max": 500, "step": 25, "default": 200},
        "LEVEL_25_STEADY_STATE_GROWTH": {"min": 1.0001, "max": 1.01, "step": 0.0001, "default": 1.001},
        "EM_CAP": {"min": 1.1, "max": 2.0, "step": 0.05, "default": 1.5},
    }

    def __init__(self):
        self.metrics_history: Dict[str, List[float]] = {}
        self.adjustments: List[ParameterAdjustment] = []
        self.cycle_count = 0
        self.last_adjustment_cycle = 0
        self.cooldown = 100  # Cycles between adjustments

    def track(self, metric: str, value: float):
        """Record a metric observation."""
        self.metrics_history.setdefault(metric, []).append(value)
        if len(self.metrics_history[metric]) > 500:
            self.metrics_history[metric] = self.metrics_history[metric][-500:]

    def _compute_trend(self, values: List[float]) -> float:
        """Compute trend direction: positive = improving, negative = degrading."""
        if len(values) < 20:
            return 0.0
        recent = values[-20:]
        older = values[-40:-20] if len(values) >= 40 else values[:len(values)//2]
        if not older:
            return 0.0
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        if older_avg == 0:
            return 0.0
        return (recent_avg - older_avg) / abs(older_avg)

    def evaluate(self, cycle: int) -> List[Dict[str, Any]]:
        """Evaluate all metrics and propose adjustments."""
        self.cycle_count = cycle
        proposals = []

        # Check cooldown
        if cycle - self.last_adjustment_cycle < self.cooldown:
            return proposals

        # Metric: energy_growth_rate
        if "energy_growth_rate" in self.metrics_history:
            trend = self._compute_trend(self.metrics_history["energy_growth_rate"])
            if trend < -0.1:
                # Growth declining — lower phi min to allow more reflect
                proposals.append({
                    "param": "SELF_DRIVE_PHI_MIN",
                    "direction": -1,
                    "reason": f"Energy growth declining (trend={trend:.3f})",
                })
            elif trend > 0.1:
                # Growth improving — can afford to be more selective
                proposals.append({
                    "param": "SELF_DRIVE_PHI_MIN",
                    "direction": 1,
                    "reason": f"Energy growth improving (trend={trend:.3f})",
                })

        # Metric: phi_variance
        if "phi_variance" in self.metrics_history:
            trend = self._compute_trend(self.metrics_history["phi_variance"])
            if trend < -0.2:
                # Phi too stable (stagnant) — increase plateau threshold
                proposals.append({
                    "param": "SELF_DRIVE_PLATEAU_THRESHOLD",
                    "direction": 1,
                    "reason": f"Phi stagnation detected (variance trend={trend:.3f})",
                })

        # Metric: level_up_interval (cycles between level-ups)
        if "level_up_interval" in self.metrics_history:
            values = self.metrics_history["level_up_interval"]
            if len(values) >= 3:
                recent_avg = sum(values[-3:]) / 3
                if recent_avg > 300:
                    # Leveling too slow — increase checkpoint frequency
                    proposals.append({
                        "param": "SELF_DRIVE_CHECKPOINT_INTERVAL",
                        "direction": -1,
                        "reason": f"Level progression slow (avg interval={recent_avg:.0f})",
                    })

        return proposals

    def apply(self, proposal: Dict[str, Any], constants_module: Any) -> bool:
        """Apply a parameter adjustment."""
        param = proposal["param"]
        direction = proposal["direction"]
        reason = proposal["reason"]

        if param not in self.TUNABLE_PARAMETERS:
            return False

        spec = self.TUNABLE_PARAMETERS[param]
        current = getattr(constants_module, param, spec["default"])
        new_value = current + direction * spec["step"]
        new_value = max(spec["min"], min(spec["max"], new_value))

        if new_value == current:
            return False

        # Apply change
        setattr(constants_module, param, new_value)
        self.adjustments.append(ParameterAdjustment(
            param=param, old_value=current, new_value=new_value,
            reason=reason, cycle=self.cycle_count,
        ))
        self.last_adjustment_cycle = self.cycle_count
        return True

    def get_status(self) -> Dict[str, Any]:
        """Return current tuning status."""
        recent = self.adjustments[-5:] if self.adjustments else []
        return {
            "total_adjustments": len(self.adjustments),
            "last_adjustment_cycle": self.last_adjustment_cycle,
            "cooldown_remaining": max(0, self.cooldown - (self.cycle_count - self.last_adjustment_cycle)),
            "recent_adjustments": [
                {"param": a.param, "old": a.old_value, "new": a.new_value, "reason": a.reason}
                for a in recent
            ],
            "metrics_tracked": list(self.metrics_history.keys()),
        }


if __name__ == "__main__":
    print("[OMNI-HUB v23] Adaptive Thresholds Demo")
    from core import constants as C

    tuner = AdaptiveThresholds()

    # Simulate declining growth
    for i in range(100):
        growth = 1.02 - i * 0.0002  # Declining growth
        tuner.track("energy_growth_rate", growth)

    proposals = tuner.evaluate(cycle=100)
    print(f"\nEvaluated at cycle 100:")
    print(f"  Proposals: {len(proposals)}")
    for p in proposals:
        print(f"  - {p['param']}: direction={p['direction']:+d}, reason={p['reason']}")

    if proposals:
        applied = tuner.apply(proposals[0], C)
        print(f"\nApplied: {applied}")
        print(f"  SELF_DRIVE_PHI_MIN: {C.SELF_DRIVE_PHI_MIN}")

    print(f"\n{tuner.get_status()}")
