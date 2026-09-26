"""
OMNI-HUB Information Theory Core v63
Entropy and mutual information.

Information is physical.
It has mass, energy, and structure.
This module measures the information content of the system —
its entropy, its complexity, its organization.

Philosophy: 信息是物理的 — Information is physical.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from collections import Counter
import math


class InformationTheoryCore:
    """
    Measures information-theoretic properties of system state.
    """

    def __init__(self):
        self.measurement_count = 0

    def entropy(self, values: List[float], bins: int = 10) -> float:
        """Calculate Shannon entropy of a distribution."""
        if not values:
            return 0.0

        # Discretize into bins
        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            return 0.0

        bin_counts = [0] * bins
        for v in values:
            idx = min(bins - 1, int((v - min_val) / (max_val - min_val) * bins))
            bin_counts[idx] += 1

        total = len(values)
        entropy = 0.0
        for count in bin_counts:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        return entropy

    def mutual_information(self, x: List[float], y: List[float], bins: int = 5) -> float:
        """Calculate mutual information between two variables."""
        if len(x) != len(y) or len(x) < 5:
            return 0.0

        # Joint histogram
        joint_counts = Counter()
        x_counts = Counter()
        y_counts = Counter()

        for i in range(len(x)):
            joint_counts[(x[i], y[i])] += 1
            x_counts[x[i]] += 1
            y_counts[y[i]] += 1

        mi = 0.0
        n = len(x)
        for (xv, yv), count in joint_counts.items():
            p_xy = count / n
            p_x = x_counts[xv] / n
            p_y = y_counts[yv] / n
            if p_x > 0 and p_y > 0:
                mi += p_xy * math.log2(p_xy / (p_x * p_y))

        return max(0, mi)

    def system_entropy(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Calculate entropy of key system variables."""
        result = {}

        # We need history for entropy, use current state as single point
        # For demonstration, calculate entropy from state vector
        values = []
        for key in ["level", "energy", "phi", "line_coherence"]:
            v = state.get(key)
            if isinstance(v, (int, float)):
                values.append(v)

        if len(values) > 1:
            # Normalize and calculate entropy
            total = sum(abs(v) for v in values)
            if total > 0:
                probs = [abs(v) / total for v in values]
                entropy = -sum(p * math.log2(p) for p in probs if p > 0)
                result["state_entropy"] = entropy

        return result

    def complexity_score(self, state: Dict[str, Any]) -> float:
        """Calculate system complexity score."""
        # More active modules = higher complexity
        active_modules = sum(1 for k, v in state.items() if v is not None and k not in ['level', 'phi', 'energy'])
        return min(1.0, active_modules / 20.0)

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Full information-theoretic analysis."""
        self.measurement_count += 1

        entropy_result = self.system_entropy(state)
        complexity = self.complexity_score(state)

        return {
            "entropy": entropy_result.get("state_entropy", 0),
            "complexity": round(complexity, 3),
            "measurements": self.measurement_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "measurements": self.measurement_count,
        }


_itc_engine = None

def get_information_theory():
    global _itc_engine
    if _itc_engine is None:
        _itc_engine = InformationTheoryCore()
    return _itc_engine
