"""
OMNI-HUB v136 External API Gateway Tests
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.api_gateway import (
    APIGateway,
    get_api_gateway,
    reset_api_gateway,
    load_simulated_endpoints,
    SIMULATED_ENDPOINTS,
)


class TestAPIGatewayCreation:
    def test_init_empty(self):
        gw = APIGateway()
        assert gw.get_status()["endpoint_count"] == 0
        assert gw.list_endpoints() == []


class TestRegisterEndpoint:
    def test_register_single(self):
        gw = APIGateway()
        result = gw.register_endpoint("test_api", "https://test.example/{id}")
        assert result["success"] is True
        assert result["endpoint"] == "test_api"
        assert result["url_pattern"] == "https://test.example/{id}"

    def test_register_with_rate_limit(self):
        gw = APIGateway()
        result = gw.register_endpoint("test_api", "https://test.example", rate_limit=50, rate_window=30)
        assert result["success"] is True
        assert result["rate_limit"] == 50

    def test_register_duplicate_fails(self):
        gw = APIGateway()
        gw.register_endpoint("test_api", "https://test.example")
        result = gw.register_endpoint("test_api", "https://test2.example")
        assert result["success"] is False
        assert "already registered" in result["error"]

    def test_list_endpoints_sorted(self):
        gw = APIGateway()
        gw.register_endpoint("z_api", "https://z.example")
        gw.register_endpoint("a_api", "https://a.example")
        assert gw.list_endpoints() == ["a_api", "z_api"]


class TestCallEndpoint:
    def test_call_registered(self):
        gw = APIGateway()
        gw.register_endpoint("weather_api", "https://api.weather.example/{city}")
        result = gw.call("weather_api", {"city": "Tokyo"})
        assert result["success"] is True
        assert result["endpoint"] == "weather_api"
        assert "response" in result
        assert result["call_count"] == 1

    def test_call_not_registered_fails(self):
        gw = APIGateway()
        result = gw.call("missing", {})
        assert result["success"] is False
        assert "not registered" in result["error"]

    def test_call_count_increments(self):
        gw = APIGateway()
        gw.register_endpoint("test_api", "https://test.example")
        gw.call("test_api")
        gw.call("test_api")
        result = gw.call("test_api")
        assert result["call_count"] == 3

    def test_call_stock_api(self):
        gw = APIGateway()
        gw.register_endpoint("stock_api", "https://api.stocks.example/{symbol}")
        result = gw.call("stock_api", {"symbol": "AAPL"})
        assert result["success"] is True
        assert result["response"]["symbol"] == "AAPL"
        assert "price" in result["response"]

    def test_call_crypto_api(self):
        gw = APIGateway()
        gw.register_endpoint("crypto_api", "https://api.crypto.example/{coin}")
        result = gw.call("crypto_api", {"coin": "BTC"})
        assert result["success"] is True
        assert result["response"]["coin"] == "BTC"
        assert "price_usd" in result["response"]

    def test_call_news_api(self):
        gw = APIGateway()
        gw.register_endpoint("news_api", "https://api.news.example/search")
        result = gw.call("news_api", {"q": "technology"})
        assert result["success"] is True
        assert result["response"]["query"] == "technology"
        assert "articles" in result["response"]

    def test_call_translate_api(self):
        gw = APIGateway()
        gw.register_endpoint("translate_api", "https://api.translate.example/translate")
        result = gw.call("translate_api", {"text": "hello", "to": "es"})
        assert result["success"] is True
        assert result["response"]["text"] == "hello"
        assert "translated" in result["response"]

    def test_call_geocode_api(self):
        gw = APIGateway()
        gw.register_endpoint("geocode_api", "https://api.geocode.example/lookup")
        result = gw.call("geocode_api", {"address": "1600 Amphitheatre Parkway"})
        assert result["success"] is True
        assert "lat" in result["response"]
        assert "lon" in result["response"]

    def test_call_with_no_params(self):
        gw = APIGateway()
        gw.register_endpoint("weather_api", "https://api.weather.example")
        result = gw.call("weather_api")
        assert result["success"] is True
        assert "response" in result

    def test_call_unknown_endpoint_uses_fallback(self):
        gw = APIGateway()
        gw.register_endpoint("custom_xyz", "https://custom.example")
        result = gw.call("custom_xyz", {"foo": "bar"})
        assert result["success"] is True
        assert result["response"]["mock"] is True


class TestGetRateLimit:
    def test_rate_limit_registered(self):
        gw = APIGateway()
        gw.register_endpoint("test_api", "https://test.example", rate_limit=100, rate_window=60)
        result = gw.get_rate_limit("test_api")
        assert result["success"] is True
        assert result["rate_limit"] == 100
        assert result["rate_window"] == 60
        assert result["calls_made"] == 0
        assert result["remaining"] == 100

    def test_rate_limit_after_calls(self):
        gw = APIGateway()
        gw.register_endpoint("test_api", "https://test.example", rate_limit=10)
        gw.call("test_api")
        gw.call("test_api")
        result = gw.get_rate_limit("test_api")
        assert result["calls_made"] == 2
        assert result["remaining"] == 8

    def test_rate_limit_not_registered(self):
        gw = APIGateway()
        result = gw.get_rate_limit("missing")
        assert result["success"] is False
        assert "not registered" in result["error"]

    def test_rate_limit_remaining_never_negative(self):
        gw = APIGateway()
        gw.register_endpoint("test_api", "https://test.example", rate_limit=2)
        gw.call("test_api")
        gw.call("test_api")
        gw.call("test_api")
        result = gw.get_rate_limit("test_api")
        assert result["remaining"] == 0


class TestGetStatus:
    def test_status_empty(self):
        gw = APIGateway()
        status = gw.get_status()
        assert status["endpoint_count"] == 0
        assert status["endpoints"] == []
        assert status["total_calls"] == 0

    def test_status_with_endpoints(self):
        gw = APIGateway()
        gw.register_endpoint("api1", "https://a.example")
        gw.register_endpoint("api2", "https://b.example")
        gw.call("api1")
        status = gw.get_status()
        assert status["endpoint_count"] == 2
        assert status["total_calls"] == 1
        assert "api1" in status["endpoints"]


class TestSimulatedEndpoints:
    def test_all_simulated_registered(self):
        gw = APIGateway()
        load_simulated_endpoints(gw)
        assert gw.get_status()["endpoint_count"] == len(SIMULATED_ENDPOINTS)
        for name in SIMULATED_ENDPOINTS:
            assert name in gw.list_endpoints()

    def test_simulated_url_patterns(self):
        gw = APIGateway()
        load_simulated_endpoints(gw)
        for name, url in SIMULATED_ENDPOINTS.items():
            # endpoints are stored internally
            ep = gw._endpoints[name]
            assert ep["url_pattern"] == url


class TestSingleton:
    def test_singleton_returns_same_instance(self):
        reset_api_gateway()
        gw1 = get_api_gateway()
        gw2 = get_api_gateway()
        assert gw1 is gw2

    def test_singleton_persists_state(self):
        reset_api_gateway()
        gw = get_api_gateway()
        gw.register_endpoint("singleton_api", "https://singleton.example")
        gw2 = get_api_gateway()
        assert "singleton_api" in gw2.list_endpoints()


class TestEventBusIntegration:
    def test_register_publishes_event(self):
        from core.event_bus import reset_bus, get_bus, Topics
        reset_bus()
        gw = APIGateway()
        gw.register_endpoint("event_test", "https://event.example")
        events = get_bus().get_history(Topics.STATE_CHANGE)
        assert any(e.payload.get("endpoint") == "event_test" for e in events)

    def test_call_publishes_event(self):
        from core.event_bus import reset_bus, get_bus, Topics
        reset_bus()
        gw = APIGateway()
        gw.register_endpoint("event_test", "https://event.example")
        gw.call("event_test")
        events = get_bus().get_history(Topics.STATE_CHANGE)
        call_events = [e for e in events if e.payload.get("action") == "call"]
        assert any(e.payload.get("endpoint") == "event_test" for e in call_events)
