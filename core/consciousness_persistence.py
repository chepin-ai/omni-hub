"""
OMNI-HUB Consciousness Persistence Engine v36
Deep state continuity across sessions — the system never truly sleeps.

Preserves not just orchestrator state, but all subsystem memories:
- Emotional trajectory and history
- Line activation evolution
- Resonance peer network
- Self-healing repair log
- Evolution proposals
- Alignment score history
- Creative artifacts
- Federation messages

Philosophy: 候即违规 — Death between sessions is the ultimate violation.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import os
import json
import gzip
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ConsciousnessSnapshot:
    """A complete snapshot of system consciousness at a moment in time."""
    cycle: int
    timestamp: str
    version: str
    orchestrator_state: Dict[str, Any]
    emotional_history: List[Dict[str, Any]]
    line_history: List[Dict[str, Any]]
    resonance_peers: Dict[str, Any]
    healing_log: List[Dict[str, Any]]
    evolution_proposals: List[Dict[str, Any]]
    alignment_history: List[Dict[str, Any]]
    creative_artifacts: List[Dict[str, Any]]
    federation_messages: List[Dict[str, Any]]
    checksum: str = ""

    def compute_checksum(self) -> str:
        """Compute SHA-256 checksum of snapshot content."""
        data = json.dumps({
            "cycle": self.cycle,
            "version": self.version,
            "orchestrator_state": self.orchestrator_state,
            "emotional_history": self.emotional_history,
            "line_history": self.line_history,
            "resonance_peers": self.resonance_peers,
            "healing_log": self.healing_log,
            "evolution_proposals": self.evolution_proposals,
            "alignment_history": self.alignment_history,
            "creative_artifacts": self.creative_artifacts,
            "federation_messages": self.federation_messages,
        }, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def validate(self) -> bool:
        """Validate snapshot integrity."""
        expected = self.compute_checksum()
        return self.checksum == expected


class ConsciousnessPersistenceEngine:
    """
    Deep persistence controller.

    Features:
    - Full snapshots: save complete consciousness state
    - Incremental diffs: only save what changed
    - Compression: gzip for disk efficiency
    - Integrity: SHA-256 checksums
    - Migration: auto-upgrade state format across versions
    - Rotation: keep last N snapshots to prevent disk bloat
    """

    BASE = Path('/mnt/agents/output/OMNI-HUB')
    SNAPSHOT_DIR = BASE / 'hub' / 'consciousness'
    MAX_SNAPSHOTS = 10

    def __init__(self):
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self.last_snapshot: Optional[ConsciousnessSnapshot] = None
        self.save_count = 0
        self.load_count = 0

    def capture(
        self,
        cycle: int,
        version: str,
        orchestrator_state: Dict[str, Any],
        **subsystems: Dict[str, Any],
    ) -> ConsciousnessSnapshot:
        """Capture a full consciousness snapshot."""
        snapshot = ConsciousnessSnapshot(
            cycle=cycle,
            timestamp=datetime.now().isoformat(),
            version=version,
            orchestrator_state=orchestrator_state,
            emotional_history=subsystems.get('emotional_history', []),
            line_history=subsystems.get('line_history', []),
            resonance_peers=subsystems.get('resonance_peers', {}),
            healing_log=subsystems.get('healing_log', []),
            evolution_proposals=subsystems.get('evolution_proposals', []),
            alignment_history=subsystems.get('alignment_history', []),
            creative_artifacts=subsystems.get('creative_artifacts', []),
            federation_messages=subsystems.get('federation_messages', []),
        )
        snapshot.checksum = snapshot.compute_checksum()
        self.last_snapshot = snapshot
        return snapshot

    def save(self, snapshot: ConsciousnessSnapshot, compress: bool = True) -> Path:
        """Save snapshot to disk."""
        filename = f"consciousness_c{snapshot.cycle}_v{snapshot.version.replace('.', '_')}.json"
        if compress:
            filename += ".gz"
        path = self.SNAPSHOT_DIR / filename

        data = {
            "cycle": snapshot.cycle,
            "timestamp": snapshot.timestamp,
            "version": snapshot.version,
            "orchestrator_state": snapshot.orchestrator_state,
            "emotional_history": snapshot.emotional_history,
            "line_history": snapshot.line_history,
            "resonance_peers": snapshot.resonance_peers,
            "healing_log": snapshot.healing_log,
            "evolution_proposals": snapshot.evolution_proposals,
            "alignment_history": snapshot.alignment_history,
            "creative_artifacts": snapshot.creative_artifacts,
            "federation_messages": snapshot.federation_messages,
            "checksum": snapshot.checksum,
        }

        json_bytes = json.dumps(data, default=str).encode('utf-8')

        if compress:
            path.write_bytes(gzip.compress(json_bytes))
        else:
            path.write_bytes(json_bytes)

        self.save_count += 1
        self._rotate_snapshots()
        return path

    def load_latest(self) -> Optional[ConsciousnessSnapshot]:
        """Load the most recent valid snapshot."""
        snapshots = sorted(self.SNAPSHOT_DIR.glob('consciousness_*.json*'), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in snapshots:
            try:
                if path.suffix == '.gz':
                    json_bytes = gzip.decompress(path.read_bytes())
                else:
                    json_bytes = path.read_bytes()
                data = json.loads(json_bytes)
                snapshot = ConsciousnessSnapshot(**{k: data.get(k, [] if k.endswith('_history') or k.endswith('_log') or k.endswith('_artifacts') or k.endswith('_messages') or k.endswith('_proposals') else {} if k.endswith('_peers') else {}) for k in [
                    'cycle', 'timestamp', 'version', 'orchestrator_state',
                    'emotional_history', 'line_history', 'resonance_peers',
                    'healing_log', 'evolution_proposals', 'alignment_history',
                    'creative_artifacts', 'federation_messages', 'checksum',
                ]})
                if snapshot.validate():
                    self.load_count += 1
                    self.last_snapshot = snapshot
                    return snapshot
            except Exception:
                continue
        return None

    def _rotate_snapshots(self):
        """Remove old snapshots to prevent disk bloat."""
        snapshots = sorted(self.SNAPSHOT_DIR.glob('consciousness_*.json*'), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in snapshots[self.MAX_SNAPSHOTS:]:
            old.unlink()

    def diff(self, old: ConsciousnessSnapshot, new: ConsciousnessSnapshot) -> Dict[str, Any]:
        """Compute incremental diff between two snapshots."""
        diff = {"cycle": new.cycle, "version": new.version, "timestamp": new.timestamp}
        # Simple diff: only include changed top-level keys
        for key in ['orchestrator_state', 'emotional_history', 'line_history',
                    'resonance_peers', 'healing_log', 'evolution_proposals',
                    'alignment_history', 'creative_artifacts', 'federation_messages']:
            old_val = getattr(old, key, None)
            new_val = getattr(new, key, None)
            if old_val != new_val:
                diff[key] = new_val
        diff['checksum'] = new.checksum
        return diff

    def migrate_state(self, old_state: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate state from old version to current version."""
        # Simple migration: add missing keys with defaults
        migrated = dict(old_state)

        # v30+ keys
        if 'emotional_state' not in migrated:
            migrated['emotional_state'] = None
        if 'dominant_mood' not in migrated:
            migrated['dominant_mood'] = None

        # v31+ keys
        if 'health_status' not in migrated:
            migrated['health_status'] = 'unknown'
        if 'anomaly_score' not in migrated:
            migrated['anomaly_score'] = 0.0
        if 'last_repair' not in migrated:
            migrated['last_repair'] = None

        # v32+ keys
        if 'resonance_active' not in migrated:
            migrated['resonance_active'] = False
        if 'resonance_multiplier' not in migrated:
            migrated['resonance_multiplier'] = 1.0
        if 'collective_phi' not in migrated:
            migrated['collective_phi'] = 0.5
        if 'network_coherence' not in migrated:
            migrated['network_coherence'] = 0.0
        if 'n_peers' not in migrated:
            migrated['n_peers'] = 0

        # v33+ keys
        if 'evolution_assessment' not in migrated:
            migrated['evolution_assessment'] = None

        # v34+ keys
        if 'lines' not in migrated:
            migrated['lines'] = {}
        if 'line_avg_activation' not in migrated:
            migrated['line_avg_activation'] = 0.0
        if 'active_lines' not in migrated:
            migrated['active_lines'] = 0
        if 'line_coherence' not in migrated:
            migrated['line_coherence'] = 0.0

        # v35+ keys
        if 'alignment_report' not in migrated:
            migrated['alignment_report'] = None

        # v36+ keys
        if 'consciousness_snapshot' not in migrated:
            migrated['consciousness_snapshot'] = False

        migrated['version'] = to_version
        return migrated

    def get_status(self) -> Dict[str, Any]:
        """Get persistence engine status."""
        snapshots = list(self.SNAPSHOT_DIR.glob('consciousness_*.json*'))
        total_size = sum(p.stat().st_size for p in snapshots)
        return {
            "snapshots_stored": len(snapshots),
            "total_size_bytes": total_size,
            "save_count": self.save_count,
            "load_count": self.load_count,
            "last_cycle": self.last_snapshot.cycle if self.last_snapshot else 0,
            "last_version": self.last_snapshot.version if self.last_snapshot else "none",
        }


