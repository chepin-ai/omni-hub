import time

import pytest

from core.node_discovery import NodeDiscovery, get_node_discovery


class TestNodeDiscovery:
    def test_init_has_fingerprint(self):
        nd = NodeDiscovery()
        assert nd._own_fingerprint is not None
        assert len(nd._own_fingerprint) == 16
        assert nd.get_peer_count() == 0

    def test_discover_adds_peer(self):
        nd = NodeDiscovery()
        result = nd.discover("peer-001")
        assert result["peer_id"] == "peer-001"
        assert result["peer_count"] == 1
        assert nd.get_peer_count() == 1

    def test_discover_generates_id_when_empty(self):
        nd = NodeDiscovery()
        result = nd.discover()
        assert result["peer_id"] is not None
        assert len(result["peer_id"]) == 16
        assert nd.get_peer_count() == 1

    def test_discover_multiple_peers(self):
        nd = NodeDiscovery()
        for i in range(5):
            nd.discover(f"peer-{i}")
        assert nd.get_peer_count() == 5

    def test_heartbeat_keeps_active_peers(self):
        nd = NodeDiscovery()
        nd.discover("peer-alive")
        result = nd.heartbeat()
        assert result["active_peers"] == 1
        assert result["removed_stale"] == 0

    def test_heartbeat_removes_stale_peers(self):
        nd = NodeDiscovery()
        nd._peers["peer-stale"] = time.time() - 301
        nd._peers["peer-fresh"] = time.time() - 10
        result = nd.heartbeat()
        assert result["active_peers"] == 1
        assert result["removed_stale"] == 1
        assert "peer-stale" not in nd._peers
        assert "peer-fresh" in nd._peers

    def test_heartbeat_boundary_exact_threshold(self):
        nd = NodeDiscovery()
        nd._peers["peer-boundary"] = time.time() - 299.5
        result = nd.heartbeat()
        assert result["active_peers"] == 1
        assert result["removed_stale"] == 0

    def test_get_status_empty(self):
        nd = NodeDiscovery()
        status = nd.get_status()
        assert status["peer_count"] == 0
        assert status["own_fingerprint"] is not None
        assert status["oldest_peer"] is None
        assert status["newest_peer"] is None

    def test_get_status_with_peers(self):
        nd = NodeDiscovery()
        nd.discover("peer-1")
        time.sleep(0.01)
        nd.discover("peer-2")
        status = nd.get_status()
        assert status["peer_count"] == 2
        assert status["own_fingerprint"] is not None
        assert status["oldest_peer"]["peer_id"] == "peer-1"
        assert status["newest_peer"]["peer_id"] == "peer-2"
        assert status["oldest_peer"]["age_seconds"] >= 0.01

    def test_get_peer_count_returns_int(self):
        nd = NodeDiscovery()
        assert isinstance(nd.get_peer_count(), int)
        nd.discover("x")
        assert nd.get_peer_count() == 1

    def test_singleton_returns_same_instance(self):
        nd1 = get_node_discovery()
        nd2 = get_node_discovery()
        assert nd1 is nd2

    def test_singleton_persists_peers(self):
        nd = get_node_discovery()
        nd._peers.clear()
        nd.discover("singleton-peer")
        nd2 = get_node_discovery()
        assert "singleton-peer" in nd2._peers
