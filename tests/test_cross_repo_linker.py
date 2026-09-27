"""
Tests for OMNI-HUB v146: Cross-Repository Linker (跨仓连接器)
"""

import pytest
from core.cross_repo_linker import CrossRepoLinker, get_cross_repo_linker, SIMULATED_REPOS


class TestCrossRepoLinker:
    def test_init(self):
        linker = CrossRepoLinker()
        assert linker.linked_repos == {}
        assert linker.channels == {}
        assert linker._last_sync is None
        assert linker._sync_count == 0
        assert linker._scan_count == 0

    def test_scan_repos_finds_known_repos(self):
        linker = CrossRepoLinker()
        result = linker.scan_repos(["/dev/ai_projects", "/src/ml_code"])
        assert isinstance(result, dict)
        assert "found_count" in result
        assert "found_repos" in result
        assert result["found_count"] > 0
        assert linker._scan_count == 1
        for repo in result["found_repos"]:
            assert "name" in repo
            assert "url" in repo
            assert "stars" in repo

    def test_scan_repos_empty_paths(self):
        linker = CrossRepoLinker()
        result = linker.scan_repos([])
        assert result["found_count"] == 0
        assert result["found_repos"] == []

    def test_scan_repos_deduplicates(self):
        linker = CrossRepoLinker()
        # Scanning the same path twice should deduplicate
        result = linker.scan_repos(["/dev/ai_projects", "/dev/ai_projects"])
        names = [r["name"] for r in result["found_repos"]]
        assert len(names) == len(set(names))

    def test_link_repo_known(self):
        linker = CrossRepoLinker()
        result = linker.link_repo(
            "https://github.com/langchain-ai/langchain",
            "langchain-ai/langchain",
        )
        assert result["success"] is True
        assert result["repo_name"] == "langchain-ai/langchain"
        assert "metadata" in result
        meta = result["metadata"]
        assert meta["stars"] > 0
        assert meta["contributors"] > 0
        assert meta["module_count"] > 0
        assert "linked_at" in meta
        assert "channel_id" in meta
        assert "langchain-ai/langchain" in linker.linked_repos
        assert meta["channel_id"] in linker.channels

    def test_link_repo_unknown(self):
        linker = CrossRepoLinker()
        result = linker.link_repo(
            "https://github.com/example/unknown-repo",
            "example/unknown-repo",
        )
        assert result["success"] is True
        assert result["repo_name"] == "example/unknown-repo"
        assert result["metadata"]["name"] == "example/unknown-repo"

    def test_link_repo_missing_args(self):
        linker = CrossRepoLinker()
        assert linker.link_repo("", "name")["success"] is False
        assert linker.link_repo("url", "")["success"] is False

    def test_sync_metadata(self):
        linker = CrossRepoLinker()
        linker.link_repo(
            "https://github.com/langchain-ai/langchain",
            "langchain-ai/langchain",
        )
        original_stars = linker.linked_repos["langchain-ai/langchain"]["stars"]
        result = linker.sync_metadata("langchain-ai/langchain")
        assert result["success"] is True
        assert result["repo_name"] == "langchain-ai/langchain"
        assert "updated_metadata" in result
        updated = result["updated_metadata"]
        assert updated["stars"] >= original_stars
        assert "health" in updated
        assert linker.linked_repos["langchain-ai/langchain"]["sync_count"] == 1
        assert linker._sync_count == 1
        assert linker._last_sync is not None

    def test_sync_metadata_unlinked(self):
        linker = CrossRepoLinker()
        result = linker.sync_metadata("nonexistent/repo")
        assert result["success"] is False
        assert "error" in result

    def test_get_linked_repos(self):
        linker = CrossRepoLinker()
        assert linker.get_linked_repos() == []
        linker.link_repo(
            "https://github.com/langchain-ai/langchain",
            "langchain-ai/langchain",
        )
        linker.link_repo(
            "https://github.com/openai/openai-python",
            "openai/openai-python",
        )
        repos = linker.get_linked_repos()
        assert len(repos) == 2
        for repo in repos:
            assert "name" in repo
            assert "url" in repo
            assert "stars" in repo
            assert "contributors" in repo
            assert "module_count" in repo
            assert "health" in repo
            assert "last_sync" in repo
            assert "linked_at" in repo
            assert "sync_count" in repo

    def test_get_status(self):
        linker = CrossRepoLinker()
        status = linker.get_status()
        assert status["linked_count"] == 0
        assert status["active_channels"] == 0
        assert status["latest_sync"] is None
        assert status["total_syncs"] == 0
        assert status["total_scans"] == 0

        linker.link_repo("https://github.com/huggingface/transformers", "huggingface/transformers")
        linker.sync_metadata("huggingface/transformers")
        status = linker.get_status()
        assert status["linked_count"] == 1
        assert status["active_channels"] == 1
        assert status["latest_sync"] is not None
        assert status["total_syncs"] == 1

    def test_compute_health_no_sync(self):
        linker = CrossRepoLinker()
        health = linker._compute_health(None, 1.0)
        assert 0.0 <= health <= 1.0
        assert health == pytest.approx(0.5, abs=0.01)

    def test_compute_health_recent_sync(self):
        linker = CrossRepoLinker()
        from datetime import datetime, timezone
        now = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        health = linker._compute_health(now, 1.0)
        assert health > 0.9

    def test_compute_health_old_sync(self):
        linker = CrossRepoLinker()
        old = "2020-01-01T00:00:00Z"
        health = linker._compute_health(old, 1.0)
        # Freshness -> 0, so health = fetch_success_rate * 0.6 = 0.6
        assert health == pytest.approx(0.6, abs=0.01)

    def test_get_status_returns_channel_ids(self):
        linker = CrossRepoLinker()
        linker.link_repo("https://github.com/pytorch/pytorch", "pytorch/pytorch")
        status = linker.get_status()
        assert "channel_ids" in status
        assert len(status["channel_ids"]) == 1

    def test_singleton(self):
        a = get_cross_repo_linker()
        b = get_cross_repo_linker()
        assert a is b

    def test_simulated_repos_populated(self):
        assert len(SIMULATED_REPOS) == 5
        for key, repo in SIMULATED_REPOS.items():
            assert "url" in repo
            assert "name" in repo
            assert "stars" in repo
            assert "last_commit" in repo
            assert "contributors" in repo
            assert "module_count" in repo
            assert "health" in repo