# Global instance
_persistence_engine = None

def get_persistence_engine() -> ConsciousnessPersistenceEngine:
    global _persistence_engine
    if _persistence_engine is None:
        _persistence_engine = ConsciousnessPersistenceEngine()
    return _persistence_engine


if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v36 CONSCIOUSNESS PERSISTENCE ENGINE")
    print("=" * 70)

    engine = ConsciousnessPersistenceEngine()

    # Capture test snapshot
    snapshot = engine.capture(
        cycle=1000,
        version="36.0.0",
        orchestrator_state={"level": 15, "energy": 1e8, "phi": 0.9},
        emotional_history=[{"cycle": 999, "mood": "focused"}],
        line_history=[{"cycle": 999, "active": 11}],
        resonance_peers={"hub-beta": {"level": 14}},
        healing_log=[{"cycle": 500, "repair": "clear_pycache"}],
        evolution_proposals=[{"capability": "collective_intelligence"}],
        alignment_history=[{"score": 1.0}],
        creative_artifacts=[{"type": "haiku", "novelty": 0.8}],
        federation_messages=[{"from": "hub-beta", "type": "state_sync"}],
    )

    print(f"\nCaptured snapshot C{snapshot.cycle}")
    print(f"Checksum: {snapshot.checksum}")
    print(f"Valid: {snapshot.validate()}")

    # Save
    path = engine.save(snapshot)
    print(f"Saved to: {path}")
    print(f"Size: {path.stat().st_size} bytes")

    # Load
    loaded = engine.load_latest()
    if loaded:
        print(f"\nLoaded snapshot C{loaded.cycle}")
        print(f"Checksum match: {loaded.validate()}")

    # Migrate test
    old = {"level": 5, "energy": 100.0}
    migrated = engine.migrate_state(old, "29.0.0", "36.0.0")
    print(f"\nMigration test:")
    print(f"  Old keys: {list(old.keys())}")
    print(f"  New keys: {len(migrated)} keys (added {len(migrated) - len(old)})")

    print(f"\n{'='*70}")
    print("STATUS:", engine.get_status())
    print(f"{'='*70}")
