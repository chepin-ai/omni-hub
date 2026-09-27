"""
OMNI-HUB Module v144: QI Engine (质量智能引擎)
Quality Intelligence system. Monitors system quality, code health,
test coverage, performance metrics. Detects degradation before it becomes critical.
"""

from typing import Dict, List, Optional, Any
import logging

# Module-level logger
logger = logging.getLogger(__name__)

# Global singleton instance
_module = None

# Predefined quality dimensions
DIMENSIONS = [
    "code_health",
    "test_coverage",
    "performance",
    "security",
    "reliability",
    "maintainability",
]


class QIEngine:
    """Quality Intelligence Engine for monitoring system quality metrics."""

    def __init__(self) -> None:
        """Initialize the QI Engine with default state."""
        # quality_scores: dimension -> list of (score, weight) tuples
        self.quality_scores: Dict[str, List[tuple]] = {dim: [] for dim in DIMENSIONS}
        # thresholds: dimension -> threshold value
        self.thresholds: Dict[str, float] = {dim: 0.7 for dim in DIMENSIONS}
        # alerts: list of alert dicts
        self.alerts: List[Dict[str, Any]] = []
        # quality history for degradation detection: dimension -> last computed index
        self._history: Dict[str, float] = {}

    def measure_dimension(
        self, dimension: str, score: float, weight: float = 1.0
    ) -> Dict[str, Any]:
        """Record a quality score for a given dimension.

        Args:
            dimension: The quality dimension to measure.
            score: Quality score in range 0-1.
            weight: Weight of this measurement (default 1.0).

        Returns:
            Dict with measurement result and any alerts triggered.
        """
        # Clamp score to 0-1 range and coerce to float
        clamped_score = max(0.0, min(1.0, float(score)))
        float_weight = float(weight)

        result: Dict[str, Any] = {
            "dimension": dimension,
            "score": clamped_score,
            "weight": float_weight,
            "alert": None,
        }

        if dimension not in self.quality_scores:
            self.quality_scores[dimension] = []

        self.quality_scores[dimension].append((clamped_score, float_weight))

        # Check threshold and generate alert if needed
        threshold = self.thresholds.get(dimension, 0.7)
        if clamped_score < 0.5:
            alert = {
                "level": "critical",
                "dimension": dimension,
                "score": clamped_score,
                "message": f"Critical: {dimension} score {clamped_score:.2f} below 0.5",
            }
            self.alerts.append(alert)
            result["alert"] = alert
        elif clamped_score < threshold:
            alert = {
                "level": "warning",
                "dimension": dimension,
                "score": clamped_score,
                "message": f"Warning: {dimension} score {clamped_score:.2f} below threshold {threshold:.2f}",
            }
            self.alerts.append(alert)
            result["alert"] = alert

        return result

    def compute_quality_index(self) -> Dict[str, Any]:
        """Compute the overall quality index as a weighted average across all dimensions.

        Returns:
            Dict with overall index, per-dimension scores, and alert summary.
        """
        dimension_scores: Dict[str, float] = {}
        total_weighted_score = 0.0
        total_weight = 0.0

        for dimension in self.quality_scores:
            measurements = self.quality_scores[dimension]
            if measurements:
                dim_total_score = sum(s * w for s, w in measurements)
                dim_total_weight = sum(w for _, w in measurements)
                dim_avg = dim_total_score / dim_total_weight if dim_total_weight > 0 else 0.0
            else:
                dim_avg = 0.0
            dimension_scores[dimension] = dim_avg
            total_weighted_score += dim_avg
            total_weight += 1.0

        overall_index = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine overall health level
        if overall_index < 0.5:
            level = "critical"
        elif overall_index < 0.7:
            level = "warning"
        else:
            level = "healthy"

        result = {
            "overall_index": overall_index,
            "level": level,
            "dimension_scores": dimension_scores,
        }

        # Store history for degradation detection
        for dim, score in dimension_scores.items():
            self._history[dim] = score

        return result

    def detect_degradation(self) -> Dict[str, Any]:
        """Detect quality degradation trends by comparing current to previous measurements.

        Degradation is detected when current score < previous score * 0.9.

        Returns:
            Dict with degraded dimensions and degradation details.
        """
        degraded: List[Dict[str, Any]] = []

        for dimension, measurements in self.quality_scores.items():
            if len(measurements) < 2:
                continue

            # Current = latest measurement, Previous = second-latest
            current_score, _ = measurements[-1]
            previous_score, _ = measurements[-2]

            if current_score < previous_score * 0.9:
                degraded.append({
                    "dimension": dimension,
                    "previous_score": previous_score,
                    "current_score": current_score,
                    "degradation_ratio": current_score / previous_score if previous_score > 0 else 0.0,
                })

        return {
            "degraded_count": len(degraded),
            "degraded_dimensions": degraded,
            "has_degradation": len(degraded) > 0,
        }

    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate a full quality report with all dimensions.

        Returns:
            Dict with complete quality report including index, degradation, and alerts.
        """
        quality_index = self.compute_quality_index()
        degradation = self.detect_degradation()

        # Classify alerts by level
        critical_alerts = [a for a in self.alerts if a["level"] == "critical"]
        warning_alerts = [a for a in self.alerts if a["level"] == "warning"]

        report = {
            "overall_index": quality_index["overall_index"],
            "level": quality_index["level"],
            "dimension_scores": quality_index["dimension_scores"],
            "degradation": degradation,
            "alerts": {
                "critical_count": len(critical_alerts),
                "warning_count": len(warning_alerts),
                "total_count": len(self.alerts),
                "critical": critical_alerts,
                "warning": warning_alerts,
            },
            "dimensions_tracked": list(self.quality_scores.keys()),
            "thresholds": self.thresholds.copy(),
        }

        return report

    def get_status(self) -> Dict[str, Any]:
        """Return current engine status.

        Returns:
            Dict with quality index, alert count, and dimensions tracked.
        """
        quality_index = self.compute_quality_index()
        return {
            "quality_index": quality_index["overall_index"],
            "level": quality_index["level"],
            "alert_count": len(self.alerts),
            "dimensions_tracked": len(self.quality_scores),
            "dimension_names": list(self.quality_scores.keys()),
        }


def get_qi_engine() -> QIEngine:
    """Return the global singleton QI Engine instance."""
    global _module
    if _module is None:
        _module = QIEngine()
    return _module
