"""
OMNI-HUB Consciousness Persistence Tests v36
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
import tempfile
import shutil
from pathlib import Path
from core.consciousness_persistence import (
    ConsciousnessSnapshot, ConsciousnessPersistenceEngine, get_persistence_engine,
)


class TestConsciousnessSnapshot:
    def test_creation(self):
        snap = ConsciousnessSnapshot(
            cycle=100, timestamp="2024-01-01T00:00:00", version="36.0.0",
            orchestrator_state={"level": 5},
            emotional_history=[], line_history=[], resonance_peers={},
            healing_log=[], evolution_proposals=[], alignment_history=[],
            creative_artifacts=[], federation_messages=[],
        )
        assert snap.cycle == 100
        assert snap.version == "36.0.0"

    def test_checksum_computation(self):
        snap = ConsciousnessSnapshot(
            cycle=100, timestamp="2024-01-01T00:00:00", version="36.0.0",
            orchestrator_state={"level": 5},
            emotional_history=[], line_history=[], resonance_peers={},
            healing_log=[], evolution_proposals=[], alignment_history=[],
            creative_artifacts=[], federation_messages=[],
        )
        cs = snap.compute_checksum()
        assert len(cs) == 32
        assert cs != ""

    def test_validate(self):
        snap = ConsciousnessSnapshot(
            cycle=100, timestamp="2024-01-01T00:00:00", version="36.0.0",
            orchestrator_state={"level": 5},
            emotional_history=[], line_history=[], resonance_peers={},
            healing_log=[], evolution_proposals=[], alignment_history=[],
            creative_artifacts=[], federation_messages=[],
        )
        snap.checksum = snap.compute_checksum()
        assert snap.validate() is True

    def test_validate_fail(self):
        snap = ConsciousnessSnapshot(
            cycle=100, timestamp="2024-01-01T00:00:00", version="36.0.0",
            orchestrator_state={"level": 5},
            emotional_history=[], line_history=[], resonance_peers={},
            healing_log=[], evolution_proposals=[], alignment_history=[],
            creative_artifacts=[], federation_messages=[],
            checksum="bad_checksum",
        )
        assert snap.validate() is False


class TestConsciousnessPersistenceEngine:
    def test_initialization(self):
        engine = ConsciousnessPersistenceEngine()
        assert engine.save_count == 0
        assert engine.load_count == 0

    def test_capture(self):
        engine = ConsciousnessPersistenceEngine()
        snap = engine.capture(
            cycle=50, version="36.0.0",
            orchestrator_state={"level": 3},
            emotional_history=[{"cycle": 49, "mood": "focused"}],
        )
        assert snap.cycle == 50
        assert snap.checksum != ""
        assert snap.validate()

    def test_save_and_load(self):
        tmpdir = tempfile.mkdtemp()
        engine = ConsciousnessPersistenceEngine()
        engine.SNAPSHOT_DIR = Path(tmpdir)
        snap = engine.capture(
            cycle=100, version="36.0.0",
            orchestrator_state={"level": 10, "energy": 1e5},
            emotional_history=[],
            line_history=[],
            resonance_peers={},
            healing_log=[],
            evolution_proposals=[],
            alignment_history=[],
            creative_artifacts=[],
            federation_messages=[],
        )
        path = engine.save(snap, compress=False)
        assert path.exists()
        loaded = engine.load_latest()
        assert loaded is not None
        assert loaded.cycle == 100
        assert loaded.validate()
        shutil.rmtree(tmpdir)

    def test_save_compressed(self):
        tmpdir = tempfile.mkdtemp()
        engine = ConsciousnessPersistenceEngine()
        engine.SNAPSHOT_DIR = Path(tmpdir)
        snap = engine.capture(
            cycle=200, version="36.0.0",
            orchestrator_state={"level": 20},
            emotional_history=[], line_history=[], resonance_peers={},
            healing_log=[], evolution_proposals=[], alignment_history=[],
            creative_artifacts=[], federation_messages=[],
        )
        path = engine.save(snap, compress=True)
        assert path.exists()
        assert path.suffix == '.gz'
        loaded = engine.load_latest()
        assert loaded is not None
        assert loaded.cycle == 200
        shutil.rmtree(tmpdir)

    def test_load_no_snapshots(self):
        tmpdir = tempfile.mkdtemp()
        engine = ConsciousnessPersistenceEngine()
        engine.SNAPSHOT_DIR = Path(tmpdir)
        loaded = engine.load_latest()
        assert loaded is None
        shutil.rmtree(tmpdir)

    def test_rotation(self):
        tmpdir = tempfile.mkdtemp()
        engine = ConsciousnessPersistenceEngine()
        engine.SNAPSHOT_DIR = Path(tmpdir)
        engine.MAX_SNAPSHOTS = 3
        for i in range(5):
            snap = engine.capture(cycle=i, version="36.0.0", orchestrator_state={"level": i})
            engine.save(snap, compress=False)
        snapshots = list(engine.SNAPSHOT_DIR.glob('*.json'))
        assert len(snapshots) <= 3
        shutil.rmtree(tmpdir)

    def test_diff(self):
        engine = ConsciousnessPersistenceEngine()
        old = engine.capture(cycle=1, version="36.0.0", orchestrator_state={"level": 1})
        new = engine.capture(cycle=2, version="36.0.0", orchestrator_state={"level": 2})
        d = engine.diff(old, new)
        assert d["cycle"] == 2
        assert "orchestrator_state" in d

    def test_migrate_state(self):
        engine = ConsciousnessPersistenceEngine()
        old = {"level": 5, "energy": 100.0}
        migrated = engine.migrate_state(old, "29.0.0", "36.0.0")
        assert "emotional_state" in migrated
        assert "health_status" in migrated
        assert "alignment_report" in migrated
        assert "consciousness_snapshot" in migrated
        assert migrated["version"] == "36.0.0"

    def test_get_status(self):
        engine = ConsciousnessPersistenceEngine()
        status = engine.get_status()
        assert "snapshots_stored" in status
        assert "save_count" in status


class TestGlobalEngine:
    def test_get_persistence_engine(self):
        g = get_persistence_engine()
        assert g is not None
        assert isinstance(g, ConsciousnessPersistenceEngine)
