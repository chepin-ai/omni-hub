"""
OMNI-HUB Causal Inference Engine v45
Extract causal relationships from system history.

Correlation is not causation. This engine finds the true
causes behind system behavior — what makes what happen.

Philosophy: 候即违规 — Know why, not just what.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CausalLink:
    """A discovered causal relationship."""
    cause: str
    effect: str
    strength: float  # 0.0-1.0
    confidence: float
    lag: int  # cycles between cause and effect
    evidence_count: int


class GrangerAnalyzer:
    """
    Simplified Granger causality analysis.
    If knowing X's history helps predict Y, then X Granger-causes Y.
    """

    def analyze(self, history: List[Dict[str, Any]], var_x: str, var_y: str, max_lag: int = 5) -> Optional[CausalLink]:
        """Test if var_x Granger-causes var_y."""
        x_series = [h.get(var_x, 0) for h in history if isinstance(h.get(var_x), (int, float))]
        y_series = [h.get(var_y, 0) for h in history if isinstance(h.get(var_y), (int, float))]

        if len(x_series) < max_lag * 2 or len(y_series) < max_lag * 2:
            return None

        # Simplified Granger: check if x history predicts y current
        best_lag = 0
        best_corr = 0.0

        for lag in range(1, min(max_lag + 1, len(x_series) // 2)):
            # x shifted forward by lag vs y starting at lag
            x_lagged = x_series[:-lag]
            y_shifted = y_series[lag:]
            # Align lengths
            n = min(len(x_lagged), len(y_shifted))
            if n < 3:
                continue
            corr = self._correlation(x_lagged[:n], y_shifted[:n])
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

        if abs(best_corr) < 0.3:
            return None

        return CausalLink(
            cause=var_x,
            effect=var_y,
            strength=abs(best_corr),
            confidence=min(1.0, abs(best_corr) * 1.5),
            lag=best_lag,
            evidence_count=len(x_series),
        )

    def _correlation(self, x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        x = x[:n]
        y = y[:n]
        avg_x = sum(x) / n
        avg_y = sum(y) / n
        num = sum((x[i] - avg_x) * (y[i] - avg_y) for i in range(n))
        den_x = sum((xi - avg_x) ** 2 for xi in x) ** 0.5
        den_y = sum((yi - avg_y) ** 2 for yi in y) ** 0.5
        if den_x == 0 or den_y == 0:
            return 0.0
        return num / (den_x * den_y)


class CausalInferenceEngine:
    """
    Discovers causal relationships in system behavior.
    """

    VARIABLES = ["level", "energy", "phi", "line_coherence", "active_lines"]

    def __init__(self):
        self.analyzer = GrangerAnalyzer()
        self.discovered_links: List[CausalLink] = []
        self.inference_count = 0

    def infer(self, history: List[Dict[str, Any]]) -> List[CausalLink]:
        """Run causal inference on history."""
        new_links = []
        for i, var_x in enumerate(self.VARIABLES):
            for var_y in self.VARIABLES[i+1:]:
                # Test x -> y
                link_xy = self.analyzer.analyze(history, var_x, var_y)
                if link_xy:
                    new_links.append(link_xy)
                # Test y -> x
                link_yx = self.analyzer.analyze(history, var_y, var_x)
                if link_yx:
                    new_links.append(link_yx)

        self.discovered_links.extend(new_links)
        self.inference_count += 1
        return new_links

    def get_causal_graph(self) -> Dict[str, List[str]]:
        """Get adjacency list of causal graph."""
        graph = defaultdict(list)
        for link in self.discovered_links:
            if link.strength > 0.5:
                graph[link.cause].append(link.effect)
        return dict(graph)

    def get_strongest_link(self) -> Optional[CausalLink]:
        """Get the strongest discovered causal link."""
        if not self.discovered_links:
            return None
        return max(self.discovered_links, key=lambda l: l.strength)

    def get_status(self) -> Dict[str, Any]:
        return {
            "discovered_links": len(self.discovered_links),
            "inference_count": self.inference_count,
            "strongest": f"{self.get_strongest_link().cause}->{self.get_strongest_link().effect}" if self.get_strongest_link() else None,
            "causal_graph": self.get_causal_graph(),
        }


_ci_engine = None

def get_causal_inference():
    global _ci_engine
    if _ci_engine is None:
        _ci_engine = CausalInferenceEngine()
    return _ci_engine
