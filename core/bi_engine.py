"""
OMNI-HUB Module v142: BI Engine (商业智能引擎)

Business Intelligence system. Analyzes market trends, financial indicators,
competitive landscape, growth opportunities. Produces actionable intelligence reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

_module = None

VALID_CATEGORIES = {"market", "financial", "operational", "customer", "product"}


class BIEngine:
    """Business Intelligence Engine for analyzing metrics, trends, and opportunities."""

    def __init__(self) -> None:
        """Initialize the BI Engine with empty metrics, reports, and trends."""
        self._metrics: List[Dict[str, Any]] = []
        self._reports: List[Dict[str, Any]] = []
        self._trends: Dict[str, Any] = {}
        self._created_at: datetime = datetime.utcnow()
        self._metric_count: int = 0
        self._report_count: int = 0

    def collect_metric(self, name: str, value: float, category: str) -> Dict[str, Any]:
        """Store a business metric.

        Args:
            name: The name of the metric.
            value: The numeric value of the metric.
            category: The category of the metric (market, financial, operational, customer, product).

        Returns:
            Dict containing the stored metric details.

        Raises:
            ValueError: If category is not valid.
        """
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {VALID_CATEGORIES}"
            )

        metric = {
            "name": name,
            "value": value,
            "category": category,
            "timestamp": datetime.utcnow().isoformat(),
            "id": self._metric_count + 1,
        }
        self._metrics.append(metric)
        self._metric_count += 1

        return {
            "status": "collected",
            "metric": metric,
            "total_metrics": self._metric_count,
        }

    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze collected metrics for trends (growth/decline/stable).

        Returns:
            Dict with trend analysis per category and overall trend direction.
        """
        if not self._metrics:
            self._trends = {
                "status": "no_data",
                "trends": {},
                "overall_direction": "unknown",
            }
            return self._trends

        # Group metrics by (name, category)
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for m in self._metrics:
            key = f"{m['category']}:{m['name']}"
            groups.setdefault(key, []).append(m)

        category_trends: Dict[str, Dict[str, Any]] = {}
        overall_changes: List[float] = []

        for key, values in groups.items():
            if len(values) < 2:
                continue

            # Sort by timestamp
            values_sorted = sorted(values, key=lambda x: x["timestamp"])
            mid = len(values_sorted) // 2
            older = values_sorted[:mid]
            recent = values_sorted[mid:]

            older_avg = sum(v["value"] for v in older) / len(older) if older else 0
            recent_avg = sum(v["value"] for v in recent) / len(recent) if recent else 0

            if older_avg == 0:
                change_pct = 0.0
            else:
                change_pct = ((recent_avg - older_avg) / abs(older_avg)) * 100

            overall_changes.append(change_pct)

            cat = key.split(":")[0]
            if cat not in category_trends:
                category_trends[cat] = {
                    "metrics": [],
                    "average_change_pct": 0.0,
                    "direction": "stable",
                }

            direction = "stable"
            if change_pct > 5:
                direction = "growth"
            elif change_pct < -5:
                direction = "decline"

            category_trends[cat]["metrics"].append(
                {
                    "name": values_sorted[0]["name"],
                    "older_avg": round(older_avg, 4),
                    "recent_avg": round(recent_avg, 4),
                    "change_pct": round(change_pct, 4),
                    "direction": direction,
                }
            )

        # Aggregate category directions
        for cat, data in category_trends.items():
            changes = [m["change_pct"] for m in data["metrics"]]
            avg_change = sum(changes) / len(changes) if changes else 0.0
            data["average_change_pct"] = round(avg_change, 4)
            if avg_change > 5:
                data["direction"] = "growth"
            elif avg_change < -5:
                data["direction"] = "decline"
            else:
                data["direction"] = "stable"

        overall_direction = "stable"
        if overall_changes:
            overall_avg = sum(overall_changes) / len(overall_changes)
            if overall_avg > 5:
                overall_direction = "growth"
            elif overall_avg < -5:
                overall_direction = "decline"

        self._trends = {
            "status": "analyzed",
            "trends": category_trends,
            "overall_direction": overall_direction,
            "analysis_time": datetime.utcnow().isoformat(),
        }
        return self._trends

    def generate_report(self) -> Dict[str, Any]:
        """Generate BI report with KPIs, trends, recommendations.

        Returns:
            Dict containing the full BI report.
        """
        if not self._metrics:
            report = {
                "status": "no_data",
                "kpis": {},
                "trends": {},
                "recommendations": ["Collect business metrics to generate insights."],
                "generated_at": datetime.utcnow().isoformat(),
            }
            self._reports.append(report)
            self._report_count += 1
            return report

        # Ensure trends are up to date
        trends = self.analyze_trends()

        # Calculate KPIs per category
        kpis: Dict[str, Dict[str, Any]] = {}
        for cat in VALID_CATEGORIES:
            cat_metrics = [m for m in self._metrics if m["category"] == cat]
            if not cat_metrics:
                continue
            values = [m["value"] for m in cat_metrics]
            latest = max(cat_metrics, key=lambda x: x["timestamp"])
            kpis[cat] = {
                "count": len(cat_metrics),
                "latest_value": latest["value"],
                "latest_metric": latest["name"],
                "average": round(sum(values) / len(values), 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
            }

        # Build recommendations based on trends
        recommendations: List[str] = []
        for cat, data in trends.get("trends", {}).items():
            direction = data.get("direction", "stable")
            if direction == "growth":
                recommendations.append(
                    f"{cat.capitalize()}: Strong growth detected. Consider increasing investment."
                )
            elif direction == "decline":
                recommendations.append(
                    f"{cat.capitalize()}: Declining trend observed. Review strategy and reduce exposure."
                )
            else:
                recommendations.append(
                    f"{cat.capitalize()}: Stable performance. Monitor for changes."
                )

        if not recommendations:
            recommendations.append("Collect more metrics to generate actionable recommendations.")

        report = {
            "status": "generated",
            "kpis": kpis,
            "trends": trends,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
            "metric_count": self._metric_count,
        }
        self._reports.append(report)
        self._report_count += 1
        return report

    def detect_opportunity(self) -> Dict[str, Any]:
        """Detect business opportunities from data patterns.

        High growth + low saturation = opportunity.

        Returns:
            Dict with detected opportunities and their scores.
        """
        if not self._metrics:
            return {
                "status": "no_data",
                "opportunities": [],
                "message": "No metrics available for opportunity detection.",
            }

        trends = self.analyze_trends()
        opportunities: List[Dict[str, Any]] = []

        for cat, data in trends.get("trends", {}).items():
            direction = data.get("direction", "stable")
            avg_change = data.get("average_change_pct", 0.0)

            # Get metric count for this category as proxy for saturation
            cat_metric_count = len(
                [m for m in self._metrics if m["category"] == cat]
            )
            # Low saturation = few metrics collected (proxy: <= 3 unique metric names)
            unique_names = len(
                set(m["name"] for m in self._metrics if m["category"] == cat)
            )
            saturation = "low" if unique_names <= 3 else "high"

            if direction == "growth" and saturation == "low":
                score = min(100.0, max(0.0, 50.0 + avg_change))
                opportunities.append(
                    {
                        "category": cat,
                        "signal": "high_growth_low_saturation",
                        "score": round(score, 2),
                        "rationale": (
                            f"{cat.capitalize()} shows strong growth ({avg_change:.2f}% change) "
                            f"with low saturation ({unique_names} metrics). "
                            f"Opportunity to capture market share."
                        ),
                        "recommendation": f"Invest aggressively in {cat} segment.",
                    }
                )
            elif direction == "growth" and saturation == "high":
                score = min(100.0, max(0.0, 30.0 + avg_change * 0.5))
                opportunities.append(
                    {
                        "category": cat,
                        "signal": "growth_high_saturation",
                        "score": round(score, 2),
                        "rationale": (
                            f"{cat.capitalize()} is growing but saturated. "
                            f"Differentiation required."
                        ),
                        "recommendation": f"Focus on differentiation in {cat} segment.",
                    }
                )
            elif direction == "decline":
                score = max(0.0, 10.0 - abs(avg_change) * 0.5)
                opportunities.append(
                    {
                        "category": cat,
                        "signal": "declining_market",
                        "score": round(score, 2),
                        "rationale": (
                            f"{cat.capitalize()} is declining. Potential turnaround or exit opportunity."
                        ),
                        "recommendation": f"Evaluate exit or turnaround for {cat} segment.",
                    }
                )
            else:
                score = 25.0
                opportunities.append(
                    {
                        "category": cat,
                        "signal": "stable_market",
                        "score": round(score, 2),
                        "rationale": (
                            f"{cat.capitalize()} is stable. Watch for disruption signals."
                        ),
                        "recommendation": f"Maintain position in {cat} segment.",
                    }
                )

        # Sort by score descending
        opportunities.sort(key=lambda x: x["score"], reverse=True)

        return {
            "status": "analyzed",
            "opportunities": opportunities,
            "top_opportunity": opportunities[0] if opportunities else None,
            "analysis_time": datetime.utcnow().isoformat(),
        }

    def get_status(self) -> Dict[str, Any]:
        """Return metric count, report count, trend direction.

        Returns:
            Dict with current engine status.
        """
        trend_direction = self._trends.get("overall_direction", "unknown")
        if not self._trends:
            trend_direction = "unknown"

        return {
            "module": "BIEngine",
            "version": "v142",
            "metric_count": self._metric_count,
            "report_count": self._report_count,
            "trend_direction": trend_direction,
            "created_at": self._created_at.isoformat(),
            "status": "active",
        }


def get_bi_engine() -> BIEngine:
    """Get the global singleton BIEngine instance.

    Returns:
        The singleton BIEngine instance.
    """
    global _module
    if _module is None:
        _module = BIEngine()
    return _module
