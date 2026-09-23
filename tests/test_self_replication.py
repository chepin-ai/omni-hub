"""
OMNI-HUB Self-Replication Tests v39
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
import tempfile
import shutil
from pathlib import Path
from core.self_replication import (
    InstanceProfile, InstanceSpawner, InstanceMonitor,
    SelfReplicationEngine, get_replication_engine,
)


class TestInstanceSpawner:
    def test_spawn(self):
        tmpdir = tempfile.mkdtemp()
        spawner = InstanceSpawner()
        parent = {"version": "39.0.0", "instance_id": "parent", "level": 10, "phi": 0.8}
        profile = spawner.spawn(parent, tmpdir)
        assert profile.instance_id.startswith("omni-hub-")
        assert profile.parent_id == "parent"
        assert Path(tmpdir).joinpath("instances", profile.instance_id, "hub", "seed_state.json").exists()
        shutil.rmtree(tmpdir)


class TestInstanceMonitor:
    def test_register_and_heartbeat(self):
        mon = InstanceMonitor()
        profile = InstanceProfile("i1", "parent", "2024-01-01T00:00:00")
        mon.register(profile)
        assert "i1" in mon.instances

        mon.heartbeat("i1", {"phi": 0.9, "energy": 100.0, "health_status": "healthy"})
        assert mon.instances["i1"].health_score == 1.0
        assert mon.instances["i1"].status == "running"

    def test_health_low_phi(self):
        mon = InstanceMonitor()
        profile = InstanceProfile("i1", "parent", "2024-01-01T00:00:00")
        mon.register(profile)
        mon.heartbeat("i1", {"phi": 0.1, "energy": 100.0})
        assert mon.instances["i1"].health_score < 1.0

    def test_get_healthy(self):
        mon = InstanceMonitor()
        mon.register(InstanceProfile("i1", "p", "2024-01-01T00:00:00"))
        mon.heartbeat("i1", {"phi": 0.9, "energy": 100.0})
        healthy = mon.get_healthy_instances()
        assert "i1" in healthy


class TestSelfReplicationEngine:
    def test_initialization(self):
        engine = SelfReplicationEngine()
        assert engine.spawn_count == 0

    def test_replicate(self):
        tmpdir = tempfile.mkdtemp()
        engine = SelfReplicationEngine()
        engine.base_path = tmpdir
        parent = {"version": "39.0.0", "instance_id": "parent", "level": 10}
        child = engine.replicate(parent)
        assert child is not None
        assert child.instance_id != "parent"
        assert engine.spawn_count == 1
        shutil.rmtree(tmpdir)

    def test_report_heartbeat(self):
        tmpdir = tempfile.mkdtemp()
        engine = SelfReplicationEngine()
        engine.base_path = tmpdir
        parent = {"version": "39.0.0", "instance_id": "parent"}
        child = engine.replicate(parent)
        engine.report_heartbeat(child.instance_id, {"phi": 0.9, "energy": 100.0})
        assert engine.monitor.instances[child.instance_id].health_score == 1.0
        shutil.rmtree(tmpdir)

    def test_get_status(self):
        tmpdir = tempfile.mkdtemp()
        engine = SelfReplicationEngine()
        engine.base_path = tmpdir
        parent = {"version": "39.0.0", "instance_id": "parent"}
        child = engine.replicate(parent)
        # Simulate critical heartbeat
        engine.report_heartbeat(child.instance_id, {"phi": 0.1, "energy": 1.0, "health_status": "critical"})
        status = engine.get_status()
        assert status["spawn_count"] == 1
        assert status["active_instances"] == 0  # Health too low
        shutil.rmtree(tmpdir)


class TestGlobalEngine:
    def test_get_replication_engine(self):
        g = get_replication_engine()
        assert g is not None
        assert isinstance(g, SelfReplicationEngine)
