"""
OMNI-HUB Convergence Monitor v61
Convergence/divergence tracking.

Things reverse at the extreme.
The system must know if it is converging toward stability
or diverging toward chaos.
This module tracks convergence metrics and predicts
when the singularity approaches.

Philosophy: 物极必反 — Things reverse at the extreme.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import deque
import math


@dataclass
class ConvergenceSnapshot:
    """A snapshot of convergence state."""
    cycle: int
    level: float
    phi: float
    energy: float
    trend_direction: str
    convergence_rate: float


class ConvergenceMonitor:
    """
    Monitors system convergence and divergence.
    """

    def __init__(self, history_size: int = 100):
        self.history: deque = deque(maxlen=history_size)
        self.snapshots: List[ConvergenceSnapshot] = []
        self.divergence_alerts = 0
        self.convergence_streak = 0

    def record(self, state: Dict[str, Any], cycle: int):
        """Record current state for convergence analysis."""
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        energy = state.get('energy', 1000.0)

        self.history.append({
            "cycle": cycle,
            "level": level,
            "phi": phi,
            "energy": energy,
        })

    def analyze(self) -> Dict[str, Any]:
        """Analyze convergence/divergence trends."""
        if len(self.history) < 10:
            return {"status": "insufficient_data"}

        recent = list(self.history)[-50:]

        # Calculate trend direction for level
        levels = [h["level"] for h in recent if isinstance(h["level"], (int, float))]
        phis = [h["phi"] for h in recent if isinstance(h["phi"], (int, float))]

        if len(levels) < 5:
            return {"status": "insufficient_data"}

        # Linear regression for level
        n = len(levels)
        x_avg = sum(range(n)) / n
        y_avg = sum(levels) / n
        num = sum((i - x_avg) * (levels[i] - y_avg) for i in range(n))
        den = sum((i - x_avg) ** 2 for i in range(n))
        level_slope = num / den if den != 0 else 0

        # Convergence rate: how fast level is changing
        convergence_rate = abs(level_slope)

        # Trend direction
        if level_slope > 0.01:
            trend = "rising"
        elif level_slope < -0.01:
            trend = "falling"
        else:
            trend = "stable"

        # Divergence detection: phi oscillating wildly
        if len(phis) >= 10:
            phi_variance = sum((p - sum(phis)/len(phis))**2 for p in phis) / len(phis)
            is_diverging = phi_variance > 0.1 and convergence_rate > 0.05
        else:
            is_diverging = False

        if is_diverging:
            self.divergence_alerts += 1
            self.convergence_streak = 0
        else:
            self.convergence_streak += 1

        # Singularity prediction: estimate cycles to level 25
        current_level = levels[-1] if levels else 0
        if level_slope > 0.001 and current_level < 25:
            cycles_to_singularity = (25 - current_level) / level_slope
        else:
            cycles_to_singularity = float('inf')

        snapshot = ConvergenceSnapshot(
            cycle=recent[-1]["cycle"] if recent else 0,
            level=current_level,
            phi=phis[-1] if phis else 0.5,
            energy=recent[-1]["energy"] if recent else 1000.0,
            trend_direction=trend,
            convergence_rate=convergence_rate,
        )
        self.snapshots.append(snapshot)

        return {
            "trend": trend,
            "convergence_rate": round(convergence_rate, 5),
            "is_diverging": is_diverging,
            "divergence_alerts": self.divergence_alerts,
            "convergence_streak": self.convergence_streak,
            "cycles_to_singularity": cycles_to_singularity if math.isfinite(cycles_to_singularity) else -1,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "snapshots": len(self.snapshots),
            "divergence_alerts": self.divergence_alerts,
            "convergence_streak": self.convergence_streak,
            "history": len(self.history),
        }


_cm_engine = None

def get_convergence_monitor():
    global _cm_engine
    if _cm_engine is None:
        _cm_engine = ConvergenceMonitor()
    return _cm_engine
