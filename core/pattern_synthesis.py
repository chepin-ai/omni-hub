"""
OMNI-HUB Pattern Synthesis Engine v50
Extract abstract patterns from history.

History repeats until it is understood.
This engine finds the patterns that hide in the noise —
the rhythms, the trends, the anomalies that make intuition.

Philosophy: 历史重复，直到被理解 — History repeats until understood.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math


@dataclass
class Pattern:
    """A discovered pattern in system behavior."""
    pattern_type: str  # 'cycle', 'trend', 'anomaly', 'correlation'
    description: str
    confidence: float
    evidence: List[Dict[str, Any]]
    first_seen: int
    last_seen: int


class CycleDetector:
    """Detects periodic cycles in time series."""

    def detect(self, series: List[float], max_period: int = 50) -> Optional[Pattern]:
        """Detect if a series has periodic behavior."""
        n = len(series)
        if n < max_period * 2:
            return None

        best_period = 0
        best_score = 0.0

        for period in range(5, min(max_period, n // 2)):
            # Compare segments
            segments = n // period
            if segments < 2:
                continue

            # Calculate autocorrelation-like score
            score = 0.0
            for i in range(period):
                values = [series[i + j * period] for j in range(segments) if i + j * period < n]
                if len(values) > 1:
                    avg = sum(values) / len(values)
                    variance = sum((v - avg) ** 2 for v in values) / len(values)
                    score += 1.0 / (1.0 + variance)

            score /= period
            if score > best_score:
                best_score = score
                best_period = period

        if best_score > 0.7 and best_period > 0:
            return Pattern(
                pattern_type="cycle",
                description=f"Periodic cycle detected with period {best_period}",
                confidence=best_score,
                evidence=[{"period": best_period, "score": best_score}],
                first_seen=0,
                last_seen=n,
            )
        return None


class TrendAnalyzer:
    """Detects long-term trends."""

    def detect(self, series: List[float]) -> Optional[Pattern]:
        """Detect linear trend using simple regression."""
        n = len(series)
        if n < 10:
            return None

        # Linear regression
        x_avg = sum(range(n)) / n
        y_avg = sum(series) / n

        num = sum((i - x_avg) * (series[i] - y_avg) for i in range(n))
        den = sum((i - x_avg) ** 2 for i in range(n))

        if den == 0:
            return None

        slope = num / den

        # R-squared
        ss_res = sum((series[i] - (y_avg + slope * (i - x_avg))) ** 2 for i in range(n))
        ss_tot = sum((series[i] - y_avg) ** 2 for i in range(n))
        r_squared = 1 - ss_res / max(ss_tot, 1e-10)

        if r_squared > 0.5:
            direction = "increasing" if slope > 0 else "decreasing"
            return Pattern(
                pattern_type="trend",
                description=f"Linear trend: {direction} (slope={slope:.4f})",
                confidence=r_squared,
                evidence=[{"slope": slope, "r_squared": r_squared}],
                first_seen=0,
                last_seen=n,
            )
        return None


class AnomalyDetector:
    """Detects anomalous values in series."""

    def detect(self, series: List[float]) -> List[Pattern]:
        """Detect values beyond 2 standard deviations."""
        n = len(series)
        if n < 10:
            return []

        avg = sum(series) / n
        std = (sum((v - avg) ** 2 for v in series) / n) ** 0.5

        anomalies = []
        for i, val in enumerate(series):
            if abs(val - avg) > 2 * std:
                anomalies.append({
                    "index": i,
                    "value": val,
                    "deviation": abs(val - avg) / max(std, 1e-10),
                })

        if anomalies:
            return [Pattern(
                pattern_type="anomaly",
                description=f"{len(anomalies)} anomalous values detected",
                confidence=min(1.0, len(anomalies) / n * 5),
                evidence=anomalies,
                first_seen=anomalies[0]["index"],
                last_seen=anomalies[-1]["index"],
            )]
        return []


class PatternSynthesisEngine:
    """
    Discovers patterns across all system history.
    """

    def __init__(self):
        self.cycle_detector = CycleDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.discovered_patterns: List[Pattern] = []
        self.synthesis_count = 0

    def synthesize(self, history: List[Dict[str, Any]]) -> List[Pattern]:
        """Run full pattern synthesis on history."""
        new_patterns = []

        # Extract time series
        variables = ["level", "energy", "phi", "line_coherence"]
        for var in variables:
            series = [h.get(var, 0) for h in history if isinstance(h.get(var), (int, float))]
            if len(series) < 20:
                continue

            # Cycle detection
            cycle = self.cycle_detector.detect(series)
            if cycle:
                cycle.description = f"{var}: {cycle.description}"
                new_patterns.append(cycle)

            # Trend detection
            trend = self.trend_analyzer.detect(series)
            if trend:
                trend.description = f"{var}: {trend.description}"
                new_patterns.append(trend)

            # Anomaly detection
            anomalies = self.anomaly_detector.detect(series)
            new_patterns.extend(anomalies)

        self.discovered_patterns.extend(new_patterns)
        self.synthesis_count += 1
        return new_patterns

    def match_current(self, current_state: Dict[str, Any]) -> List[Pattern]:
        """Match current state against known patterns."""
        matches = []
        for pattern in self.discovered_patterns:
            if pattern.pattern_type == "trend":
                # Simple match: check if state aligns with trend direction
                matches.append({
                    "pattern": pattern.description,
                    "confidence": pattern.confidence,
                })
        return matches

    def get_status(self) -> Dict[str, Any]:
        return {
            "patterns": len(self.discovered_patterns),
            "synthesis_count": self.synthesis_count,
            "by_type": {
                "cycle": len([p for p in self.discovered_patterns if p.pattern_type == "cycle"]),
                "trend": len([p for p in self.discovered_patterns if p.pattern_type == "trend"]),
                "anomaly": len([p for p in self.discovered_patterns if p.pattern_type == "anomaly"]),
            },
        }


_ps_engine = None

def get_pattern_synthesis():
    global _ps_engine
    if _ps_engine is None:
        _ps_engine = PatternSynthesisEngine()
    return _ps_engine
