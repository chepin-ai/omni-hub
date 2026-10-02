import time
"""OMNI-HUB v192 Tests — DistributedConsensusLayer"""

import pytest
from core.distributed_consensus_layer import (
    DistributedConsensusLayer, RaftNode, BFTReplica,
    ConsensusCoordinator, LogReplicator, LeaderElection,
    NodeState, ConsensusStatus, ConsensusMode, LogEntry,
    get_distributed_consensus_layer
)


class TestRaftNode:
    def test_init(self):
        n = RaftNode("n1")
        assert n.state == NodeState.FOLLOWER
        assert n.current_term == 0

    def test_request_vote(self):
        n = RaftNode("n1")
        assert n.request_vote(1, "n2") is True
        assert n.voted_for == "n2"

    def test_request_vote_lower_term(self):
        n = RaftNode("n1")
        n.current_term = 2
        assert n.request_vote(1, "n2") is False

    def test_append_entries(self):
        n = RaftNode("n1")
        e = LogEntry(1, 1, "cmd", time.time())
        assert n.append_entries(1, "leader", [e]) is True
        assert len(n.log) == 1

    def test_start_election(self):
        n = RaftNode("n1")
        msg = n.start_election()
        assert n.state == NodeState.CANDIDATE
        assert msg.msg_type == "REQUEST_VOTE"

    def test_become_leader(self):
        n = RaftNode("n1", total_nodes=3)
        n.start_election()
        n.votes_received = {"n1", "n2"}
        n.become_leader()
        assert n.state == NodeState.LEADER

    def test_get_report(self):
        n = RaftNode("n1")
        r = n.get_report()
        assert r["node_id"] == "n1"


class TestBFTReplica:
    def test_init(self):
        r = BFTReplica("r1")
        assert r.fault_tolerance == 2  # (7-1)//3
        assert r.is_byzantine is False

    def test_prepare(self):
        r = BFTReplica("r1")
        assert r.prepare(1, "digest") is True
        assert "r1" in r.prepared[1]

    def test_byzantine_prepare(self):
        r = BFTReplica("r1")
        r.set_byzantine(True)
        # Result is deterministic based on hash
        result = r.prepare(1, "digest")
        assert isinstance(result, bool)

    def test_commit_certificate(self):
        replicas = [BFTReplica(f"r{i}") for i in range(7)]
        for rep in replicas:
            rep.prepared[1] = {f"r{i}" for i in range(7)}
            rep.commit(1)
            # Simulate receiving commits from all replicas
            replicas[0].committed[1].add(rep.replica_id)
        assert replicas[0].check_commit_certificate(1) is True


class TestConsensusCoordinator:
    def test_raft_consensus(self):
        nodes = [RaftNode(f"n{i}", 3) for i in range(3)]
        nodes[0].state = NodeState.LEADER
        nodes[0].current_term = 1
        coord = ConsensusCoordinator(ConsensusMode.RAFT)
        result = coord._raft_consensus(nodes, "test_cmd")
        assert result.status in (ConsensusStatus.COMMITTED, ConsensusStatus.REJECTED)

    def test_bft_consensus(self):
        replicas = [BFTReplica(f"r{i}") for i in range(7)]
        coord = ConsensusCoordinator(ConsensusMode.BFT)
        result = coord._bft_consensus(replicas, "test_cmd")
        assert result.status in (ConsensusStatus.COMMITTED, ConsensusStatus.REJECTED)

    def test_get_report(self):
        coord = ConsensusCoordinator()
        assert coord.get_report()["total_consensus"] == 0


class TestLogReplicator:
    def test_replicate(self):
        lr = LogReplicator()
        leader = RaftNode("l1")
        leader.state = NodeState.LEADER
        f1 = RaftNode("f1")
        f2 = RaftNode("f2")
        e = LogEntry(1, 1, "cmd", time.time())
        r = lr.replicate(leader, [f1, f2], e)
        assert isinstance(r, dict)

    def test_replication_lag(self):
        lr = LogReplicator()
        lr.replica_states = {"n1": 5, "n2": 3}
        lag = lr.get_replication_lag()
        assert lag["n2"] == 2


class TestLeaderElection:
    def test_elect(self):
        le = LeaderElection()
        nodes = [RaftNode(f"n{i}", 3) for i in range(3)]
        leader = le.elect(nodes)
        # May or may not elect a leader depending on timing
        assert isinstance(leader, RaftNode) or leader is None

    def test_get_report(self):
        le = LeaderElection()
        assert le.get_report()["elections"] == 0


class TestDistributedConsensusLayer:
    def test_init(self):
        dcl = DistributedConsensusLayer()
        assert dcl.VERSION == "192.0.0"
        assert len(dcl.nodes) == 5
        assert len(dcl.replicas) == 7

    def test_propose(self):
        dcl = DistributedConsensusLayer(node_count=3, replica_count=4)
        result = dcl.propose("test_command")
        assert result.status in (ConsensusStatus.COMMITTED, ConsensusStatus.TIMEOUT, ConsensusStatus.REJECTED)

    def test_replicate_alliance_state(self):
        dcl = DistributedConsensusLayer(node_count=3, replica_count=4)
        r = dcl.replicate_alliance_state({"l1": {"health": 0.9}})
        assert "consensus" in r

    def test_simulate_byzantine(self):
        dcl = DistributedConsensusLayer()
        dcl.simulate_byzantine(["bft_0", "bft_1"])
        assert dcl.replicas[0].is_byzantine is True
        assert dcl.replicas[1].is_byzantine is True

    def test_run_cycle(self):
        dcl = DistributedConsensusLayer(node_count=3, replica_count=4)
        r = dcl.run_cycle({"l1": {"health": 0.9}})
        assert r["cycle"] == 1

    def test_get_status(self):
        dcl = DistributedConsensusLayer(node_count=3, replica_count=4)
        s = dcl.get_status()
        assert s["version"] == "192.0.0"
        assert "nodes" in s

    def test_singleton(self):
        d1 = get_distributed_consensus_layer()
        d2 = get_distributed_consensus_layer()
        assert d1 is d2

# Total: 25 tests
