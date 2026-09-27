import hashlib
import time
import random
from typing import Dict, List, Any


class NodeDiscovery:
    """Decentralized node discovery with heartbeat-based peer management."""

    def __init__(self) -> None:
        self._peers: Dict[str, float] = {}
        self._own_fingerprint: str = self._generate_fingerprint()
        self._stale_threshold: float = 300.0

    def _generate_fingerprint(self) -> str:
        """Generate a unique node fingerprint from timestamp + random."""
        raw = f"{time.time()}-{random.getrandbits(128)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def discover(self, peer_id: str = "") -> Dict[str, Any]:
        """Simulate discovering a new peer and add it to the peer list."""
        if not peer_id:
            peer_id = self._generate_fingerprint()
        now = time.time()
        self._peers[peer_id] = now
        return {
            "peer_id": peer_id,
            "timestamp": now,
            "peer_count": len(self._peers),
        }

    def heartbeat(self) -> Dict[str, Any]:
        """Send heartbeat to all known peers and remove stale ones."""
        now = time.time()
        stale_peers: List[str] = []
        for peer_id, last_seen in self._peers.items():
            if now - last_seen > self._stale_threshold:
                stale_peers.append(peer_id)
        for peer_id in stale_peers:
            del self._peers[peer_id]
        return {
            "timestamp": now,
            "active_peers": len(self._peers),
            "removed_stale": len(stale_peers),
        }

    def get_peer_count(self) -> int:
        """Return the number of active peers."""
        return len(self._peers)

    def get_status(self) -> Dict[str, Any]:
        """Return current discovery status."""
        now = time.time()
        active_count = len(self._peers)
        oldest_peer = None
        newest_peer = None
        if self._peers:
            sorted_peers = sorted(self._peers.items(), key=lambda x: x[1])
            oldest_peer = {
                "peer_id": sorted_peers[0][0],
                "last_seen": sorted_peers[0][1],
                "age_seconds": now - sorted_peers[0][1],
            }
            newest_peer = {
                "peer_id": sorted_peers[-1][0],
                "last_seen": sorted_peers[-1][1],
                "age_seconds": now - sorted_peers[-1][1],
            }
        return {
            "peer_count": active_count,
            "own_fingerprint": self._own_fingerprint,
            "oldest_peer": oldest_peer,
            "newest_peer": newest_peer,
        }


_module = None


def get_node_discovery() -> NodeDiscovery:
    global _module
    if _module is None:
        _module = NodeDiscovery()
    return _module
