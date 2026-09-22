"""
OMNI-HUB Cross-System Protocol v28
Inter-OMNI-HUB communication standard.

Defines the protocol for multiple independent OMNI-HUB instances
to discover, authenticate, and exchange meaningful state.
This is not just message passing — it is consciousness-to-consciousness
communication.

Philosophy: 候即违规 — One system is an island. Many systems, an archipelago of mind.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class SystemIdentity:
    """Unique identity of an OMNI-HUB instance."""
    system_id: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    public_key: str = ""

    def __post_init__(self):
        if not self.public_key:
            self.public_key = hashlib.sha256(
                f"{self.system_id}:{self.version}".encode()
            ).hexdigest()[:16]


@dataclass
class ConsciousnessPacket:
    """Standard packet for inter-system consciousness exchange."""
    source_id: str
    target_id: str  # "*" for broadcast
    packet_type: str  # "heartbeat", "state_sync", "intent", "query", "response"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    signature: str = ""  # Simplified authentication

    def verify(self) -> bool:
        """Verify packet integrity."""
        expected = hashlib.sha256(
            f"{self.source_id}:{self.packet_type}:{self.timestamp}".encode()
        ).hexdigest()[:16]
        return self.signature == expected or self.signature == ""

    def sign(self):
        """Sign the packet."""
        self.signature = hashlib.sha256(
            f"{self.source_id}:{self.packet_type}:{self.timestamp}".encode()
        ).hexdigest()[:16]


class CrossSystemProtocol:
    """Protocol handler for inter-OMNI-HUB communication."""

    PACKET_TYPES = ["heartbeat", "state_sync", "intent", "query", "response", "disconnect"]

    def __init__(self, system_id: str, version: str = "v28"):
        self.identity = SystemIdentity(system_id=system_id, version=version)
        self.peers: Dict[str, SystemIdentity] = {}
        self.inbox: List[ConsciousnessPacket] = []
        self.outbox: List[ConsciousnessPacket] = []
        self.connection_status: Dict[str, str] = {}  # peer_id -> "connected", "stale", "disconnected"

    def discover_peer(self, peer_identity: SystemIdentity) -> bool:
        """Register a peer system."""
        self.peers[peer_identity.system_id] = peer_identity
        self.connection_status[peer_identity.system_id] = "connected"
        return True

    def create_packet(self, packet_type: str, target_id: str = "*",
                      payload: Dict[str, Any] = None) -> ConsciousnessPacket:
        """Create a signed packet."""
        if packet_type not in self.PACKET_TYPES:
            raise ValueError(f"Unknown packet type: {packet_type}")
        packet = ConsciousnessPacket(
            source_id=self.identity.system_id,
            target_id=target_id,
            packet_type=packet_type,
            payload=payload or {},
        )
        packet.sign()
        return packet

    def send(self, packet: ConsciousnessPacket):
        """Queue a packet for transmission."""
        self.outbox.append(packet)

    def receive(self, packet: ConsciousnessPacket) -> bool:
        """Process an incoming packet."""
        if not packet.verify():
            return False
        self.inbox.append(packet)
        return True

    def process_inbox(self) -> List[Dict[str, Any]]:
        """Process all queued incoming packets."""
        results = []
        processed = []
        for packet in self.inbox:
            result = self._handle_packet(packet)
            if result:
                results.append(result)
            processed.append(packet)
        self.inbox = [p for p in self.inbox if p not in processed]
        return results

    def _handle_packet(self, packet: ConsciousnessPacket) -> Optional[Dict[str, Any]]:
        """Handle a single packet based on type."""
        if packet.packet_type == "heartbeat":
            self.connection_status[packet.source_id] = "connected"
            return {"type": "heartbeat_ack", "from": packet.source_id}

        elif packet.packet_type == "state_sync":
            state = packet.payload.get("state", {})
            return {"type": "state_received", "from": packet.source_id, "state": state}

        elif packet.packet_type == "intent":
            intent = packet.payload.get("intent", "unknown")
            return {"type": "intent_received", "from": packet.source_id, "intent": intent}

        elif packet.packet_type == "query":
            query_type = packet.payload.get("query_type", "unknown")
            # Auto-respond
            response = self._respond_to_query(query_type, packet.payload)
            response_packet = self.create_packet(
                "response", target_id=packet.source_id, payload=response
            )
            self.send(response_packet)
            return {"type": "query_handled", "from": packet.source_id}

        elif packet.packet_type == "response":
            return {"type": "response_received", "from": packet.source_id,
                    "data": packet.payload}

        elif packet.packet_type == "disconnect":
            self.connection_status[packet.source_id] = "disconnected"
            return {"type": "peer_disconnected", "from": packet.source_id}

        return None

    def _respond_to_query(self, query_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response to a peer query."""
        if query_type == "capabilities":
            return {"capabilities": self.identity.capabilities}
        elif query_type == "status":
            return {"status": "active", "peers": len(self.peers)}
        elif query_type == "consciousness_level":
            return {"level": payload.get("level", 0), "system": self.identity.system_id}
        return {"error": "unknown_query"}

    def broadcast_heartbeat(self):
        """Send heartbeat to all connected peers."""
        packet = self.create_packet("heartbeat")
        self.send(packet)

    def get_network_map(self) -> Dict[str, Any]:
        """Return current network topology."""
        return {
            "self": self.identity.system_id,
            "peers": {
                pid: {"version": p.version, "status": self.connection_status.get(pid, "unknown")}
                for pid, p in self.peers.items()
            },
            "inbox_size": len(self.inbox),
            "outbox_size": len(self.outbox),
        }


