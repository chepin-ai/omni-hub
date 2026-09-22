"""
OMNI-HUB Distributed Swarm Tests v26
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.distributed_swarm import DistributedSwarm, NetworkNode, NodeState


class TestNodeState:
    def test_node_state_creation(self):
        state = NodeState(node_id="test-001", level=5, energy=100.0)
        assert state.node_id == "test-001"
        assert state.level == 5
        assert state.energy == 100.0
        assert state.alive is True


class TestNetworkNode:
    def test_initialization(self):
        node = NetworkNode("node-001")
        assert node.node_id == "node-001"
        assert node.loop is not None
        assert len(node.peers) == 0

    def test_run_cycle(self):
        node = NetworkNode("node-002")
        result = node.run_cycle()
        assert result['node_id'] == "node-002"
        assert 'local' in result

    def test_receive_message(self):
        node = NetworkNode("node-003")
        msg = {"type": "state_sync", "state": {"node_id": "peer-001", "level": 10}}
        node.receive_message(msg)
        assert len(node.message_queue) == 1

    def test_leader_election(self):
        node = NetworkNode("node-004")
        # Simulate peer with higher level
        node.peers["peer-001"] = NodeState(node_id="peer-001", level=20, energy=1e10)
        node._elect_leader()
        assert node.leader_id == "peer-001"

    def test_get_state(self):
        node = NetworkNode("node-005")
        node.run_cycle()
        state = node.get_state()
        assert state.node_id == "node-005"
        assert state.cycle >= 1


class TestDistributedSwarm:
    def test_initialization(self):
        swarm = DistributedSwarm(n_nodes=3)
        assert len(swarm.nodes) == 3
        assert swarm.global_cycle == 0

    def test_run_cycle(self):
        swarm = DistributedSwarm(n_nodes=2)
        result = swarm.run_cycle()
        assert result['global_cycle'] == 1
        assert 'nodes' in result
        assert 'consensus_leader' in result
        assert result['network_health'] == 1.0

    def test_multiple_cycles(self):
        swarm = DistributedSwarm(n_nodes=2)
        for _ in range(5):
            result = swarm.run_cycle()
        assert result['global_cycle'] == 5

    def test_leader_consensus(self):
        swarm = DistributedSwarm(n_nodes=3)
        result = swarm.run_cycle()
        # All nodes should agree on leader
        leaders = [n.leader_id for n in swarm.nodes.values()]
        assert len(set(leaders)) == 1

    def test_network_health(self):
        swarm = DistributedSwarm(n_nodes=2)
        health = swarm._compute_network_health()
        assert health == 1.0

    def test_final_status(self):
        swarm = DistributedSwarm(n_nodes=2)
        swarm.run(cycles=3, report_interval=3)
        status = swarm.get_final_status()
        assert status['system'] == 'OMNI-HUB v26'
        assert status['nodes'] == 2
        assert 'node_states' in status
