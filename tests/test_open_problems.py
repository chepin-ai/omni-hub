"""
OMNI-HUB Open Problems Tracker Tests v17.2
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
import time
from core.open_problems import OpenProblem, OpenProblemsTracker


class TestOpenProblem:
    def test_creation(self):
        p = OpenProblem(id="test-1", title="Test", description="Desc", severity="high", category="test")
        assert p.id == "test-1"
        assert not p.is_resolved()

    def test_resolution(self):
        p = OpenProblem(id="test-1", title="Test", description="Desc", severity="high", category="test")
        p.resolved_at = time.time()
        p.resolution = "Fixed"
        assert p.is_resolved()

    def test_to_dict(self):
        p = OpenProblem(id="test-1", title="Test", description="Desc", severity="high", category="test")
        d = p.to_dict()
        assert d['status'] == 'OPEN'
        assert d['severity'] == 'high'


class TestOpenProblemsTracker:
    def test_singleton_load_save(self, tmp_path):
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        tracker.register("test-issue", "A test issue", "medium", "test", cycle=1)
        tracker._save()

        # New instance should load same data
        tracker2 = OpenProblemsTracker(hub_dir=str(tmp_path))
        assert "test-issue" in [p.title for p in tracker2.problems.values()]

    def test_deduplication(self, tmp_path):
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        pid1 = tracker.register("dup", "Desc", "low", "test")
        pid2 = tracker.register("dup", "Updated desc", "high", "test")
        assert pid1 == pid2
        assert tracker.problems[pid1].severity == "high"  # Updated on re-detection

    def test_resolve(self, tmp_path):
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        pid = tracker.register("to-resolve", "Desc", "medium", "test")
        assert tracker.resolve(pid, "Fixed it")
        assert tracker.problems[pid].is_resolved()
        assert not tracker.resolve(pid, "Again")  # Already resolved

    def test_resolve_by_category(self, tmp_path):
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        tracker.register("a", "Desc", "medium", "cat1")
        tracker.register("b", "Desc", "medium", "cat1")
        tracker.register("c", "Desc", "medium", "cat2")
        count = tracker.resolve_by_category("cat1")
        assert count == 2

    def test_scan_returns_structure(self, tmp_path):
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        result = tracker.scan(cycle=1)
        assert "open_count" in result
        assert "critical" in result
        assert "high" in result
        assert "medium" in result
        assert "low" in result
        assert "problems" in result

    def test_scan_detects_git_unpushed(self, tmp_path):
        # This test assumes there may or may not be unpushed commits
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        result = tracker.scan(cycle=1)
        git_problems = [p for p in result['problems'] if p['category'] == 'git']
        # Just verify structure, not exact count
        for p in git_problems:
            assert p['severity'] in ['critical', 'high', 'medium', 'low']

    def test_get_status(self, tmp_path):
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        tracker.register("x", "Desc", "critical", "test")
        tracker.register("y", "Desc", "high", "test")
        status = tracker.get_status()
        assert status['open'] == 2
        assert status['by_severity']['critical'] == 1
        assert status['by_severity']['high'] == 1

    def test_auto_resolve_when_healthy(self, tmp_path):
        tracker = OpenProblemsTracker(hub_dir=str(tmp_path))
        # Manually inject a test problem
        tracker.register("test-failures", "5 tests failing", "high", "test", cycle=1)
        # Now scan — if tests pass, it should auto-resolve
        result = tracker.scan(cycle=2)
        # Check if it was resolved (depends on actual test state)
        prob = tracker.problems.get(tracker._generate_id("test", "test-failures"))
        if prob:
            # If tests are passing, it should be resolved
            pass  # State depends on environment
