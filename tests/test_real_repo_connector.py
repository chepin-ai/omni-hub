"""
Tests for OMNI-HUB v152: Real Repo Connector (真实仓库连接器)
"""

import pytest
from core.real_repo_connector import (
    RealRepoConnector,
    get_real_repo_connector,
    reset_real_repo_connector,
    RepoConnection,
)


class TestRealRepoConnector:
    def test_init(self):
        connector = RealRepoConnector()
        assert connector._connections == {}
        assert connector._connect_count == 0
        assert connector._last_connect is None
        assert len(connector._repo_data) > 0

    def test_init_loads_repo_data(self):
        connector = RealRepoConnector()
        # Should have data from all three categories
        assert "vci-inbox" in connector._repo_data
        assert "langchain-ai/langchain" in connector._repo_data
        assert "vci-ucif2" in connector._repo_data
        # Categories should be set
        assert connector._repo_data["vci-inbox"]["category"] == "alliance_other"
        assert connector._repo_data["langchain-ai/langchain"]["category"] == "external_alliance"

    def test_connect_known_repo(self):
        connector = RealRepoConnector()
        result = connector.connect("vci-inbox")
        assert result["success"] is True
        assert result["repo_name"] == "vci-inbox"
        assert "metadata" in result
        assert "health" in result
        assert "connected_at" in result
        assert result["metadata"]["role"] == "inbox"
        assert connector._connect_count == 1
        assert "vci-inbox" in connector._connections

    def test_connect_external_repo(self):
        connector = RealRepoConnector()
        result = connector.connect("langchain-ai/langchain")
        assert result["success"] is True
        assert result["repo_name"] == "langchain-ai/langchain"
        assert result["metadata"]["role"] == "framework"
        assert result["health"] == 1.0  # External repos have no updated date -> 1.0

    def test_connect_unknown_repo(self):
        connector = RealRepoConnector()
        result = connector.connect("unknown/repo")
        assert result["success"] is True
        assert result["repo_name"] == "unknown/repo"
        assert result["metadata"]["role"] == "unknown"

    def test_connect_invalid_name(self):
        connector = RealRepoConnector()
        assert connector.connect("")["success"] is False
        assert connector.connect(None)["success"] is False
        assert connector.connect(123)["success"] is False

    def test_connect_idempotent(self):
        connector = RealRepoConnector()
        r1 = connector.connect("vci-inbox")
        r2 = connector.connect("vci-inbox")
        assert r1["success"] is True
        assert r2["success"] is True
        assert r2.get("message") == "Already connected"
        assert connector._connect_count == 1

    def test_batch_connect(self):
        connector = RealRepoConnector()
        repos = ["vci-inbox", "ci-yard", "langchain-ai/langchain"]
        result = connector.batch_connect(repos)
        assert result["success"] is True
        assert result["connected_count"] == 3
        assert result["failed_count"] == 0
        assert set(result["connected"]) == set(repos)
        assert len(connector._connections) == 3

    def test_batch_connect_empty(self):
        connector = RealRepoConnector()
        result = connector.batch_connect([])
        assert result["success"] is True
        assert result["connected_count"] == 0
        assert result["failed_count"] == 0

    def test_batch_connect_invalid_input(self):
        connector = RealRepoConnector()
        result = connector.batch_connect("not-a-list")
        assert result["success"] is False
        assert "error" in result

    def test_sync_health_connected_repo(self):
        connector = RealRepoConnector()
        connector.connect("vci-inbox")
        result = connector.sync_health("vci-inbox")
        assert result["success"] is True
        assert result["repo_name"] == "vci-inbox"
        assert "old_health" in result
        assert "new_health" in result
        assert "sync_count" in result
        assert result["sync_count"] == 1
        assert result["last_sync"] is not None
        conn = connector._connections["vci-inbox"]
        assert conn.sync_count == 1
        assert conn.last_sync is not None

    def test_sync_health_not_connected(self):
        connector = RealRepoConnector()
        result = connector.sync_health("vci-inbox")
        assert result["success"] is False
        assert "error" in result

    def test_sync_health_invalid_name(self):
        connector = RealRepoConnector()
        assert connector.sync_health("")["success"] is False
        assert connector.sync_health(None)["success"] is False

    def test_get_active_connections_empty(self):
        connector = RealRepoConnector()
        assert connector.get_active_connections() == []

    def test_get_active_connections_sorted(self):
        connector = RealRepoConnector()
        # Today is 2026-09-28
        # vci-inbox updated 2026-09-27 -> 1 day ago -> health 1.0 (<=1 day)
        # vci-bus updated 2026-08-27 -> 32 days ago -> health 0.2
        # langchain-ai/langchain has no updated -> health 1.0
        connector.connect("vci-inbox")
        connector.connect("vci-bus")
        connector.connect("langchain-ai/langchain")
        conns = connector.get_active_connections()
        assert len(conns) == 3
        # Should be sorted by health descending
        # vci-inbox and langchain both have health 1.0, vci-bus has 0.2
        assert conns[0]["health"] == 1.0
        assert conns[1]["health"] == 1.0
        assert conns[2]["name"] == "vci-bus"
        assert conns[2]["health"] == 0.2
        for c in conns:
            assert "metadata" in c
            assert "connected_at" in c
            assert "sync_count" in c

    def test_get_active_connections_with_different_health(self):
        connector = RealRepoConnector()
        # Manually add connections with different health values
        connector._connections["repo-high"] = RepoConnection(
            name="repo-high", metadata={}, health=1.0
        )
        connector._connections["repo-mid"] = RepoConnection(
            name="repo-mid", metadata={}, health=0.5
        )
        connector._connections["repo-low"] = RepoConnection(
            name="repo-low", metadata={}, health=0.2
        )
        conns = connector.get_active_connections()
        assert len(conns) == 3
        assert conns[0]["health"] == 1.0
        assert conns[1]["health"] == 0.5
        assert conns[2]["health"] == 0.2

    def test_get_status_empty(self):
        connector = RealRepoConnector()
        status = connector.get_status()
        assert status["connection_count"] == 0
        assert status["avg_health"] == 0.0
        assert status["strongest_connection"] is None
        assert status["weakest_connection"] is None
        assert status["total_connects"] == 0
        assert status["last_connect"] is None

    def test_get_status_with_connections(self):
        connector = RealRepoConnector()
        # vci-inbox updated 2026-09-27 -> 1 day ago -> health 1.0 (<=1 day)
        connector.connect("vci-inbox")
        connector.connect("langchain-ai/langchain")  # health 1.0 (no updated date)
        status = connector.get_status()
        assert status["connection_count"] == 2
        # avg = (1.0 + 1.0) / 2 = 1.0
        assert status["avg_health"] == 1.0
        assert status["strongest_connection"] is not None
        assert status["weakest_connection"] is not None
        assert status["total_connects"] == 2
        assert status["last_connect"] is not None

    def test_get_status_with_different_health(self):
        connector = RealRepoConnector()
        connector._connections["repo-a"] = RepoConnection(
            name="repo-a", metadata={}, health=1.0
        )
        connector._connections["repo-b"] = RepoConnection(
            name="repo-b", metadata={}, health=0.5
        )
        status = connector.get_status()
        assert status["connection_count"] == 2
        assert status["avg_health"] == 0.75
        assert status["strongest_connection"]["name"] == "repo-a"
        assert status["strongest_connection"]["health"] == 1.0
        assert status["weakest_connection"]["name"] == "repo-b"
        assert status["weakest_connection"]["health"] == 0.5

    def test_compute_health_today(self):
        connector = RealRepoConnector()
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")
        assert connector._compute_health(today_str) == 1.0

    def test_compute_health_within_7_days(self):
        connector = RealRepoConnector()
        from datetime import date, timedelta
        d = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        assert connector._compute_health(d) == 0.8

    def test_compute_health_within_30_days(self):
        connector = RealRepoConnector()
        from datetime import date, timedelta
        d = (date.today() - timedelta(days=15)).strftime("%Y-%m-%d")
        assert connector._compute_health(d) == 0.5

    def test_compute_health_over_30_days(self):
        connector = RealRepoConnector()
        from datetime import date, timedelta
        d = (date.today() - timedelta(days=60)).strftime("%Y-%m-%d")
        assert connector._compute_health(d) == 0.2

    def test_compute_health_future_date(self):
        connector = RealRepoConnector()
        from datetime import date, timedelta
        d = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        assert connector._compute_health(d) == 1.0

    def test_compute_health_none(self):
        connector = RealRepoConnector()
        assert connector._compute_health(None) == 1.0

    def test_compute_health_invalid(self):
        connector = RealRepoConnector()
        assert connector._compute_health("not-a-date") == 1.0

    def test_connect_all_required(self):
        connector = RealRepoConnector()
        result = connector.connect_all_required()
        assert result["success"] is True
        expected_count = len(RealRepoConnector.REQUIRED_NONLINE_REPOS) + len(
            RealRepoConnector.REQUIRED_EXTERNAL_REPOS
        )
        assert result["connected_count"] == expected_count
        # Verify all required repos are connected
        for repo in RealRepoConnector.REQUIRED_NONLINE_REPOS:
            assert repo in connector._connections
        for repo in RealRepoConnector.REQUIRED_EXTERNAL_REPOS:
            assert repo in connector._connections

    def test_singleton(self):
        reset_real_repo_connector()
        a = get_real_repo_connector()
        b = get_real_repo_connector()
        assert a is b

    def test_required_nonline_repo_list(self):
        expected = [
            "vci-inbox", "ci-worker-01", "qlv-lib", "lgt-worker-01", "ci-yard",
            "vci-control", "qfos-autonomous-engine", "grand-synthesis",
            "prima-50-research", "ci-worker-02", "vci-library", "vci-playground",
            "vci-root", "vci-logs", "vci-code", "vci-bus",
        ]
        assert RealRepoConnector.REQUIRED_NONLINE_REPOS == expected

    def test_required_external_repo_list(self):
        expected = [
            "langchain-ai/langchain", "microsoft/semantic-kernel",
            "openai/openai-python", "huggingface/transformers", "pytorch/pytorch",
        ]
        assert RealRepoConnector.REQUIRED_EXTERNAL_REPOS == expected

    def test_repo_connection_dataclass(self):
        conn = RepoConnection(name="test", metadata={"role": "test"})
        assert conn.name == "test"
        assert conn.metadata == {"role": "test"}
        assert conn.health == 1.0
        assert conn.sync_count == 0
        assert conn.last_sync is None
        assert conn.connected_at is not None
