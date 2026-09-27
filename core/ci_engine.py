"""
OMNI-HUB Module v143: CI Engine (竞争情报引擎)
Competitive Intelligence system for monitoring competitors,
detecting market moves, analyzing strategic positioning,
and identifying threats and opportunities.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

# Module metadata
MODULE_VERSION = "143.0.0"
MODULE_NAME = "ci_engine"

# Signal type weights for threat assessment
SIGNAL_WEIGHTS = {
    "product_launch": 0.85,
    "pricing_change": 0.70,
    "partnership": 0.75,
    "hiring": 0.50,
    "funding": 0.90,
    "tech_advance": 0.95,
}

VALID_SIGNAL_TYPES = set(SIGNAL_WEIGHTS.keys())

# Thresholds
THREAT_HIGH = 0.75
THREAT_MEDIUM = 0.45
MARKET_MOVE_THRESHOLD = 2  # min competitors with high activity

# Global singleton
_module = None


def get_ci_engine() -> "CIEngine":
    """Get the global CI Engine singleton instance."""
    global _module
    if _module is None:
        _module = CIEngine()
    return _module


class CIEngine:
    """
    Competitive Intelligence Engine.

    Monitors competitors, detects market moves,
    analyzes strategic positioning, identifies threats and opportunities.
    """

    def __init__(self) -> None:
        self.competitors: Dict[str, Dict[str, Any]] = {}
        self.intel_feeds: List[Dict[str, Any]] = []
        self.threat_level: float = 0.0
        self._initialized_at: float = time.time()
        self._event_bus = None
        self._try_init_event_bus()

    def _try_init_event_bus(self) -> None:
        """Initialize event bus connection with defensive try/except."""
        try:
            import importlib
            bus_module = importlib.import_module("core.event_bus")
            self._event_bus = getattr(bus_module, "get_event_bus", lambda: None)()
        except Exception:
            self._event_bus = None

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit an event to the event bus if available."""
        if self._event_bus is None:
            return
        try:
            if hasattr(self._event_bus, "emit"):
                self._event_bus.emit(event_type, payload)
            elif hasattr(self._event_bus, "publish"):
                self._event_bus.publish(event_type, payload)
        except Exception:
            pass

    def register_competitor(
        self, name: str, domain: str, strengths: List[str]
    ) -> Dict[str, Any]:
        """
        Register a competitor for monitoring.

        Args:
            name: Competitor name
            domain: Competitor domain/market segment
            strengths: List of competitor strengths

        Returns:
            Dict with registration result
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid competitor name", "name": name}
        if not domain or not isinstance(domain, str):
            return {"success": False, "error": "Invalid domain", "name": name}
        if not isinstance(strengths, list):
            return {"success": False, "error": "strengths must be a list", "name": name}

        competitor = {
            "name": name,
            "domain": domain,
            "strengths": list(strengths),
            "registered_at": time.time(),
            "signals": [],
            "threat_score": 0.0,
        }
        self.competitors[name] = competitor

        self._emit_event("ci.competitor.registered", {
            "name": name,
            "domain": domain,
            "strengths": strengths,
        })

        return {
            "success": True,
            "name": name,
            "domain": domain,
            "strengths": strengths,
            "competitor_count": len(self.competitors),
        }

    def collect_intel(
        self, competitor: str, signal_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Collect competitive intelligence signal.

        Args:
            competitor: Competitor name
            signal_type: Type of signal (product_launch, pricing_change, etc.)
            data: Signal data containing at least 'intensity' (0-1)

        Returns:
            Dict with collection result
        """
        if competitor not in self.competitors:
            return {
                "success": False,
                "error": f"Competitor '{competitor}' not registered",
                "competitor": competitor,
            }
        if signal_type not in VALID_SIGNAL_TYPES:
            return {
                "success": False,
                "error": f"Invalid signal type '{signal_type}'",
                "valid_types": list(VALID_SIGNAL_TYPES),
            }
        if not isinstance(data, dict):
            return {
                "success": False,
                "error": "data must be a dict",
                "competitor": competitor,
            }

        intensity = float(data.get("intensity", 0.5))
        intensity = max(0.0, min(1.0, intensity))

        intel = {
            "competitor": competitor,
            "signal_type": signal_type,
            "intensity": intensity,
            "data": data,
            "timestamp": time.time(),
            "weight": SIGNAL_WEIGHTS.get(signal_type, 0.5),
        }
        self.intel_feeds.append(intel)
        self.competitors[competitor]["signals"].append(intel)

        # Recalculate threat for this competitor
        threat_result = self.assess_threat(competitor)
        self.competitors[competitor]["threat_score"] = threat_result.get("threat_score", 0.0)

        self._emit_event("ci.intel.collected", {
            "competitor": competitor,
            "signal_type": signal_type,
            "intensity": intensity,
        })

        return {
            "success": True,
            "intel": intel,
            "competitor": competitor,
            "threat_score": threat_result.get("threat_score", 0.0),
        }

    def assess_threat(self, competitor: str) -> Dict[str, Any]:
        """
        Assess threat level for a competitor based on collected signals.

        Args:
            competitor: Competitor name

        Returns:
            Dict with threat assessment
        """
        if competitor not in self.competitors:
            return {
                "success": False,
                "error": f"Competitor '{competitor}' not registered",
                "competitor": competitor,
            }

        signals = self.competitors[competitor].get("signals", [])
        if not signals:
            return {
                "success": True,
                "competitor": competitor,
                "threat_score": 0.0,
                "threat_level": "low",
                "signal_count": 0,
            }

        # Weighted average of signal intensities
        total_weight = 0.0
        weighted_sum = 0.0

        for signal in signals[-20:]:  # Consider last 20 signals
            w = signal.get("weight", 0.5)
            i = signal.get("intensity", 0.5)
            weighted_sum += w * i
            total_weight += w

        threat_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        threat_score = round(max(0.0, min(1.0, threat_score)), 4)

        # Determine threat level
        if threat_score >= THREAT_HIGH:
            level = "high"
        elif threat_score >= THREAT_MEDIUM:
            level = "medium"
        else:
            level = "low"

        # Update global threat level as max of all competitors
        self._update_global_threat()

        return {
            "success": True,
            "competitor": competitor,
            "threat_score": threat_score,
            "threat_level": level,
            "signal_count": len(signals),
        }

    def _update_global_threat(self) -> None:
        """Update the global threat level based on all competitors."""
        if not self.competitors:
            self.threat_level = 0.0
            return
        scores = [c.get("threat_score", 0.0) for c in self.competitors.values()]
        self.threat_level = round(max(scores) if scores else 0.0, 4)

    def detect_market_move(self) -> Dict[str, Any]:
        """
        Detect significant market moves across all competitors.

        Returns:
            Dict with market move detection results
        """
        if len(self.competitors) < 1:
            return {
                "success": True,
                "market_move_detected": False,
                "reason": "No competitors registered",
            }

        # Count competitors with recent high-intensity signals
        active_competitors = 0
        move_details: List[Dict[str, Any]] = []
        now = time.time()
        window = 3600  # 1 hour window

        for name, comp in self.competitors.items():
            recent_signals = [
                s for s in comp.get("signals", [])
                if now - s.get("timestamp", 0) <= window
            ]
            high_signals = [
                s for s in recent_signals
                if s.get("intensity", 0) >= 0.7
            ]
            if len(high_signals) >= 1:
                active_competitors += 1
                move_details.append({
                    "competitor": name,
                    "high_signals": len(high_signals),
                    "recent_signals": len(recent_signals),
                })

        market_move = active_competitors >= MARKET_MOVE_THRESHOLD

        result: Dict[str, Any] = {
            "success": True,
            "market_move_detected": market_move,
            "active_competitors": active_competitors,
            "total_competitors": len(self.competitors),
            "details": move_details,
            "threshold": MARKET_MOVE_THRESHOLD,
        }

        if market_move:
            self._emit_event("ci.market_move.detected", {
                "active_competitors": active_competitors,
                "details": move_details,
            })

        return result

    def get_status(self) -> Dict[str, Any]:
        """Return current engine status."""
        self._update_global_threat()

        latest_intel = None
        if self.intel_feeds:
            latest = self.intel_feeds[-1]
            latest_intel = {
                "competitor": latest.get("competitor"),
                "signal_type": latest.get("signal_type"),
                "intensity": latest.get("intensity"),
                "timestamp": latest.get("timestamp"),
            }

        return {
            "module": MODULE_NAME,
            "version": MODULE_VERSION,
            "competitor_count": len(self.competitors),
            "threat_level": self.threat_level,
            "latest_intel": latest_intel,
            "intel_feed_count": len(self.intel_feeds),
            "uptime": round(time.time() - self._initialized_at, 2),
            "competitors": list(self.competitors.keys()),
        }
