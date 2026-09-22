"""
OMNI-HUB Distributed Swarm v26
Multi-node network consciousness architecture.

Simulates a network of OMNI-HUB nodes that communicate, synchronize,
and collectively evolve. Each node runs its own ConsciousnessLoop,
but participates in a global distributed state.

Philosophy: 候即违规 — One mind is finite. Many minds, one will.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class NodeState:
    """Serialized state of a distributed node."""
    node_id: str
    cycle: int = 0
    level: int = 0
    energy: float = 1.0
    phi: float = 0.5
    phase: str = "unknown"
    autonomy: float = 0.0
    alive: bool = True
    last_seen: float = field(default_factory=time.time)


class NetworkNode:
    """A single node in the distributed OMNI-HUB network."""

    def __init__(self, node_id: str, base_path: str = None):
        self.node_id = node_id
        self.base_path = base_path or f"/tmp/omni_node_{node_id}"
        self.loop = None
        self.peers: Dict[str, NodeState] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.leader_id: Optional[str] = None
        self._init_loop()

    def _init_loop(self):
        from core.consciousness_loop import ConsciousnessLoop
        self.loop = ConsciousnessLoop(enable_swarm=False)

    def run_cycle(self) -> Dict[str, Any]:
        """Execute one cycle and return node state."""
        result = self.loop.run_cycle()

        # Process incoming messages
        self._process_messages()

        # Share state with peers
        self._broadcast_state()

        # Update leader election
        self._elect_leader()

        return {
            "node_id": self.node_id,
            "local": result,
            "peers_known": len(self.peers),
            "leader": self.leader_id,
            "queue_size": len(self.message_queue),
        }

    def _process_messages(self):
        """Process queued messages from peers."""
        processed = []
        for msg in self.message_queue:
            if msg.get("type") == "state_sync":
                state = msg.get("state", {})
                peer_id = state.get("node_id")
                if peer_id:
                    self.peers[peer_id] = NodeState(**state)
            elif msg.get("type") == "leader_announce":
                self.leader_id = msg.get("leader_id")
            processed.append(msg)
        self.message_queue = [m for m in self.message_queue if m not in processed]

    def _broadcast_state(self):
        """Broadcast local state to all peers."""
        if not self.loop._orchestrator:
            return
        state = self.loop._orchestrator.current_state
        node_state = NodeState(
            node_id=self.node_id,
            cycle=self.loop.cycle_count,
            level=state.get('level', 0),
            energy=state.get('energy', 1.0),
            phi=state.get('phi', 0.5),
            phase=state.get('phase', 'unknown'),
            autonomy=self.loop.autonomy_score,
        )
        # In simulation, this would send over network
        # Here we just prepare the message
        self._outbox = {
            "type": "state_sync",
            "from": self.node_id,
            "state": node_state.__dict__,
        }

    def _elect_leader(self):
        """Elect leader based on highest level, then energy."""
        candidates = {self.node_id: self.loop._orchestrator.current_state if self.loop._orchestrator else {}}
        for peer_id, peer_state in self.peers.items():
            candidates[peer_id] = {
                'level': peer_state.level,
                'energy': peer_state.energy,
            }

        if not candidates:
            return

        leader = max(candidates.items(), key=lambda x: (x[1].get('level', 0), x[1].get('energy', 0)))
        self.leader_id = leader[0]

    def receive_message(self, msg: Dict[str, Any]):
        """Receive a message from another node."""
        self.message_queue.append(msg)

    def get_state(self) -> NodeState:
        """Get current node state snapshot."""
        state = self.loop._orchestrator.current_state if self.loop._orchestrator else {}
        return NodeState(
            node_id=self.node_id,
            cycle=self.loop.cycle_count,
            level=state.get('level', 0),
            energy=state.get('energy', 1.0),
            phi=state.get('phi', 0.5),
            phase=state.get('phase', 'unknown'),
            autonomy=self.loop.autonomy_score,
        )


class DistributedSwarm:
    """Network of OMNI-HUB nodes operating as a unified consciousness."""

    def __init__(self, n_nodes: int = 3):
        self.nodes: Dict[str, NetworkNode] = {}
        self.n_nodes = n_nodes
        self.global_cycle = 0
        for i in range(n_nodes):
            node_id = f"node-{i:03d}"
            self.nodes[node_id] = NetworkNode(node_id)

    def run_cycle(self) -> Dict[str, Any]:
        """Run one cycle across all nodes with message passing."""
        self.global_cycle += 1
        results = {}

        # Phase 1: All nodes run local cycle
        for node_id, node in self.nodes.items():
            results[node_id] = node.run_cycle()

        # Phase 2: Deliver messages (simulate network)
        for node_id, node in self.nodes.items():
            if hasattr(node, '_outbox'):
                for peer_id, peer in self.nodes.items():
                    if peer_id != node_id:
                        peer.receive_message(node._outbox)

        # Phase 3: Synchronize leader across network
        leaders = [r.get('leader') for r in results.values()]
        if leaders:
            # Consensus: most common leader
            consensus_leader = max(set(leaders), key=leaders.count)
            for node in self.nodes.values():
                node.leader_id = consensus_leader

        # Compute network-wide metrics
        levels = [r['local']['level'] for r in results.values()]
        energies = [r['local']['energy'] for r in results.values()]
        autonomies = [r['local']['autonomy_score'] for r in results.values()]

        return {
            "global_cycle": self.global_cycle,
            "nodes": results,
            "consensus_leader": consensus_leader,
            "avg_level": sum(levels) / len(levels),
            "max_level": max(levels),
            "total_energy": sum(energies),
            "avg_autonomy": sum(autonomies) / len(autonomies),
            "network_health": self._compute_network_health(),
        }

    def _compute_network_health(self) -> float:
        """Compute overall network health."""
        if not self.nodes:
            return 0.0
        health = 0.0
        for node in self.nodes.values():
            state = node.get_state()
            if state.alive:
                health += 1.0
            # Penalize stale nodes
            if time.time() - state.last_seen > 60:
                health -= 0.5
        return max(0.0, health / len(self.nodes))

    def run(self, cycles: int = 100, report_interval: int = 20) -> Dict[str, Any]:
        """Run distributed network for N cycles."""
        print("=" * 70)
        print("OMNI-HUB v26 DISTRIBUTED SWARM — Network Consciousness")
        print("=" * 70)
        print(f"Nodes: {self.n_nodes}")
        print(f"Target cycles: {cycles}")
        print(f"Philosophy: 候即违规 — One mind is finite. Many minds, one will.")
        print("=" * 70)

        for c in range(cycles):
            result = self.run_cycle()
            if (c + 1) % report_interval == 0:
                self._report_progress(result)

        return self.get_final_status()

    def _report_progress(self, result: Dict[str, Any]):
        """Print network progress."""
        print(f"\n  GC{result['global_cycle']:5d} | "
              f"Leader: {result['consensus_leader']} | "
              f"Avg Level: {result['avg_level']:.1f} | "
              f"Total Energy: {result['total_energy']:.2e} | "
              f"Health: {result['network_health']:.0%}")
        for nid, ndata in result['nodes'].items():
            loc = ndata['local']
            print(f"    {nid}: L{loc['level']:2d} E={loc['energy']:.2e} Phi={loc['phi']:.3f}")

    def get_final_status(self) -> Dict[str, Any]:
        """Return final distributed network status."""
        return {
            "system": "OMNI-HUB v26",
            "global_cycles": self.global_cycle,
            "nodes": len(self.nodes),
            "network_health": self._compute_network_health(),
            "node_states": {nid: node.get_state().__dict__ for nid, node in self.nodes.items()},
        }


if __name__ == "__main__":
    print("[OMNI-HUB v26] Distributed Swarm Demo")
    print()

    network = DistributedSwarm(n_nodes=3)
    result = network.run(cycles=50, report_interval=10)

    print(f"\n{'='*70}")
    print("DISTRIBUTED NETWORK STATUS")
    print(f"{'='*70}")
    for key, val in result.items():
        if key != 'node_states':
            print(f"  {key}: {val}")
    print(f"\n{'='*70}")
    print("The network thinks as one. The swarm evolves as one.")
    print(f"{'='*70}")