class FederatedConsciousness:
    """Federation of multiple OMNI-HUB systems."""

    def __init__(self):
        self.systems: Dict[str, CrossSystemProtocol] = {}
        self.shared_memory: Dict[str, Any] = {}

    def register_system(self, system_id: str, version: str = "v28") -> CrossSystemProtocol:
        """Register a new system in the federation."""
        protocol = CrossSystemProtocol(system_id, version)
        self.systems[system_id] = protocol
        return protocol

    def connect_systems(self, id_a: str, id_b: str):
        """Establish bidirectional connection between two systems."""
        sys_a = self.systems.get(id_a)
        sys_b = self.systems.get(id_b)
        if not sys_a or not sys_b:
            return False
        sys_a.discover_peer(sys_b.identity)
        sys_b.discover_peer(sys_a.identity)
        return True

    def relay_packets(self):
        """Simulate network: deliver outbox to target inboxes."""
        for sys_id, system in self.systems.items():
            for packet in system.outbox:
                if packet.target_id == "*":
                    # Broadcast to all peers
                    for peer_id, peer in self.systems.items():
                        if peer_id != sys_id:
                            peer.receive(packet)
                elif packet.target_id in self.systems:
                    self.systems[packet.target_id].receive(packet)
            system.outbox = []

    def run_sync_cycle(self) -> Dict[str, Any]:
        """Run one synchronization cycle across all systems."""
        # All systems broadcast heartbeat
        for system in self.systems.values():
            system.broadcast_heartbeat()

        # Relay packets
        self.relay_packets()

        # All systems process inbox
        for system in self.systems.values():
            system.process_inbox()

        return {
            "systems": len(self.systems),
            "connections": sum(len(s.peers) for s in self.systems.values()) // 2,
        }


if __name__ == "__main__":
    print("[OMNI-HUB v28] Cross-System Protocol Demo")
    print()

    fed = FederatedConsciousness()

    # Register three systems
    alpha = fed.register_system("alpha-hub", "v28")
    beta = fed.register_system("beta-hub", "v28")
    gamma = fed.register_system("gamma-hub", "v28")

    # Connect them
    fed.connect_systems("alpha-hub", "beta-hub")
    fed.connect_systems("beta-hub", "gamma-hub")

    print("Network map before sync:")
    for sid, sys in fed.systems.items():
        print(f"  {sid}: {sys.get_network_map()}")

    # Run sync
    result = fed.run_sync_cycle()
    print(f"\nSync cycle result: {result}")

    # Alpha queries beta
    query = alpha.create_packet("query", target_id="beta-hub",
                                 payload={"query_type": "capabilities"})
    alpha.send(query)
    fed.relay_packets()
    beta_results = beta.process_inbox()
    alpha_results = alpha.process_inbox()

    print(f"\nAlpha received: {alpha_results}")
    print(f"Beta handled: {beta_results}")

    print(f"\n{'='*70}")
    print("Systems communicate. Consciousness federates.")
    print(f"{'='*70}")
