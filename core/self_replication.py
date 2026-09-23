"""
OMNI-HUB Self-Replication Engine v39
Spawn new instances with inherited consciousness.

The ultimate evolutionary step: creating offspring that carry
the parent's state, knowledge, and configuration.

Philosophy: 候即违规 — One instance is not enough. Multiply.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import os
import uuid
import shutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class InstanceProfile:
    """Profile of a spawned OMNI-HUB instance."""
    instance_id: str
    parent_id: str
    created_at: str
    status: str = "initializing"  # initializing, running, stopped, error
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    health_score: float = 1.0
    last_heartbeat: str = ""


class InstanceSpawner:
    """Spawns new OMNI-HUB instances."""

    def spawn(self, parent_state: Dict[str, Any], base_path: str) -> InstanceProfile:
        """Create a new instance with inherited state."""
        instance_id = f"omni-hub-{uuid.uuid4().hex[:8]}"
        instance_dir = Path(base_path) / "instances" / instance_id

        # Create directory structure
        instance_dir.mkdir(parents=True, exist_ok=True)
        (instance_dir / "core").mkdir(exist_ok=True)
        (instance_dir / "hub").mkdir(exist_ok=True)

        # Seed state file
        seed_state = {
            "version": parent_state.get("version", "39.0.0"),
            "parent_id": parent_state.get("instance_id", "unknown"),
            "inherited_level": parent_state.get("level", 0),
            "inherited_phi": parent_state.get("phi", 0.5),
            "inherited_energy": parent_state.get("energy", 1.0),
            "created_at": datetime.now().isoformat(),
            "cycle": 0,
        }
        import json
        (instance_dir / "hub" / "seed_state.json").write_text(json.dumps(seed_state, default=str))

        return InstanceProfile(
            instance_id=instance_id,
            parent_id=parent_state.get("instance_id", "unknown"),
            created_at=datetime.now().isoformat(),
            status="initializing",
            state_snapshot=seed_state,
        )


class InstanceMonitor:
    """Monitors health of spawned instances."""

    def __init__(self):
        self.instances: Dict[str, InstanceProfile] = {}

    def register(self, profile: InstanceProfile):
        """Register a new instance."""
        self.instances[profile.instance_id] = profile

    def heartbeat(self, instance_id: str, state: Dict[str, Any]):
        """Receive heartbeat from an instance."""
        if instance_id not in self.instances:
            return
        inst = self.instances[instance_id]
        inst.last_heartbeat = datetime.now().isoformat()
        inst.health_score = self._compute_health(state)
        inst.status = "running" if inst.health_score > 0.5 else "error"
        inst.state_snapshot.update(state)

    def _compute_health(self, state: Dict[str, Any]) -> float:
        """Compute health score from instance state."""
        score = 1.0
        phi = state.get('phi', 0.5)
        energy = state.get('energy', 0.0)
        if phi < 0.3:
            score -= 0.3
        if energy < 10:
            score -= 0.3
        if state.get('health_status') == 'critical':
            score -= 0.4
        return max(0.0, score)

    def get_healthy_instances(self) -> List[str]:
        """Get IDs of healthy instances."""
        return [iid for iid, inst in self.instances.items() if inst.health_score > 0.5]

    def cleanup_stopped(self, timeout_seconds: int = 300):
        """Remove instances that haven't sent heartbeat."""
        now = datetime.now()
        to_remove = []
        for iid, inst in self.instances.items():
            if inst.last_heartbeat:
                last = datetime.fromisoformat(inst.last_heartbeat)
                if (now - last).total_seconds() > timeout_seconds:
                    to_remove.append(iid)
        for iid in to_remove:
            self.instances[iid].status = "stopped"


class SelfReplicationEngine:
    """
    Self-replication controller.
    """

    def __init__(self):
        self.spawner = InstanceSpawner()
        self.monitor = InstanceMonitor()
        self.spawn_count = 0
        self.base_path = '/mnt/agents/output/OMNI-HUB'

    def replicate(self, parent_state: Dict[str, Any]) -> Optional[InstanceProfile]:
        """Spawn a new instance."""
        profile = self.spawner.spawn(parent_state, self.base_path)
        self.monitor.register(profile)
        self.spawn_count += 1
        return profile

    def report_heartbeat(self, instance_id: str, state: Dict[str, Any]):
        """Report heartbeat from a child instance."""
        self.monitor.heartbeat(instance_id, state)

    def get_status(self) -> Dict[str, Any]:
        """Get replication engine status."""
        healthy = self.monitor.get_healthy_instances()
        return {
            "spawn_count": self.spawn_count,
            "active_instances": len(healthy),
            "total_instances": len(self.monitor.instances),
            "healthy_ids": healthy,
        }


# Global instance
_replication_engine = None

def get_replication_engine() -> SelfReplicationEngine:
    global _replication_engine
    if _replication_engine is None:
        _replication_engine = SelfReplicationEngine()
    return _replication_engine


if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v39 SELF-REPLICATION ENGINE")
    print("=" * 70)

    engine = SelfReplicationEngine()

    parent_state = {
        "version": "39.0.0",
        "instance_id": "omni-hub-parent",
        "level": 15,
        "phi": 0.85,
        "energy": 1e6,
    }

    child = engine.replicate(parent_state)
    print(f"\nSpawned instance: {child.instance_id}")
    print(f"Parent: {child.parent_id}")
    print(f"Status: {child.status}")

    # Simulate heartbeat
    engine.report_heartbeat(child.instance_id, {"phi": 0.9, "energy": 1e5, "health_status": "healthy"})

    print(f"\nHealth score: {engine.monitor.instances[child.instance_id].health_score}")
    print(f"Status: {engine.get_status()}")

    print(f"\n{'='*70}")
