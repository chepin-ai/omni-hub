"""
OMNI-HUB v136 External API Gateway
Gateway to all external APIs with endpoint registration and mock responses.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from datetime import datetime
import random

from core.event_bus import get_bus, Topics


class APIGateway:
    """Gateway for registering and calling external API endpoints."""

    def __init__(self) -> None:
        self._endpoints: Dict[str, Dict[str, Any]] = {}
        self._call_history: List[Dict[str, Any]] = []
        self._bus = get_bus()

    def register_endpoint(
        self,
        name: str,
        url_pattern: str,
        rate_limit: int = 100,
        rate_window: int = 60,
    ) -> Dict[str, Any]:
        """Register an external API endpoint."""
        try:
            if name in self._endpoints:
                return {
                    "success": False,
                    "error": f"Endpoint '{name}' already registered",
                    "endpoint": name,
                }
            self._endpoints[name] = {
                "name": name,
                "url_pattern": url_pattern,
                "rate_limit": rate_limit,
                "rate_window": rate_window,
                "registered_at": datetime.now().isoformat(),
                "call_count": 0,
            }
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {"component": "api_gateway", "action": "register", "endpoint": name},
                source="api_gateway",
            )
            return {
                "success": True,
                "endpoint": name,
                "url_pattern": url_pattern,
                "rate_limit": rate_limit,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": name}

    def call(self, name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a registered endpoint with parameters."""
        try:
            if name not in self._endpoints:
                return {
                    "success": False,
                    "error": f"Endpoint '{name}' not registered",
                    "endpoint": name,
                }
            endpoint = self._endpoints[name]
            params = params or {}
            endpoint["call_count"] += 1
            response = _get_mock_response(name, params)
            self._call_history.append({
                "endpoint": name,
                "params": params,
                "response": response,
                "timestamp": datetime.now().isoformat(),
            })
            self._bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "component": "api_gateway",
                    "action": "call",
                    "endpoint": name,
                    "call_count": endpoint["call_count"],
                },
                source="api_gateway",
            )
            return {
                "success": True,
                "endpoint": name,
                "response": response,
                "call_count": endpoint["call_count"],
            }
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": name}

    def get_rate_limit(self, name: str) -> Dict[str, Any]:
        """Get rate limit info for an endpoint."""
        try:
            if name not in self._endpoints:
                return {
                    "success": False,
                    "error": f"Endpoint '{name}' not registered",
                    "endpoint": name,
                }
            ep = self._endpoints[name]
            return {
                "success": True,
                "endpoint": name,
                "rate_limit": ep["rate_limit"],
                "rate_window": ep["rate_window"],
                "calls_made": ep["call_count"],
                "remaining": max(0, ep["rate_limit"] - ep["call_count"]),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "endpoint": name}

    def list_endpoints(self) -> List[str]:
        """Return a list of registered endpoint names."""
        return sorted(list(self._endpoints.keys()))

    def get_status(self) -> Dict[str, Any]:
        """Return current API gateway status."""
        return {
            "endpoint_count": len(self._endpoints),
            "endpoints": self.list_endpoints(),
            "total_calls": sum(ep["call_count"] for ep in self._endpoints.values()),
            "call_history_count": len(self._call_history),
        }


def _get_mock_response(endpoint: str, params: Dict[str, Any]) -> Any:
    """Generate a mock response for a simulated endpoint."""
    mockers: Dict[str, Any] = {
        "weather_api": {
            "location": params.get("city", "Unknown"),
            "temperature": random.randint(-10, 40),
            "condition": random.choice(["sunny", "cloudy", "rainy", "snowy"]),
        },
        "stock_api": {
            "symbol": params.get("symbol", "UNKNOWN"),
            "price": round(random.uniform(10.0, 500.0), 2),
            "change": round(random.uniform(-5.0, 5.0), 2),
        },
        "crypto_api": {
            "coin": params.get("coin", "BTC"),
            "price_usd": round(random.uniform(1000.0, 70000.0), 2),
            "change_24h": round(random.uniform(-10.0, 10.0), 2),
        },
        "news_api": {
            "query": params.get("q", "general"),
            "articles": random.randint(0, 10),
            "headlines": [f"Headline {i+1}" for i in range(random.randint(1, 3))],
        },
        "search_api": {
            "query": params.get("q", ""),
            "results": random.randint(1000, 1000000),
            "top_result": f"Result for '{params.get('q', '')}'",
        },
        "translate_api": {
            "text": params.get("text", ""),
            "source": params.get("from", "auto"),
            "target": params.get("to", "en"),
            "translated": f"[translated] {params.get('text', '')}",
        },
        "geocode_api": {
            "address": params.get("address", ""),
            "lat": round(random.uniform(-90.0, 90.0), 6),
            "lon": round(random.uniform(-180.0, 180.0), 6),
        },
    }
    return mockers.get(endpoint, {"endpoint": endpoint, "params": params, "mock": True})


# Global singleton
_module: Optional[APIGateway] = None


def get_api_gateway() -> APIGateway:
    """Get the global APIGateway singleton."""
    global _module
    if _module is None:
        _module = APIGateway()
    return _module


def reset_api_gateway() -> None:
    """Reset the global singleton (for testing)."""
    global _module
    _module = APIGateway()


# Pre-defined simulated endpoints
SIMULATED_ENDPOINTS = {
    "weather_api": "https://api.weather.example/v1/current?city={city}",
    "stock_api": "https://api.stocks.example/v1/quote/{symbol}",
    "crypto_api": "https://api.crypto.example/v1/price/{coin}",
    "news_api": "https://api.news.example/v1/search?q={q}",
    "search_api": "https://api.search.example/v1/query?q={q}",
    "translate_api": "https://api.translate.example/v1/translate",
    "geocode_api": "https://api.geocode.example/v1/lookup",
}


def load_simulated_endpoints(gateway: APIGateway = None) -> APIGateway:
    """Load all simulated endpoints into the gateway."""
    gateway = gateway or get_api_gateway()
    for name, url_pattern in SIMULATED_ENDPOINTS.items():
        gateway.register_endpoint(name, url_pattern)
    return gateway


if __name__ == "__main__":
    print("[OMNI-HUB v136] External API Gateway Demo")
    gw = APIGateway()
    load_simulated_endpoints(gw)
    print(f"Endpoints: {gw.list_endpoints()}")
    result = gw.call("weather_api", {"city": "Tokyo"})
    print(f"Weather call: {result['response']}")
    print(f"Rate limit: {gw.get_rate_limit('weather_api')}")
    print(f"Status: {gw.get_status()}")
